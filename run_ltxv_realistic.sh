#!/usr/bin/env bash
set -euo pipefail

# One-shot runner for a realism-focused LTX-Video clip.
# Auto-downloads weights from Hugging Face cache on first run.

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_BIN="${ROOT_DIR}/.venv/bin"
PY="${VENV_BIN}/python"

if [[ ! -x "$PY" ]]; then
  echo "Python venv not found at $PY. Run: python -m venv .venv && .venv/bin/python -m ensurepip && .venv/bin/python -m pip install -e '.[inference]'" >&2
  exit 1
fi

PROMPT=${LTXV_PROMPT:-"Tight medium close-up, 35mm lens, soft key light camera-left, woman in a navy blazer speaking clearly to camera, subtle head nods and natural blinking, slight smile, bokeh office background, warm cinematic tones, slow push-in camera move"}
NEG_PROMPT=${LTXV_NEG_PROMPT:-"worst quality, inconsistent motion, blurry, jittery, distorted, cartoon, CGI"}

# Prefer the lighter 2B distilled config on MPS/CPU; override via env if desired.
DEFAULT_CONFIG="configs/ltxv-2b-0.9.8-distilled.yaml"
if command -v "${PY}" >/dev/null 2>&1; then
  DEVICE_STR="$(${PY} - <<'PY'
import torch
print("cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu"))
PY
)"
  if [[ "$DEVICE_STR" == "cuda" ]]; then
    DEFAULT_CONFIG="configs/ltxv-13b-0.9.8-distilled.yaml"
  fi
fi

HEIGHT=${LTXV_HEIGHT:-576}
WIDTH=${LTXV_WIDTH:-320}
NUM_FRAMES=${LTXV_NUM_FRAMES:-97} # must be 8n+1; 97 ~= 4s at 24 fps
FPS=${LTXV_FPS:-24}
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

echo "Done. Check $OUTPUT_DIR for the rendered mp4."
