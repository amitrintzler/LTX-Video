#!/usr/bin/env python3
"""Call Option Payoff Diagram with actual visual graphs."""

import sys
sys.path.insert(0, "..")
from video_gen import VideoGenerator, Scene, TextElement, LineElement, PolygonElement

gen = VideoGenerator()

scenes = [
    # Intro
    Scene(
        title="Intro",
        duration_sec=3,
        background_color="#0d1117",
        elements=[
            TextElement("Call Option Payoff", x=960, y=200, font_size=100, anchor="mm", color="#FFD700"),
            TextElement("Visual Diagram", x=960, y=400, font_size=50, anchor="mm", color="#58a6ff"),
        ]
    ),

    # Empty Axes
    Scene(
        title="Setup Axes",
        duration_sec=2,
        background_color="#0d1117",
        elements=[
            # Axis labels
            TextElement("Stock Price ($)", x=200, y=950, font_size=40, anchor="lm", color="#8B949E"),
            TextElement("Profit/Loss ($)", x=50, y=200, font_size=40, anchor="mm", color="#8B949E"),
            # X-axis
            LineElement(150, 850, 1800, 850, color="#8B949E", width=3),
            # Y-axis
            LineElement(150, 150, 150, 850, color="#8B949E", width=3),
            # Strike price line (vertical dashed representation)
            TextElement("Strike: $100", x=600, y=900, font_size=35, anchor="mm", color="#FFD700"),
            LineElement(600, 150, 600, 850, color="#FFD700", width=2),
        ]
    ),

    # Loss zone
    Scene(
        title="Loss Zone",
        duration_sec=3,
        background_color="#0d1117",
        elements=[
            # Axes
            LineElement(150, 850, 1800, 850, color="#8B949E", width=3),
            LineElement(150, 150, 150, 850, color="#8B949E", width=3),
            LineElement(600, 150, 600, 850, color="#FFD700", width=2),
            # Loss line (horizontal at -premium)
            LineElement(150, 750, 600, 750, color="#FF4444", width=4),
            # Labels
            TextElement("Loss Zone", x=300, y=700, font_size=45, anchor="mm", color="#FF4444"),
            TextElement("Stock < Strike", x=350, y=800, font_size=35, anchor="mm", color="#FF4444"),
            TextElement("You lose premium", x=350, y=900, font_size=30, anchor="mm", color="#8B949E"),
        ]
    ),

    # Breakeven point
    Scene(
        title="Breakeven",
        duration_sec=3,
        background_color="#0d1117",
        elements=[
            # Axes
            LineElement(150, 850, 1800, 850, color="#8B949E", width=3),
            LineElement(150, 150, 150, 850, color="#8B949E", width=3),
            LineElement(600, 150, 600, 850, color="#FFD700", width=2),
            # Loss zone
            LineElement(150, 750, 600, 750, color="#FF4444", width=4),
            # Breakeven point
            LineElement(750, 150, 750, 850, color="#FFD700", width=2),
            TextElement("●", x=750, y=850, font_size=40, anchor="mm", color="#FFD700"),
            TextElement("Breakeven", x=750, y=920, font_size=35, anchor="mm", color="#FFD700"),
            TextElement("Strike + Premium", x=750, y=980, font_size=30, anchor="mm", color="#8B949E"),
        ]
    ),

    # Complete payoff curve
    Scene(
        title="Complete Payoff",
        duration_sec=4,
        background_color="#0d1117",
        elements=[
            # Axes
            LineElement(150, 850, 1800, 850, color="#8B949E", width=3),
            LineElement(150, 150, 150, 850, color="#8B949E", width=3),
            # Payoff line: horizontal left, diagonal right
            LineElement(150, 750, 600, 750, color="#FF4444", width=5),
            LineElement(600, 750, 1700, 250, color="#00C896", width=5),
            # Strike & breakeven markers
            LineElement(600, 150, 600, 850, color="#FFD700", width=2),
            LineElement(750, 150, 750, 850, color="#FFD700", width=2),
            # Key points
            TextElement("Strike", x=600, y=920, font_size=30, anchor="mm", color="#FFD700"),
            TextElement("Breakeven", x=750, y=920, font_size=30, anchor="mm", color="#FFD700"),
            # Zones
            TextElement("LOSS", x=350, y=650, font_size=40, anchor="mm", color="#FF4444"),
            TextElement("PROFIT", x=1200, y=450, font_size=40, anchor="mm", color="#00C896"),
        ]
    ),

    # Example with values
    Scene(
        title="Real Example",
        duration_sec=5,
        background_color="#0d1117",
        elements=[
            TextElement("EXAMPLE: Apple Call", x=960, y=150, font_size=70, anchor="mm", color="#FFD700"),
            # Diagram
            LineElement(150, 850, 1800, 850, color="#8B949E", width=3),
            LineElement(150, 150, 150, 850, color="#8B949E", width=3),
            LineElement(150, 750, 600, 750, color="#FF4444", width=5),
            LineElement(600, 750, 1700, 250, color="#00C896", width=5),
            LineElement(600, 150, 600, 850, color="#FFD700", width=2),
            LineElement(750, 150, 750, 850, color="#FFD700", width=2),
            # Values
            TextElement("Strike: $150", x=150, y=400, font_size=40, anchor="lm", color="#FFD700"),
            TextElement("Premium: $5", x=150, y=480, font_size=40, anchor="lm", color="#FF4444"),
            TextElement("Breakeven: $155", x=150, y=560, font_size=40, anchor="lm", color="#FFD700"),
            TextElement("If stock = $170: Profit = $15", x=150, y=700, font_size=40, anchor="lm", color="#00C896"),
        ]
    ),
]

output = gen.create_video(scenes, "../output/call-payoff-visual.mp4")
print(f"✓ Call Payoff Visual created: {output}")
