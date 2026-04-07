"""
stages/renderers/slides.py — Renderer: static educational slides

Builds a polished slide-style frame with Pillow and encodes it to MP4 with FFmpeg.
This is a lightweight non-Manim renderer for text-forward, summary-heavy scenes.
"""

from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from config import PipelineConfig


class SlidesRenderError(RuntimeError):
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

    with tempfile.TemporaryDirectory(prefix="slides_render_") as tmp_dir:
        tmp_dir = Path(tmp_dir)
        image_path = tmp_dir / "slide.png"
        _render_slide_image(
            title=title,
            narration=narration,
            description=description,
            style=style,
            width=width,
            height=height,
            out_path=image_path,
        )
        return _encode_slide_video(image_path, out_path, duration_sec, fps)


def _render_slide_image(
    *,
    title: str,
    narration: str,
    description: str,
    style: str,
    width: int,
    height: int,
    out_path: Path,
) -> None:
    bg_color, primary_color, text_color, muted_color = _theme_from_style(style)
    accent_color = primary_color
    card_color = _blend_hex(bg_color, "#ffffff", 0.06)
    card_edge = _blend_hex(bg_color, "#ffffff", 0.14)

    image = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(image)

    _draw_background(draw, width, height, bg_color, accent_color)

    margin_x = int(width * 0.07)
    top_y = int(height * 0.08)
    title_font = _load_font(int(height * 0.065), bold=True)
    subtitle_font = _load_font(int(height * 0.027))
    section_font = _load_font(int(height * 0.03), bold=True)
    body_font = _load_font(int(height * 0.025))
    small_font = _load_font(int(height * 0.018))

    draw.rounded_rectangle(
        [margin_x, top_y, width - margin_x, int(height * 0.27)],
        radius=28,
        fill=card_color,
        outline=card_edge,
        width=3,
    )
    draw.rectangle([margin_x, top_y, margin_x + 14, int(height * 0.27)], fill=accent_color)

    _draw_wrapped_text(
        draw,
        title,
        (margin_x + 38, top_y + 28),
        title_font,
        text_color,
        width - margin_x * 2 - 80,
        line_spacing=10,
    )

    if narration:
        _draw_wrapped_text(
            draw,
            narration,
            (margin_x + 40, top_y + int(height * 0.105)),
            subtitle_font,
            muted_color,
            width - margin_x * 2 - 90,
            line_spacing=8,
        )

    left_x = margin_x
    left_top = int(height * 0.33)
    card_width = int((width - margin_x * 2 - 24) / 2)
    card_height = int(height * 0.46)
    gap = 24

    left_box = [left_x, left_top, left_x + card_width, left_top + card_height]
    right_box = [left_x + card_width + gap, left_top, width - margin_x, left_top + card_height]

    draw.rounded_rectangle(left_box, radius=26, fill=card_color, outline=card_edge, width=3)
    draw.rounded_rectangle(right_box, radius=26, fill=card_color, outline=card_edge, width=3)

    _draw_section(
        draw,
        box=left_box,
        heading="Narration",
        body=narration or "Narration omitted.",
        heading_font=section_font,
        body_font=body_font,
        heading_color=primary_color,
        body_color=text_color,
    )

    bullets = _description_bullets(description)
    body_text = "\n".join(f"• {item}" for item in bullets) if bullets else "• Visual direction not specified."
    _draw_section(
        draw,
        box=right_box,
        heading="Visual beats",
        body=body_text,
        heading_font=section_font,
        body_font=body_font,
        heading_color=primary_color,
        body_color=text_color,
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_path)


def _encode_slide_video(image_path: Path, out_path: Path, duration_sec: int, fps: int) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-loop",
        "1",
        "-i",
        str(image_path),
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
        raise SlidesRenderError("FFmpeg not found. Install it with: brew install ffmpeg") from e

    if result.returncode != 0:
        raise SlidesRenderError((result.stderr or result.stdout or "FFmpeg failed")[-2000:])

    if not out_path.exists():
        raise SlidesRenderError("FFmpeg reported success but the output file was not created")
    return out_path


def _draw_background(draw: ImageDraw.ImageDraw, width: int, height: int, bg_color: str, accent_color: str) -> None:
    # Subtle layered background so slides do not look flat.
    draw.rectangle((0, 0, width, height), fill=bg_color)
    band_h = max(16, height // 60)
    draw.rectangle((0, 0, width, band_h), fill=accent_color)
    draw.rectangle((0, height - band_h, width, height), fill=_blend_hex(bg_color, accent_color, 0.28))


def _draw_section(
    draw: ImageDraw.ImageDraw,
    *,
    box: list[int],
    heading: str,
    body: str,
    heading_font,
    body_font,
    heading_color: str,
    body_color: str,
) -> None:
    x0, y0, x1, y1 = box
    padding = 28
    draw.text((x0 + padding, y0 + padding), heading, font=heading_font, fill=heading_color)
    body_top = y0 + padding + int(heading_font.size * 1.4 if hasattr(heading_font, "size") else 48)
    wrapped = _wrap_text(draw, body, body_font, x1 - x0 - padding * 2)
    draw.multiline_text(
        (x0 + padding, body_top),
        wrapped,
        font=body_font,
        fill=body_color,
        spacing=10,
    )


def _description_bullets(description: str) -> list[str]:
    if not description.strip():
        return []
    chunks = [item.strip() for item in re.split(r"(?<=[.!?])\s+", description) if item.strip()]
    if len(chunks) <= 1:
        chunks = [item.strip() for item in re.split(r",\s*", description) if item.strip()]
    bullets = []
    for item in chunks:
        cleaned = item.strip()
        if len(cleaned) > 120:
            cleaned = cleaned[:117].rstrip() + "..."
        bullets.append(cleaned)
    return bullets[:5]


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> str:
    if not text:
        return ""

    paragraphs = text.splitlines() or [text]
    wrapped_paragraphs = []
    for paragraph in paragraphs:
        if not paragraph.strip():
            wrapped_paragraphs.append("")
            continue
        words = paragraph.split()
        if not words:
            wrapped_paragraphs.append("")
            continue
        lines = []
        current = words[0]
        for word in words[1:]:
            candidate = current + " " + word
            if _text_width(draw, candidate, font) <= max_width:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
        wrapped_paragraphs.append("\n".join(lines))
    return "\n".join(wrapped_paragraphs)


def _draw_wrapped_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    pos: tuple[int, int],
    font,
    fill: str,
    max_width: int,
    line_spacing: int = 8,
) -> None:
    wrapped = _wrap_text(draw, text, font, max_width)
    draw.multiline_text(pos, wrapped, font=font, fill=fill, spacing=line_spacing)


def _text_width(draw: ImageDraw.ImageDraw, text: str, font) -> int:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def _theme_from_style(style: str) -> tuple[str, str, str, str]:
    colors = re.findall(r"#[0-9a-fA-F]{6}", style or "")
    bg = colors[0] if colors else "#0d1117"
    primary = colors[1] if len(colors) > 1 else "#FFD700"
    text = "#FFFFFF"
    muted = "#8B949E"
    return bg, primary, text, muted


def _blend_hex(a: str, b: str, ratio: float) -> str:
    ratio = max(0.0, min(1.0, ratio))
    ar, ag, ab = _hex_to_rgb(a)
    br, bg, bb = _hex_to_rgb(b)
    r = int(ar * (1 - ratio) + br * ratio)
    g = int(ag * (1 - ratio) + bg * ratio)
    b_ = int(ab * (1 - ratio) + bb * ratio)
    return f"#{r:02x}{g:02x}{b_:02x}"


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    if len(value) != 6:
        return 0, 0, 0
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def _load_font(size: int, bold: bool = False):
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Helvetica.ttc",
        "/System/Library/Fonts/Menlo.ttc",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except Exception:
            continue
    return ImageFont.load_default()
