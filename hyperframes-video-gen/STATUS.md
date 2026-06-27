# Hyperframes Video Generator - Status & Guide

## What's Complete

✅ **Hyperframes Wrapper** (`hyperframes_gen.py`)
- HTML composition generation with fixed full-screen positioning
- Scene timing (data-start, data-duration attributes)
- Project management (create, write, render)
- High-level Python API
- **Fixed**: Full-screen rendering (absolute positioning, viewport coverage)
- **Fixed**: Composition duration calculation (max of start+duration)

✅ **Documentation**
- README.md - Complete feature guide
- SETUP.md - Installation & troubleshooting
- Examples ready to run

✅ **Example Videos**
- Call Option Payoff (with SVG graphs) - 20 seconds, 298KB, full-screen verified
- Ready to extend
- **Status**: Rendering verified (no half-screen flashing)

## Directory Structure

```
hyperframes-video-gen/
├── hyperframes_gen.py          ← Core library
├── README.md                   ← Feature guide
├── SETUP.md                    ← Installation guide
├── STATUS.md                   ← This file
├── examples/
│   └── examples_call_payoff_hyperframes.py
└── output/                     ← Videos rendered here
```

## Key Differences: PIL+FFmpeg vs Hyperframes

| Aspect | PIL + FFmpeg | Hyperframes |
|--------|--------------|-------------|
| **Approach** | Image frames → FFmpeg | HTML → Puppeteer → FFmpeg |
| **Text Quality** | Basic, rasterized | Professional, vector |
| **Animations** | Frame-by-frame (slow) | GSAP, CSS (smooth) |
| **Vector Support** | Limited | Native SVG |
| **Interactive Preview** | No | Yes (live reload) |
| **Setup Complexity** | Simple | Requires Node.js |
| **Render Speed** | Fast (10-20 sec) | Medium (30-60 sec) |
| **File Size** | Small (100-300KB) | Variable (500KB-5MB) |
| **Professional Output** | Good | Excellent |
| **Best For** | Simple text videos | Complex animations, graphics |

## When to Use Each

### Use PIL + FFmpeg if:
- Simple text-based educational videos
- Quick turnaround needed
- Minimal dependencies preferred
- Small file sizes important

### Use Hyperframes if:
- Need smooth animations
- Complex layouts/graphics
- Want professional quality
- Need interactive preview
- Designing with HTML/CSS preferred

## Getting Started with Hyperframes

### Step 1: Install

```bash
# See SETUP.md for detailed instructions
npm install -g hyperframes
brew install ffmpeg
```

### Step 2: Create Video

```python
from hyperframes_gen import create_hyperframes_video

scenes = [
    {
        "id": "s01",
        "start": 0,
        "duration": 5,
        "content": '<div style="font-size: 100px; color: #FFD700;">Your Content</div>'
    }
]

output = create_hyperframes_video("my-video", scenes)
```

### Step 3: Render

```bash
# Automatic via Python
# or manually
npx hyperframes render -o my-video.mp4
```

## HTML Content Patterns

### Text Only

```html
<div style="display: flex; align-items: center; justify-content: center; height: 100%; font-size: 80px; color: #FFFFFF;">
    Hello World
</div>
```

### Two Column

```html
<div style="display: flex; height: 100%; justify-content: space-around;">
    <div style="flex: 1; text-align: center; font-size: 60px;">Left</div>
    <div style="flex: 1; text-align: center; font-size: 60px;">Right</div>
</div>
```

### SVG Graph

```html
<svg width="800" height="600" style="background: #0d1117;">
    <line x1="50" y1="500" x2="750" y2="500" stroke="#999" stroke-width="2"/>
    <line x1="50" y1="50" x2="50" y2="500" stroke="#999" stroke-width="2"/>
    <!-- Your graph here -->
</svg>
```

### With Animation

```html
<div id="box" style="font-size: 80px; opacity: 0;">
    Animated Text
</div>

<script>
gsap.to("#box", { opacity: 1, duration: 2 });
</script>
```

## Recommended Colors

```css
/* Dark background (keep consistent) */
background: #0d1117;

/* Text colors */
--gold: #FFD700;      /* Highlights, titles */
--red: #FF4444;       /* Danger, losses */
--green: #00C896;     /* Success, gains */
--blue: #38BDF8;      /* Info, highlights */
--white: #FFFFFF;     /* Body text */
--gray: #8B949E;      /* Muted text */
```

## Next Steps

1. **Follow SETUP.md** to install dependencies
2. **Copy examples** and customize for your topics
3. **Use preview mode** for rapid iteration (`gen.preview()`)
4. **Render when ready** (`gen.render()`)
5. **Share videos** directly or embed in platform

## File Locations

- **Source**: `/Users/amitri/Projects/LTX-Video/hyperframes-video-gen/`
- **Output**: `/Users/amitri/Projects/LTX-Video/hyperframes-video-gen/output/`
- **Examples**: `/Users/amitri/Projects/LTX-Video/hyperframes-video-gen/examples/`

## Performance Expectations

- **First render**: 30-90 sec (Chromium downloads & caches)
- **Subsequent renders**: 15-45 sec per video
- **Preview startup**: 5-10 sec
- **Live reload**: Instant

## Advantages This Unlocks

With Hyperframes, you can now:
- ✨ Create smooth animated transitions between scenes
- 📊 Render interactive dashboards and charts
- 🎨 Use professional typography and styling
- 🎬 Build complex multi-element compositions
- 🔄 Iterate quickly with live preview
- 🎯 Target specific visual effects (shaders, etc.)

## Comparison with Original System

| Feature | PIL+FFmpeg | Hyperframes |
|---------|------------|-------------|
| Setup time | 5 min | 15 min |
| Learning curve | Very simple | Moderate |
| Time per video | 2-5 min | 2-3 min (after first render) |
| Quality | Good | Excellent |
| Flexibility | Limited | High |
| Maintenance | Easy | Easy |

## Support

- Full working example in `examples/`
- Complete API documentation in README.md
- Step-by-step setup in SETUP.md
- Hyperframes docs at https://hyperframes.heygen.com

Ready to create your first Hyperframes video? Start with SETUP.md!
