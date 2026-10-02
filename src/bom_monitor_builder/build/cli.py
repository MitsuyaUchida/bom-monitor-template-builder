from __future__ import annotations

from pathlib import Path

import click

from .codex_service import BuildInvocation, CodexAutoResult, CodexPromptBundle, run_build_with_codex
from .exceptions import BuildError
from .service import run_build


@click.command("build")
@click.option("--input", "input_path", type=click.Path(path_type=Path), required=True)
@click.option("--output", "output_path", type=click.Path(path_type=Path), default=None)
@click.option("--profile", "profile_value", default=None, help="Profile path or profile id.")
@click.option("--template", "template_path", type=click.Path(path_type=Path), default=None)
@click.option("--work-dir", "work_dir", type=click.Path(path_type=Path), default=None)
@click.option("--overwrite", is_flag=True, help="Overwrite existing managed artifacts.")
@click.option("--dry-run", is_flag=True, help="Run CAB analysis and resolution without writing the final workbook.")
@click.option("--keep-intermediate", is_flag=True, help="Keep the generated intermediate analysis workbook.")
@click.option("--validate-only", is_flag=True, help="Validate an existing final workbook without rewriting it.")
@click.option(
    "--dump-model",
    "dump_model_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Write the masked internal model as JSON.",
)
@click.option("--verbose", is_flag=True, help="Show detection reasons and resolved paths.")
def build_command(
    input_path: Path,
    output_path: Path | None,
    profile_value: str | None,
    template_path: Path | None,
    work_dir: Path | None,
    overwrite: bool,
    dry_run: bool,
    keep_intermediate: bool,
    validate_only: bool,
    dump_model_path: Path | None,
    verbose: bool,
) -> None:
    """Run CAB analysis, profile detection, design generation, and validation in one command."""
    try:
        result = run_build(
            input_path=input_path,
            output_path=output_path,
            profile_value=profile_value,
            template_path=template_path,
            work_dir=work_dir,
            overwrite=overwrite,
            dry_run=dry_run,
            keep_intermediate=keep_intermediate,
            validate_only=validate_only,
            dump_model_path=dump_model_path,
            verbose=verbose,
        )
    except BuildError as exc:
        raise click.ClickException(str(exc)) from exc

    lines = render_build_result_lines(result)
    if result.dump_model_path is not None:
        lines.append(f"Model JSON: {result.dump_model_path}")
    if verbose:
        lines.append(f"Detection mode: {result.detection_mode}")
        if result.detection_reasons:
            lines.append("Detection reasons:")
            lines.extend(f"- {reason}" for reason in result.detection_reasons)
        if result.output_resolution_log:
            lines.append("Output resolution:")
            lines.extend(f"- {line}" for line in result.output_resolution_log)
        lines.append(f"Input unchanged: {result.input_unchanged}")
        lines.append(f"Template unchanged: {result.template_unchanged}")
        lines.append(f"Intermediate kept: {result.intermediate_kept}")
        if result.validation_checks:
            lines.append("Validation checks:")
            lines.extend(f"- {check}" for check in result.validation_checks)
    click.echo("\n".join(lines))


@click.command("build-with-codex")
@click.option("--input", "input_path", type=click.Path(path_type=Path), required=True)
@click.option("--output", "output_path", type=click.Path(path_type=Path), default=None)
@click.option("--profile", "profile_value", default=None, help="Profile path or profile id.")
@click.option("--template", "template_path", type=click.Path(path_type=Path), default=None)
@click.option("--work-dir", "work_dir", type=click.Path(path_type=Path), default=None)
@click.option("--overwrite", is_flag=True, help="Overwrite existing managed artifacts.")
@click.option("--dry-run", is_flag=True, help="Run CAB analysis and resolution without writing the final workbook.")
@click.option("--keep-intermediate", is_flag=True, help="Keep the generated intermediate analysis workbook.")
@click.option("--validate-only", is_flag=True, help="Validate an existing final workbook without rewriting it.")
@click.option(
    "--dump-model",
    "dump_model_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Write the masked internal model as JSON.",
)
@click.option("--verbose", is_flag=True, help="Show detection reasons and resolved paths.")
@click.option("--codex-prompt", is_flag=True, help="Generate only the Codex investigation prompt on failure.")
@click.option("--codex-auto", is_flag=True, help="Run Codex automatically on failure, then rerun build once.")
@click.option(
    "--codex-max-attempts",
    type=click.IntRange(1, 2),
    default=1,
    show_default=True,
    help="Maximum automatic Codex fix attempts before stopping.",
)
@click.option(
    "--codex-log-dir",
    "codex_log_dir",
    type=click.Path(path_type=Path),
    default=Path("output/codex_runs"),
    show_default=True,
    help="Directory for Codex investigation logs.",
)
def build_with_codex_command(
    input_path: Path,
    output_path: Path | None,
    profile_value: str | None,
    template_path: Path | None,
    work_dir: Path | None,
    overwrite: bool,
    dry_run: bool,
    keep_intermediate: bool,
    validate_only: bool,
    dump_model_path: Path | None,
    verbose: bool,
    codex_prompt: bool,
    codex_auto: bool,
    codex_max_attempts: int,
    codex_log_dir: Path,
) -> None:
    """Run build and generate or execute a Codex investigation workflow on failure."""
    if codex_prompt and codex_auto:
        raise click.ClickException("--codex-prompt and --codex-auto cannot be used together.")
    if not codex_prompt and not codex_auto:
        raise click.ClickException("Specify either --codex-prompt or --codex-auto.")

    invocation = BuildInvocation(
        input_path=input_path,
        output_path=output_path,
        profile_value=profile_value,
        template_path=template_path,
        work_dir=work_dir,
        overwrite=overwrite,
        dry_run=dry_run,
        keep_intermediate=keep_intermediate,
        validate_only=validate_only,
        dump_model_path=dump_model_path,
        verbose=verbose,
    )

    try:
        succeeded, output, payload = run_build_with_codex(
            invocation,
            codex_prompt_only=codex_prompt,
            codex_auto=codex_auto,
            codex_max_attempts=codex_max_attempts,
            codex_output_root=codex_log_dir,
        )
    except BuildError as exc:
        raise click.ClickException(str(exc)) from exc

    if succeeded:
        click.echo(output)
        return

    if isinstance(payload, CodexPromptBundle):
        click.echo(output.rstrip())
        click.echo(f"Codex log: {payload.log_dir}")
        raise click.ClickException("Build failed. Codex investigation prompt was generated.")

    if isinstance(payload, CodexAutoResult):
        lines = [
            "Build failed and Codex auto-investigation was executed.",
            "",
            f"Codex log: {payload.prompt_bundle.log_dir}",
            f"Codex exit code: {payload.codex_exit_code}",
            f"Rebuild exit code: {payload.rerun_exit_code}",
        ]
        if payload.rerun_stdout:
            lines.extend(["", "Rebuild output:", payload.rerun_stdout.rstrip()])
        click.echo("\n".join(lines))
        if payload.rerun_exit_code == 0 and "Validation: PASS" in payload.rerun_stdout:
            return
        raise click.ClickException("Build failed after Codex auto-investigation.")


def render_build_result_lines(result: object) -> list[str]:
    return [
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
