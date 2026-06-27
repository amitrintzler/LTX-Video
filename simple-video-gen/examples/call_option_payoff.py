#!/usr/bin/env python3
"""Call Option Payoff Diagram - Visual explanation with profit/loss zones."""

import sys
sys.path.insert(0, "..")
from video_gen import create_simple_video

scenes = [
    {
        "title": "Call Option Intro",
        "duration_sec": 4,
        "bg_color": "#0d1117",
        "text": [
            {"text": "Call Option Payoff Diagram", "x": 960, "y": 200, "font_size": 90, "anchor": "mm", "color": "#FFD700"},
            {"text": "Understanding Profit and Loss", "x": 960, "y": 400, "font_size": 50, "anchor": "mm", "color": "#58a6ff"},
        ]
    },
    {
        "title": "Definition",
        "duration_sec": 5,
        "bg_color": "#0d1117",
        "text": [
            {"text": "Call Option = Right to BUY at a fixed price", "x": 960, "y": 300, "font_size": 55, "anchor": "mm", "color": "#FFFFFF"},
            {"text": "Strike Price (K)", "x": 400, "y": 500, "font_size": 45, "anchor": "mm", "color": "#FFD700"},
            {"text": "The price you agreed to pay", "x": 400, "y": 600, "font_size": 35, "anchor": "mm", "color": "#8B949E"},
            {"text": "Premium", "x": 1520, "y": 500, "font_size": 45, "anchor": "mm", "color": "#FF4444"},
            {"text": "Cost of buying the call", "x": 1520, "y": 600, "font_size": 35, "anchor": "mm", "color": "#8B949E"},
        ]
    },
    {
        "title": "Loss Zone",
        "duration_sec": 4,
        "bg_color": "#0d1117",
        "text": [
            {"text": "Stock < Strike Price", "x": 960, "y": 250, "font_size": 60, "anchor": "mm", "color": "#FF4444"},
            {"text": "You DON'T exercise the call", "x": 960, "y": 400, "font_size": 45, "anchor": "mm", "color": "#FFFFFF"},
            {"text": "You lose the premium you paid", "x": 960, "y": 550, "font_size": 45, "anchor": "mm", "color": "#FF4444"},
            {"text": "Example: Strike $100, Stock at $90", "x": 960, "y": 700, "font_size": 40, "anchor": "mm", "color": "#8B949E"},
        ]
    },
    {
        "title": "Breakeven",
        "duration_sec": 4,
        "bg_color": "#0d1117",
        "text": [
            {"text": "Breakeven Point", "x": 960, "y": 300, "font_size": 60, "anchor": "mm", "color": "#FFD700"},
            {"text": "Stock Price = Strike Price + Premium", "x": 960, "y": 450, "font_size": 50, "anchor": "mm", "color": "#FFFFFF"},
            {"text": "Example: Strike $100 + Premium $5 = $105", "x": 960, "y": 650, "font_size": 40, "anchor": "mm", "color": "#FFD700"},
        ]
    },
    {
        "title": "Profit Zone",
        "duration_sec": 5,
        "bg_color": "#0d1117",
        "text": [
            {"text": "Stock > Breakeven", "x": 960, "y": 250, "font_size": 60, "anchor": "mm", "color": "#00C896"},
            {"text": "You exercise the call & make profit", "x": 960, "y": 400, "font_size": 45, "anchor": "mm", "color": "#FFFFFF"},
            {"text": "Profit = Stock Price - Strike - Premium", "x": 960, "y": 550, "font_size": 45, "anchor": "mm", "color": "#00C896"},
            {"text": "Example: Stock $120 - $100 - $5 = $15 profit", "x": 960, "y": 700, "font_size": 40, "anchor": "mm", "color": "#00C896"},
        ]
    },
    {
        "title": "Risk vs Reward",
        "duration_sec": 5,
        "bg_color": "#0d1117",
        "text": [
            {"text": "Call Option Risk/Reward", "x": 960, "y": 200, "font_size": 70, "anchor": "mm", "color": "#58a6ff"},
            {"text": "Max Loss", "x": 300, "y": 450, "font_size": 50, "anchor": "mm", "color": "#FF4444"},
            {"text": "Premium Only", "x": 300, "y": 550, "font_size": 40, "anchor": "mm", "color": "#8B949E"},
            {"text": "Max Gain", "x": 1620, "y": 450, "font_size": 50, "anchor": "mm", "color": "#00C896"},
            {"text": "Unlimited ∞", "x": 1620, "y": 550, "font_size": 40, "anchor": "mm", "color": "#8B949E"},
            {"text": "Bullish Strategy: Profit when stock rises", "x": 960, "y": 750, "font_size": 45, "anchor": "mm", "color": "#FFFFFF"},
        ]
    }
]

output = create_simple_video("call-option-payoff", scenes, output_path="../output/call-option-payoff.mp4")
print(f"✓ Call Option Payoff created: {output}")
