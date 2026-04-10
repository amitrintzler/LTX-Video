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
    secondary_color = "#17c0b5"
    panel_color = _blend_hex(bg_color, "#ffffff", 0.05)
    panel_edge = _blend_hex(bg_color, "#ffffff", 0.12)
    glow_color = _blend_hex(primary_color, "#ffffff", 0.18)

    image = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(image)

    _draw_background(draw, width, height, bg_color, accent_color)

    margin_x = int(width * 0.07)
    top_y = int(height * 0.09)
    title_font = _load_font(int(height * 0.072), bold=True)
    subtitle_font = _load_font(int(height * 0.026))
    body_font = _load_font(int(height * 0.039))
    rail_font = _load_font(int(height * 0.023))
    small_font = _load_font(int(height * 0.018))

    _draw_wrapped_text(
        draw,
        title,
        (margin_x, top_y),
        title_font,
        text_color,
        int(width * 0.62),
        line_spacing=8,
    )
    if narration:
        _draw_wrapped_text(
            draw,
            narration,
            (margin_x + 4, top_y + int(height * 0.095)),
            subtitle_font,
            muted_color,
            int(width * 0.58),
            line_spacing=8,
        )

    hero_box = [
        margin_x,
        int(height * 0.28),
        int(width * 0.66),
        int(height * 0.83),
    ]
    rail_box = [
        int(width * 0.71),
        int(height * 0.20),
        width - margin_x,
        int(height * 0.83),
    ]

    draw.rounded_rectangle(hero_box, radius=36, fill=panel_color, outline=panel_edge, width=3)
    draw.rectangle(
        [hero_box[0], hero_box[1], hero_box[0] + 16, hero_box[3]],
        fill=accent_color,
    )
    visual_kind = _scene_visual_kind(title, description, narration)
    draw.text(
        (hero_box[0] + 44, hero_box[1] + 24),
        _visual_label(visual_kind),
        font=small_font,
        fill=muted_color,
    )
    _draw_hero_visual(
        draw,
        hero_box,
        visual_kind,
        title=title,
        description=description,
        narration=narration,
        colors={
            "bg": bg_color,
            "panel": panel_color,
            "edge": panel_edge,
            "accent": accent_color,
            "secondary": secondary_color,
            "glow": glow_color,
            "text": text_color,
            "muted": muted_color,
        },
        fonts={
            "body": body_font,
            "rail": rail_font,
            "small": small_font,
        },
    )

    bullets = _content_bullets(title, narration, description, visual_kind)
    rail_title_y = rail_box[1]
    draw.text((rail_box[0], rail_title_y), "Key ideas", font=subtitle_font, fill=accent_color)
    chip_top = rail_title_y + 52
    chip_gap = 18
    chip_h = 96
    for bullet in bullets[:4]:
        chip_box = [rail_box[0], chip_top, rail_box[2], chip_top + chip_h]
        draw.rounded_rectangle(chip_box, radius=28, fill=panel_color, outline=panel_edge, width=2)
        draw.ellipse(
            [chip_box[0] + 20, chip_box[1] + 22, chip_box[0] + 40, chip_box[1] + 42],
            fill=glow_color,
        )
        _draw_wrapped_text(
            draw,
            bullet,
            (chip_box[0] + 56, chip_box[1] + 18),
            rail_font,
            text_color,
            chip_box[2] - chip_box[0] - 76,
            line_spacing=8,
        )
        chip_top += chip_h + chip_gap

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
    draw.ellipse(
        [int(width * 0.52), int(height * 0.08), int(width * 1.02), int(height * 0.72)],
        outline=_blend_hex(bg_color, accent_color, 0.18),
        width=3,
    )
    draw.ellipse(
        [int(width * -0.12), int(height * 0.46), int(width * 0.34), int(height * 1.02)],
        outline=_blend_hex(bg_color, "#00C896", 0.16),
        width=2,
    )


def _scene_visual_kind(title: str, description: str, narration: str) -> str:
    text = " ".join([title, description, narration]).lower()
    if any(token in text for token in ("call", "put", "payoff", "premium", "breakeven")):
        return "payoff"
    if any(token in text for token in ("volume", "open interest", "oi", "contract count")):
        return "bars"
    if any(token in text for token in ("strike ladder", "strike map", "strike wall")):
        return "ladder"
    if any(token in text for token in ("buyer", "seller", "bid", "ask", "sweep")):
        return "pressure"
    if any(token in text for token in ("delta", "gamma", "curve", "convexity")):
        return "curve"
    if any(token in text for token in ("theta", "expiration", "expiry", "time decay", "days to")):
        return "time"
    if any(token in text for token in ("checklist", "trap", "terms", "definition", "steps")):
        return "list"
    if any(token in text for token in ("flow", "signal", "unusual")):
        return "flow"
    return "concept"


def _visual_label(kind: str) -> str:
    labels = {
        "flow": "Signal map",
        "payoff": "Payoff map",
        "ladder": "Strike ladder",
        "time": "Time decay",
        "bars": "Volume vs open interest",
        "pressure": "Buyer and seller pressure",
        "curve": "Sensitivity curve",
        "list": "Key checkpoints",
        "concept": "Core concept",
    }
    return labels.get(kind, "Core concept")


def _scene_mechanics(kind: str, title: str, description: str) -> list[str]:
    label = title.strip() or "Scene"
    label = re.sub(r"\s+", " ", label)
    if len(label) > 32:
        label = label[:29].rstrip() + "..."

    defaults = {
        "flow": [
            "Track the premium spike.",
            "Mark where the flow accelerates.",
            "Confirm with a second signal.",
        ],
        "payoff": [
            "Mark strike and break-even.",
            "Show risk before the move.",
            "Keep premium visible on entry.",
        ],
        "ladder": [
            "Stack strikes from low to high.",
            "Highlight the selected contract.",
            "Compare nearby premium zones.",
        ],
        "time": [
            "Move from today to expiry.",
            "Fade value as time passes.",
            "Keep the decay path visible.",
        ],
        "bars": [
            "Compare fresh volume to open interest.",
            "Spot whether size is new or crowded.",
            "Flag the dominant side fast.",
        ],
        "pressure": [
            "Separate buyer force from seller force.",
            "Show where price gets pushed.",
            "Keep the tug-of-war readable.",
        ],
        "curve": [
            "Trace how sensitivity changes.",
            "Pin the move at one strike.",
            "Show why convexity matters.",
        ],
        "list": [
            "Reduce the scene to three checks.",
            "Keep labels short and scannable.",
            f"Anchor everything to {label}.",
        ],
        "concept": [
            f"Frame the core idea in {label}.",
            "Connect one cause to one effect.",
            "Support it with a single visual cue.",
        ],
    }

    bullets = defaults.get(kind, defaults["concept"]).copy()
    if description.strip():
        tags = _description_bullets(description)
        if tags:
            tag = re.sub(r"[.;:]+$", "", tags[0])
            tag = re.sub(r"\s+", " ", tag)
            if len(tag) > 44:
                tag = tag[:41].rstrip() + "..."
            bullets[0] = tag
    return bullets


def _content_bullets(title: str, narration: str, description: str, kind: str) -> list[str]:
    sentence_source = narration.strip() or ""
    sentences = [item.strip() for item in re.split(r"(?<=[.!?])\s+", sentence_source) if item.strip()]
    bullets: list[str] = []
    for sentence in sentences:
        cleaned = _compress_bullet(sentence)
        if cleaned and cleaned not in bullets:
            bullets.append(cleaned)
        if len(bullets) == 3:
            break

    if bullets:
        return bullets

    bullets = []
    title_line = title.strip()
    if title_line:
        bullets.append(_compress_bullet(title_line))

    bullets.extend(_scene_mechanics(kind, title, description)[:2])
    deduped: list[str] = []
    for bullet in bullets:
        if bullet and bullet not in deduped:
            deduped.append(bullet)
    return deduped[:3]


def _compress_bullet(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip(" -")
    cleaned = re.sub(r"^(now|next|then)\s+", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.rstrip(".")
    if len(cleaned) > 78:
        parts = re.split(r",|;| so | because | while ", cleaned, maxsplit=1)
        cleaned = parts[0].strip()
    if len(cleaned) > 58:
        cleaned = cleaned[:55].rstrip() + "..."
    return cleaned


def _draw_hero_visual(
    draw: ImageDraw.ImageDraw,
    box: list[int],
    kind: str,
    *,
    title: str,
    description: str,
    narration: str,
    colors: dict[str, str],
    fonts: dict[str, object],
) -> None:
    visual_box = [box[0] + 44, box[1] + 68, box[2] - 40, box[3] - 44]
    handlers = {
        "flow": _draw_flow_visual,
        "payoff": _draw_payoff_visual,
        "ladder": _draw_ladder_visual,
        "time": _draw_time_visual,
        "bars": _draw_bars_visual,
        "pressure": _draw_pressure_visual,
        "curve": _draw_curve_visual,
        "list": _draw_list_visual,
        "concept": _draw_concept_visual,
    }
    handler = handlers.get(kind, _draw_concept_visual)
    handler(draw, visual_box, title=title, description=description, narration=narration, colors=colors, fonts=fonts)


def _draw_flow_visual(
    draw: ImageDraw.ImageDraw,
    box: list[int],
    *,
    title: str,
    description: str,
    narration: str,
    colors: dict[str, str],
    fonts: dict[str, object],
) -> None:
    x0, y0, x1, y1 = box
    width = x1 - x0
    height = y1 - y0
    base_y = y0 + int(height * 0.58)
    points = [
        (x0 + int(width * 0.05), y0 + int(height * 0.45)),
        (x0 + int(width * 0.18), y0 + int(height * 0.78)),
        (x0 + int(width * 0.34), y0 + int(height * 0.60)),
        (x0 + int(width * 0.50), y0 + int(height * 0.22)),
        (x0 + int(width * 0.67), y0 + int(height * 0.48)),
        (x0 + int(width * 0.83), y0 + int(height * 0.28)),
        (x0 + int(width * 0.95), y0 + int(height * 0.66)),
    ]
    shadow = [(px + 8, py + 6) for px, py in points]
    draw.line([(x0, base_y), (x1, base_y)], fill=colors["edge"], width=2)
    draw.line(shadow, fill=colors["secondary"], width=7, joint="curve")
    draw.line(points, fill=colors["accent"], width=9, joint="curve")
    for idx, (px, py) in enumerate(points[::2], start=1):
        draw.ellipse([px - 12, py - 12, px + 12, py + 12], fill=colors["bg"], outline=colors["text"], width=3)
        draw.text((px + 10, py - 20), f"P{idx}", font=fonts["small"], fill=colors["muted"])
    _draw_badge(draw, [x0, y0, x0 + 180, y0 + 44], "PREMIUM SPIKE", colors["accent"], fonts["small"], colors["bg"])
    _draw_badge(draw, [x1 - 210, y0 + 14, x1, y0 + 58], "FOLLOW-THROUGH", colors["secondary"], fonts["small"], colors["bg"])
    draw.text((x0, y1 - 30), "Trend axis", font=fonts["small"], fill=colors["muted"])
    draw.text((x1 - 168, y1 - 30), "Research-backed motion", font=fonts["small"], fill=colors["muted"])


def _draw_payoff_visual(
    draw: ImageDraw.ImageDraw,
    box: list[int],
    *,
    title: str,
    description: str,
    narration: str,
    colors: dict[str, str],
    fonts: dict[str, object],
) -> None:
    x0, y0, x1, y1 = box
    width = x1 - x0
    height = y1 - y0
    axis_x = x0 + int(width * 0.14)
    axis_y = y1 - int(height * 0.18)
    strike_x = x0 + int(width * 0.48)
    is_put = "put" in f"{title} {description} {narration}".lower()

    draw.line([(axis_x, y0 + 10), (axis_x, axis_y)], fill=colors["edge"], width=3)
    draw.line([(axis_x, axis_y), (x1 - 16, axis_y)], fill=colors["edge"], width=3)
    draw.text((axis_x - 20, y0), "P/L", font=fonts["small"], fill=colors["muted"])
    draw.text((x1 - 76, axis_y + 8), "Price", font=fonts["small"], fill=colors["muted"])
    draw.line([(strike_x, y0 + 26), (strike_x, axis_y)], fill=colors["secondary"], width=3)
    draw.text((strike_x - 22, y0 + 4), "K", font=fonts["small"], fill=colors["secondary"])

    if is_put:
        path = [
            (x0 + int(width * 0.16), y0 + int(height * 0.18)),
            (strike_x, axis_y - 10),
            (x1 - int(width * 0.10), axis_y - 10),
        ]
        break_even_x = strike_x - int(width * 0.12)
    else:
        path = [
            (x0 + int(width * 0.16), axis_y - 10),
            (strike_x, axis_y - 10),
            (x1 - int(width * 0.08), y0 + int(height * 0.16)),
        ]
        break_even_x = strike_x + int(width * 0.12)

    draw.line(path, fill=colors["accent"], width=9, joint="curve")
    draw.line([(break_even_x, axis_y - 16), (break_even_x, axis_y + 12)], fill=colors["text"], width=2)
    draw.text((break_even_x - 34, axis_y + 18), "BE", font=fonts["small"], fill=colors["muted"])
    _draw_badge(draw, [x0, y0, x0 + 142, y0 + 44], "PREMIUM", colors["accent"], fonts["small"], colors["bg"])
    _draw_badge(draw, [x0 + 156, y0, x0 + 326, y0 + 44], "STRIKE", colors["secondary"], fonts["small"], colors["bg"])
    _draw_badge(draw, [x0 + 340, y0, x0 + 528, y0 + 44], "BREAK-EVEN", colors["panel"], fonts["small"], colors["text"], outline=colors["edge"])


def _draw_ladder_visual(
    draw: ImageDraw.ImageDraw,
    box: list[int],
    *,
    title: str,
    description: str,
    narration: str,
    colors: dict[str, str],
    fonts: dict[str, object],
) -> None:
    x0, y0, x1, y1 = box
    width = x1 - x0
    ladder_x = x0 + int(width * 0.22)
    bar_left = x0 + int(width * 0.42)
    row_h = max(42, (y1 - y0 - 24) // 6)
    strikes = ["395", "400", "405", "410", "415", "420"]
    selected = 2

    draw.line([(ladder_x, y0 + 16), (ladder_x, y1 - 16)], fill=colors["edge"], width=4)
    for idx, strike in enumerate(strikes):
        row_y = y0 + 18 + idx * row_h
        color = colors["accent"] if idx == selected else colors["edge"]
        draw.line([(ladder_x - 20, row_y), (ladder_x + 20, row_y)], fill=color, width=4)
        draw.text((ladder_x - 74, row_y - 14), strike, font=fonts["small"], fill=colors["text"])
        bar_w = int((idx + 2) / (len(strikes) + 2) * (x1 - bar_left - 10))
        fill = colors["secondary"] if idx == selected else _blend_hex(colors["secondary"], colors["bg"], 0.45)
        draw.rounded_rectangle([bar_left, row_y - 14, bar_left + bar_w, row_y + 14], radius=12, fill=fill)
    _draw_badge(draw, [bar_left, y0, bar_left + 170, y0 + 44], "SELECTED STRIKE", colors["accent"], fonts["small"], colors["bg"])
    _draw_badge(draw, [bar_left, y1 - 52, bar_left + 146, y1 - 8], "PREMIUM ZONE", colors["secondary"], fonts["small"], colors["bg"])


def _draw_time_visual(
    draw: ImageDraw.ImageDraw,
    box: list[int],
    *,
    title: str,
    description: str,
    narration: str,
    colors: dict[str, str],
    fonts: dict[str, object],
) -> None:
    x0, y0, x1, y1 = box
    width = x1 - x0
    timeline_y = y0 + int((y1 - y0) * 0.63)
    points = [
        (x0 + int(width * 0.12), "T-30"),
        (x0 + int(width * 0.38), "T-10"),
        (x0 + int(width * 0.62), "T-3"),
        (x0 + int(width * 0.84), "EXP"),
    ]
    draw.line([(points[0][0], timeline_y), (points[-1][0], timeline_y)], fill=colors["edge"], width=4)
    bar_tops = [y0 + 48, y0 + 84, y0 + 128, y0 + 184]
    for idx, (px, label) in enumerate(points):
        draw.ellipse([px - 12, timeline_y - 12, px + 12, timeline_y + 12], fill=colors["accent"] if idx == 0 else colors["secondary"])
        draw.text((px - 18, timeline_y + 20), label, font=fonts["small"], fill=colors["text"])
        alpha_fill = _blend_hex(colors["accent"], colors["bg"], idx * 0.22)
        draw.rounded_rectangle([px - 34, bar_tops[idx], px + 34, timeline_y - 34], radius=16, fill=alpha_fill)
    clock_box = [x1 - 140, y0 + 10, x1 - 16, y0 + 134]
    draw.ellipse(clock_box, outline=colors["secondary"], width=4)
    center_x = (clock_box[0] + clock_box[2]) // 2
    center_y = (clock_box[1] + clock_box[3]) // 2
    draw.line([(center_x, center_y), (center_x, center_y - 26)], fill=colors["text"], width=4)
    draw.line([(center_x, center_y), (center_x + 22, center_y + 12)], fill=colors["text"], width=4)


def _draw_bars_visual(
    draw: ImageDraw.ImageDraw,
    box: list[int],
    *,
    title: str,
    description: str,
    narration: str,
    colors: dict[str, str],
    fonts: dict[str, object],
) -> None:
    x0, y0, x1, y1 = box
    width = x1 - x0
    height = y1 - y0
    base_y = y1 - 36
    groups = [
        ("VOL", colors["accent"], [0.55, 0.85, 0.65]),
        ("OI", colors["secondary"], [0.42, 0.48, 0.45]),
    ]
    start_x = x0 + int(width * 0.16)
    gap = int(width * 0.24)
    bar_w = 44
    for group_idx, (label, fill, bars) in enumerate(groups):
        left = start_x + group_idx * gap
        draw.text((left - 10, y0 + 10), label, font=fonts["rail"], fill=colors["text"])
        for idx, factor in enumerate(bars):
            bx0 = left + idx * 60
            bx1 = bx0 + bar_w
            by0 = base_y - int(height * factor)
            draw.rounded_rectangle([bx0, by0, bx1, base_y], radius=14, fill=fill)
    _draw_badge(draw, [x1 - 220, y0, x1 - 86, y0 + 44], "NEW SIZE", colors["accent"], fonts["small"], colors["bg"])


def _draw_pressure_visual(
    draw: ImageDraw.ImageDraw,
    box: list[int],
    *,
    title: str,
    description: str,
    narration: str,
    colors: dict[str, str],
    fonts: dict[str, object],
) -> None:
    x0, y0, x1, y1 = box
    mid_x = (x0 + x1) // 2
    mid_y = (y0 + y1) // 2
    draw.rounded_rectangle([mid_x - 70, mid_y - 44, mid_x + 70, mid_y + 44], radius=24, fill=colors["panel"], outline=colors["edge"], width=2)
    draw.text((mid_x - 24, mid_y - 12), "PRICE", font=fonts["small"], fill=colors["text"])
    draw.polygon([(x0 + 30, mid_y), (mid_x - 90, mid_y - 42), (mid_x - 90, mid_y - 18), (mid_x - 12, mid_y - 18), (mid_x - 12, mid_y + 18), (mid_x - 90, mid_y + 18), (mid_x - 90, mid_y + 42)], fill=colors["accent"])
    draw.polygon([(x1 - 30, mid_y), (mid_x + 90, mid_y - 42), (mid_x + 90, mid_y - 18), (mid_x + 12, mid_y - 18), (mid_x + 12, mid_y + 18), (mid_x + 90, mid_y + 18), (mid_x + 90, mid_y + 42)], fill=colors["secondary"])
    draw.text((x0 + 18, y0 + 16), "BUYER PRESSURE", font=fonts["small"], fill=colors["accent"])
    draw.text((x1 - 120, y0 + 16), "SELLER PRESSURE", font=fonts["small"], fill=colors["secondary"])


def _draw_curve_visual(
    draw: ImageDraw.ImageDraw,
    box: list[int],
    *,
    title: str,
    description: str,
    narration: str,
    colors: dict[str, str],
    fonts: dict[str, object],
) -> None:
    x0, y0, x1, y1 = box
    width = x1 - x0
    height = y1 - y0
    axis_x = x0 + int(width * 0.14)
    axis_y = y1 - int(height * 0.16)
    draw.line([(axis_x, y0 + 20), (axis_x, axis_y)], fill=colors["edge"], width=3)
    draw.line([(axis_x, axis_y), (x1 - 20, axis_y)], fill=colors["edge"], width=3)
    points = [
        (axis_x + int(width * 0.08), axis_y - int(height * 0.10)),
        (axis_x + int(width * 0.22), axis_y - int(height * 0.14)),
        (axis_x + int(width * 0.40), axis_y - int(height * 0.24)),
        (axis_x + int(width * 0.58), axis_y - int(height * 0.44)),
        (axis_x + int(width * 0.72), axis_y - int(height * 0.70)),
    ]
    draw.line(points, fill=colors["secondary"], width=9, joint="curve")
    focus = points[3]
    draw.ellipse([focus[0] - 14, focus[1] - 14, focus[0] + 14, focus[1] + 14], fill=colors["accent"], outline=colors["text"], width=3)
    _draw_badge(draw, [focus[0] + 20, focus[1] - 18, focus[0] + 138, focus[1] + 20], "GAMMA PICKUP", colors["accent"], fonts["small"], colors["bg"])


def _draw_list_visual(
    draw: ImageDraw.ImageDraw,
    box: list[int],
    *,
    title: str,
    description: str,
    narration: str,
    colors: dict[str, str],
    fonts: dict[str, object],
) -> None:
    x0, y0, x1, y1 = box
    rows = [
        "Premium is unusually large.",
        "Volume confirms fresh participation.",
        "Strike and expiry match the thesis.",
    ]
    row_h = max(72, (y1 - y0 - 40) // 3)
    for idx, row in enumerate(rows):
        top = y0 + 12 + idx * row_h
        panel = [x0 + 16, top, x1 - 16, top + row_h - 16]
        draw.rounded_rectangle(panel, radius=26, fill=colors["panel"], outline=colors["edge"], width=2)
        draw.ellipse([panel[0] + 20, panel[1] + 18, panel[0] + 48, panel[1] + 46], fill=colors["accent"])
        _draw_wrapped_text(draw, row, (panel[0] + 70, panel[1] + 14), fonts["rail"], colors["text"], panel[2] - panel[0] - 96, line_spacing=6)


def _draw_concept_visual(
    draw: ImageDraw.ImageDraw,
    box: list[int],
    *,
    title: str,
    description: str,
    narration: str,
    colors: dict[str, str],
    fonts: dict[str, object],
) -> None:
    x0, y0, x1, y1 = box
    mid_x = (x0 + x1) // 2
    mid_y = (y0 + y1) // 2
    core_box = [mid_x - 120, mid_y - 64, mid_x + 120, mid_y + 64]
    draw.rounded_rectangle(core_box, radius=28, fill=colors["panel"], outline=colors["accent"], width=3)
    core_title = title.strip() or "Core idea"
    _draw_wrapped_text(draw, core_title, (core_box[0] + 24, core_box[1] + 22), fonts["rail"], colors["text"], core_box[2] - core_box[0] - 48, line_spacing=6)
    satellites = [
        ([x0 + 24, y0 + 38, x0 + 220, y0 + 94], "Setup"),
        ([x1 - 220, y0 + 38, x1 - 24, y0 + 94], "Signal"),
        ([mid_x - 98, y1 - 94, mid_x + 98, y1 - 38], "Takeaway"),
    ]
    for sat_box, label in satellites:
        draw.rounded_rectangle(sat_box, radius=22, fill=colors["panel"], outline=colors["edge"], width=2)
        draw.text((sat_box[0] + 22, sat_box[1] + 16), label, font=fonts["small"], fill=colors["text"])
    draw.line([(x0 + 220, y0 + 94), (core_box[0], core_box[1] + 30)], fill=colors["secondary"], width=3)
    draw.line([(x1 - 220, y0 + 94), (core_box[2], core_box[1] + 30)], fill=colors["secondary"], width=3)
    draw.line([(mid_x, y1 - 94), (mid_x, core_box[3])], fill=colors["secondary"], width=3)


def _draw_badge(
    draw: ImageDraw.ImageDraw,
    box: list[int],
    text: str,
    fill: str,
    font,
    text_color: str,
    *,
    outline: str | None = None,
) -> None:
    draw.rounded_rectangle(box, radius=18, fill=fill, outline=outline)
    text_box = draw.textbbox((0, 0), text, font=font)
    text_w = text_box[2] - text_box[0]
    text_h = text_box[3] - text_box[1]
    x = box[0] + max(10, ((box[2] - box[0]) - text_w) // 2)
    y = box[1] + max(6, ((box[3] - box[1]) - text_h) // 2 - 1)
    draw.text((x, y), text, font=font, fill=text_color)


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
    bg = "#0d1117"
    primary = "#FFD700"
    if colors:
        for candidate in colors[:3]:
            if candidate.lower() not in {"#0d1117", "#0b1021", "#111827", "#1f2937"}:
                primary = candidate
                break
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
