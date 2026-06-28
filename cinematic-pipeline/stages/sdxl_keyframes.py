"""
SDXL keyframe generator for character-consistent shots.

Loads SDXL ONCE and renders all shot keyframes in a single process (no per-image
model reload). Consistency strategy: a fixed, detailed CHARACTER clause prepended
to every prompt + a fixed base seed, so the same person appears across scenes.
These stills then drive LTX image-to-video, so each clip animates the same face.
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config as cfg  # noqa: E402

_PIPE = None


def _load():
    global _PIPE
    if _PIPE is not None:
        return _PIPE
    import torch
    from diffusers import StableDiffusionXLPipeline
    dev = cfg.detect_device()
    dtype = torch.float16 if dev.kind in ("cuda", "mps") else torch.float32
    pipe = StableDiffusionXLPipeline.from_pretrained(
        "stabilityai/stable-diffusion-xl-base-1.0",
        torch_dtype=dtype, use_safetensors=True, variant="fp16" if dtype == torch.float16 else None,
    )
    pipe = pipe.to("mps" if dev.kind == "mps" else dev.kind)
    pipe.set_progress_bar_config(disable=True)
    _PIPE = pipe
    return pipe


def generate(character: str, shots: list[dict], out_dir: Path, width: int, height: int,
             base_seed: int = 1000, steps: int = 30, neg: str = "") -> dict:
    """Render one keyframe per shot. Returns {shot_id: path}."""
    import torch
    pipe = _load()
    out_dir.mkdir(parents=True, exist_ok=True)
    neg = neg or ("deformed, disfigured, extra limbs, bad anatomy, blurry, low quality, "
                  "watermark, text, cartoon, 3d render")
    results = {}
    for s in shots:
        prompt = f"{character}, {s['prompt']}, cinematic photography, 35mm, sharp focus, detailed"
        # same base seed keeps facial structure stable; small per-shot offset varies pose/scene
        g = torch.Generator(device="cpu").manual_seed(base_seed + int(s["id"]))
        img = pipe(prompt=prompt, negative_prompt=neg, num_inference_steps=steps,
                   guidance_scale=6.5, width=width, height=height, generator=g).images[0]
        p = out_dir / f"kf_{s['id']}.png"
        img.save(p)
        results[s["id"]] = p
        print(f"  keyframe {s['id']} -> {p.name}")
    return results


def release():
    """Free the SDXL pipeline so it doesn't sit resident during LTX generation."""
    global _PIPE
    if _PIPE is None:
        return
    _PIPE = None
    try:
        import gc, torch
        gc.collect()
        if torch.backends.mps.is_available():
            torch.mps.empty_cache()
    except Exception:
        pass


if __name__ == "__main__":
    # smoke test: one NY trader keyframe
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/sdxl_test")
    char = ("a confident 38-year-old male Wall Street stock trader, short dark hair, "
            "light stubble, sharp navy pinstripe suit, white shirt, loosened red tie")
    shots = [{"id": "01", "prompt": "standing on a busy New York trading floor, "
              "screens glowing with stock charts behind him, intense expression"}]
    generate(char, shots, out, 1024, 576, steps=30)
    print("done ->", out)
