from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .exceptions import ProfileError


def read_profile_data(profile_path: Path) -> dict[str, Any]:
    if not profile_path.exists():
        raise ProfileError(f"Profile not found: {profile_path}")
    data = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ProfileError("Profile root must be a mapping.")
    for section in ["profile", "template", "source", "transform", "output", "validation", "security"]:
        if section not in data:
            raise ProfileError(f"Missing profile section: {section}")
    return data


def load_profile(profile_path: Path, template_override: Path | None = None) -> dict[str, Any]:
    data = read_profile_data(profile_path)
    template_path = template_override or resolve_template_path(profile_path, data["template"])
    data["template"]["resolved_path"] = template_path
    data["template"]["source"] = "explicit_template" if template_override is not None else "profile_template"
    return data


def resolve_template_path(profile_path: Path, template_section: dict[str, Any]) -> Path | None:
    raw_path = template_section.get("path")
    if raw_path in (None, ""):
        return None
    if not isinstance(raw_path, str):
        raise ProfileError("template.path must be a string when configured.")
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate
    profile_relative = (profile_path.parent / candidate).resolve()
    if profile_relative.exists():
        return profile_relative
    return (profile_path.parent.parent / candidate).resolve()
