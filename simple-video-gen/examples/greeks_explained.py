#!/usr/bin/env python3
"""The Greeks - Delta, Gamma, Theta, Vega, Rho explained with real-world analogies."""

import sys
sys.path.insert(0, "..")
from video_gen import create_simple_video

scenes = [
    {
        "title": "Intro",
        "duration_sec": 3,
        "bg_color": "#0d1117",
        "text": [
            {"text": "The Greeks", "x": 960, "y": 250, "font_size": 100, "anchor": "mm", "color": "#FFD700"},
            {"text": "How Options Change in Value", "x": 960, "y": 450, "font_size": 50, "anchor": "mm", "color": "#58a6ff"},
        ]
    },
    {
        "title": "Delta Overview",
        "duration_sec": 5,
        "bg_color": "#0d1117",
        "text": [
            {"text": "DELTA (Δ)", "x": 960, "y": 200, "font_size": 80, "anchor": "mm", "color": "#38BDF8"},
            {"text": "How much option price changes when stock moves $1", "x": 960, "y": 350, "font_size": 50, "anchor": "mm", "color": "#FFFFFF"},
            {"text": "Range: 0 to 1 for calls, -1 to 0 for puts", "x": 960, "y": 500, "font_size": 40, "anchor": "mm", "color": "#8B949E"},
            {"text": "Example: Delta 0.50 means +$0.50 gain if stock rises $1", "x": 960, "y": 680, "font_size": 40, "anchor": "mm", "color": "#00C896"},
        ]
    },
    {
        "title": "Theta Overview",
        "duration_sec": 5,
        "bg_color": "#0d1117",
        "text": [
            {"text": "THETA (Θ)", "x": 960, "y": 200, "font_size": 80, "anchor": "mm", "color": "#EF4444"},
            {"text": "How much option loses value each day", "x": 960, "y": 350, "font_size": 50, "anchor": "mm", "color": "#FFFFFF"},
            {"text": "Time decay: Options expire worthless", "x": 960, "y": 500, "font_size": 40, "anchor": "mm", "color": "#8B949E"},
            {"text": "Example: Theta -0.05 means -$0.05 loss per day", "x": 960, "y": 680, "font_size": 40, "anchor": "mm", "color": "#FF6B6B"},
        ]
    },
    {
        "title": "Gamma Overview",
        "duration_sec": 5,
        "bg_color": "#0d1117",
        "text": [
            {"text": "GAMMA (Γ)", "x": 960, "y": 200, "font_size": 80, "anchor": "mm", "color": "#FFD700"},
            {"text": "How much Delta changes when stock moves", "x": 960, "y": 350, "font_size": 50, "anchor": "mm", "color": "#FFFFFF"},
            {"text": "Gamma = Delta's Delta (acceleration of gains)", "x": 960, "y": 500, "font_size": 40, "anchor": "mm", "color": "#8B949E"},
            {"text": "Higher gamma = more violent price swings", "x": 960, "y": 680, "font_size": 40, "anchor": "mm", "color": "#FFD700"},
        ]
    },
    {
        "title": "Vega Overview",
        "duration_sec": 5,
        "bg_color": "#0d1117",
        "text": [
            {"text": "VEGA (ν)", "x": 960, "y": 200, "font_size": 80, "anchor": "mm", "color": "#A78BFA"},
            {"text": "How much option price changes with volatility", "x": 960, "y": 350, "font_size": 50, "anchor": "mm", "color": "#FFFFFF"},
            {"text": "High volatility = Higher option prices", "x": 960, "y": 500, "font_size": 40, "anchor": "mm", "color": "#8B949E"},
            {"text": "Example: Vega 0.15 means +$0.15 if volatility rises 1%", "x": 960, "y": 680, "font_size": 40, "anchor": "mm", "color": "#A78BFA"},
        ]
    },
    {
        "title": "Rho Overview",
        "duration_sec": 4,
        "bg_color": "#0d1117",
        "text": [
            {"text": "RHO (ρ)", "x": 960, "y": 200, "font_size": 80, "anchor": "mm", "color": "#00C896"},
            {"text": "How much option price changes with interest rates", "x": 960, "y": 350, "font_size": 50, "anchor": "mm", "color": "#FFFFFF"},
            {"text": "Less important than Delta, Theta, Vega", "x": 960, "y": 500, "font_size": 40, "anchor": "mm", "color": "#8B949E"},
            {"text": "Mostly affects long-term options", "x": 960, "y": 650, "font_size": 40, "anchor": "mm", "color": "#00C896"},
        ]
    },
    {
        "title": "Greeks Summary",
        "duration_sec": 6,
        "bg_color": "#0d1117",
        "text": [
            {"text": "The Greeks Cheat Sheet", "x": 960, "y": 150, "font_size": 70, "anchor": "mm", "color": "#FFD700"},
            {"text": "Δ Delta:  Price sensitivity", "x": 200, "y": 320, "font_size": 40, "anchor": "lm", "color": "#38BDF8"},
            {"text": "Θ Theta:  Time decay", "x": 200, "y": 420, "font_size": 40, "anchor": "lm", "color": "#EF4444"},
            {"text": "Γ Gamma:  Delta acceleration", "x": 200, "y": 520, "font_size": 40, "anchor": "lm", "color": "#FFD700"},
            {"text": "ν Vega:   Volatility impact", "x": 200, "y": 620, "font_size": 40, "anchor": "lm", "color": "#A78BFA"},
            {"text": "ρ Rho:    Interest rate impact", "x": 200, "y": 720, "font_size": 40, "anchor": "lm", "color": "#00C896"},
            {"text": "Master these = Master options trading", "x": 960, "y": 850, "font_size": 45, "anchor": "mm", "color": "#FFFFFF"},
        ]
    }
]

output = create_simple_video("greeks-explained", scenes, output_path="../output/greeks-explained.mp4")
print(f"✓ Greeks Explained created: {output}")
