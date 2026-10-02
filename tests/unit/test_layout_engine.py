from __future__ import annotations

from pathlib import Path

from bom_monitor_builder.design_excel.layout_engine import build_row_contexts, expected_merge_ranges
from bom_monitor_builder.design_excel.models import MonitorGroup, MonitorItem, RenderRow, RenderTable, WorkbookModel


def test_build_row_contexts_classifies_group_positions() -> None:
    model = sample_model()
    table = RenderTable(name="settings", sheet="Settings", start_row=5, template_row=5, rows=sample_rows())

    contexts = build_row_contexts(model, table)

    assert [context.row_type for context in contexts] == [
        "group_first",
        "group_middle",
        "group_last",
        "single_row_group",
        "group_first",
        "group_last",
    ]
    assert contexts[-1].is_table_last is True


def test_expected_merge_ranges_builds_vertical_group_ranges() -> None:
    model = sample_model()
    table = RenderTable(
        name="settings",
        sheet="Settings",
        start_row=5,
        template_row=5,
        rows=sample_rows(),
        layout={"group_merge": {"enabled": True, "columns": ["B", "C"]}},
    )

    contexts = build_row_contexts(model, table)
    merges = expected_merge_ranges(table, contexts)

    assert merges == {
        "B": ["B5:B7", "B9:B10"],
        "C": ["C5:C7", "C9:C10"],
    }


def sample_model() -> WorkbookModel:
    groups = [
        MonitorGroup(group_id="GRP01", group_name="Platform", enabled=True, comment=None, source_row=1),
        MonitorGroup(group_id="GRP02", group_name="Log", enabled=True, comment=None, source_row=2),
        MonitorGroup(group_id="GRP03", group_name="Service", enabled=True, comment=None, source_row=3),
    ]
    items = [
        MonitorItem("GRP01", "Platform", "MON01", "CPU", None, None, None, None, None, None),
        MonitorItem("GRP01", "Platform", "MON02", "Memory", None, None, None, None, None, None),
        MonitorItem("GRP01", "Platform", "MON03", "Disk", None, None, None, None, None, None),
        MonitorItem("GRP02", "Log", "MON01", "Event", None, None, None, None, None, None),
        MonitorItem("GRP03", "Service", "MON01", "RPC", None, None, None, None, None, None),
        MonitorItem("GRP03", "Service", "MON02", "WMI", None, None, None, None, None, None),
    ]
    return WorkbookModel(source_path=Path("input/sample.xlsx"), source_name="sample.xlsx", groups=groups, items=items)


def sample_rows() -> list[RenderRow]:
    return [RenderRow(values={"B": item.group_id, "C": item.group_name, "D": item.monitor_id}, source_monitor_id=item.monitor_id) for item in sample_model().items]
