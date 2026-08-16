#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"
ENV_NAME="agent-control-lab"
VENV_DIR="${ROOT}/.venv"
echo "==> Repository : ${ROOT}"
echo "==> Environment: ${ENV_NAME}"
if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="${HOME}/.local/bin:${PATH}"
fi
uv venv "${VENV_DIR}" 2>/dev/null || true
uv pip install -e ".[all]"
echo "Activate: source ${VENV_DIR}/bin/activate"
echo "Run: agent-control-lab"
