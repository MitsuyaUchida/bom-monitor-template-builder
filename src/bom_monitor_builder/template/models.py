from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class DirectoryRecord:
    path: str
    name: str
    depth: int
    parent_path: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class FileRecord:
    relative_path: str
    category_id: str | None
    category_name: str | None
    directory: str
    file_name: str
    template_name_candidate: str
    extension: str
    file_type: str
    size: int
    modified_at: str
    sha256: str
    depth: int
    is_japanese_named: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CategoryInventory:
    category_id: str | None
    category_name: str
    directory: str
    file_count: int
    cab_count: int
    html_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class TemplateInventory:
    category_id: str | None
    category_name: str
    directory: str
    template_name_candidate: str
    cab: str | None
    html: str | None
    same_name_pair: bool
    html_only: bool
    cab_only: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ExtensionInventory:
    extension: str
    file_count: int

    def to_dict(self) -> dict[str, int | str]:
        return asdict(self)


@dataclass(slots=True)
class AutoTemplateRecord:
    exists: bool
    relative_path: str | None
    size: int | None
    sha256: str | None
    modified_at: str | None
    encoding: str | None
    yaml_loadable: bool
    yaml_error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ScanSummary:
    source: str
    output: str
    directory_count: int
    file_count: int
    category_count: int
    cab_count: int
    html_count: int
    yaml_count: int
    image_count: int
    other_file_count: int
    japanese_filename_count: int
    max_depth: int
    autotemplate: AutoTemplateRecord
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["autotemplate"] = self.autotemplate.to_dict()
        return payload


@dataclass(slots=True)
class ScanResult:
    summary: ScanSummary
    directories: list[DirectoryRecord]
    directory_tree: dict[str, Any]
    files: list[FileRecord]
    categories: list[CategoryInventory]
    templates: list[TemplateInventory]
    extensions: list[ExtensionInventory]
