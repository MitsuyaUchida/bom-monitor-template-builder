from __future__ import annotations

from typing import Any

from openpyxl.worksheet.page import PageMargins  # type: ignore[import-untyped]

DEFAULT_MIN_WIDTH = 8.0
DEFAULT_MAX_WIDTH = 50.0


def clamp_width(value: float, *, min_width: float = DEFAULT_MIN_WIDTH, max_width: float = DEFAULT_MAX_WIDTH) -> float:
    return max(min_width, min(max_width, value))


def apply_standard_print_settings(
    worksheet: Any,
    *,
    orientation: str = "landscape",
    fit_to_width: int = 1,
    fit_to_height: int = 0,
    title_rows: str | None = None,
) -> None:
    worksheet.page_setup.orientation = orientation
    worksheet.page_setup.fitToWidth = fit_to_width
    worksheet.page_setup.fitToHeight = fit_to_height
    worksheet.sheet_properties.pageSetUpPr.fitToPage = True
    worksheet.page_margins = PageMargins(left=0.3, right=0.3, top=0.5, bottom=0.5, header=0.2, footer=0.2)
    worksheet.print_options.horizontalCentered = False
    worksheet.print_options.verticalCentered = False
    if title_rows:
        worksheet.print_title_rows = title_rows


def apply_standard_sheet_view(worksheet: Any, *, freeze_panes: str | None = None, show_grid_lines: bool = False, zoom_scale: int = 100) -> None:
    worksheet.sheet_view.showGridLines = show_grid_lines
    worksheet.sheet_view.zoomScale = zoom_scale
    if freeze_panes is not None:
        worksheet.freeze_panes = freeze_panes


def apply_auto_filter(worksheet: Any, ref: str | None) -> None:
    if ref:
        worksheet.auto_filter.ref = ref
