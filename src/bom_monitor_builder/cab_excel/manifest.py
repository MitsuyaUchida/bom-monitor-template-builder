"""MANIFEST.MF parsing."""

from __future__ import annotations

from .models import ManifestInfo, ParseWarning


def parse_manifest_bytes(raw: bytes) -> tuple[ManifestInfo, list[ParseWarning]]:
    """Parse MANIFEST.MF bytes into a key/value dictionary."""
    warnings: list[ParseWarning] = []
    text: str | None = None
    encoding_used = "utf-8"
    for encoding in ("utf-8", "cp932"):
        try:
            text = raw.decode(encoding)
            encoding_used = encoding
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        text = raw.decode("utf-8", errors="replace")
        warnings.append(
            ParseWarning(
                code="manifest_decode_fallback",
                message="MANIFEST.MF was decoded with replacement characters.",
            )
        )

    values: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if ":" not in stripped:
            warnings.append(
                ParseWarning(
                    code="manifest_line_ignored",
                    message=f"Skipped malformed manifest line: {stripped}",
                )
            )
            continue
        key, value = stripped.split(":", 1)
        values[key.strip()] = value.strip()

    manifest = ManifestInfo(values=values, encoding=encoding_used)
    if manifest.export_type and manifest.export_type != "Monitor_Export":
        warnings.append(
            ParseWarning(
                code="manifest_type_unexpected",
                message=f"Unexpected manifest Type: {manifest.export_type}",
            )
        )
    return manifest, warnings
