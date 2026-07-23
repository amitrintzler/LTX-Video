"""
Example: Two-column comparison layout

This is a working reference for side-by-side concept comparison.
- Left panel (x ≤ -4): First concept
- Right panel (x ≥ 4): Second concept
- Top band: Title
- Center band empty
- Duration: 14 seconds
"""

from manim import *


class TwoColumnComparisonScene(Scene):
    def construct(self):
        # Background
        self.camera.background_color = "#0f1117"

        # TITLE at top
        title = Text("Option Type Comparison", font_size=32, color="#FFD700")
        title.to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=1.0)

        # LEFT COLUMN: Call Option
        left_rect = Rectangle(
            width=3.5,
            height=4.0,
            stroke_color="#00D9FF",
            stroke_width=2,
            fill_opacity=0.05,
            fill_color="#00D9FF",
        )
        left_rect.shift(LEFT * 4.5)

        left_label = Text("CALL", font_size=20, color="#00D9FF", weight="bold")
        left_label.next_to(left_rect, UP, buff=0.2)

        left_bullet1 = Text(
            "Right to buy", font_size=14, color="#F1F5F9"
        ).next_to(left_rect.get_left(), RIGHT, buff=0.3)
        left_bullet1.to_edge(LEFT, buff=2.0)

        left_bullet2 = Text(
            "Profit if price ↑", font_size=14, color="#F1F5F9"
        ).next_to(left_bullet1, DOWN, buff=0.3)

        left_bullet3 = Text(
            "Loss if price ↓", font_size=14, color="#F1F5F9"
        ).next_to(left_bullet2, DOWN, buff=0.3)

        # RIGHT COLUMN: Put Option
        right_rect = Rectangle(
            width=3.5,
            height=4.0,
            stroke_color="#FFD700",
            stroke_width=2,
            fill_opacity=0.05,
            fill_color="#FFD700",
        )
        right_rect.shift(RIGHT * 4.5)

        right_label = Text("PUT", font_size=20, color="#FFD700", weight="bold")
        right_label.next_to(right_rect, UP, buff=0.2)

        right_bullet1 = Text(
            "Right to sell", font_size=14, color="#F1F5F9"
        ).next_to(right_rect.get_right(), LEFT, buff=0.3)
        right_bullet1.to_edge(RIGHT, buff=2.0)

        right_bullet2 = Text(
            "Profit if price ↓", font_size=14, color="#F1F5F9"
        ).next_to(right_bullet1, DOWN, buff=0.3)

        right_bullet3 = Text(
            "Loss if price ↑", font_size=14, color="#F1F5F9"
        ).next_to(right_bullet2, DOWN, buff=0.3)

        # Animate left column
        self.play(Create(left_rect), run_time=0.5)
        self.play(Write(left_label), run_time=0.5)
        self.wait(0.5)
        self.play(Write(left_bullet1), run_time=0.3)
        self.play(Write(left_bullet2), run_time=0.3)
        self.play(Write(left_bullet3), run_time=0.3)
        self.wait(0.5)

        # Animate right column
        self.play(Create(right_rect), run_time=0.5)
        self.play(Write(right_label), run_time=0.5)
        self.wait(0.5)
        self.play(Write(right_bullet1), run_time=0.3)
        self.play(Write(right_bullet2), run_time=0.3)
        self.play(Write(right_bullet3), run_time=0.3)
        self.wait(1.0)

        # Flash the contrast
        self.play(
            left_rect.animate.set_stroke("#00D9FF", width=3),
            right_rect.animate.set_stroke("#FFD700", width=3),
            run_time=0.5,
        )
        self.wait(2.0)
