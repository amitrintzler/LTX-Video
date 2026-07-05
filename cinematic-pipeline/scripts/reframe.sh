#!/usr/bin/env bash
# Reframe a 16:9 master into social aspect ratios with a branded blurred fill.
# Usage: reframe.sh <master.mp4> <out_dir>
set -euo pipefail
FF="${FF:-/opt/homebrew/bin/ffmpeg}"
SRC="$1"; OUT="${2:-$(dirname "$1")}"
base="$(basename "${SRC%.*}")"

reframe() {  # W H suffix
  local w="$1" h="$2" sfx="$3"
  "$FF" -y -loglevel error -i "$SRC" -filter_complex \
    "[0:v]split=2[bg][fg];\
     [bg]scale=${w}:${h}:force_original_aspect_ratio=increase,crop=${w}:${h},boxblur=42:2,eq=brightness=-0.10[b];\
     [fg]scale=${w}:-2:force_original_aspect_ratio=decrease[f];\
     [b][f]overlay=(W-w)/2:(H-h)/2:format=auto,format=yuv420p[v]" \
    -map "[v]" -map 0:a? -c:v libx264 -crf 18 -c:a aac -shortest \
    "$OUT/${base}_${sfx}.mp4"
  echo "  -> $OUT/${base}_${sfx}.mp4"
}

reframe 1080 1920 vertical    # 9:16  Reels / TikTok / Shorts
reframe 1080 1080 square      # 1:1   IG / FB feed
echo "done"
