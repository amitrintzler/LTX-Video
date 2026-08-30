#!/usr/bin/env python3
"""Generate the trailer's bookend hero clips via Google Flow instead of LTX.

The Options Educator trailer opens on city_reveal and closes on pantheon_night.
This regenerates exactly those clips through the Flow browser provider (a real
Veo generation on the user's own signed-in account) and registers each result
in the trailer's clip cache - {id}_payload.json / {id}_result.json in
OUTPUT_DIR - so a plain `--reuse-existing --profile final` reassembly picks
them up with zero changes to the trailer script itself.

Cache honesty: the written payload is byte-for-byte what video_payload() would
produce for the act (that is what the reuse guard compares, key by key), plus
extra `provider`/`flow_prompt` fields the guard ignores. Matching the guard is
the point - it keeps a later plain reassembly from silently re-rendering these
two clips on LTX and throwing the Flow footage away. The extra fields keep the
substitution visible to anyone reading the file.

The previous LTX-backed payload/result files are kept alongside as
{id}_payload.ltx.json / {id}_result.ltx.json, so restoring the all-LTX trailer
is a two-file rename, not a re-render.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))

import media  # noqa: E402
from providers.base import ProviderError  # noqa: E402
from providers.flow_browser import FlowBrowserProvider  # noqa: E402

TRAILER = ROOT / "scripts" / "ltx25_optionseducator_trailer60.py"
HERO_IDS = ("city_reveal", "pantheon_night")


def trailer_module():
    spec = importlib.util.spec_from_file_location("trailer_mod", TRAILER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=",".join(HERO_IDS))
    ap.add_argument("--timeout", type=int, default=900)
    args = ap.parse_args()

    mod = trailer_module()
    out_dir = mod.OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    wanted = {c.strip() for c in args.only.split(",") if c.strip()}
    targets = [a for a in mod.ATMOSPHERE if a["id"] in wanted]
    if not targets:
        print(f"No atmosphere clips match {sorted(wanted)}", file=sys.stderr)
        return 1

    # Mirrors the final-profile args the trailer itself renders with; the
    # payload written below must match video_payload()'s output exactly or
    # the reuse guard regenerates over the Flow clip.
    final_args = argparse.Namespace(resolution="720p", source_seconds=10)
    provider = FlowBrowserProvider(timeout_s=args.timeout)

    def wait(job):
        time.sleep(10)
        print(".", end="", flush=True)

    for act in targets:
        ltx_payload = mod.video_payload(act, final_args)
        # Same prompt LTX rendered with, no-text/continuous-motion suffix
        # included - identical wording is the best shot at a matching look.
        flow_prompt = ltx_payload["prompt"]

        # 10s matches the LTX clips' source_seconds, so every TIMELINE window
        # (deepest reaches 9.8s into the source) still lands inside the clip.
        spec = media.MediaSpec(
            id=act["id"], kind=media.VIDEO, prompt=flow_prompt, seconds=10
        )
        try:
            fetched = provider.generate(spec, out_dir, wait=wait)
        except ProviderError as exc:
            print(f"\n{act['id']}: {exc}", file=sys.stderr)
            return 1

        final = out_dir / f"{act['id']}_flow.mp4"
        shutil.move(str(fetched), final)
        meta_src = fetched.with_suffix(fetched.suffix + ".meta.json")
        if meta_src.exists():
            shutil.move(str(meta_src), final.with_suffix(".mp4.meta.json"))

        for kind in ("payload", "result"):
            live = out_dir / f"{act['id']}_{kind}.json"
            backup = out_dir / f"{act['id']}_{kind}.ltx.json"
            if live.exists() and not backup.exists():
                shutil.copy2(live, backup)

        payload = dict(ltx_payload)
        payload["provider"] = "flow"
        payload["flow_prompt"] = flow_prompt
        (out_dir / f"{act['id']}_payload.json").write_text(
            json.dumps(payload, indent=2) + "\n"
        )
        (out_dir / f"{act['id']}_result.json").write_text(
            json.dumps(
                {
                    "status": "complete",
                    "video_path": str(final),
                    "provider": "flow",
                },
                indent=2,
            )
            + "\n"
        )
        print(f"\n{act['id']}: {final}", flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
