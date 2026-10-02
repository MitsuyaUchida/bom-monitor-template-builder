from __future__ import annotations

from bom_monitor_builder.design_excel.monitor_type_display import get_monitor_type_display_name


def test_get_monitor_type_display_name_for_service() -> None:
    assert get_monitor_type_display_name("Service") == "サービス監視"


def test_get_monitor_type_display_name_for_evntlogwsa() -> None:
    assert get_monitor_type_display_name("EvntlogWSA") == "イベントログ監視"


def test_get_monitor_type_display_name_for_eventlogwsa() -> None:
    assert get_monitor_type_display_name("EventlogWSA") == "イベントログ監視"


def test_get_monitor_type_display_name_for_unknown_type() -> None:
    assert get_monitor_type_display_name("UnknownMonitor") == "UnknownMonitor"


def test_get_monitor_type_display_name_for_empty_string() -> None:
    assert get_monitor_type_display_name("") == ""


def test_get_monitor_type_display_name_for_none() -> None:
    assert get_monitor_type_display_name(None) == ""
