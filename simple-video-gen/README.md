# Simple Video Generator

Clean, fast video generation using **PIL + FFmpeg**. No LLM codegen, no complex pipelines, no hangs.

## Features

- Generate videos from simple text descriptions
- Full control over text positioning, colors, fonts, timing
- No clipping, no text positioning errors
- Fast frame generation + FFmpeg stitching
- Works locally on Mac
- ~150 lines of code, zero magic

## Setup

```bash
# Install ffmpeg
brew install ffmpeg

# No other dependencies needed (PIL is bundled with Pillow)
pip install Pillow
```

## Usage

### Simple API

```python
from video_gen import create_simple_video

scenes = [
    {
        "title": "Scene 1",
        "duration_sec": 3,
        "bg_color": "#0d1117",
        "text": [
            {"text": "Hello World", "x": 960, "y": 540, "font_size": 80, "anchor": "mm"}
        ]
    },
    {
        "title": "Scene 2",
        "duration_sec": 5,
        "bg_color": "#0d1117",
        "text": [
            {"text": "Line 1", "x": 960, "y": 400, "font_size": 60},
            {"text": "Line 2", "x": 960, "y": 600, "font_size": 60, "color": "#FF4444"}
        ]
    }
]

output = create_simple_video("my-video", scenes, output_path="output/my-video.mp4")
print(f"Created: {output}")
```

### Advanced API

```python
from video_gen import VideoGenerator, Scene, TextElement

gen = VideoGenerator(width=1920, height=1080, fps=60)

scenes = [
    Scene(
        title="Scene 1",
        duration_sec=3,
        background_color="#0d1117",
        elements=[
            TextElement(text="Hello", x=960, y=540, font_size=80, color="#FFFFFF", anchor="mm")
        ]
    )
]

output = gen.create_video(scenes, "output/video.mp4")
```

## Positioning

Use PIL anchor codes:
- `"mm"` — middle-middle (center)
- `"lm"` — left-middle
- `"rm"` — right-middle
- `"mt"` — middle-top
- `"mb"` — middle-bottom
- etc.

Or specify absolute (x, y) coordinates (0,0 is top-left).

## Examples

Run the example:

```bash
cd examples
python put_option_tutorial.py
```

Output will be at `output/put-option-tutorial.mp4`

## Output

All videos go to `output/` directory. Videos are:
- 1920x1080 @ 60fps
- H.264 codec
- MP4 format
- Fast preset (FFmpeg)

## Customization

Edit `video_gen.py`:
- Change default `width`, `height`, `fps` in `VideoGenerator.__init__`
- Add custom fonts in `_get_font()`
- Modify FFmpeg codec/preset in `create_video()`

## No Dependencies Beyond

- Python 3.9+
- Pillow (PIL)
- FFmpeg (brew install ffmpeg)

That's it. No LLM, no validation loops, no hanging jobs.
