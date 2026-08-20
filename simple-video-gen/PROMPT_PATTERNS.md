# Prompt Patterns for Video Generation

Copy and modify these patterns to create your own educational videos.

---

## Pattern 1: Strategy Explanation

**Use for**: Explaining any options strategy

```python
#!/usr/bin/env python3
"""[STRATEGY NAME] - [Brief Description]."""

import sys
sys.path.insert(0, "..")
from video_gen import create_simple_video

scenes = [
    {
        "title": "Title",
        "duration_sec": 3,
        "text": [
            {"text": "[STRATEGY NAME]", "x": 960, "y": 250, "font_size": 100, "anchor": "mm", "color": "#FFD700"},
            {"text": "[Tagline]", "x": 960, "y": 450, "font_size": 50, "anchor": "mm", "color": "#58a6ff"},
        ]
    },
    {
        "title": "Definition",
        "duration_sec": 5,
        "text": [
            {"text": "What is [STRATEGY]?", "x": 960, "y": 200, "font_size": 70, "anchor": "mm", "color": "#38BDF8"},
            {"text": "[Action 1]", "x": 960, "y": 350, "font_size": 50, "anchor": "mm", "color": "#FFFFFF"},
            {"text": "[Action 2]", "x": 960, "y": 480, "font_size": 50, "anchor": "mm", "color": "#FFFFFF"},
            {"text": "[Key point]", "x": 960, "y": 650, "font_size": 45, "anchor": "mm", "color": "#FFD700"},
        ]
    },
    {
        "title": "When to Use",
        "duration_sec": 4,
        "text": [
            {"text": "When to Use [STRATEGY]", "x": 960, "y": 200, "font_size": 70, "anchor": "mm", "color": "#FFD700"},
            {"text": "✓ [Condition 1]", "x": 960, "y": 380, "font_size": 50, "anchor": "mm", "color": "#00C896"},
            {"text": "✓ [Condition 2]", "x": 960, "y": 520, "font_size": 50, "anchor": "mm", "color": "#00C896"},
            {"text": "✓ [Condition 3]", "x": 960, "y": 660, "font_size": 50, "anchor": "mm", "color": "#00C896"},
        ]
    },
    {
        "title": "Risk/Reward",
        "duration_sec": 4,
        "text": [
            {"text": "Risk vs Reward", "x": 960, "y": 200, "font_size": 70, "anchor": "mm", "color": "#FFD700"},
            {"text": "Max Loss: [Amount/Limit]", "x": 300, "y": 450, "font_size": 50, "anchor": "mm", "color": "#FF4444"},
            {"text": "[Details]", "x": 300, "y": 580, "font_size": 40, "anchor": "mm", "color": "#8B949E"},
            {"text": "Max Gain: [Amount/Limit]", "x": 1620, "y": 450, "font_size": 50, "anchor": "mm", "color": "#00C896"},
            {"text": "[Details]", "x": 1620, "y": 580, "font_size": 40, "anchor": "mm", "color": "#8B949E"},
        ]
    },
]

output = create_simple_video("[video-name]", scenes)
print(f"✓ Created: {output}")
```

---

## Pattern 2: Concept Definition

**Use for**: Explaining Greeks, risk concepts, pricing factors

```python
{
    "title": "[Concept Name]",
    "duration_sec": 5,
    "text": [
        {"text": "[CONCEPT] ([Symbol])", "x": 960, "y": 200, "font_size": 80, "anchor": "mm", "color": "#38BDF8"},
        {"text": "[One-line definition]", "x": 960, "y": 350, "font_size": 50, "anchor": "mm", "color": "#FFFFFF"},
        {"text": "[How it's measured]", "x": 960, "y": 500, "font_size": 40, "anchor": "mm", "color": "#8B949E"},
        {"text": "[Real world example]", "x": 960, "y": 680, "font_size": 40, "anchor": "mm", "color": "#00C896"},
    ]
},
```

---

## Pattern 3: Side-by-Side Comparison

**Use for**: Call vs Put, different strategies, market conditions

```python
{
    "title": "Comparison",
    "duration_sec": 5,
    "text": [
        {"text": "Option A", "x": 350, "y": 200, "font_size": 60, "anchor": "mm", "color": "#38BDF8"},
        {"text": "[Feature 1]", "x": 350, "y": 350, "font_size": 45, "anchor": "mm", "color": "#FFFFFF"},
        {"text": "[Feature 2]", "x": 350, "y": 450, "font_size": 45, "anchor": "mm", "color": "#FFFFFF"},
        {"text": "[Feature 3]", "x": 350, "y": 550, "font_size": 45, "anchor": "mm", "color": "#FFFFFF"},
        
        {"text": "Option B", "x": 1570, "y": 200, "font_size": 60, "anchor": "mm", "color": "#EF4444"},
        {"text": "[Feature 1]", "x": 1570, "y": 350, "font_size": 45, "anchor": "mm", "color": "#FFFFFF"},
        {"text": "[Feature 2]", "x": 1570, "y": 450, "font_size": 45, "anchor": "mm", "color": "#FFFFFF"},
        {"text": "[Feature 3]", "x": 1570, "y": 550, "font_size": 45, "anchor": "mm", "color": "#FFFFFF"},
    ]
},
```

---

## Pattern 4: Real Number Example

**Use for**: Demonstrating with actual values

```python
{
    "title": "Real Example",
    "duration_sec": 6,
    "text": [
        {"text": "EXAMPLE: [Stock Name]", "x": 960, "y": 150, "font_size": 70, "anchor": "mm", "color": "#FFD700"},
        {"text": "[Setup: Current conditions]", "x": 960, "y": 280, "font_size": 50, "anchor": "mm", "color": "#FFFFFF"},
        
        {"text": "[Action 1]", "x": 300, "y": 450, "font_size": 45, "anchor": "mm", "color": "#38BDF8"},
        {"text": "[Detail 1]", "x": 300, "y": 550, "font_size": 40, "anchor": "mm", "color": "#FFFFFF"},
        {"text": "[Detail 2]", "x": 300, "y": 630, "font_size": 40, "anchor": "mm", "color": "#FFFFFF"},
        
        {"text": "[Action 2]", "x": 1620, "y": 450, "font_size": 45, "anchor": "mm", "color": "#EF4444"},
        {"text": "[Detail 1]", "x": 1620, "y": 550, "font_size": 40, "anchor": "mm", "color": "#FFFFFF"},
        {"text": "[Detail 2]", "x": 1620, "y": 630, "font_size": 40, "anchor": "mm", "color": "#FFFFFF"},
        
        {"text": "[Outcome]", "x": 960, "y": 800, "font_size": 50, "anchor": "mm", "color": "#00C896"},
    ]
},
```

---

## Pattern 5: Payoff Diagram with Graphs

**Use for**: Visual representation of profit/loss

```python
from video_gen import VideoGenerator, Scene, TextElement, LineElement

Scene(
    title="Payoff Diagram",
    duration_sec": 5,
    background_color="#0d1117",
    elements=[
        TextElement("[Strategy] Diagram", x=960, y=150, font_size=70, anchor="mm", color="#FFD700"),
        
        # Axes
        LineElement(200, 700, 1700, 700, color="#8B949E", width=3),  # X-axis
        LineElement(200, 150, 200, 700, color="#8B949E", width=3),  # Y-axis
        
        # Strike markers
        LineElement(500, 150, 500, 700, color="#38BDF8", width=2),
        LineElement(900, 150, 900, 700, color="#EF4444", width=2),
        
        # Payoff line(s)
        LineElement(200, 600, 500, 600, color="#FF4444", width=4),  # Loss zone
        LineElement(500, 600, 900, 400, color="#00C896", width=4),  # Profit zone
        LineElement(900, 400, 1700, 400, color="#FF4444", width=4),  # Capped zone
        
        # Labels
        TextElement("[Strike 1]", x=500, y=730, font_size=35, anchor="mm", color="#38BDF8"),
        TextElement("[Strike 2]", x=900, y=730, font_size=35, anchor="mm", color="#EF4444"),
    ]
)
```

---

## Pattern 6: Step-by-Step Process

**Use for**: Tutorials, execution steps, decision trees

```python
{
    "title": "Step 1: [Action]",
    "duration_sec": 3,
    "text": [
        {"text": "Step 1: [Action]", "x": 960, "y": 300, "font_size": 70, "anchor": "mm", "color": "#FFD700"},
        {"text": "[Explanation]", "x": 960, "y": 500, "font_size": 50, "anchor": "mm", "color": "#FFFFFF"},
    ]
},
{
    "title": "Step 2: [Action]",
    "duration_sec": 3,
    "text": [
        {"text": "Step 2: [Action]", "x": 960, "y": 300, "font_size": 70, "anchor": "mm", "color": "#FFD700"},
        {"text": "[Explanation]", "x": 960, "y": 500, "font_size": 50, "anchor": "mm", "color": "#FFFFFF"},
    ]
},
{
    "title": "Step 3: [Action]",
    "duration_sec": 3,
    "text": [
        {"text": "Step 3: [Action]", "x": 960, "y": 300, "font_size": 70, "anchor": "mm", "color": "#FFD700"},
        {"text": "[Explanation]", "x": 960, "y": 500, "font_size": 50, "anchor": "mm", "color": "#FFFFFF"},
    ]
},
```

---

## Quick Fill-in-the-Blanks Template

```python
#!/usr/bin/env python3
"""[YOUR TOPIC HERE]."""

import sys
sys.path.insert(0, "..")
from video_gen import create_simple_video

scenes = [
    # SCENE 1: INTRO (3-4 seconds)
    {
        "title": "Intro",
        "duration_sec": 3,
        "text": [
            {"text": "[MAIN TITLE]", "x": 960, "y": 300, "font_size": 100, "anchor": "mm", "color": "#FFD700"},
        ]
    },
    
    # SCENE 2: DEFINITION (4-5 seconds)
    {
        "title": "Definition",
        "duration_sec": 5,
        "text": [
            {"text": "[CONCEPT NAME]", "x": 960, "y": 200, "font_size": 70, "anchor": "mm", "color": "#38BDF8"},
            {"text": "[Definition]", "x": 960, "y": 400, "font_size": 50, "anchor": "mm", "color": "#FFFFFF"},
            {"text": "[Key detail]", "x": 960, "y": 550, "font_size": 45, "anchor": "mm", "color": "#8B949E"},
        ]
    },
    
    # SCENE 3: EXAMPLE (5-6 seconds)
    {
        "title": "Example",
        "duration_sec": 6,
        "text": [
            {"text": "Example: [SCENARIO]", "x": 960, "y": 200, "font_size": 70, "anchor": "mm", "color": "#FFD700"},
            {"text": "[Input 1: Value]", "x": 960, "y": 380, "font_size": 50, "anchor": "mm", "color": "#FFFFFF"},
            {"text": "[Input 2: Value]", "x": 960, "y": 520, "font_size": 50, "anchor": "mm", "color": "#FFFFFF"},
            {"text": "[Result: Value]", "x": 960, "y": 700, "font_size": 50, "anchor": "mm", "color": "#00C896"},
        ]
    },
    
    # SCENE 4: SUMMARY (3-4 seconds)
    {
        "title": "Summary",
        "duration_sec": 4,
        "text": [
            {"text": "Key Takeaway", "x": 960, "y": 300, "font_size": 70, "anchor": "mm", "color": "#FFD700"},
            {"text": "[Main point]", "x": 960, "y": 500, "font_size": 50, "anchor": "mm", "color": "#FFFFFF"},
        ]
    },
]

output = create_simple_video("[video-name]", scenes)
print(f"✓ Created: {output}")
```

---

## Usage Instructions

1. **Copy** one of the patterns above
2. **Replace** bracketed sections [LIKE THIS] with your content
3. **Save** as `examples/your-video-name.py`
4. **Run**: `python examples/your-video-name.py`
5. **Output**: `output/your-video-name.mp4`

All videos ready for immediate use!
