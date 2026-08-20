#!/usr/bin/env python3
"""Hyperframes video generator wrapper - HTML-native video composition."""

import json
import subprocess
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class HyperScene:
    """Hyperframe scene definition."""
    id: str
    start: float
    duration: float
    content: str  # HTML content


class HyperframesGenerator:
    """Generate videos using Hyperframes (HTML-native rendering)."""

    def __init__(self, project_name: str = "video-project", width: int = 1920, height: int = 1080, fps: int = 60):
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
        # Calculate total duration: last scene start + duration
        total_duration = max((s.get('start', 0) + s.get('duration', 5)) for s in scenes) if scenes else 10

        scenes_html = ""
        for scene in scenes:
            scenes_html += f"""
    <div
      id="{scene['id']}"
      data-start="{scene['start']}"
      data-duration="{scene['duration']}"
      style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; background: #0d1117; opacity: 1;"
    >
      {scene['content']}
    </div>
"""

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script>
        window.__hf = {{
            duration: {total_duration},
            seek: function(t) {{
                // Hyperframes will call this to seek to time t
            }}
        }};
    </script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        html, body {{
            width: 100%;
            height: 100%;
            margin: 0;
            padding: 0;
            overflow: hidden;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            background: #0d1117;
            color: #c9d1d9;
        }}

        .stage {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
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
    <div class="stage">
{scenes_html}
    </div>
</body>
</html>
"""
        return html

    def write_composition(self, html: str, filename: str = "index.html") -> Path:
        """Write HTML composition to file."""
        self.init_project()
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

        cmd = ["npx", "hyperframes", "render", "-o", output_path]

        result = subprocess.run(cmd, cwd=self.project_dir, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"Hyperframes render failed: {result.stderr}")

        return output_path

    def preview(self):
        """Start live preview server.

        Requires: npx hyperframes preview
        """
        cmd = ["npx", "hyperframes", "preview"]
        subprocess.run(cmd, cwd=self.project_dir)


def create_hyperframes_video(project_name: str, scenes: list[dict], output_path: str = None) -> str:
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
            "content": '<div class="flex-center"><div class="text-large text-gold">Hyperframes Video</div></div>'
        },
        {
            "id": "s02",
            "start": 3,
            "duration": 4,
            "content": '<div class="flex-center"><div class="text-subtitle">HTML-native rendering</div></div>'
        }
    ]

    output = create_hyperframes_video("test-hyperframes", scenes, output_path="test.mp4")
    print(f"✓ Video created: {output}")
