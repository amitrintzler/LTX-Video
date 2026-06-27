#!/usr/bin/env python3
"""Example: Create a put option tutorial video."""

import sys
sys.path.insert(0, "..")

from video_gen import create_simple_video

scenes = [
    {
        "title": "Title",
        "duration_sec": 3,
        "bg_color": "#0d1117",
        "text": [
            {"text": "Put Option Basics", "x": 960, "y": 250, "font_size": 100, "anchor": "mm", "color": "#FFD700"},
        ]
    },
    {
        "title": "Definition",
        "duration_sec": 5,
        "bg_color": "#0d1117",
        "text": [
            {"text": "What is a Put Option?", "x": 960, "y": 300, "font_size": 70, "anchor": "mm", "color": "#58a6ff"},
            {"text": "The right to SELL a stock at a fixed price", "x": 960, "y": 500, "font_size": 50, "anchor": "mm", "color": "#FFFFFF"},
            {"text": "Fixed Price = Strike Price", "x": 960, "y": 650, "font_size": 45, "anchor": "mm", "color": "#8B949E"},
        ]
    },
    {
        "title": "Protection",
        "duration_sec": 6,
        "bg_color": "#0d1117",
        "text": [
            {"text": "Why Buy a Put?", "x": 960, "y": 280, "font_size": 70, "anchor": "mm", "color": "#58a6ff"},
            {"text": "Protects your stock from falling prices", "x": 400, "y": 500, "font_size": 45, "anchor": "mm", "color": "#00C896"},
            {"text": "Like insurance on your portfolio", "x": 1520, "y": 500, "font_size": 45, "anchor": "mm", "color": "#FFD700"},
            {"text": "You pay a small premium", "x": 960, "y": 700, "font_size": 40, "anchor": "mm", "color": "#FF4444"},
        ]
    },
    {
        "title": "Example",
        "duration_sec": 7,
        "bg_color": "#0d1117",
        "text": [
            {"text": "Example: Put at Strike $50", "x": 960, "y": 250, "font_size": 70, "anchor": "mm", "color": "#58a6ff"},
            {"text": "Stock Price Falls to $40", "x": 960, "y": 450, "font_size": 55, "anchor": "mm", "color": "#FF4444"},
            {"text": "You Exercise Put: Sell at $50", "x": 960, "y": 600, "font_size": 55, "anchor": "mm", "color": "#00C896"},
            {"text": "Profit: $10 per share", "x": 960, "y": 750, "font_size": 55, "anchor": "mm", "color": "#FFD700"},
        ]
    }
]

output = create_simple_video("put-option-tutorial", scenes, output_path="../output/put-option-tutorial.mp4")
print(f"✓ Video created: {output}")
