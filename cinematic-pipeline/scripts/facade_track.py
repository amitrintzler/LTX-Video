#!/usr/bin/env python3
"""Track a facade across a shot so a painted panel stays on the building.

Used by ltx25_optionseducator_trailer60.py.

A fixed quad, or a quad scaled by a constant, only survives a camera that
does exactly one thing. These shots dolly in, pull back and pan, so the
panel has to follow the wall itself. Match the wall's patch from the first
frame against every later frame under a scale-plus-shift model and hand
back the quad's position per frame.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np

W, H = 1280, 720
GRID = 56           # template samples per side
HALF = 150.0        # template half-extent in pixels, before clamping to the quad
MIN_SCORE = 0.45    # below this the match is not trusted and the last pose is held
REFRESH = 10        # frames between template refreshes
REFRESH_SCORE = 0.55  # only refresh from a frame that matched well


def read_gray(path: Path) -> np.ndarray:
    """Whole shot as float32 luma, shape (frames, H, W)."""
    proc = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path),
         "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{W}x{H}", "-"],
        capture_output=True, check=True)
    buf = np.frombuffer(proc.stdout, dtype=np.uint8)
    return buf.reshape(-1, H, W).astype(np.float32)


def _sample(frame: np.ndarray, xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
    xi = np.clip(np.rint(xs), 0, frame.shape[1] - 1).astype(np.int32)
    yi = np.clip(np.rint(ys), 0, frame.shape[0] - 1).astype(np.int32)
    return frame[yi, xi]


def _zncc(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """a: (n, k) candidates, b: (k,) template. Returns (n,)."""
    a = a - a.mean(axis=1, keepdims=True)
    b = b - b.mean()
    na = np.sqrt((a * a).sum(axis=1)) + 1e-6
    nb = np.sqrt((b * b).sum()) + 1e-6
    return (a @ b) / (na * nb)


def track_global(frames, ratios=(0.985, 0.99, 0.995, 1.0, 1.005, 1.01, 1.015),
                 shift=6, step=3.0):
    """Estimate the shot's overall camera move: scale and shift, per frame.

    One wall can leave shot, go dark or be swallowed by a foreground building,
    and a patch tracker that loses it has nothing to fall back on but freezing
    — which reads as the panel sticking to the lens. The whole frame never
    disappears, so its motion is the safety net the patch search predicts from.
    """
    h, w = frames[0].shape
    cx, cy = w / 2.0, h / 2.0
    lin = np.linspace(-0.82, 0.82, 40)
    gx, gy = np.meshgrid(lin, lin)
    ux = (cx + gx * cx).ravel()
    uy = (cy + gy * cy).ravel()
    template = _sample(frames[0], ux, uy)

    poses = [(1.0, 0.0, 0.0)]
    offs = np.arange(-shift, shift + 1) * step
    dx, dy = np.meshgrid(offs, offs)
    dx, dy = dx.ravel(), dy.ravel()
    for f in range(1, len(frames)):
        s0, tx0, ty0 = poses[-1]
        if len(poses) >= 2:
            s1, tx1, ty1 = poses[-2]
            s0 *= s0 / s1
            tx0 += tx0 - tx1
            ty0 += ty0 - ty1
        best = (-2.0, poses[-1])
        for r in ratios:
            sc = s0 * r
            xs = cx + (ux - cx) * sc + (tx0 + dx)[:, None]
            ys = cy + (uy - cy) * sc + (ty0 + dy)[:, None]
            val = _zncc(_sample(frames[f], xs, ys), template)
            k = int(np.argmax(val))
            if val[k] > best[0]:
                best = (float(val[k]), (sc, tx0 + float(dx[k]), ty0 + float(dy[k])))
        sc, tx, ty = best[1]
        # a runaway is worse than a stiff estimate: hold the move inside what a
        # four-second shot can physically do
        sc = min(max(sc, 0.45), 2.6)
        tx = min(max(tx, -700.0), 700.0)
        ty = min(max(ty, -420.0), 420.0)
        best = (best[0], (sc, tx, ty))
        poses.append(best[1])
        if f % 8 == 0:
            sc, tx, ty = best[1]
            template = _sample(frames[f], cx + (ux - cx) * sc + tx,
                               cy + (uy - cy) * sc + ty)
    return poses


def track_quad_frames(frames, quad, ratios=(0.982, 0.988, 0.994, 1.0, 1.006, 1.012, 1.018),
                      shift=7, step=2.0, grid=GRID, half=HALF, size=(W, H),
                      prior=None):
    """Follow `quad` (frame-0 coordinates) through `clip`.

    Horizontal and vertical scale move apart when a wall recedes, so they are
    searched separately: a single scale factor loses the lock within a second
    on the faster dollies. Scale is picked on a coarse shift grid, then the
    shift is refined at that scale, which keeps the search affordable.

    Returns a list of quads, one per frame, and the per-frame match score.
    """
    n = len(frames)
    pts = np.array(quad, dtype=np.float64)
    cx, cy = pts[:, 0].mean(), pts[:, 1].mean()

    # The grid spans the quad, padded a little so wall texture around the panel
    # contributes: a flat glass face on its own has too little to lock onto.
    half_x = min(half, max(60.0 * half / HALF, (pts[:, 0].max() - pts[:, 0].min()) * 0.75))
    half_y = min(half, max(60.0 * half / HALF, (pts[:, 1].max() - pts[:, 1].min()) * 0.75))
    lin = np.linspace(-1.0, 1.0, grid)
    gx, gy = np.meshgrid(lin, lin)
    ux = (cx + gx * half_x).ravel()
    uy = (cy + gy * half_y).ravel()
    template = _sample(frames[0], ux, uy)

    if prior is None:
        prior = track_global(frames)
    gcx, gcy = frames[0].shape[1] / 2.0, frames[0].shape[0] / 2.0

    def from_global(f):
        """Where the global camera move alone would put this patch."""
        gs, gtx, gty = prior[f]
        px = gcx + (cx - gcx) * gs + gtx
        py = gcy + (cy - gcy) * gs + gty
        return gs, gs, px - cx, py - cy

    poses = [(1.0, 1.0, 0.0, 0.0)]
    scores = [1.0]
    fine = np.arange(-shift, shift + 1) * step
    fx, fy = np.meshgrid(fine, fine)
    fx, fy = fx.ravel(), fy.ravel()
    coarse = np.array([-2, -1, 0, 1, 2]) * (step * 2)
    ccx, ccy = np.meshgrid(coarse, coarse)
    ccx, ccy = ccx.ravel(), ccy.ravel()

    def score_at(frame, sx, sy, ox, oy, dx, dy):
        xs = cx + (ux - cx) * sx + (ox + dx)[:, None]
        ys = cy + (uy - cy) * sy + (oy + dy)[:, None]
        return _zncc(_sample(frame, xs, ys), template)

    for f in range(1, n):
        # predict from the camera move, not from the patch's own momentum:
        # momentum keeps drifting once the wall is gone, the camera does not
        gsx, gsy, gtx, gty = from_global(f)
        psx, psy, ptx, pty = poses[-1]
        gsx0, gsy0, gtx0, gty0 = from_global(f - 1)
        sx0 = psx * (gsx / gsx0)
        sy0 = psy * (gsy / gsy0)
        tx0 = ptx + (gtx - gtx0)
        ty0 = pty + (gty - gty0)

        best = (-2.0, None)
        for rx in ratios:
            for ry in ratios:
                sc = score_at(frames[f], sx0 * rx, sy0 * ry, tx0, ty0, ccx, ccy)
                k = int(np.argmax(sc))
                if sc[k] > best[0]:
                    best = (float(sc[k]), (sx0 * rx, sy0 * ry,
                                           tx0 + float(ccx[k]), ty0 + float(ccy[k])))
        sx, sy, bx, by = best[1]
        sc = score_at(frames[f], sx, sy, bx, by, fx, fy)
        k = int(np.argmax(sc))
        if float(sc[k]) > best[0]:
            best = (float(sc[k]), (sx, sy, bx + float(fx[k]), by + float(fy[k])))

        if best[0] < MIN_SCORE:
            # the wall is gone or unrecognisable; ride the camera rather than
            # freezing, so the panel leaves shot with the building it sits on
            poses.append((sx0, sy0, tx0, ty0))
            scores.append(best[0])
            continue
        poses.append(best[1])
        scores.append(best[0])

        # A four-second dolly changes the wall's perspective, not just its size,
        # so a frame-0 template slowly stops matching. Re-cut it at intervals,
        # and only from a frame that matched well, so shimmer cannot accumulate.
        if f % REFRESH == 0 and best[0] >= REFRESH_SCORE:
            sx, sy, tx, ty = best[1]
            template = _sample(frames[f],
                               cx + (ux - cx) * sx + tx,
                               cy + (uy - cy) * sy + ty)

    out = []
    for sx, sy, tx, ty in poses:
        out.append([[cx + (x - cx) * sx + tx, cy + (y - cy) * sy + ty] for x, y in quad])
    return out, scores


def track_cached(clip: Path, quad, cache: Path):
    key = {"clip": str(clip), "mtime": int(clip.stat().st_mtime),
           "quad": [list(map(float, p)) for p in quad]}
    if cache.is_file():
        try:
            blob = json.loads(cache.read_text())
            if blob.get("key") == key:
                return blob["quads"], blob["scores"]
        except (ValueError, KeyError):
            pass
    quads, scores = track_quad(clip, quad)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"key": key, "quads": quads, "scores": scores}))
    return quads, scores


def track_quad(clip: Path, quad, **kw):
    return track_quad_frames(read_gray(clip), quad, **kw)
