"""
stages/renderers/html_anim.py — Renderer: HTML/CSS educational motion scene

Builds a polished HTML scene in the browser, captures a rendered frame with
Playwright, and encodes that frame to MP4 with FFmpeg.
"""

from __future__ import annotations

import html
import re
import subprocess
import tempfile
from pathlib import Path

from PIL import Image  # noqa: F401 - keeps Pillow listed as a hard dependency

from config import PipelineConfig


class HTMLAnimRenderError(RuntimeError):
    pass


def render(scene: dict, config: PipelineConfig, out_path: Path) -> Path:
    title = str(scene.get("title", "Untitled")).strip() or "Untitled"
    narration = str(scene.get("narration", "")).strip()
    description = str(scene.get("description", "")).strip()
    style = str(scene.get("style", "")).strip()
    duration_sec = max(1, int(round(float(scene.get("duration_sec", 8)))))
    width = int(getattr(config, "video_width", 1920))
    height = int(getattr(config, "video_height", 1080))
    fps = int(getattr(config, "video_fps", 60))

    with tempfile.TemporaryDirectory(prefix="html_anim_render_") as tmp_dir:
        tmp_dir = Path(tmp_dir)
        html_path = tmp_dir / "scene.html"
        png_path = tmp_dir / "frame.png"

        html_path.write_text(
            _build_html(
                title=title,
                narration=narration,
                description=description,
                style=style,
                width=width,
                height=height,
            ),
            encoding="utf-8",
        )
        _capture_html_frame(html_path, png_path, width, height)
        return _encode_frame_video(png_path, out_path, duration_sec, fps)


def _build_html(*, title: str, narration: str, description: str, style: str, width: int, height: int) -> str:
    bg_color, primary_color, text_color, muted_color = _theme_from_style(style)
    bullets = _description_bullets(description)
    bullet_html = "".join(f"<li>{html.escape(item)}</li>" for item in bullets) or "<li>Visual direction not specified.</li>"
    n_lines = html.escape(narration).replace("\n", "<br>")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width={width}, height={height}, initial-scale=1.0" />
  <style>
    :root {{
      --bg: {bg_color};
      --primary: {primary_color};
      --text: {text_color};
      --muted: {muted_color};
      --panel: rgba(255, 255, 255, 0.06);
      --edge: rgba(255, 255, 255, 0.14);
    }}
    * {{ box-sizing: border-box; }}
    html, body {{
      width: 100%;
      height: 100%;
      margin: 0;
      overflow: hidden;
      background:
        radial-gradient(circle at 20% 20%, rgba(255, 215, 0, 0.16), transparent 22%),
        radial-gradient(circle at 80% 20%, rgba(0, 200, 150, 0.10), transparent 24%),
        radial-gradient(circle at 50% 80%, rgba(255, 255, 255, 0.07), transparent 28%),
        var(--bg);
      color: var(--text);
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    .frame {{
      position: relative;
      width: 100vw;
      height: 100vh;
      padding: 5.5vh 6vw;
    }}
    .glow {{
      position: absolute;
      inset: 0;
      background:
        linear-gradient(120deg, rgba(255, 215, 0, 0.03), transparent 40%),
        linear-gradient(300deg, rgba(255, 255, 255, 0.03), transparent 50%);
      pointer-events: none;
    }}
    .hero {{
      position: relative;
      border: 1px solid var(--edge);
      border-radius: 28px;
      padding: 36px 38px 34px;
      background: linear-gradient(180deg, rgba(255,255,255,0.09), rgba(255,255,255,0.04));
      box-shadow: 0 24px 80px rgba(0,0,0,0.32);
      overflow: hidden;
    }}
    .hero::before {{
      content: "";
      position: absolute;
      top: 0;
      left: 0;
      width: 14px;
      height: 100%;
      background: var(--primary);
    }}
    .eyebrow {{
      margin: 0 0 14px;
      font-size: 14px;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: var(--muted);
    }}
    h1 {{
      margin: 0;
      font-size: 58px;
      line-height: 1.02;
      letter-spacing: -0.04em;
      max-width: 16ch;
    }}
    .narration {{
      margin: 16px 0 0;
      max-width: 68ch;
      font-size: 21px;
      line-height: 1.5;
      color: var(--muted);
    }}
    .content {{
      display: grid;
      grid-template-columns: 1.1fr 0.9fr;
      gap: 24px;
      margin-top: 24px;
      height: calc(100vh - 5.5vh * 2 - 240px);
      min-height: 0;
    }}
    .panel {{
      border: 1px solid var(--edge);
      border-radius: 26px;
      background: var(--panel);
      backdrop-filter: blur(8px);
      padding: 28px;
      position: relative;
      overflow: hidden;
    }}
    .panel h2 {{
      margin: 0 0 16px;
      font-size: 20px;
      color: var(--primary);
      text-transform: uppercase;
      letter-spacing: 0.12em;
    }}
    .panel ul {{
      margin: 0;
      padding-left: 22px;
      font-size: 19px;
      line-height: 1.5;
      color: var(--text);
    }}
    .panel li {{
      margin: 0 0 14px;
    }}
    .motion {{
      display: grid;
      gap: 18px;
    }}
    .orb-row {{
      display: flex;
      gap: 14px;
      align-items: center;
      flex-wrap: wrap;
    }}
    .orb {{
      width: 78px;
      height: 78px;
      border-radius: 50%;
      border: 1px solid rgba(255,255,255,0.18);
      background:
        radial-gradient(circle at 35% 35%, rgba(255,255,255,0.45), transparent 24%),
        linear-gradient(135deg, rgba(255,215,0,0.95), rgba(255,120,80,0.65));
      box-shadow: 0 0 26px rgba(255, 215, 0, 0.25);
      animation: float 3.4s ease-in-out infinite;
    }}
    .orb:nth-child(2) {{ animation-delay: 0.35s; }}
    .orb:nth-child(3) {{ animation-delay: 0.7s; }}
    .bar {{
      height: 16px;
      border-radius: 999px;
      background: rgba(255,255,255,0.08);
      border: 1px solid rgba(255,255,255,0.14);
      overflow: hidden;
    }}
    .bar > span {{
      display: block;
      width: 76%;
      height: 100%;
      background: linear-gradient(90deg, var(--primary), rgba(0, 200, 150, 0.92));
      animation: fill 2.8s ease-in-out infinite alternate;
    }}
    .caption {{
      color: var(--muted);
      font-size: 16px;
      line-height: 1.45;
    }}
    .footer {{
      position: absolute;
      left: 6vw;
      right: 6vw;
      bottom: 4.6vh;
      display: flex;
      justify-content: space-between;
      align-items: center;
      color: var(--muted);
      font-size: 14px;
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }}
    @keyframes float {{
      0%, 100% {{ transform: translateY(0px) scale(1); }}
      50% {{ transform: translateY(-10px) scale(1.04); }}
    }}
    @keyframes fill {{
      0% {{ width: 40%; }}
      100% {{ width: 86%; }}
    }}
  </style>
</head>
<body>
  <div class="frame">
    <div class="glow"></div>
    <div class="hero">
      <p class="eyebrow">Topic-driven HTML animation</p>
      <h1>{html.escape(title)}</h1>
      <div class="narration">{n_lines}</div>
    </div>
    <div class="content">
      <section class="panel">
        <h2>Visual beats</h2>
        <ul>{bullet_html}</ul>
      </section>
      <section class="panel motion">
        <h2>Motion cues</h2>
        <div class="orb-row">
          <div class="orb"></div>
          <div class="orb"></div>
          <div class="orb"></div>
        </div>
        <div class="bar"><span></span></div>
        <div class="caption">
          Browser-rendered scene. The HTML/CSS stack lets the script choose a web-style output when the research calls for it.
        </div>
      </section>
    </div>
    <div class="footer">
      <span>renderer: html_anim</span>
      <span>{html.escape(style[:120] or "topic-driven visual system")}</span>
    </div>
  </div>
</body>
</html>"""


def _capture_html_frame(html_path: Path, png_path: Path, width: int, height: int) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        raise HTMLAnimRenderError(
            "The 'html_anim' renderer requires Playwright. Install it with: pip install playwright && playwright install chromium"
        ) from e

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
            page.goto(html_path.as_uri(), wait_until="load")
            page.wait_for_timeout(1200)
            page.screenshot(path=str(png_path))
            browser.close()
    except Exception as e:
        raise HTMLAnimRenderError(f"Failed to render HTML scene: {e}") from e


def _encode_frame_video(frame_path: Path, out_path: Path, duration_sec: int, fps: int) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-loop",
        "1",
        "-i",
        str(frame_path),
        "-t",
        str(duration_sec),
        "-r",
        str(fps),
        "-vf",
        "scale=trunc(iw/2)*2:trunc(ih/2)*2",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(out_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError as e:
        raise HTMLAnimRenderError("FFmpeg not found. Install it with: brew install ffmpeg") from e

    if result.returncode != 0:
        raise HTMLAnimRenderError((result.stderr or result.stdout or "FFmpeg failed")[-2000:])

    if not out_path.exists():
        raise HTMLAnimRenderError("FFmpeg reported success but the output file was not created")
    return out_path


def _description_bullets(description: str) -> list[str]:
    if not description.strip():
        return []
    parts = [item.strip() for item in re.split(r"(?<=[.!?])\s+", description) if item.strip()]
    if len(parts) <= 1:
        parts = [item.strip() for item in re.split(r",\s*", description) if item.strip()]
    return [item[:140].rstrip() + ("..." if len(item) > 140 else "") for item in parts[:5]]


def _theme_from_style(style: str) -> tuple[str, str, str, str]:
    colors = re.findall(r"#[0-9a-fA-F]{6}", style or "")
    bg = colors[0] if colors else "#0d1117"
    primary = colors[1] if len(colors) > 1 else "#FFD700"
    text = "#FFFFFF"
    muted = "#8B949E"
    return bg, primary, text, muted
