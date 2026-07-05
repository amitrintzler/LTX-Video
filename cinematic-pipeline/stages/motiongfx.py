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


# Persistent "market newsroom" backdrop data (dimmed, always animating behind scenes)
TAPE = [("AAPL", 189.2, 0.8), ("TSLA", 244.1, -1.2), ("NVDA", 121.6, 2.4),
        ("SPY", 556.3, 0.3), ("MSFT", 428.7, 0.6), ("AMD", 158.2, -1.1),
        ("META", 512.9, 1.8), ("QQQ", 487.4, 0.4), ("AMZN", 186.3, 0.9),
        ("GOOG", 167.5, -0.5), ("BTC", 63120, 1.4), ("VIX", 14.6, -3.1)]
HEADLINES = ["Fed holds rates steady", "Tech rally lifts major indexes",
             "Volatility spikes ahead of earnings", "Options volume hits record high",
             "Oil edges higher on supply data", "Chipmakers lead pre-market gains"]
INDEX = [("DOW", 39412, 0.61), ("S&P 500", 5563, 0.34), ("NASDAQ", 18247, 0.92)]
PRIMARY = (79, 70, 229)          # OptionsEducator brand indigo (hsl 243 75% 59%)
PRIMARY_GLOW = (199, 194, 255)


def _draw_logo(d, x, y, s, alpha=255):
    """OptionsEducator mark: indigo rounded square + white staircase to apex node."""
    u = s / 40.0
    d.rounded_rectangle([x, y, x + s, y + s], radius=int(10 * u), fill=PRIMARY + (alpha,))
    pts = [(x + px * u, y + py * u) for px, py in
           [(7, 33), (7, 21), (20, 21), (20, 13), (33, 13), (33, 7)]]
    d.line(pts, fill=(255, 255, 255, alpha), width=max(2, int(2.6 * u)), joint="curve")
    r = max(2, int(3.6 * u))
    d.ellipse([x + 33 * u - r, y + 7 * u - r, x + 33 * u + r, y + 7 * u + r],
              fill=(255, 255, 255, alpha))
    r2 = max(1, int(2.2 * u))
    d.ellipse([x + 7 * u - r2, y + 33 * u - r2, x + 7 * u + r2, y + 33 * u + r2],
              fill=(255, 255, 255, int(alpha * 0.5)))

_GRAD_CACHE = None


def _grad_bg():
    global _GRAD_CACHE
    if _GRAD_CACHE is None:
        img = Image.new("RGB", (W, H))
        px = img.load()
        for y in range(H):
            f = y / (H - 1)
            c = tuple(int(BG_TOP[i] + (BG_BOT[i] - BG_TOP[i]) * f) for i in range(3))
            for x in range(W):
                px[x, y] = c
        _GRAD_CACHE = img
    return _GRAD_CACHE.copy()


def _ctext(d, text, fnt, y, fill=WHITE, alpha=255):
    bb = d.textbbox((0, 0), text, font=fnt)
    x = (W - (bb[2] - bb[0])) // 2
    if alpha >= 255:
        d.text((x, y), text, font=fnt, fill=fill)
    else:
        d.text((x, y), text, font=fnt, fill=fill + (alpha,))
    return x


def _tape_items():
    return [f"{s}  {p:.1f}  {'+' if c >= 0 else ''}{c:.1f}%" for s, p, c in TAPE]


def _tape_width(d, fnt):
    w = 0
    for it in _tape_items():
        w += d.textbbox((0, 0), it + "      ", font=fnt)[2]
    return max(1, w)


def _draw_tape(d, fnt, x, y):
    for (s, p, c), it in zip(TAPE, _tape_items()):
        col = (UP if c >= 0 else DOWN) + (215,)
        d.text((x, y), it, font=fnt, fill=col)
        x += d.textbbox((0, 0), it + "      ", font=fnt)[2]


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

    def _bg(self):
        """Persistent animated market-newsroom backdrop (keyed to the global frame
        so ticker/news/charts scroll continuously under every scene), dimmed with a
        scrim so foreground content stays readable."""
        f = self.n
        base = _grad_bg().convert("RGBA")
        d = ImageDraw.Draw(base, "RGBA")
        # faint moving line charts behind everything
        for ci, (oy, col, spd, amp) in enumerate(
                [(H * 0.34, INDIGO, 0.9, 42), (H * 0.56, UP, 1.4, 28), (H * 0.46, DOWN, 1.1, 34)]):
            pts = [(x, oy + amp * math.sin(x * 0.012 + f * 0.05 * spd + ci * 2)) for x in range(0, W + 8, 10)]
            d.line(pts, fill=col + (34,), width=2)
        # scrim to mute the backdrop so scene content pops
        d.rectangle([0, 0, W, H], fill=(6, 7, 18, 108))

        # ================= TOP BROADCAST BAR (big) =================
        # breaking-news strip + scrolling headline crawl
        d.rectangle([0, 0, W, 44], fill=(70, 14, 20, 205))
        d.rectangle([0, 0, 150, 44], fill=(200, 40, 50, 240))
        d.text((16, 10), "BREAKING", font=_font(22), fill=(255, 255, 255, 245))
        fh = _font(22)
        hl = "     •     ".join(HEADLINES) + "     •     "
        hw = d.textbbox((0, 0), hl, font=fh)[2]
        hoff = int((f * 3) % hw)
        for rep in range(2):
            d.text((162 - hoff + rep * hw, 10), hl, font=fh, fill=(245, 232, 232, 215))

        # ---- BIG INDEX BOARD: DOW / S&P / NASDAQ, flashing on update ----
        bx, by0, cw, ch = 20, 56, 300, 62
        fnm = _font(20); fval = _font(30); fpc = _font(20)
        for i, (nm, base_v, pc) in enumerate(INDEX):
            x = bx + i * (cw + 12)
            tick = math.sin(f * 0.10 + i * 1.7)
            pc2 = pc + 0.18 * tick
            val = base_v * (1 + pc2 / 100 * 0.02 * math.sin(f * 0.2 + i))
            col = UP if pc2 >= 0 else DOWN
            flash = max(0, math.sin(f * 0.25 + i * 2.1))     # periodic update flash
            cell_bg = (28 + int(30 * flash), 32 + int(20 * flash), 60, 210)
            d.rounded_rectangle([x, by0, x + cw, by0 + ch], radius=10, fill=cell_bg)
            d.text((x + 14, by0 + 8), nm, font=fnm, fill=(200, 205, 235, 235))
            d.text((x + 14, by0 + 28), f"{val:,.0f}", font=fval, fill=(255, 255, 255, 245))
            arw = "▲" if pc2 >= 0 else "▼"
            d.text((x + cw - 120, by0 + 28), f"{arw} {abs(pc2):.2f}%", font=fpc, fill=col + (245,))

        # ---- MARKET CLOCK (big) + LIVE ----
        secs = 34200 + int(f / FPS)      # ticks up from 09:30:00 ET
        hh, mm, ss = secs // 3600 % 24, secs // 60 % 60, secs % 60
        fclk = _font(40)
        clk = f"{hh:02d}:{mm:02d}:{ss:02d}"
        cw2 = d.textbbox((0, 0), clk, font=fclk)[2]
        d.text((W - cw2 - 96, 54), clk, font=fclk, fill=(255, 255, 255, 240))
        d.text((W - 78, 66), "ET", font=_font(22), fill=(180, 186, 220, 220))
        blink = 240 if (f // 12) % 2 == 0 else 80
        d.ellipse([W - cw2 - 128, 62, W - cw2 - 110, 80], fill=(240, 60, 60, blink))
        d.text((W - cw2 - 104, 92), "LIVE  ·  NYSE", font=_font(18), fill=(210, 214, 235, 200))

        # ================= BOTTOM TICKER CRAWL (tall) =================
        by = H - 58
        d.rectangle([0, by, W, H], fill=(12, 14, 34, 230))
        d.line([(0, by), (W, by)], fill=ACCENT + (140,), width=3)
        ft = _font(26)
        toff = int((f * 4) % _tape_width(d, ft))
        _draw_tape(d, ft, -toff, by + 14)
        _draw_tape(d, ft, -toff + _tape_width(d, ft), by + 14)

        # ================= LOGO BUG (bottom-right, above ticker) =================
        lg = 58
        lx, ly = W - 360, by - lg - 18
        d.rounded_rectangle([lx - 14, ly - 10, W - 20, ly + lg + 10], radius=12,
                            fill=(10, 12, 30, 205))
        _draw_logo(d, lx, ly, lg, alpha=245)
        d.text((lx + lg + 14, ly + 6), "OPTIONS EDUCATOR", font=_font(24),
               fill=(255, 255, 255, 240))
        d.text((lx + lg + 14, ly + 34), "OPTIONS DESK  ·  LIVE", font=_font(17),
               fill=ACCENT + (220,))
        return base.convert("RGB")

    # ---- scene: kinetic title ----
    def title(self, line1, line2, secs=2.6):
        total = int(secs * FPS)
        f1, f2 = _font(90), _font(34)
        for f in range(total):
            img = self._bg(); d = ImageDraw.Draw(img, "RGBA")
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
        gy0, gy1 = int(H * 0.20), int(H * 0.72)
        fh = _font(40); fs = _font(24)

        def py(v):
            return gy1 - (v - lo_all) / (hi_all - lo_all) * (gy1 - gy0)
        cw = (gx1 - gx0) / n * 0.55
        for f in range(total):
            img = self._bg(); d = ImageDraw.Draw(img, "RGBA")
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
            _ctext(d, "Price Action", fh, int(H * 0.72), WHITE, a)
            self._save(img)

    # ---- scene: call payoff diagram ----
    def payoff(self, secs=4.2):
        total = int(secs * FPS)
        ax0, ax1 = int(W * 0.16), int(W * 0.84)
        ay0, ay1 = int(H * 0.18), int(H * 0.72)
        zero_y = int(ay0 + (ay1 - ay0) * 0.62)
        strike_x = ax0 + (ax1 - ax0) * 0.45
        prem = (ay1 - zero_y) * 0.5
        fh = _font(40); fs = _font(22)
        for f in range(total):
            img = self._bg(); d = ImageDraw.Draw(img, "RGBA")
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
            _ctext(d, "Long Call Payoff", fh, int(H * 0.72), WHITE, a)
            self._save(img)

    # ---- scene: scrolling ticker tape ----
    def ticker(self, secs=3.4):
        total = int(secs * FPS)
        items = [("AAPL", 1.2), ("TSLA", -0.8), ("NVDA", 2.4), ("SPY", 0.3),
                 ("MSFT", 0.6), ("AMD", -1.1), ("META", 1.8), ("QQQ", 0.4),
                 ("AMZN", 0.9), ("GOOG", -0.5)]
        fsym = _font(46); ftitle = _font(40)
        seg = 360
        speed = 170.0
        band_y, bh = int(H * 0.40), 120
        for fr in range(total):
            img = self._bg(); d = ImageDraw.Draw(img, "RGBA")
            a = int(255 * _fade_alpha(fr, total))
            d.rectangle([0, band_y, W, band_y + bh], fill=(20, 24, 52, int(a * 0.85)))
            d.line([(0, band_y), (W, band_y)], fill=ACCENT + (int(a * 0.5),), width=2)
            d.line([(0, band_y + bh), (W, band_y + bh)], fill=ACCENT + (int(a * 0.5),), width=2)
            off = (fr / FPS) * speed
            base = -(off % seg)
            for k in range(0, W // seg + 3):
                sym, pct = items[(int(off // seg) + k) % len(items)]
                x = int(base + k * seg)
                col = UP if pct >= 0 else DOWN
                arrow = "▲" if pct >= 0 else "▼"
                d.text((x, band_y + 24), sym, font=fsym, fill=WHITE + (a,))
                d.text((x, band_y + 68), f"{arrow} {abs(pct):.1f}%", font=_font(34), fill=col + (a,))
            _ctext(d, "The Tape", ftitle, int(H * 0.72), WHITE, a)
            self._save(img)

    # ---- scene: volatility expected-move cone ----
    def vol_cone(self, secs=3.6):
        total = int(secs * FPS)
        x0, x1 = int(W * 0.14), int(W * 0.86)
        midy = int(H * 0.48)
        maxw = int(H * 0.24)
        fh = _font(40); fs = _font(22)
        for fr in range(total):
            img = self._bg(); d = ImageDraw.Draw(img, "RGBA")
            a = int(255 * _fade_alpha(fr, total))
            d.line([(x0, midy), (x1, midy)], fill=(90, 96, 130, a), width=2)
            d.text((x0 - 4, int(H * 0.16)), "price", font=fs, fill=MUTE + (a,))
            d.text((x1 - 40, midy + 8), "time", font=fs, fill=MUTE + (a,))
            p = self._prog(fr, total, 0.3)
            steps = 60
            top_pts, bot_pts = [], []
            for s in range(steps + 1):
                t = s / steps
                if t > p:
                    break
                x = x0 + (x1 - x0) * t
                hw = maxw * math.sqrt(t)
                top_pts.append((x, midy - hw))
                bot_pts.append((x, midy + hw))
            if len(top_pts) > 1:
                poly = top_pts + bot_pts[::-1]
                d.polygon(poly, fill=(INDIGO + (int(a * 0.28),)))
                d.line(top_pts, fill=INDIGO + (a,), width=3)
                d.line(bot_pts, fill=INDIGO + (a,), width=3)
                # drifting expected price line
                cl = [(x0 + (x1 - x0) * (s / steps),
                       midy - maxw * 0.35 * math.sqrt(s / steps))
                      for s in range(len(top_pts))]
                d.line(cl, fill=ACCENT + (a,), width=3)
            _ctext(d, "Volatility", fh, int(H * 0.72), WHITE, a)
            self._save(img)

    # ---- scene: implied-volatility smile ----
    def iv_smile(self, secs=3.4):
        total = int(secs * FPS)
        x0, x1 = int(W * 0.18), int(W * 0.82)
        y0, y1 = int(H * 0.22), int(H * 0.72)
        fh = _font(40); fs = _font(22)
        for fr in range(total):
            img = self._bg(); d = ImageDraw.Draw(img, "RGBA")
            a = int(255 * _fade_alpha(fr, total))
            d.line([(x0, y0), (x0, y1)], fill=(110, 116, 150, a), width=2)
            d.line([(x0, y1), (x1, y1)], fill=(110, 116, 150, a), width=2)
            d.text((x0 - 6, y0 - 26), "IV", font=fs, fill=MUTE + (a,))
            d.text((x1 - 60, y1 + 8), "strike", font=fs, fill=MUTE + (a,))
            p = self._prog(fr, total, 0.6)
            pts = []
            steps = 60
            for s in range(steps + 1):
                t = s / steps
                if t > p:
                    break
                x = x0 + (x1 - x0) * t
                u = (t - 0.5) * 2                      # -1..1
                iv = 0.25 + 0.55 * (u * u)             # smile
                y = y1 - iv * (y1 - y0)
                pts.append((x, y))
            if len(pts) > 1:
                d.line(pts, fill=ACCENT + (a,), width=4)
                d.ellipse([pts[-1][0] - 6, pts[-1][1] - 6, pts[-1][0] + 6, pts[-1][1] + 6],
                          fill=WHITE + (a,))
            # ATM marker
            d.line([((x0 + x1) // 2, y0), ((x0 + x1) // 2, y1)], fill=(INDIGO + (int(a * 0.4),)))
            d.text(((x0 + x1) // 2 - 16, y1 + 8), "ATM", font=fs, fill=INDIGO + (a,))
            _ctext(d, "The Volatility Smile", fh, int(H * 0.72), WHITE, a)
            self._save(img)

    # ---- scene: the Greeks bars ----
    def greeks(self, secs=3.4):
        total = int(secs * FPS)
        rows = [("Delta", 0.55, ACCENT), ("Gamma", 0.30, INDIGO),
                ("Theta", 0.70, DOWN), ("Vega", 0.45, UP)]
        fl = _font(38); fv = _font(34); fh = _font(40)
        bx0 = int(W * 0.30); bx1 = int(W * 0.82)
        for fr in range(total):
            img = self._bg(); d = ImageDraw.Draw(img, "RGBA")
            a = int(255 * _fade_alpha(fr, total))
            p = self._prog(fr, total, 0.55)
            for i, (name, frac, col) in enumerate(rows):
                y = int(H * 0.26) + i * int(H * 0.13)
                d.text((int(W * 0.14), y), name, font=fl, fill=WHITE + (a,))
                d.rounded_rectangle([bx0, y, bx1, y + 34], radius=17,
                                    fill=(40, 44, 74, a))
                w = int((bx1 - bx0) * frac * p)
                d.rounded_rectangle([bx0, y, bx0 + max(34, w), y + 34], radius=17,
                                    fill=col + (a,))
                d.text((bx1 + 16, y), f"{'-' if name=='Theta' else ''}{frac*p:.2f}", font=fv, fill=col + (a,))
            _ctext(d, "The Greeks", fh, int(H * 0.72), WHITE, a)
            self._save(img)

    # ---- scene: long straddle payoff (volatility play) ----
    def straddle(self, secs=3.4):
        total = int(secs * FPS)
        ax0, ax1 = int(W * 0.16), int(W * 0.84)
        ay0, ay1 = int(H * 0.16), int(H * 0.76)
        zero_y = int(ay0 + (ay1 - ay0) * 0.58)
        cx = (ax0 + ax1) // 2
        cost = (ay1 - zero_y) * 0.7
        fh = _font(40); fs = _font(22)
        for fr in range(total):
            img = self._bg(); d = ImageDraw.Draw(img, "RGBA")
            a = int(255 * _fade_alpha(fr, total))
            d.line([(ax0, zero_y), (ax1, zero_y)], fill=(110, 116, 150, a), width=2)
            d.line([(cx, ay0), (cx, ay1)], fill=(INDIGO + (int(a * 0.4),)))
            d.text((cx - 20, ay1 + 6), "Strike", font=fs, fill=INDIGO + (a,))
            p = ease(fr / total)
            reach = (ax1 - cx) * p
            slope = (zero_y - ay0) / (ax1 - cx)
            lx = cx - reach; rx = cx + reach
            ly = (zero_y + cost) - slope * (cx - lx)
            ry = (zero_y + cost) - slope * (rx - cx)
            d.line([(cx, zero_y + cost), (rx, ry)], fill=ACCENT + (a,), width=4)
            d.line([(cx, zero_y + cost), (lx, ly)], fill=ACCENT + (a,), width=4)
            _ctext(d, "Trade Volatility: The Straddle", fh, int(H * 0.72), WHITE, a)
            self._save(img)

    # ---- scene: counting stat ----
    def stat(self, target, suffix, label, secs=2.4):
        total = int(secs * FPS)
        fbig = _font(150); flab = _font(38)
        for f in range(total):
            img = self._bg(); d = ImageDraw.Draw(img, "RGBA")
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
            img = self._bg(); d = ImageDraw.Draw(img, "RGBA")
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
            img = self._bg(); d = ImageDraw.Draw(img, "RGBA")
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

    # ================= foundations, strategies, story/game =================
    @staticmethod
    def _polyline(d, pts, p, color, a, width=4):
        if len(pts) < 2:
            return
        tot = sum(math.dist(pts[i - 1], pts[i]) for i in range(1, len(pts)))
        target = tot * p
        acc, drawn = 0.0, [pts[0]]
        for i in range(1, len(pts)):
            seg = math.dist(pts[i - 1], pts[i])
            if acc + seg <= target:
                drawn.append(pts[i]); acc += seg
            else:
                r = (target - acc) / seg if seg else 1
                drawn.append((pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * r,
                              pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * r))
                break
        if len(drawn) > 1:
            d.line(drawn, fill=color + (a,), width=width)

    @staticmethod
    def _partial(pts, p):
        """Return the polyline points covering fraction p of the total path length."""
        if len(pts) < 2:
            return list(pts)
        tot = sum(math.dist(pts[i - 1], pts[i]) for i in range(1, len(pts)))
        target = tot * max(0.0, min(1.0, p))
        acc, out = 0.0, [pts[0]]
        for i in range(1, len(pts)):
            seg = math.dist(pts[i - 1], pts[i])
            if acc + seg <= target:
                out.append(pts[i]); acc += seg
            else:
                r = (target - acc) / seg if seg else 1
                out.append((pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * r,
                            pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * r))
                break
        return out

    @staticmethod
    def _prog(f, total, hold=0.35):
        """Eased 0..1 that reaches 1 early then HOLDS the finished state."""
        return ease(min(1.0, (f / max(1, total)) / (1 - hold)))

    def payoff_shape(self, title, breaks, secs=1.9, color=ACCENT, hold=0.4):
        """Generic options payoff with axes, zero-line, strike(s) and breakeven(s).
        breaks: [(tx 0..1, profit -1..1), ...]; interior points are strikes."""
        total = int(secs * FPS)
        ax0, ax1 = int(W * 0.18), int(W * 0.82)
        ay0, ay1 = int(H * 0.20), int(H * 0.72)
        zy = int((ay0 + ay1) / 2)
        sc = (ay1 - zy) * 0.9
        pts = [(ax0 + (ax1 - ax0) * tx, zy - prof * sc) for tx, prof in breaks]
        # breakevens: sign changes in profit between consecutive breaks
        bes = []
        for i in range(1, len(breaks)):
            p0, p1 = breaks[i - 1][1], breaks[i][1]
            if (p0 < 0) != (p1 < 0) and p0 != p1:
                r = -p0 / (p1 - p0)
                tx = breaks[i - 1][0] + (breaks[i][0] - breaks[i - 1][0]) * r
                bes.append(ax0 + (ax1 - ax0) * tx)
        fh = _font(38); fs = _font(20)
        for f in range(total):
            img = self._bg(); d = ImageDraw.Draw(img, "RGBA")
            a = int(255 * _fade_alpha(f, total, 4, 5))
            # ---- STATIC scaffold (full alpha from frame 0 so the plot never reads empty) ----
            for gi in range(1, 5):                                                  # faint grid
                gy = ay0 + (ay1 - ay0) * gi / 5
                d.line([(ax0, gy), (ax1, gy)], fill=(60, 64, 96, int(a * 0.5)))
            d.line([(ax0, ay0), (ax0, ay1)], fill=(130, 136, 175, a), width=2)      # P/L axis
            for gx in range(ax0, ax1, 14):                                          # dashed zero
                d.line([(gx, zy), (gx + 7, zy)], fill=(130, 136, 175, int(a * 0.8)), width=2)
            d.text((ax0 - 4, ay0 - 26), "P/L", font=fs, fill=MUTE + (a,))
            d.text((ax1 - 44, zy + 8), "Price", font=fs, fill=MUTE + (a,))
            for (tx, _pr) in breaks[1:-1]:                                          # strikes (static)
                sx = ax0 + (ax1 - ax0) * tx
                for gy in range(ay0, ay1, 12):
                    d.line([(sx, gy), (sx, gy + 6)], fill=INDIGO + (int(a * 0.6),), width=2)
                d.text((sx - 6, ay1 + 4), "K", font=fs, fill=INDIGO + (a,))
            for bx in bes:                                                          # breakeven (static)
                d.ellipse([bx - 6, zy - 6, bx + 6, zy + 6], fill=WHITE + (a,))
                d.text((bx - 12, zy - 32), "BE", font=fs, fill=(210, 214, 235, a))
            # ---- animated P/L line: profit-green above zero, loss-red below ----
            p = self._prog(f, total, 0.6)          # completes early, holds
            drawn = self._partial(pts, p)
            for i in range(1, len(drawn)):
                seg_col = ACCENT if (drawn[i][1] <= zy and drawn[i - 1][1] <= zy) else DOWN
                d.line([drawn[i - 1], drawn[i]], fill=seg_col + (a,), width=5)
            _ctext(d, title, fh, int(H * 0.72), WHITE, a)
            self._save(img)

    def bull_bear(self, secs=1.6):
        total = int(secs * FPS)
        fbig = _font(84); fs = _font(30)
        for f in range(total):
            img = self._bg(); d = ImageDraw.Draw(img, "RGBA")
            a = int(255 * _fade_alpha(f, total, 5, 5))
            p = ease(f / total)
            # bull (left) up-arrow, bear (right) down-arrow
            for side, col, up, lbl in [(-1, UP, True, "BULL"), (1, DOWN, False, "BEAR")]:
                cx = int(W / 2 + side * W * 0.22)
                gp = ease(min(1, (p - (0.0 if side < 0 else 0.15)) / 0.5))
                y0 = int(H * 0.30); y1 = int(H * 0.58)
                if up:
                    tip, base = (cx, y0 + int((1 - gp) * (y1 - y0))), (cx, y1)
                else:
                    tip, base = (cx, y1 - int((1 - gp) * (y1 - y0))), (cx, y0)
                d.line([base, tip], fill=col + (a,), width=10)
                aw = 26
                dy = -aw if up else aw
                d.line([tip, (tip[0] - aw, tip[1] - dy)], fill=col + (a,), width=10)
                d.line([tip, (tip[0] + aw, tip[1] - dy)], fill=col + (a,), width=10)
                _ctext_side = cx - d.textbbox((0, 0), lbl, font=fbig)[2] // 2
                d.text((_ctext_side, int(H * 0.62)), lbl, font=fbig, fill=col + (a,))
            _ctext(d, "Bulls vs Bears", fs, int(H * 0.72), MUTE, a)
            self._save(img)

    def supply_demand(self, secs=1.8):
        total = int(secs * FPS)
        x0, x1 = int(W * 0.20), int(W * 0.80)
        y0, y1 = int(H * 0.22), int(H * 0.70)
        fh = _font(36); fs = _font(24)
        for f in range(total):
            img = self._bg(); d = ImageDraw.Draw(img, "RGBA")
            a = int(255 * _fade_alpha(f, total, 4, 5))
            d.line([(x0, y0), (x0, y1)], fill=(110, 116, 150, a), width=2)
            d.line([(x0, y1), (x1, y1)], fill=(110, 116, 150, a), width=2)
            p = ease(f / total)
            self._polyline(d, [(x0, y1), (x1, y0)], p, UP, a, 4)          # supply up
            self._polyline(d, [(x0, y0), (x1, y1)], p, DOWN, a, 4)        # demand down
            if p > 0.85:
                d.ellipse([(x0 + x1) // 2 - 8, (y0 + y1) // 2 - 8,
                           (x0 + x1) // 2 + 8, (y0 + y1) // 2 + 8], fill=ACCENT + (a,))
            d.text((x1 - 90, y0 - 6), "Supply", font=fs, fill=UP + (a,))
            d.text((x1 - 90, y1 - 40), "Demand", font=fs, fill=DOWN + (a,))
            _ctext(d, "Supply & Demand", fh, int(H * 0.72), WHITE, a)
            self._save(img)

    def pie_stock(self, secs=1.8):
        total = int(secs * FPS)
        fh = _font(36)
        cx, cy, r = W // 2, int(H * 0.42), int(H * 0.20)
        for f in range(total):
            img = self._bg(); d = ImageDraw.Draw(img, "RGBA")
            a = int(255 * _fade_alpha(f, total, 4, 5))
            p = ease(f / total)
            sweep = 360 * p
            cols = [(70, 74, 120), (90, 94, 150), (60, 64, 110), (80, 84, 140)]
            start = -90
            for i in range(4):
                seg = min(90, max(0, sweep - i * 90))
                if seg <= 0:
                    break
                d.pieslice([cx - r, cy - r, cx + r, cy + r], start, start + seg,
                           fill=cols[i] + (a,))
                start += 90
            # highlight "your share" wedge pulled out
            if p > 0.7:
                off = int(18 * ease((p - 0.7) / 0.3))
                d.pieslice([cx - r - off, cy - r - off, cx + r - off, cy + r - off],
                           -90, 0, fill=ACCENT + (a,))
            _ctext(d, "Stocks 101", fh, int(H * 0.72), WHITE, a)
            self._save(img)

    def level_up(self, level, secs=1.6):
        total = int(secs * FPS)
        fh = _font(40); fl = _font(64)
        bx0, bx1 = int(W * 0.22), int(W * 0.78)
        by = int(H * 0.52)
        for f in range(total):
            img = self._bg(); d = ImageDraw.Draw(img, "RGBA")
            a = int(255 * _fade_alpha(f, total, 4, 5))
            p = ease(f / total)
            d.rounded_rectangle([bx0, by, bx1, by + 40], radius=20, fill=(40, 44, 74, a))
            d.rounded_rectangle([bx0, by, bx0 + int((bx1 - bx0) * p), by + 40],
                                radius=20, fill=ACCENT + (a,))
            _ctext(d, f"LEVEL {level}", fl, int(H * 0.30), WHITE, a)
            if p > 0.9:
                _ctext(d, "UNLOCKED", fh, int(H * 0.66),
                       ACCENT, int(a * ease((p - 0.9) / 0.1)))
            self._save(img)

    def quiz(self, question, options, correct, secs=2.0):
        total = int(secs * FPS)
        fq = _font(56); fo = _font(44)
        for f in range(total):
            img = self._bg(); d = ImageDraw.Draw(img, "RGBA")
            a = int(255 * _fade_alpha(f, total, 4, 5))
            p = f / total
            _ctext(d, question, fq, int(H * 0.24), WHITE, a)
            n = len(options)
            bw, bh = int(W * 0.30), int(H * 0.20)
            gap = int(W * 0.06)
            tw = n * bw + (n - 1) * gap
            x = (W - tw) // 2
            y = int(H * 0.46)
            for i, opt in enumerate(options):
                reveal = p > 0.6
                col = ACCENT if (reveal and i == correct) else (44, 48, 78)
                tcol = (10, 20, 14) if (reveal and i == correct) else WHITE
                d.rounded_rectangle([x, y, x + bw, y + bh], radius=18, fill=col + (a,))
                bb = d.textbbox((0, 0), opt, font=fo)
                d.text((x + (bw - (bb[2] - bb[0])) // 2, y + (bh - (bb[3] - bb[1])) // 2 - bb[1]),
                       opt, font=fo, fill=tcol + (a,))
                x += bw + gap
            self._save(img)

    def _caption_png(self, text):
        """Lower-third caption strip (brand-indigo box, white text), above the ticker."""
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img, "RGBA")
        fnt = _font(30)
        bb = d.textbbox((0, 0), text, font=fnt)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        padx, pady = 26, 14
        bw, bhh = tw + 2 * padx, th + 2 * pady
        x0 = (W - bw) // 2
        y0 = H - 150
        d.rounded_rectangle([x0, y0, x0 + bw, y0 + bhh], radius=12, fill=PRIMARY + (215,))
        d.rectangle([x0, y0, x0 + 6, y0 + bhh], fill=ACCENT + (255,))   # accent edge
        d.text((x0 + padx, y0 + pady - bb[1]), text, font=fnt, fill=(255, 255, 255, 255))
        return img

    def burn_captions(self, caps):
        """Composite timed captions onto the rendered frames (no libass needed)."""
        cache = {}
        for s, e, text in caps:
            strip = cache.get(text) or cache.setdefault(text, self._caption_png(text))
            alpha_ch = strip.getchannel("A")
            total = max(1, e - s)
            for fr in range(s, e):
                fp = self.dir / f"{fr:05d}.png"
                if not fp.exists():
                    continue
                base = Image.open(fp).convert("RGBA")
                a = _fade_alpha(fr - s, total, 4, 4)
                if a < 0.999:
                    st = strip.copy()
                    st.putalpha(alpha_ch.point(lambda v: int(v * a)))
                else:
                    st = strip
                base.alpha_composite(st)
                base.convert("RGB").save(fp)

    def write_captions(self, caps, path: Path):
        """Write styled ASS lower-third captions (indigo box, above the ticker).
        caps: [(start_frame, end_frame, text), ...]."""
        def t(fr):
            s = fr / FPS
            return f"{int(s // 3600)}:{int(s // 60) % 60:02d}:{s % 60:05.2f}"
        head = (f"[Script Info]\nScriptType: v4.00+\nPlayResX: {W}\nPlayResY: {H}\n\n"
                "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, "
                "SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, "
                "StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, "
                "Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
                # white text, opaque box = semi-transparent brand indigo, bottom-centre
                "Style: Cap,Helvetica,30,&H00FFFFFF,&H00FFFFFF,&H00E5464F,&H64E5464F,"
                "-1,0,0,0,100,100,0,0,3,1,0,2,140,140,74,1\n\n"
                "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, "
                "MarginV, Effect, Text\n")
        lines = [f"Dialogue: 0,{t(s)},{t(e)},Cap,,0,0,0,,{txt}" for s, e, txt in caps]
        path.write_text(head + "\n".join(lines) + "\n")
        return path

    def encode(self, out_path: Path, audio: Path | None = None,
               subtitles: Path | None = None) -> Path:
        FF = cfg.ffmpeg_bin()
        vf = "vignette=PI/6,noise=alls=6:allf=t"
        if subtitles:
            vf += f",subtitles={subtitles}"
        vf += ",format=yuv420p"
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
