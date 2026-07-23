# Video Generation Scenario Template

Complete guide for creating educational videos using the simple video generator.

## Quick Start Scenario

```python
#!/usr/bin/env python3
"""Educational Video: [TOPIC]"""

import sys
sys.path.insert(0, "..")
from video_gen import create_simple_video

# Define your scenes
scenes = [
    {
        "title": "Scene 1 Title",
        "duration_sec": 3,
        "bg_color": "#0d1117",
        "text": [
            {"text": "Main Title", "x": 960, "y": 250, "font_size": 100, "anchor": "mm", "color": "#FFD700"},
            {"text": "Subtitle", "x": 960, "y": 450, "font_size": 50, "anchor": "mm", "color": "#58a6ff"},
        ]
    },
    # ... more scenes
]

# Generate video
output = create_simple_video("video-title", scenes, output_path="../output/video-title.mp4")
print(f"✓ Created: {output}")
```

## Full Scenario Example: Bull Call Spread

```python
#!/usr/bin/env python3
"""Bull Call Spread - Limited risk, limited reward strategy."""

import sys
sys.path.insert(0, "..")
from video_gen import VideoGenerator, Scene, TextElement, LineElement

gen = VideoGenerator()

scenes = [
    # Scene 1: Title
    Scene(
        title="Intro",
        duration_sec=3,
        background_color="#0d1117",
        elements=[
            TextElement("Bull Call Spread", x=960, y=250, font_size=100, anchor="mm", color="#FFD700"),
            TextElement("Limited Risk Strategy", x=960, y=450, font_size=50, anchor="mm", color="#58a6ff"),
        ]
    ),

    # Scene 2: Setup
    Scene(
        title="Strategy Setup",
        duration_sec=4,
        background_color="#0d1117",
        elements=[
            TextElement("What is a Bull Call Spread?", x=960, y=200, font_size=70, anchor="mm", color="#38BDF8"),
            TextElement("▪ BUY a call at lower strike", x=960, y=350, font_size=50, anchor="mm", color="#00C896"),
            TextElement("▪ SELL a call at higher strike", x=960, y=480, font_size=50, anchor="mm", color="#FF4444"),
            TextElement("Net: Pay premium upfront", x=960, y=650, font_size=45, anchor="mm", color="#FFD700"),
        ]
    ),

    # Scene 3: Risk/Reward
    Scene(
        title="Risk and Reward",
        duration_sec=4,
        background_color="#0d1117",
        elements=[
            TextElement("Risk vs Reward", x=960, y=200, font_size=70, anchor="mm", color="#FFD700"),
            TextElement("Max Loss", x=300, y=450, font_size=55, anchor="mm", color="#FF4444"),
            TextElement("Net premium paid", x=300, y=580, font_size=40, anchor="mm", color="#8B949E"),
            TextElement("Max Gain", x=1620, y=450, font_size=55, anchor="mm", color="#00C896"),
            TextElement("Difference in strikes - premium", x=1620, y=580, font_size": 40, "anchor": "mm", "color": "#8B949E"),
            TextElement("Both are LIMITED", x=960, y=750, font_size=50, anchor="mm", color="#FFFFFF"),
        ]
    ),

    # Scene 4: Payoff Diagram
    Scene(
        title="Payoff Diagram",
        duration_sec=5,
        background_color="#0d1117",
        elements=[
            TextElement("Bull Call Spread Diagram", x=960, y=150, font_size=70, anchor="mm", color="#FFD700"),
            # Axes
            LineElement(200, 700, 1700, 700, color="#8B949E", width=3),
            LineElement(200, 150, 200, 700, color="#8B949E", width=3),
            # Strike markers
            LineElement(500, 150, 500, 700, color="#38BDF8", width=2),
            LineElement(900, 150, 900, 700, color="#EF4444", width=2),
            # Payoff curve: horizontal loss, diagonal profit, horizontal cap
            LineElement(200, 600, 500, 600, color="#FF4444", width=4),
            LineElement(500, 600, 900, 400, color="#00C896", width=4),
            LineElement(900, 400, 1700, 400, color="#FF4444", width=4),
            # Labels
            TextElement("Lower Strike", x=500, y=730, font_size=35, anchor="mm", color="#38BDF8"),
            TextElement("Upper Strike", x=900, y=730, font_size=35, anchor="mm", color="#EF4444"),
            TextElement("Limited Profit", x=1200, y=300, font_size=40, anchor="mm", color="#00C896"),
            TextElement("Limited Loss", x=300, y=550, font_size=40, anchor="mm", color="#FF4444"),
        ]
    ),

    # Scene 5: Real Example
    Scene(
        title="Real Example",
        duration_sec=5,
        background_color="#0d1117",
        elements=[
            TextElement("Real Example: Apple", x=960, y=150, font_size=70, anchor="mm", color="#FFD700"),
            TextElement("Current Stock Price: $150", x=960, y=280, font_size=50, anchor="mm", color="#FFFFFF"),
            TextElement("BUY Call", x=300, y=450, font_size=50, anchor="mm", color="#00C896"),
            TextElement("Strike $150", x=300, y=550, font_size": 40, "anchor": "mm", "color": "#FFFFFF"),
            TextElement("Cost: $4", x=300, y=630, font_size=40, anchor="mm", color="#FF4444"),
            TextElement("SELL Call", x=1620, y=450, font_size=50, anchor="mm", color="#FF4444"),
            TextElement("Strike $160", x=1620, y=550, font_size=40, anchor="mm", color="#FFFFFF"),
            TextElement("Receive: $1", x=1620, y=630, font_size=40, anchor="mm", color="#00C896"),
            TextElement("Net Cost: $3", x=960, y=800, font_size=50, anchor="mm", color="#FFD700"),
        ]
    ),

    # Scene 6: Outcomes
    Scene(
        title="Profit/Loss Scenarios",
        duration_sec=6,
        background_color="#0d1117",
        elements=[
            TextElement("Possible Outcomes", x=960, y=150, font_size=70, anchor="mm", color="#FFD700"),
            TextElement("Stock stays at $150", x=960, y=300, font_size=50, anchor="mm", color="#FFD700"),
            TextElement("Loss: $3 (premium paid)", x=960, y=400, font_size=40, anchor="mm", color="#FF4444"),
            TextElement("Stock rises to $155", x=960, y=550, font_size=50, anchor="mm", color="#00C896"),
            TextElement("Profit: $2 ($155-$150-$3)", x=960, y=650, font_size=40, anchor="mm", color="#00C896"),
            TextElement("Stock rises to $170", x=960, y=800, font_size=50, anchor="mm", color="#00C896"),
            TextElement("Max Profit: $7 (capped at $160-$150-$3)", x=960, y=900, font_size=40, anchor="mm", color="#00C896"),
        ]
    ),

    # Scene 7: When to Use
    Scene(
        title="When to Use",
        duration_sec=4,
        background_color="#0d1117",
        elements=[
            TextElement("When to Use Bull Call Spread", x=960, y=200, font_size=70, anchor="mm", color="#FFD700"),
            TextElement("✓ Mildly bullish outlook", x=960, y=380, font_size=50, anchor="mm", color="#00C896"),
            TextElement("✓ Want to reduce premium cost", x=960, y=520, font_size=50, anchor="mm", color="#00C896"),
            TextElement("✓ Limited risk & reward", x=960, y=660, font_size=50, anchor="mm", color="#00C896"),
            TextElement("✓ Lower capital required", x=960, y=800, font_size=50, anchor="mm", color="#00C896"),
        ]
    ),
]

output = gen.create_video(scenes, "../output/bull-call-spread.mp4")
print(f"✓ Bull Call Spread created: {output}")
```

## Scene Structure Reference

### Basic Text Scene
```python
{
    "title": "Scene Title",
    "duration_sec": 4,
    "bg_color": "#0d1117",
    "text": [
        {
            "text": "Display text",
            "x": 960,           # X position (0-1920)
            "y": 400,           # Y position (0-1080)
            "font_size": 50,    # Font size in pixels
            "color": "#FFFFFF", # Hex color
            "anchor": "mm"      # Position anchor (mm=center)
        }
    ]
}
```

### Advanced with Graphics
```python
Scene(
    title="Graph Scene",
    duration_sec=5,
    background_color="#0d1117",
    elements=[
        # Text
        TextElement("Title", x=960, y=250, font_size=80, anchor="mm", color="#FFD700"),
        
        # Lines (axes, payoff curves)
        LineElement(x1=200, y1=800, x2=1700, y2=800, color="#8B949E", width=3),
        LineElement(x1=200, y1=200, x2=200, y2=800, color="#8B949E", width=3),
        
        # Polygons (shaded areas)
        PolygonElement(
            points=[(200, 800), (600, 600), (1200, 300), (1700, 300), (1700, 800)],
            fill="#00C896",
            outline="#00C896",
            width=2
        ),
    ]
)
```

## Color Palette (Recommended)

```
Background:    #0d1117 (Dark)
Primary:       #FFD700 (Gold)
Danger/Loss:   #FF4444 (Red)
Success/Gain:  #00C896 (Green)
Info:          #58a6ff (Blue)
Muted:         #8B949E (Gray)
Text:          #FFFFFF (White)
Alt Blue:      #38BDF8 (Light Blue)
Alt Red:       #EF4444 (Bright Red)
```

## Position Guide

```
X-axis: 0 (left) → 960 (center) → 1920 (right)
Y-axis: 0 (top) → 540 (center) → 1080 (bottom)

Common positions:
- Title area: y = 150-300
- Main content: y = 400-700
- Bottom labels: y = 900+

Three-column layout:
- Left: x = 350
- Center: x = 960
- Right: x = 1570
```

## Anchor Reference

```
"mm" = middle-middle (center)
"lm" = left-middle
"rm" = right-middle
"mt" = middle-top
"mb" = middle-bottom
"lt" = left-top
"rt" = right-top
"lb" = left-bottom
"rb" = right-bottom
```

## Video Generation Command

```bash
# From examples directory
python your_script.py

# Output goes to output/your-video.mp4
```

## Tips

1. **Timing**: 3-5 sec per scene works best for reading
2. **Text Size**: 50+ for body, 70+ for titles
3. **Graphs**: Keep curves smooth, label clearly
4. **Color**: Use accent colors sparingly (gold/red/green)
5. **Margins**: Leave 150px from edges
6. **Multiple Scenarios**: Create one file per concept

## Common Educational Structures

### Linear Explanation
1. Title/Intro (3 sec)
2. Definition (4-5 sec)
3. Examples (5-7 sec)
4. Summary (3 sec)

### Comparison
1. Title (3 sec)
2. Side-by-side breakdown (5-6 sec each)
3. Key differences (4 sec)
4. When to use (4 sec)

### Strategy Walkthrough
1. Title (3 sec)
2. Setup (4 sec)
3. Risk/Reward (4 sec)
4. Payoff Diagram (5 sec)
5. Real Example (6 sec)
6. When to Use (4 sec)

## Output

All videos saved to: `/Users/amitri/Projects/LTX-Video/simple-video-gen/output/`

Ready to embed in Options Educator platform or standalone use.
