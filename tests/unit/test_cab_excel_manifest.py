from bom_monitor_builder.cab_excel.manifest import parse_manifest_bytes


def test_parse_manifest_supports_unknown_keys() -> None:
    manifest, warnings = parse_manifest_bytes(
        b"Product: BOM for Windows\nType: Monitor_Export\nExtra: value\n"
    )

    assert manifest.product == "BOM for Windows"
    assert manifest.export_type == "Monitor_Export"
    assert manifest.values["Extra"] == "value"
    assert warnings == []


def test_parse_manifest_cp932_fallback() -> None:
    raw = "Product: テスト\nType: Monitor_Export\n".encode("cp932")

    manifest, warnings = parse_manifest_bytes(raw)

    assert manifest.product == "テスト"
    assert manifest.encoding == "cp932"
    assert warnings == []
