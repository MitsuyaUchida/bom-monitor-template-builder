from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bom_monitor_builder.build.models import BuildResult
from bom_monitor_builder.build.service import run_build


@dataclass(frozen=True, slots=True)
class GuiBuildRequest:
    input_path: Path
    output_path: Path
    overwrite: bool
    keep_intermediate: bool


def default_output_path(cab_path: str | Path) -> Path:
    return Path(cab_path).with_suffix(".xlsx")


def create_build_request(
    input_value: str,
    output_value: str,
    *,
    overwrite: bool,
    keep_intermediate: bool,
) -> GuiBuildRequest:
    if not input_value.strip():
        raise ValueError("CABファイルを指定してください。")
    if not output_value.strip():
        raise ValueError("出力Excelの保存先を指定してください。")

    input_path = Path(input_value.strip()).expanduser().resolve()
    output_path = Path(output_value.strip()).expanduser().resolve()
    if input_path.suffix.casefold() != ".cab":
        raise ValueError("入力ファイルには .CAB ファイルを指定してください。")
    if not input_path.is_file():
        raise ValueError(f"CABファイルが見つかりません: {input_path}")
    if output_path.suffix.casefold() != ".xlsx":
        raise ValueError("出力ファイルの拡張子は .xlsx にしてください。")
    if not output_path.name:
        raise ValueError("出力Excelのファイル名を指定してください。")

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ValueError(f"出力フォルダーを作成できません: {exc}") from exc
    if not output_path.parent.is_dir():
        raise ValueError(f"出力先フォルダーがありません: {output_path.parent}")
    if output_path.exists() and not overwrite:
        raise FileExistsError(
            f"出力ファイルはすでに存在します。上書きするか、別の保存先を指定してください:\n{output_path}"
        )

    return GuiBuildRequest(input_path, output_path, overwrite, keep_intermediate)


def execute_gui_build(request: GuiBuildRequest) -> BuildResult:
    """Invoke the shared build engine directly, without launching a CLI process."""
    return run_build(
        request.input_path,
        output_path=request.output_path,
        overwrite=request.overwrite,
        keep_intermediate=request.keep_intermediate,
        verbose=True,
    )
