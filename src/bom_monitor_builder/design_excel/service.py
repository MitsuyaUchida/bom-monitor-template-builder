from __future__ import annotations

import hashlib
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .exceptions import DesignExcelError
from .mapper import build_render_plan, model_to_json
from .parser import parse_workbook
from .profile_loader import load_profile
from .template_generator import cleanup_generated_template, create_generated_render_plan, profile_allows_generated_template
from .validator import validate_output
from .writer import write_render_plan


def run_conversion(
    input_path: Path,
    profile_path: Path,
    output_path: Path | None,
    *,
    template_path: Path | None = None,
    overwrite: bool = False,
    dry_run: bool = False,
    validate_only: bool = False,
    dump_model: Path | None = None,
) -> dict[str, Any]:
    resolved_output_path = resolve_output_path(output_path, input_path, profile_path)
    if resolved_output_path.exists() and not overwrite and not validate_only and not dry_run:
        raise FileExistsError(f"Output already exists: {output_path}")
    profile = load_profile(profile_path, template_override=template_path)
    resolved_template_path = profile["template"].get("resolved_path")
    generated_template = resolved_template_path is None and profile_allows_generated_template(profile)
    if resolved_template_path is not None and not resolved_template_path.exists() and not dry_run:
        raise DesignExcelError(f"Template not found: {resolved_template_path}")
    template_hash_before = (
        sha256_for_file(resolved_template_path)
        if resolved_template_path is not None and resolved_template_path.exists()
        else None
    )
    input_hash_before = sha256_for_file(input_path)
    model = parse_workbook(input_path, profile)
    if dump_model:
        dump_model.write_text(
            model_to_json(
                model,
                list(profile.get("security", {}).get("secret_patterns", [])),
            ),
            encoding="utf-8",
        )
    if resolved_template_path is None and not generated_template:
        if validate_only:
            raise DesignExcelError("No template is configured for this profile. --validate-only requires a template.")
        if not dry_run:
            raise DesignExcelError("No template is configured for this profile.")
        input_hash_after = sha256_for_file(input_path)
        return {
            "profile_id": profile["profile"]["id"],
            "input_path": str(input_path),
            "output_path": str(resolved_output_path),
            "template_path": None,
            "template_source": "missing",
            "monitor_count": len(model.items),
            "group_count": len(model.groups),
            "validation_checks": [],
            "input_unchanged": input_hash_before == input_hash_after,
            "template_unchanged": None,
            "dry_run": dry_run,
            "validate_only": validate_only,
        }
    plan = (
        create_generated_render_plan(model, profile, resolved_output_path)
        if generated_template
        else build_render_plan(model, profile, resolved_output_path)
    )
    report = None
    try:
        if not dry_run and not validate_only:
            write_render_plan(plan)
            report = validate_output(resolved_output_path, plan.template_path, input_path, plan)
        elif validate_only:
            report = validate_output(resolved_output_path, plan.template_path, input_path, plan)
        template_hash_after = (
            sha256_for_file(resolved_template_path)
            if resolved_template_path is not None and resolved_template_path.exists()
            else None
        )
        input_hash_after = sha256_for_file(input_path)
        return {
            "profile_id": profile["profile"]["id"],
            "input_path": str(input_path),
            "output_path": str(resolved_output_path),
            "template_path": None if generated_template else (str(plan.template_path) if plan.template_path is not None else None),
            "template_source": plan.template_source,
            "monitor_count": len(model.items),
            "group_count": len(model.groups),
            "validation_checks": [] if report is None else report.checks,
            "input_unchanged": input_hash_before == input_hash_after,
            "template_unchanged": (
                template_hash_before == template_hash_after
                if template_hash_before is not None
                else (True if generated_template else None)
            ),
            "dry_run": dry_run,
            "validate_only": validate_only,
        }
    finally:
        if generated_template:
            cleanup_generated_template(plan.template_path)


def sha256_for_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_output_path(
    output_path: Path | None,
    input_path: Path,
    profile_path: Path,
) -> Path:
    if output_path is not None:
        return output_path
    return Path("output") / f"{input_path.stem}_{profile_path.stem}.xlsx"
