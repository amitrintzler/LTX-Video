from manim import *
import numpy as np

config.pixel_width = 1024
config.pixel_height = 576
config.frame_rate = 24
config.background_color = "#04040e"

# Stylised vol surface curves (market-realistic shapes, not BS model)
def iv_7d(K):
    """7-day: pronounced symmetric smile"""
    x = (K - 100) / 100
    return (0.24 + 1.80 * x**2) * 100

def iv_30d(K):
    """30-day: left-skewed smirk (put skew dominates)"""
    x = (K - 100) / 100
    return (0.225 - 0.22 * x + 0.55 * x**2) * 100

def iv_90d(K):
    """90-day: flatter term structure"""
    x = (K - 100) / 100
    return (0.210 - 0.09 * x + 0.22 * x**2) * 100


class VideoScene(Scene):
    def construct(self):

        # ── Axes ──────────────────────────────────────────────────────
        axes = Axes(
            x_range=[68, 134, 10],
            y_range=[14, 52, 5],
            x_length=9.0,
            y_length=4.6,
            axis_config={"color": "#1a1a3a", "stroke_width": 1.5},
            tips=False,
        ).shift(LEFT * 0.4 + DOWN * 0.1)

        axes.get_x_axis().add_numbers(
            x_values=[70, 80, 90, 100, 110, 120, 130],
            font_size=16, color="#282850", label_constructor=Text,
        )
        axes.get_y_axis().add_numbers(
            x_values=[20, 25, 30, 35, 40, 45, 50],
            font_size=16, color="#282850", label_constructor=Text,
        )

        grid = VGroup(*[
            axes.get_horizontal_line(axes.c2p(134, y), color="#090918", stroke_width=1)
            for y in range(15, 55, 5)
        ], *[
            axes.get_vertical_line(axes.c2p(x, 52), color="#090918", stroke_width=1)
            for x in range(70, 135, 10)
        ])

        x_lbl = Text("Strike Price  K ($)", font_size=14, color="#252548")
        x_lbl.next_to(axes, DOWN, buff=0.30)
        y_lbl = Text("Implied Volatility  IV (%)", font_size=14, color="#252548").rotate(PI/2)
        y_lbl.next_to(axes, LEFT, buff=0.32)

        title = Text("VOLATILITY SMILE & TERM STRUCTURE", font_size=19, color=WHITE, weight=BOLD)
        title.to_edge(UP, buff=0.18)
        sub = Text("market-implied volatility varies by strike and expiry",
                   font_size=12, color="#1c1c3c")
        sub.next_to(title, DOWN, buff=0.06)

        # ── Three IV curves ───────────────────────────────────────────
        curve_7d  = axes.plot(iv_7d,  x_range=[70, 130], color="#00d4ff", stroke_width=3.0)
        curve_30d = axes.plot(iv_30d, x_range=[70, 130], color="#ffaa00", stroke_width=3.0)
        curve_90d = axes.plot(iv_90d, x_range=[70, 130], color="#bb99ff", stroke_width=3.0)

        lbl_7d  = Text("7-day  (smile)",  font_size=13, color="#00d4ff", weight=BOLD)
        lbl_30d = Text("30-day (skew)",   font_size=13, color="#ffaa00", weight=BOLD)
        lbl_90d = Text("90-day (flat)",   font_size=13, color="#bb99ff", weight=BOLD)
        lbl_7d.move_to(axes.c2p(75, iv_7d(75) + 2.5))
        lbl_30d.move_to(axes.c2p(77, iv_30d(77) + 2.5))
        lbl_90d.move_to(axes.c2p(79, iv_90d(79) + 2.5))

        # ── Vertical markers ──────────────────────────────────────────
        def vline(k, lbl_text, color, lbl_side=UP):
            line = DashedLine(axes.c2p(k, 14), axes.c2p(k, 51),
                              color=color, stroke_width=1.2, dash_length=0.1)
            lbl = Text(lbl_text, font_size=11, color=color)
            lbl.next_to(axes.c2p(k, 51), lbl_side, buff=0.08)
            return VGroup(line, lbl)

        vl_otm_put = vline(80,  "OTM Put",  "#ff6666")
        vl_atm     = vline(100, "ATM",      "#ffffff")
        vl_otm_call= vline(120, "OTM Call", "#66bbff")

        # ── ATM IV dots ───────────────────────────────────────────────
        dot_7d  = Dot(axes.c2p(100, iv_7d(100)),  radius=0.09, color="#00d4ff")
        dot_30d = Dot(axes.c2p(100, iv_30d(100)), radius=0.09, color="#ffaa00")
        dot_90d = Dot(axes.c2p(100, iv_90d(100)), radius=0.09, color="#bb99ff")

        # ── Callout helper ────────────────────────────────────────────
        def callout(line1, line2, pos, border):
            bg = RoundedRectangle(corner_radius=0.1, width=3.8, height=0.72,
                                  fill_color="#070714", fill_opacity=0.94,
                                  stroke_color=border, stroke_width=1)
            txt = VGroup(
                Text(line1, font_size=12, color=border, weight=BOLD),
                Text(line2,  font_size=10, color="#334455"),
            ).arrange(DOWN, buff=0.06)
            return VGroup(bg, txt).move_to(pos)

        c_skew = callout(
            "Put Skew: OTM puts cost more",
            "crash insurance demand steepens the left wing",
            [-1.0, -1.5, 0], "#ff9999",
        )
        c_term = callout(
            "Term Structure Flattens with Time",
            "longer maturities mean-revert toward long-run vol",
            [-1.0, -2.3, 0], "#bb99ff",
        )

        # ── Assemble ──────────────────────────────────────────────────
        self.add(grid, axes, x_lbl, y_lbl, title, sub)
        self.add(vl_otm_put, vl_atm, vl_otm_call)

        # Phase 1: draw curves in sequence
        self.wait(0.5)
        self.play(Create(curve_7d),  run_time=1.4, rate_func=smooth)
        self.play(FadeIn(lbl_7d), FadeIn(dot_7d), run_time=0.3)
        self.wait(0.3)

        self.play(Create(curve_30d), run_time=1.4, rate_func=smooth)
        self.play(FadeIn(lbl_30d), FadeIn(dot_30d), run_time=0.3)
        self.wait(0.3)

        self.play(Create(curve_90d), run_time=1.4, rate_func=smooth)
        self.play(FadeIn(lbl_90d), FadeIn(dot_90d), run_time=0.3)
        self.wait(0.5)

        # Phase 2: callouts
        self.play(FadeIn(c_skew), run_time=0.4)
        self.wait(1.2)
        self.play(FadeIn(c_term), run_time=0.4)
        self.wait(1.2)
        self.wait(0.5)
