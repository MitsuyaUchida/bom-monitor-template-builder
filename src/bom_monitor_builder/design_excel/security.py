from __future__ import annotations

import re
from typing import Any

from openpyxl.workbook.workbook import Workbook  # type: ignore[import-untyped]

from .normalizers import MASK

DEFAULT_SECRET_PATTERNS = [
    "password",
    "passwd",
    "secret",
    "secret_access_key",
    "access_key",
    "api_key",
    "token",
    "credential",
    "ユーザー名",
    "パスワード",
    "アクセスキー",
    "シークレットキー",
]


def is_secret_key(key: str, patterns: list[str]) -> bool:
    lowered = key.lower()
    return any(pattern.lower() in lowered for pattern in patterns)


def mask_secrets_in_mapping(values: dict[str, Any], patterns: list[str]) -> dict[str, Any]:
    masked: dict[str, Any] = {}
    for key, value in values.items():
        if is_secret_key(key, patterns):
            masked[key] = MASK if value not in (None, "") else value
            continue
        if isinstance(value, str):
            masked[key] = mask_secret_text(value, patterns)
        else:
            masked[key] = value
    return masked


def mask_secret_text(value: str, patterns: list[str]) -> str:
    masked = value
    for pattern in patterns:
        expr = re.compile(rf"(?i)([^=\n:]*{re.escape(pattern)}[^=\n:]*)\s*([:=])\s*([^\s,;]+)")
        masked = expr.sub(r"\1\2****", masked)
        flag_expr = re.compile(rf"(?i)(--?{re.escape(pattern)})\s+([^\s,;]+)")
        masked = flag_expr.sub(r"\1 ****", masked)
    masked = re.sub(r"(?i)(--?pass(?:word)?|--?pswd)\s+([^\s,;]+)", r"\1 ****", masked)
    masked = re.sub(r"(?i)(-pw:)\S+", r"\1****", masked)
    return masked


def sanitize_workbook_strings(workbook: Workbook, patterns: list[str]) -> None:
    for worksheet in workbook.worksheets:
        for row in worksheet.iter_rows():
            for cell in row:
                if isinstance(cell.value, str):
                    cell.value = mask_secret_text(cell.value, patterns)
