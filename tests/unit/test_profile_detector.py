from __future__ import annotations

from pathlib import Path

import pytest

from bom_monitor_builder.build.detector import detect_profile
from bom_monitor_builder.build.exceptions import BuildError, ProfileDetectionError
from bom_monitor_builder.build.models import DetectionInput
from bom_monitor_builder.build.service import resolve_profile_path


def test_detector_selects_aws_cost_profile() -> None:
    candidate = detect_profile(
        DetectionInput(
            source_path=Path("import/cab/0104_AWS月コスト監視.cab"),
            source_name="0104_AWS月コスト監視.cab",
            source_stem="0104_AWS月コスト監視",
            manifest_product="AWS月コスト監視",
            group_names=["AWSコスト監視"],
            monitor_names=["AWS月コスト監視"],
            monitor_types=["Custom2"],
            object_names=["C:\\aws-cost\\print_monthly_total_cost.bat"],
            value_names=["MonitorCustom"],
        )
    )
    assert candidate.profile_id == "aws_cost"


def test_detector_selects_arcserve_udp9_profile() -> None:
    candidate = detect_profile(
        DetectionInput(
            source_path=Path("import/cab/0234_Arcserve UDP 9.0 監視.CAB"),
            source_name="0234_Arcserve UDP 9.0 監視.CAB",
            source_stem="0234_Arcserve UDP 9.0 監視",
            manifest_product="Arcserve UDP 9.0",
            group_names=["Arcserve UDP 9 & 10 監視"],
            monitor_names=["Arcserve UDP エージェント サービス監視"],
            monitor_types=["Service", "EventlogWSA"],
            object_names=["CASAD2DWebSvc", "ArcserveUDPPS"],
            value_names=["CurrentState"],
        )
    )
    assert candidate.profile_id == "arcserve_udp9"


def test_detector_selects_sqlserver2022_windows_profile() -> None:
    candidate = detect_profile(
        DetectionInput(
            source_path=Path("import/cab/0307_sqlserver2022_windows.cab"),
            source_name="0307_sqlserver2022_windows.cab",
            source_stem="0307_sqlserver2022_windows",
            manifest_product="SQL Server 2022",
            group_names=[
                "SQL Server 2022 サービス監視",
                "SQL Server 2022 イベントログ監視",
                "SQL Server 2022 パフォーマンス監視",
            ],
            monitor_names=["SQL Server (MSSQLSERVER) 監視"],
            monitor_types=["Service", "EventlogWSA", "Perf"],
            object_names=["MSSQLSERVER", "SQLSERVERAGENT", "SQLBrowser"],
            value_names=["CurrentState"],
        )
    )
    assert candidate.profile_id == "sqlserver2022_windows"


def test_detector_selects_nec_esmpro23_profile() -> None:
    candidate = detect_profile(
        DetectionInput(
            source_path=Path("import/cab/NEC_ESMPRO23.CAB"),
            source_name="NEC_ESMPRO23.CAB",
            source_stem="NEC_ESMPRO23",
            manifest_product="BOM for Windows",
            group_names=["NEC ESMPRO/ServerAgent Service Ver2.3 監視"],
            monitor_names=[
                "Alert Manager Main Service 監視",
                "ESMCommonService 監視",
                "ESM System Management Service 監視",
                "ESMNVMeMonitor 監視",
            ],
            monitor_types=["Service", "EventlogWSA"],
            object_names=[
                "AlertManagerMainService",
                "ESMCommonService",
                "ESMSystemManagementService",
                "ESMNVMeMonitor",
            ],
            value_names=["CurrentState", "EventID"],
        )
    )
    assert candidate.profile_id == "nec_esmpro23"


def test_detector_selects_linux_report_profile() -> None:
    candidate = detect_profile(
        DetectionInput(
            source_path=Path("import/cab/1002_Linux_report.CAB"),
            source_name="1002_Linux_report.CAB",
            source_stem="1002_Linux_report",
            manifest_product="BOM for Windows Linux Option",
            group_names=["Linux レポート向け監視項目"],
            monitor_names=[
                "Linux Idle監視",
                "Linux LoadAverage監視",
                "Linux メモリ監視",
                "Linux NIC1 ネットワーク送信総バイト数監視",
            ],
            monitor_types=["LinuxCpu", "LinuxMemory", "LinuxDisk", "LinuxDiskStress", "LinuxNetwork", "LinuxTextlog"],
            object_names=["\\Processor(_Total)\\IdleTime%", "/dev/sda1", "\\Network(eth0)\\DevTransBytes"],
            value_names=["Value", "PercentFree"],
        )
    )
    assert candidate.profile_id == "linux_report"


def test_detector_selects_activeimage_protector2022_serveredition_profile() -> None:
    candidate = detect_profile(
        DetectionInput(
            source_path=Path("import/cab/0905_ActiveImage Protector 2022 ServerEditon.CAB"),
            source_name="0905_ActiveImage Protector 2022 ServerEditon.CAB",
            source_stem="0905_ActiveImage Protector 2022 ServerEditon",
            manifest_product="BOM for Windows",
            group_names=["ActiveImage Protector 2022 ServerEditon"],
            monitor_names=[
                "ActiveImage Protector Service 監視",
                "バックアップ失敗監視",
                "バックアップキャンセル監視",
                "バックアップ正常性監視",
            ],
            monitor_types=["Service", "EventlogWSA"],
            object_names=["AipService", "Application"],
            value_names=["CurrentState", "MonitorCountWSA"],
        )
    )
    assert candidate.profile_id == "activeimage_protector2022_serveredition"


def test_detector_selects_trellix_endpoint_security107_profile() -> None:
    candidate = detect_profile(
        DetectionInput(
            source_path=Path("import/cab/0312_Trellix Endpoint Security 107.CAB"),
            source_name="0312_Trellix Endpoint Security 107.CAB",
            source_stem="0312_Trellix Endpoint Security 107",
            manifest_product="BOM for Windows",
            group_names=["Trellix Endpoint Security 10.7 監視"],
            monitor_names=[
                "Trellix Agent Backwards Compatibility Service 監視",
                "Trellix Agent Common Services 監視",
                "Trellix Agent Service 監視",
                "Trellix Endpoint Security Web Control Service 監視",
                "McAfee Service Controller 監視",
                "McAfee Validation Trust Protection Service 監視",
                "Trellix Endpoint Security ログ監視",
            ],
            monitor_types=["Service", "EventlogWSA"],
            object_names=[
                "McAfeeFramework",
                "masvc",
                "mfewc",
                "macmnsvc",
                "mfemms",
                "mfevtp",
                "Application",
            ],
            value_names=["CurrentState", "MonitorCountWSA"],
        )
    )
    assert candidate.profile_id == "trellix_endpoint_security107"


def test_detector_selects_hyperv_profile_for_hyperv_only_cab() -> None:
    candidate = detect_profile(
        DetectionInput(
            source_path=Path("import/cab/bom8sr3-hyper-v.CAB"),
            source_name="bom8sr3-hyper-v.CAB",
            source_stem="bom8sr3-hyper-v",
            manifest_product="BOM for Windows",
            group_names=[
                "Hyper-V 監視",
                "Hyper-V  Overall health",
                "Hyper-V  Processor",
                "Hyper-V Memory",
                "Hyper-V Networking",
                "Hyper-V Storage",
            ],
            monitor_names=[
                "Hyper-V Virtual Machine Management監視",
                "Hyper-V イベントログ監視",
                "Hyper-V ホスト コンピューティング サービス監視",
                "Hyper-V Virtual Machine Health Summary -> Health Critical 監視",
            ],
            monitor_types=["Service", "EventlogWSA", "Perf"],
            object_names=[
                "vmms",
                "vmcompute",
                "\\Hyper-V Virtual Machine Health Summary\\Health Critical",
            ],
            value_names=["CurrentState", "CalculatedValue", "MonitorCountWSA"],
        )
    )
    assert candidate.profile_id == "hyperv"


def test_detector_selects_hyperv_apexone_profile_for_mixed_cab() -> None:
    candidate = detect_profile(
        DetectionInput(
            source_path=Path("samples/cab_to_excel/input/Hyper-v_ApexOne.CAB"),
            source_name="Hyper-v_ApexOne.CAB",
            source_stem="Hyper-v_ApexOne",
            manifest_product="BOM for Windows",
            group_names=[
                "Hyper-V 監視",
                "Trend Micro Apex One サーバー監視",
                "Trend Micro Apex One エージェント監視",
            ],
            monitor_names=[
                "Hyper-V Virtual Machine Management監視",
                "Hyper-V イベントログ監視",
                "Apex Oneサーバログ監視",
                "Apex One Master Service 監視",
            ],
            monitor_types=["Service", "EventlogWSA", "Perf"],
            object_names=["vmms", "vmcompute", "Trend Micro Apex One Security Agent Service"],
            value_names=["CurrentState", "CalculatedValue", "MonitorCountWSA"],
        )
    )
    assert candidate.profile_id == "hyperv_apexone"


def test_detector_does_not_match_broad_patterns_by_reverse_inclusion(tmp_path: Path) -> None:
    create_profile(
        tmp_path / "broad.yml",
        "broad",
        detection_extra="""
group_name_patterns:
  - SQL Server 2022 サービス監視
monitor_name_patterns:
  - Linux メモリ監視
priority: 100
""".strip(),
    )

    with pytest.raises(ProfileDetectionError, match="No matching profile was found"):
        detect_profile(
            DetectionInput(
                source_path=Path("import/cab/sample.cab"),
                source_name="sample.cab",
                source_stem="sample",
                manifest_product="BOM for Windows",
                group_names=["サービス監視"],
                monitor_names=["メモリ監視"],
                monitor_types=[],
                object_names=[],
                value_names=[],
            ),
            profiles_dir=tmp_path,
        )


def test_detector_raises_for_unknown_profile() -> None:
    with pytest.raises(ProfileDetectionError, match="No matching profile was found"):
        detect_profile(
            DetectionInput(
                source_path=Path("import/cab/unknown.cab"),
                source_name="unknown.cab",
                source_stem="unknown",
                manifest_product="Unknown Product",
                group_names=["Completely Unknown"],
                monitor_names=["Nothing"],
                monitor_types=["Other"],
                object_names=["foobar"],
                value_names=["baz"],
            )
        )


def test_detector_ignores_profiles_that_match_only_monitor_type(tmp_path: Path) -> None:
    create_profile(
        tmp_path / "type_only.yml",
        "type_only",
        detection_extra="""
monitor_type_patterns:
  - Service
  - EventlogWSA
priority: 100
""".strip(),
    )

    with pytest.raises(ProfileDetectionError, match="No matching profile was found"):
        detect_profile(
            DetectionInput(
                source_path=Path("import/cab/sample.cab"),
                source_name="sample.cab",
                source_stem="sample",
                manifest_product="BOM for Windows",
                group_names=["Unrelated Group"],
                monitor_names=["Unrelated Monitor"],
                monitor_types=["Service", "EventlogWSA"],
                object_names=["Application"],
                value_names=["CurrentState"],
            ),
            profiles_dir=tmp_path,
        )


def test_detector_raises_for_ambiguous_profile(tmp_path: Path) -> None:
    create_profile(tmp_path / "a.yml", "profile_a")
    create_profile(tmp_path / "b.yml", "profile_b")

    with pytest.raises(ProfileDetectionError, match="Profile detection is ambiguous"):
        detect_profile(
            DetectionInput(
                source_path=Path("import/cab/sample.cab"),
                source_name="sample.cab",
                source_stem="sample",
                manifest_product="",
                group_names=["Same Group"],
                monitor_names=["Same Monitor"],
                monitor_types=[],
                object_names=[],
                value_names=[],
            ),
            profiles_dir=tmp_path,
        )


def test_explicit_profile_bypasses_auto_detection() -> None:
    profile_path, detection_mode, reasons = resolve_profile_path(
        DetectionInput(
            source_path=Path("import/cab/unknown.cab"),
            source_name="unknown.cab",
            source_stem="unknown",
            manifest_product="Unknown Product",
            group_names=["Nothing"],
            monitor_names=["Nothing"],
            monitor_types=[],
            object_names=[],
            value_names=[],
        ),
        profile_value="profiles/sqlserver2022_windows.yml",
    )
    assert profile_path == Path("profiles/sqlserver2022_windows.yml")
    assert detection_mode == "explicit"
    assert reasons == ["profile:sqlserver2022_windows"]


def create_profile(path: Path, profile_id: str, detection_extra: str = "") -> None:
    detection_extra_block = f"\n{detection_extra}" if detection_extra else ""
    path.write_text(
        f"""
profile:
  id: {profile_id}
  name: {profile_id}
  version: 1
detection:
  group_name_patterns:
    - Same Group
  monitor_name_patterns:
    - Same Monitor
{detection_extra_block}
template:
  path: templates/dummy.xlsx
source:
  header_search_rows: 1
  sheets:
    groups:
      candidates: ["A"]
    monitors:
      candidates: ["B"]
    details:
      candidates: ["C"]
      required: false
  fields:
    group_id:
      sections: ["groups"]
      aliases: ["x"]
    group_name:
      sections: ["groups", "monitors"]
      aliases: ["y"]
    monitor_id:
      sections: ["monitors"]
      aliases: ["z"]
transform:
  replacements: {{}}
  defaults: {{}}
  derived_fields: {{}}
output:
  sheets: {{}}
  tables: {{}}
validation:
  required_fields: []
  unique_fields: []
  expected_sheets: []
security:
  secret_patterns: ["password"]
  output_policy: mask
""".strip(),
        encoding="utf-8",
    )
