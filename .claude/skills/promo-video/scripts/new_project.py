#!/usr/bin/env python3
"""
Scaffold a new cinematic-pipeline promo project.

    python .claude/skills/promo-video/scripts/new_project.py <slug> [--vertical]

Creates cinematic-pipeline/projects/<slug>/project.json prefilled with the
promo-friendly defaults (parallax motion + SDXL keyframes + per-shot text +
outro CTA card) and a 4-shot Hook->Promise->Proof->Payoff skeleton to edit.
Use --vertical for a 9:16 social cut. See references/project-schema.md.
"""
import argparse
import json
import sys
from pathlib import Path

# repo root = four levels up from this file (.claude/skills/promo-video/scripts/)
ROOT = Path(__file__).resolve().parents[4]
PROJECTS = ROOT / "cinematic-pipeline" / "projects"

BEATS = ["Hook", "Promise", "Proof", "Payoff"]


def skeleton(slug: str, vertical: bool) -> dict:
    res = {"width": 720, "height": 1280} if vertical else {"width": 1280, "height": 720}
    return {
        "project": slug,
        "tier": "2b-distilled",
        "motion": "parallax",
        "fps": 24,
        "resolution": res,
        "keyframe_resolution": res,
        "auto_keyframes": True,
        "keyframe_provider": "sdxl",
        "ip_adapter": False,
        "keyframe_base_seed": 2200,
        "character": "",
        "parallax_px": 24.0,
        "parallax_zoom": 0.12,
        "look": {"letterbox": not vertical, "vignette": True,
                 "grain": 0.035, "transition_sec": 0.5},
        "narration": "TODO: spoken script, benefit-led, ending on the CTA. "
                     "(Audio is WIP — renders muted for now, but keep it here.)",
        "voice_model": "~/piper-voices/en_US-lessac-medium.onnx",
        "audio": {"music": None, "use_shot_audio": False},
        "subtitles": None,
        "outro": {"brand": "TODO Brand", "tagline": "TODO tagline",
                  "cta": "TODO call to action  →", "duration": 3.5},
        "shots": [
            {"id": f"{i+1:02d}",
             "text": f"TODO headline ({beat})",
             "prompt": f"TODO ({beat}): cinematic, photorealistic, depth — one clear subject",
             "duration": 4 if beat in ("Hook", "Payoff") else 5,
             "seed": 3 + i * 7}
            for i, beat in enumerate(BEATS)
        ],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug", help="project slug, e.g. framework_promo")
    ap.add_argument("--vertical", action="store_true", help="9:16 social cut")
    args = ap.parse_args()

    out_dir = PROJECTS / args.slug
    out_file = out_dir / "project.json"
    if out_file.exists():
        print(f"refusing to overwrite existing {out_file}", file=sys.stderr)
        sys.exit(1)
    (out_dir / "assets").mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(skeleton(args.slug, args.vertical), indent=2) + "\n")
    print(f"created {out_file}")
    print("Next: fill narration + shot prompts/text + outro, then:")
    print(f"  python cinematic-pipeline/pipeline.py {out_file.relative_to(ROOT)} --dry-run")


if __name__ == "__main__":
    main()
