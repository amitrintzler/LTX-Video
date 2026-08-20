"""
SDXL + IP-Adapter character-consistent keyframe generator.

Strategy that actually locks identity (text+seed alone does not):
  1. Render ONE hero portrait of the character.
  2. Load IP-Adapter and use that hero portrait as an IMAGE reference for every
     scene keyframe, so the SAME face appears in all scenes.
  3. ip_adapter_scale balances identity (high) vs scene/composition freedom (low).

These stills then drive LTX image-to-video. Loads SDXL once for all shots.
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config as cfg  # noqa: E402

_PIPE = None
NEG = ("deformed, disfigured, extra limbs, bad anatomy, blurry, low quality, "
       "watermark, text, cartoon, 3d render, plastic skin")


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
        torch_dtype=dtype, use_safetensors=True,
        variant="fp16" if dtype == torch.float16 else None)
    pipe = pipe.to("mps" if dev.kind == "mps" else dev.kind)
    pipe.set_progress_bar_config(disable=True)
    _PIPE = pipe
    return pipe


def generate(character: str, shots: list[dict], out_dir: Path, width: int, height: int,
             base_seed: int = 1000, steps: int = 32, ip_scale: float = 0.6,
             hero_prompt: str | None = None, use_ip: bool = True) -> dict:
    """Render one keyframe per shot. With use_ip, first render a hero portrait and
    lock that face into every scene (character consistency). Without use_ip, render
    each scene independently (varied scenes, e.g. a promo). Returns {shot_id: path}."""
    import torch
    pipe = _load()
    out_dir.mkdir(parents=True, exist_ok=True)
    hero = None

    if use_ip:
        hp = hero_prompt or (f"{character}, professional cinematic headshot portrait, "
                             "looking at camera, sharp focus, 85mm, studio lighting")
        g = torch.Generator("cpu").manual_seed(base_seed)
        hero = pipe(prompt=hp, negative_prompt=NEG, num_inference_steps=steps,
                    guidance_scale=6.5, width=1024, height=1024, generator=g).images[0]
        hero.save(out_dir / "hero.png")
        print("  hero -> hero.png")
        pipe.load_ip_adapter("h94/IP-Adapter", subfolder="sdxl_models",
                             weight_name="ip-adapter_sdxl.safetensors")
        pipe.set_ip_adapter_scale(ip_scale)

    results = {}
    for s in shots:
        pre = f"{character}, " if character else ""
        prompt = f"{pre}{s['prompt']}, cinematic film still, sharp focus, detailed"
        g = torch.Generator("cpu").manual_seed(base_seed + int(s["id"]))
        kw = {"ip_adapter_image": hero} if use_ip else {}
        img = pipe(prompt=prompt, negative_prompt=NEG, num_inference_steps=steps,
                   guidance_scale=6.5, width=width, height=height, generator=g, **kw).images[0]
        p = out_dir / f"kf_{s['id']}.png"
        img.save(p)
        results[s["id"]] = p
        print(f"  keyframe {s['id']} -> {p.name}")
    return results


def release():
    """Free SDXL so it doesn't sit resident during LTX generation."""
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
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/sdxl_test")
    char = ("a confident 38-year-old male Wall Street stock trader, short dark hair, "
            "light stubble, navy pinstripe suit, white shirt, red tie")
    shots = [{"id": "01", "prompt": "on a busy New York trading floor, glowing stock tickers behind him"}]
    generate(char, shots, out, 1024, 576)
    print("done ->", out)
