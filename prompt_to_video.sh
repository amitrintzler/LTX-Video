#!/usr/bin/env bash
set -euo pipefail

# Generate an LTX-Video clip from a prompt.
# Usage: ./prompt_to_video.sh "your prompt here"
# Optional env overrides:
#   LTXV_PIPELINE_CONFIG (defaults to 2B distilled unless CUDA is present)
#   LTXV_HEIGHT, LTXV_WIDTH, LTXV_NUM_FRAMES, LTXV_FPS, LTXV_SEED
#   LTXV_OUTPUT_DIR, LTXV_REF_IMAGE, LTXV_REF_STRENGTH

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 \"prompt text\"" >&2
  exit 1
fi

PROMPT="$1"

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_BIN="${ROOT_DIR}/.venv/bin"
PY="${VENV_BIN}/python"

if [[ ! -x "$PY" ]]; then
  echo "Python venv not found at $PY. Create it and install deps: python -m venv .venv && .venv/bin/python -m ensurepip && .venv/bin/python -m pip install -e '.[inference]'" >&2
  exit 1
fi

# Pick lighter 2B distilled config on non-CUDA (MPS/CPU); switch to 13B on CUDA.
# Default resolutions tuned per device to avoid OOM:
#   CUDA: 1080p, 361 frames (~12s @30fps)
#   MPS: 512x288, 241 frames (~8s @30fps) – safe on M-series (Apple M4 Pro)
DEFAULT_CONFIG="configs/ltxv-2b-0.9.8-distilled.yaml"
DEVICE_STR="$("$PY" - <<'PY'
import torch
print("cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu"))
PY
)"

if [[ "$DEVICE_STR" == "cuda" ]]; then
  DEFAULT_CONFIG="configs/ltxv-13b-0.9.8-distilled.yaml"
  DEFAULT_HEIGHT=1080
  DEFAULT_WIDTH=1920
  DEFAULT_FRAMES=361
  DEFAULT_FPS=30
elif [[ "$DEVICE_STR" == "mps" ]]; then
  DEFAULT_HEIGHT=288
  DEFAULT_WIDTH=512
  DEFAULT_FRAMES=241
  DEFAULT_FPS=30
else
  DEFAULT_HEIGHT=288
  DEFAULT_WIDTH=512
  DEFAULT_FRAMES=181
  DEFAULT_FPS=24
fi

NEG_PROMPT=${LTXV_NEG_PROMPT:-"worst quality, inconsistent motion, blurry, jittery, distorted, cartoon, CGI"}
HEIGHT=${LTXV_HEIGHT:-$DEFAULT_HEIGHT}
WIDTH=${LTXV_WIDTH:-$DEFAULT_WIDTH}
NUM_FRAMES=${LTXV_NUM_FRAMES:-$DEFAULT_FRAMES} # must be 8n+1
FPS=${LTXV_FPS:-$DEFAULT_FPS}
SEED=${LTXV_SEED:-1234}
PIPELINE_CONFIG=${LTXV_PIPELINE_CONFIG:-$DEFAULT_CONFIG}
OUTPUT_DIR=${LTXV_OUTPUT_DIR:-"${ROOT_DIR}/outputs/manual"}
REF_IMAGE=${LTXV_REF_IMAGE:-}
REF_STRENGTH=${LTXV_REF_STRENGTH:-1.0}

COND_ARGS=()
if [[ -n "$REF_IMAGE" ]]; then
  if [[ ! -f "$REF_IMAGE" ]]; then
    echo "Reference image not found at $REF_IMAGE" >&2
    exit 1
  fi
  COND_ARGS+=(--conditioning_media_paths "$REF_IMAGE" --conditioning_start_frames 0 --conditioning_strengths "$REF_STRENGTH")
fi

export TOKENIZERS_PARALLELISM=${TOKENIZERS_PARALLELISM:-false}

CMD=( "$PY" inference.py
  --prompt "$PROMPT"
  --negative_prompt "$NEG_PROMPT"
  --height "$HEIGHT"
  --width "$WIDTH"
  --num_frames "$NUM_FRAMES"
  --frame_rate "$FPS"
  --seed "$SEED"
  --pipeline_config "$PIPELINE_CONFIG"
  --output_path "$OUTPUT_DIR"
)
if (( ${#COND_ARGS[@]} )); then
  CMD+=( "${COND_ARGS[@]}" )
fi

"${CMD[@]}"

echo "Done. Check $OUTPUT_DIR for output mp4."
