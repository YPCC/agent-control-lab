#!/usr/bin/env bash
set -euo pipefail
PORT="${AGT_OFFICIAL_PORT:-8501}"
CACHE="${HOME}/.cache/agent-governance-toolkit"
if [[ ! -d "$CACHE" ]]; then
  git clone --depth 1 https://github.com/microsoft/agent-governance-toolkit.git "$CACHE"
fi
cd "$CACHE"
if [[ -f dashboard/app.py ]]; then
  streamlit run dashboard/app.py --server.port "$PORT"
elif [[ -f apps/dashboard/app.py ]]; then
  streamlit run apps/dashboard/app.py --server.port "$PORT"
else
  echo "Use companion: streamlit run dashboards/companion_app.py --server.port 8502"
fi
