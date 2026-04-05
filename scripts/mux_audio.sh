#!/usr/bin/env bash
set -euo pipefail

VIDEO=${1:-"outputs/video_output_0_cinematic-photorealistic_171198_432x768x151_2.mp4"}
AUDIO=${2:-"outputs/xtts_voice_long_mix.wav"}
OUT=${3:-"outputs/with_audio_xtts_long.mov"}

FFMPEG_BIN=${FFMPEG_BIN:-""}
if [ -z "$FFMPEG_BIN" ]; then
  if command -v ffmpeg >/dev/null 2>&1; then
    FFMPEG_BIN=$(command -v ffmpeg)
  else
    FFMPEG_BIN="/opt/homebrew/lib/python3.11/site-packages/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1"
  fi
fi

"$FFMPEG_BIN" -y \
  -i "$VIDEO" \
  -i "$AUDIO" \
  -map 0:v:0 \
  -map 1:a:0 \
  -c:v copy \
  -c:a alac \
  -ac 2 \
  -ar 48000 \
  -shortest "$OUT"
