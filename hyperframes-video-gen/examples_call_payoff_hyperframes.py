#!/usr/bin/env python3
"""Call Option Payoff - Hyperframes version with smooth animations."""

import sys
sys.path.insert(0, "..")
from hyperframes_gen import create_hyperframes_video

scenes = [
    {
        "id": "s01",
        "start": 0,
        "duration": 3,
        "content": '''
        <div class="flex-center">
            <div class="text-title">Call Option Payoff</div>
            <div class="text-subtitle" style="margin-top: 40px;">Visual Diagram</div>
        </div>
        '''
    },
    {
        "id": "s02",
        "start": 3,
        "duration": 2,
        "content": '''
        <div class="flex-center">
            <svg width="1200" height="600" viewBox="0 0 1200 600" style="background: #0d1117;">
                <!-- Axes -->
                <line x1="100" y1="500" x2="1100" y2="500" stroke="#8B949E" stroke-width="3"/>
                <line x1="100" y1="100" x2="100" y2="500" stroke="#8B949E" stroke-width="3"/>

                <!-- X-axis label -->
                <text x="1100" y="540" font-size="24" fill="#8B949E">Stock Price</text>

                <!-- Y-axis label -->
                <text x="20" y="100" font-size="24" fill="#8B949E">Profit/Loss</text>
            </svg>
        </div>
        '''
    },
    {
        "id": "s03",
        "start": 5,
        "duration": 3,
        "content": '''
        <div class="flex-center">
            <svg width="1200" height="600" viewBox="0 0 1200 600" style="background: #0d1117;">
                <!-- Axes -->
                <line x1="100" y1="500" x2="1100" y2="500" stroke="#8B949E" stroke-width="3"/>
                <line x1="100" y1="100" x2="100" y2="500" stroke="#8B949E" stroke-width="3"/>

                <!-- Strike line -->
                <line x1="400" y1="100" x2="400" y2="500" stroke="#FFD700" stroke-width="2" stroke-dasharray="5,5"/>

                <!-- Loss zone line -->
                <line x1="100" y1="400" x2="400" y2="400" stroke="#FF4444" stroke-width="4"/>

                <!-- Labels -->
                <text x="400" y="540" font-size="20" fill="#FFD700" text-anchor="middle">Strike $100</text>
                <text x="200" y="380" font-size="24" fill="#FF4444">LOSS</text>
            </svg>
        </div>
        '''
    },
    {
        "id": "s04",
        "start": 8,
        "duration": 3,
        "content": '''
        <div class="flex-center">
            <svg width="1200" height="600" viewBox="0 0 1200 600" style="background: #0d1117;">
                <!-- Axes -->
                <line x1="100" y1="500" x2="1100" y2="500" stroke="#8B949E" stroke-width="3"/>
                <line x1="100" y1="100" x2="100" y2="500" stroke="#8B949E" stroke-width="3"/>

                <!-- Strikes -->
                <line x1="400" y1="100" x2="400" y2="500" stroke="#FFD700" stroke-width="2" stroke-dasharray="5,5"/>
                <line x1="550" y1="100" x2="550" y2="500" stroke="#FFD700" stroke-width="2" stroke-dasharray="5,5"/>

                <!-- Complete payoff line -->
                <line x1="100" y1="400" x2="400" y2="400" stroke="#FF4444" stroke-width="4"/>
                <line x1="400" y1="400" x2="1100" y2="150" stroke="#00C896" stroke-width="4"/>

                <!-- Labels -->
                <text x="400" y="540" font-size="18" fill="#FFD700" text-anchor="middle">Strike</text>
                <text x="550" y="540" font-size="18" fill="#FFD700" text-anchor="middle">Breakeven</text>
                <text x="250" y="380" font-size="20" fill="#FF4444">LOSS</text>
                <text x="800" y="200" font-size="20" fill="#00C896">PROFIT</text>
            </svg>
        </div>
        '''
    },
    {
        "id": "s05",
        "start": 11,
        "duration": 5,
        "content": '''
        <div class="flex-row">
            <div class="column">
                <div class="text-title">EXAMPLE</div>
                <div class="text-body" style="margin-top: 30px;">Apple Call</div>
                <div class="text-label" style="margin-top: 30px;">Strike: $150</div>
                <div class="text-label">Premium: $5</div>
                <div class="text-label">Breakeven: $155</div>
            </div>
            <div class="column">
                <svg width="400" height="500" viewBox="0 0 400 500" style="background: #0d1117;">
                    <line x1="30" y1="400" x2="370" y2="400" stroke="#8B949E" stroke-width="2"/>
                    <line x1="30" y1="50" x2="30" y2="400" stroke="#8B949E" stroke-width="2"/>

                    <line x1="150" y1="50" x2="150" y2="400" stroke="#FFD700" stroke-width="2" stroke-dasharray="3,3"/>

                    <line x1="30" y1="320" x2="150" y2="320" stroke="#FF4444" stroke-width="3"/>
                    <line x1="150" y1="320" x2="370" y2="100" stroke="#00C896" stroke-width="3"/>

                    <text x="150" y="440" font-size="16" fill="#FFD700" text-anchor="middle">$150</text>
                    <text x="80" y="350" font-size="14" fill="#FF4444">-$5</text>
                    <text x="250" y="150" font-size="14" fill="#00C896">+∞</text>
                </svg>
            </div>
        </div>
        '''
    },
    {
        "id": "s06",
        "start": 16,
        "duration": 4,
        "content": '''
        <div class="flex-center">
            <div style="text-align: center;">
                <div class="text-title">Key Takeaway</div>
                <div class="text-body color-success" style="margin-top: 40px;">Max Loss: Premium only</div>
                <div class="text-body color-success" style="margin-top: 40px;">Max Gain: Unlimited ∞</div>
                <div class="text-label" style="margin-top: 50px;">Bullish Strategy</div>
            </div>
        </div>
        '''
    }
]

output = create_hyperframes_video("call-payoff-hyperframes", scenes, output_path="../output/call-payoff-hyperframes.mp4")
print(f"✓ Call Option Payoff (Hyperframes) created: {output}")
