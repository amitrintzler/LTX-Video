#!/usr/bin/env bash
# Usage: bash /path/to/LTX-Video/scripts/create-video.sh <topic.json> --dest=<output-dir>
#
# Runs the full video pipeline for a topic JSON file and copies the resulting
# MP4(s) into the destination directory.
#
#   --dest=DIR     Where to copy the final MP4(s). Defaults to ./output.
#   --work-dir=DIR Scratch directory for pipeline state. Defaults to ./.ltx-scratch-<slug>.
#   --stage=STAGE  Limit pipeline to a specific stage (e.g. script, render).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIPELINE_LAUNCHER="$SCRIPT_DIR/run_video_pipeline.sh"

TOPIC_JSON=""
DEST_DIR=""
WORK_DIR_OVERRIDE=""
PIPELINE_ARGS=()

for arg in "$@"; do
  case "$arg" in
    --dest=*)   DEST_DIR="${arg#--dest=}" ;;
    --work-dir=*) WORK_DIR_OVERRIDE="${arg#--work-dir=}" ;;
    --*)        PIPELINE_ARGS+=("$arg") ;;
    *)          TOPIC_JSON="$arg" ;;
  esac
done

if [ -z "$TOPIC_JSON" ]; then
  echo "Usage: $0 <topic.json> [--dest=DIR] [--work-dir=DIR] [--stage=STAGE]" >&2
  exit 1
fi

TOPIC_JSON="$(python3 -c "import os,sys; print(os.path.abspath(sys.argv[1]))" "$TOPIC_JSON")"

SLUG="$(python3 -c "
import json, sys
d = json.load(open(sys.argv[1]))
print(d.get('slug') or d.get('lesson_id') or d.get('id') or 'video')
" "$TOPIC_JSON")"

WORK_DIR="${WORK_DIR_OVERRIDE:-"$(pwd)/.ltx-scratch-${SLUG}"}"
DEST_DIR="${DEST_DIR:-"$(pwd)/output"}"
OUTPUT_DIR="$WORK_DIR/output"

echo "Topic:    $TOPIC_JSON"
echo "Slug:     $SLUG"
echo "Work dir: $WORK_DIR"
echo "Dest:     $DEST_DIR"

bash "$PIPELINE_LAUNCHER" "$TOPIC_JSON" --work-dir "$WORK_DIR" "${PIPELINE_ARGS[@]+"${PIPELINE_ARGS[@]}"}"

mkdir -p "$DEST_DIR"

SHORT_VIDEO="$(find "$OUTPUT_DIR" -maxdepth 1 -name "*-narrated.mp4" 2>/dev/null | sort | tail -1)"
if [ -z "$SHORT_VIDEO" ]; then
  SHORT_VIDEO="$(find "$OUTPUT_DIR" -maxdepth 1 -name "*.mp4" 2>/dev/null | grep -v "companion" | sort | tail -1)"
fi
if [ -n "$SHORT_VIDEO" ]; then
  cp "$SHORT_VIDEO" "$DEST_DIR/${SLUG}-short.mp4"
  cp "$SHORT_VIDEO" "$DEST_DIR/${SLUG}.mp4"
  echo "Short video -> $DEST_DIR/${SLUG}-short.mp4"
  echo "Primary     -> $DEST_DIR/${SLUG}.mp4"
else
  echo "Warning: no short video found in $OUTPUT_DIR" >&2
fi

LONG_VIDEO="$(find "$OUTPUT_DIR" -maxdepth 1 -name "*-companion-long.mp4" 2>/dev/null | sort | tail -1)"
if [ -n "$LONG_VIDEO" ]; then
  cp "$LONG_VIDEO" "$DEST_DIR/${SLUG}-long.mp4"
  echo "Long video  -> $DEST_DIR/${SLUG}-long.mp4"
fi
