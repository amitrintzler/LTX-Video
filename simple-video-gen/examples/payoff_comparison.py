#!/usr/bin/env python3
"""Call vs Put Payoff Comparison - Side by side diagrams."""

import sys
sys.path.insert(0, "..")
from video_gen import VideoGenerator, Scene, TextElement, LineElement

gen = VideoGenerator()

scenes = [
    Scene(
        title="Comparison Intro",
        duration_sec=3,
        background_color="#0d1117",
        elements=[
            TextElement("Call vs Put Payoff", x=960, y=250, font_size=90, anchor="mm", color="#FFD700"),
            TextElement("Side-by-Side Comparison", x=960, y=400, font_size=50, anchor="mm", color="#58a6ff"),
        ]
    ),

    Scene(
        title="Call Payoff",
        duration_sec=4,
        background_color="#0d1117",
        elements=[
            TextElement("CALL PAYOFF", x=400, y=100, font_size=60, anchor="mm", color="#38BDF8"),
            # Left diagram axes
            LineElement(200, 650, 600, 650, color="#8B949E", width=2),
            LineElement(200, 250, 200, 650, color="#8B949E", width=2),
            # Call payoff
            LineElement(200, 550, 350, 550, color="#FF4444", width=3),
            LineElement(350, 550, 600, 300, color="#00C896", width=3),
            LineElement(350, 250, 350, 650, color="#FFD700", width=1),
            # Labels
            TextElement("L-Shaped", x=400, y=700, font_size=40, anchor="mm", color="#FFFFFF"),
            TextElement("Breakeven ↑", x=350, y=230, font_size=30, anchor="mm", color="#FFD700"),

            # Right diagram for put
            TextElement("PUT PAYOFF", x=1520, y=100, font_size=60, anchor="mm", color="#EF4444"),
            # Right diagram axes
            LineElement(1320, 650, 1720, 650, color="#8B949E", width=2),
            LineElement(1320, 250, 1320, 650, color="#8B949E", width=2),
            # Put payoff
            LineElement(1320, 300, 1470, 550, color="#00C896", width=3),
            LineElement(1470, 550, 1720, 550, color="#FF4444", width=3),
            LineElement(1470, 250, 1470, 650, color="#FFD700", width=1),
            # Labels
            TextElement("Inverted V", x=1520, y=700, font_size=40, anchor="mm", color="#FFFFFF"),
            TextElement("Breakeven ↓", x=1470, y=230, font_size=30, anchor="mm", color="#FFD700"),
        ]
    ),

    Scene(
        title="Key Differences",
        duration_sec=5,
        background_color="#0d1117",
        elements=[
            TextElement("Key Differences", x=960, y=150, font_size=80, anchor="mm", color="#FFD700"),

            TextElement("CALL", x=350, y=300, font_size=55, anchor="mm", color="#38BDF8"),
            TextElement("Unlimited profit", x=350, y=420, font_size=40, anchor="mm", color="#00C896"),
            TextElement("Limited loss (premium)", x=350, y=500, font_size=40, anchor="mm", color="#FF4444"),
            TextElement("Bullish outlook", x=350, y=600, font_size=40, anchor="mm", color="#FFFFFF"),

            TextElement("PUT", x=1570, y=300, font_size=55, anchor="mm", color="#EF4444"),
            TextElement("Limited profit (strike - premium)", x=1570, y=420, font_size=40, anchor="mm", color="#00C896"),
            TextElement("Limited loss (premium)", x=1570, y=500, font_size=40, anchor="mm", color="#FF4444"),
            TextElement("Bearish outlook", x=1570, y=600, font_size=40, anchor="mm", color="#FFFFFF"),
        ]
    ),

    Scene(
        title="Mirror Image",
        duration_sec=4,
        background_color="#0d1117",
        elements=[
            TextElement("They're Mirror Images", x=960, y=150, font_size=70, anchor="mm", color="#FFD700"),
            TextElement("Around the strike price", x=960, y=280, font_size=50, anchor="mm", color="#58a6ff"),

            # Combined diagram
            LineElement(400, 600, 1520, 600, color="#8B949E", width=2),
            LineElement(400, 200, 400, 600, color="#8B949E", width=2),

            # Call line
            LineElement(400, 500, 700, 500, color="#38BDF8", width=3),
            LineElement(700, 500, 1520, 250, color="#38BDF8", width=3),

            # Put line
            LineElement(400, 250, 700, 500, color="#EF4444", width=3),
            LineElement(700, 500, 1520, 500, color="#EF4444", width=3),

            LineElement(700, 200, 700, 600, color="#FFD700", width=2),

            # Labels
            TextElement("Strike", x=700, y=650, font_size=35, anchor="mm", color="#FFD700"),
            TextElement("Call (L-shape)", x=1000, y=350, font_size=35, anchor="mm", color="#38BDF8"),
            TextElement("Put (V-shape)", x=600, y=350, font_size=35, anchor="mm", color="#EF4444"),
        ]
    ),

    Scene(
        title="Choose Your Strategy",
        duration_sec=5,
        background_color="#0d1117",
        elements=[
            TextElement("Choose Based on Outlook", x=960, y=150, font_size=70, anchor="mm", color="#FFD700"),

            TextElement("CALL if", x=350, y=350, font_size=55, anchor="mm", color="#38BDF8"),
            TextElement("📈 Stock will rise", x=350, y=470, font_size=45, anchor="mm", color="#FFFFFF"),
            TextElement("You expect gains", x=350, y=550, font_size=40, anchor="mm", color="#00C896"),
            TextElement("Risk: Premium only", x=350, y=650, font_size=35, anchor="mm", color="#FF4444"),

            TextElement("PUT if", x=1570, y=350, font_size=55, anchor="mm", color="#EF4444"),
            TextElement("📉 Stock will fall", x=1570, y=470, font_size=45, anchor="mm", color="#FFFFFF"),
            TextElement("Protect your portfolio", x=1570, y=550, font_size=40, anchor="mm", color="#00C896"),
            TextElement("Risk: Premium only", x=1570, y=650, font_size=35, anchor="mm", color="#FF4444"),
        ]
    ),
]

output = gen.create_video(scenes, "../output/payoff-comparison.mp4")
print(f"✓ Payoff Comparison created: {output}")
