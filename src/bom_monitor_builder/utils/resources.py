from __future__ import annotations

import sys
from pathlib import Path


def resource_path(path: str | Path) -> Path:
    """Resolve a bundled resource, while preserving current-directory overrides."""
    candidate = Path(path)
    if candidate.is_absolute() or candidate.exists():
        return candidate

    bundle_root = getattr(sys, "_MEIPASS", None)
    if getattr(sys, "frozen", False) and bundle_root:
        bundled = Path(bundle_root) / candidate
        if bundled.exists():
            return bundled

    project_root = Path(__file__).resolve().parents[3]
    project_resource = project_root / candidate
    if project_resource.exists():
        return project_resource
    return candidate
