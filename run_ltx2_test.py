from __future__ import annotations

import argparse
import traceback
from pathlib import Path
from typing import Any, Dict

from log_run import end_run, event, start_run

PROMPT_PRESETS = {
    "sci-fi-plaza": (
        "A dawn drone shot glides over a flooded futuristic plaza, lanterns floating on the water "
        "as commuters move across glass bridges; the camera descends to follow a sleek tram passing "
        "through mist, then arcs upward to reveal a skyline of glowing billboards and distant mountains, "
        "ultra-detailed, soft volumetric light, cinematic"
    ),
    "underwater-library": (
        "A vast underwater library with towering coral bookshelves and glowing jellyfish lamps, a diver "
        "in a brass helmet swims past drifting books while rays of light ripple through the water; the "
        "camera tracks behind the diver, circles to reveal the grand hall, then slowly cranes upward to "
        "show a domed ceiling, high detail, serene, cinematic"
    ),
    "talking-cartoon": (
        "A massive ape-like creature stands in a jungle clearing at dusk, facing the camera and speaking with "
        "clear mouth shapes and expressive eyes; chest-up framing with hands out of frame, realistic lip motion "
        "and facial muscles, wet fur glistens under cinematic rim light, photorealistic skin detail; behind it a "
        "deep jungle with real foliage depth, layered trunks, drifting mist, a distant waterfall, and shafts of light "
        "cutting through haze, wildlife-documentary realism, clean lower third for subtitles"
    ),
    "talking-fox": (
        "A bright, stylized cartoon fox host stands center-frame on a simple studio set, facing the camera "
        "and speaking with clear mouth shapes and expressive eyebrows; the camera is locked-off, the background "
        "is clean and colorful, bold outlines, smooth shading, consistent character design, lively but clean animation"
    ),
}
DEFAULT_PROMPT_KEY = "sci-fi-plaza"
DEFAULT_LTX2_REPO = "Lightricks/LTX-2"
DEFAULT_PIPELINE_CONFIG = "configs/ltxv-2b-0.9.8-distilled.yaml"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run LTX-2 if installed via ltx_pipelines, otherwise run the local "
            "LTX-Video distilled pipeline."
        )
    )
    parser.add_argument("--use-ltx2", action="store_true", help="Force LTX-2 path.")
    parser.add_argument(
        "--ltx2-repo",
        default=DEFAULT_LTX2_REPO,
        help="Hugging Face repo for LTX-2 (used only when ltx_pipelines is installed).",
    )
    parser.add_argument(
        "--prompt",
        default=None,
        help="Text prompt. Overrides --prompt-set if provided.",
    )
    parser.add_argument(
        "--prompt-set",
        default=DEFAULT_PROMPT_KEY,
        choices=["default", "all", *PROMPT_PRESETS.keys()],
        help="Preset prompt set to use when --prompt is not provided.",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs",
        help="Output directory for LTX-Video inference.",
    )
    parser.add_argument(
        "--pipeline-config",
        default=DEFAULT_PIPELINE_CONFIG,
        help="Pipeline config for LTX-Video inference.",
    )
    parser.add_argument("--height", type=int, default=432, help="Frame height.")
    parser.add_argument("--width", type=int, default=768, help="Frame width.")
    parser.add_argument(
        "--num-frames",
        type=int,
        default=65,
        help="Number of frames to generate (will be padded to 8n+1).",
    )
    parser.add_argument("--fps", type=int, default=24, help="Frames per second.")
    parser.add_argument("--seed", type=int, default=171198, help="Random seed.")
    parser.add_argument(
        "--offload-to-cpu",
        action="store_true",
        help="Enable offload to CPU when VRAM is limited.",
    )
    parser.add_argument(
        "--negative-prompt",
        default=(
            "worst quality, inconsistent motion, blurry, jittery, distorted, text, watermark, logo, "
            "icon, UI, subtitles, border, frame, extra fingers, deformed hands, bad anatomy, "
            "cartoon, illustration, painting, flat background, low-poly, plastic"
        ),
        help="Negative prompt for undesired features.",
    )
    return parser


def _device_info() -> Dict[str, Any]:
    import torch

    device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
    return {
        "device": device,
        "torch_version": torch.__version__,
        "mps_available": torch.backends.mps.is_available(),
        "mps_built": torch.backends.mps.is_built(),
        "cuda_available": torch.cuda.is_available(),
    }


def run_ltx2(args: argparse.Namespace, output_tag: str | None = None) -> str:
    from ltx_pipelines import DistilledPipeline

    print("Loading LTX-2 distilled model...")
    pipe = DistilledPipeline.from_pretrained(
        args.ltx2_repo,
        device_map="auto",
        torch_dtype="auto",
    )

    print("Running LTX-2 inference...")
    video = pipe(
        prompt=args.prompt,
        width=args.width,
        height=args.height,
        duration=max(1, int(args.num_frames / max(1, args.fps))),
        fps=args.fps,
        enhance_prompt=True,
    )

    output_file = "ltx2_test_output.mp4"
    if output_tag:
        safe_tag = _sanitize_tag(output_tag)
        if safe_tag:
            output_file = f"ltx2_test_output_{safe_tag}.mp4"
    print(f"Saving to {output_file}...")
    video.save(output_file)
    print("Done!")
    return output_file


def _collect_new_outputs(output_dir: Path, before: set[str]) -> list[str]:
    after = {p.name for p in output_dir.glob("*.*")}
    created = sorted(after - before)
    return [str(output_dir / name) for name in created]


def run_ltx_video(args: argparse.Namespace) -> list[str]:
    from ltx_video.inference import InferenceConfig, infer

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    before = {p.name for p in output_dir.glob("*.*")}

    config = InferenceConfig(
        prompt=args.prompt,
        output_path=str(output_dir),
        pipeline_config=args.pipeline_config,
        seed=args.seed,
        height=args.height,
        width=args.width,
        num_frames=args.num_frames,
        frame_rate=args.fps,
        offload_to_cpu=args.offload_to_cpu,
        negative_prompt=args.negative_prompt,
    )
    print("Running LTX-Video inference (local pipeline)...")
    infer(config)
    return _collect_new_outputs(output_dir, before)


def _resolve_prompts(args: argparse.Namespace) -> list[tuple[str, str]]:
    if args.prompt:
        return [("custom", args.prompt)]

    prompt_set = args.prompt_set
    if prompt_set == "default":
        prompt_set = DEFAULT_PROMPT_KEY

    if prompt_set == "all":
        return list(PROMPT_PRESETS.items())

    return [(prompt_set, PROMPT_PRESETS[prompt_set])]


def _sanitize_tag(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum() or ch in "-_").strip("-_")


def _cleanup_device() -> None:
    import gc

    try:
        import torch
    except Exception:
        return

    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    if torch.backends.mps.is_available() and hasattr(torch.mps, "empty_cache"):
        torch.mps.empty_cache()


def main() -> None:
    args = build_parser().parse_args()
    run = start_run(meta={"args": vars(args)})
    event(run, "device_info", _device_info())

    try:
        prompts = _resolve_prompts(args)
        for prompt_key, prompt_text in prompts:
            args.prompt = prompt_text
            event(run, "prompt_start", {"key": prompt_key, "prompt": prompt_text})
            if args.use_ltx2:
                output_path = run_ltx2(args, output_tag=prompt_key)
                event(run, "outputs", {"paths": [output_path], "mode": "ltx2", "prompt": prompt_key})
            else:
                try:
                    output_path = run_ltx2(args, output_tag=prompt_key)
                    event(run, "outputs", {"paths": [output_path], "mode": "ltx2", "prompt": prompt_key})
                except ModuleNotFoundError:
                    outputs = run_ltx_video(args)
                    event(run, "outputs", {"paths": outputs, "mode": "ltx_video", "prompt": prompt_key})
            event(run, "prompt_end", {"key": prompt_key})
            _cleanup_device()
    except Exception as exc:
        event(run, "error", {"message": str(exc), "trace": traceback.format_exc()})
        raise
    finally:
        end_run(run)


if __name__ == "__main__":
    main()
