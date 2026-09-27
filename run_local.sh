#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
if [[ ! -x .venv/bin/uvicorn ]]; then
  printf 'Python dependencies are missing. Run: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt\n' >&2
  exit 1
fi
if [[ ! -d game/node_modules ]]; then
  (cd game && npm ci)
fi
(cd game && npm run build)

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  read -r -s -p 'OpenAI API key (input hidden): ' OPENAI_API_KEY
  printf '\n'
  export OPENAI_API_KEY
fi
if [[ -z "$OPENAI_API_KEY" ]]; then
  printf 'An OpenAI API key is required.\n' >&2
  exit 1
fi

printf 'Real AI room ready at http://127.0.0.1:8000/\n'
exec .venv/bin/uvicorn game_server:app --host 127.0.0.1 --port 8000
