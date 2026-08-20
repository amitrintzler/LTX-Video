# Hyperframes Setup Guide

## Prerequisites

- Node.js 16+ (for Hyperframes)
- Python 3.9+
- FFmpeg (for video encoding)
- Puppeteer dependencies

## Installation Steps

### 1. Install Node.js & Hyperframes

```bash
# Check if Node.js is installed
node --version

# If not, install via Homebrew
brew install node

# Install Hyperframes globally
npm install -g hyperframes

# Or use npx (auto-downloads on first use)
npx hyperframes --version
```

### 2. Install FFmpeg

```bash
# Via Homebrew
brew install ffmpeg

# Verify
ffmpeg -version
```

### 3. Install Python Dependencies

```bash
cd /Users/amitri/Projects/LTX-Video/hyperframes-video-gen

# Optional: Create virtual environment
python3 -m venv venv
source venv/bin/activate

# No Python dependencies needed for basic usage
# But recommended for full functionality:
pip install requests  # For future features
```

### 4. Test Installation

```bash
# Test Hyperframes
npx hyperframes --version

# Test FFmpeg
ffmpeg -version

# Test Python wrapper
python hyperframes_gen.py
```

## Verify Setup

Run this to verify everything works:

```bash
python examples/examples_call_payoff_hyperframes.py
```

Should create: `output/call-payoff-hyperframes.mp4`

## Troubleshooting

### Node.js Issues

**Error: `command not found: node`**
```bash
brew install node
# or check PATH
echo $PATH
```

**Error: `npm permission denied`**
```bash
# Fix npm permissions
mkdir ~/.npm-global
npm config set prefix '~/.npm-global'
export PATH=~/.npm-global/bin:$PATH
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.zshrc
```

### Hyperframes Issues

**Error: `npx hyperframes not found`**
```bash
# Try installing globally
npm install -g hyperframes@latest

# Or use directly
npx hyperframes@latest --version
```

**Error: Rendering fails with `Puppeteer`**
```bash
# Install Chromium dependencies on Mac
brew install --cask chromium

# Or let Hyperframes handle it (downloads on first use)
npx hyperframes render
```

### FFmpeg Issues

**Error: `ffmpeg: command not found`**
```bash
brew install ffmpeg
```

**Error: Codec issues**
```bash
# Verify FFmpeg has libx264
ffmpeg -codecs | grep h264

# If missing, reinstall
brew reinstall ffmpeg --with-libx264
```

## Quick Start After Setup

```bash
# 1. Create project
mkdir my-video-project
cd my-video-project

# 2. Copy example
cp ../examples/examples_call_payoff_hyperframes.py ./

# 3. Run it
python examples_call_payoff_hyperframes.py

# 4. Output
# ✓ Call Option Payoff (Hyperframes) created: ../output/call-payoff-hyperframes.mp4
```

## Development Workflow

### For Rapid Iteration

```bash
# 1. Create HTML file
cat > my-video/index.html << 'EOF'
<!DOCTYPE html>
<html>
<head><style>...</style></head>
<body>
    <div id="stage">...</div>
</body>
</html>
EOF

# 2. Start live preview
cd my-video
npx hyperframes preview

# 3. Open browser to http://localhost:3000
# Edit HTML, changes appear instantly

# 4. When done, render
npx hyperframes render -o ../output/final.mp4
```

### Via Python

```python
from hyperframes_gen import HyperframesGenerator

gen = HyperframesGenerator("my-video")
html = gen.create_html_composition(scenes)
gen.write_composition(html)

# Live preview
gen.preview()  # Opens http://localhost:3000

# When ready
gen.render(output_path="final.mp4")
```

## System Requirements

- **macOS 10.15+** (Ventura recommended)
- **Disk space**: ~500MB for Chromium + dependencies
- **RAM**: 4GB minimum, 8GB+ recommended
- **Network**: Internet required (first time Chromium download)

## Next Steps

1. ✅ Install dependencies (Node, FFmpeg, Python)
2. ✅ Test with provided example
3. 📝 Create your first video using `hyperframes_gen.py`
4. 🎨 Customize HTML/CSS for your needs
5. 🎬 Render and share!

## Support

- [Hyperframes GitHub](https://github.com/heygen-com/hyperframes)
- [Issues](https://github.com/heygen-com/hyperframes/issues)
- [Discussions](https://github.com/heygen-com/hyperframes/discussions)
