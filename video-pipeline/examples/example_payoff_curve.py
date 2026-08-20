"""
Example: Two-panel payoff diagram (Call vs Put)

This is a working reference for code generation.
- Left panel (x ≤ -4): Call payoff curve
- Right panel (x ≥ 4): Put payoff curve
- Center band empty
- Duration: 12 seconds
"""

from manim import *


class PayoffDiagramScene(Scene):
    def construct(self):
        # Background
        self.camera.background_color = "#0f1117"

        # LEFT PANEL: Call Payoff
        left_axes = Axes(
            x_range=[0, 100, 20],
            y_range=[-30, 80, 20],
            axis_config={"color": "#64748b"},
            tips=False,
        )
        left_axes.scale(0.8)
        left_axes.shift(LEFT * 5)

        # Call payoff curve: max(S - K, 0) where K=50
        def call_payoff(s):
            return max(s - 50, 0) - 5  # subtract premium

        call_curve = left_axes.plot(
            call_payoff,
            x_range=[0, 100],
            color="#00D9FF",
            stroke_width=4,
        )

        call_label = Text("Call Payoff", font_size=24, color="#FFD700").next_to(
            left_axes, UP, buff=0.5
        )

        # Mark breakeven
        call_breakeven = Dot(left_axes.c2p(55, 0), color="#FFD700", radius=0.08)

        self.play(Create(left_axes), run_time=1.0)
        self.play(Write(call_label), run_time=0.5)
        self.wait(0.5)
        self.play(Create(call_curve), run_time=1.5)
        self.play(Create(call_breakeven), run_time=0.5)

        # RIGHT PANEL: Put Payoff
        right_axes = Axes(
            x_range=[0, 100, 20],
            y_range=[-30, 80, 20],
            axis_config={"color": "#64748b"},
            tips=False,
        )
        right_axes.scale(0.8)
        right_axes.shift(RIGHT * 5)

        # Put payoff curve: max(K - S, 0) where K=50
        def put_payoff(s):
            return max(50 - s, 0) - 5  # subtract premium

        put_curve = right_axes.plot(
            put_payoff,
            x_range=[0, 100],
            color="#FFD700",
            stroke_width=4,
        )

        put_label = Text("Put Payoff", font_size=24, color="#00D9FF").next_to(
            right_axes, UP, buff=0.5
        )

        # Mark breakeven
        put_breakeven = Dot(right_axes.c2p(45, 0), color="#00D9FF", radius=0.08)

        self.play(Create(right_axes), run_time=1.0)
        self.play(Write(put_label), run_time=0.5)
        self.wait(0.5)
        self.play(Create(put_curve), run_time=1.5)
        self.play(Create(put_breakeven), run_time=0.5)

        # Center band remains empty (no text overlay)

        # Summary at bottom
        summary = Text(
            "Stock Price",
            font_size=16,
            color="#8B949E",
        ).next_to(left_axes, DOWN, buff=0.8)

        self.play(Write(summary), run_time=0.5)
        self.wait(2.0)
