from manim import *
import numpy as np

config.pixel_width = 1024
config.pixel_height = 576
config.frame_rate = 24
config.background_color = "#04040e"

# Iron condor parameters
KLP, KSP, KSC, KLC = 80, 85, 115, 120  # strikes
NET_CREDIT = 1.50                         # per share max profit
MAX_LOSS   = 3.50                         # per share (spread - credit)

def leg_long_put(S):   return max(KLP - S, 0)
def leg_short_put(S):  return -max(KSP - S, 0)
def leg_short_call(S): return -max(S - KSC, 0)
def leg_long_call(S):  return max(S - KLC, 0)

def net_pnl(S):
    return NET_CREDIT + leg_long_put(S) + leg_short_put(S) + leg_short_call(S) + leg_long_call(S)


class VideoScene(Scene):
    def construct(self):

        # ── Axes ──────────────────────────────────────────────────────
        axes = Axes(
            x_range=[68, 134, 5],
            y_range=[-4.2, 2.2, 1],
            x_length=9.2,
            y_length=4.6,
            axis_config={"color": "#1a1a3a", "stroke_width": 1.5},
            tips=False,
        ).shift(LEFT * 0.3 + DOWN * 0.35)

        axes.get_x_axis().add_numbers(
            x_values=[70, 80, 85, 100, 115, 120, 130],
            font_size=16, color="#282850", label_constructor=Text,
        )
        axes.get_y_axis().add_numbers(
            x_values=[-4, -3, -2, -1, 0, 1, 2],
            font_size=16, color="#282850", label_constructor=Text,
        )

        grid = VGroup(*[
            axes.get_horizontal_line(axes.c2p(134, y), color="#090918", stroke_width=1)
            for y in range(-4, 3, 1)
        ])

        x_lbl = Text("Stock Price at Expiry ($)", font_size=14, color="#252548")
        x_lbl.next_to(axes, DOWN, buff=0.30)
        y_lbl = Text("P&L per Share  ($)", font_size=14, color="#252548").rotate(PI/2)
        y_lbl.next_to(axes, LEFT, buff=0.32)

        zero_line = axes.get_horizontal_line(axes.c2p(134, 0),
                                             color="#ffffff", stroke_width=0.8)
        zero_line.set_opacity(0.25)

        title = Text("IRON CONDOR  —  Strategy Payoff at Expiry",
                     font_size=18, color=WHITE, weight=BOLD)
        title.to_edge(UP, buff=0.18)
        sub = Text("sell OTM strangle, buy further OTM wings for protection",
                   font_size=12, color="#1c1c3c")
        sub.next_to(title, DOWN, buff=0.06)

        # ── Individual legs ───────────────────────────────────────────
        leg_colors = {
            "long_put":   "#ffaa00",
            "short_put":  "#ff6666",
            "short_call": "#ff6666",
            "long_call":  "#ffaa00",
        }
        c_lp  = axes.plot(lambda S: leg_long_put(S)   + NET_CREDIT/4,
                          x_range=[70,130], color=leg_colors["long_put"],
                          stroke_width=1.6, stroke_opacity=0.55)
        c_sp  = axes.plot(lambda S: leg_short_put(S)  + NET_CREDIT/4,
                          x_range=[70,130], color=leg_colors["short_put"],
                          stroke_width=1.6, stroke_opacity=0.55)
        c_sc  = axes.plot(lambda S: leg_short_call(S) + NET_CREDIT/4,
                          x_range=[70,130], color=leg_colors["short_call"],
                          stroke_width=1.6, stroke_opacity=0.55)
        c_lc  = axes.plot(lambda S: leg_long_call(S)  + NET_CREDIT/4,
                          x_range=[70,130], color=leg_colors["long_call"],
                          stroke_width=1.6, stroke_opacity=0.55)

        def leg_label(text, color, pos):
            return Text(text, font_size=11, color=color).move_to(axes.c2p(*pos))

        ll_lp  = leg_label("Long Put K=80",   "#ffaa00", (73, -3.0))
        ll_sp  = leg_label("Short Put K=85",  "#ff6666", (73, -1.6))
        ll_sc  = leg_label("Short Call K=115","#ff6666", (122, -1.6))
        ll_lc  = leg_label("Long Call K=120", "#ffaa00", (125, -3.0))

        # ── Net combined payoff ───────────────────────────────────────
        net_curve = axes.plot(net_pnl, x_range=[70,130],
                              color="#ffffff", stroke_width=3.4)

        # ── Fill zones ────────────────────────────────────────────────
        # Profit zone polygon (S=85..115, y=0..1.5)
        xs_profit = np.linspace(85, 115, 60)
        profit_top = [axes.c2p(x, net_pnl(x)) for x in xs_profit]
        profit_bot = [axes.c2p(x, 0) for x in xs_profit]
        profit_fill = Polygon(*profit_top, *profit_bot[::-1],
                              fill_color="#00e676", fill_opacity=0.18, stroke_width=0)

        # Loss zones
        xs_loss_l = np.linspace(70, 80, 30)
        loss_top_l = [axes.c2p(x, 0) for x in xs_loss_l]
        loss_bot_l = [axes.c2p(x, net_pnl(x)) for x in xs_loss_l]
        loss_fill_l = Polygon(*loss_top_l, *loss_bot_l[::-1],
                              fill_color="#ff4444", fill_opacity=0.18, stroke_width=0)

        xs_loss_r = np.linspace(120, 130, 30)
        loss_top_r = [axes.c2p(x, 0) for x in xs_loss_r]
        loss_bot_r = [axes.c2p(x, net_pnl(x)) for x in xs_loss_r]
        loss_fill_r = Polygon(*loss_top_r, *loss_bot_r[::-1],
                              fill_color="#ff4444", fill_opacity=0.18, stroke_width=0)

        # ── Strike dashed lines ───────────────────────────────────────
        def strike_line(k, color):
            return DashedLine(axes.c2p(k, -4.2), axes.c2p(k, 2.2),
                              color=color, stroke_width=1.0, dash_length=0.09)

        sl80  = strike_line(80,  "#ffaa00")
        sl85  = strike_line(85,  "#ff6666")
        sl115 = strike_line(115, "#ff6666")
        sl120 = strike_line(120, "#ffaa00")

        # ── Callouts ──────────────────────────────────────────────────
        def callout(line1, line2, pos, border):
            bg = RoundedRectangle(corner_radius=0.1, width=3.6, height=0.72,
                                  fill_color="#070714", fill_opacity=0.94,
                                  stroke_color=border, stroke_width=1)
            txt = VGroup(
                Text(line1, font_size=12, color=border, weight=BOLD),
                Text(line2, font_size=10, color="#334455"),
            ).arrange(DOWN, buff=0.06)
            return VGroup(bg, txt).move_to(pos)

        c_profit = callout(
            "Max Profit: $1.50  (stay between $85\u2013$115)",
            "collect premium if stock doesn't move",
            [0.0, 2.0, 0], "#00e676",
        )
        c_loss = callout(
            "Max Loss: $3.50  (stock breaks wings)",
            "spread width $5.00 \u2212 net credit $1.50",
            [0.0, -2.8, 0], "#ff4444",
        )

        # Moving dot along net payoff
        dot_s = ValueTracker(70)
        moving_dot = always_redraw(lambda: Dot(
            axes.c2p(dot_s.get_value(), net_pnl(dot_s.get_value())),
            radius=0.11, color="#ffffff",
        ).set_stroke(color=
            "#00e676" if 85 <= dot_s.get_value() <= 115 else "#ff4444",
            width=2.0
        ))

        # ── Assemble ──────────────────────────────────────────────────
        self.add(grid, axes, zero_line, x_lbl, y_lbl, title, sub)
        self.add(sl80, sl85, sl115, sl120)

        # Phase 1: draw legs in sequence
        self.wait(0.4)
        self.play(Create(c_lp),  FadeIn(ll_lp),  run_time=0.9)
        self.play(Create(c_sp),  FadeIn(ll_sp),  run_time=0.9)
        self.play(Create(c_sc),  FadeIn(ll_sc),  run_time=0.9)
        self.play(Create(c_lc),  FadeIn(ll_lc),  run_time=0.9)
        self.wait(0.4)

        # Phase 2: combined net payoff
        self.play(Create(net_curve), run_time=1.2, rate_func=smooth)
        self.play(FadeIn(profit_fill), FadeIn(loss_fill_l), FadeIn(loss_fill_r),
                  run_time=0.5)
        self.wait(0.3)

        # Phase 3: callouts
        self.play(FadeIn(c_profit), run_time=0.4)
        self.wait(0.9)
        self.play(FadeIn(c_loss), run_time=0.4)
        self.wait(0.7)

        # Phase 4: dot slides along payoff curve
        self.add(moving_dot)
        self.play(dot_s.animate.set_value(130), run_time=4.0, rate_func=linear)
        self.wait(0.6)
