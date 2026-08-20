"""
Example: Curve animation with revealing path

This is a working reference for animating curves and mathematical functions.
- Axes in center band
- Curve reveals smoothly
- Annotations pinned to safe zones (edges, panels)
- Duration: 12 seconds
"""

from manim import *


class CurveAnimationScene(Scene):
    def construct(self):
        # Background
        self.camera.background_color = "#0f1117"

        # AXES centered
        axes = Axes(
            x_range=[0, 10, 1],
            y_range=[0, 100, 20],
            axis_config={"color": "#64748b", "stroke_width": 2},
            tips=False,
        )
        axes.scale(0.9)

        # Title at top
        title = Text("Function Growth Over Time", font_size=24, color="#FFD700")
        title.to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=0.8)

        # CURVE 1: Exponential (in teal/cyan)
        def exp_func(x):
            return (1.5 ** x) - 1

        curve1 = axes.plot(
            exp_func,
            x_range=[0, 10],
            color="#00D9FF",
            stroke_width=3,
        )

        curve1_label = Text("Exponential", font_size=14, color="#00D9FF").next_to(
            axes.get_top(), UP, buff=0.3
        )

        # CURVE 2: Linear (in gold)
        def linear_func(x):
            return x * 10

        curve2 = axes.plot(
            linear_func,
            x_range=[0, 10],
            color="#FFD700",
            stroke_width=3,
        )

        curve2_label = Text("Linear", font_size=14, color="#FFD700").next_to(
            axes.get_top(), DOWN, buff=0.3
        )

        # Create axes
        self.play(Create(axes), run_time=1.0)
        self.wait(0.5)

        # Animate first curve
        self.play(Create(curve1), run_time=2.0)
        self.play(Write(curve1_label), run_time=0.5)
        self.wait(0.5)

        # Animate second curve
        self.play(Create(curve2), run_time=2.0)
        self.play(Write(curve2_label), run_time=0.5)
        self.wait(0.5)

        # Highlight intersection point
        intersection_x = 2.0  # approx where they're similar
        intersection_point = Dot(
            axes.c2p(intersection_x, exp_func(intersection_x)),
            color="#10B981",
            radius=0.1,
        )
        self.play(Create(intersection_point), run_time=0.5)

        # Annotation at bottom safe zone
        note = Text(
            "Exponential grows faster",
            font_size=12,
            color="#8B949E",
        ).to_edge(DOWN, buff=0.8)

        self.play(Write(note), run_time=0.8)
        self.wait(1.5)

        # Brief highlight of the divergence
        self.play(
            curve1.animate.set_stroke("#00D9FF", width=4),
            curve2.animate.set_stroke("#FFD700", width=3),
            run_time=0.5,
        )
        self.wait(1.0)
