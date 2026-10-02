"""Best-effort parsing for monitor Options strings."""

from __future__ import annotations

import re
import shlex

from .models import OptionsInfo

RETRY_PATTERN = re.compile(r"-RetryInterval:(\d+)")
TIMEOUT_PATTERN = re.compile(r"-t:(\d+)")
SCRIPT_PATTERN = re.compile(r"([A-Za-z0-9_$(){}\\\\/.-]+\.(?:ps1|bat|cmd|exe|vbs))", re.IGNORECASE)


def parse_options(options: str) -> OptionsInfo:
    """Parse a monitor Options string without failing the whole workflow."""
    info = OptionsInfo(original=options)
    retry_match = RETRY_PATTERN.search(options)
    if retry_match:
        info.retry_interval = int(retry_match.group(1))

    timeout_match = TIMEOUT_PATTERN.search(options)
    if timeout_match:
        info.timeout = int(timeout_match.group(1))

    script_match = SCRIPT_PATTERN.search(options)
    if script_match:
        info.script_path = script_match.group(1)
        lowered = info.script_path.lower()
        if lowered.endswith(".ps1"):
            info.execution_type = "PowerShell"
        elif lowered.endswith(".exe"):
            info.execution_type = "Executable"
        else:
            info.execution_type = "Script"

    try:
        tokens = shlex.split(options, posix=False)
    except ValueError:
        tokens = [options]

    filtered: list[str] = []
    for token in tokens:
        if token.startswith("-RetryInterval:") or token.startswith("-t:"):
            continue
        filtered.append(token)
    info.other_arguments = filtered
    return info
