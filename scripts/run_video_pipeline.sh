#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PIPELINE_DIR="$REPO_ROOT/video-pipeline"
PIPELINE_PY="$PIPELINE_DIR/pipeline.py"
DEFAULT_CONFIG="$PIPELINE_DIR/config.json"
PYTHON_BIN="${PYTHON_BIN:-}"

if [[ -z "$PYTHON_BIN" ]]; then
  if command -v python3.11 >/dev/null 2>&1; then
    PYTHON_BIN="python3.11"
  elif [[ -n "${VIRTUAL_ENV:-}" && -x "$VIRTUAL_ENV/bin/python" ]]; then
    PYTHON_BIN="$VIRTUAL_ENV/bin/python"
  elif [[ -x "$PWD/.venv/bin/python" ]]; then
    PYTHON_BIN="$PWD/.venv/bin/python"
  elif [[ -x "$REPO_ROOT/.venv/bin/python" ]]; then
    PYTHON_BIN="$REPO_ROOT/.venv/bin/python"
  elif [[ -x "$PIPELINE_DIR/.venv/bin/python" ]]; then
    PYTHON_BIN="$PIPELINE_DIR/.venv/bin/python"
  else
    echo "No Python 3.11 interpreter found. Install python3.11 or activate a venv with Python 3.10+." >&2
    echo "You can also set PYTHON_BIN=/path/to/python before running this launcher." >&2
    exit 1
  fi
fi

echo "Using Python: $PYTHON_BIN" >&2

usage() {
  cat <<'EOF'
Usage:
  run_video_pipeline.sh <topic-or-script> [--work-dir DIR] [--config FILE] [pipeline args...]

Examples:
  run_video_pipeline.sh "Black-Scholes options pricing"
  run_video_pipeline.sh /Users/amitri/Projects/other-repo/scripts/topic-narrated.json --stage validate
  run_video_pipeline.sh "Black-Scholes options pricing" --work-dir /Users/amitri/Projects/other-repo --stage all
EOF
}

SCRIPT_PATH=""
TMP_ROOT="${TMPDIR:-/tmp}"
WORK_DIR="${TMP_ROOT%/}/ltx-video"
CONFIG_PATH="$DEFAULT_CONFIG"
PIPELINE_ARGS=()

while (($#)); do
  case "$1" in
    --work-dir)
      if (($# < 2)); then
        echo "Missing value for --work-dir" >&2
        usage >&2
        exit 1
      fi
      WORK_DIR="$2"
      shift 2
      ;;
    --config)
      if (($# < 2)); then
        echo "Missing value for --config" >&2
        usage >&2
        exit 1
      fi
      CONFIG_PATH="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      PIPELINE_ARGS+=("$@")
      break
      ;;
    *)
      if [[ -z "$SCRIPT_PATH" ]]; then
        SCRIPT_PATH="$1"
      else
        PIPELINE_ARGS+=("$1")
      fi
      shift
      ;;
  esac
done

if [[ -z "$SCRIPT_PATH" ]]; then
  usage >&2
  exit 1
fi

if [[ ! -f "$CONFIG_PATH" ]]; then
  echo "Config not found: $CONFIG_PATH" >&2
  exit 1
fi

mkdir -p "$WORK_DIR"

TMP_CONFIG="$(mktemp /tmp/video-pipeline-config.XXXXXX)"
trap 'rm -f "$TMP_CONFIG"' EXIT

"$PYTHON_BIN" - "$CONFIG_PATH" "$WORK_DIR" "$TMP_CONFIG" <<'PY'
import json
import sys
from pathlib import Path

config_path = Path(sys.argv[1])
work_dir = sys.argv[2]
out_path = Path(sys.argv[3])

with config_path.open() as f:
    data = json.load(f)

data["work_dir"] = work_dir

with out_path.open("w") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
PY

if ((${#PIPELINE_ARGS[@]})); then
  exec "$PYTHON_BIN" "$PIPELINE_PY" "$SCRIPT_PATH" --config "$TMP_CONFIG" "${PIPELINE_ARGS[@]}"
fi

exec "$PYTHON_BIN" "$PIPELINE_PY" "$SCRIPT_PATH" --config "$TMP_CONFIG"
