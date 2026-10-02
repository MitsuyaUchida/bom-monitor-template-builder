from __future__ import annotations

CONDITION_DISPLAY_NAMES = {
    "5ContYellow": "5回連続注意",
}


def get_condition_display_name(value: str | None) -> str:
    if not value:
        return ""
    return CONDITION_DISPLAY_NAMES.get(value, value)
