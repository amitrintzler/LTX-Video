#!/usr/bin/env python3
"""Hyperframes video generator wrapper - HTML-native video composition."""

import html as html_lib
import os
import re
import shutil
import subprocess
from pathlib import Path
from dataclasses import dataclass

# The CLI and GSAP are pinned by `npm ci` in video-pipeline/hyperframes. Using
# them keeps this wrapper on the same HyperFrames version as the pipeline's
# hyperframes renderer instead of whatever `npx` resolves that day.
PINNED_DIR = Path(__file__).resolve().parents[1] / "video-pipeline" / "hyperframes"
PINNED_CLI = PINNED_DIR / "node_modules" / ".bin" / "hyperframes"
PINNED_GSAP = PINNED_DIR / "node_modules" / "gsap" / "dist" / "gsap.min.js"

_SCENE_ID_RE = re.compile(r"^[A-Za-z][\w-]*$")
ENTRANCE_SEC = 0.6


def _tool_env() -> dict:
    return {**os.environ, "HYPERFRAMES_SKIP_SKILLS": "1", "NO_COLOR": "1"}


def _cli_command() -> list[str]:
    return [str(PINNED_CLI)] if PINNED_CLI.exists() else ["npx", "hyperframes"]


def _fmt(value: float) -> str:
    value = float(value)
    return str(int(value)) if value == int(value) else f"{value:g}"


def _assign_tracks(scenes: list[dict]) -> list[int]:
    """Lowest track index per scene such that clips on one track never overlap
    in time (HyperFrames lints overlapping clips on a shared track)."""
    track_end: list[float] = []
    tracks = []
    for scene in scenes:
        start = float(scene.get("start", 0))
        end = start + float(scene.get("duration", 5))
        for index, busy_until in enumerate(track_end):
            if start >= busy_until:
                track_end[index] = end
                tracks.append(index)
                break
        else:
            track_end.append(end)
            tracks.append(len(track_end) - 1)
    return tracks


@dataclass
class HyperScene:
    """Hyperframe scene definition."""

    id: str
    start: float
    duration: float
    content: str  # HTML content


class HyperframesGenerator:
    """Generate videos using Hyperframes (HTML-native rendering)."""

    def __init__(
        self,
        project_name: str = "video-project",
        width: int = 1920,
        height: int = 1080,
        fps: int = 60,
    ):
        self.project_name = project_name
        self.width = width
        self.height = height
        self.fps = fps
        self.project_dir = Path(project_name)

    def init_project(self):
        """Initialize a Hyperframes project."""
        self.project_dir.mkdir(exist_ok=True)
        (self.project_dir / "index.html").parent.mkdir(exist_ok=True)

    def create_html_composition(self, scenes: list[dict], title: str = "Video") -> str:
        """Create HTML composition from scene descriptions.

        Args:
            scenes: List of dicts with {
                "id": "s01",
                "start": 0,
                "duration": 5,
                "content": "<div>...</div>"  # HTML content
            }
            title: Video title

        Returns:
            HTML string ready to render
        """
        for scene in scenes:
            if not _SCENE_ID_RE.match(str(scene["id"])):
                raise ValueError(
                    f"scene id {scene['id']!r} must start with a letter and use "
                    "only letters, digits, '_' or '-' (it is used as a CSS selector)"
                )
        ids = [scene["id"] for scene in scenes]
        if len(ids) != len(set(ids)):
            raise ValueError("scene ids must be unique")

        # Calculate total duration: last scene start + duration
        total_duration = (
            max((s.get("start", 0) + s.get("duration", 5)) for s in scenes)
            if scenes
            else 10
        )
        total = _fmt(total_duration)
        resolution = {
            (1920, 1080): "landscape",
            (1080, 1920): "portrait",
            (1080, 1080): "square",
        }.get((self.width, self.height))
        resolution_attr = f' data-resolution="{resolution}"' if resolution else ""

        # Every scene is a clip on the timeline; the runtime shows it only
        # inside [start, start + duration). Each one enters with a fade and a
        # short slide, as a real tween on a paused timeline that the renderer
        # seeks frame by frame.
        scenes_html = ""
        tweens = ""
        for scene, track in zip(scenes, _assign_tracks(scenes)):
            start = _fmt(scene["start"])
            duration = _fmt(scene["duration"])
            scenes_html += f"""
    <div
      id="{scene['id']}"
      class="clip scene"
      data-start="{start}"
      data-duration="{duration}"
      data-track-index="{track}"
    >
      {scene['content']}
    </div>
"""
            entrance = _fmt(min(ENTRANCE_SEC, float(scene["duration"])))
            tweens += (
                f'        tl.fromTo("#{scene["id"]}", {{ opacity: 0, y: 40 }}, '
                f'{{ opacity: 1, y: 0, duration: {entrance}, ease: "power2.out" }}, {start});\n'
            )

        html = f"""<!DOCTYPE html>
<html lang="en"{resolution_attr}>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width={self.width}, height={self.height}">
    <title>{html_lib.escape(title)}</title>
    <script src="gsap.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        html, body {{
            width: {self.width}px;
            height: {self.height}px;
            margin: 0;
            padding: 0;
            overflow: hidden;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            background: #0d1117;
            color: #c9d1d9;
        }}

        #root {{
            position: relative;
            width: {self.width}px;
            height: {self.height}px;
            overflow: hidden;
            background: #0d1117;
        }}

        .scene {{
            position: absolute;
            top: 0;
            left: 0;
            width: {self.width}px;
            height: {self.height}px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #0d1117;
        }}

        .text-large {{
            font-size: 100px;
            font-weight: bold;
            color: #FFFFFF;
        }}

        .text-title {{
            font-size: 80px;
            font-weight: bold;
            color: #FFD700;
        }}

        .text-subtitle {{
            font-size: 60px;
            color: #38BDF8;
        }}

        .text-body {{
            font-size: 50px;
            color: #FFFFFF;
        }}

        .text-label {{
            font-size: 40px;
            color: #8B949E;
        }}

        .color-danger {{ color: #FF4444; }}
        .color-success {{ color: #00C896; }}
        .color-gold {{ color: #FFD700; }}
        .color-info {{ color: #58a6ff; }}

        .text-center {{
            text-align: center;
        }}

        .text-left {{
            text-align: left;
        }}

        .text-right {{
            text-align: right;
        }}

        .flex-center {{
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            height: 100%;
        }}

        .flex-row {{
            display: flex;
            align-items: center;
            justify-content: space-around;
            height: 100%;
            padding: 0 100px;
        }}

        .column {{
            flex: 1;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div
      id="root"
      data-composition-id="main"
      data-start="0"
      data-duration="{total}"
      data-width="{self.width}"
      data-height="{self.height}"
      data-fps="{self.fps}"
    >
{scenes_html}
    </div>
    <script>
        const tl = gsap.timeline({{ paused: true }});
{tweens}        window.__timelines = window.__timelines || {{}};
        window.__timelines["main"] = tl;
        tl.seek(0);
    </script>
</body>
</html>
"""
        return html

    def write_composition(self, html: str, filename: str = "index.html") -> Path:
        """Write HTML composition to file."""
        self.init_project()
        if not PINNED_GSAP.exists():
            raise FileNotFoundError(
                f"GSAP not found at {PINNED_GSAP}. Run `npm ci` in {PINNED_DIR}."
            )
        shutil.copy2(PINNED_GSAP, self.project_dir / "gsap.min.js")
        output_file = self.project_dir / filename
        output_file.write_text(html)
        return output_file

    def render(self, output_path: str = None) -> str:
        """Render project to MP4 using Hyperframes CLI.

        Requires: npx hyperframes render

        Args:
            output_path: Where to save MP4 (e.g., "../output/video.mp4")

        Returns:
            Path to rendered video
        """
        if output_path is None:
            output_path = f"{self.project_name}.mp4"

        cmd = [
            *_cli_command(),
            "render",
            "-o",
            output_path,
            "--fps",
            str(self.fps),
            "--quiet",
        ]

        result = subprocess.run(
            cmd,
            cwd=self.project_dir,
            capture_output=True,
            text=True,
            env=_tool_env(),
        )

        if result.returncode != 0:
            raise RuntimeError(f"Hyperframes render failed: {result.stderr}")

        return output_path

    def preview(self):
        """Start live preview server.

        Requires: npx hyperframes preview
        """
        cmd = [*_cli_command(), "preview"]
        subprocess.run(cmd, cwd=self.project_dir, env=_tool_env())


def create_hyperframes_video(
    project_name: str, scenes: list[dict], output_path: str = None
) -> str:
    """High-level API: Create video from scene descriptions.

    Args:
        project_name: Project directory name
        scenes: List of scene dicts with {
            "id": "s01",
            "start": 0,
            "duration": 5,
            "content": "<div>...</div>"  # HTML content
        }
        output_path: Where to save MP4

    Returns:
        Path to rendered video
    """
    gen = HyperframesGenerator(project_name)
    html = gen.create_html_composition(scenes, title=project_name)
    gen.write_composition(html)

    if output_path is None:
        output_path = f"{project_name}.mp4"

    return gen.render(output_path)


if __name__ == "__main__":
    # Example
    scenes = [
        {
            "id": "s01",
            "start": 0,
            "duration": 3,
            "content": '<div class="flex-center"><div class="text-large text-gold">Hyperframes Video</div></div>',
        },
        {
            "id": "s02",
            "start": 3,
            "duration": 4,
            "content": '<div class="flex-center"><div class="text-subtitle">HTML-native rendering</div></div>',
        },
    ]

    output = create_hyperframes_video(
        "test-hyperframes", scenes, output_path="test.mp4"
    )
    print(f"✓ Video created: {output}")
