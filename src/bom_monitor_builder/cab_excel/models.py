"""Data models for BOM CAB parsing and workbook generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from pathlib import Path
ScalarValue = bool | int | float | Decimal | str | None


@dataclass(slots=True)
class ParseWarning:
    """Non-fatal parsing warning."""

    code: str
    message: str
    path: str | None = None


@dataclass(slots=True)
class ManifestInfo:
    """Parsed MANIFEST.MF content."""

    values: dict[str, str]
    encoding: str

    @property
    def product(self) -> str:
        return self.values.get("Product", "")

    @property
    def export_type(self) -> str:
        return self.values.get("Type", "")

    @property
    def major_version(self) -> str:
        return self.values.get("MajorVersion", "")

    @property
    def minor_version(self) -> str:
        return self.values.get("MinorVersion", "")

    @property
    def bom_version(self) -> str:
        if self.major_version or self.minor_version:
            return f"{self.major_version}.{self.minor_version}"
        return ""


@dataclass(slots=True)
class XmlRecord:
    """Shared XML record state."""

    kind: str
    group_folder: str
    xml_file: str
    raw_values: dict[str, str]
    typed_values: dict[str, ScalarValue]
    root_tag: str

    @property
    def display_name(self) -> str:
        name = self.raw_values.get("Name", "")
        return name if name else self.xml_file


@dataclass(slots=True)
class MonitorGroup(XmlRecord):
    """Monitor group XML record."""


@dataclass(slots=True)
class MonitorItem(XmlRecord):
    """Monitor item XML record."""


@dataclass(slots=True)
class OptionsInfo:
    """Extracted fields from Options."""

    original: str
    retry_interval: int | None = None
    timeout: int | None = None
    execution_type: str | None = None
    script_path: str | None = None
    other_arguments: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ParsedCab:
    """Parsed monitor export state."""

    source_path: Path
    source_name: str
    manifest: ManifestInfo
    groups: list[MonitorGroup]
    items: list[MonitorItem]
    warnings: list[ParseWarning]
    extraction_method: str
    extracted_root: Path
    extracted_root_recorded: bool
    input_sha256: str
    parsed_started_at: datetime
    parsed_completed_at: datetime
    recognized_monitor_types: list[str]
    unknown_comparison_values: list[str]
    unknown_interval_units: list[str]


@dataclass(slots=True)
class WorkbookResult:
    """Workbook generation result."""

    parsed: ParsedCab
    output_path: Path


@dataclass(slots=True)
class CabFileEntry:
    """Single file entry inside a CAB."""

    name: str
    size: int
    offset: int
    folder_index: int


@dataclass(slots=True)
class CabFolderEntry:
    """Single folder stream inside a CAB."""

    data_offset: int
    data_block_count: int
    compression_type: int


@dataclass(slots=True)
class CabArchiveLayout:
    """Parsed CAB archive layout."""

    file_entries: list[CabFileEntry]
    folder_entries: list[CabFolderEntry]
    reserve_per_folder: int
    reserve_per_data: int
