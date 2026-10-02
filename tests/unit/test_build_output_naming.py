from __future__ import annotations

from pathlib import Path

import pytest

from bom_monitor_builder.build.exceptions import BuildError
from bom_monitor_builder.build.output_naming import (
    default_output_path,
    normalize_output_stem,
    resolve_build_output_path,
)


def test_resolve_build_output_path_uses_cab_stem_when_output_does_not_exist(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    result = resolve_build_output_path(
        input_path=Path("import/cab/standard.cab"),
        profile_path=Path("profiles/sqlserver2022_windows.yml"),
        requested_output=None,
        overwrite=False,
        dry_run=False,
        validate_only=False,
    )

    assert result.path == Path("output/standard.xlsx")


def test_resolve_build_output_path_adds_first_sequence_when_base_exists(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    (output_dir / "standard.xlsx").write_text("base", encoding="utf-8")

    result = resolve_build_output_path(
        input_path=Path("import/cab/standard.cab"),
        profile_path=Path("profiles/sqlserver2022_windows.yml"),
        requested_output=None,
        overwrite=False,
        dry_run=False,
        validate_only=False,
    )

    assert result.path == Path("output/standard_001.xlsx")


def test_resolve_build_output_path_adds_next_sequence_when_multiple_exist(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    (output_dir / "standard.xlsx").write_text("base", encoding="utf-8")
    (output_dir / "standard_001.xlsx").write_text("first", encoding="utf-8")

    result = resolve_build_output_path(
        input_path=Path("import/cab/standard.cab"),
        profile_path=Path("profiles/sqlserver2022_windows.yml"),
        requested_output=None,
        overwrite=False,
        dry_run=False,
        validate_only=False,
    )

    assert result.path == Path("output/standard_002.xlsx")


def test_resolve_build_output_path_keeps_base_name_when_overwrite_enabled() -> None:
    result = resolve_build_output_path(
        input_path=Path("import/cab/standard.cab"),
        profile_path=Path("profiles/sqlserver2022_windows.yml"),
        requested_output=None,
        overwrite=True,
        dry_run=False,
        validate_only=False,
    )

    assert result.path == Path("output/standard.xlsx")


def test_resolve_build_output_path_uses_requested_output_when_available() -> None:
    result = resolve_build_output_path(
        input_path=Path("import/cab/standard.cab"),
        profile_path=Path("profiles/sqlserver2022_windows.yml"),
        requested_output=Path("output/custom.xlsx"),
        overwrite=False,
        dry_run=False,
        validate_only=False,
    )

    assert result.path == Path("output/custom.xlsx")


def test_resolve_build_output_path_uses_requested_output_when_overwrite_enabled() -> None:
    result = resolve_build_output_path(
        input_path=Path("import/cab/standard.cab"),
        profile_path=Path("profiles/sqlserver2022_windows.yml"),
        requested_output=Path("output/custom.xlsx"),
        overwrite=True,
        dry_run=False,
        validate_only=False,
    )

    assert result.path == Path("output/custom.xlsx")


def test_default_output_path_preserves_japanese_spaces_and_parentheses() -> None:
    result = default_output_path(
        input_path=Path("import/cab/0307_SQL Server 2022 (Windows版).CAB"),
        profile_path=Path("profiles/sqlserver2022_windows.yml"),
    )

    assert result == Path("output/0307_SQL Server 2022 (Windows版).xlsx")


def test_normalize_output_stem_replaces_invalid_filename_characters() -> None:
    assert normalize_output_stem('invalid/name\\\\with:chars*?"<>|') == "invalid_name__with_chars______"


def test_validate_only_uses_latest_existing_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    (output_dir / "standard.xlsx").write_text("base", encoding="utf-8")
    (output_dir / "standard_001.xlsx").write_text("first", encoding="utf-8")
    latest = output_dir / "standard_002.xlsx"
    latest.write_text("second", encoding="utf-8")

    result = resolve_build_output_path(
        input_path=Path("import/cab/standard.cab"),
        profile_path=Path("profiles/sqlserver2022_windows.yml"),
        requested_output=None,
        overwrite=False,
        dry_run=False,
        validate_only=True,
    )

    assert result.path == Path("output/standard_002.xlsx")


def test_validate_only_requires_existing_output_when_not_explicit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)

    with pytest.raises(BuildError, match="--validate-only requires an existing output workbook"):
        resolve_build_output_path(
            input_path=Path("import/cab/standard.cab"),
            profile_path=Path("profiles/sqlserver2022_windows.yml"),
            requested_output=None,
            overwrite=False,
            dry_run=False,
            validate_only=True,
        )
