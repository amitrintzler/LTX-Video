"""
Motion-graphics promo engine — genuine frame-by-frame animation (no AI stills).

Renders animated scenes to PNG frames, then FFmpeg encodes them:
  - kinetic title reveal
  - candlestick chart forming one candle at a time
  - options call payoff diagram drawing itself
  - a stat number counting up
  - kinetic taglines flying in
  - brand / CTA end card

Everything moves. Local, sharp, fast. Brand colours from Options Educator.
"""
from __future__ import annotations
import math
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config as cfg  # noqa: E402

W, H, FPS = 1280, 720, 24
BG_TOP = (16, 18, 40)
BG_BOT = (8, 9, 22)
WHITE = (245, 247, 255)
MUTE = (150, 158, 190)
ACCENT = (99, 248, 137)     # green
INDIGO = (110, 112, 240)
UP = (86, 220, 130)
DOWN = (224, 74, 90)

FONTS = [
    "/System/Library/Fonts/SFNS.ttf",
    "/System/Library/Fonts/HelveticaNeue.ttc",
    "/System/Library/Fonts/Helvetica.ttc",
    "/Library/Fonts/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def _font(sz):
    for p in FONTS:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, sz)
            except OSError:
                continue
    return ImageFont.load_default()


def ease(t):                       # smoothstep 0..1
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def _bg():
    img = Image.new("RGB", (W, H))
    px = img.load()
    for y in range(H):
        f = y / (H - 1)
        c = tuple(int(BG_TOP[i] + (BG_BOT[i] - BG_TOP[i]) * f) for i in range(3))
        for x in range(W):
            px[x, y] = c
    return img


def _ctext(d, text, fnt, y, fill=WHITE, alpha=255):
    bb = d.textbbox((0, 0), text, font=fnt)
    x = (W - (bb[2] - bb[0])) // 2
    if alpha >= 255:
        d.text((x, y), text, font=fnt, fill=fill)
    else:
        d.text((x, y), text, font=fnt, fill=fill + (alpha,))
    return x


def _fade_alpha(local_f, total, fin=6, fout=6):
    a = 1.0
    if local_f < fin:
        a = local_f / fin
    if local_f > total - fout:
        a = max(0.0, (total - local_f) / fout)
    return ease(a)


class Promo:
    def __init__(self, frames_dir: Path):
        self.dir = frames_dir
        self.dir.mkdir(parents=True, exist_ok=True)
        self.n = 0

    def _save(self, img):
        img.save(self.dir / f"{self.n:05d}.png")
        self.n += 1

    # ---- scene: kinetic title ----
    def title(self, line1, line2, secs=2.6):
        total = int(secs * FPS)
        f1, f2 = _font(90), _font(34)
        for f in range(total):
            img = _bg(); d = ImageDraw.Draw(img, "RGBA")
            p = ease(f / total)
            a = int(255 * _fade_alpha(f, total, 8, 8))
            # accent line grows
            lw = int(W * 0.34 * ease(min(1, f / (total * 0.5))))
            d.rectangle([(W - lw) // 2, int(H * 0.60), (W + lw) // 2, int(H * 0.60) + 4],
                        fill=ACCENT + (a,))
            yoff = int((1 - p) * 30)
            _ctext(d, line1, f1, int(H * 0.36) + yoff, WHITE, a)
            _ctext(d, line2, f2, int(H * 0.66), MUTE, a)
            self._save(img)

    # ---- scene: candlesticks forming ----
    def candles(self, secs=4.2):
        total = int(secs * FPS)
        # generative-ish upward trend candles (deterministic)
        data = []
        price = 40.0
        seq = [3, -1, 4, 2, -2, 5, 3, -1, 6, 4, -2, 5, 7, 4]
        for delta in seq:
            o = price
            c = price + delta
            hi = max(o, c) + 1.5
            lo = min(o, c) - 1.5
            data.append((o, c, hi, lo))
            price = c
        n = len(data)
        lo_all = min(x[3] for x in data); hi_all = max(x[2] for x in data)
        gx0, gx1 = int(W * 0.12), int(W * 0.88)
        gy0, gy1 = int(H * 0.20), int(H * 0.82)
        fh = _font(40); fs = _font(24)

        def py(v):
            return gy1 - (v - lo_all) / (hi_all - lo_all) * (gy1 - gy0)
        cw = (gx1 - gx0) / n * 0.55
        for f in range(total):
            img = _bg(); d = ImageDraw.Draw(img, "RGBA")
            a = int(255 * _fade_alpha(f, total, 6, 8))
            # grid
            for gi in range(5):
                yy = gy0 + (gy1 - gy0) * gi / 4
                d.line([(gx0, yy), (gx1, yy)], fill=(60, 64, 96, int(a * 0.5)))
            d.text((gx0, int(H * 0.11)), "AAPL  ·  live", font=fs, fill=MUTE + (a,))
            reveal = (f / total) * n
            for i, (o, c, hi, lo) in enumerate(data):
                if i > reveal:
                    break
                grow = ease(min(1.0, reveal - i))    # newest candle grows
                cx = gx0 + (gx1 - gx0) * (i + 0.5) / n
                col = (UP if c >= o else DOWN)
                # wick
                d.line([(cx, py(hi)), (cx, py(lo))], fill=col + (a,), width=2)
                yb0, yb1 = py(o), py(c)
                top = min(yb0, yb1); bot = max(yb0, yb1)
                mid = (top + bot) / 2
                hh = (bot - top) / 2 * grow
                d.rectangle([cx - cw / 2, mid - hh, cx + cw / 2, mid + hh],
                            fill=col + (a,))
            _ctext(d, "Read the Charts", fh, int(H * 0.86), WHITE, a)
            self._save(img)

    # ---- scene: call payoff diagram ----
    def payoff(self, secs=4.2):
        total = int(secs * FPS)
        ax0, ax1 = int(W * 0.16), int(W * 0.84)
        ay0, ay1 = int(H * 0.18), int(H * 0.78)
        zero_y = int(ay0 + (ay1 - ay0) * 0.62)
        strike_x = ax0 + (ax1 - ax0) * 0.45
        prem = (ay1 - zero_y) * 0.5
        fh = _font(40); fs = _font(22)
        for f in range(total):
            img = _bg(); d = ImageDraw.Draw(img, "RGBA")
            a = int(255 * _fade_alpha(f, total, 6, 8))
            # axes
            d.line([(ax0, ay0), (ax0, ay1)], fill=(120, 126, 160, a), width=2)
            d.line([(ax0, zero_y), (ax1, zero_y)], fill=(120, 126, 160, a), width=2)
            d.text((ax0 - 6, ay0 - 26), "Profit", font=fs, fill=MUTE + (a,))
            d.text((ax1 - 90, zero_y + 8), "Stock Price", font=fs, fill=MUTE + (a,))
            # payoff line draws left->right
            p = ease(f / total)
            end_x = ax0 + (ax1 - ax0) * p
            # segment 1: flat at -prem until strike
            seg1_end = min(end_x, strike_x)
            d.line([(ax0, zero_y + prem), (seg1_end, zero_y + prem)],
                   fill=ACCENT + (a,), width=4)
            if end_x > strike_x:
                # segment 2: rising 45-ish
                x2 = end_x
                slope = (ay0 - (zero_y + prem)) / (ax1 - strike_x)
                y2 = (zero_y + prem) + slope * (x2 - strike_x)
                d.line([(strike_x, zero_y + prem), (x2, y2)], fill=ACCENT + (a,), width=4)
            # strike + breakeven markers (appear late)
            if p > 0.55:
                ma = int(a * ease((p - 0.55) / 0.45))
                d.line([(strike_x, ay0), (strike_x, ay1)], fill=(INDIGO + (int(ma * 0.6),)))
                d.text((strike_x - 20, ay1 + 6), "Strike", font=fs, fill=INDIGO + (ma,))
                be_x = strike_x + prem / ((ay0 - (zero_y + prem)) / (ax1 - strike_x)) * -1
                be_x = strike_x + prem * (ax1 - strike_x) / (zero_y + prem - ay0) * -1
            _ctext(d, "Long Call Payoff", fh, int(H * 0.85), WHITE, a)
            self._save(img)

    # ---- scene: counting stat ----
    def stat(self, target, suffix, label, secs=2.4):
        total = int(secs * FPS)
        fbig = _font(150); flab = _font(38)
        for f in range(total):
            img = _bg(); d = ImageDraw.Draw(img, "RGBA")
            a = int(255 * _fade_alpha(f, total, 6, 8))
            val = int(round(target * ease(min(1.0, f / (total * 0.7)))))
            _ctext(d, f"{val}{suffix}", fbig, int(H * 0.30), ACCENT, a)
            _ctext(d, label, flab, int(H * 0.62), WHITE, a)
            self._save(img)

    # ---- scene: kinetic taglines ----
    def kinetic(self, words, secs=3.0):
        total = int(secs * FPS)
        fw = _font(96)
        # stagger each word
        for f in range(total):
            img = _bg(); d = ImageDraw.Draw(img, "RGBA")
            ga = _fade_alpha(f, total, 6, 8)
            n = len(words)
            block_h = 120
            y0 = int(H / 2 - n * block_h / 2)
            for i, wtxt in enumerate(words):
                start = 0.10 + i * 0.22
                lp = ease(max(0.0, min(1.0, (f / total - start) / 0.22)))
                a = int(255 * ga * lp)
                dx = int((1 - lp) * 120)
                col = ACCENT if i == n - 1 else WHITE
                bb = d.textbbox((0, 0), wtxt, font=fw)
                x = (W - (bb[2] - bb[0])) // 2 + dx
                d.text((x, y0 + i * block_h), wtxt, font=fw, fill=col + (a,))
            self._save(img)

    # ---- scene: CTA ----
    def cta(self, brand, tagline, cta, secs=2.8):
        total = int(secs * FPS)
        fb = _font(96); ft = _font(36); fc = _font(40)
        for f in range(total):
            img = _bg(); d = ImageDraw.Draw(img, "RGBA")
            a = int(255 * _fade_alpha(f, total, 8, 6))
            p = ease(min(1.0, f / (total * 0.5)))
            _ctext(d, brand, fb, int(H * 0.30) + int((1 - p) * 20), WHITE, a)
            _ctext(d, tagline, ft, int(H * 0.46), MUTE, a)
            # CTA pill pulses
            pulse = 1 + 0.03 * math.sin(f / 4.0)
            bb = d.textbbox((0, 0), cta, font=fc)
            cw, ch = bb[2] - bb[0], bb[3] - bb[1]
            px, py = int(60 * pulse), 26
            x0 = (W - cw) // 2 - px; y0 = int(H * 0.62)
            d.rounded_rectangle([x0, y0, x0 + cw + 2 * px, y0 + ch + 2 * py],
                                radius=40, fill=ACCENT + (a,))
            d.text(((W - cw) // 2, y0 + py - bb[1]), cta, font=fc, fill=(8, 20, 14))
            self._save(img)

    def encode(self, out_path: Path, audio: Path | None = None) -> Path:
        FF = cfg.ffmpeg_bin()
        vf = "vignette=PI/6,noise=alls=6:allf=t,format=yuv420p"
        raw = out_path.parent / "_mg_video.mp4"
        subprocess.run([FF, "-y", "-loglevel", "error", "-framerate", str(FPS),
                        "-i", str(self.dir / "%05d.png"), "-vf", vf,
                        "-c:v", "libx264", "-crf", "16", "-r", str(FPS), str(raw)], check=True)
        if audio and audio.exists():
            subprocess.run([FF, "-y", "-loglevel", "error", "-i", str(raw),
                            "-i", str(audio), "-filter_complex", "[1:a]apad[a]",
                            "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac",
                            "-shortest", str(out_path)], check=True)
        else:
            subprocess.run([FF, "-y", "-loglevel", "error", "-i", str(raw),
                            "-c:v", "copy", str(out_path)], check=True)
        return out_path


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/mg_promo.mp4")
    frames = out.parent / "_mg_frames"
    p = Promo(frames)
    p.title("Options Educator", "options trading, made simple")
    p.candles()
    p.payoff()
    p.stat(12, "+", "proven strategies")
    p.kinetic(["Calls.", "Puts.", "Mastered."])
    p.cta("Options Educator", "Options, finally made clear.", "Start Learning  →")
    print("frames:", p.n)
    p.encode(out)
    print("done ->", out)
