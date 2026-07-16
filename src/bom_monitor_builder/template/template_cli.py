from __future__ import annotations

from pathlib import Path

import click

from bom_monitor_builder.template.report import write_scan_outputs
from bom_monitor_builder.template.scanner import scan_template_data


@click.group()
def template() -> None:
    """Explore BOM TemplateData inventory."""


@template.command("scan")
@click.option(
    "--source",
    type=click.Path(path_type=Path),
    default=Path("import/TemplateData"),
    show_default=True,
    help="TemplateData source directory.",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    default=Path("knowledge"),
    show_default=True,
    help="Output directory.",
)
def scan(source: Path, output: Path) -> None:
    """Scan TemplateData and generate Iteration00 inventory outputs."""
    scan_result = scan_template_data(source, output)
    write_scan_outputs(scan_result, output)

    click.echo("TemplateData Scan")
    click.echo(f"Source: {scan_result.summary.source}")
    click.echo(f"Categories: {scan_result.summary.category_count}")
    click.echo(f"CAB: {scan_result.summary.cab_count}")
    click.echo(f"HTML: {scan_result.summary.html_count}")
    click.echo(f"YAML: {scan_result.summary.yaml_count}")
    click.echo(f"Images: {scan_result.summary.image_count}")
    click.echo(f"Other files: {scan_result.summary.other_file_count}")
    click.echo(f"Max depth: {scan_result.summary.max_depth}")
    click.echo(f"Completed: {output.resolve()}")
