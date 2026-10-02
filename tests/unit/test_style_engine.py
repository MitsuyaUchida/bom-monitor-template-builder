from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook  # type: ignore[import-untyped]
from openpyxl.styles import Alignment, Border, Side  # type: ignore[import-untyped]

from bom_monitor_builder.design_excel.layout_engine import RowContext
from bom_monitor_builder.design_excel.models import RenderTable
from bom_monitor_builder.design_excel.style_engine import apply_table_styles, expected_alignment, expected_border, expected_row_height


def test_apply_table_styles_applies_alignment_border_and_row_height() -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Settings"
    sheet["A3"] = "template"
    sheet["A3"].alignment = Alignment(horizontal="center", vertical="top", wrap_text=True)
    sheet["A3"].border = Border(top=Side(style="thin"), bottom=Side(style="thin"))
    sheet["B3"] = "template"
    sheet["B3"].alignment = Alignment(horizontal="left", vertical="top")
    sheet["B3"].border = Border(top=Side(style="thin"), bottom=Side(style="thin"))
    sheet.row_dimensions[3].height = 20

    table = RenderTable(
        name="settings",
        sheet="Settings",
        start_row=3,
        template_row=3,
        rows=[],
        managed_columns={"group_id": "A", "monitor_name": "B"},
        layout={"style_sources": {"single_row_group": 3, "table_last": 3}},
        format_rules={
            "alignment": {
                "A": {"horizontal": "center", "vertical": "center", "wrap_text": True},
                "B": {"horizontal": "left", "vertical": "center", "wrap_text": True},
            },
            "row_height": {
                "default": 20,
                "thresholds": [{"max": 10, "height": 20}, {"max": 30, "height": 30}],
                "fallback": 45,
            },
        },
    )
    sheet["A3"] = "GRP01"
    sheet["B3"] = "A very long monitor name"
    context = RowContext(3, "GRP01", "Platform", "MON01", 0, 0, 1, True, True, True)

    apply_table_styles(sheet, table, [context])

    assert sheet["A3"].alignment.horizontal == "center"
    assert sheet["A3"].alignment.vertical == "center"
    assert sheet["B3"].alignment.wrap_text is True
    assert sheet["A3"].border.top.style == "thin"
    assert sheet.row_dimensions[3].height == 30


def test_expected_style_helpers_follow_template_source() -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Settings"
    sheet["A5"].alignment = Alignment(horizontal="center", vertical="top")
    sheet["A5"].border = Border(left=Side(style="thin"), right=Side(style="thin"))
    sheet.row_dimensions[5].height = 22

    table = RenderTable(
        name="settings",
        sheet="Settings",
        start_row=5,
        template_row=5,
        rows=[],
        managed_columns={"group_id": "A"},
        layout={"style_sources": {"group_first": 5}},
        format_rules={"alignment": {"A": {"horizontal": "center", "vertical": "top"}}},
    )
    context = RowContext(5, "GRP01", "Platform", "MON01", 0, 0, 2, True, False, False)

    alignment = expected_alignment(table, sheet, context, "A")
    border = expected_border(table, sheet, context, "A")
    height = expected_row_height(table, sheet, context)

    assert alignment is not None and alignment.horizontal == "center"
    assert border is not None and border.left.style == "thin"
    assert height == 22
