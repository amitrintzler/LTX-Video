from manim import *
import numpy as np
from scipy.stats import norm

config.pixel_width = 1024
config.pixel_height = 576
config.frame_rate = 24
config.background_color = "#04040e"


def bs_call(S, K=100, T=30/365, r=0.05, sigma=0.30):
    if T <= 1e-6: return max(S - K, 0.0)
    d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
    return float(S*norm.cdf(d1) - K*np.exp(-r*T)*norm.cdf(d1 - sigma*np.sqrt(T)))

def bs_delta(S, K=100, T=30/365, r=0.05, sigma=0.30):
    if T <= 1e-6: return 0.5
    d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
    return norm.cdf(d1)

def bs_gamma(S, K=100, T=30/365, r=0.05, sigma=0.30):
    if T <= 1e-6: return 0.0
    d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
    return norm.pdf(d1) / (S*sigma*np.sqrt(T))

def bs_theta(S, K=100, T=30/365, r=0.05, sigma=0.30):
    if T <= 1e-6: return 0.0
    d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)
    return (-(S*norm.pdf(d1)*sigma)/(2*np.sqrt(T)) - r*K*np.exp(-r*T)*norm.cdf(d2)) / 365

def bs_vega(S, K=100, T=30/365, r=0.05, sigma=0.30):
    if T <= 1e-6: return 0.0
    d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
    return S*norm.pdf(d1)*np.sqrt(T) / 100


class VideoScene(Scene):
    def construct(self):
        S_t = ValueTracker(100.0)

        # ── Main chart axes ───────────────────────────────────────────
        axes = Axes(
            x_range=[68, 132, 10],
            y_range=[0, 36, 5],
            x_length=7.0,
            y_length=4.0,
            axis_config={"color": "#1a1a3a", "stroke_width": 1.5},
            tips=False,
        ).shift(LEFT * 1.8 + DOWN * 0.2)

        axes.get_x_axis().add_numbers(
            x_values=[70, 80, 90, 100, 110, 120, 130],
            font_size=16, color="#282850", label_constructor=Text,
        )
        axes.get_y_axis().add_numbers(
            x_values=[5, 10, 15, 20, 25, 30],
            font_size=16, color="#282850", label_constructor=Text,
        )

        grid = VGroup(*[
            axes.get_horizontal_line(axes.c2p(132, y), color="#090918", stroke_width=1)
            for y in range(5, 40, 5)
        ], *[
            axes.get_vertical_line(axes.c2p(x, 36), color="#090918", stroke_width=1)
            for x in range(70, 135, 10)
        ])

        x_lbl = Text("Stock Price  S ($)", font_size=13, color="#252548")
        x_lbl.next_to(axes, DOWN, buff=0.28)
        y_lbl = Text("Call Option Value ($)", font_size=13, color="#252548").rotate(PI/2)
        y_lbl.next_to(axes, LEFT, buff=0.32)

        # Static BS curve (T=30d, sigma=30%)
        static_curve = axes.plot(bs_call, x_range=[70, 130],
                                 color="#223344", stroke_width=2.2)

        # ATM strike line
        k_line = DashedLine(axes.c2p(100, 0), axes.c2p(100, 34),
                            color="#aa2222", stroke_width=1.1, dash_length=0.09)
        k_lbl  = Text("K=$100", font_size=11, color="#aa2222")
        k_lbl.next_to(axes.c2p(100, 34), UP, buff=0.06)

        params = Text("T = 30 days    \u03c3 = 30%    r = 5%",
                      font_size=11, color="#181838")
        params.move_to(axes.get_corner(UL) + RIGHT*1.1 + DOWN*0.2)

        # ── Tracker line + dot on curve ───────────────────────────────
        def make_tracker_line():
            S = S_t.get_value()
            return DashedLine(
                axes.c2p(S, 0), axes.c2p(S, 36),
                color="#ffffff", stroke_width=1.2,
                dash_length=0.09, stroke_opacity=0.4,
            )
        tracker_line = always_redraw(make_tracker_line)

        def make_curve_dot():
            S = S_t.get_value()
            price = bs_call(S)
            # Color: cyan when ITM (S>100), amber when OTM (S<100)
            c = "#00d4ff" if S >= 100 else "#ffaa00"
            dot = Dot(axes.c2p(S, price), radius=0.12, color=c)
            dot.set_stroke(WHITE, width=2.0)
            return dot
        curve_dot = always_redraw(make_curve_dot)

        # ── Right panel: Greek gauges ─────────────────────────────────
        px = 3.55

        title = Text("THE OPTION GREEKS", font_size=20, color=WHITE, weight=BOLD)
        title.move_to([px, 2.58, 0])
        sub = Text("how option price responds to each input",
                   font_size=11, color="#1a1a38")
        sub.move_to([px, 2.22, 0])

        vsep = Line([2.1, 2.9, 0], [2.1, -2.9, 0], color="#0d0d22", stroke_width=1.5)

        # Gauge helper: label, bar, value
        BAR_W = 2.0

        def make_gauge(label, val_fn, max_val, color_fn, y):
            def make():
                v = val_fn(S_t.get_value())
                v_abs = abs(v)
                fill_frac = min(v_abs / max_val, 1.0)
                c = color_fn(S_t.get_value())

                lbl = Text(label, font_size=11, color="#202040")
                val = Text(f"{v:+.4f}" if abs(v) < 10 else f"{v:+.2f}",
                           font_size=20, color=c, weight=BOLD)

                bg_bar = Rectangle(width=BAR_W, height=0.16,
                                   fill_color="#111128", fill_opacity=1,
                                   stroke_width=0)
                fg_bar = Rectangle(width=max(BAR_W * fill_frac, 0.01), height=0.16,
                                   fill_color=c, fill_opacity=0.85, stroke_width=0)

                bg_bar.move_to([px, y - 0.24, 0])
                fg_bar.move_to([px - BAR_W/2 + max(BAR_W * fill_frac, 0.01)/2,
                                y - 0.24, 0])
                lbl.move_to([px - 0.8, y + 0.06, 0])
                val.move_to([px + 0.6, y + 0.06, 0])
                return VGroup(lbl, val, bg_bar, fg_bar)
            return always_redraw(make)

        # Delta: 0→1 range, cyan when ITM, amber when OTM
        delta_gauge = make_gauge(
            "DELTA  \u0394  (price sensitivity)",
            bs_delta,
            max_val=1.0,
            color_fn=lambda S: "#00d4ff" if S >= 100 else "#ffaa00",
            y=1.52,
        )

        # Gamma: 0→0.12 range, amber → red when high
        def gamma_color(S):
            g = bs_gamma(S)
            if g > 0.065: return "#ff5555"
            if g > 0.045: return "#ffaa00"
            return "#88aacc"

        gamma_gauge = make_gauge(
            "GAMMA  \u0393  (delta rate of change)",
            bs_gamma,
            max_val=0.12,
            color_fn=gamma_color,
            y=0.62,
        )

        # Theta: range -0.15→0, always red
        def theta_abs(S): return abs(bs_theta(S))
        theta_gauge = make_gauge(
            "THETA  \u03b8  (daily time decay $)",
            lambda S: bs_theta(S),
            max_val=0.15,
            color_fn=lambda S: "#ff5555",
            y=-0.28,
        )

        # Vega: 0→0.45 range, lavender
        vega_gauge = make_gauge(
            "VEGA  \u03bd  (per 1% vol move $)",
            bs_vega,
            max_val=0.45,
            color_fn=lambda S: "#bb99ff",
            y=-1.18,
        )

        params_r = Text("K=$100  T=30d  \u03c3=30%  r=5%", font_size=10, color="#141430")
        params_r.move_to([px, -2.52, 0])

        # ── Callouts ──────────────────────────────────────────────────
        def callout(line1, line2, pos, border):
            bg = RoundedRectangle(corner_radius=0.1, width=3.0, height=0.72,
                                  fill_color="#070714", fill_opacity=0.94,
                                  stroke_color=border, stroke_width=1)
            txt = VGroup(
                Text(line1, font_size=12, color=border, weight=BOLD),
                Text(line2, font_size=10, color="#334455"),
            ).arrange(DOWN, buff=0.06)
            return VGroup(bg, txt).move_to(pos)

        c_itm = callout(
            "Deep ITM: Delta \u2192 1.0",
            "gamma falls: delta already maxed out",
            [px, -2.0, 0], "#00d4ff",
        )
        c_atm = callout(
            "ATM: Gamma Peaks Here",
            "maximum rate of delta change at the money",
            [px, -2.0, 0], "#ffaa00",
        )
        c_otm = callout(
            "Deep OTM: Delta \u2192 0",
            "vega persists: still vol-sensitive",
            [px, -2.0, 0], "#ffaa00",
        )

        # ── Assemble ──────────────────────────────────────────────────
        self.add(grid, axes, static_curve, k_line, k_lbl, x_lbl, y_lbl, params)
        self.add(vsep, title, sub)
        self.add(delta_gauge, gamma_gauge, theta_gauge, vega_gauge, params_r)
        self.add(tracker_line, curve_dot)

        # Phase 1: hold at S=100 ATM
        self.wait(1.5)

        # Phase 2: S -> 125 (deep ITM)
        self.play(FadeIn(c_itm), run_time=0.3)
        self.play(S_t.animate.set_value(125), run_time=3.0, rate_func=linear)
        self.wait(0.4)
        self.play(FadeOut(c_itm), run_time=0.3)

        # Phase 3: S -> 100 (ATM, gamma peaks)
        self.play(FadeIn(c_atm), run_time=0.3)
        self.play(S_t.animate.set_value(100), run_time=2.0, rate_func=linear)
        self.wait(0.5)
        self.play(FadeOut(c_atm), run_time=0.3)

        # Phase 4: S -> 75 (deep OTM)
        self.play(FadeIn(c_otm), run_time=0.3)
        self.play(S_t.animate.set_value(75), run_time=3.5, rate_func=linear)
        self.wait(0.5)
        self.play(FadeOut(c_otm), run_time=0.3)
        self.wait(0.5)
