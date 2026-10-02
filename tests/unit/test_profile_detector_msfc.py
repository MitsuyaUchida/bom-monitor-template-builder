from __future__ import annotations

from pathlib import Path

from bom_monitor_builder.build.detector import detect_profile
from bom_monitor_builder.build.models import DetectionInput


def test_detector_selects_msfc_2022_profile() -> None:
    candidate = detect_profile(
        DetectionInput(
            source_path=Path("import/cab/msfc-2022.CAB"),
            source_name="msfc-2022.CAB",
            source_stem="msfc-2022",
            manifest_product="BOM for Windows",
            group_names=["MSFC_Windows Server 2022  監視"],
            monitor_names=[
                "Cluster Service 監視",
                "フェールオーバークラスタリング 重大/エラー/警告ログ監視",
                "クラスター イベント 重大/エラー/警告ログ監視",
                "Cluster Resources -> Resource Failure 監視",
                "Cluster NetFt Heartbeats -> Missing heartbeats 監視",
            ],
            monitor_types=["Service", "EventlogWSA", "Perf"],
            object_names=[
                "ClusSvc",
                "System",
                "\\Cluster Resources(_Total)\\Resource Failure",
                "\\Cluster NetFt Heartbeats(clussvc.exe)\\Missing heartbeats",
            ],
            value_names=["CurrentState", "MonitorCountWSA", "CalculatedValue"],
        )
    )
    assert candidate.profile_id == "msfc_2022"
