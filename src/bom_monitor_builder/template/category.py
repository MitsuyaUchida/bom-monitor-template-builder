from __future__ import annotations

import re
from collections import defaultdict

from bom_monitor_builder.template.models import CategoryInventory, FileRecord

CATEGORY_PATTERN = re.compile(r"^(?P<category_id>\d{4})_(?P<category_name>.+)$")


def build_category_inventory(files: list[FileRecord]) -> list[CategoryInventory]:
    grouped: dict[str, list[FileRecord]] = defaultdict(list)
    for entry in files:
        if entry.category_name is None:
            continue
        grouped[entry.directory].append(entry)

    rows: list[CategoryInventory] = []
    for directory in sorted(grouped):
        entries = grouped[directory]
        category_id, category_name = parse_category_directory(directory)
        rows.append(
            CategoryInventory(
                category_id=category_id,
                category_name=category_name,
                directory=directory,
                file_count=len(entries),
                cab_count=sum(1 for entry in entries if entry.file_type == "cab"),
                html_count=sum(1 for entry in entries if entry.file_type == "html"),
            )
        )
    return rows


def parse_category_directory(directory: str) -> tuple[str | None, str]:
    match = CATEGORY_PATTERN.match(directory)
    if match is None:
        return None, directory
    return match.group("category_id"), match.group("category_name")
