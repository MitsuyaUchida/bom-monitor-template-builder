import logging
from pathlib import Path
from typing import Any

import click

from bom_monitor_builder.analyzers.relevance import calculate_relevance
from bom_monitor_builder.build.cli import build_command, build_with_codex_command
from bom_monitor_builder.cab_excel.cli import cab_excel
from bom_monitor_builder.design_excel.cli import design_excel
from bom_monitor_builder.generators.template import write_candidate_report
from bom_monitor_builder.knowledge.logging import configure_logging
from bom_monitor_builder.knowledge.service import import_source, inspect_source, summarize_for_click
from bom_monitor_builder.models.discovery import MonitoringCandidate
from bom_monitor_builder.template.template_cli import template
from bom_monitor_builder.utils.config import load_config


@click.group()
def main() -> None:
    """Build BOM monitoring-template candidates."""


@main.command()
@click.option(
    "--config",
    "config_path",
    type=click.Path(path_type=Path),
    default=Path("config/settings.yml"),
    show_default=True,
)
def check(config_path: Path) -> None:
    """Validate the project configuration."""
    config = load_config(config_path)
    click.echo(f"Configuration OK: {config['project']['name']}")


@main.command()
@click.option("--software", required=True, help="Target software name.")
@click.option("--candidate", required=True, help="Candidate service or event-provider name.")
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    default=Path("output/reports/sample_candidates.csv"),
    show_default=True,
)
def sample(software: str, candidate: str, output: Path) -> None:
    """Run the initial sample analysis."""
    score, reason = calculate_relevance(software, candidate)
    result = MonitoringCandidate(
        target_type="sample",
        target_name=candidate,
        relevance_score=score,
        reason=reason,
    )
    write_candidate_report([result], output)
    click.echo(f"Report written: {output}")


@main.group()
def knowledge() -> None:
    """Inspect and import BOM TemplateData knowledge."""


main.add_command(template)
main.add_command(cab_excel)
main.add_command(design_excel)
main.add_command(build_command)
main.add_command(build_with_codex_command)


@knowledge.command("inspect")
@click.option(
    "--source",
    type=click.Path(path_type=Path),
    default=None,
    help="TemplateData source directory.",
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(path_type=Path),
    default=Path("config/settings.yml"),
    show_default=True,
)
def knowledge_inspect(source: Path | None, config_path: Path) -> None:
    """Inspect TemplateData without modifying source files."""
    config = load_config(config_path)
    source_path = source or get_nested_path(config, "knowledge", "source_dir", "import/TemplateData")
    logger = build_knowledge_logger(config)
    scan_result = inspect_source(source_path, logger)
    for label, value in summarize_for_click(scan_result).items():
        click.echo(f"{label}: {value}")
    emit_warnings(scan_result.summary.warnings)


@knowledge.command("import")
@click.option(
    "--source",
    type=click.Path(path_type=Path),
    default=None,
    help="TemplateData source directory.",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    default=None,
    help="Knowledge output directory.",
)
@click.option("--dry-run", is_flag=True, help="Inspect and plan outputs without writing files.")
@click.option("--force", is_flag=True, help="Mark all existing entries for refresh.")
@click.option(
    "--config",
    "config_path",
    type=click.Path(path_type=Path),
    default=Path("config/settings.yml"),
    show_default=True,
)
def knowledge_import(
    source: Path | None,
    output: Path | None,
    dry_run: bool,
    force: bool,
    config_path: Path,
) -> None:
    """Import TemplateData inventory and AutoTemplate analysis."""
    config = load_config(config_path)
    source_path = source or get_nested_path(config, "knowledge", "source_dir", "import/TemplateData")
    output_path = output or get_nested_path(config, "knowledge", "output_dir", "knowledge")
    logger = build_knowledge_logger(config)

    scan_result, import_plan = import_source(
        source_path=source_path,
        output_path=output_path,
        dry_run=dry_run,
        force=force,
        logger=logger,
    )
    for label, value in summarize_for_click(scan_result).items():
        click.echo(f"{label}: {value}")

    click.echo(f"Added: {import_plan.added}")
    click.echo(f"Updated: {import_plan.updated}")
    click.echo(f"Unchanged: {import_plan.unchanged}")
    click.echo(f"Removed: {import_plan.removed}")
    click.echo(f"Failed: {import_plan.failed}")
    click.echo(f"Skipped: {import_plan.skipped}")
    click.echo(f"Analysis targets: {scan_result.summary.total_file_count}")
    click.echo(f"Planned output: {import_plan.output_path}")

    if dry_run:
        click.echo("Dry-run mode: no files were written.")
    else:
        click.echo(f"Artifacts written under: {output_path}")

    emit_warnings(scan_result.summary.warnings)


def build_knowledge_logger(config: dict[str, Any]) -> logging.Logger:
    level = get_nested_str(config, "logging", "level", "INFO")
    log_file = get_nested_path(config, "logging", "file", "logs/bom-monitor-builder.log")
    return configure_logging(log_file, level)


def get_nested_path(
    config: dict[str, Any],
    section: str,
    key: str,
    default_value: str,
) -> Path:
    section_value = config.get(section)
    if isinstance(section_value, dict):
        candidate = section_value.get(key)
        if isinstance(candidate, str):
            return Path(candidate)
    return Path(default_value)


def get_nested_str(
    config: dict[str, Any],
    section: str,
    key: str,
    default_value: str,
) -> str:
    section_value = config.get(section)
    if isinstance(section_value, dict):
        candidate = section_value.get(key)
        if isinstance(candidate, str):
            return candidate
    return default_value


def emit_warnings(warnings: list[str]) -> None:
    if not warnings:
        return
    click.echo("Warnings:")
    for warning in warnings:
        click.echo(f"- {warning}")
