#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "${PROJECT_DIR}"

if [[ ! -f .venv/bin/activate ]]; then
  echo "ERROR: .venv does not exist."
  echo "Run: ./scripts/setup.sh"
  exit 1
fi

source .venv/bin/activate
exec bom-monitor-builder "$@"
