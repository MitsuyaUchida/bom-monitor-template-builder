from pathlib import Path

from bom_monitor_builder.cab_excel.xml_parser import parse_extracted_monitor_tree, parse_xml_bytes


def test_parse_xml_supports_namespaces_and_type_conversion() -> None:
    raw = b"""<?xml version="1.0" encoding="UTF-8"?>
<MonitorItem xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <Type>Custom2</Type>
  <Enabled>true</Enabled>
  <Interval>5</Interval>
  <Scale>1.5</Scale>
  <Comments></Comments>
</MonitorItem>
"""

    record, warnings = parse_xml_bytes(raw, group_folder="GRP01", xml_file="Monitor/GRP01/MON01.xml")

    assert record.raw_values["Type"] == "Custom2"
    assert record.typed_values["Enabled"] is True
    assert record.typed_values["Interval"] == 5
    assert str(record.typed_values["Scale"]) == "1.5"
    assert record.raw_values["Comments"] == ""
    assert warnings == []


def test_parse_extracted_monitor_tree_reads_fixture() -> None:
    root = Path("tests/fixtures/sample_extracted")

    groups, items, warnings = parse_extracted_monitor_tree(root)

    assert len(groups) == 1
    assert len(items) == 4
    assert groups[0].raw_values["Name"] == "ディスクパフォーマンス監視"
    assert items[0].raw_values["Name"] == "レイテンシ(ディスク転送時間)"
    assert warnings == []
