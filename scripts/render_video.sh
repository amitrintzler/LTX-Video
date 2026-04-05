#!/usr/bin/env bash
set -euo pipefail

PROMPT=${1:-"Cinematic, photorealistic wildlife documentary. A massive silverback gorilla creature stands chest-up (no hands visible), wet fur, detailed skin pores. He speaks directly to camera: mouth clearly opening and closing, visible teeth and tongue, strong jaw motion, accurate lip articulation. He says: 'I am here now. The jungle hears us, the river moves, and your choices will echo through my kingdom.' Background: dense tropical rainforest clearing with layered foliage, depth, mist, sunbeams, distant waterfall, rich natural color grading, shallow depth of field, 35mm lens, light film grain. Clean lower third for subtitles."}

export PYTORCH_ENABLE_MPS_FALLBACK=1
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0
export TOKENIZERS_PARALLELISM=false

python3.11 run_ltx2_test.py \
  --pipeline-config configs/ltxv-2b-0.9.8-distilled-local.yaml \
  --fps 15 \
  --num-frames 151 \
  --prompt "$PROMPT"
