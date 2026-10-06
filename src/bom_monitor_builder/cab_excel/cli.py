"""CLI workflow for BOM CAB to Excel generation."""

from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path

import click

from bom_monitor_builder import __version__

from .exceptions import ExcelWriteError, ExtractionError, InputError, ParseError
from .excel_writer import save_workbook
from .extractor import ExtractionSession, prepare_input, sha256_for_path
from .formatter import format_interval, format_threshold
from .manifest import parse_manifest_bytes
from .models import ParsedCab, ParseWarning
from .xml_parser import parse_extracted_action_tree, parse_extracted_monitor_tree

LOGGER = logging.getLogger(__name__)


def _safe_output_name(stem: str) -> str:
    return re.sub(r'[\\\\/:*?"<>|]+', "_", stem)


def _find_manifest_path(extracted_root: Path) -> Path:
    direct = extracted_root / "MANIFEST.MF"
    if direct.exists():
        return direct
    matches = list(extracted_root.rglob("MANIFEST.MF"))
    if not matches:
        raise ParseError("MANIFEST.MF was not found.")
    return matches[0]


def parse_input_to_model(
    input_path: Path,
    *,
    extracted: bool,
    keep_extracted: bool,
) -> tuple[ParsedCab, ExtractionSession]:
    """Parse a CAB file or extracted folder into the shared data model."""
    started = datetime.now().astimezone()
    session, _ = prepare_input(input_path, extracted=extracted)
    warnings: list[ParseWarning] = []
    try:
        manifest_path = _find_manifest_path(session.extracted_root)
        manifest, manifest_warnings = parse_manifest_bytes(manifest_path.read_bytes())
        warnings.extend(manifest_warnings)
        groups, items, xml_warnings = parse_extracted_monitor_tree(session.extracted_root)
        actions = parse_extracted_action_tree(session.extracted_root)
        warnings.extend(xml_warnings)
        recognized_monitor_types = sorted(
            {item.raw_values.get("Type", "") for item in items if item.raw_values.get("Type", "")}
        )
        unknown_comparison_values: set[str] = set()
        unknown_interval_units: set[str] = set()
        for item in items:
            _, unknown_interval = format_interval(
                item.typed_values.get("Interval"),
                item.raw_values.get("IntervalUnit", ""),
            )
            if unknown_interval:
                unknown_interval_units.add(unknown_interval)
            for method_key, value_key in (("CmpMethodY", "CmpValueY"), ("CmpMethodR", "CmpValueR")):
                _, unknown_method = format_threshold(
                    item.typed_values.get(value_key),
                    item.raw_values.get(method_key, ""),
                )
                if unknown_method:
                    unknown_comparison_values.add(unknown_method)
        parsed = ParsedCab(
            source_path=input_path,
            source_name=input_path.name,
            manifest=manifest,
            groups=groups,
            items=items,
            warnings=warnings,
            extraction_method=session.method,
            extracted_root=session.extracted_root,
            extracted_root_recorded=keep_extracted,
            input_sha256=sha256_for_path(input_path),
            parsed_started_at=started,
            parsed_completed_at=datetime.now().astimezone(),
            recognized_monitor_types=recognized_monitor_types,
            unknown_comparison_values=sorted(unknown_comparison_values),
            unknown_interval_units=sorted(unknown_interval_units),
            actions=actions,
        )
        return parsed, session
    except Exception:
        if not keep_extracted:
            session.cleanup()
        raise


def resolve_output_path(input_path: Path, output: Path | None) -> Path:
    """Resolve output workbook path."""
    default_name = f"{_safe_output_name(input_path.stem)}_設定仕様書.xlsx"
    if output is None:
        return input_path.with_name(default_name)
    if output.exists() and output.is_dir():
        return output / default_name
    if output.suffix.lower() == ".xlsx":
        return output
    return output / default_name


def build_workbooks(
    input_path: Path,
    *,
    output: Path | None = None,
    extracted: bool = False,
    keep_extracted: bool = False,
    overwrite: bool = False,
) -> list[Path]:
    """Build one or more workbooks from an input path."""
    if not input_path.exists():
        raise InputError(f"Input path does not exist: {input_path}")

    output_paths: list[Path] = []
    targets: list[tuple[Path, bool]] = []
    if extracted:
        targets.append((input_path, True))
    elif input_path.is_file():
        targets.append((input_path, False))
    elif input_path.is_dir():
        for cab_path in sorted(input_path.rglob("*")):
            if cab_path.is_file() and cab_path.suffix.lower() == ".cab":
                targets.append((cab_path, False))
    else:
        raise InputError(f"Unsupported input path: {input_path}")

    if not targets:
        raise InputError("No CAB files or extracted folders were found.")

    for target_path, target_is_extracted in targets:
        output_path = resolve_output_path(target_path, output)
        if output_path.exists() and not overwrite:
            raise ExcelWriteError(f"Output already exists: {output_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        parsed, session = parse_input_to_model(
            target_path,
            extracted=target_is_extracted,
            keep_extracted=keep_extracted,
        )
        try:
            save_workbook(parsed, output_path, tool_version=__version__)
        except Exception as exc:
            raise ExcelWriteError(str(exc)) from exc
        finally:
            if not keep_extracted:
                session.cleanup()
        output_paths.append(output_path)
    return output_paths


@click.command("cab-excel")
@click.argument("input_path", type=click.Path(path_type=Path))
@click.option("-o", "--output", type=click.Path(path_type=Path), default=None)
@click.option("--extracted", is_flag=True, help="Treat input as an extracted CAB directory.")
@click.option("--keep-extracted", is_flag=True, help="Keep temporary extracted files.")
@click.option("--overwrite", is_flag=True, help="Overwrite existing workbook files.")
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    default="INFO",
    show_default=True,
)
@click.version_option(version=__version__)
def cab_excel(
    input_path: Path,
    output: Path | None,
    extracted: bool,
    keep_extracted: bool,
    overwrite: bool,
    log_level: str,
) -> None:
    """Generate BOM monitor specification workbooks from CAB exports."""
    logging.basicConfig(level=getattr(logging, log_level.upper()))
    try:
        output_paths = build_workbooks(
            input_path,
            output=output,
            extracted=extracted,
            keep_extracted=keep_extracted,
            overwrite=overwrite,
        )
    except (InputError, ExtractionError, ParseError, ExcelWriteError) as exc:
        raise click.ClickException(str(exc)) from exc
    for output_path in output_paths:
        click.echo(str(output_path))
