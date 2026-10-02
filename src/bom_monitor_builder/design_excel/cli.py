from __future__ import annotations

import json
import logging
from pathlib import Path

import click

from .exceptions import DesignExcelError
from .service import run_conversion


@click.command("design-excel")
@click.option("--input", "input_path", type=click.Path(path_type=Path), required=True)
@click.option("--profile", "profile_path", type=click.Path(path_type=Path), required=True)
@click.option("--output", "output_path", type=click.Path(path_type=Path), default=None)
@click.option("--template", "template_path", type=click.Path(path_type=Path), default=None)
@click.option("--overwrite", is_flag=True, help="Overwrite an existing output file.")
@click.option("--dry-run", is_flag=True, help="Parse and map only without writing output.")
@click.option("--validate-only", is_flag=True, help="Validate an existing output workbook.")
@click.option("--verbose", is_flag=True, help="Enable verbose logging.")
@click.option(
    "--dump-model",
    "dump_model_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Write the parsed internal model as JSON.",
)
def design_excel(
    input_path: Path,
    profile_path: Path,
    output_path: Path | None,
    template_path: Path | None,
    overwrite: bool,
    dry_run: bool,
    validate_only: bool,
    verbose: bool,
    dump_model_path: Path | None,
) -> None:
    """Convert a parsed BOM monitoring workbook into a design workbook."""
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)
    if validate_only and output_path is None:
        raise click.ClickException("--validate-only requires --output.")
    try:
        result = run_conversion(
            input_path=input_path,
            profile_path=profile_path,
            output_path=output_path,
            template_path=template_path,
            overwrite=overwrite,
            dry_run=dry_run,
            validate_only=validate_only,
            dump_model=dump_model_path,
        )
    except (DesignExcelError, FileExistsError) as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(json.dumps(result, ensure_ascii=False, indent=2))
