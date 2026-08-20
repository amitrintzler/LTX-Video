#!/usr/bin/env python3
"""Call vs Put Comparison - Side-by-side educational breakdown."""

import sys
sys.path.insert(0, "..")
from video_gen import create_simple_video

scenes = [
    {
        "title": "Intro",
        "duration_sec": 3,
        "bg_color": "#0d1117",
        "text": [
            {"text": "Calls vs Puts", "x": 960, "y": 250, "font_size": 100, "anchor": "mm", "color": "#FFD700"},
            {"text": "The Two Basic Options", "x": 960, "y": 450, "font_size": 50, "anchor": "mm", "color": "#58a6ff"},
        ]
    },
    {
        "title": "Call Definition",
        "duration_sec": 4,
        "bg_color": "#0d1117",
        "text": [
            {"text": "CALL OPTION", "x": 400, "y": 250, "font_size": 70, "anchor": "mm", "color": "#38BDF8"},
            {"text": "Right to BUY", "x": 400, "y": 380, "font_size": 55, "anchor": "mm", "color": "#FFFFFF"},
            {"text": "at a fixed price", "x": 400, "y": 500, "font_size": 45, "anchor": "mm", "color": "#8B949E"},
            {"text": "PUT OPTION", "x": 1520, "y": 250, "font_size": 70, "anchor": "mm", "color": "#EF4444"},
            {"text": "Right to SELL", "x": 1520, "y": 380, "font_size": 55, "anchor": "mm", "color": "#FFFFFF"},
            {"text": "at a fixed price", "x": 1520, "y": 500, "font_size": 45, "anchor": "mm", "color": "#8B949E"},
        ]
    },
    {
        "title": "Market Outlook",
        "duration_sec": 4,
        "bg_color": "#0d1117",
        "text": [
            {"text": "CALL", "x": 400, "y": 250, "font_size": 60, "anchor": "mm", "color": "#38BDF8"},
            {"text": "BULLISH 📈", "x": 400, "y": 380, "font_size": 50, "anchor": "mm", "color": "#00C896"},
            {"text": "Bet on price UP", "x": 400, "y": 500, "font_size": 40, "anchor": "mm", "color": "#FFFFFF"},
            {"text": "PUT", "x": 1520, "y": 250, "font_size": 60, "anchor": "mm", "color": "#EF4444"},
            {"text": "BEARISH 📉", "x": 1520, "y": 380, "font_size": 50, "anchor": "mm", "color": "#FF6B6B"},
            {"text": "Bet on price DOWN", "x": 1520, "y": 500, "font_size": 40, "anchor": "mm", "color": "#FFFFFF"},
        ]
    },
    {
        "title": "When You Profit",
        "duration_sec": 4,
        "bg_color": "#0d1117",
        "text": [
            {"text": "CALL Profit", "x": 400, "y": 250, "font_size": 55, "anchor": "mm", "color": "#38BDF8"},
            {"text": "Stock rises above strike", "x": 400, "y": 400, "font_size": 40, "anchor": "mm", "color": "#FFFFFF"},
            {"text": "Higher price = More profit", "x": 400, "y": 520, "font_size": 40, "anchor": "mm", "color": "#00C896"},
            {"text": "PUT Profit", "x": 1520, "y": 250, "font_size": 55, "anchor": "mm", "color": "#EF4444"},
            {"text": "Stock falls below strike", "x": 1520, "y": 400, "font_size": 40, "anchor": "mm", "color": "#FFFFFF"},
            {"text": "Lower price = More profit", "x": 1520, "y": 520, "font_size": 40, "anchor": "mm", "color": "#FF6B6B"},
        ]
    },
    {
        "title": "Use Cases",
        "duration_sec": 5,
        "bg_color": "#0d1117",
        "text": [
            {"text": "CALL Use Cases", "x": 400, "y": 200, "font_size": 55, "anchor": "mm", "color": "#38BDF8"},
            {"text": "▪ Bet on growth", "x": 400, "y": 350, "font_size": 40, "anchor": "mm", "color": "#FFFFFF"},
            {"text": "▪ Own stock cheaper", "x": 400, "y": 480, "font_size": 40, "anchor": "mm", "color": "#FFFFFF"},
            {"text": "▪ Generate income", "x": 400, "y": 610, "font_size": 40, "anchor": "mm", "color": "#FFFFFF"},
            {"text": "PUT Use Cases", "x": 1520, "y": 200, "font_size": 55, "anchor": "mm", "color": "#EF4444"},
            {"text": "▪ Protect portfolio", "x": 1520, "y": 350, "font_size": 40, "anchor": "mm", "color": "#FFFFFF"},
            {"text": "▪ Bet on decline", "x": 1520, "y": 480, "font_size": 40, "anchor": "mm", "color": "#FFFFFF"},
            {"text": "▪ Cheap entry point", "x": 1520, "y": 610, "font_size": 40, "anchor": "mm", "color": "#FFFFFF"},
        ]
    },
    {
        "title": "Risk Profile",
        "duration_sec": 4,
        "bg_color": "#0d1117",
        "text": [
            {"text": "CALL Risk", "x": 400, "y": 300, "font_size": 55, "anchor": "mm", "color": "#38BDF8"},
            {"text": "Loss: Premium paid", "x": 400, "y": 450, "font_size": 40, "anchor": "mm", "color": "#FF4444"},
            {"text": "Gain: Unlimited ∞", "x": 400, "y": 600, "font_size": 40, "anchor": "mm", "color": "#00C896"},
            {"text": "PUT Risk", "x": 1520, "y": 300, "font_size": 55, "anchor": "mm", "color": "#EF4444"},
            {"text": "Loss: Premium paid", "x": 1520, "y": 450, "font_size": 40, "anchor": "mm", "color": "#FF4444"},
            {"text": "Gain: Capped at strike", "x": 1520, "y": 600, "font_size": 40, "anchor": "mm", "color": "#00C896"},
        ]
    }
]

output = create_simple_video("call-vs-put", scenes, output_path="../output/call-vs-put.mp4")
print(f"✓ Call vs Put comparison created: {output}")
