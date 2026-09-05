#!/usr/bin/env python3
"""Parse a trailers/<slug>/upload-kit.md and upload the matching mp4."""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from youtube_upload import upload_video

ROOT = Path(__file__).resolve().parent.parent / "trailers"


def parse_kit(text: str) -> tuple[str, str, list[str]]:
    title = re.search(r"^## Title\n\n(.+)$", text, re.M).group(1).strip()
    desc = (
        re.search(r"^## Description\n\n(.*?)\n\n## Tags", text, re.S | re.M)
        .group(1)
        .strip()
    )
    tags_block = (
        re.search(r"^## Tags\n\n(.*?)\n\n## ", text, re.S | re.M).group(1).strip()
    )
    tags = [t.strip() for t in tags_block.replace("\n", " ").split(",") if t.strip()]
    return title, desc, tags


def main() -> int:
    slug = sys.argv[1]
    kit_path = ROOT / slug / "upload-kit.md"
    text = kit_path.read_text()
    title, desc, tags = parse_kit(text)
    mp4s = list((ROOT / slug).glob("*_trailer.mp4"))
    if not mp4s:
        mp4s = list(
            (Path.home() / "LTX-Renders" / "trailers" / slug).glob("*_trailer.mp4")
        )
    if not mp4s:
        print(f"no mp4 found for slug {slug!r}", file=sys.stderr)
        return 1
    video = mp4s[0]
    upload_video(video, title, desc, tags, playlist="Trailers", privacy="unlisted")
    return 0


if __name__ == "__main__":
    sys.exit(main())
