#!/usr/bin/env bash
set -euo pipefail

# Add/replace audio on a video using ffmpeg.
# Usage: ./add_audio_to_video.sh input_video.mp4 input_audio.wav output_with_audio.mp4
# Optional env: AUDIO_OFFSET (seconds, can be negative), AUDIO_VOLUME (e.g., 1.0, 0.8)

if [[ $# -lt 3 ]]; then
  echo "Usage: $0 <video.mp4> <audio.wav|mp3> <output.mp4>" >&2
  exit 1
fi

VIDEO="$1"
AUDIO="$2"
OUT="$3"
OFFSET=${AUDIO_OFFSET:-0}
VOLUME=${AUDIO_VOLUME:-1.0}

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ffmpeg is required. Install it and retry." >&2
  exit 1
fi
if [[ ! -f "$VIDEO" ]]; then
  echo "Video not found: $VIDEO" >&2
  exit 1
fi
if [[ ! -f "$AUDIO" ]]; then
  echo "Audio not found: $AUDIO" >&2
  exit 1
fi

# -itsoffset aligns audio; -shortest trims/avoids overrun; re-encodes audio to AAC.
ffmpeg -y -i "$VIDEO" -itsoffset "$OFFSET" -i "$AUDIO" \
  -filter:a "volume=${VOLUME}" \
  -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -shortest "$OUT"

echo "Wrote $OUT"
