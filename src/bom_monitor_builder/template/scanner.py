from __future__ import annotations

import hashlib
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Sequence

import yaml  # type: ignore[import-untyped]

from bom_monitor_builder.knowledge.yaml_tools import detect_encoding
from bom_monitor_builder.template.category import build_category_inventory, parse_category_directory
from bom_monitor_builder.template.inventory import (
    build_extension_inventory,
    build_template_inventory,
)
from bom_monitor_builder.template.models import (
    AutoTemplateRecord,
    CategoryInventory,
    DirectoryRecord,
    FileRecord,
    ScanResult,
    ScanSummary,
)
from bom_monitor_builder.template.tree import build_directory_tree

IMAGE_EXTENSIONS = {
    ".bmp",
    ".gif",
    ".ico",
    ".jpeg",
    ".jpg",
    ".png",
    ".svg",
    ".tif",
    ".tiff",
    ".webp",
}


def scan_template_data(source_root: Path, output_root: Path) -> ScanResult:
    resolved_source = source_root.resolve()
    validate_source_directory(resolved_source)

    directories = collect_directories(resolved_source)
    files = collect_files(resolved_source)
    autotemplate = inspect_autotemplate(resolved_source)
    categories = build_category_inventory(files)
    templates = build_template_inventory(files)
    extensions = build_extension_inventory(files)
    directory_tree = build_directory_tree(resolved_source)
    summary = build_summary(
        source_root=resolved_source,
        output_root=output_root.resolve(),
        directories=directories,
        files=files,
        categories=categories,
        autotemplate=autotemplate,
    )

    return ScanResult(
        summary=summary,
        directories=directories,
        directory_tree=directory_tree,
        files=files,
        categories=categories,
        templates=templates,
        extensions=extensions,
    )


def validate_source_directory(source_root: Path) -> None:
    if not source_root.exists():
        raise ValueError(f"Source path does not exist: {source_root}")
    if not source_root.is_dir():
        raise ValueError(f"Source path is not a directory: {source_root}")
    if not os.access(source_root, os.R_OK):
        raise ValueError(f"Source path is not readable: {source_root}")


def collect_directories(source_root: Path) -> list[DirectoryRecord]:
    rows: list[DirectoryRecord] = []
    for dir_path, dir_names, _ in os.walk(source_root, topdown=True, followlinks=False):
        current = Path(dir_path)
        dir_names[:] = sorted(
            [name for name in dir_names if not (current / name).is_symlink()],
            key=str.casefold,
        )
        if current == source_root:
            continue
        relative = current.relative_to(source_root).as_posix()
        parts = current.relative_to(source_root).parts
        parent_path = None if len(parts) == 1 else Path(*parts[:-1]).as_posix()
        rows.append(
            DirectoryRecord(
                path=relative,
                name=current.name,
                depth=len(parts),
                parent_path=parent_path,
            )
        )
    return sorted(rows, key=lambda entry: entry.path)


def collect_files(source_root: Path) -> list[FileRecord]:
    rows: list[FileRecord] = []
    for dir_path, dir_names, file_names in os.walk(source_root, topdown=True, followlinks=False):
        current = Path(dir_path)
        dir_names[:] = sorted(
            [name for name in dir_names if not (current / name).is_symlink()],
            key=str.casefold,
        )
        for file_name in sorted(file_names, key=str.casefold):
            file_path = current / file_name
            if file_path.is_symlink():
                continue
            rows.append(build_file_record(file_path, source_root))
    return sorted(rows, key=lambda entry: entry.relative_path)


def build_file_record(file_path: Path, source_root: Path) -> FileRecord:
    relative_path = file_path.relative_to(source_root).as_posix()
    raw_bytes = file_path.read_bytes()
    stat_result = file_path.stat()
    parts = file_path.relative_to(source_root).parts
    category_directory = parts[0] if len(parts) > 1 else ""
    category_id, category_name = parse_category_directory(category_directory) if category_directory else (
        None,
        None,
    )
    return FileRecord(
        relative_path=relative_path,
        category_id=category_id,
        category_name=category_name,
        directory=category_directory,
        file_name=file_path.name,
        template_name_candidate=file_path.stem,
        extension=file_path.suffix.lower(),
        file_type=classify_file_type(file_path),
        size=stat_result.st_size,
        modified_at=datetime.fromtimestamp(stat_result.st_mtime, tz=UTC).isoformat(),
        sha256=hashlib.sha256(raw_bytes).hexdigest(),
        depth=len(parts),
        is_japanese_named=contains_non_ascii(file_path.name),
    )


def inspect_autotemplate(source_root: Path) -> AutoTemplateRecord:
    path = source_root / "AutoTemplate.yml"
    if not path.exists():
        return AutoTemplateRecord(
            exists=False,
            relative_path=None,
            size=None,
            sha256=None,
            modified_at=None,
            encoding=None,
            yaml_loadable=False,
            yaml_error=None,
        )

    raw_bytes = path.read_bytes()
    stat_result = path.stat()
    encoding = detect_encoding(raw_bytes)
    yaml_error: str | None = None
    yaml_loadable = False
    try:
        yaml.safe_load(raw_bytes.decode(encoding))
        yaml_loadable = True
    except (UnicodeDecodeError, yaml.YAMLError) as error:
        yaml_error = str(error)

    return AutoTemplateRecord(
        exists=True,
        relative_path=path.relative_to(source_root).as_posix(),
        size=stat_result.st_size,
        sha256=hashlib.sha256(raw_bytes).hexdigest(),
        modified_at=datetime.fromtimestamp(stat_result.st_mtime, tz=UTC).isoformat(),
        encoding=encoding,
        yaml_loadable=yaml_loadable,
        yaml_error=yaml_error,
    )


def build_summary(
    source_root: Path,
    output_root: Path,
    directories: list[DirectoryRecord],
    files: list[FileRecord],
    categories: Sequence[CategoryInventory],
    autotemplate: AutoTemplateRecord,
) -> ScanSummary:
    max_depth = max([0, *[entry.depth for entry in directories], *[entry.depth for entry in files]])
    cab_count = sum(1 for entry in files if entry.file_type == "cab")
    html_count = sum(1 for entry in files if entry.file_type == "html")
    yaml_count = sum(1 for entry in files if entry.file_type == "yaml")
    image_count = sum(1 for entry in files if entry.file_type == "image")
    other_file_count = sum(1 for entry in files if entry.file_type == "other")
    japanese_filename_count = sum(1 for entry in files if entry.is_japanese_named)
    return ScanSummary(
        source=str(source_root),
        output=str(output_root),
        directory_count=len(directories),
        file_count=len(files),
        category_count=len(categories),
        cab_count=cab_count,
        html_count=html_count,
        yaml_count=yaml_count,
        image_count=image_count,
        other_file_count=other_file_count,
        japanese_filename_count=japanese_filename_count,
        max_depth=max_depth,
        autotemplate=autotemplate,
    )


def classify_file_type(path: Path) -> str:
    extension = path.suffix.lower()
    if extension == ".cab":
        return "cab"
    if extension in {".htm", ".html"}:
        return "html"
    if extension in {".yaml", ".yml"}:
        return "yaml"
    if extension in IMAGE_EXTENSIONS:
        return "image"
    return "other"


def contains_non_ascii(value: str) -> bool:
    return any(ord(character) > 127 for character in value)
