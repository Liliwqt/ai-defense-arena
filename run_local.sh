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
if [[ -z "${FREE_ACCESS_VOUCHER:-}" ]]; then
  FREE_ACCESS_VOUCHER="$(.venv/bin/python - <<'PYVOUCHER'
import os
from pathlib import Path
import secrets
folder = Path('.local')
folder.mkdir(exist_ok=True)
path = folder / 'free-access-voucher'
try:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
except FileExistsError:
    pass
else:
    with os.fdopen(fd, 'w') as output:
        output.write(secrets.token_urlsafe(32))
os.chmod(path, 0o600)
print(path.read_text().strip())
PYVOUCHER
)"
  export FREE_ACCESS_VOUCHER
  printf 'Free-access voucher is available in .local/free-access-voucher (keep it private).\n'
fi
if [[ -z "${GOOGLE_CLIENT_ID:-}" || -z "${GOOGLE_CLIENT_SECRET:-}" || -z "${AUTH_SESSION_SECRET:-}" || -z "${AUTH_PUBLIC_BASE_URL:-}" ]]; then
  printf 'Google host sign-in needs configuration. Follow the README account setup; joining and visual previews remain available.\n'
fi

printf 'Real AI room ready at http://127.0.0.1:8000/\n'
exec .venv/bin/uvicorn game_server:app --host 127.0.0.1 --port 8000
