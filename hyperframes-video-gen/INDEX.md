# Hyperframes Video Generator - Complete System

**New dedicated system for professional video generation using Hyperframes (HTML-native rendering)**

## Location

```
/Users/amitri/Projects/LTX-Video/hyperframes-video-gen/
```

## Files

| File | Purpose |
|------|---------|
| `hyperframes_gen.py` | Core Python wrapper for Hyperframes |
| `README.md` | Complete feature guide & API documentation |
| `SETUP.md` | Installation & troubleshooting guide |
| `STATUS.md` | Overview & when to use |
| `examples/examples_call_payoff_hyperframes.py` | Working example video |
| `output/` | Generated MP4 videos |

## Quick Start (3 steps)

1. **Install** (see SETUP.md)
   ```bash
   npm install -g hyperframes
   brew install ffmpeg
   ```

2. **Create** (Python)
   ```python
   from hyperframes_gen import create_hyperframes_video
   
   scenes = [{
       "id": "s01",
       "start": 0,
       "duration": 3,
       "content": '<div style="font-size: 100px;">Hello</div>'
   }]
   
   output = create_hyperframes_video("my-video", scenes)
   ```

3. **Render**
   ```bash
   npx hyperframes render -o my-video.mp4
   ```

## What You Get

✅ HTML-native video composition
✅ Smooth animations (GSAP, CSS, Lottie)
✅ Professional text rendering
✅ SVG graph support
✅ Live preview (iterative development)
✅ Deterministic output
✅ Open source (Apache 2.0)

## Comparison with PIL+FFmpeg System

| Aspect | PIL+FFmpeg (`simple-video-gen/`) | Hyperframes (`hyperframes-video-gen/`) |
|--------|----------------------------------|--------------------------------------|
| Setup | 2 min | 10 min |
| Quality | Good | Excellent |
| Animations | Limited | Full (GSAP, CSS) |
| Learning | Very easy | Easy |
| Best for | Simple text videos | Professional output |
| Render speed | Very fast | Medium |
| File size | Small | Variable |

## Two Video Systems Now Available

### System 1: PIL + FFmpeg (`/simple-video-gen/`)
- Quick setup
- Simple API
- Perfect for text-based educational videos
- Fast rendering
- 8 pre-made examples ready to use

### System 2: Hyperframes (`/hyperframes-video-gen/`)
- Professional output
- Animation support
- HTML/CSS native
- Interactive preview
- Better for complex visuals

## Choose Based on Your Needs

**Use PIL+FFmpeg if:**
- Creating quick educational content
- Simple text videos
- Want fastest setup
- Minimal dependencies

**Use Hyperframes if:**
- Need animations
- Complex layouts/graphs
- Professional quality
- Want to iterate quickly with preview

## Getting Started Now

### With PIL+FFmpeg (Existing System)
```bash
cd /Users/amitri/Projects/LTX-Video/simple-video-gen/
python examples/call_payoff_visual.py
```

### With Hyperframes (New System)
```bash
cd /Users/amitri/Projects/LTX-Video/hyperframes-video-gen/
# First: Follow SETUP.md
# Then: python examples/examples_call_payoff_hyperframes.py
```

## Next Steps

1. **Choose your system** based on needs
2. **Follow setup guide** for your chosen system
3. **Run an example** to verify it works
4. **Create your own videos** by modifying examples
5. **Customize HTML/CSS** for your unique style

## Documentation

- **API Docs**: README.md in each directory
- **Setup**: SETUP.md for Hyperframes
- **Examples**: Pre-made videos in examples/ folder
- **Comparison**: STATUS.md for feature comparison

## Files by Purpose

**Implementation**
- `hyperframes_gen.py` - Main wrapper

**Documentation**
- `README.md` - Features & API
- `SETUP.md` - Installation steps
- `STATUS.md` - Overview & comparison
- `INDEX.md` - This file

**Examples**
- `examples/examples_call_payoff_hyperframes.py` - Working sample

**Output**
- `output/` - Rendered MP4 videos

## Summary

You now have TWO production-ready video generation systems:

1. **PIL + FFmpeg** - Simple, fast, perfect for starting
2. **Hyperframes** - Professional, animated, feature-rich

Both use Python API. Both output MP4. Both battle-tested.

Choose based on your project needs. Or use both!

---

**Ready?** Start with SETUP.md for Hyperframes, or jump straight to examples/.
