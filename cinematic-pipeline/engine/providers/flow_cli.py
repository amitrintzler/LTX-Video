#!/usr/bin/env python3
"""Command-line front door for the Flow provider, so a job runner that only
knows how to launch subprocesses - like this repo's studio - can drive it the
same way it drives every other job, without importing the engine as a library.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import media  # noqa: E402
from providers.base import ProviderError  # noqa: E402
from providers.flow_browser import FlowBrowserProvider  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt")
    ap.add_argument("--kind", choices=media.KINDS, default=media.VIDEO)
    ap.add_argument("--seconds", type=float, default=None)
    ap.add_argument("--out-dir", default=str(Path.home() / "LTX-Renders" / "flow"))
    ap.add_argument("--timeout", type=int, default=600)
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    spec = media.MediaSpec(
        id="flow-clip", kind=args.kind, prompt=args.prompt, seconds=args.seconds
    )
    # Always attaches to the dedicated, user-launched Chrome (flow_login.py) -
    # there's no headless/headed choice to make here anymore, since this
    # never launches a browser of its own. See flow_browser.py's docstring.
    provider = FlowBrowserProvider(timeout_s=args.timeout)

    def wait(job):
        import time

        time.sleep(5)
        print(".", end="", flush=True)

    try:
        path = provider.generate(spec, out_dir, wait=wait)
    except ProviderError as exc:
        print(f"\n{exc}", file=sys.stderr)
        return 1
    print(f"\nfinal={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
