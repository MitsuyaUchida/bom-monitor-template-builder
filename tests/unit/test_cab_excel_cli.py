from pathlib import Path

from click.testing import CliRunner
from openpyxl import load_workbook  # type: ignore[import-untyped]

from bom_monitor_builder.cli import main


def test_cab_excel_command_generates_workbook(tmp_path: Path) -> None:
    source = Path("tests/fixtures/sample_extracted")
    output = tmp_path / "result.xlsx"
    runner = CliRunner()

    result = runner.invoke(
        main,
        ["cab-excel", str(source), "--extracted", "--output", str(output), "--overwrite"],
    )

    assert result.exit_code == 0
    assert output.exists()
    workbook = load_workbook(output)
    assert workbook["監視項目一覧"]["D2"].value == "レイテンシ(ディスク転送時間)"
