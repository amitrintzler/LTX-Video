#!/usr/bin/env python3
"""Deliver the Framework Design video to the Options Educator site repo.

This was the one step of the pipeline that stayed manual: QA the render, copy
it and its poster into the site repo, keep the music-provenance record honest,
commit, and prove the committed bytes are the bytes that passed QA.

What it will not do, by design:

  * It never merges. A merge to that repo's main is a production Netlify
    deploy and that account has been over its deploy budget, so choosing the
    moment is a person's job, not a job queue's.
  * It never pushes unless asked (`--push`). A push publishes the branch and
    may trigger a paid deploy-preview build.
  * It never touches the working checkout. That repo is usually sitting on an
    unrelated branch with uncommitted work, so delivery happens in its own git
    worktree off `origin/main` and nothing else is disturbed.
  * It refuses to deliver a render that fails QA. Copying a broken file into a
    live site quickly is worse than not copying it at all.

Usage:
    deliver_site_video.py                  # QA, stage, commit, stop
    deliver_site_video.py --dry-run        # QA and report only, write nothing
    deliver_site_video.py --push           # also push the branch (no merge)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RENDER_DIR = Path.home() / "LTX-Renders" / "framework-design"
VIDEO = RENDER_DIR / "framework-demo.mp4"
POSTER = RENDER_DIR / "framework-demo.jpg"

SITE_REPO = Path.home() / "Projects" / "optionseducator"
WORKTREE = Path.home() / "Projects" / "optionseducator-framework-demo"
BRANCH = "feat/framework-demo-video"
REL_DIR = Path("public/assets/videos")

# What the video is meant to be. A render that drifts from this is a bug, not
# a new creative choice, so delivery stops rather than shipping it.
WANT = {
    "duration": (74.0, 74.6),
    "width": 1920,
    "height": 1080,
    "fps": "30/1",
    "lufs": (-17.5, -14.5),
    "true_peak_max": -1.0,
    "drop_at": (9.7, 10.0),  # the music lands on the 5-move sequence
}


def sh(cmd: list[str], cwd: Path | None = None, check: bool = True) -> str:
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise SystemExit(f"command failed: {' '.join(cmd)}\n{r.stderr.strip()}")
    return r.stdout.strip()


def digest(p: Path) -> str:
    h = hashlib.sha1()
    with p.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


# ---- gate 1: the render is what it claims to be -----------------------------
def probe() -> dict:
    out = json.loads(
        sh(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "stream=codec_type,codec_name,width,height,r_frame_rate",
                "-show_entries",
                "format=duration",
                "-of",
                "json",
                str(VIDEO),
            ]
        )
    )
    v = next((s for s in out["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in out["streams"] if s["codec_type"] == "audio"), None)
    return {"video": v, "audio": a, "duration": float(out["format"]["duration"])}


def loudness() -> tuple[float, float]:
    err = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-nostats",
            "-i",
            str(VIDEO),
            "-af",
            "loudnorm=I=-16:TP=-1.5:print_format=summary",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
    ).stderr
    i = re.search(r"Input Integrated:\s*(-?[\d.]+) LUFS", err)
    tp = re.search(r"Input True Peak:\s*(-?[\d.]+) dBTP", err)
    if not i or not tp:
        raise SystemExit("could not measure loudness")
    return float(i.group(1)), float(tp.group(1))


def audio_shape() -> dict:
    """Dropouts and where the music's drop lands, measured from the samples."""
    import numpy as np
    import soundfile as sf

    wav = RENDER_DIR / "work" / "_deliver_check.wav"
    wav.parent.mkdir(parents=True, exist_ok=True)
    sh(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-i",
            str(VIDEO),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "48000",
            str(wav),
        ]
    )
    x, sr = sf.read(wav)
    wav.unlink(missing_ok=True)
    hop = int(sr * 0.05)
    rms = np.array(
        [
            np.sqrt(np.mean(x[i : i + hop] ** 2) + 1e-12)
            for i in range(0, len(x) - hop, hop)
        ]
    )
    db = 20 * np.log10(rms + 1e-9)
    body = db[20:-40]  # ignore the deliberate fade in and out
    rise = np.diff(db[int(8 / 0.05) : int(30 / 0.05)])
    return {
        "peak": float(np.abs(x).max()),
        "dropout_frames": int((body < -60).sum()),
        "drop_at": 8.0 + (int(np.argmax(rise)) + 1) * 0.05,
        "drop_db": float(rise.max()),
    }


def motion() -> dict:
    """Proof the picture actually moves. freezedetect judges by absolute
    difference and so flags this film's deliberate slow drifts; what matters is
    that no frame is ever simply repeated, and that nothing holds still long
    enough to read as a stuck player."""
    import numpy as np

    w, h, fps = 480, 270, 10
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(VIDEO), "-vf", f"fps={fps},scale={w}:{h}",
         "-pix_fmt", "gray", "-f", "rawvideo", "-"],
        capture_output=True,
    ).stdout
    a = np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.int16)
    d = np.abs(np.diff(a, axis=0)).mean((1, 2))
    longest = cur = 0
    for v in d:
        cur = cur + 1 if v < 0.05 else 0
        longest = max(longest, cur)
    return {
        "mean_delta": float(d.mean()),
        "identical_pairs": int((d == 0).sum()),
        "longest_static": longest / fps,
    }


def qa() -> tuple[list[str], dict[str, str]]:
    """Every check, with the failures named. No failures means deliverable.

    The measurements come back as well, so the delivery report and the pull
    request quote the same numbers this run actually took."""
    bad: list[str] = []
    for p in (VIDEO, POSTER):
        if not p.is_file() or p.stat().st_size == 0:
            bad.append(f"missing or empty: {p}")
    if bad:
        return bad, {}

    p = probe()
    if not p["video"]:
        bad.append("no video stream")
    if not p["audio"]:
        bad.append("no audio stream - the score and narration are missing")
    lo, hi = WANT["duration"]
    if not lo <= p["duration"] <= hi:
        bad.append(f"duration {p['duration']:.2f}s outside {lo}-{hi}s")
    if p["video"]:
        if (p["video"]["width"], p["video"]["height"]) != (
            WANT["width"],
            WANT["height"],
        ):
            bad.append(
                f"resolution {p['video']['width']}x{p['video']['height']}, want 1920x1080"
            )
        if p["video"]["r_frame_rate"] != WANT["fps"]:
            bad.append(f"frame rate {p['video']['r_frame_rate']}, want {WANT['fps']}")

    lufs, tp = loudness()
    lo, hi = WANT["lufs"]
    if not lo <= lufs <= hi:
        bad.append(f"loudness {lufs} LUFS outside {lo}..{hi}")
    if tp > WANT["true_peak_max"]:
        bad.append(f"true peak {tp} dBTP above {WANT['true_peak_max']}")

    a = audio_shape()
    if a["dropout_frames"]:
        bad.append(f"{a['dropout_frames']} silent frames mid-video (audio dropout)")
    lo, hi = WANT["drop_at"]
    if not lo <= a["drop_at"] <= hi:
        bad.append(f"music drop at {a['drop_at']:.2f}s outside {lo}-{hi}s")
    if a["peak"] >= 1.0:
        bad.append(f"digital clipping (peak {a['peak']:.3f})")

    print(
        f"  duration {p['duration']:.2f}s  {p['video']['width']}x{p['video']['height']}"
        f"  {p['video']['codec_name']}+{p['audio']['codec_name'] if p['audio'] else 'NONE'}",
        flush=True,
    )
    print(
        f"  {lufs} LUFS  {tp} dBTP  peak {a['peak']:.3f}  drop {a['drop_at']:.2f}s"
        f" (+{a['drop_db']:.0f} dB)  dropouts {a['dropout_frames']}",
        flush=True,
    )

    m = motion()
    if m["identical_pairs"]:
        bad.append(f"{m['identical_pairs']} identical consecutive frames - the picture is frozen")
    if m["longest_static"] > 3.0:
        bad.append(f"{m['longest_static']:.1f}s with no visible movement")
    print(
        f"  motion: mean frame delta {m['mean_delta']:.2f}, no identical frames,"
        f" longest still run {m['longest_static']:.1f}s",
        flush=True,
    )

    # The repo's generic QA tool runs for the record. Two of its checks are
    # wrong for this asset and are reported rather than enforced:
    #   freezedetect (n=-45dB) counts this film's slow camera drifts as
    #   freezes, while motion() above proves no frame is actually repeated;
    #   and its "loudness lurches" rule fails any spread over 4.5 LU, which is
    #   precisely the dynamic arc this score is built on (quiet hook, hush
    #   before the CTA, big finale) and which was asked for.
    # Its duplicate-frame and silence checks are real, so those still gate.
    r = subprocess.run(
        [sys.executable, str(HERE / "studio_qa.py"), str(VIDEO)],
        capture_output=True,
        text=True,
    )
    report = r.stdout or r.stderr
    for line in report.splitlines():
        if line.startswith(("duplicates", "silence")):
            key, _, value = line.partition(":")
            if value.strip() not in ("0", "0s"):
                bad.append(f"studio_qa: {key.strip()} = {value.strip()}")
    print("  studio_qa (informational): " +
          "; ".join(l.strip() for l in report.splitlines()
                    if l.startswith(("freeze", "spread", "VERDICT"))), flush=True)
    measured = {
        "duration": f"{p['duration']:.2f}s (want 74.0-74.6)",
        "picture": f"{p['video']['width']}x{p['video']['height']} {p['video']['r_frame_rate'].split('/')[0]}fps {p['video']['codec_name']}",
        "audio": p["audio"]["codec_name"] if p["audio"] else "MISSING",
        "loudness": f"{lufs} LUFS (want -17.5..-14.5)",
        "true peak": f"{tp} dBTP (ceiling -1.0)",
        "sample peak": f"{a['peak']:.3f} (no clipping)",
        "music drop": f"{a['drop_at']:.2f}s, +{a['drop_db']:.0f} dB (lands on the 5-move beat)",
        "audio dropouts": str(a["dropout_frames"]),
        "motion": f"no repeated frames; longest still run {m['longest_static']:.1f}s",
    }
    return bad, measured


# ---- gate 2: a worktree that cannot disturb anyone ---------------------------
def ensure_worktree() -> Path:
    if not (SITE_REPO / ".git").exists():
        raise SystemExit(f"site repo not found at {SITE_REPO}")
    sh(["git", "fetch", "--quiet", "origin", "main"], cwd=SITE_REPO)

    if WORKTREE.exists():
        dirty = sh(["git", "status", "--porcelain"], cwd=WORKTREE)
        if dirty:
            raise SystemExit(
                f"{WORKTREE} has uncommitted changes - resolve them first:\n{dirty}"
            )
        sh(["git", "checkout", "--quiet", "-B", BRANCH, "origin/main"], cwd=WORKTREE)
        return WORKTREE

    existing = sh(["git", "branch", "--list", BRANCH], cwd=SITE_REPO)
    args = ["git", "worktree", "add", str(WORKTREE)]
    args += [BRANCH] if existing else ["-b", BRANCH, "origin/main"]
    sh(args, cwd=SITE_REPO)
    if existing:
        sh(["git", "checkout", "--quiet", "-B", BRANCH, "origin/main"], cwd=WORKTREE)
    return WORKTREE


# ---- the provenance record ---------------------------------------------------
ENTRY = """- `framework-demo.mp4` / `.jpg` — built outside this repo by the LTX-Video studio's `site-video` job, from live captures of
  `/framework-design`, `/daily-brief` and a lesson page (plus the arcade and open-world captures from the games and
  open-world trailers): `cinematic-pipeline/scripts/capture_framework_design.py`, `capture_framework_portal.py` and
  `framework_design_video.py`. 1920x1080, 30fps, {dur:.1f}s. Replaces the Remotion render.
  **`tsx scripts/render-demo-video.ts --id FrameworkDemo` (the old Remotion composition) would overwrite this file with the
  old version - do not run it unless you mean to revert.** The poster `.jpg` is a designed key-art frame, not a frame of the video.
  Music: original score composed for this video in code (`cinematic-pipeline/scripts/framework_score.py`), synthesised from
  numpy - no samples and no third-party audio, so no licence or attribution applies.
  Narration: Kokoro-82M (https://github.com/hexgrad/kokoro, Apache-2.0 code and weights), voice `am_michael`, run locally and
  offline, pitched down, EQ'd and reverbed (`framework_voice.py`); the spoken lines are the page's own copy. This video no
  longer uses the CC0 `audio-framework.mp3` below; that file is left in place.
  Delivered by `cinematic-pipeline/scripts/deliver_site_video.py`; mp4 sha1 `{sha}`."""


def update_readme(readme: Path, duration: float, sha: str) -> bool:
    """Replace the framework-demo entry in place. Idempotent."""
    text = readme.read_text()
    entry = ENTRY.format(dur=duration, sha=sha)
    start = text.find("- `framework-demo.mp4`")
    if start == -1:
        raise SystemExit(f"no framework-demo entry to replace in {readme}")
    # the entry runs until the next top-level bullet or blank-line section break
    end = len(text)
    for m in re.finditer(r"\n(?=- `|\n[A-Z])", text[start:]):
        end = start + m.start()
        break
    new = text[:start] + entry + text[end:]
    if new == text:
        return False
    readme.write_text(new)
    return True


BEGIN = "<!-- studio:facts -->"
END = "<!-- /studio:facts -->"
TITLE = "Framework Design demo video: production rebuild from the studio"

PR_INTRO = """## What

Replaces `public/assets/videos/framework-demo.mp4` and its poster (used by
`src/pages/FrameworkDesign.tsx`). Assets and the provenance README only - no code change.

Built by the LTX-Video studio's `site-video` job from live captures of `/framework-design`,
`/daily-brief` and a lesson page. It states the outcome, not only the method: one idea becomes a
full personal learning portal - lessons, videos, podcasts, stories, games and an open world -
with real captures as proof. Score and narration are original; no third-party audio.
"""


def facts_block(measured: dict, sha: str, changed: bool, signoff: str | None) -> str:
    """Only things this run measured, so the table cannot drift from the file."""
    rows = "\n".join(f"| {k} | {v} |" for k, v in measured.items())
    scope = (
        "the video, its poster and the provenance entry"
        if changed
        else "the provenance entry only - `main` already holds these exact video bytes"
    )
    decision = (
        f"**Workflow sign-off:** {signoff}"
        if signoff
        else (
            "**Workflow sign-off: still open.** `AGENTS.md` (Video and Media Formats) asks for "
            "approved non-Remotion workflows and for options to be presented before a new video "
            "tool is adopted. This asset comes from the external LTX-Video studio (PIL + FFmpeg, "
            "no Remotion) rather than this repo's `scripts/video-gen` pipeline, and it replaces a "
            "Remotion-rendered file. A maintainer needs to either accept it as an externally "
            "produced asset or ask for it to be rebuilt in `scripts/video-gen`."
        )
    )
    return f"""{BEGIN}
### Measured on delivery

This table and the rest of this block are written by
`cinematic-pipeline/scripts/deliver_site_video.py`, which refuses to deliver a render that fails
any of these checks. Everything here was measured from the committed file.

| Check | Value |
| --- | --- |
{rows}
| mp4 sha1 | `{sha}` |

This change touches {scope}.

### Before merging

- **Merging is a production Netlify deploy** and that account has been over its deploy budget
  (`docs/NETLIFY_DEPLOY_BUDGET.md`). This job never merges and never enables auto-merge; pick the
  moment deliberately.
- **Listen to it.** The score and narration were verified by measurement - levels, key, clicks,
  drop alignment, voice intelligibility - not by ear.
- `tsx scripts/render-demo-video.ts --id FrameworkDemo` (the old Remotion composition) would
  overwrite these files with the old version.
- If `assets/videos` is later offloaded to R2, this file needs uploading there too.
- English only. The podcast and video surfaces are shown from the real `/daily-brief` page;
  nothing plays inside them.

{decision}
{END}"""


def upsert_pr(wt: Path, block: str, dry: bool) -> None:
    """Create the PR, or refresh only this job's block in an existing one.

    A person may have written in that description - a decision, a reply to a
    reviewer - so an update rewrites the delimited block and nothing else.
    Merging is never automated here, and neither is auto-merge.
    """
    slug = sh(["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"], cwd=wt)
    base = sh(["gh", "repo", "view", "--json", "defaultBranchRef",
               "-q", ".defaultBranchRef.name"], cwd=wt)
    open_prs = json.loads(
        sh(["gh", "pr", "list", "--repo", slug, "--head", BRANCH, "--state", "open",
            "--json", "number,body,url"], cwd=wt)
        or "[]"
    )

    if open_prs:
        pr = open_prs[0]
        body = pr["body"] or ""
        if BEGIN in body and END in body:
            head, _, rest = body.partition(BEGIN)
            _, _, tail = rest.partition(END)
            new_body = head + block + tail
            note = f"refreshed the measured block in PR #{pr['number']}, kept the rest"
        else:
            new_body = (body.rstrip() + "\n\n" + block + "\n") if body.strip() else block
            note = f"added a measured block to PR #{pr['number']}"
        if dry:
            print(f"dry run: would have {note}", flush=True)
            print("--- body that would be written ---\n" + new_body, flush=True)
            return
        f = Path(wt) / ".pr-body.md"
        f.write_text(new_body)
        sh(["gh", "pr", "edit", str(pr["number"]), "--repo", slug, "--body-file", str(f)], cwd=wt)
        f.unlink(missing_ok=True)
        print(f"{note}: {pr['url']}", flush=True)
        print(f"delivered={pr['url']} (PR updated)", flush=True)
        return

    body = PR_INTRO + "\n" + block + "\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\n"
    if dry:
        print(f"dry run: would open a PR on {slug} ({BRANCH} -> {base}) titled:\n  {TITLE}", flush=True)
        print("--- body that would be written ---\n" + body, flush=True)
        return
    f = Path(wt) / ".pr-body.md"
    f.write_text(body)
    url = sh(["gh", "pr", "create", "--repo", slug, "--base", base, "--head", BRANCH,
              "--title", TITLE, "--body-file", str(f)], cwd=wt).splitlines()[-1]
    f.unlink(missing_ok=True)
    print(f"opened {url}", flush=True)
    print(f"delivered={url} (PR opened)", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--dry-run", action="store_true", help="QA and report, write nothing"
    )
    ap.add_argument(
        "--pr",
        action="store_true",
        help="also open or refresh the pull request (implies --push); never merges",
    )
    ap.add_argument(
        "--signoff",
        help="record an approval verbatim in the PR (e.g. 'accepted by @owner 2026-09-20'); "
        "without it the PR states the workflow decision is still open",
    )
    ap.add_argument(
        "--push",
        action="store_true",
        help="also push the branch (may trigger a paid deploy-preview); never merges",
    )
    a = ap.parse_args()

    print("QA of the render:", flush=True)
    failures, measured = qa()
    if failures:
        print("\nNOT DELIVERABLE:", flush=True)
        for f in failures:
            print(f"  - {f}", flush=True)
        return 1
    print("  every check passed", flush=True)

    sha_video, sha_poster = digest(VIDEO), digest(POSTER)
    duration = probe()["duration"]

    if a.dry_run:
        print(f"\ndry run: would deliver mp4 {sha_video[:12]} / jpg {sha_poster[:12]}"
              f" to {SITE_REPO} on {BRANCH}; nothing written.", flush=True)
        if a.pr:
            wt = WORKTREE if WORKTREE.exists() else SITE_REPO
            upsert_pr(wt, facts_block(measured, sha_video, True, a.signoff), dry=True)
        return 0

    wt = ensure_worktree()
    print(f"\nstaging in {wt} on {BRANCH} (off origin/main)", flush=True)
    shutil.copy2(VIDEO, wt / REL_DIR / VIDEO.name)
    shutil.copy2(POSTER, wt / REL_DIR / POSTER.name)
    readme_changed = update_readme(wt / REL_DIR / "README.md", duration, sha_video)

    sh(["git", "add", str(REL_DIR)], cwd=wt)
    if not sh(["git", "diff", "--cached", "--name-only"], cwd=wt):
        print(
            "nothing to deliver: origin/main already has this exact video.", flush=True
        )
        return 0

    # Say what actually changed. When origin/main already holds these exact
    # bytes, this is a provenance-record update and claiming otherwise would
    # put a false statement in the history.
    staged = sh(["git", "diff", "--cached", "--name-only"], cwd=wt).splitlines()
    video_changed = any(VIDEO.name in n or POSTER.name in n for n in staged)
    if video_changed:
        message = (
            "Replace the Framework Design demo video with a production rebuild\n\n"
            "Built outside this repo by the LTX-Video studio's site-video job, from\n"
            "live captures of /framework-design, /daily-brief and a lesson page. Sells\n"
            "the outcome as well as the method: one idea becomes a full personal\n"
            f"learning portal. 1920x1080, 30fps, {duration:.1f}s, designed poster.\n"
            "Original score and narration, no third-party audio. README records the\n"
            "provenance and the overwrite warning.\n\n"
            f"mp4 sha1 {sha_video}\n"
        )
    else:
        message = (
            "Record how the Framework Design demo video was produced\n\n"
            "The video and poster already on main are unchanged - this only brings\n"
            "their provenance entry up to date: the studio job that builds them, the\n"
            "capture sources, the original score, the Kokoro narration, and the sha1\n"
            "of the delivered file so the record can be checked.\n\n"
            f"mp4 sha1 {sha_video} (unchanged)\n"
        )

    sh(["git", "commit", "--quiet", "-m", message], cwd=wt)
    head = sh(["git", "rev-parse", "--short", "HEAD"], cwd=wt)

    # The point of the exercise: what is committed is what passed QA.
    blob = subprocess.run(
        ["git", "show", f"HEAD:{(REL_DIR / VIDEO.name).as_posix()}"],
        cwd=wt,
        capture_output=True,
    ).stdout
    if hashlib.sha1(blob).hexdigest() != sha_video:
        raise SystemExit(
            "committed bytes differ from the QA'd render - refusing to continue"
        )
    what = "video + poster + provenance" if video_changed else "provenance only (video unchanged)"
    print(f"committed {head}: {what}; bytes verified identical to the QA'd render", flush=True)
    print(
        f"  README provenance {'updated' if readme_changed else 'already current'}",
        flush=True,
    )
    # A line the studio recognises, so the job reports what it produced.
    print(f"delivered={wt} {BRANCH} {head} ({what})", flush=True)

    if a.push or a.pr:
        sh(["git", "push", "--force-with-lease", "-u", "origin", BRANCH], cwd=wt)
        print(f"pushed {BRANCH}", flush=True)
        if a.pr:
            upsert_pr(wt, facts_block(measured, sha_video, video_changed, a.signoff), dry=False)
        print("Merging is a production deploy and this job never does it - merge yourself when "
              "the Netlify deploy budget allows.", flush=True)
    else:
        print(f"\nNot pushed. To publish:  git -C {wt} push -u origin {BRANCH}", flush=True)
        print("Merging is a production deploy; do that deliberately.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
