/**
 * LongFormVideo.tsx
 *
 * 10-minute deep-dive lesson videos using SceneManager + all scene types.
 * Each lesson is its own named export wired to composition-registry.
 *
 * Scene pacing: durationInFrames per scene is set proportionally to narration
 * segment length (sec field in narration-scripts-long.json).
 */

import React from "react";
import { useVideoConfig } from "remotion";
import {
  SceneManager,
  TitleScene,
  BulletScene,
  SummaryScene,
  RealWorldExampleScene,
  PayoffDiagramScene,
  CalculationScene,
  ComparisonTableScene,
  MistakeHighlightScene,
  WorkedExampleScene,
  type SceneDef,
} from "./SceneSystem";

const FPS = 30;

/** Convert narration seconds to frames with 0.5s buffer. */
const sec = (s: number) => Math.round((s + 0.5) * FPS);

// ── Basics Flow Long ──────────────────────────────────────────────────────────
// Lesson: Options Basics Flow — full payoff diagram walkthrough, 10 min

export type BasicsFlowLongProps = {
  accent?: string;
};

export const BasicsFlowLong: React.FC<BasicsFlowLongProps> = ({ accent = "#10b981" }) => {
  useVideoConfig();

  const scenes: SceneDef[] = [
    // Scene 1 (30s) — Hook: the $350 story
    {
      durationInFrames: sec(30),
      render: () => (
        <TitleScene
          label="Options Basics"
          title="The $350 Bet"
          subtitle="How one contract gives you control of 100 shares"
          accent={accent}
        />
      ),
    },

    // Scene 2 (15s) — Framework overview
    {
      durationInFrames: sec(15),
      render: () => (
        <BulletScene
          heading="Options Flow: The Complete Framework"
          bullets={[
            "Right to buy or sell — not an obligation",
            "Strike price: the agreed transaction price",
            "Expiry: when your right expires worthless",
            "Premium: the price you pay for that right",
          ]}
          accent={accent}
          icon="⚙️"
        />
      ),
    },

    // Scene 3 (70s) — Payoff diagram concept (what is it, why it matters)
    {
      durationInFrames: sec(70),
      render: () => (
        <PayoffDiagramScene
          heading="The Payoff Diagram"
          subheading="Profit and loss at expiry — the single most important chart in options"
          legs={[{ type: "long-call", strike: 185, premium: 3.5 }]}
          priceMin={160}
          priceMax={215}
          currentPrice={185}
          accent={accent}
          footnote="Premium of $350 (3.50 × 100) is your maximum loss. Upside is theoretically unlimited."
        />
      ),
    },

    // Scene 4 (55s) — Watch the payoff line animate
    {
      durationInFrames: sec(55),
      render: () => (
        <PayoffDiagramScene
          heading="Long Call vs Long Put: Mirror Images"
          subheading="Same mechanics, opposite direction"
          legs={[
            { type: "long-call", strike: 185, premium: 3.5 },
            { type: "long-put", strike: 185, premium: 3.5 },
          ]}
          priceMin={160}
          priceMax={215}
          currentPrice={185}
          accent={accent}
          footnote="Call profits when price rises past breakeven. Put profits when price falls below breakeven."
        />
      ),
    },

    // Scene 5 (40s) — Contract anatomy
    {
      durationInFrames: sec(40),
      render: () => (
        <BulletScene
          heading="One Contract = 100 Shares"
          bullets={[
            "Premium quoted per share — multiply by 100 for actual cost",
            "$3.50 premium = $350 out of pocket per contract",
            "Multiplier is fixed: always 100 shares per equity option",
            "One contract controls the same position a $18,500 stock buyer has",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 6 (85s) — Real numbers calculation
    {
      durationInFrames: sec(85),
      render: () => (
        <CalculationScene
          heading="The Trade in Real Numbers"
          steps={[
            { label: "Stock price", formula: "AAPL trading at", result: "$185.00" },
            { label: "You buy", formula: "1 × $185 call, expiry 30 days", result: "@$3.50" },
            { label: "Total cost", formula: "$3.50 × 100 shares", result: "$350", highlight: true },
            { label: "Breakeven at expiry", formula: "$185 strike + $3.50 premium", result: "$188.50" },
            { label: "If AAPL closes at $195", formula: "($195 − $185 − $3.50) × 100", result: "+$650", highlight: true, color: "#22c55e" },
            { label: "If AAPL closes at $180", formula: "Option expires worthless", result: "-$350", color: "#ef4444" },
          ]}
          conclusion="Maximum loss is always the premium paid. Maximum gain is theoretically unlimited."
          accent={accent}
        />
      ),
    },

    // Scene 7 (40s) — The three numbers that matter
    {
      durationInFrames: sec(40),
      render: () => (
        <ComparisonTableScene
          heading="The Three Numbers That Define Every Option"
          subheading="Strike × Premium × Expiry = complete position"
          columns={["Parameter", "Controls", "Affects"]}
          rows={[
            { cells: ["Strike", "Entry price of stock transaction", "Breakeven, intrinsic value"], highlight: false },
            { cells: ["Premium", "Cost of the right (×100)", "Max loss, ROI calculation"], highlight: true, winner: 1 },
            { cells: ["Expiry", "How long you have this right", "Time value, theta decay rate"], highlight: false },
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 8 (55s) — The beginner trap
    {
      durationInFrames: sec(55),
      render: () => (
        <MistakeHighlightScene
          heading="The Trap That Catches Most Beginners"
          mistake={{
            label: "Confusing intrinsic and time value",
            detail: "An option priced at $3.50 when the stock is exactly at the strike has ZERO intrinsic value. The entire $3.50 is time value that erodes to zero at expiry.",
          }}
          correction={{
            label: "Price is always intrinsic + time value",
            detail: "Intrinsic: how much the option is worth if exercised right now. Time value: the optionality premium the market charges. Both decay as expiry approaches.",
          }}
          insight="At expiry, time value = zero. Options price converges to pure intrinsic value. This is why buying options with 1 day left is extremely risky."
          accent={accent}
        />
      ),
    },

    // Scene 9 (70s) — Tesla harder example
    {
      durationInFrames: sec(70),
      render: () => (
        <WorkedExampleScene
          heading="A Harder Example: Tesla Earnings Play"
          subheading="Buying a call before earnings — step by step"
          company="Tesla"
          ticker="TSLA"
          trades={[
            { day: "Day 0", event: "TSLA at $240, earnings in 7 days", action: "Buy 1× $245 call @ $6.00", pl: -600, cumPl: -600 },
            { day: "Day 5", event: "Pre-earnings IV spike, option still OTM", action: "Option now worth $9.50 (IV up 40%)", pl: 350, cumPl: -250 },
            { day: "Day 7", event: "TSLA reports — beats estimates", action: "TSLA opens at $268, option worth $24.50", pl: 1850, cumPl: 1600 },
            { day: "Day 7", event: "IV crush post-earnings (drops 35%)", action: "Hold: option drops to $18.00 as IV collapses", pl: -650, cumPl: 950 },
            { day: "Day 7", event: "Sell before close", action: "Close position @ $18.00", pl: 0, cumPl: 1200 },
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 10 (25s) — Cross-topic connections
    {
      durationInFrames: sec(25),
      render: () => (
        <BulletScene
          heading="How This Connects to the Rest of Options"
          bullets={[
            "Delta: how much does the option value change per $1 stock move?",
            "Theta: how much time value erodes per day?",
            "Vega: how much does IV change the premium?",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 11 (40s) — Four rules
    {
      durationInFrames: sec(40),
      render: () => (
        <SummaryScene
          heading="Four Rules to Take With You"
          takeaways={[
            "Premium × 100 = your actual cash at risk, always",
            "Breakeven = strike + premium (calls) or strike minus premium (puts)",
            "Time value erodes to zero at expiry — hold too long and it disappears",
            "IV spike before earnings can profit even when the stock does not move",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 12 (25s) — Closing scenario
    {
      durationInFrames: sec(25),
      render: () => (
        <RealWorldExampleScene
          heading="Your Closing Scenario"
          company="Practice Trade"
          scenario="NVDA at $900, you buy a $920 call expiring in 3 weeks, premium $12.00"
          setupItems={[
            { label: "Cost", value: "$1,200", color: "#ef4444" },
            { label: "Breakeven", value: "$932.00" },
            { label: "Max Loss", value: "$1,200", color: "#ef4444" },
          ]}
          outcome="NVDA reaches $950 before expiry"
          outcomeDetail="Option worth $30.00 at minimum intrinsic. Return: +$1,800 on $1,200 invested (+150%)"
          outcomeColor="#22c55e"
          accent={accent}
        />
      ),
    },

    // Scene 13 (25s) — Breakeven math
    {
      durationInFrames: sec(25),
      render: () => (
        <CalculationScene
          heading="The $185 Call Breakeven Math"
          steps={[
            { label: "Strike", formula: "AAPL $185 call", result: "$185.00" },
            { label: "Premium", formula: "Cost per share", result: "$3.50" },
            { label: "Breakeven", formula: "$185.00 + $3.50", result: "$188.50", highlight: true },
            { label: "At $188.50", formula: "($188.50 − $185 − $3.50) × 100", result: "$0", color: "#94a3b8" },
          ]}
          conclusion="Every dollar above $188.50 is pure profit. Every dollar below is loss up to your $350 max."
          accent={accent}
        />
      ),
    },

    // Scene 14 (25s) — Closing
    {
      durationInFrames: sec(25),
      render: () => (
        <SummaryScene
          heading="What You Now Understand"
          takeaways={[
            "Payoff diagrams: your primary decision tool",
            "Calls and puts: same structure, opposite direction",
            "Real math: premium, strike, breakeven, outcome",
          ]}
          accent={accent}
          closingLine="Next: how delta, theta and vega shift this diagram in real time."
        />
      ),
    },
  ];

  return (
    <SceneManager
      scenes={scenes}
      theme={{
        bg: "#080c12",
        accent,
        textPrimary: "#f8fafc",
        textSecondary: "#94a3b8",
      }}
    />
  );
};
