#!/usr/bin/env bash
set -euo pipefail

TEXT=${1:-"I am here now. The jungle hears us, the river moves, and your choices will echo through my kingdom."}
SPEAKER_WAV=${2:-"/path/to/clean_voice.wav"}
AMBIENT_WAV=${3:-"outputs/ambient_jungle_v3.wav"}
OUT_VOICE=${4:-"outputs/xtts_voice_long.wav"}
OUT_MIX=${5:-"outputs/xtts_voice_long_mix.wav"}

export COQUI_TOS_AGREED=1

python3.11 xtts_tts.py \
  --text "$TEXT" \
  --speaker-wav "$SPEAKER_WAV" \
  --out "$OUT_VOICE" \
  --ambient "$AMBIENT_WAV" \
  --mix-out "$OUT_MIX"
