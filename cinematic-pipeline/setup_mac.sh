#!/usr/bin/env bash
# One-shot local setup for the cinematic pipeline on macOS (Apple Silicon).
# Idempotent: safe to re-run. Installs everything needed for the free/local path.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # repo root (LTX-Video)
PIPE="$ROOT/cinematic-pipeline"
VOICES="${HOME}/piper-voices"

say() { printf "\033[1;36m==> %s\033[0m\n" "$*"; }

# --- 1. system tools via Homebrew ---------------------------------------------
if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew not found. Install it from https://brew.sh then re-run." >&2
  exit 1
fi
say "Installing ffmpeg + node (Homebrew)…"
brew list ffmpeg >/dev/null 2>&1 || brew install ffmpeg
brew list node   >/dev/null 2>&1 || brew install node

# --- 2. python venv -----------------------------------------------------------
say "Creating Python venv (.venv)…"
PY="$(command -v python3.11 || command -v python3)"
"$PY" -m venv "$ROOT/.venv"
# shellcheck disable=SC1091
source "$ROOT/.venv/bin/activate"
pip install --quiet --upgrade pip wheel

# --- 3. LTX-Video model deps (the generate stage) -----------------------------
say "Installing LTX-Video (torch/diffusers/transformers) — this is the big one…"
pip install --quiet -e "$ROOT[inference]"

# --- 4. pipeline deps ---------------------------------------------------------
say "Installing pipeline deps…"
pip install --quiet -r "$PIPE/requirements.txt"

# --- 5. Piper voice (offline narration) ---------------------------------------
say "Fetching a free Piper voice (en_US-lessac-medium)…"
mkdir -p "$VOICES"
BASE="https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium"
for f in en_US-lessac-medium.onnx en_US-lessac-medium.onnx.json; do
  [ -f "$VOICES/$f" ] || curl -fSL "$BASE/$f" -o "$VOICES/$f" \
    || echo "  (voice download failed — narration will be skipped until you add a model)"
done

# --- 6. report detected hardware ---------------------------------------------
say "Detected hardware / selected model tier:"
python "$PIPE/pipeline.py" --probe || true

cat <<EOF

✅ Setup complete.

Activate the env in new shells with:   source "$ROOT/.venv/bin/activate"

Try a dry-run (prints the plan, renders nothing):
    python "$PIPE/pipeline.py" "$PIPE/projects/example/project.json" --dry-run

Render the example film (needs LTX-2 weights; first run downloads them):
    python "$PIPE/pipeline.py" "$PIPE/projects/example/project.json"

Re-edit/grade only (GPU-free, fast):
    python "$PIPE/pipeline.py" "$PIPE/projects/example/project.json" --stage edit
EOF
