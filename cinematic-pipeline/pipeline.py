#!/usr/bin/env python3
"""
Cinematic pipeline orchestrator.

    project.json  ──►  keyframes ──►  generate (LTX-2) ──►  edit+grade ──►  final.mp4
                                                    audio (Piper + music) ┘

Runs the best quality the host machine allows (see config.detect_device).
GPU-free stages (keyframes/placeholder, edit, audio) work anywhere; the
`generate` stage needs a GPU (CUDA) or Apple Silicon (MPS) to run LTX-2.

Usage:
    python pipeline.py projects/example/project.json
    python pipeline.py projects/example/project.json --stage edit   # re-edit only
    python pipeline.py projects/example/project.json --dry-run       # print plan, no render
    python pipeline.py --probe                                       # show detected hardware
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import config as cfg                       # noqa: E402
from stages import generate, edit, audio, keyframes  # noqa: E402

STAGES = ["keyframes", "generate", "audio", "edit"]


def run(project_path: Path, only: str | None, dry_run: bool, tier_override: str | None):
    project = cfg.load_project(project_path)
    proj_dir = project_path.parent
    work = proj_dir / "work"
    work.mkdir(exist_ok=True)
    out_dir = proj_dir / "output"
    out_dir.mkdir(exist_ok=True)

    dev = cfg.detect_device()
    tier = cfg.select_tier(dev, prefer=tier_override or project.get("tier"))
    print(f"== {project.get('project', project_path.stem)} ==")
    print(f"Device {dev.kind.upper()} {dev.name} | {dev.vram_gb}GB | tier={tier['name']}")
    print(f"Shots: {len(project['shots'])}  fps={project.get('fps')}  "
          f"res={project['resolution']['width']}x{project['resolution']['height']}")

    stages = [only] if only else STAGES

    # 1. keyframes
    if "keyframes" in stages:
        kp = project.get("keyframe_provider", "placeholder")
        print(f"\n[1/4] keyframes  (provider={kp})")
        # Placeholder keyframes are blank gradient cards — useless as i2v
        # conditioning, and feeding them via --input_media_path trips an
        # assertion at full-noise timestep. Only real keyframes (flux/stock)
        # are attached for image-to-video; placeholder => pure text-to-video.
        if kp == "placeholder":
            print("  (placeholder provider: running text-to-video, no conditioning)")
        elif kp == "sdxl":
            # character-consistent keyframes: one SDXL load, all shots, fixed
            # character clause + base seed so the same person appears throughout.
            char = project.get("character", "")
            kf_res = project.get("keyframe_resolution", {"width": 1024, "height": 576})
            existing = {s["id"]: work / f"kf_{s['id']}.png" for s in project["shots"]}
            if all(p.exists() for p in existing.values()):
                print("  (reusing existing keyframes on disk)")
                for shot in project["shots"]:
                    shot["keyframe"] = str(existing[shot["id"]].relative_to(proj_dir))
            elif not dry_run:
                from stages import sdxl_keyframes
                made = sdxl_keyframes.generate(
                    char, project["shots"], work,
                    kf_res["width"], kf_res["height"],
                    base_seed=project.get("keyframe_base_seed", 1000),
                    ip_scale=project.get("ip_adapter_scale", 0.6),
                    hero_prompt=project.get("hero_prompt"))
                for shot in project["shots"]:
                    shot["keyframe"] = str((made[shot["id"]]).relative_to(proj_dir))
                sdxl_keyframes.release()   # free ~12GB before LTX generation
            else:
                for shot in project["shots"]:
                    shot["keyframe"] = str((work / f"kf_{shot['id']}.png").relative_to(proj_dir))
        else:
            for shot in project["shots"]:
                if shot.get("keyframe") is None and project.get("auto_keyframes"):
                    kf = work / f"kf_{shot['id']}.png"
                    if not dry_run:
                        keyframes.make_keyframe(shot, project, kf, kp)
                    shot["keyframe"] = str(kf.relative_to(proj_dir))

    # 2. generate shots — LTX i2v/t2v, or depth-parallax camera motion on the still
    motion = project.get("motion", "ltx")
    clips: list[Path] = []
    if "generate" in stages:
        print(f"\n[2/4] generate  ({len(project['shots'])} shots, motion={motion})")
        for shot in project["shots"]:
            if motion == "parallax":
                from stages import parallax
                fps = int(project.get("fps", 24))
                nframes = int(round(shot.get("duration", 5) * fps))
                kf = Path(shot["keyframe"])
                kf = kf if kf.is_absolute() else proj_dir / kf
                out = work / f"shot_{shot['id']}.mp4"
                print(f"  [{shot['id']}] parallax {nframes}f @ {fps}fps")
                if not dry_run:
                    parallax.animate(kf, out, nframes, fps,
                                     parallax_px=project.get("parallax_px", 22.0),
                                     zoom=project.get("parallax_zoom", 0.10))
                clips.append(out)
            else:
                clips.append(generate.generate_shot(shot, project, tier, work, dev, dry_run))
    else:
        clips = sorted(work.glob("shot_*.mp4"))

    # 3. audio bed
    bed = None
    if "audio" in stages and not dry_run:
        print("\n[3/4] audio")
        if not clips:
            clips = sorted(work.glob("shot_*.mp4"))
        xf = project.get("look", {}).get("transition_sec", 0.5)
        # use ACTUAL rendered clip lengths (frame-capping can shorten them)
        total = sum(edit._probe_duration(c) for c in clips) - xf * (len(clips) - 1)
        narration = None
        narr_text = project.get("narration")
        if narr_text:
            voice = Path(project.get("voice_model", "")).expanduser()
            narration = audio.narrate(narr_text, voice, work / "narration.wav")
        bed = audio.build_bed(project, total, work, narration)

    # 4. edit + grade + mux
    if "edit" in stages and not dry_run:
        print("\n[4/4] edit + grade")
        if not clips:
            print("  no shot clips found in work/ — run the generate stage first.")
            return
        srt = proj_dir / project["subtitles"] if project.get("subtitles") else None
        final = out_dir / f"{project.get('project', 'film')}_final.mp4"
        if bed is None and (work / "bed.wav").exists():
            bed = work / "bed.wav"   # reuse audio from a prior run on --stage edit
        edit.assemble(clips, project, final, audio=bed, subtitles=srt)
        print(f"\n✅ {final}")
    elif dry_run:
        print("\n(dry-run: no files rendered)")


def main():
    ap = argparse.ArgumentParser(description="Cinematic LTX-2 pipeline")
    ap.add_argument("project", nargs="?", help="path to project.json")
    ap.add_argument("--stage", choices=STAGES, help="run a single stage")
    ap.add_argument("--tier", help="force a model tier (see config.TIERS)")
    ap.add_argument("--dry-run", action="store_true", help="print plan without rendering")
    ap.add_argument("--probe", action="store_true", help="show detected hardware and exit")
    args = ap.parse_args()

    if args.probe:
        import subprocess
        subprocess.run([sys.executable, str(HERE / "config.py")])
        return
    if not args.project:
        ap.error("project.json path required (or use --probe)")
    run(Path(args.project).resolve(), args.stage, args.dry_run, args.tier)


if __name__ == "__main__":
    main()
