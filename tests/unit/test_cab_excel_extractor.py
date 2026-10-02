from __future__ import annotations

import struct
import zlib
from pathlib import Path

import pytest

from bom_monitor_builder.cab_excel.exceptions import ExtractionError
from bom_monitor_builder.cab_excel.extractor import (
    CabExtractor,
    CommandCabExtractor,
    PythonCabExtractor,
    prepare_input,
)


def _build_cab(
    path: Path,
    *,
    blocks: list[tuple[bytes, int]],
    file_name: str = "payload.bin",
    compression_type: int = 1,
) -> None:
    file_name_bytes = file_name.encode("utf-8") + b"\x00"
    coff_files = 36 + 8
    file_entry = struct.pack("<IIHHHH", sum(decoded_size for _, decoded_size in blocks), 0, 0, 0, 0, 0)
    file_entry += file_name_bytes
    data_offset = coff_files + len(file_entry)
    folder_entry = struct.pack("<IHH", data_offset, len(blocks), compression_type)
    cfdata = b"".join(
        struct.pack("<IHH", 0, len(block), decoded_size) + block
        for block, decoded_size in blocks
    )
    cabinet_size = data_offset + len(cfdata)
    header = struct.pack(
        "<4sIIIIIBBHHHHH",
        b"MSCF",
        0,
        cabinet_size,
        0,
        coff_files,
        0,
        3,
        1,
        1,
        1,
        0,
        0,
        0,
    )
    path.write_bytes(header + folder_entry + file_entry + cfdata)

def _mszip_block(payload: bytes, *, zdict: bytes | None = None) -> bytes:
    kwargs = {"level": 9, "wbits": -15}
    if zdict is not None:
        kwargs["zdict"] = zdict
    compressor = zlib.compressobj(**kwargs)
    return b"CK" + compressor.compress(payload) + compressor.flush()


def test_python_extractor_handles_single_block_mszip(tmp_path: Path) -> None:
    cab_path = tmp_path / "single.cab"
    destination = tmp_path / "out"
    payload = b"single block payload"
    _build_cab(cab_path, blocks=[(_mszip_block(payload), len(payload))])

    method = PythonCabExtractor().extract(cab_path, destination)

    assert method == "python"
    assert (destination / "payload.bin").read_bytes() == payload


def test_python_extractor_uses_previous_block_dictionary(tmp_path: Path) -> None:
    cab_path = tmp_path / "multi.cab"
    destination = tmp_path / "out"
    first_payload = b"A" * 32768
    second_payload = b"A" * 4096
    first_block = _mszip_block(first_payload)
    second_block = _mszip_block(second_payload, zdict=first_payload[-32768:])
    _build_cab(
        cab_path,
        blocks=[(first_block, len(first_payload)), (second_block, len(second_payload))],
    )

    PythonCabExtractor().extract(cab_path, destination)

    assert (destination / "payload.bin").read_bytes() == first_payload + second_payload


def test_python_extractor_rejects_invalid_ck_signature(tmp_path: Path) -> None:
    cab_path = tmp_path / "invalid-ck.cab"
    destination = tmp_path / "out"
    _build_cab(cab_path, blocks=[(b"ZZ" + zlib.compress(b"bad")[2:], 3)])

    with pytest.raises(ExtractionError, match="MSZIP block signature was invalid"):
        PythonCabExtractor().extract(cab_path, destination)


def test_prepare_input_falls_back_to_external_extractor(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cab_path = tmp_path / "fallback.cab"
    cab_path.write_bytes(b"stub")
    leaked_dir: Path | None = None

    def failing_extract(self: PythonCabExtractor, cab_file: Path, destination: Path) -> str:
        nonlocal leaked_dir
        leaked_dir = destination
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "partial.txt").write_text("partial", encoding="utf-8")
        raise ExtractionError("python failed")

    class FakeExternalExtractor(CabExtractor):
        def extract(self, cab_file: Path, destination: Path) -> str:
            assert leaked_dir is not None
            assert not leaked_dir.exists()
            destination.mkdir(parents=True, exist_ok=True)
            (destination / "payload.bin").write_bytes(b"external")
            return "cabextract"

    monkeypatch.setattr(PythonCabExtractor, "extract", failing_extract)
    monkeypatch.setattr(
        "bom_monitor_builder.cab_excel.extractor.detect_external_extractor",
        lambda: FakeExternalExtractor(),
    )

    session, kind = prepare_input(cab_path, extracted=False)
    try:
        assert kind == "cab"
        assert session.method == "cabextract"
        assert (session.extracted_root / "payload.bin").read_bytes() == b"external"
    finally:
        session.cleanup()


def test_prepare_input_reports_missing_external_extractor(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cab_path = tmp_path / "missing-tool.cab"
    cab_path.write_bytes(b"stub")

    def failing_extract(self: PythonCabExtractor, cab_file: Path, destination: Path) -> str:
        raise ExtractionError("python failed")

    monkeypatch.setattr(PythonCabExtractor, "extract", failing_extract)
    monkeypatch.setattr(
        "bom_monitor_builder.cab_excel.extractor.detect_external_extractor",
        lambda: None,
    )

    with pytest.raises(ExtractionError) as excinfo:
        prepare_input(cab_path, extracted=False)

    message = str(excinfo.value)
    assert "PythonのMSZIP展開に失敗しました" in message
    assert "sudo apt-get install cabextract" in message
    assert "--extracted" in message


def test_command_extractor_uses_cabextract_arguments(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cab_path = tmp_path / "tool.cab"
    destination = tmp_path / "out"
    cab_path.write_bytes(b"stub")
    captured: list[list[str]] = []

    def fake_run(cmd: list[str], *, capture_output: bool, text: bool, check: bool):  # type: ignore[no-untyped-def]
        captured.append(cmd)
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "payload.bin").write_bytes(b"ok")

        class Result:
            returncode = 0
            stderr = ""
            stdout = ""

        return Result()

    monkeypatch.setattr("bom_monitor_builder.cab_excel.extractor.subprocess.run", fake_run)

    method = CommandCabExtractor(["cabextract"], "cabextract").extract(cab_path, destination)

    assert method == "cabextract"
    assert captured == [["cabextract", str(cab_path), str(destination)]]
