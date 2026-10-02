from __future__ import annotations

from collections import Counter
from pathlib import Path

from bom_monitor_builder.template.analyze_models import AnalysisResult


def write_analysis_docs(result: AnalysisResult, docs_root: Path) -> None:
    docs_root.mkdir(parents=True, exist_ok=True)
    (docs_root / "iteration01_inventory.md").write_text(
        build_inventory_markdown(result), encoding="utf-8"
    )
    (docs_root / "iteration01_cab_analysis.md").write_text(
        build_cab_markdown(result), encoding="utf-8"
    )
    (docs_root / "iteration01_html_analysis.md").write_text(
        build_html_markdown(result), encoding="utf-8"
    )
    (docs_root / "iteration01_mapping.md").write_text(
        build_mapping_markdown(result), encoding="utf-8"
    )
    (docs_root / "iteration01_generation_requirements.md").write_text(
        build_requirement_markdown(result),
        encoding="utf-8",
    )


def build_inventory_markdown(result: AnalysisResult) -> str:
    files = result.template_inventory["files"]
    category_counter = Counter(item["category"] for item in files)
    lines = [
        "# Iteration01 Inventory",
        "",
        f"- Source: `{result.source}`",
        f"- Output: `{result.output}`",
        f"- Inventory files: {len(files)}",
        "",
        "## Category Counts",
        "",
        "| Category | Files |",
        "| --- | ---: |",
    ]
    for category, count in sorted(category_counter.items()):
        lines.append(f"| {category} | {count} |")
    return "\n".join(lines) + "\n"


def build_cab_markdown(result: AnalysisResult) -> str:
    cabs = result.cab_structure["cabs"]
    compression_counter = Counter(item["compression_format"] for item in cabs)
    lines = [
        "# Iteration01 CAB Analysis",
        "",
        f"- CAB files: {len(cabs)}",
        "",
        "## Compression Formats",
        "",
        "| Compression | Count |",
        "| --- | ---: |",
    ]
    for compression, count in sorted(compression_counter.items()):
        lines.append(f"| {compression} | {count} |")
    lines.extend(
        [
            "",
            "## Examples",
            "",
            "| CAB | Compression | Internal files | Extraction status |",
            "| --- | --- | ---: | --- |",
        ]
    )
    for item in cabs[:10]:
        lines.append(
            "| "
            f"{item['relative_path']} | {item['compression_format']} | "
            f"{len(item['internal_files'])} | {item['extraction_status']} |"
        )
    return "\n".join(lines) + "\n"


def build_html_markdown(result: AnalysisResult) -> str:
    html_files = result.html_analysis["html_files"]
    lines = [
        "# Iteration01 HTML Analysis",
        "",
        f"- HTML files: {len(html_files)}",
        "",
        "## Examples",
        "",
        "| HTML | Title | Monitor items | Services | Event logs | Related CAB |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for item in html_files[:10]:
        lines.append(
            "| "
            f"{item['relative_path']} | {item['title']} | {len(item['monitor_items'])} | "
            f"{len(item['services'])} | {len(item['event_logs'])} | {item['related_cab']} |"
        )
    return "\n".join(lines) + "\n"


def build_mapping_markdown(result: AnalysisResult) -> str:
    mappings = result.mapping["mappings"]
    lines = [
        "# Iteration01 Mapping",
        "",
        f"- Mapping records: {len(mappings)}",
        "",
        "| CAB | HTML | Images | AutoTemplate refs |",
        "| --- | --- | ---: | ---: |",
    ]
    for item in mappings[:20]:
        lines.append(
            "| "
            f"{item['cab']} | {item['html']} | {len(item['images'])} | "
            f"{len(item['autotemplate_refs'])} |"
        )
    return "\n".join(lines) + "\n"


def build_requirement_markdown(result: AnalysisResult) -> str:
    lines = [
        "# Iteration01 Generation Requirements",
        "",
        "## CAB Generation",
        "",
    ]
    for field in result.requirements.cab_required_fields:
        lines.append(f"- {field}")
    lines.extend(
        [
            "",
            "## HTML Generation",
            "",
        ]
    )
    for field in result.requirements.html_required_fields:
        lines.append(f"- {field}")
    lines.extend(
        [
            "",
            "## Sample Comparison",
            "",
            "| Sample | HTML | CAB | Monitor items | Services | Event logs | Perf counters |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for item in result.sample_comparison:
        monitor_count = item.monitor_item_count
        lines.append(
            "| "
            f"{item.sample_type} | {item.html} | {item.cab} | {monitor_count} | "
            f"{len(item.services)} | {len(item.event_logs)} | {len(item.performance_counters)} |"
        )
    return "\n".join(lines) + "\n"
