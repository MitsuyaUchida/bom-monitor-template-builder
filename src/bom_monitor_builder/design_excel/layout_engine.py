from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import RenderTable, WorkbookModel


@dataclass(slots=True)
class RowContext:
    row: int
    group_id: str | None
    group_name: str | None
    monitor_id: str
    group_index: int
    monitor_index_in_group: int
    group_size: int
    is_group_first: bool
    is_group_last: bool
    is_table_last: bool

    @property
    def row_type(self) -> str:
        if self.group_size == 1:
            return "single_row_group"
        if self.is_group_first:
            return "group_first"
        if self.is_group_last:
            return "group_last"
        return "group_middle"


def build_row_contexts(model: WorkbookModel, table: RenderTable) -> list[RowContext]:
    contexts: list[RowContext] = []
    index = 0
    groups = group_items(model)
    for group_index, items in enumerate(groups):
        group_size = len(items)
        for monitor_index_in_group, item in enumerate(items):
            row = table.start_row + index
            context = RowContext(
                row=row,
                group_id=item.group_id,
                group_name=item.group_name,
                monitor_id=item.monitor_id,
                group_index=group_index,
                monitor_index_in_group=monitor_index_in_group,
                group_size=group_size,
                is_group_first=monitor_index_in_group == 0,
                is_group_last=monitor_index_in_group == group_size - 1,
                is_table_last=index == len(model.items) - 1,
            )
            contexts.append(context)
            index += 1
    return contexts


def group_items(model: WorkbookModel) -> list[list[Any]]:
    grouped: list[list[Any]] = []
    current_group: list[Any] = []
    current_key: tuple[str | None, str | None] | None = None
    for item in model.items:
        key = (item.group_id, item.group_name)
        if current_key is None or key == current_key:
            current_group.append(item)
            current_key = key
            continue
        grouped.append(current_group)
        current_group = [item]
        current_key = key
    if current_group:
        grouped.append(current_group)
    return grouped


def expected_merge_ranges(table: RenderTable, contexts: list[RowContext]) -> dict[str, list[str]]:
    group_merge = table.layout.get("group_merge", {})
    if not isinstance(group_merge, dict) or not group_merge.get("enabled"):
        return {}
    requested_columns = list(group_merge.get("columns", []))
    merge_ranges: dict[str, list[str]] = {column: [] for column in requested_columns}
    for column in requested_columns:
        for context in contexts:
            if not context.is_group_first:
                continue
            if context.group_size <= 1:
                continue
            end_row = context.row + context.group_size - 1
            merge_ranges[column].append(f"{column}{context.row}:{column}{end_row}")
    return merge_ranges


def row_type_for_context(context: RowContext) -> str:
    if context.is_table_last:
        return "table_last"
    return context.row_type
