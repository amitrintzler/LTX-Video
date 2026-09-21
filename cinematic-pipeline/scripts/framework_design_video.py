#!/usr/bin/env python3
"""Framework Design video: the production replacement for the site's
/assets/videos/framework-demo.mp4 (page: /framework-design).

Why a rebuild: the video it replaces opens on a blank grey frame, shows a
"Finish prerequisites" locked modal over several scenes, spends its time on
Physics/Math (which the page itself labels "framework demonstration only"),
is very dark, and never shows the 5-move methodology the page is about.

What this makes instead - every word of on-screen copy is the page's own:

  HOOK        logo, then the real page hero with a glide-to-subheading
  5 MOVES     designed motion graphics, one move per 8 beats, a progress
              spine that builds as the method builds
  STRUCTURE   the real Course-blueprint / Simulator-structure columns, one
              spotlit sweep each
  EXAMPLES    two designed diagrams built from the page's example templates
  PORTAL      the payoff: one idea fans out into every format (lessons, videos,
              podcasts, stories, games, open world, simulator, assistant), then
              REAL proof of four of them - a lesson page with every format
              tab, the daily podcast + video, the games arcade, the open world
  CTA         "Ready to design your own framework?"

Real vs drawn, stated plainly: page beats are a virtual camera over ONE real
retina capture of the live page (capture_framework_design.py), so every
pixel of UI is real. The methodology and example beats are motion design, not
UI mock-ups - they say so by looking like graphics, and contain only the
page's own text.

Music: an original score written for this film (framework_score.py,
synthesised with numpy, no third-party audio) on the video's own 97.35 BPM
beat grid. It is built the way the method is built: one bell note (the idea),
the drop, then each of the five moves adds a voice, the key lifts a whole tone
for the portal act, where every format (lesson, video, podcast, story, game,
open world...) enters in its own timbre, and the loop closes on the tonic.
Every scene change starts on a beat.

Usage:
    framework_design_video.py --stills 3,8,12,20     # QA frames -> work/stills/
    framework_design_video.py                         # full render + mix + poster
"""

from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

Image.MAX_IMAGE_PIXELS = None
RS = Image.Resampling
W, H, FPS = 1920, 1080, 30

HERE = Path(__file__).resolve().parent
OUT_DIR = Path.home() / "LTX-Renders" / "framework-design"
WORK = OUT_DIR / "work"
FONTS = Path.home() / "LTX-Studio" / "fonts"
# ---- music grid (measured; see module docstring) ---------------------------
BPM = 97.35
BEAT = 60.0 / BPM


def bt(b: float) -> float:
    return b * BEAT


B_DROP = 16
B_MOVES = 16
B_STRUCT = 56
B_EXAMPLES = 68
B_PORTAL = 84
B_CTA = 112
B_END = 120.5
T_END = bt(B_END)

# ---- brand ------------------------------------------------------------------
ACC_A = (0, 166, 229)  # hsl(198 100% 45%): the site's --gradient-primary start
ACC_B = (79, 70, 229)  # hsl(243 75% 59%): the site's --primary
OK = (34, 197, 94)
TXT = (238, 242, 255)
MUTED = (148, 163, 184)
BG_TOP, BG_BOT = (8, 10, 20), (15, 17, 34)

FONT_FILES = {
    "eb": "Montserrat-ExtraBold.ttf",
    "b": "Montserrat-Bold.ttf",
    "sb": "Montserrat-SemiBold.ttf",
    "qs": "Quicksand-SemiBold.ttf",
    "qm": "Quicksand-Medium.ttf",
}
FONT_CSS = {
    "Montserrat-ExtraBold.ttf": "Montserrat:wght@800",
    "Montserrat-Bold.ttf": "Montserrat:wght@700",
    "Montserrat-SemiBold.ttf": "Montserrat:wght@600",
    "Quicksand-SemiBold.ttf": "Quicksand:wght@600",
    "Quicksand-Medium.ttf": "Quicksand:wght@500",
}


def ensure_fonts() -> None:
    """The site's own faces (Montserrat headings, Quicksand body; SIL OFL),
    fetched once as static TrueType. A legacy Safari user-agent makes Google
    Fonts serve TTF instead of woff2, which PIL can read."""
    import re
    import urllib.request

    FONTS.mkdir(parents=True, exist_ok=True)
    ua = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/534.59.10 "
        "(KHTML, like Gecko) Version/5.1.9 Safari/534.59.10"
    )
    for fname, fam in FONT_CSS.items():
        dest = FONTS / fname
        if dest.is_file():
            continue
        req = urllib.request.Request(
            f"https://fonts.googleapis.com/css2?family={fam}",
            headers={"User-Agent": ua},
        )
        css = urllib.request.urlopen(req, timeout=30).read().decode()
        url = re.search(r"url\((https://[^)]+)\)", css).group(1)
        dest.write_bytes(urllib.request.urlopen(url, timeout=60).read())


@lru_cache(maxsize=None)
def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / FONT_FILES[name]), size)


# ---- small math helpers -----------------------------------------------------
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def e_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def e_in(x):
    x = clamp(x)
    return x**3


def e_io(x):
    x = clamp(x)
    return 4 * x**3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_t(a, b, t):
    return tuple(lerp(x, y, t) for x, y in zip(a, b))


# ---- text -------------------------------------------------------------------
@lru_cache(maxsize=512)
def text_img(txt: str, fname: str, size: int, fill: tuple) -> Image.Image:
    f = font(fname, size)
    bb = f.getbbox(txt)
    pad = 6
    img = Image.new("RGBA", (bb[2] + 2 * pad, bb[3] + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((pad - bb[0] * 0, pad), txt, font=f, fill=(*fill, 255))
    return img


def paste(frame: Image.Image, layer: Image.Image, xy, alpha=1.0, scale=1.0):
    if alpha <= 0.003:
        return
    if scale != 1.0:
        layer = layer.resize(
            (max(1, int(layer.width * scale)), max(1, int(layer.height * scale))),
            RS.BICUBIC,
        )
    x, y = int(xy[0]), int(xy[1])
    if alpha < 0.999:
        a = layer.getchannel("A")
        a = ImageChops.multiply(a, Image.new("L", a.size, int(255 * alpha)))
        layer = layer.copy()
        layer.putalpha(a)
    frame.paste(layer, (x, y), layer)


def wrap(txt: str, fname: str, size: int, max_w: int) -> list[str]:
    f = font(fname, size)
    lines, cur = [], ""
    for w in txt.split():
        trial = (cur + " " + w).strip()
        if f.getlength(trial) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_words(
    frame,
    lines,
    fname,
    size,
    fill,
    x,
    y,
    lh,
    t,
    start,
    stagger=0.06,
    rise=22,
    alpha=1.0,
):
    """Word-by-word reveal: each word eases up and in, staggered."""
    f = font(fname, size)
    k = 0
    for li, line in enumerate(lines):
        cx = x
        for w in line.split():
            a = e_out((t - start - k * stagger) / 0.42)
            layer = text_img(w, fname, size, fill)
            paste(
                frame,
                layer,
                (cx - 6, y + li * lh - 6 + (1 - a) * rise),
                alpha=a * alpha,
            )
            cx += f.getlength(w + " ")
            k += 1


def letterspaced(txt: str, gap: int = 2) -> str:
    return (" " * 0).join(c + (" " * gap if c != " " else " ") for c in txt).strip()


# ---- backgrounds ------------------------------------------------------------
@lru_cache(maxsize=1)
def bg_base() -> Image.Image:
    y = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    top, bot = np.array(BG_TOP, np.float32), np.array(BG_BOT, np.float32)
    arr = np.broadcast_to(top + (bot - top) * y, (H, W, 3)).copy()
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    g1 = np.exp(-(((xx - 260) ** 2 + (yy - 120) ** 2) / (2 * 560**2)))
    g2 = np.exp(-(((xx - 1680) ** 2 + (yy - 980) ** 2) / (2 * 680**2)))
    arr += g1[..., None] * np.array((0, 24, 44), np.float32)
    arr += g2[..., None] * np.array((24, 18, 62), np.float32)
    arr[::96, :, :] += 5  # faint grid
    arr[:, ::96, :] += 5
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


@lru_cache(maxsize=1)
def vignette() -> Image.Image:
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2)
    a = np.clip((d - 0.55) * 1.1, 0, 1) ** 1.6 * 150
    out = np.zeros((H, W, 4), np.uint8)
    out[..., 0], out[..., 1], out[..., 2] = 3, 4, 10
    out[..., 3] = a.astype(np.uint8)
    return Image.fromarray(out)


def with_particles(frame: Image.Image, t: float, n=26, strength=1.0):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for i in range(n):
        seed = i * 137.5
        px = (seed * 3.7) % W
        py = H - ((t * (14 + i % 5 * 3) + seed * 5) % (H + 40))
        r = 1.3 + (i % 3) * 0.7
        al = int((55 + 40 * math.sin(t * 1.6 + i)) * strength)
        d.ellipse([px - r, py - r, px + r, py + r], fill=(190, 230, 255, max(0, al)))
    frame.paste(ov, (0, 0), ov)


@lru_cache(maxsize=4)
def glow_sprite(rgb: tuple, size: int = 1000, peak: int = 46) -> Image.Image:
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    d = np.sqrt((xx - size / 2) ** 2 + (yy - size / 2) ** 2) / (size / 2)
    out = np.zeros((size, size, 4), np.uint8)
    out[..., 0], out[..., 1], out[..., 2] = rgb
    out[..., 3] = (np.clip(1 - d, 0, 1) ** 2 * peak).astype(np.uint8)
    return Image.fromarray(out)


def designed_bg(t: float) -> Image.Image:
    """Base gradient + two slow-drifting pools of light + drifting particles,
    so no designed scene is ever a still image, even during a hold."""
    f = bg_base().copy()
    for rgb, cx, cy in (
        (ACC_A, 330 + 320 * math.sin(t * 0.33), 220 + 140 * math.cos(t * 0.27)),
        (ACC_B, 1560 + 260 * math.sin(t * 0.29 + 2), 900 + 120 * math.cos(t * 0.36 + 1)),
    ):
        sp = glow_sprite(rgb)
        f.paste(sp, (int(cx - 500), int(cy - 500)), sp)
    with_particles(f, t)
    return f


# ---- AA canvas (shapes are drawn 2x and reduced so edges are smooth) -------
class AA:
    def __init__(self, box):
        self.box = box  # x0, y0, x1, y1 in frame coords
        self.w, self.h = box[2] - box[0], box[3] - box[1]
        self.img = Image.new("RGBA", (self.w * 2, self.h * 2), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    def p(self, x, y):
        return ((x - self.box[0]) * 2, (y - self.box[1]) * 2)

    def rrect(self, x, y, w, h, r, fill=None, outline=None, width=2):
        x0, y0 = self.p(x, y)
        self.d.rounded_rectangle(
            [x0, y0, x0 + w * 2, y0 + h * 2],
            radius=r * 2,
            fill=fill,
            outline=outline,
            width=width * 2,
        )

    def line(self, pts, color, width=4):
        q = [self.p(*pt) for pt in pts]
        self.d.line(q, fill=color, width=width * 2, joint="curve")
        for e in (q[0], q[-1]):
            r = width
            self.d.ellipse([e[0] - r, e[1] - r, e[0] + r, e[1] + r], fill=color)

    def dot(self, x, y, r, fill):
        cx, cy = self.p(x, y)
        self.d.ellipse([cx - r * 2, cy - r * 2, cx + r * 2, cy + r * 2], fill=fill)

    def ring(self, x, y, r, color, width=3):
        cx, cy = self.p(x, y)
        self.d.ellipse(
            [cx - r * 2, cy - r * 2, cx + r * 2, cy + r * 2],
            outline=color,
            width=width * 2,
        )

    def polygon(self, pts, fill):
        self.d.polygon([self.p(*pt) for pt in pts], fill=fill)

    def composite_onto(self, frame: Image.Image):
        small = self.img.resize((self.w, self.h), RS.LANCZOS)
        frame.paste(small, (self.box[0], self.box[1]), small)


def bezier(p0, p1, p2, p3, u):
    a = (1 - u) ** 3
    b = 3 * (1 - u) ** 2 * u
    c = 3 * (1 - u) * u**2
    d = u**3
    return (
        a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0],
        a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1],
    )


def gradient_fill(size, c1, c2) -> Image.Image:
    w, h = size
    t = (
        np.linspace(0, 1, w, dtype=np.float32)[None, :]
        + np.linspace(0, 1, h, dtype=np.float32)[:, None]
    ) / 2
    arr = np.zeros((h, w, 3), np.float32)
    for i in range(3):
        arr[..., i] = c1[i] + (c2[i] - c1[i]) * t
    return Image.fromarray(arr.astype(np.uint8))


@lru_cache(maxsize=32)
def gradient_text(txt: str, fname: str, size: int) -> Image.Image:
    mask = text_img(txt, fname, size, (255, 255, 255)).getchannel("A")
    grad = gradient_fill(mask.size, ACC_A, ACC_B)
    out = Image.new("RGBA", mask.size, (0, 0, 0, 0))
    out.paste(grad, (0, 0), mask)
    return out


@lru_cache(maxsize=4)
def logo_mark(px: int) -> Image.Image:
    """The site's mark (AppLogo.tsx geometry): gradient rounded square, white
    staircase to an apex node."""
    s = px * 4
    k = s / 40.0
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    grad = gradient_fill((s, s), (79, 70, 229), (196, 192, 255))
    m = Image.new("L", (s, s), 0)
    ImageDraw.Draw(m).rounded_rectangle(
        [0, 0, s - 1, s - 1], radius=int(10 * k), fill=255
    )
    img.paste(grad, (0, 0), m)
    d = ImageDraw.Draw(img)
    pts = [(7, 33), (7, 21), (20, 21), (20, 13), (33, 13), (33, 7)]
    q = [(x * k, y * k) for x, y in pts]
    d.line(q, fill=(255, 255, 255, 235), width=int(3.2 * k), joint="curve")
    for e in (q[0], q[-1]):
        r = 1.6 * k
        d.ellipse([e[0] - r, e[1] - r, e[0] + r, e[1] + r], fill=(255, 255, 255, 235))
    r = 4.4 * k
    d.ellipse([33 * k - r, 7 * k - r, 33 * k + r, 7 * k + r], fill=(255, 255, 255, 255))
    return img.resize((px, px), RS.LANCZOS)


# ---- panels / chips ---------------------------------------------------------
def panel(frame, x, y, w, h, alpha=1.0, accent=True):
    box = (
        max(0, int(x) - 4),
        max(0, int(y) - 4),
        min(W, int(x + w) + 4),
        min(H, int(y + h) + 4),
    )
    aa = AA(box)
    aa.rrect(
        x,
        y,
        w,
        h,
        22,
        fill=(9, 13, 28, int(228 * alpha)),
        outline=(255, 255, 255, int(34 * alpha)),
        width=1,
    )
    if accent:
        aa.rrect(x + 18, y + 22, 6, h - 44, 3, fill=(*ACC_A, int(255 * alpha)))
    aa.composite_onto(frame)


def chip(frame, x, y, txt, alpha=1.0, color=ACC_A):
    f = font("sb", 24)
    label = letterspaced(txt.upper(), 1)
    w = int(f.getlength(label)) + 44
    aa = AA((int(x) - 3, int(y) - 3, int(x) + w + 3, int(y) + 50 + 3))
    aa.rrect(
        x,
        y,
        w,
        50,
        25,
        fill=(0, 20, 34, int(190 * alpha)),
        outline=(*color, int(200 * alpha)),
        width=2,
    )
    aa.composite_onto(frame)
    paste(frame, text_img(label, "sb", 24, color), (x + 16, y + 6), alpha=alpha)
    return w


def lower_third(frame, lt, tin, tout, kicker, title, sub, pos="bottom"):
    a_in = e_out((lt - tin) / 0.5)
    a_out = 1 - e_in((lt - tout) / 0.4)
    alpha = min(a_in, a_out)
    if alpha <= 0.003:
        return
    sub_lines = wrap(sub, "qs", 30, 1320)
    h = 34 + 30 + 74 + 14 + len(sub_lines) * 40 + 30
    w = int(
        max(
            font("eb", 56).getlength(title),
            *(font("qs", 30).getlength(s) for s in sub_lines),
            font("sb", 24).getlength(letterspaced(kicker, 1)),
        )
        + 92
    )
    x = 96 + (1 - e_out((lt - tin) / 0.5)) * -46
    y = 64 if pos == "top" else H - 84 - h
    panel(frame, x, y, w, h, alpha)
    paste(
        frame,
        text_img(letterspaced(kicker, 1), "sb", 24, ACC_A),
        (x + 44, y + 26),
        alpha=alpha,
    )
    paste(frame, text_img(title, "eb", 56, TXT), (x + 44, y + 62), alpha=alpha)
    for i, s in enumerate(sub_lines):
        paste(
            frame,
            text_img(s, "qs", 30, MUTED),
            (x + 44, y + 62 + 74 + 8 + i * 40),
            alpha=alpha,
        )


# ---- real-page camera -------------------------------------------------------
class PageCam:
    def __init__(self):
        base = Image.open(WORK / "page.png").convert("RGB")
        self.levels = {2.0: base}
        for s in (1.5, 1.0):
            self.levels[s] = base.resize(
                (int(base.width * s / 2), int(base.height * s / 2)), RS.LANCZOS
            )
        self.rects = json.loads((WORK / "rects.json").read_text())["items"]

    def find(self, text: str, tag: str | None = None, card: bool = False):
        for it in self.rects:
            if it["text"].startswith(text) and (tag is None or it["tag"] == tag):
                if card and it["card"]:
                    c = it["card"]
                    return (c["x"], c["y"], c["w"], c["h"])
                r = it["rect"]
                return (r["x"], r["y"], r["w"], r["h"])
        raise KeyError(text)

    def frame(self, cx, cy, zoom) -> Image.Image:
        s = next(v for v in (1.0, 1.5, 2.0) if v >= zoom - 1e-6)
        r = s / zoom
        x0 = cx - (W / zoom) / 2
        y0 = cy - (H / zoom) / 2
        return self.levels[s].transform(
            (W, H),
            Image.Transform.AFFINE,
            (r, 0, x0 * s, 0, r, y0 * s),
            resample=RS.BICUBIC,
            fillcolor=(9, 11, 20),
        )


def spotlight(frame, rect_screen, dim, pad=18, radius=20):
    if dim <= 0.01:
        return frame
    fw, fh = frame.size
    x, y, w, h = rect_screen
    box = [x - pad, y - pad, x + w + pad, y + h + pad]
    m = Image.new("L", (fw // 2, fh // 2), 0)
    ImageDraw.Draw(m).rounded_rectangle([c / 2 for c in box], radius=radius / 2, fill=255)
    m = m.filter(ImageFilter.GaussianBlur(7)).resize((fw, fh), RS.BILINEAR)
    dark = Image.blend(frame, Image.new("RGB", (fw, fh), (3, 5, 12)), dim)
    out = Image.composite(frame, dark, m)
    aa = AA((max(0, int(box[0]) - 8), max(0, int(box[1]) - 8), min(fw, int(box[2]) + 8), min(fh, int(box[3]) + 8)))
    aa.rrect(box[0], box[1], box[2] - box[0], box[3] - box[1], radius, outline=(*ACC_A, int(230 * min(1, dim / 0.4))), width=3)
    aa.composite_onto(out)
    return out


class PageScene:
    """A virtual camera + spotlight over the real page capture.

    stops: (beat_the_move_starts, cx, cy, zoom, spot_rect_or_None, dim).
    Each move eases over MOVE_S seconds and starts exactly on its beat.
    """

    MOVE_S = 0.85

    def __init__(self, cam: PageCam, b0: float, stops, lowers, chip_txt=None):
        self.cam, self.b0, self.lowers, self.chip_txt = cam, b0, lowers, chip_txt
        # a None spotlight adopts the next real rect so it can fade in place
        st = [list(s) for s in stops]
        for i, s in enumerate(st):
            if s[4] is None:
                s[4] = next(
                    (n[4] for n in st[i + 1 :] if n[4] is not None), (0, 0, 10, 10)
                )
        self.stops = st

    def state(self, lt):
        cur = self.stops[0][1:]
        for i in range(1, len(self.stops)):
            s = self.stops[i]
            t0 = bt(s[0])
            p = e_io((lt - t0) / self.MOVE_S)
            if lt < t0:
                break
            prev = self.stops[i - 1]
            cur = [
                lerp(prev[1], s[1], p),
                lerp(prev[2], s[2], p),
                lerp(prev[3], s[3], p),
                tuple(lerp(a, b, p) for a, b in zip(prev[4], s[4])),
                lerp(prev[5], s[5], p),
            ]
            if p < 1:
                break
            cur = list(s[1:])
        return cur

    def render(self, t: float) -> Image.Image:
        lt = t - bt(self.b0)
        cx, cy, z, rect, dim = self.state(lt)
        z = min(2.0, z * (1 + 0.004 * max(0.0, lt)))  # slow push, never a locked-off frame
        cx += 7 * math.sin(lt * 0.55)
        fr = self.cam.frame(cx, cy, z)
        x0, y0 = cx - (W / z) / 2, cy - (H / z) / 2
        rs = ((rect[0] - x0) * z, (rect[1] - y0) * z, rect[2] * z, rect[3] * z)
        fr = spotlight(fr, rs, dim)
        fr.paste(vignette(), (0, 0), vignette())
        if self.chip_txt:
            chip(fr, 96, 84, self.chip_txt, alpha=e_out((lt - 0.2) / 0.5))
        for tin, tout, k, ti, su, *pos in self.lowers:
            lower_third(fr, lt, bt(tin), bt(tout), k, ti, su, pos[0] if pos else "bottom")
        return fr


# ---- designed scene: the 5 moves -------------------------------------------
MOVES = [
    (
        "Define the transformation",
        "Write the before-and-after skill change in one sentence.",
        "Transformation",
    ),
    (
        "Break it into milestones",
        "Identify 3-5 measurable milestones that prove progress.",
        "Milestones",
    ),
    (
        "Build the lesson spine",
        "Draft the essential lessons that teach each milestone.",
        "Lesson spine",
    ),
    (
        "Create simulator reps",
        "Attach a practice scenario to each lesson for repetition.",
        "Simulator reps",
    ),
    (
        "Close the loop",
        "Add reflection prompts and success criteria after each rep.",
        "Close the loop",
    ),
]
SPINE_X = [240, 600, 960, 1320, 1680]
SPINE_Y = 936


@lru_cache(maxsize=8)
def move_icon(kind: int) -> Image.Image:
    px = 132
    aa = AA((0, 0, px, px))
    c = (255, 255, 255, 240)
    ac = (*ACC_A, 255)
    if kind == 0:  # before -> after
        aa.ring(30, 66, 15, c, 5)
        aa.line([(56, 66), (84, 66)], ac, 6)
        aa.polygon([(84, 52), (84, 80), (104, 66)], ac)
        aa.dot(112, 66, 0.1, c)
    elif kind == 1:  # ascending milestones with a flag
        for i in range(3):
            aa.rrect(
                16 + i * 34,
                96 - i * 24,
                28,
                24 + i * 24,
                4,
                fill=(255, 255, 255, 60 + i * 60),
            )
        aa.line([(90, 50), (90, 16)], ac, 5)
        aa.polygon([(90, 16), (118, 26), (90, 36)], ac)
    elif kind == 2:  # spine with lesson nodes
        aa.line([(34, 16), (34, 116)], c, 5)
        for i, y in enumerate((26, 66, 106)):
            aa.dot(34, y, 9, ac)
            aa.rrect(56, y - 13, 60, 26, 7, fill=(255, 255, 255, 70))
    elif kind == 3:  # simulator screen with candles
        aa.rrect(10, 22, 112, 88, 12, outline=c, width=4)
        for x, top, bot, col in (
            (38, 50, 84, (34, 197, 94, 255)),
            (66, 42, 76, (34, 197, 94, 255)),
            (94, 60, 92, (239, 68, 68, 255)),
        ):
            aa.line([(x, top - 8), (x, bot + 8)], col, 3)
            aa.rrect(x - 8, top, 16, bot - top, 3, fill=col)
    else:  # loop with a check
        aa.ring(66, 66, 40, c, 6)
        aa.line([(48, 68), (61, 82), (86, 52)], ac, 8)
    img = aa.img.resize((px, px), RS.LANCZOS)
    return img


def draw_move(frame, i: int, lt: float, alpha: float, dx: float = 0.0):
    if alpha <= 0.003:
        return
    title, desc, _ = MOVES[i]
    num = f"0{i + 1}"
    a_num = e_out(lt / 0.5) * alpha
    nf = 6 * math.sin(lt * 1.4)  # gentle float keeps the hold alive
    fl = 4 * math.sin(lt * 1.7 + 1)
    paste(
        frame,
        gradient_text(num, "eb", 360),
        (150 + dx + (1 - e_out(lt / 0.55)) * -90, 250 + nf),
        alpha=a_num,
    )
    a_ic = e_out((lt - 0.1) / 0.45) * alpha
    aa = AA((770 + int(dx) - 6, 236, 770 + int(dx) + 156, 386))
    aa.rrect(
        776 + dx,
        242 + fl,
        144,
        144,
        34,
        fill=(255, 255, 255, int(20 * a_ic)),
        outline=(*ACC_A, int(150 * a_ic)),
        width=2,
    )
    aa.composite_onto(frame)
    paste(frame, move_icon(i), (782 + dx, 248 + fl + (1 - a_ic) * 14), alpha=a_ic)
    lines = wrap(title, "eb", 84, 960)
    draw_words(frame, lines, "eb", 84, TXT, 790 + dx, 428, 100, lt, 0.24, alpha=alpha)
    dy = 428 + len(lines) * 100 + 18
    dlines = wrap(desc, "qs", 44, 940)
    for j, s in enumerate(dlines):
        paste(
            frame,
            text_img(s, "qs", 44, (196, 206, 226)),
            (790 + dx, dy + j * 56 + (1 - e_out((lt - 0.7) / 0.5)) * 14),
            alpha=e_out((lt - 0.7) / 0.5) * alpha,
        )


def draw_spine(frame, cur: int, lt: float, t_global: float):
    aa = AA((150, SPINE_Y - 44, 1770, SPINE_Y + 52))
    aa.line([(SPINE_X[0], SPINE_Y), (SPINE_X[-1], SPINE_Y)], (255, 255, 255, 46), 5)
    end_x = (
        SPINE_X[cur]
        if cur == 0
        else lerp(SPINE_X[cur - 1], SPINE_X[cur], e_io(lt / 0.7))
    )
    if cur > 0 or end_x > SPINE_X[0]:
        aa.line([(SPINE_X[0], SPINE_Y), (end_x, SPINE_Y)], (*ACC_A, 255), 5)
    for k, x in enumerate(SPINE_X):
        done = k < cur or (k == cur and (cur == 0 or lt > 0.55))
        if done:
            aa.dot(x, SPINE_Y, 14 if k != cur else 18, (*ACC_A, 255))
            aa.dot(x, SPINE_Y, 5, (255, 255, 255, 255))
        else:
            aa.ring(x, SPINE_Y, 13, (255, 255, 255, 90), 3)
        if k == cur:
            pr = (t_global * 0.9) % 1.0
            aa.ring(x, SPINE_Y, 22 + pr * 16, (*ACC_A, int(200 * (1 - pr))), 3)
    aa.composite_onto(frame)
    for k, x in enumerate(SPINE_X):
        lab = MOVES[k][2]
        w = font("qs", 26).getlength(lab)
        paste(
            frame,
            text_img(lab, "qs", 26, TXT if k <= cur else (110, 122, 145)),
            (x - w / 2 - 6, SPINE_Y + 34),
        )


def moves_scene(t: float) -> Image.Image:
    lt_all = t - bt(B_MOVES)
    fr = designed_bg(t)
    chip(fr, 96, 84, "The 5-move methodology", alpha=e_out((lt_all - 0.2) / 0.5))
    paste(
        fr,
        text_img(
            "Follow these steps to convert a raw idea into a complete learning experience.",
            "qs",
            30,
            MUTED,
        ),
        (96, 150),
        alpha=e_out((lt_all - 0.5) / 0.6),
    )
    per = bt(8)
    i = min(4, int(lt_all // per))
    lt = lt_all - i * per
    # incoming move on top; outgoing slides left and fades over 0.28s
    if i > 0 and lt < 0.2:
        p = lt / 0.2
        draw_move(fr, i - 1, per, 1 - e_out(p), dx=-70 * e_out(p))
    draw_move(fr, i, lt, 1.0)
    draw_spine(fr, i, lt, t)
    return fr


# ---- designed scene: example diagrams --------------------------------------
def node_card(aa: AA, x, y, w, h, alpha, accent=ACC_A, fill_tint=0):
    aa.rrect(
        x,
        y,
        w,
        h,
        20,
        fill=(14, 20, 40, int(236 * alpha)),
        outline=(255, 255, 255, int(40 * alpha)),
        width=1,
    )
    aa.rrect(x, y + 18, 5, h - 36, 2.5, fill=(*accent, int(255 * alpha)))


def arrow(aa: AA, x0, y, x1, p, alpha, color=ACC_A):
    if p <= 0:
        return
    xe = lerp(x0, x1, e_io(p))
    aa.line([(x0, y), (xe, y)], (*color, int(255 * alpha)), 4)
    if p > 0.85:
        aa.polygon(
            [(xe + 2, y), (xe - 18, y - 12), (xe - 18, y + 12)],
            (*color, int(255 * alpha)),
        )


def draw_check(aa: AA, cx, cy, s, p, alpha):
    pts = [
        (cx - s * 0.5, cy + s * 0.05),
        (cx - s * 0.12, cy + s * 0.42),
        (cx + s * 0.55, cy - s * 0.38),
    ]
    if p <= 0:
        return
    seg1 = clamp(p / 0.4)
    seg2 = clamp((p - 0.4) / 0.6)
    a = (pts[0][0], pts[0][1])
    m = (lerp(pts[0][0], pts[1][0], seg1), lerp(pts[0][1], pts[1][1], seg1))
    aa.line([a, m], (255, 255, 255, int(255 * alpha)), 8)
    if seg2 > 0:
        e = (lerp(pts[1][0], pts[2][0], seg2), lerp(pts[1][1], pts[2][1], seg2))
        aa.line([pts[1], e], (255, 255, 255, int(255 * alpha)), 8)


TREE = {
    "title": "Idea → Course map",
    "sub": "“How to trade earnings” becomes a 4-part course series.",
    "idea": "How to trade earnings",
    "mods": [
        "Module 1: Earnings basics",
        "Module 2: Pre-earnings setups",
        "Module 3: Post-earnings reactions",
        "Module 4: Risk management playbook",
    ],
}
CHAINS = [
    {
        "title": "Lesson → Simulator rep",
        "sub": "Each lesson feeds directly into a practice session.",
        "nodes": [
            ("LESSON", "Identify implied volatility crush"),
            ("SCENARIO", "Simulate two earnings releases"),
            ("DEBRIEF", "Compare outcomes and risk"),
        ],
        "final": False,
    },
    {
        "title": "Milestone → Assessment",
        "sub": "Confirm progress with a structured check-in.",
        "nodes": [
            ("MILESTONE", "Build a neutral options strategy"),
            ("ASSESSMENT", "5-minute scenario quiz"),
            ("SUCCESS", "80% accuracy or higher"),
        ],
        "final": True,
    },
]


def diagram_header(fr, lt_all, title, sub, lt):
    chip(fr, 96, 84, "Example templates", alpha=e_out((lt_all - 0.2) / 0.5))
    paste(
        fr,
        text_img(title, "eb", 76, TXT),
        (90, 166 + (1 - e_out((lt - 0.05) / 0.5)) * 24),
        alpha=e_out((lt - 0.05) / 0.5),
    )
    paste(
        fr,
        text_img(sub, "qs", 38, MUTED),
        (96, 268 + (1 - e_out((lt - 0.3) / 0.5)) * 16),
        alpha=e_out((lt - 0.3) / 0.5),
    )


def draw_tree(fr, lt, t):
    by = 4 * math.sin(t * 1.25)
    mods_y = [400 + by, 520 + by, 640 + by, 760 + by]
    idea = (170, 560 + by, 520, 140)
    p0 = (idea[0] + idea[2], idea[1] + idea[3] / 2)
    aa = AA((140, 380, 1790, 900))
    a_idea = e_out((lt - 0.5) / 0.5)
    node_card(aa, idea[0], idea[1], idea[2], idea[3], a_idea, ACC_A)
    texts = [(idea[0] + 34, idea[1] + 34, TREE["idea"], "eb", 40, a_idea)]
    for k, y in enumerate(mods_y):
        s = 1.2 + k * 0.32
        p_line = clamp((lt - s) / 0.7)
        end = (1000, y + 50)
        c1, c2 = (p0[0] + 160, p0[1]), (end[0] - 160, end[1])
        if p_line > 0:
            pts = [bezier(p0, c1, c2, end, u) for u in np.linspace(0, e_io(p_line), 26)]
            aa.line(pts, (*ACC_A, 235), 4)
        a_mod = e_out((lt - s - 0.55) / 0.4)
        if a_mod > 0:
            node_card(aa, 1000 + (1 - a_mod) * 30, y, 700, 100, a_mod, ACC_B)
            texts.append(
                (1000 + 34 + (1 - a_mod) * 30, y + 25, TREE["mods"][k], "b", 34, a_mod)
            )
        if lt > s + 1.4:  # traveling pulse along a finished connector
            u = ((t * 0.55) + k * 0.23) % 1.0
            x, y2 = bezier(p0, c1, c2, end, u)
            aa.dot(x, y2, 6, (255, 255, 255, 235))
    aa.composite_onto(fr)
    for x, y, s, fn, sz, a in texts:
        paste(fr, text_img(s, fn, sz, TXT), (x - 6, y - 6), alpha=a)


def draw_chain(fr, lt, t, ch):
    xs = [170, 725, 1280]
    by = 4 * math.sin(t * 1.25 + 1)
    y, w, h = 540 + by, 470, 210
    aa = AA((140, 500, 1790, 800))
    texts = []
    for k, (kick, main) in enumerate(ch["nodes"]):
        s = 0.5 + k * 1.3
        a = e_out((lt - s) / 0.5)
        last_ok = ch["final"] and k == 2
        accent = OK if last_ok else (ACC_A if k == 0 else ACC_B)
        if a > 0:
            node_card(aa, xs[k] + (1 - a) * 26, y, w, h, a, accent)
            if last_ok:
                aa.rrect(xs[k], y, w, h, 20, outline=(*OK, int(140 * a)), width=2)
            texts.append((xs[k] + (1 - a) * 26 + 40, y + 34, kick, "sb", 24, accent, a))
            for j, ln in enumerate(wrap(main, "qs", 42, w - 80)):
                texts.append(
                    (xs[k] + (1 - a) * 26 + 40, y + 82 + j * 52, ln, "qs", 42, TXT, a)
                )
        if k < 2:
            arrow(
                aa,
                xs[k] + w + 14,
                y + h / 2,
                xs[k + 1] - 14,
                clamp((lt - s - 0.55) / 0.55),
                1.0,
            )
            if lt > s + 1.2:  # a pulse keeps travelling once the arrow is drawn
                u = (t * 0.9 + k * 0.35) % 1.0
                aa.dot(lerp(xs[k] + w + 14, xs[k + 1] - 14, u), y + h / 2, 6, (255, 255, 255, 235))
    if ch["final"] and lt > 3.2:
        draw_check(aa, xs[2] + w - 78, y + 70, 64, clamp((lt - 3.2) / 0.5), 1.0)
    aa.composite_onto(fr)
    for x, yy, s, fn, sz, col, a in texts:
        paste(fr, text_img(s, fn, sz, col), (x - 6, yy - 6), alpha=a)


def examples_scene(t: float) -> Image.Image:
    lt_all = t - bt(B_EXAMPLES)
    per = bt(8)
    i = min(1, int(lt_all // per))
    lt = lt_all - i * per
    fr = designed_bg(t)
    if i == 0:
        diagram_header(fr, lt_all, TREE["title"], TREE["sub"], lt)
        draw_tree(fr, lt, t)
    else:
        ch = CHAINS[i - 1]
        diagram_header(fr, lt_all, ch["title"], ch["sub"], lt)
        draw_chain(fr, lt, t, ch)
    if i > 0 and lt < 0.25:  # quick dip between diagrams
        fr = Image.blend(fr, Image.new("RGB", (W, H), BG_TOP), 1 - e_out(lt / 0.25))
    return fr


# ---- "what you get": one idea -> every format, then real proof ---------------
PORTAL_TILES = ["Lessons", "Videos", "Podcasts", "Stories", "Games", "Open world", "Simulator", "AI assistant", "and more"]
REPO_ASSETS = HERE.parent / "trailers"


@lru_cache(maxsize=16)
def tile_icon(kind: int) -> Image.Image:
    px = 56
    aa = AA((0, 0, px, px))
    c, dim, ac = (255, 255, 255, 235), (255, 255, 255, 110), (*ACC_A, 255)
    if kind == 0:  # lessons: open book
        aa.rrect(8, 12, 18, 32, 3, outline=c, width=3)
        aa.rrect(30, 12, 18, 32, 3, outline=ac, width=3)
    elif kind == 1:  # videos: play
        aa.rrect(6, 14, 44, 28, 6, outline=c, width=3)
        aa.polygon([(22, 21), (22, 35), (36, 28)], ac)
    elif kind == 2:  # podcasts: microphone
        aa.rrect(21, 5, 14, 24, 7, fill=c)
        aa.line([(14, 26), (14, 30), (20, 38), (28, 40), (36, 38), (42, 30), (42, 26)], ac, 3)
        aa.line([(28, 40), (28, 50)], c, 3)
    elif kind == 3:  # stories: a page with lines
        aa.rrect(11, 7, 34, 42, 4, outline=c, width=3)
        for yy in (19, 27, 35):
            aa.line([(18, yy), (38, yy)], ac if yy == 19 else dim, 3)
    elif kind == 4:  # games: pad
        aa.rrect(5, 15, 46, 28, 14, outline=c, width=3)
        aa.line([(13, 29), (23, 29)], ac, 3)
        aa.line([(18, 24), (18, 34)], ac, 3)
        aa.dot(36, 26, 3, ac)
        aa.dot(42, 32, 3, ac)
    elif kind == 5:  # open world: city blocks
        aa.rrect(7, 27, 13, 22, 2, fill=dim)
        aa.rrect(22, 12, 14, 37, 2, fill=c)
        aa.rrect(38, 22, 11, 27, 2, fill=dim)
        aa.dot(29, 20, 2.5, ac)
    elif kind == 6:  # simulator: candles
        for x, top, bot, col in ((16, 24, 44, (34, 197, 94, 255)), (28, 14, 36, (34, 197, 94, 255)), (40, 26, 46, (239, 68, 68, 255))):
            aa.line([(x, top - 6), (x, bot + 6)], col, 2)
            aa.rrect(x - 5, top, 10, bot - top, 2, fill=col)
    elif kind == 7:  # assistant: speech bubble
        aa.rrect(6, 9, 44, 30, 9, outline=c, width=3)
        aa.polygon([(15, 38), (15, 50), (28, 38)], c)
        for x in (19, 28, 37):
            aa.dot(x, 24, 2.5, ac)
    else:  # and more
        for x in (13, 28, 43):
            aa.dot(x, 28, 4.5, ac)
    return aa.img.resize((px, px), RS.LANCZOS)


def draw_portal_hub(fr, lt, t):
    by = 4 * math.sin(t * 1.25)
    a_h = e_out((lt - 0.1) / 0.5)
    chip(fr, 96, 84, "What you get", alpha=a_h)
    paste(fr, text_img("One idea. A whole learning portal.", "eb", 74, TXT), (90, 160 + (1 - a_h) * 24), alpha=a_h)
    a_s = e_out((lt - 0.35) / 0.5)
    paste(fr, text_img("Lessons, videos, podcasts, stories, games and an open world, all fitted to your idea.", "qs", 36, MUTED), (96, 262 + (1 - a_s) * 16), alpha=a_s)
    aa = AA((120, 372, 1830, 800))
    idea = (120, 513 + by, 520, 130)
    a_idea = e_out((lt - 0.4) / 0.5)
    node_card(aa, idea[0], idea[1], idea[2], idea[3], a_idea, ACC_A)
    p0 = (idea[0] + idea[2], idea[1] + idea[3] / 2)
    geo = []
    for k, label in enumerate(PORTAL_TILES):
        col, row = k % 3, k // 3
        x, y = 730 + col * 364, 400 + row * 126 + by
        st = 0.9 + k * 0.2
        end = (x, y + 52)
        c1, c2 = (p0[0] + 50, p0[1]), (end[0] - 50, end[1])
        geo.append((k, label, x, y, st))
        p_line = clamp((lt - st) / 0.55)
        if p_line > 0:
            pts = [bezier(p0, c1, c2, end, u) for u in np.linspace(0, e_io(p_line), 24)]
            aa.line(pts, (*ACC_A, 215), 3)
        if lt > st + 1.4:
            u = (t * 0.55 + k * 0.17) % 1.0
            px_, py_ = bezier(p0, c1, c2, end, u)
            aa.dot(px_, py_, 5, (255, 255, 255, 230))
    labels = []
    for k, label, x, y, st in geo:  # tiles drawn after every line so lines pass behind them
        a = e_out((lt - st - 0.45) / 0.35)
        if a > 0:
            node_card(aa, x + (1 - a) * 24, y, 340, 104, a, ACC_B if k % 2 else ACC_A)
            labels.append((k, x + (1 - a) * 24, y, a, label))
    aa.composite_onto(fr)
    paste(fr, text_img("YOUR IDEA", "sb", 22, ACC_A), (idea[0] + 34, idea[1] + 24), alpha=a_idea)
    paste(fr, text_img("How to trade earnings", "eb", 36, TXT), (idea[0] + 34, idea[1] + 62), alpha=a_idea)
    for k, x, y, a, label in labels:
        paste(fr, tile_icon(k), (x + 22, y + 24), alpha=a)
        paste(fr, text_img(label, "b", 30, TXT), (x + 96 - 6, y + 34 - 6), alpha=a)


PROOFS = [
    dict(
        src="lesson", crop=(236, 190, 1448, 469), scale=1.19,
        kicker="EVERY LESSON", title="Every format, one lesson",
        sub="Listen / Watch · Storybook explanation · Games · Story · Quiz · Ask assistant",
        spots=[(0.5, (934, 284, 712, 44)), (1.5, (276, 500, 1368, 58))],
    ),
    dict(
        src="daily", crop=(488, 335, 944, 470), scale=1.3,
        kicker="EVERY DAY", title="Podcasts and videos",
        sub="Every trading day, one real market event taken apart.",
        spots=[(0.5, (553, 458, 395, 256)), (1.2, (972, 458, 395, 256)), (1.9, (553, 736, 571, 62))],
    ),
    dict(
        src="games", crop=(236, 420, 1448, 571), scale=1.19,
        kicker="GAMES", title="Practice you can play",
        sub="Fast playable drills for options mechanics, strategy, and market-making.",
        spots=[(0.5, (276, 436, 1368, 244)), (1.5, (276, 697, 910, 242))],
    ),
    dict(
        src="city", crop=(0, 60, 1920, 800), scale=0.9,
        kicker="OPEN WORLD", title="A city you can trade in",
        sub="Walk the city, take missions, make options decisions.",
        spots=[],
    ),
]


@lru_cache(maxsize=8)
def proof_src(name: str) -> Image.Image:
    path = {
        "lesson": WORK / "portal" / "lesson.png",
        "daily": WORK / "portal" / "daily.png",
        "games": REPO_ASSETS / "mini-games" / "assets" / "games_a.png",
        "city": REPO_ASSETS / "open-world" / "assets" / "city_a.png",
    }[name]
    return Image.open(path).convert("RGB")


@lru_cache(maxsize=8)
def round_mask(size: tuple, r: int) -> Image.Image:
    m = Image.new("L", (size[0] * 2, size[1] * 2), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0] * 2 - 1, size[1] * 2 - 1], radius=r * 2, fill=255)
    return m.resize(size, RS.LANCZOS)


@lru_cache(maxsize=8)
def card_shadow(size: tuple) -> Image.Image:
    pad = 60
    m = Image.new("L", (size[0] + 2 * pad, size[1] + 2 * pad), 0)
    ImageDraw.Draw(m).rounded_rectangle([pad, pad + 16, pad + size[0], pad + 16 + size[1]], radius=24, fill=150)
    return m.filter(ImageFilter.GaussianBlur(26))


def spot_state(spots, lt):
    if not spots:
        return None, 0.0
    rect = spots[0][1]
    for k in range(1, len(spots)):
        t0, r1 = spots[k]
        p = e_io((lt - t0) / 0.5)
        if lt < t0:
            break
        rect = tuple(lerp(a, b, p) for a, b in zip(spots[k - 1][1], r1))
        if p < 1:
            break
        rect = r1
    return rect, 0.72 * e_out((lt - 0.3) / 0.4)


def proof_frame(i: int, lt: float, t: float) -> Image.Image:
    P = PROOFS[i]
    src = proof_src(P["src"])
    cx0, cy0, cw, ch = P["crop"]
    dw, dh = int(cw * P["scale"]), int(ch * P["scale"])
    z = 1 + 0.012 * lt
    cw2, ch2 = cw / z, ch / z
    x0 = cx0 + (cw - cw2) / 2 + 8 * math.sin(lt * 0.55)
    y0 = cy0 + (ch - ch2) / 2 + 5 * math.cos(lt * 0.45)
    card = src.transform((dw, dh), Image.Transform.AFFINE, (cw2 / dw, 0, x0, 0, ch2 / dh, y0), resample=RS.BICUBIC, fillcolor=(9, 11, 20))
    rect, dim = spot_state(P["spots"], lt)
    if rect is not None:
        rc = ((rect[0] - x0) * dw / cw2, (rect[1] - y0) * dh / ch2, rect[2] * dw / cw2, rect[3] * dh / ch2)
        card = spotlight(card, rc, dim, pad=10, radius=14)
    fr = designed_bg(t)
    a = e_out(lt / 0.4)
    chip(fr, 96, 84, P["kicker"], alpha=a)
    paste(fr, text_img(P["title"], "eb", 64, TXT), (90, 150 + (1 - a) * 20), alpha=a)
    paste(fr, text_img(P["sub"], "qs", 34, MUTED), (96, 236 + (1 - a) * 14), alpha=e_out((lt - 0.15) / 0.4))
    x, y = (W - dw) // 2, min(330, 1050 - dh) + int(5 * math.sin(t * 1.2)) + int((1 - a) * 26)
    sh = card_shadow((dw, dh))
    fr.paste(Image.new("RGB", sh.size, (2, 3, 8)), (x - 60, y - 60), ImageChops.multiply(sh, Image.new("L", sh.size, int(255 * a))))
    m = round_mask((dw, dh), 22)
    if a < 0.999:
        m = ImageChops.multiply(m, Image.new("L", m.size, int(255 * a)))
    fr.paste(card, (x, y), m)
    aa = AA((x - 4, y - 4, x + dw + 4, y + dh + 4))
    aa.rrect(x, y, dw, dh, 22, outline=(255, 255, 255, int(46 * a)), width=1)
    aa.composite_onto(fr)
    return fr


def portal_close(lt: float, t: float) -> Image.Image:
    fr = designed_bg(t)
    paste(fr, logo_mark(88), (W // 2 - 44, 170), alpha=e_out(lt / 0.5))
    rows = [("One idea.", "eb", 150, True, 0.0, 300), ("A full learning portal", "eb", 92, False, 0.55, 500), ("for you only.", "eb", 92, True, 1.1, 616)]
    for txt, fn, sz, grad, st, y in rows:
        a = e_out((lt - st) / 0.5)
        lay = gradient_text(txt, fn, sz) if grad else text_img(txt, fn, sz, TXT)
        paste(fr, lay, (W // 2 - lay.width // 2, y + (1 - a) * 30), alpha=a)
    return fr


def portal_scene(t: float) -> Image.Image:
    lt_all = t - bt(B_PORTAL)
    hub_end, close_start, per = bt(7), bt(23), bt(4)
    if lt_all < hub_end:
        fr = designed_bg(t)
        draw_portal_hub(fr, lt_all, t)
        return fr
    if lt_all < close_start:
        rel = lt_all - hub_end
        i = min(3, int(rel // per))
        lt = rel - i * per
        fr = proof_frame(i, lt, t)
        if lt < 0.25:
            if i == 0:
                prev = designed_bg(t)
                draw_portal_hub(prev, lt_all, t)
            else:
                prev = proof_frame(i - 1, lt + per, t)
            fr = Image.blend(prev, fr, e_io(lt / 0.25))
        return fr
    fr = portal_close(lt_all - close_start, t)
    x = lt_all - close_start
    if x < 0.25:
        fr = Image.blend(proof_frame(3, x + bt(4), t), fr, e_io(x / 0.25))
    return fr


# ---- scenes: hook / structure / cta ----------------------------------------
def logo_card(t: float) -> Image.Image:
    fr = designed_bg(t)
    a = e_out(t / 0.9)
    wm_w = int(
        max(font("b", 58).getlength("OPTIONS"), font("eb", 66).getlength("EDUCATOR"))
    )
    gx = (W - (150 + 44 + wm_w)) // 2
    gy = H // 2 - 75 + int(3 * math.sin(t * 1.6))
    paste(fr, logo_mark(150), (gx, gy + (1 - a) * 12), alpha=a)
    paste(
        fr,
        text_img("OPTIONS", "b", 58, (215, 222, 240)),
        (gx + 194 - 6, gy - 6 + (1 - a) * 12),
        alpha=a,
    )
    paste(
        fr,
        gradient_text("EDUCATOR", "eb", 66),
        (gx + 194 - 6, gy + 62 + (1 - a) * 12),
        alpha=a,
    )
    return fr


def poster_frame() -> Image.Image:
    """The still shown in the <video poster> before play: the promise, the
    brand, and the method's five moves lit up as the progress spine."""
    fr = bg_base().copy()
    with_particles(fr, 3.0, n=34)
    chip(fr, 150, 150, "Framework design")
    for i, line in enumerate(["Turn any idea into a", "course + simulator blueprint"]):
        paste(fr, gradient_text(line, "eb", 104) if i else text_img(line, "eb", 104, TXT), (144, 250 + i * 128))
    paste(fr, text_img("One idea becomes a full learning portal, for you only:", "qs", 40, (196, 206, 226)), (150, 540))
    paste(fr, text_img("lessons, videos, podcasts, stories, games and an open world.", "qs", 40, (196, 206, 226)), (150, 594))
    aa = AA((150, 800, 1770, 1000))
    aa.line([(SPINE_X[0], SPINE_Y - 100), (SPINE_X[-1], SPINE_Y - 100)], (*ACC_A, 255), 5)
    for x in SPINE_X:
        aa.dot(x, SPINE_Y - 100, 15, (*ACC_A, 255))
        aa.dot(x, SPINE_Y - 100, 5, (255, 255, 255, 255))
    aa.composite_onto(fr)
    for k, x in enumerate(SPINE_X):
        lab = MOVES[k][2]
        w = font("qs", 28).getlength(lab)
        paste(fr, text_img(lab, "qs", 28, TXT), (x - w / 2 - 6, SPINE_Y - 100 + 30))
    paste(fr, logo_mark(84), (W - 84 - 110, 96))
    fr.paste(vignette(), (0, 0), vignette())
    return fr


def build_scenes(cam: PageCam):
    h1 = cam.find("Turn any idea", "h1")
    sub = cam.find("Use this repeatable framework", "p")
    hook = PageScene(
        cam,
        0,
        [
            (0, 700, 330, 1.3, None, 0.0),
            (5, 700, 330, 1.42, h1, 0.74),
            (10, 760, 360, 1.42, sub, 0.74),
        ],
        [
            (
                4.4,
                15.4,
                "FRAMEWORK DESIGN",
                "One idea. A whole learning portal.",
                "Lessons, videos, podcasts, stories, games and an open world, all fitted to your idea.",
            )
        ],
    )
    c = lambda name, tag="h3": cam.find(name, tag, card=True)  # noqa: E731

    def column(names):
        rs = [c(n) for n in names]
        x0 = min(r[0] for r in rs)
        y0 = min(r[1] for r in rs)
        x1 = max(r[0] + r[2] for r in rs)
        y1 = max(r[1] + r[3] for r in rs)
        return (x0, y0, x1 - x0, y1 - y0)

    def focus(beat, rect, z, dim=0.72, sy=670):
        cx = rect[0] + rect[2] / 2
        cy = rect[1] + rect[3] / 2 - (sy - H / 2) / z
        return (beat, cx, cy, z, rect, dim)

    left = column(["Module overview", "Lesson sequence", "Reinforcement assets"])
    right = column(["Scenario setup", "Decision path", "Debrief"])
    struct = PageScene(
        cam,
        B_STRUCT,
        [
            (0, 960, 1290, 0.95, None, 0.0),
            focus(1.0, left, 1.3),
            focus(6.0, right, 1.3),
        ],
        [
            (0.4, 5.6, "COURSE BLUEPRINT STRUCTURE", "Every module, the same shape",
             "A consistent format keeps every module easy to follow and easy to scale.", "top"),
            (6.3, 11.6, "SIMULATOR STRUCTURE", "Every run, one milestone",
             "Each simulator run should reinforce a specific milestone.", "top"),
        ],
    )
    return hook, struct


def cta_scene(t: float) -> Image.Image:
    lt = t - bt(B_CTA)
    fr = designed_bg(t)
    paste(fr, logo_mark(92), (W // 2 - 46, 150), alpha=e_out(lt / 0.6))
    lines = ["Ready to design", "your own framework?"]
    for i, s in enumerate(lines):
        lay = text_img(s, "eb", 96, TXT)
        paste(
            fr,
            lay,
            (
                W // 2 - lay.width // 2,
                300 + i * 116 + (1 - e_out((lt - 0.2 - i * 0.14) / 0.6)) * 26,
            ),
            alpha=e_out((lt - 0.2 - i * 0.14) / 0.6),
        )
    sub = text_img(
        "Use the onboarding flow to personalize your next learning track.",
        "qs",
        40,
        MUTED,
    )
    paste(fr, sub, (W // 2 - sub.width // 2, 560), alpha=e_out((lt - 1.0) / 0.6))
    # button: gradient pill, pulses on the music's finale hit
    fin = bt(114.8) - bt(B_CTA)
    pulse = 1 + 0.05 * math.exp(-abs(lt - fin) * 5) if lt >= fin - 0.05 else 1.0
    bw, bh = int(430 * pulse), int(96 * pulse)
    bx, by = W // 2 - bw // 2, 690 - (bh - 96) // 2
    a_b = e_out((lt - 1.4) / 0.6)
    if a_b > 0:
        grad = gradient_fill((bw, bh), ACC_A, ACC_B)
        m = Image.new("L", (bw * 2, bh * 2), 0)
        ImageDraw.Draw(m).rounded_rectangle(
            [0, 0, bw * 2 - 1, bh * 2 - 1], radius=bh, fill=int(255 * a_b)
        )
        m = m.resize((bw, bh), RS.LANCZOS)
        fr.paste(grad, (bx, by), m)
        lab = text_img("Go to onboarding", "b", 38, (255, 255, 255))
        paste(
            fr,
            lab,
            (W // 2 - lab.width // 2, by + (bh - lab.height) // 2 - 2),
            alpha=a_b,
        )
    url = text_img("gameofoptions.netlify.app", "qs", 34, ACC_A)
    paste(fr, url, (W // 2 - url.width // 2, 856), alpha=e_out((lt - 1.9) / 0.6))
    return fr


# ---- top-level frame --------------------------------------------------------
def frame_at(t: float, scenes) -> Image.Image:
    hook, struct = scenes
    t_drop = bt(B_DROP)

    def hook_fn(tt):
        fr = hook.render(tt)
        if tt < 2.4:  # logo card resolves into the real page
            lg = logo_card(tt)
            a = 1.0 if tt < 1.7 else 1 - e_io((tt - 1.7) / 0.7)
            fr = Image.blend(fr, lg, a)
        return fr

    chain = [
        (B_DROP, moves_scene),
        (B_STRUCT, struct.render),
        (B_EXAMPLES, examples_scene),
        (B_PORTAL, portal_scene),
        (B_CTA, cta_scene),
    ]
    if t < t_drop:
        fr = hook_fn(t)
    else:
        idx = max(i for i, (b, _) in enumerate(chain) if t >= bt(b))
        fr = chain[idx][1](t)
        x = t - bt(chain[idx][0])
        if idx > 0 and x < 0.3:  # dip in from the previous scene
            fr = Image.blend(chain[idx - 1][1](t), fr, e_io(x / 0.3))
    # the drop: a brief white flash
    if 0 <= t - t_drop < 0.2:
        fr = Image.blend(fr, Image.new("RGB", (W, H), (255, 255, 255)), 0.55 * (1 - (t - t_drop) / 0.2))
    if t < 0.5:
        fr = Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), fr, e_out(t / 0.5))
    if t > T_END - 1.3:
        fr = Image.blend(fr, Image.new("RGB", (W, H), (0, 0, 0)), e_in((t - (T_END - 1.3)) / 1.3))
    return fr


# ---- score + mix -------------------------------------------------------------
def voice_script():
    """The narration: (text, speed, start seconds). Every phrase is the page's own
    copy, placed on the on-screen text and kept out of the dense passages."""
    cl, c0 = bt(B_PORTAL + 23), bt(B_CTA)
    return [
        ("One idea.", 0.92, 2.85),
        ("A whole learning portal.", 0.92, 4.1),
        ("Lessons, videos, podcasts, stories, games, and an open world.", 1.0, bt(B_PORTAL) + 0.2),
        ("One idea.", 0.92, cl + 0.05),
        ("A full learning portal.", 0.92, cl + 1.05),
        ("For you only.", 0.9, cl + 2.45),
        ("Ready to design your own framework?", 0.95, c0 + 0.65),
    ]


def build_score() -> Path:
    sys.path.insert(0, str(HERE))
    import framework_score
    import framework_voice

    path = WORK / "score.wav"
    ev = dict(
        drop=B_DROP,
        moves=B_MOVES,
        struct=B_STRUCT,
        examples=B_EXAMPLES,
        portal=B_PORTAL,
        cta=B_CTA,
        end=B_END,
        finale=114.8,
    )
    script = voice_script()
    clips = framework_voice.render_lines([(t, sp) for t, sp, _ in script], WORK / "vo")
    voice = [(at, y) for (_, _, at), y in zip(script, clips)]
    for (text, _, at), (_, y) in zip(script, voice):
        print(f"  vo {at:6.2f}-{at + len(y) / 48000 - 0.9:6.2f}s  {text}", flush=True)
    framework_score.build_score(BPM, T_END, ev, path, voice=voice)
    return path


def _measure_lufs(path: Path) -> float:
    r = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af",
         "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
        capture_output=True, text=True, check=True,
    )
    blob = re.search(r"\{[^{}]*\}", r.stderr, re.S).group(0)
    return float(json.loads(blob)["input_i"])


def mix_and_mux(video: Path, score: Path, out: Path, target_lufs: float = -16.0) -> None:
    """Inputs: 0 = silent video (copied, never re-encoded), 1 = the score.
    Loudness is a single static gain to the target, then a ceiling limiter:
    an adaptive loudnorm would flatten the dynamics the score is built on."""
    gain = target_lufs - _measure_lufs(score)
    fc = (
        f"[1:a]atrim=0:{T_END:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.25,"
        f"afade=t=out:st={T_END - 2.6:.3f}:d=2.6,volume={gain:.2f}dB,"
        "alimiter=limit=0.78:attack=3:release=60:level=0,aresample=48000[a]"
    )
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-i", str(video),
            "-i", str(score),
            "-filter_complex", fc,
            "-map", "0:v", "-map", "[a]",
            "-c:v", "copy", "-c:a", "aac_at", "-b:a", "224k",
            "-t", f"{T_END:.3f}",
            "-movflags", "+faststart",
            str(out),
        ],
        check=True,
    )
    print(f"static gain {gain:+.2f} dB to reach {target_lufs} LUFS", flush=True)


def render_video(scenes, out: Path) -> None:
    n = int(round(T_END * FPS))
    enc = subprocess.Popen(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-s",
            f"{W}x{H}",
            "-r",
            str(FPS),
            "-i",
            "-",
            "-c:v",
            "libx264",
            "-preset",
            "slow",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-profile:v",
            "high",
            "-movflags",
            "+faststart",
            str(out),
        ],
        stdin=subprocess.PIPE,
    )
    for i in range(n):
        enc.stdin.write(frame_at(i / FPS, scenes).tobytes())
        if i % 150 == 0:
            print(f"  frame {i}/{n}", flush=True)
    enc.stdin.close()
    enc.wait()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--stills", help="comma-separated times (s): write QA frames and stop"
    )
    ap.add_argument(
        "--no-render", action="store_true", help="reuse work/video_only.mp4"
    )
    args = ap.parse_args()

    ensure_fonts()
    WORK.mkdir(parents=True, exist_ok=True)
    if not (WORK / "page.png").is_file():
        raise SystemExit("run capture_framework_design.py first")
    cam = PageCam()
    scenes = build_scenes(cam)

    if args.stills:
        d = WORK / "stills"
        d.mkdir(exist_ok=True)
        poster_frame().save(d / "poster.png")
        for s in args.stills.split(","):
            t = float(s)
            frame_at(t, scenes).save(d / f"t{t:06.2f}.png")
            print("still", t, flush=True)
        return 0

    video_only = WORK / "video_only.mp4"
    if not args.no_render:
        print(f"rendering {T_END:.2f}s @ {FPS}fps ...", flush=True)
        render_video(scenes, video_only)
    score = build_score()
    final = OUT_DIR / "framework-demo.mp4"
    mix_and_mux(video_only, score, final)
    poster = OUT_DIR / "framework-demo.jpg"
    poster_frame().save(poster, quality=90)
    print(f"final={final}  poster={poster}  ({T_END:.1f}s)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
