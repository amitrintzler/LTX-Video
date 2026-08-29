#!/usr/bin/env bash
# Starts the Video Studio on the interpreter its dependencies are actually
# installed on. This machine has two python3s - Homebrew's 3.12 comes first
# on PATH but has none of fastapi/uvicorn/numpy/playwright installed, so a
# bare `python3 -m uvicorn` silently fails or runs a server missing half its
# capabilities. That is why the dashboard has looked broken before: not a
# missing feature, a wrong interpreter.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

# The Flow account this connects to is a paid Google AI "PLUS" plan
# (confirmed 2026-08-29 - not the free tier flow_quota.py defaults to
# otherwise), so this lifts its daily-cap assumption. Job subprocesses
# inherit this from the server process, same as everything else here.
export FLOW_TIER="${FLOW_TIER:-paid}"

PY="/Applications/Xcode.app/Contents/Developer/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3"
if [ ! -x "$PY" ]; then
  echo "Expected interpreter not found at $PY - falling back to PATH python3." >&2
  echo "If the dashboard shows missing capabilities, this is almost certainly why." >&2
  PY="python3"
fi

if ! "$PY" -c "import fastapi, uvicorn" 2>/dev/null; then
  echo "fastapi/uvicorn are not installed for $PY" >&2
  echo "Install with: $PY -m pip install --user fastapi uvicorn" >&2
  exit 1
fi

PORT="${PORT:-8765}"
if lsof -tiTCP:"$PORT" >/dev/null 2>&1; then
  echo "Port $PORT is already in use - stopping the previous instance." >&2
  lsof -tiTCP:"$PORT" | xargs kill -9
  sleep 1
fi

echo "Video Studio: $PY on port $PORT"
exec "$PY" -m uvicorn server:app --host 127.0.0.1 --port "$PORT"
