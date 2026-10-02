from __future__ import annotations

import sys
from types import SimpleNamespace
from pathlib import Path

from bom_monitor_builder.build.codex_service import (
    BuildFailureKind,
    BuildInvocation,
    CodexPromptBundle,
    build_rerun_command,
    classify_failure,
    extract_candidates,
    render_codex_prompt,
    run_codex_auto,
)
from bom_monitor_builder.build.detector import analyze_profiles
from bom_monitor_builder.build.models import DetectionInput


def test_classify_failure_detects_profile_not_found_and_intermediate_path(tmp_path: Path) -> None:
    intermediate_path = tmp_path / "example.xlsx"
    failure = classify_failure(
        Exception(
            "No matching profile was found.\n\n"
            "Specify --profile explicitly or add a detection rule to a profile.\n"
            f"Intermediate Excel: {intermediate_path}"
        )
    )

    assert failure.kind == BuildFailureKind.PROFILE_NOT_FOUND
    assert failure.intermediate_excel == intermediate_path


def test_classify_failure_detects_profile_ambiguous_and_candidates(tmp_path: Path) -> None:
    intermediate_path = tmp_path / "example.xlsx"
    failure = classify_failure(
        Exception(
            "Profile detection is ambiguous.\n\n"
            "Candidates:\n\n"
            "- sqlserver2022_windows\n"
            "- arcserve_udp9\n\n"
            "Specify --profile explicitly.\n"
            f"Intermediate Excel: {intermediate_path}"
        )
    )

    assert failure.kind == BuildFailureKind.PROFILE_AMBIGUOUS
    assert failure.candidates == ["sqlserver2022_windows", "arcserve_udp9"]


def test_extract_candidates_returns_empty_list_when_not_present() -> None:
    assert extract_candidates("No candidates here.") == []


def test_analyze_profiles_exposes_score_breakdown_for_activeimage_case() -> None:
    analyses = analyze_profiles(
        DetectionInput(
            source_path=Path("import/cab/0905_ActiveImage Protector 2022 ServerEditon.CAB"),
            source_name="0905_ActiveImage Protector 2022 ServerEditon.CAB",
            source_stem="0905_ActiveImage Protector 2022 ServerEditon",
            manifest_product="BOM for Windows",
            group_names=["ActiveImage Protector 2022 ServerEditon"],
            monitor_names=[
                "ActiveImage Protector Service 監視",
                "バックアップ失敗監視",
                "バックアップキャンセル監視",
                "バックアップ正常性監視",
            ],
            monitor_types=["Service", "EventlogWSA"],
            object_names=["AipService", "Application"],
            value_names=["CurrentState", "MonitorCountWSA"],
        )
    )

    by_profile = {analysis.profile_id: analysis for analysis in analyses}
    activeimage = by_profile["activeimage_protector2022_serveredition"]
    sqlserver = by_profile["sqlserver2022_windows"]
    arcserve = by_profile["arcserve_udp9"]

    assert activeimage.final_score > 0
    assert "ActiveImage Protector 2022 ServerEditon" in activeimage.group_matches
    assert "AipService" in activeimage.monitor_matches
    assert activeimage.monitor_type_matches == ["Service", "EventlogWSA"]

    assert sqlserver.raw_score == 0
    assert sqlserver.final_score == 0
    assert sqlserver.monitor_type_matches == ["Service", "EventlogWSA"]

    assert arcserve.raw_score == 0
    assert arcserve.final_score == 0
    assert arcserve.monitor_type_matches == ["Service", "EventlogWSA"]


def test_build_invocation_cli_args_includes_selected_options(tmp_path: Path) -> None:
    invocation = BuildInvocation(
        input_path=Path("import/cab/example.cab"),
        output_path=tmp_path / "out.xlsx",
        profile_value="profiles/example.yml",
        template_path=Path("templates/example.xlsx"),
        work_dir=tmp_path / "work",
        overwrite=True,
        dry_run=True,
        keep_intermediate=True,
        dump_model_path=tmp_path / "model.json",
        verbose=True,
    )

    assert invocation.cli_args() == [
        "build",
        "--input",
        str(Path("import/cab/example.cab")),
        "--output",
        str(tmp_path / "out.xlsx"),
        "--profile",
        "profiles/example.yml",
        "--template",
        str(Path("templates/example.xlsx")),
        "--work-dir",
        str(tmp_path / "work"),
        "--overwrite",
        "--dry-run",
        "--keep-intermediate",
        "--dump-model",
        str(tmp_path / "model.json"),
        "--verbose",
    ]


def test_build_rerun_command_uses_current_python_and_preserves_cli_args(tmp_path: Path) -> None:
    invocation = BuildInvocation(
        input_path=Path("import/cab/example.cab"),
        output_path=tmp_path / "out.xlsx",
        profile_value="example",
        overwrite=True,
        keep_intermediate=True,
        verbose=True,
    )

    command = build_rerun_command(invocation)

    assert command[0] == sys.executable
    assert command[1:3] == [
        "-c",
        "from bom_monitor_builder.cli import main; main()",
    ]
    assert command[3:] == invocation.cli_args()
    assert ".venv/bin/bom-monitor-builder" not in command


def test_codex_auto_rerun_uses_current_python_without_external_codex(
    tmp_path: Path, monkeypatch
) -> None:
    invocation = BuildInvocation(
        input_path=Path("import/cab/example.cab"),
        output_path=tmp_path / "out.xlsx",
        overwrite=True,
        keep_intermediate=True,
        verbose=True,
    )
    bundle = CodexPromptBundle(
        prompt="prompt",
        log_dir=tmp_path,
        failure=classify_failure(Exception("build failed")),
        summary=None,
        detection_input=None,
    )
    commands: list[list[str]] = []

    def fake_run(command, **kwargs):
        commands.append(command)
        stdout = "Validation: PASS" if command[0] == sys.executable else "Codex done"
        return SimpleNamespace(returncode=0, stdout=stdout, stderr="")

    monkeypatch.setattr("bom_monitor_builder.build.codex_service.subprocess.run", fake_run)

    result = run_codex_auto(invocation, bundle, max_attempts=1)

    assert commands[1] == build_rerun_command(invocation)
    assert commands[1][0] == sys.executable
    assert commands[1][3:] == invocation.cli_args()
    assert result.rerun_exit_code == 0
    assert "Validation: PASS" in result.rerun_stdout


def test_codex_prompt_uses_cross_platform_rerun_instructions(tmp_path: Path) -> None:
    invocation = BuildInvocation(input_path=Path("import/cab/example.cab"))
    failure = classify_failure(Exception("build failed"))
    prompt = render_codex_prompt(invocation, failure, None, None, [])

    assert ".venv/bin/bom-monitor-builder" not in prompt
    assert "sys.executable" in prompt
    assert "bom_monitor_builder.cli:main" in prompt
