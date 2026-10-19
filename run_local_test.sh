#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ ! -x .venv/bin/python ]]; then
  printf 'Install Python dependencies using the README first.\n' >&2
  exit 1
fi
if [[ ! -d game/node_modules ]]; then
  (cd game && npm ci)
fi
(cd game && npm run build)
if [[ -z "${OPENROUTER_API_KEY:-}" ]]; then
  read -r -s -p 'OpenRouter API key (input hidden): ' OPENROUTER_API_KEY
  printf '\n'
  export OPENROUTER_API_KEY
fi
if [[ -z "$OPENROUTER_API_KEY" ]]; then
  printf 'An OpenRouter API key is required.\n' >&2
  exit 1
fi
exec .venv/bin/python -m backend.local_dev "$@"
