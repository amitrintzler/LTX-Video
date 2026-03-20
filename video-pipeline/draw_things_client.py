"""
draw_things_client.py — Thin wrapper around Draw Things local HTTP API

Draw Things exposes an SD-compatible REST API on localhost:7860.
  GET  /                      → current config JSON
  POST /sdapi/v1/txt2img      → text-to-image (returns base64 images)
  POST /sdapi/v1/img2img      → image-to-image (returns base64 images)
  GET  /sdapi/v1/progress     → generation progress (0.0–1.0)

For video generation, Draw Things uses the same txt2img / img2img endpoints
but with extra parameters in `alwayson_scripts` when a video model is loaded.
The response contains video frames as a sequence of base64 images which we
then encode to MP4 via FFmpeg.

Models are specified per-request via the "model" / "refiner_model" keys in
the payload. Draw Things reloads the model automatically when it changes.
"""

from __future__ import annotations
import base64
import logging
import time
import requests
from pathlib import Path


log = logging.getLogger("draw_things_client")


class DrawThingsError(RuntimeError):
    pass


class DrawThingsClient:
    def __init__(self, host: str = "http://localhost:7860", timeout: int = 600):
        self.host = host.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    # ── Health ──────────────────────────────────────────────────────
    def ping(self) -> dict:
        """Returns current Draw Things config. Raises if server is down."""
        try:
            r = self.session.get(f"{self.host}/", timeout=10)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            raise DrawThingsError(
                f"Draw Things API unreachable at {self.host}.\n"
                "→ Open Draw Things, go to Settings → API Server → Enable HTTP Server."
            ) from e

    # ── Progress ─────────────────────────────────────────────────────
    def progress(self) -> float:
        """Returns generation progress 0.0–1.0."""
        try:
            r = self.session.get(
                f"{self.host}/sdapi/v1/progress",
                params={"skip_current_image": "true"},
                timeout=10,
            )
            return r.json().get("progress", 0.0)
        except Exception:
            return 0.0

    def wait_for_idle(self, poll_interval: float = 3.0):
        """Block until the server reports idle (progress == 0 after starting)."""
        time.sleep(2)  # let it start
        while True:
            p = self.progress()
            if p == 0.0:
                break
            log.debug(f"  progress: {p:.0%}")
            time.sleep(poll_interval)

    # ── Image generation (txt2img) ───────────────────────────────────
    def txt2img(self, prompt: str, negative: str = "", **kwargs) -> list[bytes]:
        """
        Generate image(s) from text. Returns list of PNG bytes.
        kwargs: width, height, steps, cfg_scale, seed, batch_size, sampler_name, model
        """
        payload = {
            "prompt": prompt,
            "negative_prompt": negative,
            "width": kwargs.get("width", 1024),
            "height": kwargs.get("height", 576),
            "steps": kwargs.get("steps", 25),
            "cfg_scale": kwargs.get("cfg_scale", 7.0),
            "seed": kwargs.get("seed", -1),
            "batch_size": kwargs.get("batch_size", 1),
            "sampler_name": kwargs.get("sampler_name", "DPM++ 2M Karras"),
        }
        if kwargs.get("model"):
            payload["model"] = kwargs["model"]
        return self._post_generation("/sdapi/v1/txt2img", payload)

    # ── Video generation (img2img with video model) ──────────────────
    def img2video(
        self,
        image_path: Path,
        prompt: str,
        negative: str = "",
        **kwargs,
    ) -> list[bytes]:
        """
        Animate a storyboard image into video frames.
        Draw Things uses img2img endpoint with video-specific params.
        Returns list of PNG frame bytes (one per generated frame).

        kwargs: width, height, steps, cfg_scale, seed,
                frames (number of video frames), fps, model, refiner_model
        """
        img_b64 = base64.b64encode(image_path.read_bytes()).decode()
        payload = {
            "prompt": prompt,
            "negative_prompt": negative,
            "init_images": [img_b64],
            "width": kwargs.get("width", 1024),
            "height": kwargs.get("height", 576),
            "steps": kwargs.get("steps", 30),
            "cfg_scale": kwargs.get("cfg_scale", 6.0),
            "seed": kwargs.get("seed", -1),
            "denoising_strength": kwargs.get("denoising_strength", 1.0),
            "num_frames": kwargs.get("frames", 81),
            "fps": kwargs.get("fps", 16),
        }
        if kwargs.get("model"):
            payload["model"] = kwargs["model"]
        if kwargs.get("refiner_model"):
            payload["refiner_model"] = kwargs["refiner_model"]
        if kwargs.get("tea_cache"):
            payload["tea_cache"] = True
        return self._post_generation("/sdapi/v1/img2img", payload)

    # ── Internal ─────────────────────────────────────────────────────
    def _post_generation(self, endpoint: str, payload: dict) -> list[bytes]:
        url = f"{self.host}{endpoint}"
        log.debug(f"POST {url} — prompt: {payload.get('prompt','')[:60]}…")
        try:
            r = self.session.post(url, json=payload, timeout=self.timeout)
            r.raise_for_status()
        except requests.exceptions.Timeout:
            raise DrawThingsError(
                f"Generation timed out after {self.timeout}s. "
                "Increase api_timeout in config.json or reduce frame count."
            )
        except requests.exceptions.HTTPError as e:
            raise DrawThingsError(f"API error {r.status_code}: {r.text[:300]}") from e

        data = r.json()
        images_b64 = data.get("images", [])
        if not images_b64:
            raise DrawThingsError(f"No images returned from {endpoint}. Response: {data}")

        return [base64.b64decode(img) for img in images_b64]
