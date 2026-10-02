from __future__ import annotations

import json
import struct
from pathlib import Path

from click.testing import CliRunner

from bom_monitor_builder.cli import main


def test_template_analyze_writes_iteration01_outputs(tmp_path: Path) -> None:
    source_path = create_iteration01_template_data(tmp_path)
    output_path = tmp_path / "output" / "iteration01"
    docs_path = tmp_path / "docs" / "analysis"

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "template",
            "analyze",
            "--source",
            str(source_path),
            "--output",
            str(output_path),
            "--docs-output",
            str(docs_path),
        ],
    )

    assert result.exit_code == 0
    assert "TemplateData Analyze" in result.output

    json_outputs = [
        output_path / "template_inventory.json",
        output_path / "autotemplate.json",
        output_path / "cab_structure.json",
        output_path / "html_analysis.json",
        output_path / "cab_html_mapping.json",
    ]
    for path in json_outputs:
        assert path.exists()

    doc_outputs = [
        docs_path / "iteration01_inventory.md",
        docs_path / "iteration01_cab_analysis.md",
        docs_path / "iteration01_html_analysis.md",
        docs_path / "iteration01_mapping.md",
        docs_path / "iteration01_generation_requirements.md",
    ]
    for path in doc_outputs:
        assert path.exists()

    template_inventory = json.loads((output_path / "template_inventory.json").read_text("utf-8"))
    assert len(template_inventory["files"]) == 14

    autotemplate = json.loads((output_path / "autotemplate.json").read_text("utf-8"))
    assert len(autotemplate["entries"]) == 6
    assert autotemplate["entries"][0]["type"] == "win_service"

    cab_structure = json.loads((output_path / "cab_structure.json").read_text("utf-8"))
    assert len(cab_structure["cabs"]) == 6
    assert cab_structure["cabs"][0]["file_format"] == "Microsoft Cabinet"
    assert cab_structure["cabs"][0]["internal_files"][0]["category"] == "XML"

    html_analysis = json.loads((output_path / "html_analysis.json").read_text("utf-8"))
    html_rows = {row["title"]: row for row in html_analysis["html_files"]}
    assert html_rows["0201_DNS Server"]["services"] == ["DNS"]
    assert html_rows["0201_DNS Server"]["event_logs"] == ["システム"]
    assert html_rows["0301_SQL Server"]["performance_counters"] == ["Batch Requests/sec"]

    mapping = json.loads((output_path / "cab_html_mapping.json").read_text("utf-8"))
    assert len(mapping["mappings"]) == 6
    dns_mapping = next(item for item in mapping["mappings"] if item["cab"].endswith("DNS Server.cab"))
    assert dns_mapping["html"].endswith("DNS Server.htm")
    assert dns_mapping["autotemplate_refs"][0]["type"] == "win_service"

    requirement_doc = (docs_path / "iteration01_generation_requirements.md").read_text("utf-8")
    assert "Sample Comparison" in requirement_doc
    assert "Windows標準" in requirement_doc
    assert "Arcserve" in requirement_doc


def create_iteration01_template_data(tmp_path: Path) -> Path:
    source_path = tmp_path / "import" / "TemplateData"
    source_path.mkdir(parents=True)

    samples = [
        ("0000_標準構成テンプレート", "0102_Windows システム監視 Basic", "windows", "Windows標準"),
        ("0003_Windows オプション", "0201_DNS Server", "DNS", "DNS"),
        (
            "0007_Web サーバー",
            "0104_Internet Information Services 10.0",
            "W3SVC",
            "IIS",
        ),
        (
            "0005_データベース サーバー",
            "0301_SQL Server",
            "MSSQLSERVER",
            "SQL Server",
        ),
        ("0003_Windows オプション", "1004_Hyper-V", "vmcompute", "Hyper-V"),
        ("0009_バックアップ ソフト", "0232_Arcserve RHA 18.0", "RHAEngine", "Arcserve"),
    ]

    autotemplate_lines = ["---"]
    for index, (directory, stem, service_name, _) in enumerate(samples):
        category_path = source_path / directory
        category_path.mkdir(parents=True, exist_ok=True)
        (category_path / f"{stem}.cab").write_bytes(
            make_fake_cab(
                [
                    ("monitor.xml", 128),
                    ("config.ini", 64),
                    ("icon.png", 32),
                ]
            )
        )
        (category_path / f"{stem}.htm").write_text(
            build_html(stem, service_name, index == 3),
            encoding="cp932",
        )

        if index == 0:
            (category_path / "overview.png").write_bytes(b"\x89PNG\r\n\x1a\n")

        autotemplate_lines.extend(
            [
                '- type: "win_service"',
                "  names:",
                f'    - "{service_name}"',
                "  templatepaths:",
                f"    - '{directory}\\{stem}.cab'",
            ]
        )

    (source_path / "AutoTemplate.yml").write_text(
        "\n".join(autotemplate_lines) + "\n",
        encoding="utf-8",
    )
    return source_path


def make_fake_cab(files: list[tuple[str, int]]) -> bytes:
    header_size = 44
    file_offset = 44
    folder_entry = struct.pack("<IHH", 0, 1, 1)

    file_entries = bytearray()
    for name, size in files:
        file_entries.extend(struct.pack("<IIHHHH", 0, size, 0, 0, 0, 0))
        file_entries.extend(name.encode("ascii"))
        file_entries.append(0)

    total_size = header_size + len(folder_entry) + len(file_entries)
    header = bytearray(b"MSCF")
    header.extend(struct.pack("<I", 0))
    header.extend(struct.pack("<I", total_size))
    header.extend(struct.pack("<I", 0))
    header.extend(struct.pack("<I", file_offset))
    header.extend(struct.pack("<I", 0))
    header.extend(bytes([3, 1]))
    header.extend(struct.pack("<H", 1))
    header.extend(struct.pack("<H", len(files)))
    header.extend(struct.pack("<H", 0))
    header.extend(struct.pack("<H", 0))
    header.extend(struct.pack("<H", 0))
    header.extend(folder_entry)

    return bytes(header) + bytes(file_entries)


def build_html(title: str, service_name: str, include_perf: bool) -> str:
    performance_block = ""
    if include_perf:
        performance_block = """
            <div class="monitor_item">
                <div class="monitor_desc">
                    <div class="monitor_title">
                        <div class="monitor_name">SQL Perf</div>
                        <div class="monitor_caption">性能監視</div>
                    </div>
                    <div class="monitor_note">
                        <div class="monitor_enabled">有効/無効：有効</div>
                        <div class="monitor_interval">監視間隔：5分</div>
                        <div class="monitor_type">監視タイプ：パフォーマンス監視</div>
                    </div>
                    <div class="monitor_settings">
                        <div class="monitor_object">監視対象：SQLServer</div>
                        <div class="monitor_counter">カウンター：Batch Requests/sec</div>
                        <div class="monitor_eventid"></div>
                    </div>
                    <div class="monitor_threshold">
                        <div class="monitor_threshold_yellow_value">注意：80</div>
                        <div class="monitor_threshold_red_value">警告：90</div>
                    </div>
                </div>
            </div>
        """

    return f"""<?xml version="1.0" encoding="Shift_JIS"?>
<html xml:lang="ja" lang="ja" xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=Shift_JIS"/>
    <title>{title}</title>
  </head>
  <body>
    <div class="template_data">
      <div class="package_header">
        <div class="header_template">{title}</div>
        <div class="header_package_caution">説明：{title} の説明</div>
      </div>
      <div class="group_header">
        <div class="group_name">{title} 監視</div>
      </div>
      <div class="monitor_data">
        <div class="monitor_item">
          <div class="monitor_desc">
            <div class="monitor_title">
              <div class="monitor_name">{service_name} サービス監視</div>
              <div class="monitor_caption">サービスの状態を監視します</div>
            </div>
            <div class="monitor_note">
              <div class="monitor_enabled">有効/無効：有効</div>
              <div class="monitor_interval">監視間隔：1分</div>
              <div class="monitor_type">監視タイプ：サービス監視</div>
            </div>
            <div class="monitor_settings">
              <div class="monitor_object">サービス名：{service_name}</div>
              <div class="monitor_counter">正常なサービスの状態：開始</div>
              <div class="monitor_eventid"></div>
            </div>
            <div class="monitor_threshold">
              <div class="monitor_threshold_yellow_value">注意：停止</div>
              <div class="monitor_threshold_red_value">警告：停止継続</div>
            </div>
          </div>
        </div>
        <div class="monitor_item">
          <div class="monitor_desc">
            <div class="monitor_title">
              <div class="monitor_name">{service_name} イベント監視</div>
              <div class="monitor_caption">イベントログを監視します</div>
            </div>
            <div class="monitor_note">
              <div class="monitor_enabled">有効/無効：有効</div>
              <div class="monitor_interval">監視間隔：5分</div>
              <div class="monitor_type">監視タイプ：イベントログ監視</div>
            </div>
            <div class="monitor_settings">
              <div class="monitor_object">監視ログ：システム</div>
              <div class="monitor_counter">種別：重大, エラー, 警告</div>
              <div class="monitor_eventid">イベントID：1000</div>
            </div>
            <div class="monitor_threshold">
              <div class="monitor_threshold_yellow_value">注意：1回</div>
              <div class="monitor_threshold_red_value">警告：5回</div>
            </div>
          </div>
        </div>
        {performance_block}
      </div>
    </div>
  </body>
</html>
"""
