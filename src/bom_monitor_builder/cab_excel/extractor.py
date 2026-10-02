"""CAB extraction support."""

from __future__ import annotations

import hashlib
import shutil
import struct
import subprocess
import zlib
from abc import ABC, abstractmethod
from pathlib import Path
from tempfile import TemporaryDirectory

from .exceptions import ExtractionError
from .models import CabArchiveLayout, CabFileEntry, CabFolderEntry


def _decode_name(raw_name: bytes) -> str:
    for encoding in ("utf-8", "cp932", "shift_jis", "latin-1"):
        try:
            return raw_name.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw_name.decode("latin-1", errors="replace")


def _normalize_relative_path(name: str) -> Path:
    normalized = name.replace("\\", "/")
    path = Path(normalized)
    if path.is_absolute():
        raise ExtractionError(f"Absolute CAB path is not allowed: {name}")
    if any(part in {"..", ""} for part in path.parts):
        raise ExtractionError(f"Unsafe CAB path is not allowed: {name}")
    return path


def parse_cab_layout(raw: bytes) -> CabArchiveLayout:
    """Parse CAB headers, reserve sizes, folder entries, and file entries."""
    if raw[:4] != b"MSCF" or len(raw) < 36:
        raise ExtractionError("Input file is not a valid Microsoft Cabinet archive.")

    _, _, _, _, coff_files, _, _, _, folder_count, file_count, flags, _, _ = struct.unpack_from(
        "<4sIIIIIBBHHHHH", raw, 0
    )
    cursor = 36
    reserve_per_folder = 0
    reserve_per_data = 0
    if flags & 0x0004:
        reserve_header, reserve_per_folder, reserve_per_data = struct.unpack_from(
            "<HBB", raw, cursor
        )
        cursor += 4 + reserve_header

    folder_entries: list[CabFolderEntry] = []
    for _ in range(folder_count):
        data_offset, data_block_count, compression_type = struct.unpack_from("<IHH", raw, cursor)
        folder_entries.append(
            CabFolderEntry(
                data_offset=data_offset,
                data_block_count=data_block_count,
                compression_type=compression_type & 0x000F,
            )
        )
        cursor += 8 + reserve_per_folder

    file_entries: list[CabFileEntry] = []
    cursor = coff_files
    for _ in range(file_count):
        size, offset, folder_index, _, _, _ = struct.unpack_from("<IIHHHH", raw, cursor)
        cursor += 16
        name_end = raw.find(b"\x00", cursor)
        if name_end == -1:
            raise ExtractionError("CAB file table entry is truncated.")
        name = _decode_name(raw[cursor:name_end])
        file_entries.append(
            CabFileEntry(name=name, size=size, offset=offset, folder_index=folder_index)
        )
        cursor = name_end + 1

    return CabArchiveLayout(
        file_entries=file_entries,
        folder_entries=folder_entries,
        reserve_per_folder=reserve_per_folder,
        reserve_per_data=reserve_per_data,
    )


class CabExtractor(ABC):
    """CAB extraction contract."""

    @abstractmethod
    def extract(self, cab_path: Path, destination: Path) -> str:
        """Extract a CAB file to destination and return method label."""


class PythonCabExtractor(CabExtractor):
    """Extract NONE and MSZIP CAB archives using Python."""

    def extract(self, cab_path: Path, destination: Path) -> str:
        raw = cab_path.read_bytes()
        layout = parse_cab_layout(raw)
        folder_data: list[bytes] = []
        for folder in layout.folder_entries:
            cursor = folder.data_offset
            buffer = self._extract_folder(raw, cursor, folder, layout.reserve_per_data)
            folder_data.append(bytes(buffer))

        destination.mkdir(parents=True, exist_ok=True)
        for entry in layout.file_entries:
            relative_path = _normalize_relative_path(entry.name)
            target_path = destination / relative_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            folder_bytes = folder_data[entry.folder_index]
            payload = folder_bytes[entry.offset : entry.offset + entry.size]
            target_path.write_bytes(payload)
        return "python"

    def _extract_folder(
        self,
        raw: bytes,
        cursor: int,
        folder: CabFolderEntry,
        reserve_per_data: int,
    ) -> bytearray:
        buffer = bytearray()
        previous_window = b""
        for block_index in range(folder.data_block_count):
            _, compressed_size, _ = struct.unpack_from("<IHH", raw, cursor)
            cursor += 8 + reserve_per_data
            block = raw[cursor : cursor + compressed_size]
            cursor += compressed_size
            try:
                decoded = self._decode_block(
                    block,
                    compression_type=folder.compression_type,
                    previous_window=previous_window,
                    block_index=block_index,
                )
            except zlib.error as exc:
                raise ExtractionError(
                    f"Python MSZIP extraction failed at CFDATA block {block_index + 1}: {exc}"
                ) from exc
            buffer.extend(decoded)
            previous_window = bytes(buffer[-32768:])
        return buffer

    def _decode_block(
        self,
        block: bytes,
        *,
        compression_type: int,
        previous_window: bytes,
        block_index: int,
    ) -> bytes:
        if compression_type == 0:
            return block
        if compression_type != 1:
            raise ExtractionError(f"Unsupported CAB compression type: {compression_type}")
        if len(block) < 2 or block[:2] != b"CK":
            raise ExtractionError(
                f"MSZIP block signature was invalid at CFDATA block {block_index + 1}."
            )
        payload = block[2:]
        if block_index == 0:
            return zlib.decompress(payload, -15)
        decompressor = zlib.decompressobj(wbits=-15, zdict=previous_window)
        return decompressor.decompress(payload) + decompressor.flush()


class CommandCabExtractor(CabExtractor):
    """Extract CAB archives with an external command."""

    def __init__(self, command: list[str], method_name: str) -> None:
        self.command = command
        self.method_name = method_name

    def extract(self, cab_path: Path, destination: Path) -> str:
        destination.mkdir(parents=True, exist_ok=True)
        if self.method_name == "expand":
            cmd = self.command + [str(cab_path), "-F:*", str(destination)]
        elif self.method_name in {"7z", "7zz"}:
            cmd = self.command + ["x", str(cab_path), f"-o{destination}", "-y"]
        else:
            cmd = self.command + [str(cab_path), str(destination)]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise ExtractionError(
                f"{self.method_name} failed: {result.stderr.strip() or result.stdout.strip()}"
            )
        _validate_extracted_paths(destination)
        return self.method_name


def detect_external_extractor() -> CabExtractor | None:
    """Detect external CAB extractor commands by platform order."""
    candidates = [
        (["expand.exe"], "expand"),
        (["7zz"], "7zz"),
        (["7z"], "7z"),
        (["cabextract"], "cabextract"),
    ]
    for command, method_name in candidates:
        if shutil.which(command[0]):
            return CommandCabExtractor(command, method_name)
    return None


def _validate_extracted_paths(destination: Path) -> None:
    base = destination.resolve()
    for path in destination.rglob("*"):
        resolved = path.resolve()
        resolved.relative_to(base)


class ExtractionSession:
    """Managed extraction lifecycle."""

    def __init__(self, extracted_root: Path, method: str, temp_dir: TemporaryDirectory[str] | None) -> None:
        self.extracted_root = extracted_root
        self.method = method
        self._temp_dir = temp_dir

    def cleanup(self) -> None:
        if self._temp_dir is not None:
            self._temp_dir.cleanup()


def prepare_input(input_path: Path, *, extracted: bool) -> tuple[ExtractionSession, str]:
    """Prepare an extracted root from either an extracted directory or a CAB file."""
    if extracted:
        if not input_path.is_dir():
            raise ExtractionError(f"Extracted input is not a directory: {input_path}")
        return ExtractionSession(input_path, "pre-extracted", None), "directory"
    if not input_path.is_file():
        raise ExtractionError(f"CAB input is not a file: {input_path}")

    temp_dir = TemporaryDirectory(prefix="bom-cab-excel-")
    extracted_root = Path(temp_dir.name)
    python_extractor = PythonCabExtractor()
    try:
        method = python_extractor.extract(input_path, extracted_root)
    except ExtractionError:
        temp_dir.cleanup()
        external = detect_external_extractor()
        if external is None:
            raise ExtractionError(_build_python_extract_failure_message(input_path))
        temp_dir = TemporaryDirectory(prefix="bom-cab-excel-")
        extracted_root = Path(temp_dir.name)
        method = external.extract(input_path, extracted_root)
    return ExtractionSession(extracted_root, method, temp_dir), "cab"


def _build_python_extract_failure_message(input_path: Path) -> str:
    return (
        f"PythonのMSZIP展開に失敗しました: {input_path}\n"
        "外部展開ツールを使用してください。`cabextract` は Ubuntu/Debian では "
        "`sudo apt-get install cabextract` でインストールできます。\n"
        "あらかじめ展開済みフォルダーを用意して `--extracted` 付きで入力することもできます。"
    )


def sha256_for_path(path: Path) -> str:
    """Calculate SHA-256 for a file or directory tree."""
    digest = hashlib.sha256()
    if path.is_file():
        digest.update(path.read_bytes())
        return digest.hexdigest()
    for child in sorted(path.rglob("*")):
        if child.is_dir():
            continue
        digest.update(child.relative_to(path).as_posix().encode("utf-8"))
        digest.update(child.read_bytes())
    return digest.hexdigest()
