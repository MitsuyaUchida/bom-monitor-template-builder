#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "${PROJECT_DIR}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 is not installed."
  exit 1
fi

if ! python3 -m venv --help >/dev/null 2>&1; then
  echo "python3-venv is required."
  echo "Run: sudo apt update && sudo apt install -y python3-venv python3-pip"
  exit 1
fi

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python -m pip install -e .

if [[ ! -f .env ]]; then
  cp .env.example .env
fi

echo
echo "Setup completed."
echo "Activate the environment with:"
echo "  source .venv/bin/activate"
