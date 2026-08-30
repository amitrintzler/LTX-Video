import { AbsoluteFill, Sequence, useVideoConfig, interpolate, spring, useCurrentFrame } from "remotion";
import { CinematicIntro } from "./CinematicIntro";
import { GreekDial } from "./GreekDial";
import {
  SceneManager, TitleScene, BulletScene, SummaryScene,
  RealWorldExampleScene, SvgLineChartScene,
  type SceneDef
} from "./SceneSystem";
import React from "react";
import { TEMPLATE_STYLES } from "../lib/templateStyles";

const S = TEMPLATE_STYLES["greeks"];

export type GreekVisualizerProps = {
  title: string;
  subtitle: string;
  subjectLabel: string;
  posterUrl: string;
  accent: string;
  glow: string;
  greekName: "Intro" | "Delta" | "Gamma" | "Theta" | "Vega" | "Rho";
  startValue: number;
  endValue: number;
  explanation: string;
};

// ── Greek dial scene ─────────────────────────────────────────────────────────
const DialScene: React.FC<{
  greekName: string;
  startValue: number;
  endValue: number;
  accent: string;
  explanation: string;
}> = ({ greekName, startValue, endValue, accent, explanation }) => (
  <AbsoluteFill style={{ backgroundColor: S.bg, display: "flex", justifyContent: "center", alignItems: "center" }}>
    <div style={{ display: "flex", flexDirection: "row", alignItems: "center", gap: 80 }}>
      <GreekDial name={greekName} startValue={startValue} endValue={endValue} color={accent} size={380} />
      <div style={{ display: "flex", flexDirection: "column", gap: 20, maxWidth: 660 }}>
        <h2 style={{ fontSize: 64, fontWeight: 900, color: S.textPrimary, margin: 0 }}>{greekName}</h2>
        <p style={{ fontSize: 32, color: S.textSecondary, lineHeight: 1.6, margin: 0 }}>{explanation}</p>
      </div>
    </div>
  </AbsoluteFill>
);

// ── Per-greek data ─────────────────────────────────────────────────────────────
const GREEK_DATA: Record<string, {
  description: string;
  bullets: string[];
  chartData: Array<{ label: string; value: number }>;
  chartHeading: string;
  chartSubheading: string;
  chartXLabel: string;
  chartYLabel: string;
  chartHighlightIdx: number;
  chartFootnote: string;
  example: {
    heading: string;
    company: string;
    scenario: string;
    setupItems: Array<{ label: string; value: string; color?: string }>;
    outcome: string;
    outcomeDetail: string;
    outcomeColor: string;
  };
  takeaways: string[];
}> = {
  Intro: {
    description: "The five Greeks, Delta, Gamma, Theta, Vega, and Rho, are the five forces that determine how an option's price moves. Master them and you control your risk.",
    bullets: [
      "Delta: how much the option moves per $1 in the stock (directional exposure)",
      "Gamma: how fast delta changes, the accelerator pedal near expiry",
      "Theta: time decay, how much premium you lose each day you hold",
      "Vega: sensitivity to implied volatility changes, the IV risk factor",
    ],
    chartData: [
      { label: "Rho", value: 0.05 }, { label: "Gamma", value: 0.18 }, { label: "Vega", value: 0.35 },
      { label: "Theta", value: 0.55 }, { label: "Delta", value: 0.95 },
    ],
    chartHeading: "Greek Sensitivity: Relative Impact on a 45 DTE ATM Call",
    chartSubheading: "Normalized score showing which Greek drives the most P&L for a typical position",
    chartXLabel: "Greek",
    chartYLabel: "Relative Sensitivity",
    chartHighlightIdx: 4,
    chartFootnote: "Delta (★) dominates short term P&L. Vega matters more for longer dated options. Theta is always working against you as a buyer",
    example: {
      heading: "All 5 Greeks in One Trade",
      company: "AAPL 45 DTE ATM Call",
      scenario: "Bought AAPL $185 call (45 DTE) for $6.20 when stock was at $185. All 5 Greeks are live simultaneously, each one affects your P&L differently every day.",
      setupItems: [
        { label: "Delta", value: "0.52 (direction)", color: "#10b981" },
        { label: "Gamma", value: "0.04 (accelerator)", color: "#f43f5e" },
        { label: "Theta", value: "-$0.08/day", color: "#eab308" },
        { label: "Vega", value: "$0.14 per IV%", color: "#a855f7" },
        { label: "Rho", value: "$0.09 per 1%", color: "#0ea5e9" },
      ],
      outcome: "Greeks = your risk dashboard",
      outcomeDetail: "AAPL rises $5, Delta earns +$2.60. Gamma pushes delta to 0.60. Meanwhile Theta steals -$0.08/day. If IV drops 5%, Vega costs -$0.70. Understanding all 5 simultaneously is what separates options traders from gamblers.",
      outcomeColor: "#6366f1",
    },
    takeaways: [
      "Delta is your primary P&L driver on directional trades",
      "Theta works against you every day, have a time plan when buying",
      "Vega is the hidden risk most beginners ignore before earnings",
      "Greeks change as price, time, and IV change, they're always moving",
    ],
  },

  Delta: {
    description: "Delta measures how much an option's price changes for every $1 move in the underlying stock. It ranges from 0 to 1 for calls, and from -1 to 0 for puts.",
    bullets: [
      "Delta 0.50 = option gains $0.50 for every $1 the stock rises",
      "Deep ITM calls approach delta 1.0 and move dollar for dollar with the stock",
      "Far OTM calls have delta near 0 and are barely affected by small price moves",
      "Delta also approximates the probability of expiring in the money",
    ],
    chartData: [
      { label: "$130", value: 0.05 }, { label: "$140", value: 0.12 }, { label: "$148", value: 0.30 },
      { label: "$150★", value: 0.50 }, { label: "$152", value: 0.68 }, { label: "$160", value: 0.85 }, { label: "$170", value: 0.95 },
    ],
    chartHeading: "Delta vs. Underlying Price",
    chartSubheading: "Strike at $150, delta rises as stock moves from OTM to ITM",
    chartXLabel: "Stock Price",
    chartYLabel: "Delta",
    chartHighlightIdx: 3,
    chartFootnote: "ATM option (★) has delta ≈ 0.50, gains half of every dollar move",
    example: {
      heading: "Real Trade: Delta in Action",
      company: "AAPL Bullish Call Buy",
      scenario: "AAPL trading at $180. You buy a $185 call (25 DTE) for $3.50. The option has delta 0.38. AAPL earnings beat sends stock up $12 overnight.",
      setupItems: [
        { label: "Stock Price", value: "$180", color: "#94a3b8" },
        { label: "Strike", value: "$185", color: "#6366f1" },
        { label: "Premium Paid", value: "$3.50", color: "#f59e0b" },
        { label: "Delta", value: "0.38", color: "#10b981" },
        { label: "Stock Move", value: "+$12", color: "#10b981" },
      ],
      outcome: "+$4.56 per contract",
      outcomeDetail: "$12 × 0.38 delta = $4.56 gain. Option went from $3.50 to $8.06. +130% return on a 6.7% stock move. Leverage = delta working for you.",
      outcomeColor: "#10b981",
    },
    takeaways: [
      "Delta tells you your dollar exposure per $1 move in the stock",
      "Buy higher delta options for more stock-like behavior",
      "Use delta to size positions, equal delta = equal directional risk",
      "Delta changes as price moves, that change rate is gamma",
    ],
  },

  Gamma: {
    description: "Gamma measures the rate of change of delta, specifically how quickly delta shifts as the stock price moves. It is highest for ATM options near expiration.",
    bullets: [
      "High gamma = delta is changing rapidly with each price tick",
      "ATM options have the highest gamma, delta shifts most near the strike",
      "Gamma explodes in the final week before expiration",
      "Long options have positive gamma (helps you); short options have negative gamma (hurts you)",
    ],
    chartData: [
      { label: "$130", value: 0.01 }, { label: "$140", value: 0.04 }, { label: "$146", value: 0.10 },
      { label: "$150★", value: 0.18 }, { label: "$154", value: 0.11 }, { label: "$160", value: 0.04 }, { label: "$170", value: 0.01 },
    ],
    chartHeading: "Gamma vs. Underlying Price",
    chartSubheading: "Bell curve peaks at ATM strike ($150), gamma risk is highest here",
    chartXLabel: "Stock Price",
    chartYLabel: "Gamma",
    chartHighlightIdx: 3,
    chartFootnote: "ATM options (★) hold maximum gamma, small moves flip your delta fast near expiry",
    example: {
      heading: "Real Trade: Gamma Explosion",
      company: "SPY Short Put Near Expiry",
      scenario: "SPY at $450. You sold a $450 put expiring in 3 days for $1.20 credit. Gamma is 0.09. SPY drops $6 intraday on a surprise CPI print.",
      setupItems: [
        { label: "SPY Price", value: "$450", color: "#94a3b8" },
        { label: "Strike (Short)", value: "$450 Put", color: "#ef4444" },
        { label: "Credit", value: "$1.20", color: "#10b981" },
        { label: "Gamma", value: "0.09", color: "#f59e0b" },
        { label: "SPY Drop", value: "-$6", color: "#ef4444" },
      ],
      outcome: "-$3.40 loss",
      outcomeDetail: "Delta went from -0.50 to -0.78 as SPY fell. The $450 put jumped from $1.20 to $4.60. Gamma amplified losses 3x beyond what delta alone predicted. Short gamma means asymmetric pain.",
      outcomeColor: "#ef4444",
    },
    takeaways: [
      "Short ATM options near expiry carry the most gamma risk",
      "Positive gamma benefits you, your deltas accelerate in your favor",
      "Manage gamma by rolling positions before the final week",
      "Iron condors and calendars reduce gamma exposure vs naked shorts",
    ],
  },

  Theta: {
    description: "Theta measures time decay, specifically how much an option loses in value each day as it approaches expiration. It always works against option buyers.",
    bullets: [
      "Theta accelerates non-linearly, decay doubles in the last 30 days",
      "ATM options lose the most time value per day in absolute terms",
      "Selling options means theta works for you, you collect daily decay",
      "45 DTE is the sweet spot, theta starts accelerating and is still manageable",
    ],
    chartData: [
      { label: "60d", value: 4.00 }, { label: "45d", value: 3.52 }, { label: "30d", value: 2.90 },
      { label: "21d", value: 2.22 }, { label: "14d★", value: 1.48 }, { label: "7d", value: 0.72 }, { label: "0d", value: 0.00 },
    ],
    chartHeading: "Theta Decay, ATM Option Premium Over Time",
    chartSubheading: "TSLA $250 call, IV 45%, watch premium bleed accelerate near expiry",
    chartXLabel: "Days to Expiration",
    chartYLabel: "Premium ($)",
    chartHighlightIdx: 4,
    chartFootnote: "Last 14 days (★) = fastest decay. The final week alone bleeds ~50% of remaining time value.",
    example: {
      heading: "Real Trade: Theta Bleeding a Buyer",
      company: "TSLA Long Call Wrong Timing",
      scenario: "TSLA at $245, 30 DTE. You buy a $250 call for $4.00. Theta = -$0.08/day. TSLA chops sideways for 3 weeks with no big move.",
      setupItems: [
        { label: "Premium Paid", value: "$4.00", color: "#f59e0b" },
        { label: "Theta/Day", value: "-$0.08", color: "#ef4444" },
        { label: "Days Held", value: "21 days", color: "#94a3b8" },
        { label: "TSLA Move", value: "±$3", color: "#94a3b8" },
      ],
      outcome: "-$2.40 from theta",
      outcomeDetail: "21 days × $0.08/day = $1.68 theta loss. As expiry approached, theta accelerated to -$0.14/day. Total: option worth $1.60 even though TSLA barely moved. Time was the killer.",
      outcomeColor: "#ef4444",
    },
    takeaways: [
      "Buy options with enough DTE, at least 45 days for the thesis to develop",
      "Selling options at 45 DTE captures theta while IV is still rich",
      "Close short options at 50% profit, the remaining premium isn't worth gamma risk",
      "Theta decay is not linear, the last week decays the fastest",
    ],
  },

  Vega: {
    description: "Vega measures sensitivity to implied volatility. A 1% rise in IV increases option price by the vega amount, and long options want IV to rise.",
    bullets: [
      "Higher vega = option is more sensitive to volatility changes",
      "45 DTE options have roughly 3x more vega than 7 DTE options",
      "Buying before earnings is a vega bet, IV crush can destroy the trade after",
      "Sell high IV options and buy low IV options to profit from mean reversion",
    ],
    chartData: [
      { label: "IV 20%", value: 3.20 }, { label: "IV 30%", value: 4.80 }, { label: "IV 40%★", value: 6.40 },
      { label: "IV 50%", value: 8.00 }, { label: "IV 60%", value: 9.60 }, { label: "IV 70%", value: 11.20 }, { label: "IV 80%", value: 12.80 },
    ],
    chartHeading: "Option Price vs. Implied Volatility (45 DTE ATM Call)",
    chartSubheading: "Each 10% IV increase adds ~$1.60 to premium, vega = $0.16 per 1% IV move",
    chartXLabel: "Implied Volatility",
    chartYLabel: "Option Price ($)",
    chartHighlightIdx: 2,
    chartFootnote: "At IV 40% (★) the ATM call costs $6.40. At IV 80% (pre earnings) the same option costs $12.80.",
    example: {
      heading: "Real Trade: IV Crush After Earnings",
      company: "NVDA Earnings Trap",
      scenario: "NVDA at $480 before Q3 earnings. IV Rank = 82. You bought the $480 call for $18.40 (vega = $0.28). Earnings beat and NVDA jumped +$20 in after hours.",
      setupItems: [
        { label: "NVDA Price", value: "$480", color: "#94a3b8" },
        { label: "Premium", value: "$18.40", color: "#f59e0b" },
        { label: "Vega", value: "0.28", color: "#8b5cf6" },
        { label: "IV Before", value: "82%", color: "#ef4444" },
        { label: "IV After", value: "44%", color: "#10b981" },
        { label: "Stock Move", value: "+$20", color: "#10b981" },
      ],
      outcome: "Option worth $12.80",
      outcomeDetail: "Stock moved the right direction, but IV crashed 38 points. IV crush: 38 × $0.28 = $10.64 loss. Delta gain on +$20 move: +$8.80. Net: -$5.60. Right direction, wrong volatility timing.",
      outcomeColor: "#ef4444",
    },
    takeaways: [
      "Never buy options into earnings when IV Rank is above 60",
      "IV crush after a catalyst destroys even correct directional trades",
      "Sell premium (iron condors, credit spreads) when IV is elevated",
      "Use IV Rank to compare current IV to its historical range for that ticker",
    ],
  },

  Rho: {
    description: "Rho measures sensitivity to interest rate changes. It is small for short dated options but can be significant for LEAPS in changing rate environments.",
    bullets: [
      "Rising rates increase call values and decrease put values",
      "Rho is 8x larger for 1 year options vs. 30 day options",
      "Short dated options have negligible rho in most trading decisions",
      "In aggressive Fed tightening cycles, LEAPS holders see meaningful moves",
    ],
    chartData: [
      { label: "7d", value: 0.01 }, { label: "30d", value: 0.04 }, { label: "60d", value: 0.09 },
      { label: "90d", value: 0.14 }, { label: "180d", value: 0.28 }, { label: "270d", value: 0.42 }, { label: "365d★", value: 0.58 },
    ],
    chartHeading: "Rho vs. Days to Expiration",
    chartSubheading: "AAPL $190 call, ATM, rho scales steeply with time horizon",
    chartXLabel: "Days to Expiry",
    chartYLabel: "Rho (per 1% rate move)",
    chartHighlightIdx: 6,
    chartFootnote: "365 DTE LEAPS (★) gain $0.58 per 1% rate increase, 58x more than a 7 day option",
    example: {
      heading: "Real Trade: Rho on LEAPS in Rate Cycle",
      company: "SPY LEAPS During Fed Hike Cycle",
      scenario: "You hold 10 SPY LEAPS calls (1-year expiry, ATM). Each has rho = $0.52. The Fed raises rates by 0.75% in a single meeting (2022 style aggressive hike).",
      setupItems: [
        { label: "Contracts", value: "10 × 100", color: "#94a3b8" },
        { label: "Rho Each", value: "$0.52", color: "#6366f1" },
        { label: "Rate Hike", value: "+0.75%", color: "#f59e0b" },
        { label: "Notional", value: "1,000 shares", color: "#94a3b8" },
      ],
      outcome: "+$390 from rho",
      outcomeDetail: "0.75% rate hike × $0.52 rho × 10 contracts × 100 multiplier = +$390. In 2022, three 75bp hikes = +$1,170 rho contribution to your LEAPS position. Rho matters for long horizons.",
      outcomeColor: "#10b981",
    },
    takeaways: [
      "Rho is usually the least important Greek for short dated trades",
      "It becomes meaningful for LEAPS, factor it in for 6 to 12 month horizons",
      "Rising rates benefit call holders and hurt put holders on long dated options",
      "In a rate hiking cycle, LEAPS calls get a tailwind from rho",
    ],
  },
};

// ── Main component ──────────────────────────────────────────────────────────────
export const GreekVisualizerVideo = ({
  title, subtitle, subjectLabel, posterUrl, accent, glow,
  greekName, startValue, endValue, explanation,
}: GreekVisualizerProps) => {
  const { fps, durationInFrames } = useVideoConfig();
  const info = GREEK_DATA[greekName] || GREEK_DATA["Delta"];

  if (durationInFrames < 600) {
    return (
      <AbsoluteFill style={{ backgroundColor: S.bg, color: "white", fontFamily: "Inter, sans-serif" }}>
        <Sequence from={0} durationInFrames={4 * fps}>
          <CinematicIntro title={title} subtitle={subtitle} subjectLabel={subjectLabel} posterUrl={posterUrl} accent={accent} glow={glow} />
        </Sequence>
        <Sequence from={4 * fps} durationInFrames={8 * fps}>
          <DialScene greekName={greekName} startValue={startValue} endValue={endValue} accent={accent} explanation={explanation} />
        </Sequence>
      </AbsoluteFill>
    );
  }

  const ex = info.example;
  const scenes: SceneDef[] = [
    // Scene 1: Title + concept intro
    { render: () => <TitleScene label={`The Greeks: ${greekName}`} title={title} subtitle={info.description} accent={accent} /> },
    // Scene 2: How it works — bullet points
    { render: () => <BulletScene heading={`How ${greekName} Works`} bullets={info.bullets} accent={accent} /> },
    // Scene 3: Live dial visualization
    { durationInFrames: Math.floor(durationInFrames * 0.18), render: () => <DialScene greekName={greekName} startValue={startValue} endValue={endValue} accent={accent} explanation={explanation} /> },
    // Scene 4: Animated chart (price/time curve)
    { durationInFrames: Math.floor(durationInFrames * 0.22), render: () => (
      <SvgLineChartScene
        heading={info.chartHeading}
        subheading={info.chartSubheading}
        data={info.chartData}
        accent={accent}
        xLabel={info.chartXLabel}
        yLabel={info.chartYLabel}
        highlightIdx={info.chartHighlightIdx}
        footnote={info.chartFootnote}
      />
    )},
    // Scene 5: Real-world trade example
    { durationInFrames: Math.floor(durationInFrames * 0.26), render: () => (
      <RealWorldExampleScene
        heading={ex.heading}
        company={ex.company}
        scenario={ex.scenario}
        setupItems={ex.setupItems}
        outcome={ex.outcome}
        outcomeDetail={ex.outcomeDetail}
        outcomeColor={ex.outcomeColor}
        accent={accent}
      />
    )},
    // Scene 6: Key takeaways
    { render: () => <SummaryScene heading="Key Takeaways" takeaways={info.takeaways} accent={accent} closingLine={`Understanding ${greekName} gives you a measurable edge in every options trade.`} /> },
  ];

  return <SceneManager scenes={scenes} theme={S} />;
};
