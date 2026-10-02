from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class AutoTemplateEntry:
    entry_index: int
    type: str
    names: list[str]
    templatepaths: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CabInternalFile:
    name: str
    size: int
    category: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CabAnalysis:
    relative_path: str
    file_format: str
    header_signature: str
    header_hex: str
    file_size: int
    folder_count: int | str
    file_count: int | str
    cab_version: str | None
    compression_format: str
    extractable: bool
    extraction_status: str
    internal_files: list[CabInternalFile]
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["internal_files"] = [entry.to_dict() for entry in self.internal_files]
        return payload


@dataclass(slots=True)
class HtmlMonitorItem:
    name: str
    description: str
    monitor_type: str
    monitoring_target: str
    monitoring_item: str
    service: str
    event_log: str
    event_id: str
    performance_counter: str
    threshold: str
    interval: str
    enabled: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class HtmlAnalysis:
    relative_path: str
    title: str
    product_name: str
    description: str
    monitoring_target: list[str]
    monitoring_items: list[str]
    services: list[str]
    event_logs: list[str]
    event_ids: list[str]
    performance_counters: list[str]
    thresholds: list[str]
    monitoring_intervals: list[str]
    supported_os: str
    related_cab: str
    image_references: list[str]
    monitor_items: list[HtmlMonitorItem]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["monitor_items"] = [entry.to_dict() for entry in self.monitor_items]
        return payload


@dataclass(slots=True)
class MappingRecord:
    template_key: str
    cab: str
    html: str
    images: list[str]
    autotemplate_refs: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SampleComparisonRecord:
    sample_type: str
    html: str
    cab: str
    monitor_item_count: int | str
    services: list[str]
    event_logs: list[str]
    performance_counters: list[str]
    common_fields: list[str]
    variable_fields: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class RequirementSummary:
    cab_required_fields: list[str]
    html_required_fields: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AnalysisResult:
    source: str
    output: str
    template_inventory: dict[str, Any]
    autotemplate: dict[str, Any]
    cab_structure: dict[str, Any]
    html_analysis: dict[str, Any]
    mapping: dict[str, Any]
    sample_comparison: list[SampleComparisonRecord]
    requirements: RequirementSummary
