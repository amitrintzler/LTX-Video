#!/usr/bin/env python3
"""Designed native 9:16 (and 1:1) social cut: brand header (big logo + wordmark),
the 16:9 promo full-width in the center, branded footer with CTA — no blurred
letterbox. Usage: make_vertical.py <master_16x9.mp4> <out_dir> [square]
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, "cinematic-pipeline")
from stages import motiongfx as mg  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

FF = mg.cfg.ffmpeg_bin()
SRC = Path(sys.argv[1])
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else SRC.parent
SQUARE = len(sys.argv) > 3 and sys.argv[3] == "square"

VW = 1080
VIDEO_H = 608                       # 1080-wide 16:9 content height
CW, CH = (1080, 1080) if SQUARE else (1080, 1920)
vy = (CH - VIDEO_H) // 2            # content vertical position


def canvas_png(path: Path) -> Path:
    img = Image.new("RGB", (CW, CH))
    px = img.load()
    for y in range(CH):                                   # brand gradient
        f = y / CH
        px_row = tuple(int(mg.BG_TOP[i] + (mg.BG_BOT[i] - mg.BG_TOP[i]) * f) for i in range(3))
        for x in range(CW):
            px[x, y] = px_row
    d = ImageDraw.Draw(img, "RGBA")
    # window where the video will sit (subtle framed screen)
    d.rounded_rectangle([0, vy - 6, CW, vy + VIDEO_H + 6], radius=8, fill=(6, 7, 18))
    d.rectangle([0, vy - 3, CW, vy - 1], fill=mg.ACCENT)
    d.rectangle([0, vy + VIDEO_H + 1, CW, vy + VIDEO_H + 3], fill=mg.ACCENT)

    # ---- HEADER (above video) ----
    hy = vy // 2
    lg = 96 if not SQUARE else 64
    mg._draw_logo(d, (CW - lg) // 2, hy - lg - (60 if not SQUARE else 30), lg)
    fw = mg._font(64 if not SQUARE else 44)
    ft = mg._font(30 if not SQUARE else 24)
    bb = d.textbbox((0, 0), "OPTIONS EDUCATOR", font=fw)
    d.text(((CW - (bb[2] - bb[0])) // 2, hy + (10 if not SQUARE else 6)),
           "OPTIONS EDUCATOR", font=fw, fill=(255, 255, 255))
    sub = "stocks · options · volatility"
    bb = d.textbbox((0, 0), sub, font=ft)
    d.text(((CW - (bb[2] - bb[0])) // 2, hy + (86 if not SQUARE else 54)), sub,
           font=ft, fill=mg.MUTE)

    # ---- FOOTER (below video) ----
    fy = vy + VIDEO_H + (CH - (vy + VIDEO_H)) // 2
    cta = "Start Learning  →"
    fc = mg._font(48 if not SQUARE else 36)
    bb = d.textbbox((0, 0), cta, font=fc)
    cw2, ch2 = bb[2] - bb[0], bb[3] - bb[1]
    padx, pady = 46, 22
    x0 = (CW - cw2) // 2 - padx
    d.rounded_rectangle([x0, fy - pady, x0 + cw2 + 2 * padx, fy + ch2 + pady],
                        radius=40, fill=mg.ACCENT)
    d.text(((CW - cw2) // 2, fy - bb[1]), cta, font=fc, fill=(8, 20, 14))
    if not SQUARE:
        fu = mg._font(28)
        u = "optionseducator.com"
        bb = d.textbbox((0, 0), u, font=fu)
        d.text(((CW - (bb[2] - bb[0])) // 2, fy + ch2 + pady + 30), u, font=fu,
               fill=(200, 205, 235))
    img.save(path)
    return path


canvas = canvas_png(OUT / ("_canvas_sq.png" if SQUARE else "_canvas_vert.png"))
sfx = "square_native" if SQUARE else "vertical_native"
out = OUT / f"{SRC.stem}_{sfx}.mp4"
subprocess.run([
    FF, "-y", "-loglevel", "error", "-loop", "1", "-i", str(canvas), "-i", str(SRC),
    "-filter_complex",
    f"[1:v]scale={VW}:-2[v];[0:v][v]overlay=(W-w)/2:{vy}:format=auto,format=yuv420p[o]",
    "-map", "[o]", "-c:v", "libx264", "-crf", "18", "-c:a", "aac",
    "-shortest", str(out)], check=True)
print("DONE ->", out)
