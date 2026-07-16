from bom_monitor_builder.analyzers.relevance import calculate_relevance


def test_exact_match() -> None:
    score, reason = calculate_relevance("BOM", "BOM")
    assert score == 100
    assert reason == "exact name match"


def test_partial_match() -> None:
    score, _ = calculate_relevance("BOM", "BOM Helper Service")
    assert score == 80


def test_no_match() -> None:
    score, _ = calculate_relevance("BOM", "SQL Server")
    assert score == 0
