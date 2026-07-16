from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from bom_monitor_builder.cli import main


def test_knowledge_inspect_reports_iteration1_summary(tmp_path: Path) -> None:
    source_path = create_template_data(tmp_path)
    config_path = write_config(tmp_path)

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "knowledge",
            "inspect",
            "--source",
            str(source_path),
            "--config",
            str(config_path),
        ],
    )

    assert result.exit_code == 0
    assert "Category count: 2" in result.output
    assert "CAB count: 2" in result.output
    assert "HTML/HTM count: 1" in result.output
    assert "AutoTemplate.yml: present" in result.output
    assert "Duplicate hash count: 1" in result.output
    assert "Japanese filename count: 1" in result.output
    assert "Unexpected extensions: .bin" in result.output


def test_knowledge_import_dry_run_does_not_write_outputs(tmp_path: Path) -> None:
    source_path = create_template_data(tmp_path)
    config_path = write_config(tmp_path)
    output_path = tmp_path / "knowledge"

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "knowledge",
            "import",
            "--source",
            str(source_path),
            "--output",
            str(output_path),
            "--dry-run",
            "--config",
            str(config_path),
        ],
    )

    assert result.exit_code == 0
    assert "Dry-run mode: no files were written." in result.output
    assert not output_path.exists()


def test_knowledge_import_writes_inventory_and_autotemplate_outputs(tmp_path: Path) -> None:
    source_path = create_template_data(tmp_path)
    config_path = write_config(tmp_path)
    output_path = tmp_path / "knowledge"

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "knowledge",
            "import",
            "--source",
            str(source_path),
            "--output",
            str(output_path),
            "--config",
            str(config_path),
        ],
    )

    assert result.exit_code == 0
    assert (output_path / "source_inventory/inventory.json").exists()
    assert (output_path / "source_inventory/inventory.csv").exists()
    assert (output_path / "categories/categories.csv").exists()
    assert (output_path / "autotemplate/analysis.json").exists()
    assert (output_path / "autotemplate/paths.csv").exists()
    assert (output_path / "state/source_inventory_state.json").exists()

    analysis = json.loads((output_path / "autotemplate/analysis.json").read_text(encoding="utf-8"))
    assert analysis["encoding"] == "utf-8"
    assert analysis["parsed"]["catalog"][0]["meta"]["enabled"] is True

    paths = json.loads((output_path / "autotemplate/paths.json").read_text(encoding="utf-8"))
    rendered_paths = {row["path"]: row["value"] for row in paths["paths"]}
    assert rendered_paths["$.catalog[0].meta.enabled"] == "True"
    assert rendered_paths["$.unknown_branch[1]"] == "20"


def test_knowledge_import_uses_state_for_updated_removed_and_unchanged(tmp_path: Path) -> None:
    source_path = create_template_data(tmp_path)
    config_path = write_config(tmp_path)
    output_path = tmp_path / "knowledge"

    runner = CliRunner()
    first_result = runner.invoke(
        main,
        [
            "knowledge",
            "import",
            "--source",
            str(source_path),
            "--output",
            str(output_path),
            "--config",
            str(config_path),
        ],
    )
    assert first_result.exit_code == 0

    (source_path / "0002_Windows 基本" / "page.html").write_text("<html>changed</html>", encoding="utf-8")
    (source_path / "0003_App" / "copy.cab").unlink()

    second_result = runner.invoke(
        main,
        [
            "knowledge",
            "import",
            "--source",
            str(source_path),
            "--output",
            str(output_path),
            "--dry-run",
            "--config",
            str(config_path),
        ],
    )

    assert second_result.exit_code == 0
    assert "Updated: 1" in second_result.output
    assert "Removed: 1" in second_result.output
    assert "Unchanged: 4" in second_result.output


def create_template_data(tmp_path: Path) -> Path:
    source_path = tmp_path / "import" / "TemplateData"
    category_one = source_path / "0002_Windows 基本"
    category_two = source_path / "0003_App"
    category_one.mkdir(parents=True)
    category_two.mkdir(parents=True)

    (source_path / "AutoTemplate.yml").write_text(
        "\n".join(
            [
                "catalog:",
                "  - name: base-template",
                "    meta:",
                "      enabled: true",
                "unknown_branch:",
                "  - 10",
                "  - 20",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (category_one / "page.html").write_text("<html>template</html>", encoding="utf-8")
    (category_one / "説明.txt").write_text("jp", encoding="utf-8")
    (category_two / "main.cab").write_bytes(b"same-cab")
    (category_two / "copy.cab").write_bytes(b"same-cab")
    (category_two / "notes.bin").write_bytes(b"\x00\x01")
    return source_path


def write_config(tmp_path: Path) -> Path:
    config_path = tmp_path / "settings.yml"
    config_path.write_text(
        "\n".join(
            [
                "project:",
                "  name: test-project",
                "logging:",
                f"  file: {tmp_path / 'logs' / 'knowledge.log'}",
                "  level: INFO",
                "knowledge:",
                "  source_dir: import/TemplateData",
                "  output_dir: knowledge",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return config_path
