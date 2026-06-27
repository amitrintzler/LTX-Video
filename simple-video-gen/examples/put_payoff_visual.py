#!/usr/bin/env python3
"""Put Option Payoff Diagram - Inverted V shape."""

import sys
sys.path.insert(0, "..")
from video_gen import VideoGenerator, Scene, TextElement, LineElement, PolygonElement

gen = VideoGenerator()

scenes = [
    Scene(
        title="Intro",
        duration_sec=3,
        background_color="#0d1117",
        elements=[
            TextElement("Put Option Payoff", x=960, y=200, font_size=100, anchor="mm", color="#FF4444"),
            TextElement("Insurance Strategy", x=960, y=400, font_size=50, anchor="mm", color="#58a6ff"),
        ]
    ),

    Scene(
        title="Axes",
        duration_sec=2,
        background_color="#0d1117",
        elements=[
            TextElement("Stock Price ($)", x=200, y=950, font_size=40, anchor="lm", color="#8B949E"),
            TextElement("Profit/Loss ($)", x=50, y=200, font_size=40, anchor="mm", color="#8B949E"),
            LineElement(150, 850, 1800, 850, color="#8B949E", width=3),
            LineElement(150, 150, 150, 850, color="#8B949E", width=3),
            TextElement("Strike: $100", x=600, y=900, font_size=35, anchor="mm", color="#FFD700"),
            LineElement(600, 150, 600, 850, color="#FFD700", width=2),
        ]
    ),

    Scene(
        title="Profit Zone",
        duration_sec=3,
        background_color="#0d1117",
        elements=[
            LineElement(150, 850, 1800, 850, color="#8B949E", width=3),
            LineElement(150, 150, 150, 850, color="#8B949E", width=3),
            LineElement(600, 150, 600, 850, color="#FFD700", width=2),
            # Profit line (upward to the left of strike)
            LineElement(150, 250, 600, 750, color="#00C896", width=4),
            TextElement("Profit Zone", x=300, y=450, font_size=45, anchor="mm", color="#00C896"),
            TextElement("Stock < Strike", x=300, y=800, font_size=35, anchor="mm", color="#00C896"),
        ]
    ),

    Scene(
        title="Breakeven",
        duration_sec=3,
        background_color="#0d1117",
        elements=[
            LineElement(150, 850, 1800, 850, color="#8B949E", width=3),
            LineElement(150, 150, 150, 850, color="#8B949E", width=3),
            LineElement(600, 150, 600, 850, color="#FFD700", width=2),
            LineElement(150, 250, 600, 750, color="#00C896", width=4),
            # Breakeven marker
            LineElement(450, 150, 450, 850, color="#FFD700", width=2),
            TextElement("●", x=450, y=850, font_size=40, anchor="mm", color="#FFD700"),
            TextElement("Breakeven", x=450, y=920, font_size=35, anchor="mm", color="#FFD700"),
        ]
    ),

    Scene(
        title="Loss Zone",
        duration_sec=3,
        background_color="#0d1117",
        elements=[
            LineElement(150, 850, 1800, 850, color="#8B949E", width=3),
            LineElement(150, 150, 150, 850, color="#8B949E", width=3),
            LineElement(600, 150, 600, 850, color="#FFD700", width=2),
            LineElement(150, 250, 600, 750, color="#00C896", width=4),
            # Loss zone (horizontal at -premium to the right)
            LineElement(600, 750, 1700, 750, color="#FF4444", width=4),
            TextElement("LOSS ZONE", x=1200, y=650, font_size=40, anchor="mm", color="#FF4444"),
            TextElement("Stock > Strike", x=1200, y=800, font_size=35, anchor="mm", color="#FF4444"),
        ]
    ),

    Scene(
        title="Complete Payoff",
        duration_sec=4,
        background_color="#0d1117",
        elements=[
            LineElement(150, 850, 1800, 850, color="#8B949E", width=3),
            LineElement(150, 150, 150, 850, color="#8B949E", width=3),
            # Complete payoff: diagonal left, horizontal right
            LineElement(150, 250, 600, 750, color="#00C896", width=5),
            LineElement(600, 750, 1700, 750, color="#FF4444", width=5),
            LineElement(600, 150, 600, 850, color="#FFD700", width=2),
            LineElement(450, 150, 450, 850, color="#FFD700", width=2),
            # Zone labels
            TextElement("PROFIT", x=300, y=550, font_size=40, anchor="mm", color="#00C896"),
            TextElement("LOSS", x=1200, y=650, font_size=40, anchor="mm", color="#FF4444"),
            TextElement("Strike $100", x=600, y=920, font_size=30, anchor="mm", color="#FFD700"),
        ]
    ),

    Scene(
        title="Real Example",
        duration_sec=5,
        background_color="#0d1117",
        elements=[
            TextElement("EXAMPLE: Apple Put", x=960, y=150, font_size=70, anchor="mm", color="#FF4444"),
            # Diagram
            LineElement(150, 850, 1800, 850, color="#8B949E", width=3),
            LineElement(150, 150, 150, 850, color="#8B949E", width=3),
            LineElement(150, 250, 600, 750, color="#00C896", width=5),
            LineElement(600, 750, 1700, 750, color="#FF4444", width=5),
            LineElement(600, 150, 600, 850, color="#FFD700", width=2),
            # Values on left
            TextElement("Strike: $100", x=150, y=400, font_size=40, anchor="lm", color="#FFD700"),
            TextElement("Premium: $4", x=150, y=480, font_size=40, anchor="lm", color="#FF4444"),
            TextElement("Breakeven: $96", x=150, y=560, font_size=40, anchor="lm", color="#FFD700"),
            TextElement("If stock = $80: Profit = $16", x=150, y=700, font_size=40, anchor="lm", color="#00C896"),
            TextElement("Max gain: $96 (strike - premium)", x=150, y=780, font_size=35, anchor="lm", color="#00C896"),
        ]
    ),

    Scene(
        title="Why Use Puts",
        duration_sec=4,
        background_color="#0d1117",
        elements=[
            TextElement("Why Buy Puts?", x=960, y=200, font_size=80, anchor="mm", color="#FF4444"),
            TextElement("Portfolio Insurance", x=400, y=450, font_size=50, anchor="mm", color="#00C896"),
            TextElement("Protects from", x=400, y=550, font_size=40, anchor="mm", color="#FFFFFF"),
            TextElement("large losses", x=400, y=600, font_size=40, anchor="mm", color="#FFFFFF"),
            TextElement("Bet on Decline", x=1520, y=450, font_size=50, anchor="mm", color="#FF6B6B"),
            TextElement("Profit when", x=1520, y=550, font_size=40, anchor="mm", color="#FFFFFF"),
            TextElement("stock falls", x=1520, y=600, font_size=40, anchor="mm", color="#FFFFFF"),
        ]
    )
]

output = gen.create_video(scenes, "../output/put-payoff-visual.mp4")
print(f"✓ Put Payoff Visual created: {output}")
