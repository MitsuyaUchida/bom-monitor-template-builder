from __future__ import annotations

MONITOR_TYPE_DISPLAY_NAMES = {
    "Service": "サービス監視",
    "EvntlogWSA": "イベントログ監視",
    "EventlogWSA": "イベントログ監視",
}


def get_monitor_type_display_name(monitor_type: str | None) -> str:
    if not monitor_type:
        return ""
    return MONITOR_TYPE_DISPLAY_NAMES.get(monitor_type, monitor_type)
