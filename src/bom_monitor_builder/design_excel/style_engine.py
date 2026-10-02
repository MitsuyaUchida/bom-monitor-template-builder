from __future__ import annotations

from copy import copy
from typing import Any

from openpyxl.styles import Alignment, Border  # type: ignore[import-untyped]
from openpyxl.worksheet.worksheet import Worksheet  # type: ignore[import-untyped]

from .layout_engine import RowContext, row_type_for_context
from .models import RenderTable
from .standard_style import (
    monitor_setting_danger_style,
    monitor_setting_disabled_style,
    monitor_setting_group_style,
    monitor_setting_warning_style,
)


def apply_table_styles(worksheet: Worksheet, table: RenderTable, contexts: list[RowContext]) -> None:
    for context in contexts:
        apply_row_style(worksheet, table, context)
    apply_column_widths(worksheet, table)


def apply_row_style(worksheet: Worksheet, table: RenderTable, context: RowContext) -> None:
    source_row = resolve_style_source_row(worksheet, table, context)
    if source_row is None:
        return
    target_height = worksheet.row_dimensions[source_row].height
    if target_height is not None:
        worksheet.row_dimensions[context.row].height = resolve_row_height(worksheet, table, context, target_height)
    for column_name in table.managed_columns.values():
        source_cell = worksheet[f"{column_name}{source_row}"]
        target_cell = worksheet[f"{column_name}{context.row}"]
        if source_cell.has_style:
            target_cell._style = copy(source_cell._style)  # noqa: SLF001
        target_cell.font = copy(source_cell.font)
        target_cell.fill = copy(source_cell.fill)
        target_cell.border = resolve_border(source_cell.border, table, context, column_name)
        target_cell.alignment = resolve_alignment(source_cell.alignment, table, column_name)
        target_cell.number_format = source_cell.number_format
        target_cell.protection = copy(source_cell.protection)
    if getattr(table, "name", "") == "monitor_settings":
        apply_generated_semantic_style(worksheet, table, context)


def resolve_style_source_row(worksheet: Worksheet, table: RenderTable, context: RowContext) -> int | None:
    style_sources = table.layout.get("style_sources", {})
    if not isinstance(style_sources, dict):
        style_sources = {}
    if context.is_table_last and "table_last" in style_sources:
        return int(style_sources["table_last"])
    row_type = context.row_type
    if row_type in style_sources:
        return int(style_sources[row_type])
    if row_type == "single_row_group" and "group_first" in style_sources:
        return int(style_sources["group_first"])
    return table.template_row if worksheet.max_row >= table.template_row else None


def resolve_alignment(base_alignment: Alignment, table: RenderTable, column_name: str) -> Alignment:
    overrides = table.format_rules.get("alignment", {})
    column_rule = overrides.get(column_name)
    if not isinstance(column_rule, dict):
        return copy(base_alignment)
    return Alignment(
        horizontal=column_rule.get("horizontal", base_alignment.horizontal),
        vertical=column_rule.get("vertical", base_alignment.vertical),
        text_rotation=base_alignment.text_rotation,
        wrap_text=column_rule.get("wrap_text", base_alignment.wrap_text),
        shrink_to_fit=base_alignment.shrink_to_fit,
        indent=column_rule.get("indent", base_alignment.indent),
    )


def resolve_border(base_border: Border, table: RenderTable, context: RowContext, column_name: str) -> Border:
    border_rules = table.format_rules.get("borders", {})
    column_rules = border_rules.get("columns", {})
    rule = border_rules.get(row_type_for_context(context), {})
    column_rule = column_rules.get(column_name, {})
    if not isinstance(rule, dict):
        rule = {}
    if not isinstance(column_rule, dict):
        column_rule = {}
    if not rule and not column_rule:
        return copy(base_border)
    return Border(
        left=base_border.left if "left" not in column_rule and "left" not in rule else copy_side(base_border.left, column_rule.get("left", rule.get("left"))),
        right=base_border.right if "right" not in column_rule and "right" not in rule else copy_side(base_border.right, column_rule.get("right", rule.get("right"))),
        top=base_border.top if "top" not in column_rule and "top" not in rule else copy_side(base_border.top, column_rule.get("top", rule.get("top"))),
        bottom=base_border.bottom if "bottom" not in column_rule and "bottom" not in rule else copy_side(base_border.bottom, column_rule.get("bottom", rule.get("bottom"))),
        diagonal=copy(base_border.diagonal),
        diagonalDown=base_border.diagonalDown,
        diagonalUp=base_border.diagonalUp,
        outline=base_border.outline,
        vertical=copy(base_border.vertical),
        horizontal=copy(base_border.horizontal),
    )


def copy_side(side: Any, style: str | None) -> Any:
    copied = copy(side)
    copied.style = style
    return copied


def resolve_row_height(worksheet: Worksheet, table: RenderTable, context: RowContext, default_height: float) -> float:
    row_height_rules = table.format_rules.get("row_height", {})
    if not isinstance(row_height_rules, dict):
        return default_height
    if "default" in row_height_rules:
        default_height = float(row_height_rules["default"])
    thresholds = row_height_rules.get("thresholds")
    if not isinstance(thresholds, list):
        return default_height
    wrap_columns = [
        column_name
        for column_name, rule in table.format_rules.get("alignment", {}).items()
        if isinstance(rule, dict) and rule.get("wrap_text")
    ]
    if not wrap_columns:
        return default_height
    max_length = max(
        len(str(worksheet[f"{column_name}{context.row}"].value))
        for column_name in wrap_columns
        if worksheet[f"{column_name}{context.row}"].value not in (None, "")
    ) if any(worksheet[f"{column_name}{context.row}"].value not in (None, "") for column_name in wrap_columns) else 0
    for threshold in thresholds:
        if max_length <= int(threshold["max"]):
            return float(threshold["height"])
    return float(row_height_rules.get("fallback", default_height))


def apply_column_widths(worksheet: Worksheet, table: RenderTable) -> None:
    widths = table.format_rules.get("column_widths", {})
    if not isinstance(widths, dict):
        return
    for column_name, width in widths.items():
        worksheet.column_dimensions[column_name].width = float(width)


def expected_alignment(table: RenderTable, worksheet: Worksheet, context: RowContext, column_name: str) -> Alignment | None:
    source_row = resolve_style_source_row(worksheet, table, context)
    if source_row is None:
        return None
    return resolve_alignment(worksheet[f"{column_name}{source_row}"].alignment, table, column_name)


def expected_border(table: RenderTable, worksheet: Worksheet, context: RowContext, column_name: str) -> Border | None:
    source_row = resolve_style_source_row(worksheet, table, context)
    if source_row is None:
        return None
    return resolve_border(worksheet[f"{column_name}{source_row}"].border, table, context, column_name)


def expected_row_height(table: RenderTable, worksheet: Worksheet, context: RowContext) -> float | None:
    source_row = resolve_style_source_row(worksheet, table, context)
    if source_row is None:
        return None
    source_height = worksheet.row_dimensions[source_row].height
    if source_height is None:
        return None
    return resolve_row_height(worksheet, table, context, float(source_height))


def apply_generated_semantic_style(worksheet: Worksheet, table: RenderTable, context: RowContext) -> None:
    reverse_columns = {column_name: field_name for field_name, column_name in table.managed_columns.items()}
    enabled_column = table.managed_columns.get("enabled")
    enabled_value = worksheet[f"{enabled_column}{context.row}"].value if enabled_column is not None else None
    disabled = str(enabled_value).strip() == "無効"
    for column_name in table.managed_columns.values():
        field_name = reverse_columns.get(column_name, "")
        cell = worksheet[f"{column_name}{context.row}"]
        if disabled:
            style = monitor_setting_disabled_style(cell.alignment, top_style=None, bottom_style=None)
            cell.fill = copy(style.fill)
            cell.font = copy(style.font)
            continue
        if context.is_group_first:
            style = monitor_setting_group_style(horizontal=cell.alignment.horizontal or "left", wrap_text=bool(cell.alignment.wrap_text))
            cell.fill = copy(style.fill)
        if field_name in {"warning_condition"}:
            style = monitor_setting_warning_style(cell.alignment)
            cell.fill = copy(style.fill)
        elif field_name in {"critical_condition"}:
            style = monitor_setting_danger_style(cell.alignment)
            cell.fill = copy(style.fill)
