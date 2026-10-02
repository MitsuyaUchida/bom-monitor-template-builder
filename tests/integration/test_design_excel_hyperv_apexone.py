from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from bom_monitor_builder.cli import main


def test_hyperv_apexone_dry_run_dump_model_uses_real_input() -> None:
    input_path = Path("input/Hyper-V_ApexOne.xlsx")
    profile_path = Path("profiles/hyperv_apexone.yml")
    output_model_path = Path("output/hyperv_apexone_model_test.json")
    runner = CliRunner()

    result = runner.invoke(
        main,
        [
            "design-excel",
            "--input",
            str(input_path),
            "--profile",
            str(profile_path),
            "--dump-model",
            str(output_model_path),
            "--dry-run",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(output_model_path.read_text(encoding="utf-8"))

    assert sorted(payload.keys()) == ["extensions", "groups", "metadata", "monitors"]
    assert len(payload["groups"]) == 6
    assert len(payload["monitors"]) == 31

    group_names = {group["group_name"] for group in payload["groups"]}
    assert "Hyper-V 監視" in group_names
    assert "Trend Micro Apex One サーバー監視" in group_names
    assert "Trend Micro Apex One エージェント監視" in group_names

    monitor_names = {monitor["monitor_name"] for monitor in payload["monitors"]}
    assert "Hyper-V イベントログ監視" in monitor_names
    assert "Apex Oneサーバログ監視" in monitor_names

    extension = payload["extensions"]["hyperv_apexone"]["details"]
    assert extension["GRP04/MON05"]["ObjectName"] == "Microsoft-Windows"
    assert "Hyper-V-VMMS" in extension["GRP04/MON05"]["Options"]
    assert extension["GRP05/MON08"]["ObjectName"] == "Application"
    assert "Trend Micro Apex One" in extension["GRP05/MON08"]["Options"]
