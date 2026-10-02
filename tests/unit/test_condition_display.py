from __future__ import annotations

from bom_monitor_builder.design_excel.condition_display import get_condition_display_name


def test_get_condition_display_name_for_5contyellow() -> None:
    assert get_condition_display_name("5ContYellow") == "5回連続注意"


def test_get_condition_display_name_for_unknown_value() -> None:
    assert get_condition_display_name("UnknownCondition") == "UnknownCondition"


def test_get_condition_display_name_for_empty_string() -> None:
    assert get_condition_display_name("") == ""


def test_get_condition_display_name_for_none() -> None:
    assert get_condition_display_name(None) == ""
