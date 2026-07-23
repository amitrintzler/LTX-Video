#!/usr/bin/env python3
"""Simple video generator using PIL + FFmpeg. No dependencies beyond PIL and ffmpeg."""

import subprocess
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from dataclasses import dataclass
import json


@dataclass
class TextElement:
    text: str
    x: int
    y: int
    font_size: int = 48
    color: str = "#FFFFFF"
    anchor: str = "lm"


@dataclass
class LineElement:
    x1: int
    y1: int
    x2: int
    y2: int
    color: str = "#FFFFFF"
    width: int = 2


@dataclass
class PolygonElement:
    points: list
    fill: str = "#FFFFFF"
    outline: str = None
    width: int = 1


@dataclass
class Scene:
    title: str
    duration_sec: float
    background_color: str = "#0d1117"
    elements: list = None

    def __post_init__(self):
        if self.elements is None:
            self.elements = []


class VideoGenerator:
    def __init__(self, width: int = 1920, height: int = 1080, fps: int = 60):
        self.width = width
        self.height = height
        self.fps = fps
        self.temp_dir = None

    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _get_font(self, size: int):
        """Get system font. Falls back to default if not available."""
        try:
            return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)
        except:
            return ImageFont.load_default()

    def _create_frame(self, scene: Scene) -> Image.Image:
        """Create a single frame for a scene."""
        img = Image.new("RGB", (self.width, self.height), self._hex_to_rgb(scene.background_color))
        draw = ImageDraw.Draw(img)

        for element in scene.elements:
            if isinstance(element, TextElement):
                font = self._get_font(element.font_size)
                color = self._hex_to_rgb(element.color)
                draw.text((element.x, element.y), element.text, font=font, fill=color, anchor=element.anchor)
            elif isinstance(element, LineElement):
                color = self._hex_to_rgb(element.color)
                draw.line([(element.x1, element.y1), (element.x2, element.y2)], fill=color, width=element.width)
            elif isinstance(element, PolygonElement):
                fill = self._hex_to_rgb(element.fill) if element.fill else None
                outline = self._hex_to_rgb(element.outline) if element.outline else None
                draw.polygon(element.points, fill=fill, outline=outline, width=element.width)

        return img

    def _generate_frame_sequence(self, scene: Scene, output_dir: Path):
        """Generate all frames for a scene."""
        frame_count = int(scene.duration_sec * self.fps)
        frame = self._create_frame(scene)

        for i in range(frame_count):
            frame_path = output_dir / f"frame_{i:06d}.png"
            frame.save(frame_path)

    def create_video(self, scenes: list[Scene], output_path: str) -> str:
        """Create MP4 from scenes."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)

            # Generate all frames
            for i, scene in enumerate(scenes):
                scene_dir = temp_dir / f"scene_{i:02d}"
                scene_dir.mkdir()
                self._generate_frame_sequence(scene, scene_dir)

            # Concatenate all frames
            all_frames_dir = temp_dir / "all_frames"
            all_frames_dir.mkdir()

            frame_num = 0
            for i, scene in enumerate(scenes):
                scene_dir = temp_dir / f"scene_{i:02d}"
                for frame_path in sorted(scene_dir.glob("frame_*.png")):
                    new_path = all_frames_dir / f"frame_{frame_num:06d}.png"
                    frame_path.rename(new_path)
                    frame_num += 1

            # Stitch frames to video with FFmpeg
            input_pattern = str(all_frames_dir / "frame_%06d.png")
            cmd = [
                "ffmpeg",
                "-y",
                "-framerate", str(self.fps),
                "-i", input_pattern,
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-preset", "fast",
                str(output_path)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg failed: {result.stderr}")

        return str(output_path)


def create_simple_video(title: str, scenes: list[dict], output_path: str = None) -> str:
    """High-level API: Create video from scene descriptions.

    Args:
        title: Video title
        scenes: List of dicts with keys: text (str or list), duration_sec, bg_color (optional)
        output_path: Where to save MP4 (default: ./output/{title}.mp4)

    Returns:
        Path to generated MP4
    """
    if output_path is None:
        output_path = f"output/{title}.mp4"

    scene_objects = []
    for scene_desc in scenes:
        texts = scene_desc.get("text", [])
        if isinstance(texts, str):
            texts = [{"text": texts, "x": 960, "y": 540}]

        elements = []
        for i, text_desc in enumerate(texts):
            if isinstance(text_desc, str):
                text_desc = {"text": text_desc, "x": 960, "y": 400 + i * 100}

            elements.append(TextElement(
                text=text_desc.get("text", ""),
                x=text_desc.get("x", 960),
                y=text_desc.get("y", 540),
                font_size=text_desc.get("font_size", 48),
                color=text_desc.get("color", "#FFFFFF"),
                anchor=text_desc.get("anchor", "mm")
            ))

        scene_objects.append(Scene(
            title=scene_desc.get("title", ""),
            duration_sec=scene_desc.get("duration_sec", 5),
            background_color=scene_desc.get("bg_color", "#0d1117"),
            elements=elements
        ))

    gen = VideoGenerator()
    return gen.create_video(scene_objects, output_path)


if __name__ == "__main__":
    # Example usage
    scenes = [
        {
            "title": "Intro",
            "duration_sec": 3,
            "text": [
                {"text": "Put Option Basics", "x": 960, "y": 300, "font_size": 80, "anchor": "mm"},
                {"text": "The right to sell at a fixed price", "x": 960, "y": 500, "font_size": 48, "anchor": "mm"}
            ]
        },
        {
            "title": "Definition",
            "duration_sec": 5,
            "text": [
                {"text": "Strike Price: $50", "x": 960, "y": 400, "font_size": 60, "anchor": "mm"},
                {"text": "Stock Falls to: $40", "x": 960, "y": 550, "font_size": 60, "anchor": "mm", "color": "#FF4444"},
                {"text": "Your Profit: $10/share", "x": 960, "y": 700, "font_size": 60, "anchor": "mm", "color": "#00C896"}
            ]
        }
    ]

    output = create_simple_video("put-option-demo", scenes)
    print(f"Video created: {output}")
