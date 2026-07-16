from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    if not isinstance(data, dict):
        raise ValueError(f"Invalid configuration file: {path}")

    return data
