from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class MonitorGroup:
    group_id: str
    group_name: str
    enabled: str | bool | None
    comment: str | None
    source_row: int
    raw_values: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class MonitorDetail:
    key: str
    value: Any
    source_row: int


@dataclass(slots=True)
class MonitorItem:
    group_id: str | None
    group_name: str | None
    monitor_id: str
    monitor_name: str
    monitor_type: str | None
    enabled: str | bool | None
    interval: str | None
    warning_condition: str | None
    critical_condition: str | None
    comment: str | None
    details: dict[str, Any] = field(default_factory=dict)
    source_sheet: str = ""
    source_row: int = 0
    raw_values: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ActionSetting:
    values: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class EnvironmentSetting:
    values: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class WorkbookModel:
    source_path: Path
    source_name: str
    groups: list[MonitorGroup]
    items: list[MonitorItem]
    details: dict[str, dict[str, Any]] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    extensions: dict[str, Any] = field(default_factory=dict)
    raw_sections: dict[str, list[dict[str, Any]]] = field(default_factory=dict)


@dataclass(slots=True)
class RenderRow:
    values: dict[str, Any]
    source_monitor_id: str


@dataclass(slots=True)
class RenderTable:
    name: str
    sheet: str
    start_row: int
    template_row: int
    rows: list[RenderRow]
    managed_columns: dict[str, str] = field(default_factory=dict)
    group_merge_fields: list[str] = field(default_factory=list)
    layout: dict[str, Any] = field(default_factory=dict)
    format_rules: dict[str, Any] = field(default_factory=dict)
    group_labels_first_row_only: bool = False
    clear_existing_data: bool = False
    trim_unused_rows: bool = True
    unused_rows_mode: str = "clear_values"
    template_data_end_row: int | None = None
    clear_existing_rows: bool = False
    reuse_existing_rows: bool = False


@dataclass(slots=True)
class RenderPlan:
    output_path: Path
    template_path: Path | None
    cells: dict[str, dict[str, Any]]
    tables: list[RenderTable]
    model: WorkbookModel
    profile: dict[str, Any]
    template_source: str = "profile_template"


@dataclass(slots=True)
class ValidationReport:
    output_path: Path
    checks: list[str]
