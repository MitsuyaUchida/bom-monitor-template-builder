from __future__ import annotations

from pathlib import Path
from typing import Any


def build_directory_tree(source_root: Path) -> dict[str, Any]:
    return build_node(source_root, source_root)


def build_node(path: Path, source_root: Path) -> dict[str, Any]:
    relative_path = "." if path == source_root else path.relative_to(source_root).as_posix()
    depth = 0 if path == source_root else len(path.relative_to(source_root).parts)

    children: list[dict[str, Any]] = []
    for child in sorted(path.iterdir(), key=lambda entry: entry.name.casefold()):
        if child.is_symlink():
            continue
        if child.is_dir():
            children.append(build_node(child, source_root))
        else:
            child_depth = len(child.relative_to(source_root).parts)
            children.append(
                {
                    "name": child.name,
                    "path": child.relative_to(source_root).as_posix(),
                    "type": "file",
                    "depth": child_depth,
                }
            )

    return {
        "name": path.name,
        "path": relative_path,
        "type": "directory",
        "depth": depth,
        "children": children,
    }
