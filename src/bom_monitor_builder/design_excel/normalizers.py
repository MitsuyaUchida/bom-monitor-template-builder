from __future__ import annotations

import re
from typing import Any, Callable

MASK = "****"


def trim(value: Any) -> Any:
    return value.strip() if isinstance(value, str) else value


def normalize_spaces(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    compact = re.sub(r"[ \t\u3000]+", " ", value.strip())
    return compact.replace(" 以上", "以上").replace(" 以下", "以下")


def strip_extension(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    return re.sub(r"\.[A-Za-z0-9]+$", "", value)


def normalize_boolean(value: Any) -> Any:
    if isinstance(value, bool):
        return "有効" if value else "無効"
    if not isinstance(value, str):
        return value
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes", "enabled", "有効"}:
        return "有効"
    if normalized in {"false", "0", "no", "disabled", "無効"}:
        return "無効"
    return value


def normalize_interval(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    return value.strip().replace(" ", "")


def normalize_threshold(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    compact = normalize_spaces(value)
    if isinstance(compact, str):
        return compact.replace(" ", "")
    return compact


def mask_secret(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    masked = re.sub(r"(?i)(password|passwd|secret|token|api[_-]?key|access[_-]?key)\s*[:=]\s*\S+", r"\1=" + MASK, value)
    masked = re.sub(r"(?i)(-pw:)\S+", r"\1" + MASK, masked)
    return masked


NORMALIZERS: dict[str, Callable[[Any], Any]] = {
    "trim": trim,
    "normalize_spaces": normalize_spaces,
    "strip_extension": strip_extension,
    "normalize_boolean": normalize_boolean,
    "normalize_interval": normalize_interval,
    "normalize_threshold": normalize_threshold,
    "mask_secret": mask_secret,
}
