# Hyperframes Video Generator

HTML-native video generation using **Hyperframes** by HeyGen. Write HTML, render video, built for agents.

## Why Hyperframes?

✅ **HTML-native** - Compositions are just HTML + CSS
✅ **Animation support** - GSAP, CSS animations, Lottie, Three.js
✅ **Deterministic** - Same input = identical output
✅ **Agent-optimized** - Designed for AI-driven workflows
✅ **Open source** - Apache 2.0 licensed
✅ **Professional quality** - Puppeteer + FFmpeg rendering

## Setup

```bash
# Install Hyperframes
npm install hyperframes
# or
npx hyperframes  # Downloads on first use

# Install Python dependencies
pip install -r requirements.txt
```

## Quick Start

```python
from hyperframes_gen import create_hyperframes_video

scenes = [
    {
        "id": "s01",
        "start": 0,
        "duration": 3,
        "content": '<div style="font-size: 80px; color: white;">Hello World</div>'
    }
]

output = create_hyperframes_video("my-video", scenes, output_path="my-video.mp4")
print(f"Video created: {output}")
```

## Project Structure

```
hyperframes-video-gen/
├── hyperframes_gen.py          ← Main library
├── README.md                   ← This file
├── SETUP.md                    ← Installation guide
├── examples/                   ← Example videos
│   └── examples_call_payoff_hyperframes.py
└── output/                     ← Generated videos
```

## Core Classes

### HyperframesGenerator

Main class for creating Hyperframes projects.

```python
gen = HyperframesGenerator(
    project_name="my-video",
    width=1920,
    height=1080,
    fps=60
)

# Create HTML composition
html = gen.create_html_composition(scenes, title="My Video")

# Write to project directory
html_file = gen.write_composition(html)

# Render to MP4
output = gen.render(output_path="video.mp4")

# Or preview in browser
gen.preview()  # Opens http://localhost:3000
```

## Scene Structure

Each scene is a dictionary:

```python
{
    "id": "s01",           # Unique scene ID
    "start": 0,            # Start time in seconds
    "duration": 5,         # Duration in seconds
    "content": "<div>...</div>"  # HTML content
}
```

## HTML Content Examples

### Simple Text

```python
"content": '''
<div style="display: flex; align-items: center; justify-content: center; height: 100%;">
    <div style="font-size: 100px; color: #FFD700; font-weight: bold;">Hello</div>
</div>
'''
```

### Side-by-Side Layout

```python
"content": '''
<div style="display: flex; height: 100%; justify-content: space-around; align-items: center; padding: 0 100px;">
    <div style="flex: 1; text-align: center;">
        <div style="font-size: 60px; color: #38BDF8; margin-bottom: 20px;">Left</div>
        <div style="font-size: 40px; color: white;">Content here</div>
    </div>
    <div style="flex: 1; text-align: center;">
        <div style="font-size: 60px; color: #EF4444; margin-bottom: 20px;">Right</div>
        <div style="font-size: 40px; color: white;">Content here</div>
    </div>
</div>
'''
```

### SVG Graphs

```python
"content": '''
<div style="display: flex; align-items: center; justify-content: center; height: 100%;">
    <svg width="1200" height="600" viewBox="0 0 1200 600">
        <!-- Axes -->
        <line x1="100" y1="500" x2="1100" y2="500" stroke="#8B949E" stroke-width="3"/>
        <line x1="100" y1="100" x2="100" y2="500" stroke="#8B949E" stroke-width="3"/>

        <!-- Payoff line -->
        <line x1="100" y1="400" x2="400" y2="400" stroke="#FF4444" stroke-width="4"/>
        <line x1="400" y1="400" x2="1100" y2="150" stroke="#00C896" stroke-width="4"/>

        <!-- Labels -->
        <text x="550" y="540" font-size="20" fill="#FFD700">Strike Price</text>
        <text x="250" y="380" font-size="20" fill="#FF4444">LOSS</text>
        <text x="800" y="200" font-size="20" fill="#00C896">PROFIT</text>
    </svg>
</div>
'''
```

### With CSS Animations (GSAP)

```python
"content": '''
<div style="display: flex; align-items: center; justify-content: center; height: 100%;">
    <div id="animated" style="font-size: 80px; color: #FFD700; opacity: 0;">
        Animated Text
    </div>
</div>

<script>
// Hyperframes will execute embedded scripts
gsap.to("#animated", {
    opacity: 1,
    duration: 2,
    ease: "power2.out"
});
</script>
'''
```

## Color Palette

```
Dark Background:  #0d1117
Gold/Highlight:   #FFD700
Red/Loss:         #FF4444
Green/Gain:       #00C896
Blue/Info:        #38BDF8
Light Blue:       #58a6ff
Gray/Muted:       #8B949E
White/Text:       #FFFFFF
```

## Rendering

### Command Line

```bash
# Render single project
npx hyperframes render -o output.mp4

# Preview in browser (live reload)
npx hyperframes preview

# Lint HTML
npx hyperframes lint
```

### Python API

```python
gen = HyperframesGenerator("my-project")
gen.render(output_path="video.mp4")
```

## Creating Videos

### Step 1: Define Scenes

```python
scenes = [
    {
        "id": "intro",
        "start": 0,
        "duration": 3,
        "content": "..."
    },
    {
        "id": "main",
        "start": 3,
        "duration": 5,
        "content": "..."
    }
]
```

### Step 2: Create Composition

```python
gen = HyperframesGenerator("my-video")
html = gen.create_html_composition(scenes, title="My Video")
gen.write_composition(html)
```

### Step 3: Render

```python
# Via Python
output = gen.render(output_path="my-video.mp4")

# Or via CLI
# npx hyperframes render -o my-video.mp4
```

## Examples

See `examples/` directory for complete examples:

- `examples_call_payoff_hyperframes.py` - Call option payoff with SVG graphs

Run:
```bash
python examples/examples_call_payoff_hyperframes.py
```

## Advantages Over PIL + FFmpeg

| Feature | PIL + FFmpeg | Hyperframes |
|---------|--------------|-------------|
| Animation Support | No | Yes (GSAP, CSS, Lottie) |
| Text Rendering | Basic | Professional |
| Vector Graphics | Manual | Native SVG |
| Interactive Preview | No | Yes (live reload) |
| Complex Layouts | Difficult | HTML/CSS native |
| Video Composition | No | Yes |
| Agent-Friendly | No | Yes |

## Troubleshooting

**Issue: `npx hyperframes not found`**
```bash
npm install -g hyperframes
# or
npx hyperframes@latest
```

**Issue: Rendering is slow**
- First render creates cache (~1-2 min)
- Subsequent renders are faster
- Use `preview` mode to iterate quickly

**Issue: Fonts not rendering**
- Hyperframes uses system fonts + web fonts
- Specify font-family in HTML
- Works with Google Fonts via `<link>`

## Documentation

- [Hyperframes GitHub](https://github.com/heygen-com/hyperframes)
- [Hyperframes Docs](https://hyperframes.heygen.com)
- [HeyGen](https://www.heygen.com)

## License

This wrapper is MIT licensed. Hyperframes is Apache 2.0 licensed.
