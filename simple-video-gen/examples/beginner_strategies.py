#!/usr/bin/env python3
"""Beginner Options Strategies - Long Call, Long Put, and Covered Call."""

import sys
sys.path.insert(0, "..")
from video_gen import create_simple_video

scenes = [
    {
        "title": "Intro",
        "duration_sec": 3,
        "bg_color": "#0d1117",
        "text": [
            {"text": "Beginner Options Strategies", "x": 960, "y": 250, "font_size": 90, "anchor": "mm", "color": "#FFD700"},
            {"text": "3 strategies to start with", "x": 960, "y": 450, "font_size": 50, "anchor": "mm", "color": "#58a6ff"},
        ]
    },
    {
        "title": "Long Call",
        "duration_sec": 5,
        "bg_color": "#0d1117",
        "text": [
            {"text": "Strategy 1: LONG CALL", "x": 960, "y": 200, "font_size": 70, "anchor": "mm", "color": "#38BDF8"},
            {"text": "What: Buy a call option", "x": 960, "y": 350, "font_size": 45, "anchor": "mm", "color": "#FFFFFF"},
            {"text": "Outlook: Bullish (expect stock to rise)", "x": 960, "y": 480, "font_size": 45, "anchor": "mm", "color": "#00C896"},
            {"text": "Max Loss: Premium paid", "x": 960, "y": 610, "font_size": 45, "anchor": "mm", "color": "#FF4444"},
            {"text": "Max Gain: Unlimited ∞", "x": 960, "y": 740, "font_size": 45, "anchor": "mm", "color": "#00C896"},
        ]
    },
    {
        "title": "Long Put",
        "duration_sec": 5,
        "bg_color": "#0d1117",
        "text": [
            {"text": "Strategy 2: LONG PUT", "x": 960, "y": 200, "font_size": 70, "anchor": "mm", "color": "#EF4444"},
            {"text": "What: Buy a put option", "x": 960, "y": 350, "font_size": 45, "anchor": "mm", "color": "#FFFFFF"},
            {"text": "Outlook: Bearish (expect stock to fall)", "x": 960, "y": 480, "font_size": 45, "anchor": "mm", "color": "#FF6B6B"},
            {"text": "Max Loss: Premium paid", "x": 960, "y": 610, "font_size": 45, "anchor": "mm", "color": "#FF4444"},
            {"text": "Max Gain: Strike price minus premium", "x": 960, "y": 740, "font_size": 45, "anchor": "mm", "color": "#00C896"},
        ]
    },
    {
        "title": "Covered Call",
        "duration_sec": 5,
        "bg_color": "#0d1117",
        "text": [
            {"text": "Strategy 3: COVERED CALL", "x": 960, "y": 200, "font_size": 70, "anchor": "mm", "color": "#A78BFA"},
            {"text": "What: Own stock + Sell a call", "x": 960, "y": 350, "font_size": 45, "anchor": "mm", "color": "#FFFFFF"},
            {"text": "Outlook: Neutral to slightly bullish", "x": 960, "y": 480, "font_size": 45, "anchor": "mm", "color": "#FFD700"},
            {"text": "Why: Generate income from stock you own", "x": 960, "y": 610, "font_size": 45, "anchor": "mm", "color": "#58a6ff"},
            {"text": "Benefit: Premium keeps you, stock called away", "x": 960, "y": 740, "font_size": 40, "anchor": "mm", "color": "#8B949E"},
        ]
    },
    {
        "title": "Long Call Example",
        "duration_sec": 6,
        "bg_color": "#0d1117",
        "text": [
            {"text": "Long Call: Real Example", "x": 960, "y": 180, "font_size": 70, "anchor": "mm", "color": "#38BDF8"},
            {"text": "Apple stock: $150", "x": 960, "y": 320, "font_size": 45, "anchor": "mm", "color": "#FFFFFF"},
            {"text": "Buy Call: Strike $155, Premium $3", "x": 960, "y": 420, "font_size": 45, "anchor": "mm", "color": "#FFFFFF"},
            {"text": "Scenario 1: Stock rises to $160", "x": 200, "y": 560, "font_size": 40, "anchor": "lm", "color": "#00C896"},
            {"text": "Gain: ($160 - $155) - $3 = $2 profit", "x": 200, "y": 630, "font_size": 40, "anchor": "lm", "color": "#00C896"},
            {"text": "Scenario 2: Stock falls to $140", "x": 200, "y": 730, "font_size": 40, "anchor": "lm", "color": "#FF4444"},
            {"text": "Loss: Premium $3 (option expires worthless)", "x": 200, "y": 800, "font_size": 40, "anchor": "lm", "color": "#FF4444"},
        ]
    },
    {
        "title": "Covered Call Example",
        "duration_sec": 6,
        "bg_color": "#0d1117",
        "text": [
            {"text": "Covered Call: Real Example", "x": 960, "y": 180, "font_size": 70, "anchor": "mm", "color": "#A78BFA"},
            {"text": "Own 100 Apple shares @ $150 each", "x": 960, "y": 320, "font_size": 45, "anchor": "mm", "color": "#FFFFFF"},
            {"text": "Sell Call: Strike $160, Premium $2", "x": 960, "y": 420, "font_size": 45, "anchor": "mm", "color": "#FFFFFF"},
            {"text": "Scenario: Stock stays at $150", "x": 200, "y": 560, "font_size": 40, "anchor": "lm", "color": "#FFD700"},
            {"text": "You keep: $200 premium (no gain)", "x": 200, "y": 630, "font_size": 40, "anchor": "lm", "color": "#FFD700"},
            {"text": "Scenario: Stock rises to $165", "x": 200, "y": 730, "font_size": 40, "anchor": "lm", "color": "#00C896"},
            {"text": "Stock called away @ $160 + $200 premium", "x": 200, "y": 800, "font_size": 40, "anchor": "lm", "color": "#00C896"},
        ]
    },
    {
        "title": "When to Use Each",
        "duration_sec": 5,
        "bg_color": "#0d1117",
        "text": [
            {"text": "Long Call", "x": 200, "y": 250, "font_size": 55, "anchor": "mm", "color": "#38BDF8"},
            {"text": "Strong bullish", "x": 200, "y": 380, "font_size": 40, "anchor": "mm", "color": "#FFFFFF"},
            {"text": "Limited capital", "x": 200, "y": 460, "font_size": 40, "anchor": "mm", "color": "#FFFFFF"},
            {"text": "Long Put", "x": 700, "y": 250, "font_size": 55, "anchor": "mm", "color": "#EF4444"},
            {"text": "Bearish outlook", "x": 700, "y": 380, "font_size": 40, "anchor": "mm", "color": "#FFFFFF"},
            {"text": "Or hedging risk", "x": 700, "y": 460, "font_size": 40, "anchor": "mm", "color": "#FFFFFF"},
            {"text": "Covered Call", "x": 1220, "y": 250, "font_size": 55, "anchor": "mm", "color": "#A78BFA"},
            {"text": "Income from stock", "x": 1220, "y": 380, "font_size": 40, "anchor": "mm", "color": "#FFFFFF"},
            {"text": "You own the stock", "x": 1220, "y": 460, "font_size": 40, "anchor": "mm", "color": "#FFFFFF"},
        ]
    }
]

output = create_simple_video("beginner-strategies", scenes, output_path="../output/beginner-strategies.mp4")
print(f"✓ Beginner Strategies created: {output}")
