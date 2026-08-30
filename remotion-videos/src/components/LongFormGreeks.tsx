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
  StatsScene,
  SetupScene,
  SvgLineChartScene,
  type SceneDef,
} from "./SceneSystem";

const FPS = 30;
const sec = (s: number) => Math.round((s + 0.5) * FPS);

// ── IntroGreeksLong ───────────────────────────────────────────────────────────
// Lesson: intro-greeks — "Meet the Five Greeks"

export type IntroGreeksLongProps = {
  accent?: string;
};

export const IntroGreeksLong: React.FC<IntroGreeksLongProps> = ({ accent = "#6366f1" }) => {
  useVideoConfig();

  const scenes: SceneDef[] = [
    // Scene 1 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <TitleScene
          label="Options Greeks"
          title="Five Numbers That Define Every Option"
          subtitle="Delta Gamma Theta Vega and Rho explained with real trades"
          accent={accent}
        />
      ),
    },

    // Scene 2 (20s)
    {
      durationInFrames: sec(20),
      render: () => (
        <BulletScene
          heading="Why Greeks Are Your Trading Dashboard"
          bullets={[
            "Delta: how much the option moves per one dollar stock move",
            "Gamma: how fast delta accelerates as stock price shifts",
            "Theta: the daily dollar cost of holding this option open",
            "Vega: how much implied volatility swings change your premium",
            "Rho: how much a one percent rate change alters your option price",
          ]}
          accent={accent}
          icon="🎛️"
        />
      ),
    },

    // Scene 3 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <ComparisonTableScene
          heading="The Five Greeks: Quick Reference"
          subheading="AAPL 185 call with 30 days to expiry and IV at 28 percent"
          columns={["Greek", "Symbol", "Typical Range", "Who Cares Most"]}
          rows={[
            { cells: ["Delta", "Δ", "0 to 1 (calls)", "Directional traders"], winner: 2 },
            { cells: ["Gamma", "Γ", "0.01 to 0.15", "Scalpers near expiry"], winner: 2 },
            { cells: ["Theta", "Θ", "0.03 to 0.30", "Option sellers"], winner: 3, highlight: true },
            { cells: ["Vega", "ν", "0.05 to 0.25", "Earnings players"], winner: 2 },
            { cells: ["Rho", "ρ", "0.01 to 0.30", "LEAPS holders"], winner: 3 },
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 4 (60s)
    {
      durationInFrames: sec(60),
      render: () => (
        <CalculationScene
          heading="Delta in Real Numbers: The AAPL Example"
          steps={[
            { label: "Stock", formula: "AAPL current price", result: "$185.00" },
            { label: "Option", formula: "185 call, 30 days, IV 28%", result: "@ $3.50" },
            { label: "Delta", formula: "ATM call delta", result: "0.52", highlight: true },
            { label: "Stock moves up $1", formula: "Option gain = delta × 100", result: "+$52" },
            { label: "Stock moves down $2", formula: "Option loss = 0.52 × 200", result: "−$104", color: "#ef4444" },
            { label: "Key insight", formula: "Delta = approx probability ITM", result: "52%", highlight: true },
          ]}
          conclusion="Each dollar the stock moves shifts your option price by delta times 100 dollars."
          accent={accent}
        />
      ),
    },

    // Scene 5 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <CalculationScene
          heading="Theta: The Daily Clock Cost"
          steps={[
            { label: "Premium paid", formula: "AAPL 185 call", result: "$3.50" },
            { label: "Theta at 30 DTE", formula: "Cost per calendar day", result: "−$0.08" },
            { label: "Theta at 14 DTE", formula: "Decay accelerates", result: "−$0.14" },
            { label: "Theta at 7 DTE", formula: "Near expiry spike", result: "−$0.22" },
            { label: "Total 30 day cost", formula: "Average theta × days", result: "−$3.20", highlight: true, color: "#ef4444" },
            { label: "Remaining value day before expiry", formula: "$3.50 minus $3.20", result: "$0.30" },
          ]}
          conclusion="Theta steals most of your premium in the final two weeks. Hold long options past day 21 at your own risk."
          accent={accent}
        />
      ),
    },

    // Scene 6 (65s)
    {
      durationInFrames: sec(65),
      render: () => (
        <SvgLineChartScene
          heading="Theta Decay Curve: Time Value by Days to Expiry"
          subheading="AAPL 185 ATM call, IV 28%, starting premium $3.50"
          data={[
            { label: "90", value: 3.50 },
            { label: "60", value: 3.10 },
            { label: "45", value: 2.60 },
            { label: "30", value: 2.00 },
            { label: "21", value: 1.50 },
            { label: "14", value: 1.00 },
            { label: "7", value: 0.55 },
            { label: "3", value: 0.25 },
            { label: "1", value: 0.08 },
            { label: "0", value: 0.00 },
          ]}
          accent={accent}
          yLabel="Time Value ($)"
          xLabel="Days to Expiry"
          highlightIdx={4}
          footnote="The final 21 days lose more value than the first 69 days combined."
        />
      ),
    },

    // Scene 7 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <PayoffDiagramScene
          heading="Delta at Work: How the Payoff Slope Equals Delta"
          subheading="185 call at expiry. Slope of profit line = 1.0 (delta becomes 1 deep ITM)"
          legs={[{ type: "long-call", strike: 185, premium: 3.5 }]}
          priceMin={160}
          priceMax={215}
          currentPrice={185}
          accent={accent}
          footnote="At expiry delta is 0 below 185 and 1 above 185. Before expiry it transitions smoothly around 0.50 at the money."
        />
      ),
    },

    // Scene 8 (70s)
    {
      durationInFrames: sec(70),
      render: () => (
        <WorkedExampleScene
          heading="Live Greeks Through an NVDA Trade"
          subheading="Tracking delta gamma theta and vega day by day"
          company="NVIDIA"
          ticker="NVDA"
          trades={[
            { day: "Day 1", event: "Buy NVDA 500 call, 21 DTE, IV 45%", action: "Premium $12.00, delta 0.48, theta −0.35, vega 0.28", pl: -1200, cumPl: -1200 },
            { day: "Day 5", event: "NVDA rallies $15 to $515", action: "Delta now 0.68, option worth $18.50", pl: 650, cumPl: -550 },
            { day: "Day 10", event: "Flat market, theta eating value", action: "NVDA $515, option now $14.00 (theta cost $4.50)", pl: -450, cumPl: -1000 },
            { day: "Day 15", event: "IV spikes 8 points before product launch", action: "Option worth $17.00 (vega added $2.24)", pl: 300, cumPl: -700 },
            { day: "Day 20", event: "Sell before expiry weekend theta spike", action: "Close at $16.00, final exit", pl: -100, cumPl: -800 },
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 9 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <MistakeHighlightScene
          heading="The Greek Mistake That Drains Accounts"
          mistake={{
            label: "Ignoring theta when buying options",
            detail: "Many beginners buy cheap options with 7 days left because the premium looks small. At 7 DTE theta is at its steepest and the option loses 3 to 5 percent of its value every single day.",
          }}
          correction={{
            label: "Check the theta to premium ratio before entering",
            detail: "Divide daily theta by option premium. If that ratio exceeds 3 percent per day you are paying a steep time tax. Only buy near expiry if you expect a large immediate move.",
          }}
          insight="Theta does not sleep on weekends. An option worth $1.00 Friday loses roughly $0.06 over Saturday and Sunday with no stock movement required."
          accent={accent}
        />
      ),
    },

    // Scene 10 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <StatsScene
          heading="Greeks Snapshot: AAPL 185 Call at 30 DTE"
          stats={[
            { label: "Delta", value: "0.52", color: "#6366f1" },
            { label: "Gamma", value: "0.08", color: "#22c55e" },
            { label: "Theta", value: "−$0.08", color: "#ef4444" },
            { label: "Vega", value: "+$0.18", color: "#f59e0b" },
            { label: "Rho", value: "+$0.12", color: "#a855f7" },
          ]}
          accent={accent}
          footnote="These values change every day as stock price, time, and volatility shift."
        />
      ),
    },

    // Scene 11 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <BulletScene
          heading="How to Use Greeks Together"
          bullets={[
            "Enter trades when delta gives enough directional exposure (0.40 to 0.60 for balanced plays)",
            "Check theta before buying: avoid options losing more than 2 percent of premium per day",
            "Use vega to judge earnings plays: high vega means earnings crush will hurt you",
            "Gamma tells you how fast your position is changing: high gamma near expiry means rapid swings",
            "Rho matters for LEAPS: a 2 percent rate rise can shift a 2 year LEAPS by 50 cents",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 12 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <SummaryScene
          heading="Five Greeks, One Trading Edge"
          takeaways={[
            "Delta is your directional exposure and probability gauge",
            "Theta is a daily tax: time is always working against option buyers",
            "Vega is the IV multiplier: high IV pays sellers and punishes buyers",
            "Gamma accelerates your delta near expiry: powerful but dangerous",
            "Understanding all five together separates informed traders from guessers",
          ]}
          accent={accent}
          closingLine="Next: Delta scaling and hedging complete portfolios."
        />
      ),
    },

    // Scene 13 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <RealWorldExampleScene
          heading="Putting Greeks to Work: The Earnings Filter"
          company="Pre Earnings Screen"
          scenario="Stock with IV rank above 75: vega risk is high. Buy a put spread instead of a naked put to cap your vega exposure."
          setupItems={[
            { label: "IV Rank", value: "82%", color: "#f59e0b" },
            { label: "Vega", value: "$0.28" },
            { label: "Theta", value: "−$0.12" },
            { label: "Delta", value: "−0.45" },
          ]}
          outcome="Spread caps vega exposure"
          outcomeDetail="Buying a put spread reduces vega by 60 percent while keeping most of the directional delta. Theta also improves because the short leg earns time decay."
          outcomeColor="#22c55e"
          accent={accent}
        />
      ),
    },
  ];

  return (
    <SceneManager
      scenes={scenes}
      theme={{ bg: "#080c12", accent, textPrimary: "#f8fafc", textSecondary: "#94a3b8" }}
    />
  );
};

// ── DeltaScalingLong ──────────────────────────────────────────────────────────
// Lesson: delta-scaling — "Delta: Your Position's Leverage Dial"

export type DeltaScalingLongProps = {
  accent?: string;
};

export const DeltaScalingLong: React.FC<DeltaScalingLongProps> = ({ accent = "#6366f1" }) => {
  useVideoConfig();

  const scenes: SceneDef[] = [
    // Scene 1 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <TitleScene
          label="Options Delta"
          title="Delta: Your Position Leverage Dial"
          subtitle="How one number controls your risk and your hedge"
          accent={accent}
        />
      ),
    },

    // Scene 2 (20s)
    {
      durationInFrames: sec(20),
      render: () => (
        <BulletScene
          heading="Four Things Delta Tells You"
          bullets={[
            "Dollar sensitivity: option gains this many dollars per $1 stock move",
            "Probability: delta approximately equals the chance of expiring in the money",
            "Hedge ratio: shares to sell to neutralize a directional position",
            "Equivalent shares: 10 calls × delta × 100 equals your stock exposure",
          ]}
          accent={accent}
          icon="⚖️"
        />
      ),
    },

    // Scene 3 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <ComparisonTableScene
          heading="Delta by Strike and Moneyness"
          subheading="AAPL 30 day options with stock at $185"
          columns={["Strike", "Moneyness", "Call Delta", "Put Delta"]}
          rows={[
            { cells: ["$170", "Deep ITM", "0.87", "−0.13"] },
            { cells: ["$180", "Slightly ITM", "0.64", "−0.36"] },
            { cells: ["$185", "At the Money", "0.52", "−0.48"], highlight: true, winner: 2 },
            { cells: ["$190", "Slightly OTM", "0.38", "−0.62"] },
            { cells: ["$200", "Deep OTM", "0.15", "−0.85"] },
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 4 (60s)
    {
      durationInFrames: sec(60),
      render: () => (
        <CalculationScene
          heading="Portfolio Delta: 10 Contract Position"
          steps={[
            { label: "Position", formula: "10 AAPL 185 calls", result: "10 contracts" },
            { label: "Delta per option", formula: "ATM call delta", result: "0.52" },
            { label: "Shares equivalent", formula: "10 × 0.52 × 100", result: "520 shares", highlight: true },
            { label: "At $185 per share", formula: "520 × $185", result: "$96,200 exposure" },
            { label: "If AAPL moves up $5", formula: "520 × $5", result: "+$2,600" },
            { label: "If AAPL moves down $5", formula: "520 × $5", result: "−$2,600", color: "#ef4444" },
          ]}
          conclusion="10 call contracts at delta 0.52 give you the same directional exposure as owning 520 shares of AAPL."
          accent={accent}
        />
      ),
    },

    // Scene 5 (65s)
    {
      durationInFrames: sec(65),
      render: () => (
        <CalculationScene
          heading="Delta Neutral Hedge: Eliminating Directionality"
          steps={[
            { label: "Starting position", formula: "10 AAPL 185 calls, delta 0.52", result: "Long 520 delta" },
            { label: "To hedge, sell shares", formula: "Sell 520 shares of AAPL", result: "Short 520 delta" },
            { label: "Net portfolio delta", formula: "520 long minus 520 short", result: "0 (neutral)", highlight: true },
            { label: "Cost to hedge", formula: "520 × $185 × margin", result: "~$48,100" },
            { label: "Daily rebalancing cost", formula: "Gamma shift requires daily trade", result: "$40 to $150" },
            { label: "Why do this", formula: "Earn theta without directional risk", result: "Pure time decay" },
          ]}
          conclusion="Delta neutral means stock direction does not matter. You profit from theta and volatility changes instead."
          accent={accent}
        />
      ),
    },

    // Scene 6 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <PayoffDiagramScene
          heading="Delta Comparison: OTM vs ATM vs ITM Calls"
          subheading="Three AAPL calls expiring in 30 days. Notice how slope steepens as you go deeper ITM."
          legs={[
            { type: "long-call", strike: 200, premium: 0.80 },
            { type: "long-call", strike: 185, premium: 3.50 },
            { type: "long-call", strike: 170, premium: 15.50 },
          ]}
          priceMin={160}
          priceMax={215}
          currentPrice={185}
          accent={accent}
          footnote="OTM (200 strike) has a shallow slope because delta is only 0.15. ITM (170 strike) tracks stock almost one for one."
        />
      ),
    },

    // Scene 7 (70s)
    {
      durationInFrames: sec(70),
      render: () => (
        <WorkedExampleScene
          heading="Delta Scalping: Staying Neutral Through a Volatile Day"
          subheading="Market maker style delta management on SPY options"
          company="S&P 500 ETF"
          ticker="SPY"
          trades={[
            { day: "9:30am", event: "Buy 50 SPY 500 straddles, delta near zero", action: "Position: long 50 calls + 50 puts, net delta 5", pl: 0, cumPl: 0 },
            { day: "10:15am", event: "SPY rallies to $505, delta drifts to +200", action: "Sell 200 SPY shares to rebalance to zero delta", pl: 300, cumPl: 300 },
            { day: "11:30am", event: "SPY drops back to $498, delta now −150", action: "Buy 150 SPY shares to rebalance", pl: 450, cumPl: 750 },
            { day: "2:00pm", event: "SPY closes at $501, IV unchanged", action: "Both legs worth slightly less. Theta collected $180.", pl: 180, cumPl: 930 },
            { day: "Close", event: "Unwind straddles at end of day", action: "Sell both legs, realize theta gain minus slippage", pl: -120, cumPl: 810 },
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 8 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <MistakeHighlightScene
          heading="The Delta Drift Trap"
          mistake={{
            label: "Setting delta neutral and never rebalancing",
            detail: "A position that starts at zero delta will drift as the stock moves. Gamma moves the delta constantly. After a $5 stock move your delta could be 200 or more and you are no longer hedged.",
          }}
          correction={{
            label: "Rebalance delta at fixed intervals or thresholds",
            detail: "Professional traders rebalance when delta drifts more than 50 shares equivalent. For retail traders with smaller positions, rebalancing daily at market close is often practical enough.",
          }}
          insight="Delta hedging has a cost: every rebalance trade pays spread. The benefit must exceed the transaction cost or the hedge destroys value instead of protecting it."
          accent={accent}
        />
      ),
    },

    // Scene 9 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <StatsScene
          heading="Delta Facts Worth Memorizing"
          stats={[
            { label: "ATM delta", value: "~0.50", color: "#6366f1" },
            { label: "ITM delta approaches", value: "1.00", color: "#22c55e" },
            { label: "OTM delta approaches", value: "0.00", color: "#ef4444" },
            { label: "Put delta range", value: "−1 to 0", color: "#f59e0b" },
          ]}
          accent={accent}
          footnote="Call deltas sum to 1 with put deltas at same strike: 0.52 call plus 0.48 put equals 1."
        />
      ),
    },

    // Scene 10 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <SvgLineChartScene
          heading="Delta Curve: ATM to ITM as Stock Rallies"
          data={[
            { label: "160", value: 0.08 },
            { label: "165", value: 0.12 },
            { label: "170", value: 0.19 },
            { label: "175", value: 0.28 },
            { label: "180", value: 0.38 },
            { label: "185", value: 0.50 },
            { label: "190", value: 0.62 },
            { label: "195", value: 0.72 },
            { label: "200", value: 0.80 },
            { label: "205", value: 0.87 },
            { label: "210", value: 0.93 },
          ]}
          accent={accent}
          yLabel="Delta"
          xLabel="Stock Price ($)"
          highlightIdx={5}
          footnote="This S curve is the cumulative normal distribution from Black Scholes. It flattens out near 0 and 1 at the extremes."
        />
      ),
    },

    // Scene 11 (35s)
    {
      durationInFrames: sec(35),
      render: () => (
        <BulletScene
          heading="Delta Rules for Practical Trading"
          bullets={[
            "Never buy options with delta below 0.25 unless you expect a very large move",
            "10 options contracts with delta 0.50 is equivalent to 500 shares of stock",
            "Monitor portfolio delta daily: it shifts with every stock price change",
            "Delta approaching 1.0 means the option behaves like stock but with limited downside",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 12 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <SummaryScene
          heading="Delta: The Foundation of Position Sizing"
          takeaways={[
            "Delta measures dollar sensitivity per $1 stock move times 100 shares",
            "Portfolio delta is the sum of all individual option deltas",
            "Delta neutral positions profit from theta and vega not stock direction",
            "Rebalancing delta is not free: each trade has a spread cost to account for",
          ]}
          accent={accent}
          closingLine="Next: Theta clock and the accelerating cost of holding options."
        />
      ),
    },

    // Scene 13 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <RealWorldExampleScene
          heading="Delta on a Covered Call"
          company="Income Strategy"
          scenario="Own 100 AAPL shares and sell a 195 call. The short call has delta 0.28. Your effective net delta is 0.72 instead of 1.0."
          setupItems={[
            { label: "Stock delta", value: "1.00" },
            { label: "Short call delta", value: "−0.28", color: "#ef4444" },
            { label: "Net delta", value: "0.72", color: "#6366f1" },
          ]}
          outcome="Capped upside, cushioned downside"
          outcomeDetail="If AAPL rallies to $195 you earn $185 to $195 gain on 72 delta equivalent. Above $195 the short call limits your profit. You collected $1.10 premium as income."
          outcomeColor="#22c55e"
          accent={accent}
        />
      ),
    },
  ];

  return (
    <SceneManager
      scenes={scenes}
      theme={{ bg: "#080c12", accent, textPrimary: "#f8fafc", textSecondary: "#94a3b8" }}
    />
  );
};

// ── ThetaClockLong ────────────────────────────────────────────────────────────
// Lesson: theta-clock — "The Clock That Eats Your Premium"

export type ThetaClockLongProps = {
  accent?: string;
};

export const ThetaClockLong: React.FC<ThetaClockLongProps> = ({ accent = "#f59e0b" }) => {
  useVideoConfig();

  const scenes: SceneDef[] = [
    // Scene 1 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <TitleScene
          label="Options Theta"
          title="The Clock That Eats Your Premium"
          subtitle="Why time is always working against option buyers"
          accent={accent}
        />
      ),
    },

    // Scene 2 (20s)
    {
      durationInFrames: sec(20),
      render: () => (
        <BulletScene
          heading="What Theta Means in Plain English"
          bullets={[
            "Theta is the daily dollar amount your option loses due to time passing alone",
            "An option with theta of 0.08 loses 8 cents per share (8 dollars per contract) every single day",
            "Theta accelerates: it is small at 90 DTE and massive at 7 DTE",
            "Theta benefits sellers and hurts buyers, it is the core income of selling strategies",
            "Weekend theta: two days of decay happen between Friday close and Monday open",
          ]}
          accent={accent}
          icon="⏰"
        />
      ),
    },

    // Scene 3 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <CalculationScene
          heading="Theta by Days to Expiry: The AAPL 185 Call"
          steps={[
            { label: "90 DTE", formula: "Time value: $4.80", result: "−$0.04/day" },
            { label: "60 DTE", formula: "Time value: $4.20", result: "−$0.05/day" },
            { label: "30 DTE", formula: "Time value: $3.00", result: "−$0.08/day" },
            { label: "21 DTE", formula: "Time value: $2.20", result: "−$0.12/day" },
            { label: "14 DTE", formula: "Time value: $1.30", result: "−$0.16/day" },
            { label: "7 DTE", formula: "Time value: $0.55", result: "−$0.28/day", highlight: true, color: "#ef4444" },
            { label: "1 DTE", formula: "Time value: $0.08", result: "−$0.08 remaining" },
          ]}
          conclusion="The last 21 days destroy more premium than the first 69 days combined. Theta is not linear, it is exponential."
          accent={accent}
        />
      ),
    },

    // Scene 4 (65s)
    {
      durationInFrames: sec(65),
      render: () => (
        <SvgLineChartScene
          heading="Theta Decay Curve: Premium Lost by DTE"
          subheading="AAPL 185 ATM call starting at $5.00 time value"
          data={[
            { label: "90", value: 5.00 },
            { label: "75", value: 4.50 },
            { label: "60", value: 3.90 },
            { label: "45", value: 3.20 },
            { label: "30", value: 2.40 },
            { label: "21", value: 1.65 },
            { label: "14", value: 1.00 },
            { label: "7", value: 0.48 },
            { label: "3", value: 0.18 },
            { label: "1", value: 0.06 },
            { label: "0", value: 0.00 },
          ]}
          accent={accent}
          yLabel="Time Value ($)"
          xLabel="Days to Expiry"
          highlightIdx={4}
          footnote="Notice the sharp drop in the final 21 days. This is not a bug: it is the mathematical structure of option pricing."
        />
      ),
    },

    // Scene 5 (60s)
    {
      durationInFrames: sec(60),
      render: () => (
        <PayoffDiagramScene
          heading="Short Call Payoff: Theta Working for You"
          subheading="Selling the AAPL 185 call collects $3.50. Theta earns you money every day if stock stays below breakeven."
          legs={[{ type: "short-call", strike: 185, premium: 3.5 }]}
          priceMin={165}
          priceMax={210}
          currentPrice={185}
          accent={accent}
          footnote="The seller of this call earns $0.08 per share ($8 per contract) every single day from theta alone, assuming stock stays flat."
        />
      ),
    },

    // Scene 6 (70s)
    {
      durationInFrames: sec(70),
      render: () => (
        <WorkedExampleScene
          heading="Theta Calendar Play: Selling Weekly Against Monthly"
          subheading="Selling 7 DTE calls against a 30 DTE long position"
          company="Calendar Trade"
          ticker="QQQ"
          trades={[
            { day: "Week 1", event: "Buy QQQ 380 call expiring in 30 days for $4.80", action: "Long theta negative position: losing $0.12 per day", pl: -840, cumPl: -840 },
            { day: "Week 1", event: "Sell QQQ 380 call expiring in 7 days for $1.80", action: "Short theta positive: earning $0.28 per day", pl: 1800, cumPl: 960 },
            { day: "Week 1 end", event: "7 DTE call expires worthless (QQQ flat at $380)", action: "Collected full $1.80 premium from short call", pl: 1800, cumPl: 2760 },
            { day: "Week 2", event: "Sell another QQQ 380 call for 7 days at $1.65", action: "Repeat the theta harvest on the long call", pl: 1650, cumPl: 4410 },
            { day: "Week 3", event: "QQQ drops to $374 and short call already expired", action: "Long call still alive with 9 days left. Close at $2.80.", pl: 2800, cumPl: 7210 },
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 7 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <MistakeHighlightScene
          heading="The Theta Trap: Holding Too Long"
          mistake={{
            label: "Holding options past the 21 DTE threshold",
            detail: "A trader buys an AAPL call with 45 days left. They are right about direction: AAPL stays flat for 25 days then rallies. But by day 25 the option has lost 40 percent of its time value to theta. A small rally does not overcome the theta drag.",
          }}
          correction={{
            label: "Set a DTE exit rule before entering",
            detail: "Many professionals close long options at 21 DTE regardless of profit. If you are right about direction, close and re enter with more time. The cost of rolling is always less than the cost of holding through the final theta cliff.",
          }}
          insight="The 21 day rule is not arbitrary. At 21 DTE gamma spikes and theta accelerates together. Volatility events near expiry can move options dramatically in either direction, amplifying the time decay pain."
          accent={accent}
        />
      ),
    },

    // Scene 8 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <StatsScene
          heading="Theta Reality Check: What You Actually Lose"
          stats={[
            { label: "7 DTE theta", value: "−3% per day", color: "#ef4444" },
            { label: "21 DTE theta", value: "−1.5% per day", color: "#f59e0b" },
            { label: "45 DTE theta", value: "−0.6% per day", color: "#22c55e" },
            { label: "90 DTE theta", value: "−0.35% per day", color: "#6366f1" },
          ]}
          accent={accent}
          footnote="These percentages are of premium value, not premium dollars. A 7 DTE option worth $1.00 loses 3 cents every day."
        />
      ),
    },

    // Scene 9 (45s)
    {
      durationInFrames: sec(45),
      render: () => (
        <CalculationScene
          heading="Weekend Theta: The Silent Monday Loss"
          steps={[
            { label: "Friday close", formula: "Option price at end of day", result: "$2.40" },
            { label: "Theta per day", formula: "Current daily theta", result: "−$0.14" },
            { label: "Weekend days", formula: "Saturday + Sunday = 2 calendar days", result: "2 days" },
            { label: "Monday open loss", formula: "2 × $0.14 (plus small premium for Monday)", result: "−$0.28", highlight: true, color: "#ef4444" },
            { label: "Monday open expected price", formula: "$2.40 minus $0.28", result: "~$2.12" },
          ]}
          conclusion="Buying options Thursday evening and selling Monday morning is a theta trap. The market charges you for two days of time with no chance to profit overnight."
          accent={accent}
        />
      ),
    },

    // Scene 10 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <BulletScene
          heading="Theta Strategy Rules That Work"
          bullets={[
            "Sell options with 30 to 45 DTE to capture the steepest part of the theta curve",
            "Close short options at 21 DTE to avoid gamma risk even if you could earn more",
            "For long options enter with at least 45 DTE to limit theta cost per day",
            "Calendar spreads earn net theta: short near expiry and long further out",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 11 (35s)
    {
      durationInFrames: sec(35),
      render: () => (
        <ComparisonTableScene
          heading="Theta for Sellers vs Buyers"
          columns={["Strategy", "DTE", "Daily Theta", "Net Effect"]}
          rows={[
            { cells: ["Long call", "30 DTE", "−$0.08", "You pay"] },
            { cells: ["Short call", "30 DTE", "+$0.08", "You earn"], winner: 3 },
            { cells: ["Long straddle", "30 DTE", "−$0.16", "2x pay"] },
            { cells: ["Iron condor", "30 DTE", "+$0.22", "Net earn"], winner: 3 },
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 12 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <SummaryScene
          heading="Theta: The Tax You Pay to Participate"
          takeaways={[
            "Theta decay is exponential: the final 21 days cost more than the first 69 combined",
            "Sellers earn theta, buyers pay it. Structure trades accordingly.",
            "The 21 DTE exit rule protects long option holders from the steepest decay period",
            "Weekend theta silently reduces Monday open prices with no chance to react",
          ]}
          accent={accent}
          closingLine="Next: Gamma acceleration and how delta changes faster near expiry."
        />
      ),
    },

    // Scene 13 (45s)
    {
      durationInFrames: sec(45),
      render: () => (
        <RealWorldExampleScene
          heading="Theta Income Strategy: The Covered Call"
          company="Covered Call Example"
          scenario="Own 100 shares of MSFT at $415. Sell the 430 call expiring in 21 days for $2.80. Theta earns you $0.13 per day."
          setupItems={[
            { label: "Premium collected", value: "$280" },
            { label: "Theta per day", value: "+$0.13", color: "#22c55e" },
            { label: "Breakeven", value: "$417.80" },
            { label: "Max profit", value: "$430.00" },
          ]}
          outcome="21 days of theta income collected"
          outcomeDetail="If MSFT stays below $430 at expiry you keep the full $280 premium. If MSFT rallies above $430 your shares get called away at $430 but you still keep the premium."
          outcomeColor="#22c55e"
          accent={accent}
        />
      ),
    },
  ];

  return (
    <SceneManager
      scenes={scenes}
      theme={{ bg: "#080c12", accent, textPrimary: "#f8fafc", textSecondary: "#94a3b8" }}
    />
  );
};

// ── GammaAccelerationLong ─────────────────────────────────────────────────────
// Lesson: gamma-acceleration — "Gamma: How Delta Changes"

export type GammaAccelerationLongProps = {
  accent?: string;
};

export const GammaAccelerationLong: React.FC<GammaAccelerationLongProps> = ({ accent = "#22c55e" }) => {
  useVideoConfig();

  const scenes: SceneDef[] = [
    // Scene 1 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <TitleScene
          label="Options Gamma"
          title="Gamma: How Delta Changes"
          subtitle="The acceleration force that makes near expiry options explosive"
          accent={accent}
        />
      ),
    },

    // Scene 2 (20s)
    {
      durationInFrames: sec(20),
      render: () => (
        <BulletScene
          heading="Gamma in Plain English"
          bullets={[
            "Gamma measures how much delta changes when stock moves one dollar",
            "A gamma of 0.08 means: every dollar the stock moves, delta shifts by 0.08",
            "High gamma = rapid change in your directional exposure",
            "Gamma peaks at ATM and spikes dramatically in the final week before expiry",
            "Short gamma sellers get hurt when stock makes large rapid moves",
          ]}
          accent={accent}
          icon="⚡"
        />
      ),
    },

    // Scene 3 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <ComparisonTableScene
          heading="Gamma by Strike: NVDA $500 Options at 30 DTE"
          subheading="Stock at $500, IV at 45 percent"
          columns={["Strike", "Moneyness", "Gamma", "What It Means"]}
          rows={[
            { cells: ["$480", "Deep OTM", "0.003", "Delta barely shifts"] },
            { cells: ["$490", "Slightly OTM", "0.012", "Moderate acceleration"] },
            { cells: ["$500", "ATM", "0.018", "Maximum gamma"], highlight: true, winner: 3 },
            { cells: ["$510", "Slightly ITM", "0.013", "Decelerating"] },
            { cells: ["$520", "Deep ITM", "0.004", "Almost like stock"] },
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 4 (60s)
    {
      durationInFrames: sec(60),
      render: () => (
        <CalculationScene
          heading="Gamma in Action: NVDA $500 Call"
          steps={[
            { label: "Starting delta", formula: "NVDA 500 call, ATM, 30 DTE", result: "0.50" },
            { label: "NVDA moves up $5", formula: "Delta change = 5 × gamma 0.018", result: "+0.09" },
            { label: "New delta after $5 rally", formula: "0.50 + 0.09", result: "0.59", highlight: true },
            { label: "NVDA moves up another $5", formula: "Delta change at new level", result: "+0.07" },
            { label: "Delta at $510", formula: "Accumulated delta", result: "0.66" },
            { label: "Practical meaning", formula: "10 contracts now = 660 share equiv", result: "Was 500" },
          ]}
          conclusion="Gamma means your position automatically gets more aggressive as the stock moves in your favor. 10 contracts become more powerful without you doing anything."
          accent={accent}
        />
      ),
    },

    // Scene 5 (65s)
    {
      durationInFrames: sec(65),
      render: () => (
        <SvgLineChartScene
          heading="Gamma Curve: Peaks Sharply at ATM Near Expiry"
          subheading="NVDA 500 call gamma as stock price varies from $450 to $550"
          data={[
            { label: "450", value: 0.001 },
            { label: "460", value: 0.003 },
            { label: "470", value: 0.007 },
            { label: "480", value: 0.012 },
            { label: "490", value: 0.016 },
            { label: "500", value: 0.018 },
            { label: "510", value: 0.015 },
            { label: "520", value: 0.010 },
            { label: "530", value: 0.006 },
            { label: "540", value: 0.003 },
            { label: "550", value: 0.001 },
          ]}
          accent={accent}
          yLabel="Gamma"
          xLabel="Stock Price ($)"
          highlightIdx={5}
          footnote="This bell curve shape means gamma is most dangerous and most powerful at the money. Deep ITM or OTM options have almost no gamma."
        />
      ),
    },

    // Scene 6 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <CalculationScene
          heading="7 DTE Gamma Explosion vs 30 DTE"
          steps={[
            { label: "30 DTE ATM gamma", formula: "SPY 500 call, 30 days", result: "0.018" },
            { label: "7 DTE ATM gamma", formula: "Same strike, 7 days left", result: "0.055" },
            { label: "1 DTE ATM gamma", formula: "Expiry tomorrow", result: "0.180" },
            { label: "Delta shift from $2 move (30 DTE)", formula: "2 × 0.018", result: "+0.036" },
            { label: "Delta shift from $2 move (1 DTE)", formula: "2 × 0.180", result: "+0.360", highlight: true, color: "#ef4444" },
            { label: "Interpretation", formula: "10 contracts shift by", result: "360 shares!" },
          ]}
          conclusion="At 1 DTE a $2 stock move shifts your effective stock exposure by 360 shares on 10 contracts. This is why expiry day is called gamma day."
          accent={accent}
        />
      ),
    },

    // Scene 7 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <PayoffDiagramScene
          heading="Short Gamma Risk: The Iron Condor Near Expiry"
          subheading="SPY iron condor 490/495/505/510. Gamma kills you if stock breaks out in final week."
          legs={[
            { type: "short-put", strike: 495, premium: 1.80 },
            { type: "long-put", strike: 490, premium: 0.80 },
            { type: "short-call", strike: 505, premium: 1.80 },
            { type: "long-call", strike: 510, premium: 0.80 },
          ]}
          priceMin={482}
          priceMax={518}
          currentPrice={500}
          accent={accent}
          footnote="Inside the 495 to 505 range you profit from theta. Outside that range gamma accelerates your losses rapidly."
        />
      ),
    },

    // Scene 8 (70s)
    {
      durationInFrames: sec(70),
      render: () => (
        <WorkedExampleScene
          heading="Gamma Squeeze: NVDA Before Options Expiry"
          subheading="How market maker hedging creates self fulfilling rallies"
          company="NVIDIA"
          ticker="NVDA"
          trades={[
            { day: "Monday", event: "NVDA at $498, large open interest at 500 strike", action: "Market makers are short 500 calls. Delta 0.45, gamma 0.015.", pl: 0, cumPl: 0 },
            { day: "Tuesday", event: "NVDA rallies to $503. Market makers must buy shares to hedge.", action: "Dealers buy $503 worth of NVDA to offset delta drift.", pl: 500, cumPl: 500 },
            { day: "Wednesday", event: "Buying pressure pushes NVDA to $508. More hedging needed.", action: "Gamma now 0.012 at 508. More shares bought by dealers.", pl: 800, cumPl: 1300 },
            { day: "Thursday", event: "NVDA at $512. Short call sellers panic and buy back.", action: "Forced covering adds more upward pressure.", pl: 600, cumPl: 1900 },
            { day: "Friday", event: "Expiry: NVDA at $515. All 500 calls expire deep ITM.", action: "Gamma squeeze complete. Rally was partly self reinforcing.", pl: 300, cumPl: 2200 },
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 9 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <MistakeHighlightScene
          heading="The Gamma Blind Spot"
          mistake={{
            label: "Selling short dated options without sizing for gamma",
            detail: "A trader sells 10 weekly SPY straddles on Monday. The premium looks attractive. But with 5 DTE the gamma is 0.045. A $3 SPY move shifts delta by 270 shares on 10 contracts. The position can swing $2,000 on a single intraday move.",
          }}
          correction={{
            label: "Reduce size when selling near expiry options",
            detail: "Professional gamma sellers trade 30 to 50 percent fewer contracts when DTE drops below 7. The high theta income near expiry comes with equally high gamma risk. Adjust your contract count to keep dollar gamma risk constant.",
          }}
          insight="Gamma and theta are always paired: high theta near expiry means high gamma. You cannot get one without the other. There is no free lunch in selling short dated options."
          accent={accent}
        />
      ),
    },

    // Scene 10 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <StatsScene
          heading="Gamma Risk at Different DTE"
          stats={[
            { label: "30 DTE gamma", value: "0.018", color: "#22c55e" },
            { label: "14 DTE gamma", value: "0.032", color: "#f59e0b" },
            { label: "7 DTE gamma", value: "0.055", color: "#ef4444" },
            { label: "1 DTE gamma", value: "0.180", color: "#ef4444" },
          ]}
          accent={accent}
          footnote="Each of these values assumes ATM options. OTM and ITM options have much lower gamma at every DTE."
        />
      ),
    },

    // Scene 11 (35s)
    {
      durationInFrames: sec(35),
      render: () => (
        <BulletScene
          heading="Gamma Rules for Safer Trading"
          bullets={[
            "Long gamma profits from large moves: perfect for pre earnings positions",
            "Short gamma collects theta but loses on big stock moves",
            "Reduce size as expiry approaches if you are short gamma",
            "Pin risk: if stock is near your short strike at expiry, gamma is enormous",
            "Use defined risk spreads to cap gamma exposure when selling near expiry",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 12 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <SummaryScene
          heading="Gamma: Acceleration You Cannot Ignore"
          takeaways={[
            "Gamma measures how fast delta changes per dollar of stock movement",
            "ATM options near expiry have the highest gamma: most explosive and most dangerous",
            "Long gamma positions benefit from large moves, short gamma from small moves",
            "Never ignore gamma when sizing positions with less than 7 days to expiry",
          ]}
          accent={accent}
          closingLine="Next: Vega sensitivity and how implied volatility changes your premium."
        />
      ),
    },

    // Scene 13 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <RealWorldExampleScene
          heading="Long Gamma Trade: Buying Before a Catalyst"
          company="Pre Earnings Position"
          scenario="NVDA reports earnings in 3 days. IV is 55%. Buy ATM straddle: pay $24 total ($12 call plus $12 put). Gamma is 0.021 ATM."
          setupItems={[
            { label: "Straddle cost", value: "$2,400" },
            { label: "Gamma", value: "0.021", color: "#22c55e" },
            { label: "Breakeven move", value: "$24" },
            { label: "DTE", value: "3 days" },
          ]}
          outcome="NVDA moves $35 on earnings"
          outcomeDetail="The $35 move exceeds the $24 breakeven by $11. Profit on straddle: $1,100 per contract. Gamma amplified the position as the stock moved through ATM and kept accelerating delta."
          outcomeColor="#22c55e"
          accent={accent}
        />
      ),
    },
  ];

  return (
    <SceneManager
      scenes={scenes}
      theme={{ bg: "#080c12", accent, textPrimary: "#f8fafc", textSecondary: "#94a3b8" }}
    />
  );
};

// ── VegaSensitivityLong ───────────────────────────────────────────────────────
// Lesson: vega-sensitivity — "Vega: The IV Premium You Pay"

export type VegaSensitivityLongProps = {
  accent?: string;
};

export const VegaSensitivityLong: React.FC<VegaSensitivityLongProps> = ({ accent = "#a855f7" }) => {
  useVideoConfig();

  const scenes: SceneDef[] = [
    // Scene 1 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <TitleScene
          label="Options Vega"
          title="Vega: The IV Premium You Pay"
          subtitle="Why implied volatility changes your option price even when the stock does not move"
          accent={accent}
        />
      ),
    },

    // Scene 2 (20s)
    {
      durationInFrames: sec(20),
      render: () => (
        <BulletScene
          heading="Vega in Three Sentences"
          bullets={[
            "Vega measures how much an option price changes when implied volatility moves by one percentage point",
            "A vega of 0.15 means: option price shifts by 15 cents for every 1% IV change",
            "Vega is highest for ATM options with the most time left: more uncertainty equals more vega sensitivity",
            "Earnings events cause massive IV spikes before and crushes after",
            "Understanding vega separates traders who profit from IV changes from those who are surprised by them",
          ]}
          accent={accent}
          icon="📊"
        />
      ),
    },

    // Scene 3 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <CalculationScene
          heading="Vega in Real Numbers: AAPL 30 DTE"
          steps={[
            { label: "Option", formula: "AAPL 185 call, 30 DTE", result: "$3.50" },
            { label: "Current IV", formula: "Implied volatility", result: "28%" },
            { label: "Vega", formula: "Price sensitivity per 1% IV", result: "$0.18" },
            { label: "IV rises to 35% (+7 points)", formula: "7 × $0.18", result: "+$1.26", highlight: true, color: "#22c55e" },
            { label: "New option price", formula: "$3.50 + $1.26", result: "$4.76" },
            { label: "IV falls to 22% (−6 points)", formula: "6 × $0.18", result: "−$1.08", color: "#ef4444" },
            { label: "New option price at low IV", formula: "$3.50 minus $1.08", result: "$2.42" },
          ]}
          conclusion="A 7 point IV increase earns you $1.26 per share even if AAPL does not move. That is 36% of your original premium for zero directional exposure."
          accent={accent}
        />
      ),
    },

    // Scene 4 (60s)
    {
      durationInFrames: sec(60),
      render: () => (
        <ComparisonTableScene
          heading="IV Percentile and What It Means for Options"
          subheading="IV rank shows where current IV sits in its 52 week range"
          columns={["IV Rank", "Situation", "Strategy", "Vega Play"]}
          rows={[
            { cells: ["0 to 20", "IV historically low", "Buy options (cheap)", "Long vega"], winner: 2 },
            { cells: ["20 to 40", "Normal range", "Balanced positions", "Monitor vega"] },
            { cells: ["40 to 60", "Above average", "Slight seller edge", "Short vega lightly"] },
            { cells: ["60 to 80", "High IV", "Sell spreads aggressively", "Short vega heavily"], highlight: true, winner: 3 },
            { cells: ["80 to 100", "Extreme IV", "Sell premium or wait", "Short vega max"] },
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 5 (65s)
    {
      durationInFrames: sec(65),
      render: () => (
        <SvgLineChartScene
          heading="Earnings IV Cycle: Before and After the Report"
          subheading="NVDA IV path over 6 weeks surrounding a major earnings event"
          data={[
            { label: "42 DTE", value: 38 },
            { label: "35 DTE", value: 42 },
            { label: "28 DTE", value: 48 },
            { label: "21 DTE", value: 55 },
            { label: "14 DTE", value: 62 },
            { label: "7 DTE", value: 72 },
            { label: "1 DTE", value: 80 },
            { label: "Earnings", value: 80 },
            { label: "Post +1", value: 42 },
            { label: "Post +7", value: 38 },
          ]}
          accent={accent}
          yLabel="Implied Volatility (%)"
          xLabel="Time to / from Earnings"
          highlightIdx={7}
          footnote="IV crush: the day after earnings IV drops 40 to 50 percent instantly. Option holders lose enormous vega value even when the stock moves in their favor."
        />
      ),
    },

    // Scene 6 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <PayoffDiagramScene
          heading="Long Straddle vs IV Crush: The Earnings Danger"
          subheading="Bought NVDA ATM straddle for $24 before earnings. IV crush kills value even on a $15 move."
          legs={[
            { type: "long-call", strike: 500, premium: 12 },
            { type: "long-put", strike: 500, premium: 12 },
          ]}
          priceMin={460}
          priceMax={540}
          currentPrice={500}
          accent={accent}
          footnote="The straddle needs a $24 move just to break even. If IV crushes 35% post earnings (losing $8.40 in vega value), you now need a $32.40 move to profit."
        />
      ),
    },

    // Scene 7 (60s)
    {
      durationInFrames: sec(60),
      render: () => (
        <WorkedExampleScene
          heading="Vega Trade: Buying IV Before an Earnings Spike"
          subheading="Entering a long vega position two weeks before AAPL earnings"
          company="Apple"
          ticker="AAPL"
          trades={[
            { day: "Day 1", event: "AAPL at $185, IV at 28%, earnings in 14 days", action: "Buy 5 straddles at $7.00 each ($700 × 5 = $3,500)", pl: -3500, cumPl: -3500 },
            { day: "Day 7", event: "IV rises to 36%, AAPL flat at $185", action: "Straddle worth $9.00 on vega alone (no stock move needed)", pl: 1000, cumPl: -2500 },
            { day: "Day 12", event: "IV at 42%, AAPL drops $3 to $182", action: "Straddle worth $11.50 (vega + delta gain)", pl: 1250, cumPl: -1250 },
            { day: "Day 13", event: "Sell before earnings: take IV profit, avoid crush", action: "Close at $11.50. Capture vega gain before risk.", pl: 2250, cumPl: 1000 },
            { day: "Day 14", event: "Earnings: AAPL misses by $0.03, drops $8", action: "IV crushes to 22%. Straddle worth $12.00 but vega lost $4.00.", pl: 0, cumPl: 1000 },
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 8 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <MistakeHighlightScene
          heading="The Vega Trap: Buying Options in High IV"
          mistake={{
            label: "Buying calls when IV rank is above 70",
            detail: "A trader sees NVDA rallying and buys calls when IV is 65%, well above its 52 week average of 40%. Even if NVDA keeps rallying, the IV reversion to 40% costs $2.50 per contract in vega value. The stock gain is partially eaten by the IV contraction.",
          }}
          correction={{
            label: "Check IV rank before buying: buy low IV and sell high IV",
            detail: "When IV rank is above 60 you are paying a premium above the long term average. Buy options with IV rank below 30 when you want a directional trade. When IV rank is above 70, sell spreads to collect the elevated vega.",
          }}
          insight="Vega is not just about earnings. Market wide volatility events like Fed meetings and macro data releases spike IV across all sectors simultaneously. Portfolio vega explodes before any major market event."
          accent={accent}
        />
      ),
    },

    // Scene 9 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <StatsScene
          heading="Vega Values: How Much IV Change Costs You"
          stats={[
            { label: "ATM vega (30 DTE)", value: "$0.18", color: "#a855f7" },
            { label: "ATM vega (90 DTE)", value: "$0.32", color: "#6366f1" },
            { label: "OTM vega (30 DTE)", value: "$0.08", color: "#22c55e" },
            { label: "Typical IV crush", value: "30 to 50%", color: "#ef4444" },
          ]}
          accent={accent}
          footnote="LEAPS options have massive vega because they have more time for IV to matter. A $1.00 vega LEAPS loses $30 if IV drops from 40% to 10%."
        />
      ),
    },

    // Scene 10 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <BulletScene
          heading="Vega Strategy Rules"
          bullets={[
            "Buy options when IV rank is below 30: you are paying fair or discounted vega",
            "Sell spreads when IV rank is above 70: collect the inflated vega premium",
            "Never hold through earnings if you do not understand the IV crush risk",
            "Use calendars to exploit vega term structure: sell near month high IV, buy far month low IV",
            "Calculate your portfolio vega exposure before any major market event",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 11 (35s)
    {
      durationInFrames: sec(35),
      render: () => (
        <ComparisonTableScene
          heading="Long Vega vs Short Vega Positions"
          columns={["Position", "Vega", "Benefits When", "Hurts When"]}
          rows={[
            { cells: ["Long call", "Positive", "IV rises", "IV falls"], winner: 2 },
            { cells: ["Short call", "Negative", "IV falls", "IV rises"], winner: 3 },
            { cells: ["Long straddle", "2x Positive", "IV spikes", "IV crushes"], winner: 2 },
            { cells: ["Iron condor", "Negative", "IV falls and stays low", "IV spikes"], winner: 3, highlight: true },
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 12 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <SummaryScene
          heading="Vega: Master IV and Master Options Pricing"
          takeaways={[
            "Vega is the IV multiplier on your option price: know it before every trade",
            "Buy options with low IV rank (below 30), sell options with high IV rank (above 70)",
            "Earnings IV crush can destroy a profitable trade even when direction is right",
            "Portfolio vega must be monitored before macro events like FOMC and CPI prints",
          ]}
          accent={accent}
          closingLine="Next: Rho and how interest rate changes affect LEAPS and longer dated options."
        />
      ),
    },

    // Scene 13 (45s)
    {
      durationInFrames: sec(45),
      render: () => (
        <RealWorldExampleScene
          heading="Short Vega Income: Selling an Iron Condor in High IV"
          company="High IV Market"
          scenario="SPY IV rank at 78%. Sell the 490/495/505/510 iron condor for $2.80 net credit. Vega on the position is negative 0.18."
          setupItems={[
            { label: "Net credit", value: "$280" },
            { label: "Vega exposure", value: "−0.18", color: "#22c55e" },
            { label: "Max profit", value: "$280" },
            { label: "Max loss", value: "$220" },
          ]}
          outcome="IV falls from 78th to 45th percentile"
          outcomeDetail="As IV normalizes from elevated levels your short vega position gains $0.33 from IV contraction alone (1.83 IV points × 0.18 vega). Combined with theta collected, total profit is $180 in 2 weeks."
          outcomeColor="#22c55e"
          accent={accent}
        />
      ),
    },
  ];

  return (
    <SceneManager
      scenes={scenes}
      theme={{ bg: "#080c12", accent, textPrimary: "#f8fafc", textSecondary: "#94a3b8" }}
    />
  );
};

// ── RhoRateRiskLong ───────────────────────────────────────────────────────────
// Lesson: rho-rate-risk — "Rho: How Interest Rates Move Options"

export type RhoRateRiskLongProps = {
  accent?: string;
};

export const RhoRateRiskLong: React.FC<RhoRateRiskLongProps> = ({ accent = "#14b8a6" }) => {
  useVideoConfig();

  const scenes: SceneDef[] = [
    // Scene 1 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <TitleScene
          label="Options Rho"
          title="Rho: How Interest Rates Move Options"
          subtitle="The least discussed Greek becomes critical for LEAPS and high rate environments"
          accent={accent}
        />
      ),
    },

    // Scene 2 (20s)
    {
      durationInFrames: sec(20),
      render: () => (
        <BulletScene
          heading="Why Rho Matters in 2024 and Beyond"
          bullets={[
            "Rho measures option price sensitivity to a one percent change in the risk free interest rate",
            "Call options benefit from higher rates: carrying stock is more expensive, so calls are preferred",
            "Put options lose value when rates rise: the discount on the future put payoff increases",
            "The effect is tiny for short dated options but significant for LEAPS and multi year positions",
            "In a high rate environment like 2023 to 2025, rho is the largest Greek surprise for unprepared traders",
          ]}
          accent={accent}
          icon="📈"
        />
      ),
    },

    // Scene 3 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <CalculationScene
          heading="Rho in Numbers: AAPL 2 Year LEAPS Call"
          steps={[
            { label: "Option", formula: "AAPL 185 call, 2 years to expiry", result: "$28.50" },
            { label: "Rho", formula: "Price change per 1% rate change", result: "+$0.25" },
            { label: "Rates rise 1% (e.g., Fed hike)", formula: "1 × $0.25", result: "+$0.25" },
            { label: "Rates rise 2% total", formula: "2 × $0.25", result: "+$0.50", highlight: true, color: "#22c55e" },
            { label: "Rates fall 1% (Fed cut)", formula: "1 × $0.25", result: "−$0.25", color: "#ef4444" },
            { label: "4 rate cuts × 0.25%", formula: "1% total rate reduction", result: "−$0.25" },
          ]}
          conclusion="A 1% rate change on a 2 year LEAPS call changes your option price by $0.25 per share or $25 per contract. Not huge on a single contract but meaningful across a portfolio."
          accent={accent}
        />
      ),
    },

    // Scene 4 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <ComparisonTableScene
          heading="Rho by Option Type and Expiry"
          columns={["Option", "Expiry", "Rho", "Rate Impact per 1%"]}
          rows={[
            { cells: ["AAPL call", "30 DTE", "0.04", "+$4 per contract"] },
            { cells: ["AAPL call", "90 DTE", "0.12", "+$12 per contract"] },
            { cells: ["AAPL call", "1 year", "0.22", "+$22 per contract"] },
            { cells: ["AAPL call", "2 years LEAPS", "0.25", "+$25 per contract"], highlight: true, winner: 3 },
            { cells: ["AAPL put", "30 DTE", "−0.03", "−$3 per contract"] },
            { cells: ["AAPL put", "2 years", "−0.20", "−$20 per contract"] },
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 5 (60s)
    {
      durationInFrames: sec(60),
      render: () => (
        <SvgLineChartScene
          heading="Rho Effect: LEAPS Call Price as Rates Change"
          subheading="AAPL 185 call with 2 years to expiry at different rate levels"
          data={[
            { label: "1%", value: 22.50 },
            { label: "2%", value: 24.00 },
            { label: "3%", value: 25.80 },
            { label: "4%", value: 27.50 },
            { label: "5%", value: 28.50 },
            { label: "6%", value: 29.50 },
            { label: "7%", value: 30.20 },
            { label: "8%", value: 30.80 },
          ]}
          accent={accent}
          yLabel="Call Price ($)"
          xLabel="Risk Free Rate (%)"
          highlightIdx={4}
          footnote="The rate effect compounds over 2 years. A 1% rise from 5% to 6% adds $1.00 to the LEAPS call because of rho plus the time value shift."
        />
      ),
    },

    // Scene 6 (65s)
    {
      durationInFrames: sec(65),
      render: () => (
        <WorkedExampleScene
          heading="LEAPS Trade Through a Rate Cycle"
          subheading="Holding AAPL 2 year LEAPS through the 2022 to 2024 rate cycle"
          company="Apple LEAPS"
          ticker="AAPL"
          trades={[
            { day: "Jan 2022", event: "Fed funds rate at 0.25%. Buy AAPL LEAPS 185 call for $28.00", action: "Rho 0.24, low rates. Delta 0.62, IV 28%.", pl: -2800, cumPl: -2800 },
            { day: "Jul 2022", event: "Fed hikes to 2.5%. AAPL drops to $163.", action: "Rho adds $0.58 (2.25% rate rise). Delta loss −$1,355.", pl: -797, cumPl: -3597 },
            { day: "Feb 2023", event: "Fed at 4.75%. AAPL recovers to $180.", action: "Rho total gain $1.08. AAPL rally adds delta gain $1,240.", pl: 443, cumPl: -3154 },
            { day: "Oct 2023", event: "Fed at 5.25%. AAPL at $171 then rallies to $189.", action: "LEAPS worth $26.50. Rho has added $1.20 total.", pl: -50, cumPl: -3204 },
            { day: "Jan 2024", event: "AAPL at $195. Rate cuts expected.", action: "LEAPS worth $38.50. Sell and take profit despite rate headwind.", pl: 1200, cumPl: -2004 },
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 7 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <MistakeHighlightScene
          heading="The Rho Surprise in a Hiking Cycle"
          mistake={{
            label: "Buying long dated puts during a Fed hiking cycle",
            detail: "A trader buys 2 year AAPL puts to hedge a stock portfolio when the Fed starts hiking. The put rho is negative 0.20. As the Fed hikes 4 times by 1%, the puts lose $80 per contract in rho value alone before the stock even moves. The hedge underperforms badly.",
          }}
          correction={{
            label: "Use shorter dated puts for directional hedges in high rate environments",
            detail: "For hedging in a rising rate environment, use 90 day puts rolled quarterly rather than LEAPS puts. The short dated puts have rho near zero so rate moves do not erode the hedge value. Roll before expiry to maintain protection.",
          }}
          insight="In the 2022 to 2023 hiking cycle, LEAPS puts lost 15 to 25% of their value purely from rho as rates rose 5.25%. Traders who did not account for rho were confused why their hedges kept shrinking."
          accent={accent}
        />
      ),
    },

    // Scene 8 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <StatsScene
          heading="Rho Snapshot: Current Market Context"
          stats={[
            { label: "Fed funds rate", value: "5.25%", color: "#14b8a6" },
            { label: "AAPL 2yr LEAPS rho", value: "+0.25", color: "#22c55e" },
            { label: "AAPL 2yr put rho", value: "−0.20", color: "#ef4444" },
            { label: "Rate impact (1%)", value: "$20 to $25", color: "#f59e0b" },
          ]}
          accent={accent}
          footnote="Rho matters most for LEAPS and any position held across FOMC meeting dates. Short dated options have rho near zero."
        />
      ),
    },

    // Scene 9 (45s)
    {
      durationInFrames: sec(45),
      render: () => (
        <CalculationScene
          heading="Put Rho: The Hedge That Shrinks in Rate Hikes"
          steps={[
            { label: "AAPL 2yr put", formula: "Strike $185, rho −0.20", result: "Worth $22.00" },
            { label: "Fed hikes 0.25%", formula: "Rho effect = 0.25 × $0.20", result: "−$0.05 per hike" },
            { label: "Four consecutive hikes (1%)", formula: "4 × 0.05", result: "−$0.20" },
            { label: "Put value after 4 hikes", formula: "$22.00 minus $0.20", result: "$21.80" },
            { label: "12 hikes (3% total in 2022)", formula: "12 × 0.05", result: "−$0.60", color: "#ef4444" },
            { label: "Hedge lost 2.7% to rho alone", formula: "$0.60 of $22.00", result: "Small but real" },
          ]}
          conclusion="In the 2022 cycle with 475 basis points of hikes, LEAPS put holders lost roughly $0.95 per contract in rho value silently."
          accent={accent}
        />
      ),
    },

    // Scene 10 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <BulletScene
          heading="Rho Risk Management Rules"
          bullets={[
            "Check rho before entering LEAPS or any position with more than 6 months to expiry",
            "Before FOMC meetings assess your portfolio rho: know if you benefit or hurt from rate changes",
            "Calls benefit from rate rises, puts are hurt by rate rises: remember this at every Fed meeting",
            "For LEAPS trading in a volatile rate environment, trade closer to ATM where rho is more predictable",
            "Rho is often the last Greek checked but the first surprise in macro driven markets",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 11 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <SummaryScene
          heading="Rho: The Rate Risk You Cannot Afford to Ignore"
          takeaways={[
            "Rho is small for short dated options but material for LEAPS over 6 months",
            "Call rho is positive: higher rates make calls more valuable",
            "Put rho is negative: higher rates make puts less valuable",
            "In a hiking cycle, long dated put hedges silently shrink from rho before the stock moves",
          ]}
          accent={accent}
          closingLine="Next: Black Scholes pricing model and how all Greeks combine into a single theoretical price."
        />
      ),
    },

    // Scene 12 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <RealWorldExampleScene
          heading="FOMC Day Rho Impact on a LEAPS Portfolio"
          company="Rate Sensitive Portfolio"
          scenario="Hold 10 AAPL 2 year LEAPS calls with total rho of 2.50 dollars per 1 percent rate change. Fed cuts 0.25 percent at FOMC meeting."
          setupItems={[
            { label: "Total LEAPS position", value: "10 contracts" },
            { label: "Total rho", value: "$2.50" },
            { label: "Rate change", value: "−0.25%" },
            { label: "Expected rho gain", value: "−$0.63" },
          ]}
          outcome="Rate cut of 0.25% hurts LEAPS calls"
          outcomeDetail="Counterintuitively a rate cut reduces call option value via rho. The $2.50 total rho loses 0.25 of 1% change, or $62.50 per 1 percent unit. On a 0.25% cut that is minus $62.50 from rho alone. Delta from any rally offsets this."
          outcomeColor="#14b8a6"
          accent={accent}
        />
      ),
    },

    // Scene 13 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <ComparisonTableScene
          heading="Rho vs Other Greeks: Relative Importance"
          columns={["Greek", "30 DTE Impact", "1 Year Impact", "2 Year Impact"]}
          rows={[
            { cells: ["Delta", "Major", "Major", "Major"], winner: 1 },
            { cells: ["Theta", "Major", "Moderate", "Minor"], winner: 1 },
            { cells: ["Gamma", "Critical near ATM", "Moderate", "Minor"], winner: 1 },
            { cells: ["Vega", "High", "High", "High"], winner: 2 },
            { cells: ["Rho", "Minor", "Moderate", "Major"], highlight: true, winner: 3 },
          ]}
          accent={accent}
        />
      ),
    },
  ];

  return (
    <SceneManager
      scenes={scenes}
      theme={{ bg: "#080c12", accent, textPrimary: "#f8fafc", textSecondary: "#94a3b8" }}
    />
  );
};

// ── BlackScholesPricingLong ───────────────────────────────────────────────────
// Lesson: black-scholes-pricing — "What Black Scholes Actually Tells You"

export type BlackScholesPricingLongProps = {
  accent?: string;
};

export const BlackScholesPricingLong: React.FC<BlackScholesPricingLongProps> = ({ accent = "#ec4899" }) => {
  useVideoConfig();

  const scenes: SceneDef[] = [
    // Scene 1 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <TitleScene
          label="Options Pricing"
          title="What Black Scholes Actually Tells You"
          subtitle="Five inputs one price and why the model is both brilliant and limited"
          accent={accent}
        />
      ),
    },

    // Scene 2 (20s)
    {
      durationInFrames: sec(20),
      render: () => (
        <BulletScene
          heading="The Five Inputs to Black Scholes"
          bullets={[
            "S: current stock price (the underlying asset price right now)",
            "K: strike price (the agreed upon transaction price in the contract)",
            "T: time to expiry (in years: 30 days = 0.082 years)",
            "r: risk free interest rate (typically 90 day Treasury bill yield)",
            "σ: implied volatility (annualized standard deviation of returns: the market's fear gauge)",
          ]}
          accent={accent}
          icon="🔢"
        />
      ),
    },

    // Scene 3 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <CalculationScene
          heading="Walking Through Black Scholes: AAPL 185 Call"
          steps={[
            { label: "S (Stock price)", formula: "AAPL current price", result: "$185.00" },
            { label: "K (Strike price)", formula: "Contract strike", result: "$185.00" },
            { label: "T (Time to expiry)", formula: "30 days ÷ 365", result: "0.082 years" },
            { label: "r (Risk free rate)", formula: "3 month T bill yield", result: "5.25%" },
            { label: "σ (Implied volatility)", formula: "Market implied vol", result: "28%" },
            { label: "BSM call price output", formula: "Theoretical fair value", result: "$3.54", highlight: true },
          ]}
          conclusion="The market price of $3.50 is almost exactly equal to the theoretical BSM price of $3.54. When they differ significantly, traders look for mispricing opportunities."
          accent={accent}
        />
      ),
    },

    // Scene 4 (60s)
    {
      durationInFrames: sec(60),
      render: () => (
        <ComparisonTableScene
          heading="How Each Input Shifts the Option Price"
          subheading="Effect of changing one input by a fixed amount while holding others constant"
          columns={["Input", "Change", "Call Price Effect", "Put Price Effect"]}
          rows={[
            { cells: ["Stock price +$5", "S from 185 to 190", "+$2.60", "+$0.80"], winner: 2 },
            { cells: ["Strike +$5", "K from 185 to 190", "−$1.90", "−$0.80"] },
            { cells: ["Time +30 days", "T from 30 to 60 days", "+$0.90", "+$0.90"] },
            { cells: ["Rate +1%", "r from 5.25% to 6.25%", "+$0.05", "−$0.04"] },
            { cells: ["IV +5%", "σ from 28% to 33%", "+$0.90", "+$0.90"], highlight: true, winner: 2 },
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 5 (65s)
    {
      durationInFrames: sec(65),
      render: () => (
        <SvgLineChartScene
          heading="BSM Price vs Stock Price: The Option Price Curve"
          subheading="AAPL 185 call (30 DTE, IV 28%) theoretical price at different stock levels"
          data={[
            { label: "160", value: 0.08 },
            { label: "165", value: 0.22 },
            { label: "170", value: 0.55 },
            { label: "175", value: 1.15 },
            { label: "180", value: 2.10 },
            { label: "185", value: 3.54 },
            { label: "190", value: 5.50 },
            { label: "195", value: 7.80 },
            { label: "200", value: 10.30 },
            { label: "205", value: 13.00 },
            { label: "210", value: 15.80 },
          ]}
          accent={accent}
          yLabel="Option Price ($)"
          xLabel="Stock Price ($)"
          highlightIdx={5}
          footnote="This curve is convex (bows upward). The slope at any point equals delta. The curvature (how fast slope changes) equals gamma."
        />
      ),
    },

    // Scene 6 (60s)
    {
      durationInFrames: sec(60),
      render: () => (
        <WorkedExampleScene
          heading="BSM Mispricing Trade: IV Arbitrage"
          subheading="When market price diverges from BSM theoretical value"
          company="Volatility Arb"
          ticker="AAPL"
          trades={[
            { day: "Monday", event: "AAPL 185 call (30 DTE) at $4.20 in market, BSM says $3.54 at IV 28%", action: "Market IV is actually 32.5% implied by $4.20 price", pl: 0, cumPl: 0 },
            { day: "Monday", event: "IV rank is 85th percentile (above normal). Rich premium.", action: "Sell 5 calls at $4.20 and buy 260 shares to hedge delta", pl: 2100, cumPl: 2100 },
            { day: "Wednesday", event: "IV reverts from 32.5% to 29%. Options cheapen.", action: "Buy back calls at $3.55. Close delta hedge.", pl: 325, cumPl: 2425 },
            { day: "Total", event: "Net P&L: $4.20 sold minus $3.55 bought = $0.65 per share", action: "5 contracts × 100 × $0.65 = $325 profit", pl: 325, cumPl: 2750 },
            { day: "Key lesson", event: "BSM does not predict direction but identifies rich vs cheap vol", action: "Sell when market IV exceeds BSM IV at fair vol", pl: 0, cumPl: 2750 },
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 7 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <MistakeHighlightScene
          heading="The Black Scholes Misconception"
          mistake={{
            label: "Treating BSM price as the true correct option price",
            detail: "Black Scholes assumes constant volatility, no dividends, continuous trading, and normally distributed returns. In reality volatility is not constant (the vol smile proves this), dividends affect pricing, and stocks can gap overnight. BSM is an approximation, not a law.",
          }}
          correction={{
            label: "Use BSM as a relative value benchmark, not an absolute truth",
            detail: "Professional traders use BSM to find options that are priced at higher IV than they historically realize, then sell those. They also use it to identify when IV is low historically and options are cheap enough to buy. BSM is a starting point, not an endpoint.",
          }}
          insight="The 1987 market crash shattered confidence in BSM because the model predicted far smaller moves were possible than what actually occurred. Today traders add skew adjustments and use more realistic vol models built on BSM's foundation."
          accent={accent}
        />
      ),
    },

    // Scene 8 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <StatsScene
          heading="BSM vs Market Reality"
          stats={[
            { label: "BSM assumes vol is", value: "Constant", color: "#ef4444" },
            { label: "Actual vol varies", value: "Daily", color: "#22c55e" },
            { label: "BSM assumes returns are", value: "Normal", color: "#ef4444" },
            { label: "Actual returns have", value: "Fat tails", color: "#f59e0b" },
          ]}
          accent={accent}
          footnote="Despite its flaws BSM remains the universal language of options pricing. Every desk uses BSM derived Greeks even with more complex models running underneath."
        />
      ),
    },

    // Scene 9 (45s)
    {
      durationInFrames: sec(45),
      render: () => (
        <CalculationScene
          heading="Put Call Parity: The No Arbitrage Relationship"
          steps={[
            { label: "Put call parity formula", formula: "C − P = S − K × e^(−rT)", result: "Must hold" },
            { label: "Call price", formula: "AAPL 185 call, 30 DTE", result: "$3.54" },
            { label: "Put price (theoretical)", formula: "From put call parity", result: "$3.04" },
            { label: "Check: C − P", formula: "$3.54 minus $3.04", result: "$0.50" },
            { label: "S − K × discount", formula: "$185 minus $184.20 (K discounted)", result: "$0.80" },
            { label: "Arbitrage signal", formula: "If C − P ≠ S − K×e^−rT", result: "Buy cheap leg" },
          ]}
          conclusion="Put call parity is enforced by arbitrageurs. When it breaks briefly, market makers immediately buy the cheap option and sell the expensive one, closing the gap within seconds."
          accent={accent}
        />
      ),
    },

    // Scene 10 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <BulletScene
          heading="Using BSM Practically as a Trader"
          bullets={[
            "Check the implied volatility your option price is embedding using a BSM calculator",
            "Compare that IV to the stock's 30 day historical volatility to see if options are rich or cheap",
            "If IV is significantly above historical vol, options are overpriced and selling makes sense",
            "If IV is significantly below historical vol, options are cheap and buying is more favorable",
            "Every Greeks calculator in your broker is a BSM derivative: understanding the source makes the tool more useful",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 11 (35s)
    {
      durationInFrames: sec(35),
      render: () => (
        <ComparisonTableScene
          heading="Historical Vol vs Implied Vol: What It Means"
          columns={["Scenario", "HV", "IV", "Action"]}
          rows={[
            { cells: ["IV premium (normal)", "25%", "28%", "Slight sell edge"], winner: 3 },
            { cells: ["IV crush post earnings", "25%", "18%", "Buy cheap IV"], winner: 2, highlight: true },
            { cells: ["Crisis spike", "25%", "60%", "Sell rich IV"], winner: 3 },
            { cells: ["Low vol market", "12%", "10%", "Buy cheap options"], winner: 2 },
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 12 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <SummaryScene
          heading="Black Scholes: The Foundation You Cannot Skip"
          takeaways={[
            "Five inputs produce one theoretical price and five Greeks from a single model",
            "BSM is a benchmark for finding rich vs cheap vol, not a perfect price oracle",
            "Put call parity enforces a no arbitrage relationship between calls and puts",
            "Every broker's Greeks calculator and options pricing tool is built on BSM",
          ]}
          accent={accent}
          closingLine="Next: Bid ask reality and how spread costs affect every trade you take."
        />
      ),
    },

    // Scene 13 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <RealWorldExampleScene
          heading="BSM in Practice: Your Options Calculator"
          company="Practical Tool Usage"
          scenario="Before entering any options trade, use a BSM calculator (free on cboe.com or your broker) to find the theoretical price. Enter all 5 inputs and check if the market price is above or below theoretical."
          setupItems={[
            { label: "Inputs needed", value: "S, K, T, r, σ" },
            { label: "Time to set up", value: "60 seconds" },
            { label: "Typical IV edge", value: "1 to 5%" },
          ]}
          outcome="Know if you are buying rich or cheap vol"
          outcomeDetail="If the market price is $4.20 but BSM theoretical is $3.54 at 28% IV, then the market is pricing 32.5% IV. That is above the 52 week IV average of 30%. You are paying a premium. Sell spreads instead."
          outcomeColor="#ec4899"
          accent={accent}
        />
      ),
    },

    // Scene 14 (25s)
    {
      durationInFrames: sec(25),
      render: () => (
        <BulletScene
          heading="BSM Quick Reference Before Every Trade"
          bullets={[
            "Calculate implied IV from market price using a BSM calculator",
            "Compare to 30 day historical vol: is market vol above or below realized?",
            "Check IV rank (percentile) to put current IV in context",
            "Make the buy or sell decision based on whether options look cheap or expensive relative to history",
          ]}
          accent={accent}
        />
      ),
    },
  ];

  return (
    <SceneManager
      scenes={scenes}
      theme={{ bg: "#080c12", accent, textPrimary: "#f8fafc", textSecondary: "#94a3b8" }}
    />
  );
};
