#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "${PROJECT_DIR}"

source .venv/bin/activate
pytest --cov=bom_monitor_builder --cov-report=term-missing
