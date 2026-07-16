from __future__ import annotations

from collections import Counter, defaultdict

from bom_monitor_builder.template.models import ExtensionInventory, FileRecord, TemplateInventory


def build_extension_inventory(files: list[FileRecord]) -> list[ExtensionInventory]:
    counts = Counter(entry.extension or "[no extension]" for entry in files)
    return [
        ExtensionInventory(extension=extension, file_count=counts[extension])
        for extension in sorted(counts)
    ]


def build_template_inventory(files: list[FileRecord]) -> list[TemplateInventory]:
    grouped: dict[tuple[str, str], list[FileRecord]] = defaultdict(list)
    for entry in files:
        if entry.category_name is None:
            continue
        if entry.file_type not in {"cab", "html"}:
            continue
        key = (entry.directory, entry.template_name_candidate.casefold())
        grouped[key].append(entry)

    rows: list[TemplateInventory] = []
    for _, entries in sorted(grouped.items(), key=lambda item: item[0]):
        first = sorted(entries, key=lambda entry: entry.relative_path)[0]
        cab = select_path(entries, "cab")
        html = select_path(entries, "html")
        rows.append(
            TemplateInventory(
                category_id=first.category_id,
                category_name=first.category_name or "",
                directory=first.directory,
                template_name_candidate=first.template_name_candidate,
                cab=cab,
                html=html,
                same_name_pair=cab is not None and html is not None,
                html_only=cab is None and html is not None,
                cab_only=cab is not None and html is None,
            )
        )
    return rows


def select_path(entries: list[FileRecord], file_type: str) -> str | None:
    matches = sorted(entry.relative_path for entry in entries if entry.file_type == file_type)
    if not matches:
        return None
    return matches[0]
