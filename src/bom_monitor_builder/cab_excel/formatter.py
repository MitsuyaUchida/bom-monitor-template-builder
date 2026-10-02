"""Formatting helpers for workbook output."""

from __future__ import annotations

from decimal import Decimal

from .models import ScalarValue

COMPARISON_LABELS = {
    "GreaterEqual": "以上",
    "Greater": "より大きい",
    "LessEqual": "以下",
    "Less": "より小さい",
    "Equal": "等しい",
    "NotEqual": "等しくない",
}

INTERVAL_UNITS = {
    "Seconds": "秒",
    "Minutes": "分",
    "Hours": "時間",
    "Days": "日",
}


def format_enabled(value: object) -> str:
    """Format enabled state."""
    return "有効" if bool(value) else "無効"


def format_interval(interval: ScalarValue, unit: str) -> tuple[str, str | None]:
    """Format interval text and return any unknown unit."""
    interval_text = "" if interval is None else str(interval)
    localized = INTERVAL_UNITS.get(unit)
    if localized is None:
        return f"{interval_text} {unit}".strip(), unit if unit else None
    return f"{interval_text}{localized}", None


def format_threshold(value: ScalarValue, method: str) -> tuple[str, str | None]:
    """Format threshold text and return any unknown comparator."""
    comparator = COMPARISON_LABELS.get(method)
    value_text = "" if value is None else str(value)
    if comparator is None:
        if method:
            return f"{value_text} {method}".strip(), method
        return value_text, None
    return f"{value_text} {comparator}".strip(), None


def sanitize_excel_text(value: object) -> object:
    """Prevent formula injection while keeping numeric values as numbers."""
    if value is None:
        return ""
    if isinstance(value, bool | int | float | Decimal):
        return value
    text = str(value)
    if text[:1] in {"=", "+", "-", "@"}:
        return "'" + text
    return text
