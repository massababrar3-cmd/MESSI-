#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export UV_CACHE_DIR="${UV_CACHE_DIR:-$PWD/.local/cache/uv}"
export NPM_CONFIG_CACHE="${NPM_CONFIG_CACHE:-$PWD/.local/cache/npm}"
if [ ! -x .venv/bin/python ]; then uv venv --python python3 .venv; fi
uv pip sync --require-hashes --python .venv/bin/python backend/requirements.txt
npm ci
PYTHONPATH=backend .venv/bin/python -m messi.bootstrap
npm run build
