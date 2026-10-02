from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from bom_monitor_builder.design_excel.profile_loader import read_profile_data

from .exceptions import BuildError

INVALID_FILENAME_CHARS = '\\/:*?"<>|'
NUMBERED_OUTPUT_PATTERN = re.compile(r"^(?P<stem>.+)_(?P<index>\d+)$")


@dataclass(slots=True)
class OutputResolution:
    path: Path
    planned: bool = False
    used_profile_default: bool = False
    log_lines: list[str] = field(default_factory=list)


def resolve_build_output_path(
    *,
    input_path: Path,
    profile_path: Path,
    requested_output: Path | None,
    overwrite: bool,
    dry_run: bool,
    validate_only: bool,
    verbose: bool = False,
) -> OutputResolution:
    base_output = requested_output or default_output_path(input_path=input_path, profile_path=profile_path)
    log_lines: list[str] = []

    if validate_only:
        resolved = resolve_validate_only_output(base_output, requested_output=requested_output)
        return OutputResolution(path=resolved, log_lines=log_lines)

    if overwrite:
        return OutputResolution(path=base_output, planned=dry_run, log_lines=log_lines)

    if not base_output.exists():
        return OutputResolution(path=base_output, planned=dry_run, log_lines=log_lines)

    numbered_output = next_available_output_path(base_output, log_lines=log_lines if verbose else None)
    return OutputResolution(path=numbered_output, planned=dry_run, log_lines=log_lines)


def default_output_path(*, input_path: Path, profile_path: Path) -> Path:
    safe_stem = normalize_output_stem(input_path.stem)
    if safe_stem:
        return Path("output") / f"{safe_stem}.xlsx"

    profile_data = read_profile_data(profile_path)
    output_section = profile_data.get("output", {})
    default_filename = output_section.get("default_filename")
    if isinstance(default_filename, str) and default_filename.strip():
        return Path("output") / Path(default_filename.strip()).name

    profile_id = str(profile_data.get("profile", {}).get("id", profile_path.stem))
    return Path("output") / f"{normalize_output_stem(profile_id) or profile_path.stem}.xlsx"


def normalize_output_stem(value: str) -> str:
    sanitized = value
    for char in INVALID_FILENAME_CHARS:
        sanitized = sanitized.replace(char, "_")
    sanitized = re.sub(r"\s+", " ", sanitized).strip(" .")
    return sanitized


def next_available_output_path(path: Path, *, log_lines: list[str] | None = None) -> Path:
    if log_lines is not None:
        log_lines.append(f"Output candidate exists: {path}")
    candidate_index = 1
    while True:
        numbered = path.with_name(f"{path.stem}_{candidate_index:03d}{path.suffix}")
        if log_lines is not None:
            log_lines.append(f"Trying: {numbered}")
        if not numbered.exists():
            if log_lines is not None:
                log_lines.append(f"Selected: {numbered}")
            return numbered
        candidate_index += 1


def resolve_validate_only_output(base_output: Path, *, requested_output: Path | None) -> Path:
    if requested_output is not None:
        return requested_output

    latest = find_latest_existing_output(base_output)
    if latest is None:
        raise BuildError(f"--validate-only requires an existing output workbook: {base_output}")
    return latest


def find_latest_existing_output(base_output: Path) -> Path | None:
    directory = base_output.parent
    suffix = base_output.suffix
    base_name = base_output.stem
    latest: tuple[int, Path] | None = None

    if base_output.exists():
        latest = (0, base_output)

    if not directory.exists():
        return None if latest is None else latest[1]

    for candidate in directory.glob(f"{base_name}_*{suffix}"):
        match = NUMBERED_OUTPUT_PATTERN.match(candidate.stem)
        if match is None or match.group("stem") != base_name:
            continue
        index = int(match.group("index"))
        if latest is None or index > latest[0]:
            latest = (index, candidate)
    return None if latest is None else latest[1]
