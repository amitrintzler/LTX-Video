from manim import *
import numpy as np
from scipy.stats import norm

config.pixel_width = 1024
config.pixel_height = 576
config.frame_rate = 24
config.background_color = "#04040e"


def bs_call(S, K=100, T=1.0, r=0.05, sigma=0.30):
    if T <= 1e-6: return max(S - K, 0.0)
    d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
    return float(S*norm.cdf(d1) - K*np.exp(-r*T)*norm.cdf(d1 - sigma*np.sqrt(T)))

def bs_put(S, K=100, T=1.0, r=0.05, sigma=0.30):
    return bs_call(S,K,T,r,sigma) - S + K*np.exp(-r*T)

def bs_delta(S, K=100, T=1.0, r=0.05, sigma=0.30):
    if T <= 1e-6: return 0.5
    d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
    return norm.cdf(d1)

def bs_gamma(S, K=100, T=1.0, r=0.05, sigma=0.30):
    if T <= 1e-6: return 0.0
    d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
    return norm.pdf(d1) / (S*sigma*np.sqrt(T))

def bs_theta(S, K=100, T=1.0, r=0.05, sigma=0.30):
    if T <= 1e-6: return 0.0
    d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)
    return (-(S*norm.pdf(d1)*sigma)/(2*np.sqrt(T)) - r*K*np.exp(-r*T)*norm.cdf(d2)) / 365

def bs_vega(S, K=100, T=1.0, r=0.05, sigma=0.30):
    if T <= 1e-6: return 0.0
    d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
    return S*norm.pdf(d1)*np.sqrt(T) / 100


class VideoScene(Scene):
    def construct(self):
        S_t     = ValueTracker(100.0)
        sigma_t = ValueTracker(0.30)
        T_t     = ValueTracker(60 / 365)

        def S():   return S_t.get_value()
        def sig(): return sigma_t.get_value()
        def T():   return T_t.get_value()

        # ── Vertical separator ────────────────────────────────────────
        vsep = Line([0.3, 2.9, 0], [0.3, -2.9, 0], color="#0d0d22", stroke_width=1.5)

        # ── Left panel: inputs ────────────────────────────────────────
        lx = -2.6

        title = Text("BLACK-SCHOLES MODEL", font_size=19, color=WHITE, weight=BOLD)
        title.move_to([lx, 2.60, 0])
        sub = Text("live pricing dashboard", font_size=11, color="#1c1c3a")
        sub.move_to([lx, 2.26, 0])

        div_top = Line([lx-1.9, 2.0, 0], [lx+1.9, 2.0, 0], color="#111130", stroke_width=1)

        # Input rows
        s_row = always_redraw(lambda: VGroup(
            Text("Stock Price  S", font_size=12, color="#1e2e4e"),
            Text(f"${S_t.get_value():.1f}", font_size=28, color="#00d4ff", weight=BOLD),
        ).arrange(DOWN, buff=0.03).move_to([lx, 1.52, 0]))

        k_row = VGroup(
            Text("Strike Price  K", font_size=12, color="#1e1e3a"),
            Text("$100.00", font_size=28, color="#555566", weight=BOLD),
        ).arrange(DOWN, buff=0.03).move_to([lx, 0.72, 0])

        t_row = always_redraw(lambda: VGroup(
            Text("Days to Expiry  T", font_size=12, color="#1e1e3a"),
            Text(f"{T_t.get_value()*365:.0f} days", font_size=28, color="#ffffff", weight=BOLD),
        ).arrange(DOWN, buff=0.03).move_to([lx, -0.08, 0]))

        sig_row = always_redraw(lambda: VGroup(
            Text("Implied Vol  \u03c3", font_size=12, color="#2e2e1a"),
            Text(f"{sigma_t.get_value()*100:.1f}%", font_size=28, color="#ffaa00", weight=BOLD),
        ).arrange(DOWN, buff=0.03).move_to([lx, -0.88, 0]))

        r_row = VGroup(
            Text("Risk-Free Rate  r", font_size=12, color="#1e1e3a"),
            Text("5.00%", font_size=28, color="#555566", weight=BOLD),
        ).arrange(DOWN, buff=0.03).move_to([lx, -1.68, 0])

        params_lbl = Text("model: Black-Scholes (1973)", font_size=10, color="#111130")
        params_lbl.move_to([lx, -2.52, 0])

        # ── Right panel: outputs ──────────────────────────────────────
        rx = 2.7

        call_disp = always_redraw(lambda: VGroup(
            Text("CALL PRICE", font_size=13, color="#1a3040"),
            Text(f"${bs_call(S(),T=T(),sigma=sig()):.2f}",
                 font_size=48, color="#00d4ff", weight=BOLD),
        ).arrange(DOWN, buff=0.04).move_to([rx, 1.82, 0]))

        put_disp = always_redraw(lambda: VGroup(
            Text("PUT PRICE", font_size=13, color="#302a10"),
            Text(f"${bs_put(S(),T=T(),sigma=sig()):.2f}",
                 font_size=48, color="#ffaa00", weight=BOLD),
        ).arrange(DOWN, buff=0.04).move_to([rx, 0.68, 0]))

        div_mid = Line([rx-1.1, -0.05, 0], [rx+1.1, -0.05, 0], color="#111130", stroke_width=1)

        # Greeks 2x2
        gxl, gxr = rx - 0.58, rx + 0.58
        gy1, gy2 = -0.72, -1.76

        delta_disp = always_redraw(lambda: VGroup(
            Text("DELTA  \u0394", font_size=11, color="#1a2838"),
            Text(f"{bs_delta(S(),T=T(),sigma=sig()):.4f}",
                 font_size=26, color="#00d4ff", weight=BOLD),
        ).arrange(DOWN, buff=0.03).move_to([gxl, gy1, 0]))

        gamma_disp = always_redraw(lambda: VGroup(
            Text("GAMMA  \u0393", font_size=11, color="#2a2810"),
            Text(f"{bs_gamma(S(),T=T(),sigma=sig()):.4f}",
                 font_size=26, color="#ffaa00", weight=BOLD),
        ).arrange(DOWN, buff=0.03).move_to([gxr, gy1, 0]))

        theta_disp = always_redraw(lambda: VGroup(
            Text("THETA  \u03b8", font_size=11, color="#281818"),
            Text(f"${bs_theta(S(),T=T(),sigma=sig()):.3f}",
                 font_size=26, color="#ff5555", weight=BOLD),
        ).arrange(DOWN, buff=0.03).move_to([gxl, gy2, 0]))

        vega_disp = always_redraw(lambda: VGroup(
            Text("VEGA  \u03bd", font_size=11, color="#1a1828"),
            Text(f"${bs_vega(S(),T=T(),sigma=sig()):.3f}",
                 font_size=26, color="#bb99ff", weight=BOLD),
        ).arrange(DOWN, buff=0.03).move_to([gxr, gy2, 0]))

        parity = Text("C \u2212 P = S \u2212 Ke\u207b\u02b3\u1d40  (put-call parity)", font_size=10, color="#111130")
        parity.move_to([rx, -2.52, 0])

        # ── Callout helper ────────────────────────────────────────────
        def callout(line1, line2, x, y, border="#00d4ff"):
            bg = RoundedRectangle(corner_radius=0.1, width=3.4, height=0.74,
                                  fill_color="#070714", fill_opacity=0.94,
                                  stroke_color=border, stroke_width=1)
            txt = VGroup(
                Text(line1, font_size=13, color=border, weight=BOLD),
                Text(line2, font_size=10, color="#334455"),
            ).arrange(DOWN, buff=0.06)
            c = VGroup(bg, txt)
            c.move_to([x, y, 0])
            return c

        c_iv    = callout("Higher IV = Pricier Options",
                          "vega measures this sensitivity per 1% vol move",
                          lx, -2.1, "#ffaa00")
        c_delta = callout("Delta = Sensitivity to Stock Price",
                          "ATM call delta \u2248 0.5  \u2014  ITM approaches 1.0",
                          lx, -2.1, "#00d4ff")

        # ── Assemble ──────────────────────────────────────────────────
        self.add(vsep, title, sub, div_top, div_mid)
        self.add(s_row, k_row, t_row, sig_row, r_row, params_lbl)
        self.add(call_disp, put_disp, delta_disp, gamma_disp, theta_disp, vega_disp, parity)

        # Phase 1: hold
        self.wait(1.5)

        # Phase 2: sigma sweep 30% -> 50%
        self.play(FadeIn(c_iv), run_time=0.3)
        self.play(sigma_t.animate.set_value(0.50), run_time=2.5, rate_func=linear)
        self.wait(0.4)
        self.play(sigma_t.animate.set_value(0.30), run_time=1.5, rate_func=linear)
        self.play(FadeOut(c_iv), run_time=0.3)

        # Phase 3: S sweep 100 -> 115
        self.play(FadeIn(c_delta), run_time=0.3)
        self.play(S_t.animate.set_value(115), run_time=2.5, rate_func=linear)
        self.wait(0.3)
        self.play(S_t.animate.set_value(100), run_time=1.5, rate_func=linear)
        self.play(FadeOut(c_delta), run_time=0.3)

        # Phase 4: T decay 60d -> 5d (gamma spikes, theta falls)
        self.play(T_t.animate.set_value(5 / 365), run_time=3.5, rate_func=linear)
        self.wait(0.8)
