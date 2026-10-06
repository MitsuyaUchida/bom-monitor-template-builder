"""Monitor XML parsing."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from pathlib import Path
from xml.etree import ElementTree

from .models import ActionItem, MonitorGroup, MonitorItem, ParseWarning, ScalarValue, XmlRecord


def local_name(tag: str) -> str:
    """Return the local element name without namespace."""
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag


def element_text(element: ElementTree.Element) -> str:
    """Return normalized text content for a single element."""
    text = "".join(element.itertext()).strip()
    return text


def convert_scalar(value: str) -> ScalarValue:
    """Convert XML text to a typed scalar while preserving the raw string elsewhere."""
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if value == "":
        return ""
    if value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
        try:
            return int(value)
        except ValueError:
            return value
    try:
        decimal_value = Decimal(value)
    except InvalidOperation:
        return value
    if "." in value:
        return decimal_value
    return value


def parse_xml_bytes(
    raw: bytes,
    *,
    group_folder: str,
    xml_file: str,
) -> tuple[XmlRecord, list[ParseWarning]]:
    """Parse a monitor XML file into a typed record."""
    warnings: list[ParseWarning] = []
    try:
        root = ElementTree.fromstring(raw)
    except ElementTree.ParseError as exc:
        raise ValueError(f"Invalid XML in {xml_file}: {exc}") from exc

    raw_values: dict[str, str] = {}
    typed_values: dict[str, ScalarValue] = {}
    for child in list(root):
        key = local_name(child.tag)
        raw_text = element_text(child)
        raw_values[key] = raw_text
        typed_values[key] = convert_scalar(raw_text)

    root_name = local_name(root.tag)
    if root_name == "MonitorGroup":
        record: XmlRecord = MonitorGroup(
            kind=root_name,
            group_folder=group_folder,
            xml_file=xml_file,
            raw_values=raw_values,
            typed_values=typed_values,
            root_tag=root.tag,
        )
    elif root_name == "MonitorItem":
        record = MonitorItem(
            kind=root_name,
            group_folder=group_folder,
            xml_file=xml_file,
            raw_values=raw_values,
            typed_values=typed_values,
            root_tag=root.tag,
        )
    elif root_name == "ActionItem":
        record = ActionItem(
            kind=root_name,
            group_folder=group_folder,
            xml_file=xml_file,
            raw_values=raw_values,
            typed_values=typed_values,
            root_tag=root.tag,
        )
    else:
        raise ValueError(f"Unsupported XML root {root_name} in {xml_file}")
    return record, warnings


def parse_extracted_monitor_tree(root: Path) -> tuple[list[MonitorGroup], list[MonitorItem], list[ParseWarning]]:
    """Parse all group and monitor item XML files under an extracted tree."""
    monitor_root = root / "Monitor"
    warnings: list[ParseWarning] = []
    groups: list[MonitorGroup] = []
    items: list[MonitorItem] = []
    if not monitor_root.exists():
        return groups, items, warnings

    for group_dir in sorted(path for path in monitor_root.iterdir() if path.is_dir()):
        group_folder = group_dir.name
        for xml_path in sorted(group_dir.glob("*.xml")):
            xml_file = xml_path.relative_to(root).as_posix()
            try:
                record, record_warnings = parse_xml_bytes(
                    xml_path.read_bytes(),
                    group_folder=group_folder,
                    xml_file=xml_file,
                )
            except ValueError as exc:
                warnings.append(
                    ParseWarning(code="xml_parse_error", message=str(exc), path=xml_file)
                )
                continue
            warnings.extend(record_warnings)
            if isinstance(record, MonitorGroup):
                groups.append(record)
            elif isinstance(record, MonitorItem):
                items.append(record)
    return groups, items, warnings


def parse_extracted_action_tree(root: Path) -> list[ActionItem]:
    """Parse ActionItem XML independently from monitor profile detection."""
    monitor_root = root / "Monitor"
    actions: list[ActionItem] = []
    if not monitor_root.exists():
        return actions
    for group_dir in sorted(path for path in monitor_root.iterdir() if path.is_dir()):
        for xml_path in sorted(group_dir.glob("*ACT*.xml")):
            record, _ = parse_xml_bytes(
                xml_path.read_bytes(),
                group_folder=group_dir.name,
                xml_file=xml_path.relative_to(root).as_posix(),
            )
            if isinstance(record, ActionItem):
                actions.append(record)
    return actions
