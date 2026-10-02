from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .exceptions import MappingError
from .condition_display import get_condition_display_name
from .models import RenderPlan, RenderRow, RenderTable, WorkbookModel
from .monitor_type_display import get_monitor_type_display_name
from .normalizers import NORMALIZERS
from .security import DEFAULT_SECRET_PATTERNS, mask_secrets_in_mapping


def build_render_plan(
    model: WorkbookModel,
    profile: dict[str, Any],
    output_path: Path,
) -> RenderPlan:
    transformed_rows = [build_output_row(item, model, profile) for item in model.items]
    tables = []
    monitor_table_defaults = profile["output"].get("monitor_table", {})
    for table_name, config in profile["output"].get("tables", {}).items():
        rows = [
            RenderRow(
                values=build_table_row(row_values, config["columns"]),
                source_monitor_id=row_values["monitor_id"],
            )
            for row_values in transformed_rows
        ]
        managed_config = resolve_managed_table_config(table_name, config, monitor_table_defaults)
        tables.append(
            RenderTable(
                name=table_name,
                sheet=config["sheet"],
                start_row=int(config["start_row"]),
                template_row=int(config["template_row"]),
                rows=rows,
                managed_columns=managed_config["managed_columns"],
                group_merge_fields=managed_config["group_merge_fields"],
                layout=managed_config["layout"],
                format_rules=managed_config["format_rules"],
                group_labels_first_row_only=managed_config["group_labels_first_row_only"],
                clear_existing_data=managed_config["clear_existing_data"],
                trim_unused_rows=managed_config["trim_unused_rows"],
                unused_rows_mode=managed_config["unused_rows_mode"],
                template_data_end_row=managed_config["template_data_end_row"],
                clear_existing_rows=bool(config.get("clear_existing_rows", False)),
                reuse_existing_rows=bool(config.get("reuse_existing_rows", False)),
            )
        )
    cells = {}
    for name, config in profile["output"].get("cells", {}).items():
        resolved = resolve_cell_config(config, model, profile)
        if resolved is None:
            continue
        cells[name] = resolved
    return RenderPlan(
        output_path=output_path,
        template_path=profile["template"].get("resolved_path"),
        cells=cells,
        tables=tables,
        model=model,
        profile=profile,
    )


def build_output_row(item: Any, model: WorkbookModel, profile: dict[str, Any]) -> dict[str, Any]:
    defaults = profile["transform"].get("defaults", {})
    replacements = profile["transform"].get("replacements", {})
    normalizers = profile["transform"].get("normalizers", {})
    row: dict[str, Any] = {
        "group_id": item.group_id,
        "group_name": item.group_name,
        "monitor_id": item.monitor_id,
        "monitor_name": item.monitor_name,
        "monitor_type": item.monitor_type,
        "enabled": item.enabled,
        "interval": item.interval,
        "warning_condition": item.warning_condition,
        "critical_condition": item.critical_condition,
        "comment": item.comment,
        "source_name": model.source_name,
    }
    row.update(item.raw_values)
    row.update(item.details)
    for key, value in defaults.items():
        row.setdefault(key, value)
    for field_name, mapping in replacements.items():
        current = row.get(field_name)
        if current in mapping:
            row[field_name] = mapping[current]
    for field_name, functions in normalizers.items():
        current = row.get(field_name)
        for function_name in functions:
            function = NORMALIZERS.get(function_name)
            if function is None:
                raise MappingError(f"Unknown normalizer: {function_name}")
            current = function(current)
        row[field_name] = current
    derived = profile["transform"].get("derived_fields", {})
    for key, expression in derived.items():
        row[key] = render_template_value(expression, model, profile, row)
    apply_row_rules(row, model, profile)
    secret_patterns = profile.get("security", {}).get("secret_patterns", DEFAULT_SECRET_PATTERNS)
    return mask_secrets_in_mapping(row, list(secret_patterns))


def build_table_row(values: dict[str, Any], columns: dict[str, str]) -> dict[str, Any]:
    row: dict[str, Any] = {}
    for column, field_name in columns.items():
        value = values.get(field_name)
        if field_name == "monitor_type":
            value = get_monitor_type_display_name(value)
        elif field_name in {"warning_condition", "critical_condition"}:
            value = get_condition_display_name(value)
        row[column] = value
    return row


def resolve_managed_table_config(
    table_name: str,
    table_config: dict[str, Any],
    monitor_table_defaults: dict[str, Any],
) -> dict[str, Any]:
    combined: dict[str, Any] = {}
    if isinstance(monitor_table_defaults, dict):
        target_table = monitor_table_defaults.get("table")
        if target_table in (None, table_name):
            combined.update(monitor_table_defaults)
    combined.update(table_config.get("monitor_table", {}))

    managed_columns = combined.get("managed_columns")
    if not isinstance(managed_columns, dict) or not managed_columns:
        managed_columns = {field_name: column for column, field_name in table_config["columns"].items()}

    return {
        "managed_columns": managed_columns,
        "group_merge_fields": list(combined.get("group_merge_fields", [])),
        "layout": dict(combined.get("layout", {})),
        "format_rules": dict(combined.get("format", {})),
        "group_labels_first_row_only": bool(combined.get("group_labels", {}).get("first_row_only", False)),
        "clear_existing_data": bool(combined.get("clear_existing_data", True)),
        "trim_unused_rows": bool(combined.get("trim_unused_rows", True)),
        "unused_rows_mode": str(combined.get("unused_rows", {}).get("mode", "clear_values")),
        "template_data_end_row": (
            int(combined["template_data_end_row"])
            if combined.get("template_data_end_row") is not None
            else None
        ),
    }


def render_template_value(
    template: Any,
    model: WorkbookModel,
    profile: dict[str, Any],
    row: dict[str, Any] | None = None,
) -> Any:
    if not isinstance(template, str):
        return template
    context = {
        "source_name": model.source_name,
        "source_stem": model.source_path.stem,
        "profile_id": profile["profile"].get("id"),
        "monitor_count": len(model.items),
        "group_count": len(model.groups),
    }
    if row:
        context.update({key: "" if value is None else value for key, value in row.items()})
    value = template
    for key, item in context.items():
        value = value.replace(f"{{{{ {key} }}}}", str(item))
    return value


def resolve_cell_config(
    config: dict[str, Any],
    model: WorkbookModel,
    profile: dict[str, Any],
) -> dict[str, Any] | None:
    context = build_render_context(model, profile)
    conditions = config.get("when", {})
    if isinstance(conditions, dict) and conditions and not row_rule_matches(context, conditions):
        if config.get("clear_if_unresolved"):
            return {
                "sheet": config["sheet"],
                "cell": config["cell"],
                "value": None,
            }
        return None
    value = render_template_value(config.get("value"), model, profile)
    if value in (None, "") and config.get("clear_if_unresolved"):
        value = None
    return {
        "sheet": config["sheet"],
        "cell": config["cell"],
        "value": value,
    }


def build_render_context(model: WorkbookModel, profile: dict[str, Any]) -> dict[str, Any]:
    context = {
        "source_name": model.source_name,
        "source_stem": model.source_path.stem,
        "profile_id": profile["profile"].get("id"),
        "monitor_count": len(model.items),
        "group_count": len(model.groups),
    }
    context.update(model.metadata)
    return context


def apply_row_rules(row: dict[str, Any], model: WorkbookModel, profile: dict[str, Any]) -> None:
    for rule in profile["transform"].get("row_rules", []):
        if not row_rule_matches(row, rule.get("when", {})):
            continue
        for key, value in rule.get("set", {}).items():
            row[key] = render_template_value(value, model, profile, row)


def row_rule_matches(row: dict[str, Any], conditions: dict[str, Any]) -> bool:
    for key, expected in conditions.items():
        actual = row.get(key)
        if isinstance(expected, list):
            if actual not in expected:
                return False
            continue
        if actual != expected:
            return False
    return True


def model_to_json(model: WorkbookModel, secret_patterns: list[str] | None = None) -> str:
    patterns = secret_patterns or DEFAULT_SECRET_PATTERNS
    payload = {
        "groups": [
            {
                "group_id": group.group_id,
                "group_name": group.group_name,
                "enabled": group.enabled,
                "comment": group.comment,
                "source_row": group.source_row,
            }
            for group in model.groups
        ],
        "monitors": [
            {
                "group_id": item.group_id,
                "group_name": item.group_name,
                "monitor_id": item.monitor_id,
                "monitor_name": item.monitor_name,
                "monitor_type": item.monitor_type,
                "enabled": item.enabled,
                "interval": item.interval,
                "warning_condition": item.warning_condition,
                "critical_condition": item.critical_condition,
                "comment": item.comment,
                "source_sheet": item.source_sheet,
                "source_row": item.source_row,
            }
            for item in model.items
        ],
        "metadata": {
            "source_path": str(model.source_path),
            "source_name": model.source_name,
            **model.metadata,
        },
        "extensions": sanitize_nested(model.extensions, patterns),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, default=str)


def sanitize_nested(value: Any, patterns: list[str]) -> Any:
    if isinstance(value, dict):
        return {key: sanitize_nested(mask_secrets_in_mapping({key: item}, patterns)[key], patterns) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize_nested(item, patterns) for item in value]
    if isinstance(value, str):
        return mask_secrets_in_mapping({"value": value}, patterns)["value"]
    return value
