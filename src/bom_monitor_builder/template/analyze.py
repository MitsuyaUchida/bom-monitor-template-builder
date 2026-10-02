from __future__ import annotations

import json
import re
import struct
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

import yaml  # type: ignore[import-untyped]

from bom_monitor_builder.knowledge.yaml_tools import detect_encoding
from bom_monitor_builder.template.analyze_models import (
    AnalysisResult,
    AutoTemplateEntry,
    CabAnalysis,
    CabInternalFile,
    HtmlAnalysis,
    HtmlMonitorItem,
    MappingRecord,
    RequirementSummary,
    SampleComparisonRecord,
)
from bom_monitor_builder.template.scanner import scan_template_data

SUPPORTED_EXTENSIONS = {".cab", ".htm", ".html", ".png", ".jpg", ".jpeg", ".gif"}
SAMPLE_KEYWORDS = (
    ("Windows標準", ("Windows システム", "標準構成", "Windows 基本")),
    ("DNS", ("DNS",)),
    ("IIS", ("Internet Information Services", "IIS")),
    ("SQL Server", ("SQL Server",)),
    ("Hyper-V", ("Hyper-V",)),
    ("Arcserve", ("Arcserve", "ARCserve")),
)
TEXT_SPLIT_PATTERN = re.compile(r"[：:]", re.UNICODE)


def analyze_template_data(source_root: Path, output_root: Path) -> AnalysisResult:
    scan_result = scan_template_data(source_root, output_root)
    generated_at = datetime.now(tz=UTC).isoformat()

    template_inventory = build_template_inventory_payload(scan_result.files, generated_at)
    autotemplate_entries = analyze_autotemplate(source_root / "AutoTemplate.yml")
    autotemplate_payload = {
        "generated_at": generated_at,
        "source": str(source_root.resolve()),
        "entries": [entry.to_dict() for entry in autotemplate_entries],
    }

    cab_records = analyze_cab_files(source_root, scan_result.files)
    cab_payload = {
        "generated_at": generated_at,
        "source": str(source_root.resolve()),
        "cabs": [record.to_dict() for record in cab_records],
    }

    html_records = analyze_html_files(source_root, scan_result.files)
    html_payload = {
        "generated_at": generated_at,
        "source": str(source_root.resolve()),
        "html_files": [record.to_dict() for record in html_records],
    }

    mappings = build_mapping_records(scan_result.files, autotemplate_entries, html_records)
    mapping_payload = {
        "generated_at": generated_at,
        "source": str(source_root.resolve()),
        "mappings": [record.to_dict() for record in mappings],
    }

    sample_comparison = build_sample_comparison(html_records)
    requirements = build_requirement_summary(cab_records, html_records)

    return AnalysisResult(
        source=str(source_root.resolve()),
        output=str(output_root.resolve()),
        template_inventory=template_inventory,
        autotemplate=autotemplate_payload,
        cab_structure=cab_payload,
        html_analysis=html_payload,
        mapping=mapping_payload,
        sample_comparison=sample_comparison,
        requirements=requirements,
    )


def build_template_inventory_payload(files: list[Any], generated_at: str) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for entry in files:
        extension = entry.extension.lower()
        if extension not in SUPPORTED_EXTENSIONS and entry.file_name != "AutoTemplate.yml":
            continue
        rows.append(
            {
                "file_name": entry.file_name,
                "relative_path": entry.relative_path,
                "size": entry.size,
                "modified_at": entry.modified_at,
                "sha256": entry.sha256,
                "category": entry.directory or "ROOT",
                "category_id": entry.category_id,
                "category_name": entry.category_name,
                "file_type": entry.file_type,
            }
        )
    return {"generated_at": generated_at, "files": rows}


def analyze_autotemplate(path: Path) -> list[AutoTemplateEntry]:
    if not path.exists():
        return []

    raw_bytes = path.read_bytes()
    encoding = detect_encoding(raw_bytes)
    loaded = yaml.safe_load(raw_bytes.decode(encoding))
    if not isinstance(loaded, list):
        return []

    rows: list[AutoTemplateEntry] = []
    for index, item in enumerate(loaded):
        if not isinstance(item, dict):
            rows.append(
                AutoTemplateEntry(entry_index=index, type="UNKNOWN", names=[], templatepaths=[])
            )
            continue
        raw_names = item.get("names")
        raw_templatepaths = item.get("templatepaths")
        names = [str(value) for value in raw_names] if isinstance(raw_names, list) else []
        templatepaths = (
            [normalize_template_path(str(value)) for value in raw_templatepaths]
            if isinstance(raw_templatepaths, list)
            else []
        )
        raw_type = item.get("type")
        entry_type = str(raw_type) if raw_type is not None else "UNKNOWN"
        rows.append(
            AutoTemplateEntry(
                entry_index=index,
                type=entry_type,
                names=names,
                templatepaths=templatepaths,
            )
        )
    return rows


def analyze_cab_files(source_root: Path, files: list[Any]) -> list[CabAnalysis]:
    rows: list[CabAnalysis] = []
    for entry in files:
        if entry.file_type != "cab":
            continue
        rows.append(analyze_cab_file(source_root / entry.relative_path, entry.relative_path))
    return rows


def analyze_cab_file(path: Path, relative_path: str) -> CabAnalysis:
    raw = path.read_bytes()
    header = raw[:64]
    signature = header[:4].decode("ascii", errors="replace")
    if signature != "MSCF" or len(raw) < 36:
        return CabAnalysis(
            relative_path=relative_path,
            file_format="UNKNOWN",
            header_signature=signature or "UNKNOWN",
            header_hex=header.hex(),
            file_size=len(raw),
            folder_count="UNKNOWN",
            file_count="UNKNOWN",
            cab_version=None,
            compression_format="UNKNOWN",
            extractable=False,
            extraction_status="unsupported_header",
            internal_files=[],
            notes=["CAB signature was not recognized."],
        )

    coff_files = struct.unpack_from("<I", raw, 16)[0]
    version_minor = raw[24]
    version_major = raw[25]
    folder_count = struct.unpack_from("<H", raw, 26)[0]
    file_count = struct.unpack_from("<H", raw, 28)[0]
    flags = struct.unpack_from("<H", raw, 30)[0]
    compression_type = "UNKNOWN"
    notes: list[str] = []

    if flags != 0:
        notes.append(f"Header flags detected: 0x{flags:04x}")

    if len(raw) >= 44 and folder_count > 0:
        compression_bits = struct.unpack_from("<H", raw, 42)[0] & 0x000F
        compression_type = map_compression_type(compression_bits)

    internal_files = parse_cab_file_entries(raw, coff_files, file_count)
    extraction_status = "header_and_file_table_parsed" if internal_files else "header_only"

    return CabAnalysis(
        relative_path=relative_path,
        file_format="Microsoft Cabinet",
        header_signature=signature,
        header_hex=header.hex(),
        file_size=len(raw),
        folder_count=folder_count,
        file_count=file_count,
        cab_version=f"{version_major}.{version_minor}",
        compression_format=compression_type,
        extractable=False,
        extraction_status=extraction_status,
        internal_files=internal_files,
        notes=notes,
    )


def parse_cab_file_entries(raw: bytes, offset: int, file_count: int) -> list[CabInternalFile]:
    rows: list[CabInternalFile] = []
    cursor = offset
    for _ in range(file_count):
        if cursor + 16 > len(raw):
            break
        _, file_size, _, _, _, _ = struct.unpack_from("<IIHHHH", raw, cursor)
        cursor += 16
        name_end = raw.find(b"\x00", cursor)
        if name_end == -1:
            break
        name = decode_cab_name(raw[cursor:name_end])
        rows.append(
            CabInternalFile(
                name=name,
                size=file_size,
                category=classify_internal_file(name),
            )
        )
        cursor = name_end + 1
    return rows


def decode_cab_name(raw_name: bytes) -> str:
    for encoding in ("utf-8", "cp932", "shift_jis", "latin-1"):
        try:
            return raw_name.decode(encoding)
        except UnicodeDecodeError:
            continue
    return "UNKNOWN"


def map_compression_type(value: int) -> str:
    return {
        0: "NONE",
        1: "MSZIP",
        2: "QUANTUM",
        3: "LZX",
    }.get(value, "UNKNOWN")


def classify_internal_file(name: str) -> str:
    suffix = Path(name).suffix.lower()
    if suffix == ".xml":
        return "XML"
    if suffix == ".json":
        return "JSON"
    if suffix in {".ini", ".cfg", ".conf"}:
        return "INI"
    if suffix in {".sqlite", ".db"}:
        return "SQLite"
    if suffix in {".png", ".jpg", ".jpeg", ".gif", ".bmp"}:
        return "IMAGE"
    return "OTHER"


def analyze_html_files(source_root: Path, files: list[Any]) -> list[HtmlAnalysis]:
    rows: list[HtmlAnalysis] = []
    for entry in files:
        if entry.file_type != "html":
            continue
        rows.append(analyze_html_file(source_root / entry.relative_path, source_root))
    return rows


def analyze_html_file(path: Path, source_root: Path) -> HtmlAnalysis:
    raw_bytes = path.read_bytes()
    encoding = detect_encoding(raw_bytes)
    text = raw_bytes.decode(encoding)
    parse_text = re.sub(r"^\s*<\?xml[^>]*\?>", "", text, count=1)
    relative_path = path.relative_to(source_root).as_posix()
    try:
        root = ElementTree.fromstring(parse_text)
    except ElementTree.ParseError:
        return HtmlAnalysis(
            relative_path=relative_path,
            title=extract_title_from_text(text),
            product_name="UNKNOWN",
            description="UNKNOWN",
            monitoring_target=[],
            monitoring_items=[],
            services=[],
            event_logs=[],
            event_ids=[],
            performance_counters=[],
            thresholds=[],
            monitoring_intervals=[],
            supported_os="UNKNOWN",
            related_cab=detect_related_cab(path),
            image_references=[],
            monitor_items=[],
        )

    title = find_first_text_by_tag(root, "title") or "UNKNOWN"
    product_name = find_first_text_by_class(root, "header_template") or "UNKNOWN"
    description_parts = find_all_texts_by_class(root, "header_package_caution")
    monitoring_target = unique_preserve_order(find_all_texts_by_class(root, "group_name"))
    image_references = extract_image_references(root)
    monitor_items = extract_monitor_items(root)

    services = unique_preserve_order(
        [item.service for item in monitor_items if item.service != "UNKNOWN"]
    )
    event_logs = unique_preserve_order(
        [item.event_log for item in monitor_items if item.event_log != "UNKNOWN"]
    )
    event_ids = unique_preserve_order(
        [item.event_id for item in monitor_items if item.event_id != "UNKNOWN"]
    )
    performance_counters = unique_preserve_order(
        [
            item.performance_counter
            for item in monitor_items
            if item.performance_counter != "UNKNOWN"
        ]
    )
    thresholds = unique_preserve_order(
        [item.threshold for item in monitor_items if item.threshold != "UNKNOWN"]
    )
    monitoring_intervals = unique_preserve_order(
        [item.interval for item in monitor_items if item.interval != "UNKNOWN"]
    )
    monitoring_items = unique_preserve_order([item.monitoring_item for item in monitor_items])

    return HtmlAnalysis(
        relative_path=relative_path,
        title=title,
        product_name=product_name,
        description="\n".join(description_parts) if description_parts else "UNKNOWN",
        monitoring_target=monitoring_target,
        monitoring_items=monitoring_items,
        services=services,
        event_logs=event_logs,
        event_ids=event_ids,
        performance_counters=performance_counters,
        thresholds=thresholds,
        monitoring_intervals=monitoring_intervals,
        supported_os=find_supported_os(text),
        related_cab=detect_related_cab(path),
        image_references=image_references,
        monitor_items=monitor_items,
    )


def extract_monitor_items(root: ElementTree.Element) -> list[HtmlMonitorItem]:
    rows: list[HtmlMonitorItem] = []
    for element in root.iter():
        if get_local_name(element.tag) != "div" or element.attrib.get("class") != "monitor_item":
            continue
        fields = {
            child.attrib.get("class"): normalize_text("".join(child.itertext()))
            for child in element.iter()
            if get_local_name(child.tag) == "div" and child.attrib.get("class")
        }
        monitor_type = extract_value(fields.get("monitor_type"))
        monitor_object = extract_value(fields.get("monitor_object"))
        monitor_counter = extract_value(fields.get("monitor_counter"))
        monitor_eventid = extract_value(fields.get("monitor_eventid"))
        threshold_values = [
            normalize_text(value)
            for key, value in fields.items()
            if key and key.startswith("monitor_threshold_") and normalize_text(value)
        ]
        threshold = " | ".join(threshold_values) if threshold_values else "UNKNOWN"

        rows.append(
            HtmlMonitorItem(
                name=fields.get("monitor_name", "UNKNOWN") or "UNKNOWN",
                description=fields.get("monitor_caption", "UNKNOWN") or "UNKNOWN",
                monitor_type=monitor_type or "UNKNOWN",
                monitoring_target=monitor_type or "UNKNOWN",
                monitoring_item=infer_monitoring_item(monitor_type, monitor_object, monitor_counter),
                service=extract_service(monitor_type, monitor_object),
                event_log=extract_event_log(monitor_type, monitor_object),
                event_id=monitor_eventid or "UNKNOWN",
                performance_counter=extract_performance_counter(monitor_type, monitor_counter),
                threshold=threshold,
                interval=extract_value(fields.get("monitor_interval")) or "UNKNOWN",
                enabled=extract_value(fields.get("monitor_enabled")) or "UNKNOWN",
            )
        )
    return rows


def infer_monitoring_item(monitor_type: str, monitor_object: str, monitor_counter: str) -> str:
    if monitor_type == "サービス監視":
        return "サービス"
    if monitor_type == "イベントログ監視":
        return "イベントログ"
    if "パフォーマンス" in monitor_type:
        return "パフォーマンスカウンター"
    if monitor_counter != "UNKNOWN":
        return monitor_counter
    if monitor_object != "UNKNOWN":
        return monitor_object
    return "UNKNOWN"


def extract_service(monitor_type: str, monitor_object: str) -> str:
    if monitor_type != "サービス監視":
        return "UNKNOWN"
    return monitor_object or "UNKNOWN"


def extract_event_log(monitor_type: str, monitor_object: str) -> str:
    if monitor_type != "イベントログ監視":
        return "UNKNOWN"
    return monitor_object or "UNKNOWN"


def extract_performance_counter(monitor_type: str, monitor_counter: str) -> str:
    if "パフォーマンス" not in monitor_type:
        return "UNKNOWN"
    return monitor_counter or "UNKNOWN"


def find_supported_os(text: str) -> str:
    match = re.search(r"対応OS[：:]\s*([^\r\n<]+)", text)
    if match:
        return normalize_text(match.group(1))
    return "UNKNOWN"


def detect_related_cab(path: Path) -> str:
    for suffix in (".cab", ".CAB"):
        candidate = path.with_suffix(suffix)
        if candidate.exists():
            return candidate.name
    return "UNKNOWN"


def build_mapping_records(
    files: list[Any],
    autotemplate_entries: list[AutoTemplateEntry],
    html_records: list[HtmlAnalysis],
) -> list[MappingRecord]:
    html_by_stem = {Path(record.relative_path).with_suffix("").as_posix(): record for record in html_records}
    sibling_images: dict[str, list[str]] = defaultdict(list)
    cab_paths: set[str] = set()

    for entry in files:
        if entry.file_type == "image":
            directory = str(Path(entry.relative_path).parent.as_posix())
            sibling_images[directory].append(entry.relative_path)
        if entry.file_type == "cab":
            cab_paths.add(entry.relative_path)

    refs_by_path: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in autotemplate_entries:
        for templatepath in item.templatepaths:
            refs_by_path[templatepath].append(
                {
                    "entry_index": item.entry_index,
                    "type": item.type,
                    "names": item.names,
                }
            )

    rows: list[MappingRecord] = []
    for cab_path in sorted(cab_paths):
        template_key = Path(cab_path).with_suffix("").as_posix()
        html_record = html_by_stem.get(template_key)
        directory = str(Path(cab_path).parent.as_posix())
        image_refs = list(html_record.image_references) if html_record else []
        sibling_refs = sibling_images.get(directory, [])
        merged_images = unique_preserve_order(image_refs + sibling_refs)
        rows.append(
            MappingRecord(
                template_key=template_key,
                cab=cab_path,
                html=html_record.relative_path if html_record else "UNKNOWN",
                images=merged_images,
                autotemplate_refs=refs_by_path.get(cab_path, []),
            )
        )
    return rows


def build_sample_comparison(html_records: list[HtmlAnalysis]) -> list[SampleComparisonRecord]:
    rows: list[SampleComparisonRecord] = []
    used_paths: set[str] = set()

    for sample_type, keywords in SAMPLE_KEYWORDS:
        match = select_html_by_keywords(html_records, keywords, used_paths)
        if match is None:
            rows.append(
                SampleComparisonRecord(
                    sample_type=sample_type,
                    html="UNKNOWN",
                    cab="UNKNOWN",
                    monitor_item_count="UNKNOWN",
                    services=[],
                    event_logs=[],
                    performance_counters=[],
                    common_fields=["title", "product_name", "monitor_items"],
                    variable_fields=[],
                )
            )
            continue
        used_paths.add(match.relative_path)
        rows.append(
            SampleComparisonRecord(
                sample_type=sample_type,
                html=match.relative_path,
                cab=match.related_cab,
                monitor_item_count=len(match.monitor_items),
                services=match.services,
                event_logs=match.event_logs,
                performance_counters=match.performance_counters,
                common_fields=derive_common_fields(match),
                variable_fields=derive_variable_fields(match),
            )
        )

    return rows


def select_html_by_keywords(
    html_records: list[HtmlAnalysis], keywords: tuple[str, ...], used_paths: set[str]
) -> HtmlAnalysis | None:
    lowered_keywords = tuple(keyword.casefold() for keyword in keywords)
    for record in html_records:
        if record.relative_path in used_paths:
            continue
        haystack = " ".join((record.title, record.product_name, record.relative_path)).casefold()
        if any(keyword in haystack for keyword in lowered_keywords):
            return record
    return None


def derive_common_fields(record: HtmlAnalysis) -> list[str]:
    fields = ["title", "product_name", "monitor_items"]
    if record.services:
        fields.append("services")
    if record.monitoring_intervals:
        fields.append("monitoring_intervals")
    return fields


def derive_variable_fields(record: HtmlAnalysis) -> list[str]:
    rows: list[str] = []
    if record.event_logs:
        rows.append("event_logs")
    if record.performance_counters:
        rows.append("performance_counters")
    if record.thresholds:
        rows.append("thresholds")
    if record.supported_os != "UNKNOWN":
        rows.append("supported_os")
    return rows


def build_requirement_summary(
    cab_records: list[CabAnalysis], html_records: list[HtmlAnalysis]
) -> RequirementSummary:
    cab_fields = [
        "monitoring_target_name",
        "category",
        "cab_file_name",
        "internal_file_names",
        "compression_format",
        "html_pair_path",
    ]
    html_fields = [
        "title",
        "product_name",
        "description",
        "monitor_items",
        "services",
        "event_logs",
        "event_ids",
        "performance_counters",
        "thresholds",
        "monitoring_intervals",
        "related_cab",
        "image_references",
    ]

    if any(record.internal_files for record in cab_records):
        cab_fields.append("internal_file_categories")
    if any(record.supported_os != "UNKNOWN" for record in html_records):
        html_fields.append("supported_os")

    return RequirementSummary(
        cab_required_fields=unique_preserve_order(cab_fields),
        html_required_fields=unique_preserve_order(html_fields),
    )


def write_analysis_outputs(result: AnalysisResult, output_root: Path) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    write_json(output_root / "template_inventory.json", result.template_inventory)
    write_json(output_root / "autotemplate.json", result.autotemplate)
    write_json(output_root / "cab_structure.json", result.cab_structure)
    write_json(output_root / "html_analysis.json", result.html_analysis)
    write_json(output_root / "cab_html_mapping.json", result.mapping)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_template_path(value: str) -> str:
    return value.replace("\\", "/")


def get_local_name(tag: str) -> str:
    return tag.split("}", 1)[-1]


def find_first_text_by_tag(root: ElementTree.Element, tag_name: str) -> str | None:
    for element in root.iter():
        if get_local_name(element.tag) == tag_name:
            text = normalize_text("".join(element.itertext()))
            if text:
                return text
    return None


def find_first_text_by_class(root: ElementTree.Element, class_name: str) -> str | None:
    values = find_all_texts_by_class(root, class_name)
    if values:
        return values[0]
    return None


def find_all_texts_by_class(root: ElementTree.Element, class_name: str) -> list[str]:
    rows: list[str] = []
    for element in root.iter():
        if get_local_name(element.tag) != "div":
            continue
        if element.attrib.get("class") != class_name:
            continue
        text = normalize_text("".join(element.itertext()))
        if text:
            rows.append(text)
    return rows


def extract_image_references(root: ElementTree.Element) -> list[str]:
    rows: list[str] = []
    for element in root.iter():
        if get_local_name(element.tag) != "img":
            continue
        source = element.attrib.get("src", "").strip()
        if source and not source.startswith("data:"):
            rows.append(source)
    return unique_preserve_order(rows)


def extract_title_from_text(text: str) -> str:
    match = re.search(r"<title>(.*?)</title>", text, flags=re.IGNORECASE | re.DOTALL)
    if match:
        return normalize_text(match.group(1))
    return "UNKNOWN"


def extract_value(value: str | None) -> str:
    if not value:
        return "UNKNOWN"
    parts = TEXT_SPLIT_PATTERN.split(value, maxsplit=1)
    if len(parts) == 2:
        candidate = normalize_text(parts[1])
        return candidate or "UNKNOWN"
    candidate = normalize_text(value)
    return candidate or "UNKNOWN"


def normalize_text(value: str) -> str:
    return " ".join(value.replace("\u3000", " ").split()).strip()


def unique_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    rows: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        rows.append(value)
    return rows
