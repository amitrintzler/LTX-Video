"""
stages/renderers/d3.py — Renderer: chart-centric Python scene

Builds a data-viz style frame in Pillow and encodes it to MP4 with FFmpeg.
This renderer is for chart-heavy, metrics-heavy, or statistical topics.
"""

from __future__ import annotations

import math
import re
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from config import PipelineConfig


class D3RenderError(RuntimeError):
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

    with tempfile.TemporaryDirectory(prefix="d3_render_") as tmp_dir:
        tmp_dir = Path(tmp_dir)
        png_path = tmp_dir / "frame.png"

        _capture_html_frame(
            png_path,
            width=width,
            height=height,
            title=title,
            narration=narration,
            description=description,
            style=style,
        )
        return _encode_frame_video(png_path, out_path, duration_sec, fps)


def _capture_html_frame(
    png_path: Path,
    *,
    width: int,
    height: int,
    title: str,
    narration: str,
    description: str,
    style: str,
) -> None:
    frame = Image.new("RGBA", (width, height), _hex_to_rgba(_theme_from_style(style)[0], 255))
    draw = ImageDraw.Draw(frame, "RGBA")
    bg_color, primary_color, secondary_color, text_color, muted_color = _theme_from_style(style)

    _paint_background(frame, primary_color, secondary_color)

    pad_x = int(width * 0.055)
    pad_y = int(height * 0.055)
    header_h = int(height * 0.27)
    gap = int(width * 0.016)
    panel_y = pad_y + header_h + gap
    panel_h = height - panel_y - int(height * 0.09)
    left_w = int(width * 0.64)
    right_w = width - (pad_x * 2) - gap - left_w
    left_x = pad_x
    right_x = left_x + left_w + gap

    _draw_panel(draw, (pad_x, pad_y, width - pad_x, pad_y + header_h), fill=(255, 255, 255, 18), outline=(255, 255, 255, 32))
    _draw_panel(draw, (left_x, panel_y, left_x + left_w, panel_y + panel_h), fill=(255, 255, 255, 14), outline=(255, 255, 255, 30))
    _draw_panel(draw, (right_x, panel_y, right_x + right_w, panel_y + panel_h), fill=(255, 255, 255, 14), outline=(255, 255, 255, 30))

    eyebrow_font = _load_font(max(18, int(width * 0.012)), bold=True)
    title_font, title_lines = _fit_wrapped_text(
        draw,
        title,
        max_width=int(width * 0.47),
        max_lines=3,
        start_size=max(42, int(width * 0.032)),
        min_size=max(26, int(width * 0.022)),
        bold=True,
    )
    narration_font, narration_lines = _fit_wrapped_text(
        draw,
        narration or "This scene turns the research into a visual explanation.",
        max_width=int(width * 0.52),
        max_lines=4,
        start_size=max(24, int(width * 0.018)),
        min_size=max(16, int(width * 0.014)),
    )

    draw.text((pad_x + 28, pad_y + 20), "Chart-centric data story", fill=muted_color, font=eyebrow_font)
    _draw_multiline_text(draw, pad_x + 28, pad_y + 56, title_lines, title_font, fill=text_color, spacing=int(title_font.size * 0.14))
    title_block_height = _text_block_height(draw, title_lines, title_font, spacing=int(title_font.size * 0.14))
    narration_y = pad_y + 56 + title_block_height + 16
    _draw_multiline_text(draw, pad_x + 28, narration_y, narration_lines, narration_font, fill=muted_color, spacing=int(narration_font.size * 0.22))

    # Left panel: chart
    chart_x0 = left_x + 48
    chart_y0 = panel_y + 54
    chart_x1 = left_x + left_w - 44
    chart_y1 = panel_y + panel_h - 44
    _draw_chart(draw, (chart_x0, chart_y0, chart_x1, chart_y1), description, primary_color, secondary_color, muted_color, text_color)

    # Right panel: signal cards and bullets
    cards_top = panel_y + 38
    card_h = int((panel_h - 126) * 0.22)
    card_gap = int(height * 0.012)
    card_x = right_x + 24
    card_w = right_w - 48
    for idx, (label, value, fill_ratio, accent) in enumerate(_signal_cards(description, primary_color, secondary_color)):
        y = cards_top + idx * (card_h + card_gap)
        _draw_card(draw, (card_x, y, card_x + card_w, y + card_h), label, value, fill_ratio, accent, muted_color, text_color)

    bullets_top = cards_top + 3 * (card_h + card_gap) + 6
    bullets = _description_bullets(description)
    if not bullets:
        bullets = ["Chart-driven scene.", "The visual language stays data-first.", "Each signal is grounded in the research."]
    _draw_bullet_list(draw, card_x, bullets_top, card_w, panel_y + panel_h - 34, bullets, text_color, muted_color)

    footer_font = _load_font(max(14, int(width * 0.008)), bold=False)
    footer_y = height - int(height * 0.04)
    draw.text((pad_x, footer_y), "renderer: d3", fill=muted_color, font=footer_font)
    footer_text = style[:120] or "topic-driven chart system"
    footer_bbox = draw.textbbox((0, 0), footer_text, font=footer_font)
    draw.text((width - pad_x - (footer_bbox[2] - footer_bbox[0]), footer_y), footer_text, fill=muted_color, font=footer_font)

    png_path.parent.mkdir(parents=True, exist_ok=True)
    frame.convert("RGB").save(png_path, format="PNG")


def _draw_chart(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    description: str,
    primary_color: str,
    secondary_color: str,
    muted_color: str,
    text_color: str,
) -> None:
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=26, fill=(255, 255, 255, 10), outline=(255, 255, 255, 24), width=2)

    inner = (x0 + 20, y0 + 20, x1 - 20, y1 - 26)
    ix0, iy0, ix1, iy1 = inner

    for i in range(5):
        yy = iy0 + i * (iy1 - iy0) / 4
        draw.line((ix0, yy, ix1, yy), fill=(255, 255, 255, 16), width=1)
    for i in range(5):
        xx = ix0 + i * (ix1 - ix0) / 4
        draw.line((xx, iy0, xx, iy1), fill=(255, 255, 255, 12), width=1)

    points = _synthetic_points(description)
    mapped = _map_points(points, ix0 + 18, iy0 + 18, ix1 - ix0 - 36, iy1 - iy0 - 36)
    if len(mapped) >= 2:
        glow = [((255, 215, 0, 38), 16), ((255, 215, 0, 62), 10)]
        for color, width in glow:
            draw.line(mapped, fill=color, width=width)
        for idx in range(len(mapped) - 1):
            mix = idx / max(len(mapped) - 2, 1)
            color = _mix_hex(primary_color, secondary_color, mix)
            draw.line([mapped[idx], mapped[idx + 1]], fill=color, width=8)

    for idx, (sx, sy) in enumerate(mapped):
        draw.ellipse((sx - 12, sy - 12, sx + 12, sy + 12), fill=(0, 0, 0, 90))
        draw.ellipse((sx - 9, sy - 9, sx + 9, sy + 9), fill=_hex_to_rgba("#FFFFFF", 235), outline=_hex_to_rgba(primary_color, 200), width=2)
        label = f"P{idx + 1}"
        draw.text((sx + 14, sy - 20), label, fill=muted_color, font=_load_font(14, bold=True))

    axis_font = _load_font(16, bold=False)
    draw.text((ix0, iy1 + 8), "Trend axis", fill=muted_color, font=axis_font)
    draw.text((ix1 - 160, iy1 + 8), "Research-backed motion", fill=muted_color, font=axis_font)

    header_font = _load_font(20, bold=True)
    draw.text((x0 + 24, y0 + 16), "Trend view", fill=text_color, font=header_font)


def _draw_card(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    label: str,
    value: str,
    fill_ratio: float,
    accent: str,
    muted_color: str,
    text_color: str,
) -> None:
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=20, fill=(255, 255, 255, 12), outline=(255, 255, 255, 24), width=2)
    label_font = _load_font(14, bold=True)
    value_font = _load_font(34, bold=True)
    draw.text((x0 + 18, y0 + 14), label, fill=muted_color, font=label_font)
    draw.text((x0 + 18, y0 + 34), value, fill=text_color, font=value_font)

    bar_h = 13
    bar_y = y1 - 22 - bar_h
    draw.rounded_rectangle((x0 + 18, bar_y, x1 - 18, bar_y + bar_h), radius=999, fill=(255, 255, 255, 12), outline=(255, 255, 255, 18), width=1)
    fill_w = int((x1 - x0 - 36) * max(0.18, min(fill_ratio, 1.0)))
    draw.rounded_rectangle((x0 + 18, bar_y, x0 + 18 + fill_w, bar_y + bar_h), radius=999, fill=_hex_to_rgba(accent, 255))


def _draw_bullet_list(
    draw: ImageDraw.ImageDraw,
    x: int,
    top: int,
    width: int,
    bottom: int,
    bullets: list[str],
    text_color: str,
    muted_color: str,
) -> None:
    title_font = _load_font(18, bold=True)
    body_font = _load_font(17, bold=False)
    draw.text((x, top), "Key signals", fill=text_color, font=title_font)
    y = top + 34
    bullet_width = width - 12
    for bullet in bullets[:5]:
        lines = _wrap_text(draw, bullet, body_font, bullet_width - 22)
        draw.ellipse((x + 2, y + 8, x + 10, y + 16), fill=_hex_to_rgba(muted_color, 220))
        _draw_multiline_text(draw, x + 18, y, lines, body_font, fill=text_color, spacing=4)
        y += _text_block_height(draw, lines, body_font, spacing=4) + 14
        if y > bottom:
            break


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
        raise D3RenderError("FFmpeg not found. Install it with: brew install ffmpeg") from e

    if result.returncode != 0:
        raise D3RenderError((result.stderr or result.stdout or "FFmpeg failed")[-2000:])

    if not out_path.exists():
        raise D3RenderError("FFmpeg reported success but the output file was not created")
    return out_path


def _paint_background(frame: Image.Image, primary_color: str, secondary_color: str) -> None:
    width, height = frame.size
    overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay, "RGBA")

    overlay_draw.ellipse(
        (-int(width * 0.1), -int(height * 0.05), int(width * 0.42), int(height * 0.35)),
        fill=_hex_to_rgba(primary_color, 40),
    )
    overlay_draw.ellipse(
        (int(width * 0.68), int(height * 0.06), int(width * 1.05), int(height * 0.42)),
        fill=_hex_to_rgba(secondary_color, 36),
    )
    overlay_draw.ellipse(
        (int(width * 0.42), int(height * 0.72), int(width * 0.82), int(height * 1.02)),
        fill=_hex_to_rgba("#FFFFFF", 20),
    )
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=max(30, int(min(width, height) * 0.05))))
    frame.alpha_composite(overlay)

    grid = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    grid_draw = ImageDraw.Draw(grid, "RGBA")
    step_x = max(120, width // 14)
    step_y = max(120, height // 10)
    for x in range(0, width + step_x, step_x):
        grid_draw.line((x, 0, x, height), fill=(255, 255, 255, 5), width=1)
    for y in range(0, height + step_y, step_y):
        grid_draw.line((0, y, width, y), fill=(255, 255, 255, 5), width=1)
    frame.alpha_composite(grid)


def _draw_panel(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], *, fill: tuple[int, int, int, int], outline: tuple[int, int, int, int]) -> None:
    draw.rounded_rectangle(box, radius=28, fill=fill, outline=outline, width=2)


def _theme_from_style(style: str) -> tuple[str, str, str, str, str]:
    colors = re.findall(r"#[0-9a-fA-F]{6}", style or "")
    bg = colors[0] if colors else "#0d1117"
    primary = colors[1] if len(colors) > 1 else "#FFD700"
    secondary = colors[2] if len(colors) > 2 else "#00C896"
    text = colors[3] if len(colors) > 3 else "#FFFFFF"
    muted = "#8B949E"
    return bg, primary, secondary, text, muted


def _synthetic_points(description: str) -> list[tuple[float, float]]:
    seed = sum(ord(c) for c in description) or 1
    points = []
    for i in range(7):
        x = 1 + i
        y = 30 + ((seed * (i + 3)) % 50) + int(18 * math.sin((seed % 11 + 1) * (i + 1) / 3.0))
        points.append((x, max(12, min(90, y))))
    return points


def _map_points(points: list[tuple[float, float]], x0: int, y0: int, width: int, height: int) -> list[tuple[float, float]]:
    if not points:
        return []
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    span_x = max(max_x - min_x, 1)
    span_y = max(max_y - min_y, 1)
    mapped = []
    for x, y in points:
        sx = x0 + (x - min_x) / span_x * width
        sy = y0 + height - (y - min_y) / span_y * height
        mapped.append((sx, sy))
    return mapped


def _description_bullets(description: str) -> list[str]:
    if not description.strip():
        return []
    parts = [item.strip() for item in re.split(r"(?<=[.!?])\s+", description) if item.strip()]
    if len(parts) <= 1:
        parts = [item.strip() for item in re.split(r",\s*", description) if item.strip()]
    bullets = []
    for item in parts[:5]:
        bullets.append(item[:140].rstrip() + ("..." if len(item) > 140 else ""))
    return bullets


def _signal_cards(description: str, primary_color: str, secondary_color: str) -> list[tuple[str, str, float, str]]:
    seed = sum(ord(c) for c in description) or 1
    cards = []
    labels = ["Signal 1", "Signal 2", "Signal 3"]
    suffixes = ["%", "x", "pts"]
    for idx, label in enumerate(labels):
        value = (seed * (idx + 3)) % 100
        cards.append((label, f"{value:02d}{suffixes[idx]}", 0.42 + 0.18 * idx, primary_color if idx != 1 else secondary_color))
    return cards


def _metric_value(description: str, index: int) -> str:
    seed = sum(ord(c) for c in description) or 1
    value = (seed * (index + 3)) % 100
    suffix = ["%", "x", "pts"][index % 3]
    return f"{value:02d}{suffix}"


def _mix_hex(a: str, b: str, t: float) -> tuple[int, int, int, int]:
    ar, ag, ab = _hex_to_rgb(a)
    br, bg, bb = _hex_to_rgb(b)
    return (
        int(ar + (br - ar) * t),
        int(ag + (bg - ag) * t),
        int(ab + (bb - ab) * t),
        255,
    )


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def _hex_to_rgba(value: str, alpha: int) -> tuple[int, int, int, int]:
    r, g, b = _hex_to_rgb(value)
    return r, g, b, alpha


def _load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica Neue Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Helvetica Neue.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica.ttc",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Supplemental/DejaVu Sans Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/DejaVu Sans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except Exception:
            continue
    return ImageFont.load_default()


def _fit_wrapped_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    *,
    max_width: int,
    max_lines: int,
    start_size: int,
    min_size: int,
    bold: bool = False,
) -> tuple[ImageFont.ImageFont, list[str]]:
    for size in range(start_size, min_size - 1, -2):
        font = _load_font(size, bold=bold)
        lines = _wrap_text(draw, text, font, max_width)
        if len(lines) <= max_lines:
            return font, lines
    font = _load_font(min_size, bold=bold)
    return font, _wrap_text(draw, text, font, max_width)[:max_lines]


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if _text_width(draw, candidate, font) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _draw_multiline_text(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    lines: list[str],
    font: ImageFont.ImageFont,
    *,
    fill: str,
    spacing: int,
) -> None:
    cur_y = y
    for line in lines:
        draw.text((x, cur_y), line, fill=fill, font=font)
        cur_y += _line_height(draw, font) + spacing


def _text_block_height(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    font: ImageFont.ImageFont,
    *,
    spacing: int,
) -> int:
    if not lines:
        return 0
    return len(lines) * _line_height(draw, font) + max(0, len(lines) - 1) * spacing


def _text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> int:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def _line_height(draw: ImageDraw.ImageDraw, font: ImageFont.ImageFont) -> int:
    bbox = draw.textbbox((0, 0), "Ag", font=font)
    return bbox[3] - bbox[1]
