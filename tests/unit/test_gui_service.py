from __future__ import annotations

from pathlib import Path

import pytest

import bom_monitor_builder.gui_service as gui_service
from bom_monitor_builder.gui_service import create_build_request, default_output_path


@pytest.mark.parametrize(
    ("cab_name", "expected_name"),
    [
        ("Hyper-V.CAB", "Hyper-V.xlsx"),
        ("SQL Server.cab", "SQL Server.xlsx"),
    ],
)
def test_default_output_path_uses_cab_folder_and_stem(
    tmp_path: Path,
    cab_name: str,
    expected_name: str,
) -> None:
    cab_path = tmp_path / cab_name

    assert default_output_path(cab_path) == tmp_path / expected_name


def test_create_build_request_validates_and_creates_output_folder(tmp_path: Path) -> None:
    cab_path = tmp_path / "input.CAB"
    cab_path.write_bytes(b"CAB fixture")
    output_path = tmp_path / "new-folder" / "output.xlsx"

    request = create_build_request(
        str(cab_path),
        str(output_path),
        overwrite=True,
        keep_intermediate=False,
    )

    assert request.input_path == cab_path.resolve()
    assert request.output_path == output_path.resolve()
    assert request.overwrite is True
    assert request.keep_intermediate is False
    assert output_path.parent.is_dir()


@pytest.mark.parametrize(
    ("input_value", "output_value", "message"),
    [
        ("", "output.xlsx", "CAB"),
        ("missing.CAB", "output.xlsx", "見つかりません"),
        ("input.CAB", "output.csv", ".xlsx"),
    ],
)
def test_create_build_request_reports_invalid_paths(
    tmp_path: Path,
    input_value: str,
    output_value: str,
    message: str,
) -> None:
    if input_value == "input.CAB":
        (tmp_path / input_value).write_bytes(b"CAB fixture")

    with pytest.raises(ValueError, match=message):
        create_build_request(
            str(tmp_path / input_value) if input_value else "",
            str(tmp_path / output_value),
            overwrite=True,
            keep_intermediate=False,
        )


def test_existing_output_is_rejected_when_overwrite_is_off(tmp_path: Path) -> None:
    cab_path = tmp_path / "input.CAB"
    cab_path.write_bytes(b"CAB fixture")
    output_path = tmp_path / "output.xlsx"
    output_path.write_bytes(b"existing")

    with pytest.raises(FileExistsError, match="すでに存在"):
        create_build_request(
            str(cab_path),
            str(output_path),
            overwrite=False,
            keep_intermediate=False,
        )


def test_execute_gui_build_calls_shared_engine_with_gui_options(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cab_path = tmp_path / "input.CAB"
    cab_path.write_bytes(b"CAB fixture")
    request = create_build_request(
        str(cab_path),
        str(tmp_path / "output.xlsx"),
        overwrite=True,
        keep_intermediate=True,
    )
    expected_result = object()
    calls: dict[str, object] = {}

    def fake_run_build(input_path: Path, **kwargs: object) -> object:
        calls["input_path"] = input_path
        calls.update(kwargs)
        return expected_result

    monkeypatch.setattr(gui_service, "run_build", fake_run_build)

    result = gui_service.execute_gui_build(request)

    assert result is expected_result
    assert calls == {
        "input_path": cab_path.resolve(),
        "output_path": (tmp_path / "output.xlsx").resolve(),
        "overwrite": True,
        "keep_intermediate": True,
        "verbose": True,
    }
