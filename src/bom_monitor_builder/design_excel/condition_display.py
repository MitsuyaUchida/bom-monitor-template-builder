from __future__ import annotations

import re
from typing import Any

CURRENT_STATE_DISPLAY_NAMES = {
    "1": "\u505c\u6b62",
    "2": "\u958b\u59cb\u4e2d",
    "3": "\u505c\u6b62\u4e2d",
    "4": "\u958b\u59cb",
    "5": "\u518d\u958b\u4e2d",
    "6": "\u4e00\u6642\u505c\u6b62\u4e2d",
    "7": "\u4e00\u6642\u505c\u6b62",
}

_CONT_YELLOW_PATTERN = re.compile(r"^(\d+)\s*ContYellow$")


def get_condition_display_name(value: Any) -> Any:
    """Return an Excel-facing Japanese label without changing the source value."""
    if value is None or value == "":
        return "" if value is None else value

    text = str(value)
    match = _CONT_YELLOW_PATTERN.fullmatch(text)
    if match:
        return f"{match.group(1)}\u56de\u9023\u7d9a\u6ce8\u610f"
    return value


def get_service_state_display_name(
    value: Any,
    *,
    monitor_type: str | None,
    value_name: str | None,
) -> Any:
    """Translate a service state only when its BOM field context is explicit."""
    if monitor_type != "Service" or value_name != "CurrentState" or value is None:
        return value
    return CURRENT_STATE_DISPLAY_NAMES.get(str(value), value)
