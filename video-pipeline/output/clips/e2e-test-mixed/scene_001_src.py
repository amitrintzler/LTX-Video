from manim import *
import numpy as np
from scipy.stats import norm

config.pixel_width = 1024
config.pixel_height = 576
config.frame_rate = 24
config.background_color = "#04040e"


def bs_call(S, K=100, T=1.0, r=0.05, sigma=0.30):
    if T <= 1e-6:
        return max(S - K, 0.0)
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    return float(S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2))


def bs_theta_daily(S, K=100, T=1.0, r=0.05, sigma=0.30):
    """Daily theta (per calendar day)."""
    if T <= 1e-6:
        return 0.0
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    theta = (-(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
             - r * K * np.exp(-r * T) * norm.cdf(d2))
    return theta / 365


def bs_delta(S, K=100, T=1.0, r=0.05, sigma=0.30):
    if T <= 1e-6:
        return 0.5
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    return norm.cdf(d1)


def bs_gamma(S, K=100, T=1.0, r=0.05, sigma=0.30):
    if T <= 1e-6:
        return 0.0
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    return norm.pdf(d1) / (S * sigma * np.sqrt(T))


class VideoScene(Scene):
    def construct(self):

        T_max = 60 / 365
        t = ValueTracker(T_max)

        def curve_color():
            ratio = t.get_value() / T_max
            return interpolate_color(ManimColor("#ff2020"), ManimColor("#00b8ff"), ratio)

        # ── Main chart axes ───────────────────────────────────────────────
        axes = Axes(
            x_range=[72, 132, 10],
            y_range=[0, 38, 5],
            x_length=7.4,
            y_length=4.2,
            axis_config={"color": "#1a1a3a", "stroke_width": 1.5},
            tips=False,
        ).shift(LEFT * 1.6 + DOWN * 0.15)

        axes.get_x_axis().add_numbers(
            x_values=[80, 90, 100, 110, 120, 130],
            font_size=18,
            color="#282850",
            label_constructor=Text,
        )
        axes.get_y_axis().add_numbers(
            x_values=[5, 10, 15, 20, 25, 30],
            font_size=18,
            color="#282850",
            label_constructor=Text,
        )

        grid = VGroup(*[
            axes.get_horizontal_line(axes.c2p(132, y), color="#090918", stroke_width=1)
            for y in range(5, 40, 5)
        ], *[
            axes.get_vertical_line(axes.c2p(x, 38), color="#090918", stroke_width=1)
            for x in range(80, 135, 10)
        ])

        x_lbl = Text("Stock Price at Expiry ($)", font_size=14, color="#252548")
        x_lbl.next_to(axes, DOWN, buff=0.34)
        y_lbl = Text("Option Value ($)", font_size=14, color="#252548").rotate(PI / 2)
        y_lbl.next_to(axes, LEFT, buff=0.38)

        params_lbl = Text("σ = 30%   r = 5%   K = $100", font_size=11, color="#1c1c3c")
        params_lbl.move_to(axes.get_corner(UL) + RIGHT * 1.1 + DOWN * 0.2)

        # Intrinsic value floor
        intrinsic = axes.plot(
            lambda x: max(x - 100, 0),
            x_range=[72, 132], color="#ffffff",
            stroke_width=1.1, stroke_opacity=0.13,
        )
        intrinsic_lbl = Text("Intrinsic  max(S-K, 0)", font_size=10, color="#202040")
        intrinsic_lbl.move_to(axes.c2p(119, 21))

        k_line = DashedLine(
            axes.c2p(100, 0), axes.c2p(100, 36),
            color="#bb2222", stroke_width=1.2, dash_length=0.09,
        )
        k_lbl = Text("K = $100", font_size=12, color="#bb3333")
        k_lbl.next_to(axes.c2p(100, 36), UP, buff=0.07)

        atm_lbl_static = Text("ATM", font_size=11, color="#771111")
        atm_lbl_static.next_to(axes.c2p(100, 0), DOWN, buff=0.1)

        # ── Live BS curve ─────────────────────────────────────────────────
        live_curve = always_redraw(lambda: axes.plot(
            lambda x: bs_call(x, T=t.get_value()),
            x_range=[72, 132],
            color=curve_color(),
            stroke_width=3.4,
        ))

        # ── Time-value fill ───────────────────────────────────────────────
        def build_fill():
            T = t.get_value()
            xs = np.linspace(72, 132, 100)
            top = [axes.c2p(x, bs_call(x, T=T)) for x in xs]
            bot = [axes.c2p(x, max(x - 100, 0)) for x in xs]
            return Polygon(*top, *bot[::-1],
                           fill_color=curve_color(), fill_opacity=0.18, stroke_width=0)

        live_fill = always_redraw(build_fill)

        # ── ATM tracking dot ──────────────────────────────────────────────
        def make_atm_dot():
            price = bs_call(100, T=t.get_value())
            dot = Dot(axes.c2p(100, price), radius=0.11, color=curve_color())
            dot.set_stroke(WHITE, width=2.0)
            return dot

        atm_dot = always_redraw(make_atm_dot)

        # ── Time-value bracket at right edge of chart ─────────────────────
        def make_tv_bracket():
            T = t.get_value()
            price = bs_call(100, T=T)
            if price < 0.1:
                return VGroup()
            xb = 123
            top_pt = np.array(axes.c2p(xb, price))
            bot_pt = np.array(axes.c2p(xb, 0.0))
            mid_pt = (top_pt + bot_pt) / 2
            bar   = Line(bot_pt, top_pt, color="#252550", stroke_width=1.1)
            t_top = Line(top_pt + LEFT * 0.1, top_pt + RIGHT * 0.1,
                         color="#252550", stroke_width=1.1)
            t_bot = Line(bot_pt + LEFT * 0.1, bot_pt + RIGHT * 0.1,
                         color="#252550", stroke_width=1.1)
            lbl = Text("TIME\nVALUE", font_size=10, color="#2e2e5a", line_spacing=0.8)
            lbl.move_to(mid_pt + RIGHT * 0.55)
            return VGroup(bar, t_top, t_bot, lbl)

        tv_bracket = always_redraw(make_tv_bracket)

        # ── Right panel ───────────────────────────────────────────────────
        px = 3.62

        title = Text("THETA DECAY", font_size=25, color=WHITE, weight=BOLD)
        title.move_to([px, 2.60, 0])

        sub = Text("time value eroding toward zero", font_size=12, color="#20203e")
        sub.move_to([px, 2.25, 0])

        # Day countdown
        def make_days():
            days = int(t.get_value() * 365)
            c = curve_color()
            return VGroup(
                Text(f"{days:>2}", font_size=66, color=c, weight=BOLD),
                Text("days to expiry", font_size=14, color="#262646"),
            ).arrange(DOWN, buff=0.03).move_to([px, 1.30, 0])

        days_disp = always_redraw(make_days)

        div1 = Line([px - 1.1, 0.52, 0], [px + 1.1, 0.52, 0],
                    color="#131330", stroke_width=1)

        # ── Mini θ-rate chart ─────────────────────────────────────────────
        # Plots daily theta vs days remaining. Key insight: the curve is
        # convex — theta accelerates non-linearly as expiry approaches.
        mini_ax = Axes(
            x_range=[0, 62, 20],
            y_range=[-0.32, 0, 0.08],
            x_length=2.15,
            y_length=1.0,
            axis_config={"color": "#151535", "stroke_width": 1},
            tips=False,
        ).move_to([px, -0.26, 0])

        theta_curve_bg = mini_ax.plot(
            lambda d: bs_theta_daily(100, T=d / 365) if d > 0.5 else -0.32,
            x_range=[0.5, 60],
            color="#20204a",
            stroke_width=1.8,
        )

        mini_x_lbl = Text("Days remaining →", font_size=10, color="#18183a")
        mini_x_lbl.next_to(mini_ax, DOWN, buff=0.07)
        mini_y_lbl = Text("θ / day  ($)", font_size=10, color="#18183a")
        mini_y_lbl.next_to(mini_ax, UP, buff=0.04)

        # Tracking dot slides along the static theta curve
        def make_theta_dot():
            days = max(t.get_value() * 365, 0.5)
            th = bs_theta_daily(100, T=days / 365)
            return Dot(mini_ax.c2p(days, max(th, -0.315)),
                       radius=0.07, color=curve_color())

        theta_dot = always_redraw(make_theta_dot)

        div2 = Line([px - 1.1, -0.98, 0], [px + 1.1, -0.98, 0],
                    color="#131330", stroke_width=1)

        # ── Stats row 1: ATM Time Value | Daily Theta ─────────────────────
        def make_tv():
            tv = bs_call(100, T=t.get_value())
            c = curve_color()
            return VGroup(
                Text("ATM TIME VALUE", font_size=10, color="#222244"),
                Text(f"${tv:.2f}", font_size=30, color=c, weight=BOLD),
            ).arrange(DOWN, buff=0.04).move_to([px - 0.57, -1.44, 0])

        tv_disp = always_redraw(make_tv)

        def make_theta_num():
            th = bs_theta_daily(100, T=t.get_value())
            c = curve_color()
            return VGroup(
                Text("DAILY THETA", font_size=10, color="#222244"),
                Text(f"${th:.3f}", font_size=30, color=c, weight=BOLD),
            ).arrange(DOWN, buff=0.04).move_to([px + 0.57, -1.44, 0])

        theta_num_disp = always_redraw(make_theta_num)

        div3 = Line([px - 1.1, -1.96, 0], [px + 1.1, -1.96, 0],
                    color="#131330", stroke_width=1)

        # ── Stats row 2: Delta | Gamma ────────────────────────────────────
        # Delta (Δ): probability of expiring ITM ≈ 0.5 for ATM; barely moves
        # Gamma (Γ): rate of delta change; spikes dramatically near expiry
        def make_delta():
            d = bs_delta(100, T=t.get_value())
            c = curve_color()
            return VGroup(
                Text("DELTA  Δ", font_size=10, color="#222244"),
                Text(f"{d:.3f}", font_size=28, color=c, weight=BOLD),
            ).arrange(DOWN, buff=0.04).move_to([px - 0.57, -2.40, 0])

        delta_disp = always_redraw(make_delta)

        def make_gamma():
            g = bs_gamma(100, T=t.get_value())
            days = t.get_value() * 365
            # Gamma turns urgent red below 10 days — shows exploding risk
            if days < 10:
                c = ManimColor("#ff3333")
            elif days < 25:
                c = interpolate_color(
                    ManimColor("#ff3333"), curve_color(), (days - 10) / 15
                )
            else:
                c = curve_color()
            g_str = f"{g:.3f}" if g < 0.9995 else ">0.999"
            return VGroup(
                Text("GAMMA  Γ", font_size=10, color="#222244"),
                Text(g_str, font_size=28, color=c, weight=BOLD),
            ).arrange(DOWN, buff=0.04).move_to([px + 0.57, -2.40, 0])

        gamma_disp = always_redraw(make_gamma)

        # Vertical separator
        vsep = Line([2.32, 2.88, 0], [2.32, -2.88, 0],
                    color="#0e0e20", stroke_width=1.5)

        # ── Phase annotations ─────────────────────────────────────────────
        # Callout shown during 20-day pause on main chart
        callout_bg = RoundedRectangle(
            corner_radius=0.12, width=2.9, height=0.80,
            fill_color="#110606", fill_opacity=0.92,
            stroke_color="#ff3333", stroke_width=1,
        )
        callout_txt = VGroup(
            Text("⚡  GAMMA RISK ZONE", font_size=13, color="#ff5555", weight=BOLD),
            Text("rapid Δ swings  ·  expiry pin risk", font_size=10, color="#882222"),
        ).arrange(DOWN, buff=0.06)
        callout = VGroup(callout_bg, callout_txt)
        callout.move_to([-0.7, 0.85, 0])  # upper center of main chart (above BS curve)

        # Gamma-spikes label that fades in on mini chart near the steep end
        gamma_spike_lbl = Text("← Γ spikes here", font_size=9, color="#552222")
        gamma_spike_lbl.move_to(mini_ax.c2p(8, -0.22))

        # Expiry moment text
        expiry_txt = Text("ALL TIME PREMIUM LOST", font_size=14,
                          color="#ff3333", weight=BOLD)
        expiry_txt.move_to([-1.6, 0.55, 0])

        # ── Assemble all static + live elements ───────────────────────────
        self.add(grid, axes, intrinsic, intrinsic_lbl, k_line, k_lbl,
                 atm_lbl_static, x_lbl, y_lbl, params_lbl)
        self.add(vsep, title, sub, div1, div2, div3)
        self.add(mini_ax, theta_curve_bg, mini_x_lbl, mini_y_lbl)
        self.add(live_fill, live_curve, atm_dot, tv_bracket)
        self.add(days_disp, theta_dot, tv_disp, theta_num_disp,
                 delta_disp, gamma_disp)

        # ── Phase 1: Hold at 60 days (viewer reads panel) ─────────────────
        self.wait(1.5)

        # ── Phase 2: Decay 60d → 20d ──────────────────────────────────────
        self.play(
            t.animate.set_value(20 / 365),
            run_time=4.5,
            rate_func=linear,
        )

        # Pause at 20 days: gamma risk callout + spike label on mini chart
        self.play(
            FadeIn(callout),
            FadeIn(gamma_spike_lbl),
            run_time=0.4,
        )
        self.wait(1.2)
        self.play(
            FadeOut(callout),
            run_time=0.3,
        )

        # ── Phase 3: Decay 20d → 0 (gamma accelerating) ──────────────────
        self.play(
            t.animate.set_value(1e-6),
            run_time=5.0,
            rate_func=linear,
        )

        # ── Expiry: all premium gone ──────────────────────────────────────
        self.play(FadeIn(expiry_txt), run_time=0.4)
        self.wait(1.0)
