from bom_monitor_builder.cab_excel.formatter import format_interval, format_threshold, sanitize_excel_text
from bom_monitor_builder.cab_excel.options_parser import parse_options


def test_parse_options_extracts_retry_timeout_and_script() -> None:
    options = (
        '-RetryInterval:60000 -t:60000 "-x:-ExecutionPolicy Bypass '
        '-F \\"$(InstallDir)\\bin\\support\\disklatency.ps1\\""'
    )

    parsed = parse_options(options)

    assert parsed.retry_interval == 60000
    assert parsed.timeout == 60000
    assert parsed.execution_type == "PowerShell"
    assert parsed.script_path == "$(InstallDir)\\bin\\support\\disklatency.ps1"


def test_formatter_handles_known_and_unknown_values() -> None:
    assert format_interval(5, "Minutes") == ("5分", None)
    assert format_threshold(20, "GreaterEqual") == ("20 以上", None)
    assert format_interval(5, "Weeks") == ("5 Weeks", "Weeks")
    assert format_threshold(20, "Around") == ("20 Around", "Around")


def test_formula_injection_is_sanitized() -> None:
    assert sanitize_excel_text("=SUM(A1:A2)") == "'=SUM(A1:A2)"
    assert sanitize_excel_text("+1") == "'+1"
    assert sanitize_excel_text(10) == 10
