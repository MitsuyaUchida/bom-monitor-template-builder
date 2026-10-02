from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from bom_monitor_builder import __version__
from bom_monitor_builder.cab_excel.cli import parse_input_to_model
from bom_monitor_builder.cab_excel.excel_writer import save_workbook
from bom_monitor_builder.design_excel.profile_loader import load_profile, read_profile_data
from bom_monitor_builder.design_excel.service import run_conversion
from bom_monitor_builder.design_excel.template_generator import profile_allows_generated_template

from .detector import detect_profile
from .exceptions import BuildError, ProfileDetectionError
from .models import BuildResult, DetectionInput
from .output_naming import normalize_output_stem, resolve_build_output_path


def run_build(
    input_path: Path,
    *,
    output_path: Path | None = None,
    profile_value: str | None = None,
    template_path: Path | None = None,
    work_dir: Path | None = None,
    overwrite: bool = False,
    dry_run: bool = False,
    keep_intermediate: bool = False,
    validate_only: bool = False,
    dump_model_path: Path | None = None,
    verbose: bool = False,
) -> BuildResult:
    if dry_run and validate_only:
        raise BuildError("--dry-run and --validate-only cannot be used together.")
    if not input_path.exists():
        raise BuildError(f"Input CAB was not found: {input_path}")

    cleanup_dir: Path | None = None
    resolved_work_dir, cleanup_dir = resolve_work_dir(work_dir, keep_intermediate=keep_intermediate)
    extracted = input_path.is_dir()
    intermediate_path = resolved_work_dir / f"{normalize_output_stem(input_path.stem)}.xlsx"

    if intermediate_path.exists() and not overwrite:
        raise BuildError(f"Intermediate Excel already exists: {intermediate_path}")

    resolved_work_dir.mkdir(parents=True, exist_ok=True)
    parsed, session = parse_input_to_model(
        input_path,
        extracted=extracted,
        keep_extracted=keep_intermediate,
    )
    try:
        save_workbook(parsed, intermediate_path, tool_version=__version__)
    except Exception as exc:
        raise BuildError(f"CAB analysis failed: {exc}") from exc
    finally:
        if not keep_intermediate:
            session.cleanup()

    try:
        detection_input = build_detection_input(parsed)
        profile_path, detection_mode, detection_reasons = resolve_profile_path(
            detection_input,
            profile_value=profile_value,
        )
        profile = load_profile(profile_path, template_override=template_path)
        resolved_template_path = profile["template"].get("resolved_path")
        generated_template = resolved_template_path is None and profile_allows_generated_template(profile)
        if resolved_template_path is None and not generated_template:
            if validate_only:
                raise BuildError("No template is configured for this profile. --validate-only requires a template.")
            if not dry_run:
                profile_id = str(profile.get("profile", {}).get("id", profile_path.stem))
                raise BuildError(
                    "Detected profile:\n"
                    f"  {profile_id}\n\n"
                    "No template is configured for this profile.\n\n"
                    "CAB analysis completed successfully.\n"
                    f"Intermediate Excel: {intermediate_path}"
                )
        output_resolution = resolve_build_output_path(
            requested_output=output_path,
            profile_path=profile_path,
            input_path=input_path,
            overwrite=overwrite,
            dry_run=dry_run,
            validate_only=validate_only,
            verbose=verbose,
        )
        resolved_output_path = output_resolution.path
        if validate_only and not resolved_output_path.exists():
            raise BuildError(f"--validate-only requires an existing output workbook: {resolved_output_path}")
        result = run_conversion(
            input_path=intermediate_path,
            profile_path=profile_path,
            output_path=resolved_output_path,
            template_path=template_path,
            overwrite=overwrite,
            dry_run=dry_run,
            validate_only=validate_only,
            dump_model=dump_model_path,
        )
    except ProfileDetectionError as exc:
        if cleanup_dir is not None:
            cleanup_dir = None
        raise BuildError(f"{exc}\nIntermediate Excel: {intermediate_path}") from exc
    except Exception:
        if cleanup_dir is not None:
            cleanup_dir = None
        raise
    finally:
        if cleanup_dir is not None and cleanup_dir.exists():
            shutil.rmtree(cleanup_dir, ignore_errors=True)

    return BuildResult(
        input_path=input_path,
        output_path=resolved_output_path,
        planned_output=output_resolution.planned,
        intermediate_path=intermediate_path,
        intermediate_kept=keep_intermediate or work_dir is not None,
        profile_path=profile_path,
        profile_id=result["profile_id"],
        template_path=Path(result["template_path"]) if result["template_path"] is not None else None,
        template_source=str(result["template_source"]),
        group_count=int(result["group_count"]),
        monitor_count=int(result["monitor_count"]),
        validation_checks=list(result["validation_checks"]),
        input_unchanged=bool(result["input_unchanged"]),
        template_unchanged=result["template_unchanged"],
        dry_run=bool(result["dry_run"]),
        validate_only=bool(result["validate_only"]),
        dump_model_path=dump_model_path,
        detection_mode=detection_mode,
        detection_reasons=detection_reasons,
        output_resolution_log=output_resolution.log_lines,
    )


def resolve_work_dir(work_dir: Path | None, *, keep_intermediate: bool) -> tuple[Path, Path | None]:
    if work_dir is not None:
        return work_dir, None
    if keep_intermediate:
        return Path("input"), None
    temp_dir = Path(tempfile.mkdtemp(prefix="bom-monitor-build-"))
    return temp_dir, temp_dir


def build_detection_input(parsed: object) -> DetectionInput:
    group_names = [group.raw_values.get("Name", "") for group in parsed.groups]
    monitor_names = [item.raw_values.get("Name", "") for item in parsed.items]
    monitor_types = [item.raw_values.get("Type", "") for item in parsed.items]
    object_names = [item.raw_values.get("ObjectName", "") for item in parsed.items]
    value_names = [item.raw_values.get("ValueName", "") for item in parsed.items]
    return DetectionInput(
        source_path=parsed.source_path,
        source_name=parsed.source_name,
        source_stem=parsed.source_path.stem,
        manifest_product=parsed.manifest.product,
        group_names=sorted({name for name in group_names if isinstance(name, str) and name}),
        monitor_names=sorted({name for name in monitor_names if isinstance(name, str) and name}),
        monitor_types=sorted({name for name in monitor_types if isinstance(name, str) and name}),
        object_names=sorted({name for name in object_names if isinstance(name, str) and name}),
        value_names=sorted({name for name in value_names if isinstance(name, str) and name}),
    )


def resolve_profile_path(
    detection_input: DetectionInput,
    *,
    profile_value: str | None,
) -> tuple[Path, str, list[str]]:
    if profile_value:
        profile_path = resolve_profile_reference(profile_value)
        profile_data = read_profile_data(profile_path)
        profile_id = str(profile_data.get("profile", {}).get("id", profile_path.stem))
        return profile_path, "explicit", [f"profile:{profile_id}"]
    candidate = detect_profile(detection_input)
    return candidate.profile_path, "auto", candidate.reasons


def resolve_profile_reference(profile_value: str) -> Path:
    candidate = Path(profile_value)
    if candidate.exists():
        return candidate
    if candidate.suffix not in {".yml", ".yaml"}:
        by_id = Path("profiles") / f"{profile_value}.yml"
        if by_id.exists():
            return by_id
    raise BuildError(f"Profile not found: {profile_value}")
