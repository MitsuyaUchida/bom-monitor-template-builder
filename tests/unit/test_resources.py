from __future__ import annotations

import sys
from pathlib import Path

from bom_monitor_builder.utils.resources import resource_path


def test_resource_path_uses_bundled_root_for_frozen_executable(
    tmp_path: Path,
    monkeypatch,
) -> None:
    bundle_root = tmp_path / "bundle"
    bundled_profile = bundle_root / "profiles" / "generic.yml"
    bundled_profile.parent.mkdir(parents=True)
    bundled_profile.write_text("profile: generic\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(bundle_root), raising=False)

    assert resource_path("profiles/generic.yml") == bundled_profile


def test_resource_path_prefers_existing_working_directory_resource(
    tmp_path: Path,
    monkeypatch,
) -> None:
    working_resource = tmp_path / "profiles" / "custom.yml"
    working_resource.parent.mkdir(parents=True)
    working_resource.write_text("profile: custom\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert resource_path("profiles/custom.yml") == Path("profiles/custom.yml")


def test_resource_path_finds_project_resources_in_python_mode(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delattr(sys, "frozen", raising=False)
    monkeypatch.delattr(sys, "_MEIPASS", raising=False)

    assert resource_path("profiles/generic.yml").is_file()
