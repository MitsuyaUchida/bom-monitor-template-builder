from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from bom_monitor_builder.cab_excel.cli import parse_input_to_model
from bom_monitor_builder.design_excel.exceptions import ValidationError

from .detector import analyze_profiles
from .exceptions import BuildError
from .models import DetectionCandidateAnalysis, DetectionInput
from .service import build_detection_input, run_build


class BuildFailureKind(StrEnum):
    PROFILE_NOT_FOUND = "PROFILE_NOT_FOUND"
    PROFILE_AMBIGUOUS = "PROFILE_AMBIGUOUS"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    CAB_PARSE_FAILED = "CAB_PARSE_FAILED"
    BUILD_FAILED_UNKNOWN = "BUILD_FAILED_UNKNOWN"


@dataclass(slots=True)
class BuildInvocation:
    input_path: Path
    output_path: Path | None = None
    profile_value: str | None = None
    template_path: Path | None = None
    work_dir: Path | None = None
    overwrite: bool = False
    dry_run: bool = False
    keep_intermediate: bool = False
    validate_only: bool = False
    dump_model_path: Path | None = None
    verbose: bool = False

    def cli_args(self) -> list[str]:
        args = ["build", "--input", str(self.input_path)]
        if self.output_path is not None:
            args.extend(["--output", str(self.output_path)])
        if self.profile_value is not None:
            args.extend(["--profile", self.profile_value])
        if self.template_path is not None:
            args.extend(["--template", str(self.template_path)])
        if self.work_dir is not None:
            args.extend(["--work-dir", str(self.work_dir)])
        if self.overwrite:
            args.append("--overwrite")
        if self.dry_run:
            args.append("--dry-run")
        if self.keep_intermediate:
            args.append("--keep-intermediate")
        if self.validate_only:
            args.append("--validate-only")
        if self.dump_model_path is not None:
            args.extend(["--dump-model", str(self.dump_model_path)])
        if self.verbose:
            args.append("--verbose")
        return args


@dataclass(slots=True)
class BuildFailure:
    kind: BuildFailureKind
    message: str
    exit_code: int
    stdout: str
    stderr: str
    intermediate_excel: Path | None
    detected_profile: str | None = None
    candidates: list[str] = field(default_factory=list)
    stack_trace: str | None = None


@dataclass(slots=True)
class IntermediateWorkbookSummary:
    path: Path
    sheet_names: list[str]
    manifest_product: str
    group_count: int
    monitor_count: int
    group_names: list[str]
    monitor_names: list[str]
    monitor_types: list[str]
    object_names: list[str]
    value_names: list[str]


@dataclass(slots=True)
class CodexPromptBundle:
    prompt: str
    log_dir: Path
    failure: BuildFailure
    summary: IntermediateWorkbookSummary | None
    detection_input: DetectionInput | None
    profile_analyses: list[DetectionCandidateAnalysis] = field(default_factory=list)


@dataclass(slots=True)
class CodexAutoResult:
    prompt_bundle: CodexPromptBundle
    codex_exit_code: int | None
    codex_stdout: str
    codex_stderr: str
    rerun_exit_code: int | None
    rerun_stdout: str
    rerun_stderr: str


def run_build_with_codex(
    invocation: BuildInvocation,
    *,
    codex_prompt_only: bool,
    codex_auto: bool,
    codex_max_attempts: int = 1,
    codex_output_root: Path = Path("output/codex_runs"),
) -> tuple[bool, str, CodexPromptBundle | CodexAutoResult | None]:
    try:
        result = run_build(
            input_path=invocation.input_path,
            output_path=invocation.output_path,
            profile_value=invocation.profile_value,
            template_path=invocation.template_path,
            work_dir=invocation.work_dir,
            overwrite=invocation.overwrite,
            dry_run=invocation.dry_run,
            keep_intermediate=invocation.keep_intermediate,
            validate_only=invocation.validate_only,
            dump_model_path=invocation.dump_model_path,
            verbose=invocation.verbose,
        )
    except Exception as exc:
        failure = classify_failure(exc)
        bundle = build_codex_prompt_bundle(
            invocation=invocation,
            failure=failure,
            codex_output_root=codex_output_root,
        )
        if codex_prompt_only:
            return False, bundle.prompt, bundle
        if codex_auto:
            return False, "", run_codex_auto(invocation, bundle, max_attempts=codex_max_attempts)
        raise
    return True, format_success_output(result), None


def classify_failure(exc: Exception) -> BuildFailure:
    message = str(exc)
    kind = BuildFailureKind.BUILD_FAILED_UNKNOWN
    if "No matching profile was found." in message:
        kind = BuildFailureKind.PROFILE_NOT_FOUND
    elif "Profile detection is ambiguous." in message:
        kind = BuildFailureKind.PROFILE_AMBIGUOUS
    elif isinstance(exc, ValidationError) or "ValidationError" in message or "Validation failed" in message:
        kind = BuildFailureKind.VALIDATION_FAILED
    elif "CAB analysis failed:" in message or "MANIFEST.MF" in message or "Input CAB was not found:" in message:
        kind = BuildFailureKind.CAB_PARSE_FAILED
    intermediate_excel = extract_trailing_path(message, "Intermediate Excel:")
    candidates = extract_candidates(message)
    detected_profile = extract_trailing_value(message, "Detected profile:")
    return BuildFailure(
        kind=kind,
        message=message,
        exit_code=1,
        stdout="",
        stderr=message,
        intermediate_excel=intermediate_excel,
        detected_profile=detected_profile,
        candidates=candidates,
        stack_trace=None,
    )


def build_codex_prompt_bundle(
    *,
    invocation: BuildInvocation,
    failure: BuildFailure,
    codex_output_root: Path,
) -> CodexPromptBundle:
    log_dir = codex_output_root / datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") / sanitize_stem(invocation.input_path.stem)
    log_dir.mkdir(parents=True, exist_ok=True)
    summary = summarize_intermediate(invocation.input_path, failure.intermediate_excel)
    detection_input = build_detection_input_from_summary(invocation.input_path, summary)
    analyses = analyze_profiles(detection_input) if detection_input is not None else []
    prompt = render_codex_prompt(invocation, failure, summary, detection_input, analyses)
    persist_codex_bundle(log_dir, invocation, failure, summary, detection_input, analyses, prompt)
    return CodexPromptBundle(
        prompt=prompt,
        log_dir=log_dir,
        failure=failure,
        summary=summary,
        detection_input=detection_input,
        profile_analyses=analyses,
    )


def run_codex_auto(
    invocation: BuildInvocation,
    bundle: CodexPromptBundle,
    *,
    max_attempts: int,
) -> CodexAutoResult:
    attempts = max(1, min(max_attempts, 2))
    codex_stdout = ""
    codex_stderr = ""
    codex_exit_code: int | None = None
    rerun_stdout = ""
    rerun_stderr = ""
    rerun_exit_code: int | None = None

    for attempt in range(attempts):
        command = [
            "codex",
            "exec",
            "--cd",
            str(Path.cwd()),
            "--sandbox",
            "workspace-write",
            bundle.prompt,
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        codex_exit_code = result.returncode
        codex_stdout = result.stdout
        codex_stderr = result.stderr
        (bundle.log_dir / f"codex_exec_attempt_{attempt + 1}.stdout.txt").write_text(result.stdout, encoding="utf-8")
        (bundle.log_dir / f"codex_exec_attempt_{attempt + 1}.stderr.txt").write_text(result.stderr, encoding="utf-8")

        rerun = subprocess.run(
            build_rerun_command(invocation),
            capture_output=True,
            text=True,
            check=False,
        )
        rerun_exit_code = rerun.returncode
        rerun_stdout = rerun.stdout
        rerun_stderr = rerun.stderr
        (bundle.log_dir / f"rerun_build_attempt_{attempt + 1}.stdout.txt").write_text(rerun.stdout, encoding="utf-8")
        (bundle.log_dir / f"rerun_build_attempt_{attempt + 1}.stderr.txt").write_text(rerun.stderr, encoding="utf-8")
        if rerun.returncode == 0 and "Validation: PASS" in rerun.stdout:
            break

    persist_auto_summary(bundle.log_dir, codex_exit_code, rerun_exit_code, rerun_stdout)
    return CodexAutoResult(
        prompt_bundle=bundle,
        codex_exit_code=codex_exit_code,
        codex_stdout=codex_stdout,
        codex_stderr=codex_stderr,
        rerun_exit_code=rerun_exit_code,
        rerun_stdout=rerun_stdout,
        rerun_stderr=rerun_stderr,
    )


def build_rerun_command(invocation: BuildInvocation) -> list[str]:
    return [
        sys.executable,
        "-c",
        "from bom_monitor_builder.cli import main; main()",
        *invocation.cli_args(),
    ]


def summarize_intermediate(input_path: Path, intermediate_excel: Path | None) -> IntermediateWorkbookSummary | None:
    if intermediate_excel is None:
        return None
    if intermediate_excel.exists():
        parsed, session = parse_input_to_model(input_path, extracted=input_path.is_dir(), keep_extracted=False)
        try:
            return IntermediateWorkbookSummary(
                path=intermediate_excel,
                sheet_names=["表紙", "監視グループ一覧", "監視項目一覧", "監視項目詳細", "XML全項目", "解析情報"],
                manifest_product=parsed.manifest.product,
                group_count=len(parsed.groups),
                monitor_count=len(parsed.items),
                group_names=sorted({str(group.raw_values.get("Name", "")) for group in parsed.groups if group.raw_values.get("Name", "")}),
                monitor_names=sorted({str(item.raw_values.get("Name", "")) for item in parsed.items if item.raw_values.get("Name", "")}),
                monitor_types=sorted({str(item.raw_values.get("Type", "")) for item in parsed.items if item.raw_values.get("Type", "")}),
                object_names=sorted({str(item.raw_values.get("ObjectName", "")) for item in parsed.items if item.raw_values.get("ObjectName", "")}),
                value_names=sorted({str(item.raw_values.get("ValueName", "")) for item in parsed.items if item.raw_values.get("ValueName", "")}),
            )
        finally:
            session.cleanup()
    return None


def build_detection_input_from_summary(
    input_path: Path,
    summary: IntermediateWorkbookSummary | None,
) -> DetectionInput | None:
    if summary is None:
        return None
    return DetectionInput(
        source_path=input_path,
        source_name=input_path.name,
        source_stem=input_path.stem,
        manifest_product=summary.manifest_product,
        group_names=summary.group_names,
        monitor_names=summary.monitor_names,
        monitor_types=summary.monitor_types,
        object_names=summary.object_names,
        value_names=summary.value_names,
    )


def render_codex_prompt(
    invocation: BuildInvocation,
    failure: BuildFailure,
    summary: IntermediateWorkbookSummary | None,
    detection_input: DetectionInput | None,
    analyses: list[DetectionCandidateAnalysis],
) -> str:
    base = [
        "# Codex自動調査フローからの依頼",
        "",
        "最初から修正方法を決め打ちしないこと。",
        "対象CAB、中間Excel、既存profile、detector、関連テストを確認してから判断すること。",
        "単にbuildを通すのではなく、正しいprofileが選ばれていることを確認すること。",
        "--profileで強制適用してbuildが通っても、それを適合の証拠にしないこと。",
        "ファイル名だけに依存した検出を避けること。",
        "monitor_typeだけの一致を製品固有の根拠にしないこと。",
        "既存profileと互換性がないなら新規profileを検討すること。",
        "誤検出原因が一般化できるならdetector側も改善すること。",
        "既存profileの正常検出を壊さないこと。",
        "特定CABだけを通すハードコードを避けること。",
        "",
        f"対象CAB: {invocation.input_path}",
        f"ビルドは現在の環境のPython (sys.executable) から bom_monitor_builder.cli:main を呼び出し、{' '.join(invocation.cli_args())} を渡して実行すること。",
        f"エラー種別: {failure.kind}",
        f"exit code: {failure.exit_code}",
        f"stdout: {failure.stdout or '(none)'}",
        f"stderr: {failure.stderr}",
        f"Intermediate Excel: {failure.intermediate_excel if failure.intermediate_excel is not None else '(unknown)'}",
        "",
        "既存profiles一覧:",
    ]
    base.extend(f"- {path.stem}" for path in sorted(Path("profiles").glob("*.yml")))
    if summary is not None:
        base.extend(
            [
                "",
                "中間Excelの主要内容:",
                f"- シート構成: {', '.join(summary.sheet_names)}",
                f"- 製品名: {summary.manifest_product}",
                f"- グループ数: {summary.group_count}",
                f"- 監視件数: {summary.monitor_count}",
                f"- グループ名: {', '.join(summary.group_names[:10]) or '(none)'}",
                f"- 監視名: {', '.join(summary.monitor_names[:10]) or '(none)'}",
                f"- 監視タイプ: {', '.join(summary.monitor_types[:10]) or '(none)'}",
                f"- サービス名/オブジェクト名: {', '.join(summary.object_names[:10]) or '(none)'}",
                f"- イベント/値名: {', '.join(summary.value_names[:10]) or '(none)'}",
            ]
        )
    if detection_input is not None:
        base.extend(
            [
                "",
                "profile detection処理経路:",
                "run_build() -> parse_input_to_model() -> save_workbook() -> build_detection_input() -> resolve_profile_path() -> detect_profile()",
                "",
                "build_detection_input() で抽出されるシグナル:",
                "- source_name",
                "- source_stem",
                "- manifest_product",
                "- group_names",
                "- monitor_names",
                "- monitor_types",
                "- object_names",
                "- value_names",
            ]
        )
    if failure.kind == BuildFailureKind.PROFILE_AMBIGUOUS and analyses:
        base.append("")
        base.append("候補profileのscore内訳:")
        for analysis in analyses[:10]:
            if analysis.final_score <= 0:
                continue
            base.extend(
                [
                    f"{analysis.profile_id}",
                    f"  filename: {analysis.filename_matches or []}",
                    f"  group: {analysis.group_matches or []}",
                    f"  monitor: {analysis.monitor_matches or []}",
                    f"  monitor_type: {analysis.monitor_type_matches or []}",
                    f"  raw score: {analysis.raw_score}",
                    f"  priority: {analysis.priority}",
                    f"  final score: {analysis.final_score}",
                ]
            )
    base.extend(render_failure_specific_instructions(failure))
    base.extend(
        [
            "",
            "修正した場合は最低限以下を実行すること。",
            "1. focused test",
            "2. 現在の環境のPythonで python -m pytest を実行",
            f"3. 現在の環境のPython (sys.executable) から bom_monitor_builder.cli:main を呼び出し、{' '.join(invocation.cli_args())} で再実行",
            "",
            "最終報告では、原因、採用方針、変更ファイル、テスト結果、再build結果を具体的に示すこと。",
        ]
    )
    return "\n".join(base) + "\n"


def render_failure_specific_instructions(failure: BuildFailure) -> list[str]:
    if failure.kind == BuildFailureKind.PROFILE_NOT_FOUND:
        return [
            "",
            "PROFILE_NOT_FOUND として調査すること。",
            "1. CABから中間Excelへ変換する処理経路を確認する。",
            "2. detect_profile() の採点方式を確認する。",
            "3. 中間Excelの主要シグナルを抽出する。",
            "4. 既存profileのうち最も近いものを比較する。",
            "5. --profile を明示した場合に build できるか確認する。",
            "6. ただし build が通ることと profile が適合していることを混同しない。",
            "7. 既存profileへ detection だけ追加すべきか、新規profileが必要か判断する。",
        ]
    if failure.kind == BuildFailureKind.PROFILE_AMBIGUOUS:
        return [
            "",
            "PROFILE_AMBIGUOUS として調査すること。",
            "1. 候補profileとの実互換性を確認する。",
            "2. monitor_type_patterns だけで候補化されていないか必ず確認する。",
            "3. monitor_type が Service / EventlogWSA / Perf だけなら誤検出を疑うこと。",
            "4. 対象製品固有シグナルを探し、新規profile追加の要否を判断すること。",
            "5. 誤検出原因が一般化できるなら detector 側も改善すること。",
            "",
            "ActiveImage Protector 2022 事例の重要知見:",
            "- type:Service と type:EventlogWSA だけで sqlserver2022_windows と arcserve_udp9 が同点候補化した。",
            "- monitor_type は補助シグナルであり、filename/group/monitor の非汎用シグナルが無い profile を候補化しないのが自然。",
        ]
    if failure.kind == BuildFailureKind.VALIDATION_FAILED:
        return [
            "",
            "VALIDATION_FAILED として調査すること。",
            "1. どの validation が失敗したか確認する。",
            "2. 対象 sheet / row / monitor / 入力値 / profile変換結果 / mapper出力 / validation直前の値を追うこと。",
            "3. CAB parser / 中間Excel変換 / profile / mapper / style / validation のどこで壊れたか切り分けること。",
            "4. 単に validation 条件を緩めないこと。",
        ]
    if failure.kind == BuildFailureKind.CAB_PARSE_FAILED:
        return [
            "",
            "CAB_PARSE_FAILED として調査すること。",
            "1. CAB extractor, MANIFEST, XML parser のどこで失敗したか切り分けること。",
            "2. 中間Excelが残っている場合は内容を確認し、残っていなければ parser 側を優先して調査すること。",
        ]
    return [
        "",
        "BUILD_FAILED_UNKNOWN として調査すること。",
        "1. stack trace と直前の profile 解決結果を確認すること。",
        "2. 既存設計とテストを確認し、責務を混在させずに原因を切り分けること。",
    ]


def persist_codex_bundle(
    log_dir: Path,
    invocation: BuildInvocation,
    failure: BuildFailure,
    summary: IntermediateWorkbookSummary | None,
    detection_input: DetectionInput | None,
    analyses: list[DetectionCandidateAnalysis],
    prompt: str,
) -> None:
    (log_dir / "build_invocation.json").write_text(
        json.dumps(serialize_dataclass(invocation), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (log_dir / "failure.json").write_text(
        json.dumps(serialize_dataclass(failure), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if summary is not None:
        (log_dir / "intermediate_summary.json").write_text(
            json.dumps(serialize_dataclass(summary), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    if detection_input is not None:
        (log_dir / "detection_input.json").write_text(
            json.dumps(serialize_dataclass(detection_input), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    (log_dir / "profile_analysis.json").write_text(
        json.dumps([serialize_dataclass(item) for item in analyses], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (log_dir / "codex_prompt.txt").write_text(prompt, encoding="utf-8")


def persist_auto_summary(
    log_dir: Path,
    codex_exit_code: int | None,
    rerun_exit_code: int | None,
    rerun_stdout: str,
) -> None:
    payload = {
        "codex_exit_code": codex_exit_code,
        "rerun_exit_code": rerun_exit_code,
        "rerun_validation_pass": "Validation: PASS" in rerun_stdout,
    }
    (log_dir / "codex_auto_summary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def serialize_dataclass(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        data = asdict(value)
    else:
        data = value
    if isinstance(data, dict):
        return {key: serialize_dataclass(item) for key, item in data.items()}
    if isinstance(data, list):
        return [serialize_dataclass(item) for item in data]
    if isinstance(data, Path):
        return str(data)
    return data


def extract_trailing_path(message: str, label: str) -> Path | None:
    value = extract_trailing_value(message, label)
    return Path(value) if value else None


def extract_trailing_value(message: str, label: str) -> str | None:
    for line in message.splitlines():
        if line.startswith(label):
            return line.split(":", 1)[1].strip() or None
    return None


def extract_candidates(message: str) -> list[str]:
    lines = message.splitlines()
    try:
        start = lines.index("Candidates:")
    except ValueError:
        return []
    result: list[str] = []
    for line in lines[start + 1 :]:
        stripped = line.strip()
        if not stripped:
            if result:
                break
            continue
        if stripped.startswith("- "):
            result.append(stripped[2:])
            continue
        if result:
            break
    return result


def sanitize_stem(value: str) -> str:
    return "".join(character if character.isalnum() or character in {"-", "_"} else "_" for character in value)


def format_success_output(result: Any) -> str:
    lines = [
        "Build completed successfully.",
        "",
        f"Input CAB: {result.input_path}",
        f"Detected profile: {result.profile_id}",
        (
            "Template: generated automatically"
            if result.template_source == "generated_template"
            else f"Template: {result.template_path if result.template_path is not None else 'not configured'}"
        ),
        f"Intermediate Excel: {result.intermediate_path}",
        f"{'Planned output' if result.planned_output else 'Output'}: {result.output_path}",
        f"Groups: {result.group_count}",
        f"Monitors: {result.monitor_count}",
        f"Validation: {'PASS' if result.validation_checks else 'SKIPPED'}",
    ]
    if result.dump_model_path is not None:
        lines.append(f"Model JSON: {result.dump_model_path}")
    return "\n".join(lines)
