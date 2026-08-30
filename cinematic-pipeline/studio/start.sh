#!/usr/bin/env bash
# Start the video studio on http://127.0.0.1:8765 (this Mac only).
set -euo pipefail
cd "$(dirname "$0")"
python3 -c "import fastapi, uvicorn" 2>/dev/null || {
  echo "Missing dependencies. Install with:"
  echo "  pip3 install fastapi uvicorn"
  exit 1
}
echo "Video Studio → http://127.0.0.1:8765"
exec python3 server.py
