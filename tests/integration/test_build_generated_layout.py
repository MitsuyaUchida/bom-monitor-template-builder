from __future__ import annotations

import shutil
from pathlib import Path

from click.testing import CliRunner
from openpyxl import load_workbook  # type: ignore[import-untyped]

from bom_monitor_builder.cli import main

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_build_standard_cab_applies_generated_layout_rules(tmp_path: Path, monkeypatch) -> None:
    prepare_build_workspace(tmp_path, monkeypatch)
    runner = CliRunner()

    result = runner.invoke(
        main,
        [
            "build",
            "--input",
            "import/cab/standard.cab",
            "--profile",
            "profiles/sqlserver2022_windows.yml",
        ],
    )

    assert result.exit_code == 0, result.output
    workbook = load_workbook(tmp_path / "output/standard.xlsx", data_only=False)
    settings = workbook["監視設定"]

    assert settings["B5"].alignment.horizontal == "center"
    assert settings["C5"].alignment.horizontal == "center"
    assert settings["D5"].alignment.horizontal == "center"
    assert settings["K5"].alignment.wrap_text is True

    assert settings["B11"].border.top.style == "thin"
    assert settings["C11"].border.top.style == "thin"
    assert settings["B15"].border.bottom.style == "thin"
    assert settings["C15"].border.bottom.style == "thin"
    assert [settings[f"B{row}"].value for row in range(5, 16)].count("GRP01") == 1
    assert [settings[f"B{row}"].value for row in range(5, 16)].count("GRP02") == 1
    assert [settings[f"B{row}"].value for row in range(5, 16)].count("GRP03") == 1

    assert settings.row_dimensions[5].height is None
    assert settings.row_dimensions[11].height is None
    assert [str(item) for item in settings.merged_cells.ranges if item.min_row >= 5] == []


def prepare_build_workspace(tmp_path: Path, monkeypatch) -> None:
    for directory in ("import", "profiles", "templates"):
        shutil.copytree(PROJECT_ROOT / directory, tmp_path / directory)
    monkeypatch.chdir(tmp_path)
