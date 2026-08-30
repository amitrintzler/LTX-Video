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

// ─────────────────────────────────────────────────────────────────────────────
// 1. VerticalSpreadsLong
// ─────────────────────────────────────────────────────────────────────────────

export type VerticalSpreadsLongProps = { accent?: string };
export const VerticalSpreadsLong: React.FC<VerticalSpreadsLongProps> = ({
  accent = "#10b981",
}) => {
  useVideoConfig();
  const scenes: SceneDef[] = [
    {
      durationInFrames: sec(30),
      render: () => (
        <TitleScene
          label="Options Strategy"
          title="Vertical Spreads: Defined Risk Options"
          subtitle="How to cap your risk and still profit from directional moves"
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(20),
      render: () => (
        <BulletScene
          heading="Why Traders Choose Vertical Spreads"
          bullets={[
            "Defined maximum loss unlike naked options",
            "Lower cost than buying a single option outright",
            "Collect or pay a net credit or debit at entry",
            "Higher probability of profit for credit spreads",
            "Greeks are partially hedged by the opposing leg",
          ]}
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(55),
      render: () => (
        <PayoffDiagramScene
          heading="Bull Call Spread: AAPL 185 to 190"
          subheading="Buy 185 call at $3.50, sell 190 call at $2.00. Net debit $1.50 per share."
          legs={[
            { type: "long-call", strike: 185, premium: 3.5 },
            { type: "short-call", strike: 190, premium: 2.0 },
          ]}
          priceMin={170}
          priceMax={210}
          currentPrice={185}
          accent={accent}
          footnote="Maximum profit $350 per contract when AAPL closes above $190. Maximum loss $150 when below $185."
        />
      ),
    },
    {
      durationInFrames: sec(60),
      render: () => (
        <CalculationScene
          heading="Bull Call Spread Math: Every Number You Need"
          steps={[
            { label: "Long 185 call cost", formula: "Pay", result: "$3.50" },
            { label: "Short 190 call credit", formula: "Collect", result: "$2.00" },
            { label: "Net debit", formula: "$3.50 minus $2.00", result: "$1.50", highlight: true },
            { label: "Max loss", formula: "Net debit times 100", result: "$150" },
            { label: "Max profit", formula: "($190 minus $185 minus $1.50) times 100", result: "$350", highlight: true, color: "#22c55e" },
            { label: "Breakeven", formula: "$185 strike plus $1.50 net debit", result: "$186.50" },
            { label: "Probability max profit", formula: "Approximately (100 minus delta of short leg)", result: "~38%" },
          ]}
          conclusion="Risk $150 to make $350 means you only need to be right 30 percent of the time to break even long term."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(50),
      render: () => (
        <ComparisonTableScene
          heading="Bull Call Spread vs Alternatives"
          columns={["Strategy", "Max Loss", "Max Profit", "Breakeven", "Prob Profit"]}
          rows={[
            { cells: ["Long call (naked)", "$350", "Unlimited", "$188.50", "~48%"] },
            { cells: ["Bull call spread", "$150", "$350", "$186.50", "~62%"], highlight: true, winner: 1 },
            { cells: ["Short put", "$18,500", "$320", "$181.80", "~68%"] },
            { cells: ["Bull put spread", "$180", "$120", "$183.80", "~68%"] },
          ]}
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(65),
      render: () => (
        <WorkedExampleScene
          heading="SPY Bull Call Spread: Full Trade Lifecycle"
          subheading="SPY at $495, buying the $495 to $500 call spread for $2.20 debit, 21 days to expiry"
          company="S and P 500 ETF"
          ticker="SPY"
          trades={[
            { day: "Entry", event: "SPY at $495, 21 DTE, IV rank 35%", action: "Buy 495 call, sell 500 call. Pay $2.20 net debit.", pl: -220, cumPl: -220 },
            { day: "Day 7", event: "SPY rallies to $499. Spread worth $3.40.", action: "Up $120. Hold toward max profit zone.", pl: 120, cumPl: -100 },
            { day: "Day 14", event: "SPY at $502, above short strike $500", action: "Spread worth $4.20. Approaching max of $5.00.", pl: 200, cumPl: 100 },
            { day: "Day 18", event: "SPY pulls back to $499. 3 DTE.", action: "Close at $3.80 to lock profit before expiry gamma risk.", pl: -40, cumPl: 60 },
            { day: "Close", event: "Closed at $3.80. Total profit $1.60 per share.", action: "$160 profit on $220 risk. 72% return on risk.", pl: 160, cumPl: 160 },
          ]}
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(55),
      render: () => (
        <MistakeHighlightScene
          heading="The Vertical Spread Sizing Trap"
          mistake={{
            label: "Widening the spread to increase max profit",
            detail: "A trader sees that widening from a $5 spread to a $10 spread doubles max profit. So they buy the $185 to $195 bull call spread instead. The problem is that max loss also doubles and the probability of achieving max profit is much lower.",
          }}
          correction={{
            label: "Keep spreads to 5 point width unless you have a specific reason",
            detail: "Narrow spreads have a higher probability of reaching max profit. A $5 wide spread needs a $5 stock move. A $10 wide spread needs a $10 move for the same percentage return on risk. Narrow is usually better for retail traders.",
          }}
          insight="The best use of vertical spreads is replacing naked long options. A $185 call costs $350 and has unlimited profit. A $185 to $190 bull call spread costs $150 with $350 max profit. You keep 73% of the upside for 43% of the cost."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(40),
      render: () => (
        <StatsScene
          heading="Vertical Spread Performance Statistics"
          stats={[
            { label: "Win rate credit spreads", value: "~65%", color: "#22c55e" },
            { label: "Win rate debit spreads", value: "~45%", color: "#f59e0b" },
            { label: "Typical return on risk", value: "40 to 80%", color: accent },
            { label: "Best DTE", value: "30 to 45 days", color: "#6366f1" },
          ]}
          footnote="Statistics vary by market conditions and strike selection. These are general observations from SPX and SPY spreads."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(40),
      render: () => (
        <BulletScene
          heading="Vertical Spread Rules That Work"
          bullets={[
            "For bull call spreads enter when IV rank is below 50: you pay fair value for the debit",
            "For bull put spreads enter when IV rank is above 50: collect elevated premium",
            "Target 50 percent of max profit as your take profit on credit spreads",
            "Close before 7 DTE to avoid gamma risk compressing your profit zone",
            "Size positions so max loss is 1 to 2 percent of portfolio",
          ]}
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(30),
      render: () => (
        <SummaryScene
          heading="Vertical Spreads: Defined Risk With Real Upside"
          takeaways={[
            "Debit spreads cost less than naked options with capped but real upside",
            "Credit spreads collect premium with defined maximum loss",
            "Breakeven calculation: long strike plus or minus net debit or credit",
            "Close at 50 percent of max profit to avoid late stage gamma compression",
          ]}
          accent={accent}
          closingLine="Next: Iron condor range plays and collecting premium from both sides."
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

// ─────────────────────────────────────────────────────────────────────────────
// 2. IronCondorLong
// ─────────────────────────────────────────────────────────────────────────────

export type IronCondorLongProps = { accent?: string };
export const IronCondorLong: React.FC<IronCondorLongProps> = ({
  accent = "#f59e0b",
}) => {
  useVideoConfig();
  const scenes: SceneDef[] = [
    {
      durationInFrames: sec(30),
      render: () => (
        <TitleScene
          label="Options Strategy"
          title="The Iron Condor: Collecting Premium in a Range"
          subtitle="Four legs one trade and a defined profit zone built around probability"
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(20),
      render: () => (
        <BulletScene
          heading="Why the Iron Condor Is Popular"
          bullets={[
            "Sells time decay from two directions simultaneously",
            "Defined max profit AND max loss from entry",
            "Profits if stock stays in a range for 30 to 45 days",
            "High probability strategy when IV is elevated",
            "Can be managed and adjusted if stock tests one wing",
          ]}
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(65),
      render: () => (
        <PayoffDiagramScene
          heading="SPY Iron Condor: 490 to 510 Range"
          subheading="Sell 495 put, buy 490 put, sell 505 call, buy 510 call. Net credit $1.80."
          legs={[
            { type: "short-put", strike: 495, premium: 1.8 },
            { type: "long-put", strike: 490, premium: 0.8 },
            { type: "short-call", strike: 505, premium: 1.8 },
            { type: "long-call", strike: 510, premium: 0.8 },
          ]}
          priceMin={482}
          priceMax={518}
          currentPrice={500}
          accent={accent}
          footnote="Profit zone is $493.20 to $506.80. Max profit $180 per condor. Max loss $320 per condor."
        />
      ),
    },
    {
      durationInFrames: sec(65),
      render: () => (
        <CalculationScene
          heading="Iron Condor Math: All the Numbers"
          steps={[
            { label: "Short put premium", formula: "Sell 495 put", result: "+$1.80" },
            { label: "Long put premium", formula: "Buy 490 put", result: "−$0.80" },
            { label: "Short call premium", formula: "Sell 505 call", result: "+$1.80" },
            { label: "Long call premium", formula: "Buy 510 call", result: "−$0.80" },
            { label: "Net credit", formula: "Sum of all four legs", result: "+$1.80", highlight: true, color: "#22c55e" },
            { label: "Max profit", formula: "Net credit times 100", result: "$180" },
            { label: "Max loss per side", formula: "(Spread width minus credit) times 100", result: "$320" },
            { label: "Lower breakeven", formula: "Short put minus net credit", result: "$493.20" },
            { label: "Upper breakeven", formula: "Short call plus net credit", result: "$506.80" },
          ]}
          conclusion="Probability of max profit is approximately the probability SPY stays between $493.20 and $506.80 for 30 days."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(50),
      render: () => (
        <ComparisonTableScene
          heading="Iron Condor vs Related Strategies"
          columns={["Strategy", "Premium", "Max Loss", "Profit Condition", "IV Preference"]}
          rows={[
            { cells: ["Iron condor", "$180", "$320", "Range bound", "High IV"], highlight: true, winner: 1 },
            { cells: ["Short strangle", "Unlimited upside", "Unlimited", "Range bound", "High IV"] },
            { cells: ["Iron butterfly", "$350", "$150", "Pin to strike", "High IV"] },
            { cells: ["Covered call", "$150", "Stock cost", "Flat to up", "Any"] },
          ]}
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(70),
      render: () => (
        <WorkedExampleScene
          heading="SPY Iron Condor: Managing a Tested Wing"
          subheading="Entry at $500, short strikes at $495 and $505, net credit $1.80"
          company="S and P 500 ETF"
          ticker="SPY"
          trades={[
            { day: "Entry", event: "SPY at $500, sell condor for $1.80 net credit, 35 DTE", action: "Short puts at $495, short calls at $505. Max profit $180.", pl: 180, cumPl: 180 },
            { day: "Day 10", event: "SPY flat at $501. Theta collecting. Down $0.60 in credit.", action: "Position worth $1.20 to buy back. Theta working.", pl: 60, cumPl: 240 },
            { day: "Day 18", event: "SPY drops to $496, testing the $495 short put wing", action: "Condor now worth $2.60. Loss of $0.80 versus entry.", pl: -80, cumPl: 160 },
            { day: "Day 20", event: "Roll the tested put side down and out: sell new $490 put", action: "Collect $0.40 additional credit. New lower breakeven $489.60.", pl: 40, cumPl: 200 },
            { day: "Day 30", event: "SPY recovers to $499 at expiry of original options", action: "Both spreads expire worthless. Keep full adjusted credit $2.20.", pl: 220, cumPl: 420 },
          ]}
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(55),
      render: () => (
        <MistakeHighlightScene
          heading="The Wing Management Mistake"
          mistake={{
            label: "Holding an iron condor when one short strike is breached",
            detail: "A trader has a SPY $495 to $505 condor. SPY drops to $492, well through the $495 short put. The full $320 max loss is imminent. They freeze and hold, hoping for a recovery. SPY continues to $488 and the condor expires at max loss.",
          }}
          correction={{
            label: "Have a predetermined adjustment trigger at 50 percent of max loss",
            detail: "When the condor loses 50 percent of max profit ($90 in this case, or current loss of $90), either close the tested spread for a controlled loss or roll it to a lower strike and later expiry to collect more credit and buy time for recovery.",
          }}
          insight="Professional condor traders do not win every trade. They win by keeping losses controlled at 1 to 1.5 times max profit and taking winners at 50 percent of max profit. That math works over many trades."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(40),
      render: () => (
        <StatsScene
          heading="Iron Condor Historical Performance"
          stats={[
            { label: "Win rate at target", value: "~68%", color: "#22c55e" },
            { label: "Average hold time", value: "18 to 22 days", color: accent },
            { label: "Ideal IV rank entry", value: "Above 50%", color: "#6366f1" },
            { label: "Target credit", value: "30 to 40% of width", color: "#a855f7" },
          ]}
          footnote="These numbers are based on SPX and SPY options over extended backtests. Individual results vary."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(35),
      render: () => (
        <BulletScene
          heading="Iron Condor Checklist Before Every Entry"
          bullets={[
            "IV rank above 50% to ensure you are selling elevated premium",
            "Short strikes at 16 to 20 delta each side (approximately 1 standard deviation)",
            "Width of each spread at least 5 points for meaningful credit",
            "Days to expiry 30 to 45 for optimal theta to gamma ratio",
            "Defined profit target: close at 50 percent of max credit collected",
          ]}
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(30),
      render: () => (
        <SummaryScene
          heading="Iron Condor: Range Bound Premium Collection"
          takeaways={[
            "Four legs create a defined profit zone between both short strikes",
            "Net credit received is your maximum profit per contract",
            "Adjust early when tested: do not wait for max loss",
            "High IV rank at entry maximizes the credit you collect",
          ]}
          accent={accent}
          closingLine="Next: Butterfly spreads for precision target trades."
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

// ─────────────────────────────────────────────────────────────────────────────
// 3. ButterflySpreadsLong
// ─────────────────────────────────────────────────────────────────────────────

export type ButterflySpreadsLongProps = { accent?: string };
export const ButterflySpreadsLong: React.FC<ButterflySpreadsLongProps> = ({
  accent = "#a855f7",
}) => {
  useVideoConfig();
  const scenes: SceneDef[] = [
    {
      durationInFrames: sec(30),
      render: () => (
        <TitleScene
          label="Options Strategy"
          title="Butterfly Spreads: Precision Target Trades"
          subtitle="Maximum profit when stock pins exactly where you predict"
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(20),
      render: () => (
        <BulletScene
          heading="What Makes a Butterfly"
          bullets={[
            "Buy one lower strike option",
            "Sell two middle strike options (the body)",
            "Buy one higher strike option (the wing)",
            "Net debit is your maximum loss",
            "Maximum profit occurs exactly at the middle strike at expiry",
          ]}
          accent={accent}
          icon="🦋"
        />
      ),
    },
    {
      durationInFrames: sec(60),
      render: () => (
        <PayoffDiagramScene
          heading="QQQ Butterfly: $380 to $385 to $390 Call"
          subheading="Buy $380 call, sell two $385 calls, buy $390 call. Net debit approximately $1.20."
          legs={[
            { type: "long-call", strike: 380, premium: 7.0 },
            { type: "short-call", strike: 385, premium: 4.0 },
            { type: "short-call", strike: 385, premium: 4.0 },
            { type: "long-call", strike: 390, premium: 2.2 },
          ]}
          priceMin={370}
          priceMax={400}
          currentPrice={385}
          accent={accent}
          footnote="Peak profit $380 when QQQ expires exactly at $385. The shape is an inverted V at the short strike."
        />
      ),
    },
    {
      durationInFrames: sec(60),
      render: () => (
        <CalculationScene
          heading="Butterfly Math: Everything in One Place"
          steps={[
            { label: "Buy 380 call", formula: "Cost", result: "$7.00" },
            { label: "Sell 2 x 385 calls", formula: "Credit received", result: "$8.00" },
            { label: "Buy 390 call", formula: "Cost", result: "$2.20" },
            { label: "Net debit", formula: "$7.00 plus $2.20 minus $8.00", result: "$1.20", highlight: true },
            { label: "Max profit", formula: "(Spread width minus debit) times 100", result: "$380" },
            { label: "Max loss", formula: "Net debit times 100", result: "$120" },
            { label: "Lower breakeven", formula: "$380 strike plus $1.20", result: "$381.20" },
            { label: "Upper breakeven", formula: "$390 strike minus $1.20", result: "$388.80" },
          ]}
          conclusion="Risk $120 to make $380 when QQQ pins within $3.80 of the middle strike at expiry."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(50),
      render: () => (
        <ComparisonTableScene
          heading="Butterfly vs Condor vs Straddle"
          columns={["Strategy", "Max Profit", "Max Loss", "Profit Condition", "Target Use"]}
          rows={[
            { cells: ["Butterfly", "$380", "$120", "Stock pins at strike", "Precise target"] },
            { cells: ["Iron condor", "$180", "$320", "Wide range", "Range uncertainty"], winner: 2 },
            { cells: ["Long straddle", "Unlimited", "$2,300", "Big move", "Earnings play"] },
            { cells: ["Short straddle", "$2,300", "Unlimited", "Stock flat", "High IV income"] },
          ]}
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(65),
      render: () => (
        <WorkedExampleScene
          heading="QQQ Butterfly Before FOMC: Pinning at Support"
          subheading="Entering a butterfly with QQQ at $385, expecting the Fed to be neutral and QQQ to pin near current level"
          company="Nasdaq 100 ETF"
          ticker="QQQ"
          trades={[
            { day: "Entry", event: "QQQ at $384.50, FOMC in 3 days, expect neutral statement", action: "Buy QQQ $380 to $385 to $390 butterfly for $1.20 debit", pl: -120, cumPl: -120 },
            { day: "FOMC day", event: "Fed holds rates, neutral statement as expected", action: "QQQ moves to $385.20 at close. Perfect pin.", pl: 250, cumPl: 130 },
            { day: "Day after", event: "QQQ at $386.00. Still inside profit zone.", action: "Butterfly worth $2.80. Up $1.60 per share.", pl: 160, cumPl: 290 },
            { day: "2 days later", event: "QQQ rallies to $389.00. Approaching upper breakeven.", action: "Close butterfly at $2.00. Lock in profit before it collapses.", pl: -80, cumPl: 210 },
            { day: "Exit", event: "Closed at $2.00. Net profit $0.80 per share.", action: "$80 profit on $120 risk at 67% return on risk.", pl: 80, cumPl: 210 },
          ]}
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(55),
      render: () => (
        <MistakeHighlightScene
          heading="The Butterfly Precision Trap"
          mistake={{
            label: "Using a butterfly when you are uncertain about direction",
            detail: "Butterflies require a precise price target. A trader buys a $385 butterfly on QQQ but is actually unsure if QQQ will be at $385, $390, or $395 at expiry. The butterfly expires at a small profit at $388 but would have been worthless at $390.",
          }}
          correction={{
            label: "Only trade butterflies when you have a specific price target",
            detail: "Butterflies are for pinning plays: FOMC where you expect a neutral reaction and stocks to hold a level, or expiration day where you expect a max pain magnet. If you are genuinely uncertain about price, use an iron condor with a wider range instead.",
          }}
          insight="The butterfly is the only options strategy that gets worse the more the stock moves. The asymmetry works in your favor only when your target price prediction is accurate."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(40),
      render: () => (
        <StatsScene
          heading="Butterfly Trade Statistics"
          stats={[
            { label: "Typical debit paid", value: "20 to 25% of width", color: accent },
            { label: "Max profit to max loss", value: "3 to 5:1", color: "#22c55e" },
            { label: "Probability of max profit", value: "~5 to 15%", color: "#ef4444" },
            { label: "Probability of any profit", value: "~35 to 45%", color: "#f59e0b" },
          ]}
          footnote="Probability of max profit is low because exact pinning is rare. Most butterfly profits come from partial fills between the breakevens."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(35),
      render: () => (
        <BulletScene
          heading="When to Use a Butterfly"
          bullets={[
            "You have a specific price target and high conviction",
            "Days to expiry of 7 to 21 for sharp pinning effect",
            "Stock has a technical magnet like a gap fill or 52 week level",
            "Before FOMC when you expect a neutral market reaction",
            "Size small: butterflies can expire worthless if the stock moves away",
          ]}
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(30),
      render: () => (
        <SummaryScene
          heading="Butterfly: High Reward When Precision Pays Off"
          takeaways={[
            "Maximum profit only at the middle strike: you need to be right about the exact price",
            "Risk is always limited to the small net debit paid",
            "Use when you expect stock to pin at a specific technical level",
            "Better risk reward than buying a naked option when you are highly confident in a target",
          ]}
          accent={accent}
          closingLine="Next: Calendar spreads and how to profit from the difference in theta between two expirations."
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

// ─────────────────────────────────────────────────────────────────────────────
// 4. CalendarDiagonalLong
// ─────────────────────────────────────────────────────────────────────────────

export type CalendarDiagonalLongProps = { accent?: string };
export const CalendarDiagonalLong: React.FC<CalendarDiagonalLongProps> = ({
  accent = "#14b8a6",
}) => {
  useVideoConfig();
  const scenes: SceneDef[] = [
    {
      durationInFrames: sec(30),
      render: () => (
        <TitleScene
          label="Options Strategy"
          title="Calendar Spreads: Selling Time Against Time"
          subtitle="Profit from the difference in theta and vega between two expiration dates"
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(20),
      render: () => (
        <BulletScene
          heading="The Two Types of Calendar Spreads"
          bullets={[
            "Calendar spread: same strike, different expiration dates",
            "Diagonal spread: different strikes AND different expirations",
            "Both exploit the faster theta decay of near dated options",
            "Net vega is positive: you benefit when IV rises",
            "Best entered when near term IV is elevated relative to far term IV",
          ]}
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(55),
      render: () => (
        <CalculationScene
          heading="QQQ Calendar Spread Math"
          steps={[
            { label: "Sell 30 DTE QQQ 380 call", formula: "Near month credit", result: "+$4.80" },
            { label: "Buy 60 DTE QQQ 380 call", formula: "Far month debit", result: "−$7.20" },
            { label: "Net debit", formula: "$7.20 minus $4.80", result: "$2.40" },
            { label: "Near month daily theta", formula: "Short leg earns per day", result: "+$0.16" },
            { label: "Far month daily theta", formula: "Long leg costs per day", result: "−$0.10" },
            { label: "Net daily theta", formula: "Earn minus pay", result: "+$0.06", highlight: true, color: "#22c55e" },
            { label: "30 day theta gain", formula: "30 times $0.06", result: "+$1.80" },
          ]}
          conclusion="If QQQ stays near $380 for 30 days the near month expires and you earn $4.80 while the back month retains much of its value. Net result: profit on the debit paid."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(60),
      render: () => (
        <ComparisonTableScene
          heading="Calendar vs Diagonal vs Covered Call"
          columns={["Strategy", "Direction", "Vega", "Theta Net", "Best Market"]}
          rows={[
            { cells: ["Calendar", "Neutral", "Positive", "Positive", "Flat with low movement"], highlight: true, winner: 2 },
            { cells: ["Diagonal", "Slight bullish", "Positive", "Positive", "Slow drift up or flat"] },
            { cells: ["Covered call", "Slight bullish", "Negative", "Positive", "Flat to slightly up"] },
            { cells: ["Naked short call", "Bearish to neutral", "Negative", "Positive", "Falling or flat"] },
          ]}
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(60),
      render: () => (
        <SvgLineChartScene
          heading="Calendar Spread Profit and Loss at Front Month Expiry"
          subheading="QQQ 380 calendar spread profit at different QQQ prices when near month expires"
          data={[
            { label: "370", value: -1.4 },
            { label: "373", value: -0.8 },
            { label: "376", value: 0.1 },
            { label: "379", value: 1.6 },
            { label: "380", value: 2.2 },
            { label: "381", value: 1.6 },
            { label: "384", value: 0.1 },
            { label: "387", value: -0.8 },
            { label: "390", value: -1.4 },
          ]}
          yLabel="Profit ($)"
          xLabel="QQQ Price at Front Expiry ($)"
          highlightIdx={4}
          footnote="The bell curve peaks at the calendar strike. The spread is profitable in a 10 to 12 point range around the strike."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(65),
      render: () => (
        <WorkedExampleScene
          heading="QQQ Calendar Trade Through Front Month Expiry"
          subheading="Entering with QQQ at $380, targeting theta income over 30 days"
          company="Nasdaq 100 ETF"
          ticker="QQQ"
          trades={[
            { day: "Entry", event: "QQQ at $380, IV rank 35%. Buy calendar spread for $2.40 debit.", action: "Sell 30 DTE 380 call, buy 60 DTE 380 call.", pl: -240, cumPl: -240 },
            { day: "Day 10", event: "QQQ flat at $381. Theta earned $0.60.", action: "Calendar now worth $2.80. Up $0.40.", pl: 40, cumPl: -200 },
            { day: "Day 20", event: "IV spikes 3 points. Calendar benefits from vega.", action: "Back month gains more than front month from IV rise. Worth $3.20.", pl: 40, cumPl: -160 },
            { day: "Day 28", event: "QQQ at $380 with 2 days to front month expiry.", action: "Front month losing last time value rapidly. Calendar worth $3.60.", pl: 40, cumPl: -120 },
            { day: "Expiry", event: "Front month expires. Net P and L calculated.", action: "Sold front month for $4.80 original credit. Back month now worth $5.40. Total: $5.40 minus $7.20 plus $4.80 = $3.00 value. Profit: $0.60.", pl: 60, cumPl: -60 },
          ]}
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(55),
      render: () => (
        <MistakeHighlightScene
          heading="The IV Environment Mistake for Calendars"
          mistake={{
            label: "Entering a calendar when near term IV is lower than far term IV",
            detail: "When near month IV is below far month IV the trade works against you: you are selling cheap options and buying expensive ones. This is called selling into backwardation. The trade has negative expected value from the start.",
          }}
          correction={{
            label: "Enter calendars when near term IV is higher than far term IV (contango)",
            detail: "Check your broker options chain: if the front month straddle costs more than the back month straddle at the same strike as a percentage, IV is in contango. This is the ideal calendar entry environment. Normal market structure is contango.",
          }}
          insight="The VIX term structure measures this: when VIX3M is above VIX the near term is cheap relative to medium term. When VIX exceeds VIX3M, near term is elevated and calendars thrive."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(40),
      render: () => (
        <StatsScene
          heading="Calendar Spread Facts"
          stats={[
            { label: "Net theta per day", value: "+$4 to $8", color: "#22c55e" },
            { label: "Net vega", value: "Positive", color: accent },
            { label: "Best IV rank entry", value: "20 to 50%", color: "#6366f1" },
            { label: "Profit range", value: "10 to 15 points", color: "#f59e0b" },
          ]}
          footnote="These are approximate values for a $380 QQQ calendar spread. Values scale with the option premium and the spread width."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(35),
      render: () => (
        <BulletScene
          heading="Calendar Spread Rules"
          bullets={[
            "Enter when IV rank is 20 to 50%: normal range with slight elevation is ideal",
            "Place the strike at or slightly below current price for slightly bullish bias",
            "Roll the short leg monthly to keep collecting near term theta",
            "Close the whole spread if QQQ moves more than 5 percent from the strike",
            "Avoid calendars in very low IV: near term is too cheap to sell profitably",
          ]}
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(30),
      render: () => (
        <SummaryScene
          heading="Calendar Spreads: Theta and Vega Working Together"
          takeaways={[
            "Sell near dated options and buy far dated to collect the theta differential",
            "Net positive vega means IV spikes help the position not hurt it",
            "Profit zone spans 10 to 15 points around the calendar strike",
            "Roll the short front month leg repeatedly to compound theta income",
          ]}
          accent={accent}
          closingLine="Next: Straddles and strangles for trading volatility itself."
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

// ─────────────────────────────────────────────────────────────────────────────
// 5. StraddleStrangleLong
// ─────────────────────────────────────────────────────────────────────────────

export type StraddleStrangleLongProps = { accent?: string };
export const StraddleStrangleLong: React.FC<StraddleStrangleLongProps> = ({
  accent = "#ef4444",
}) => {
  useVideoConfig();
  const scenes: SceneDef[] = [
    {
      durationInFrames: sec(30),
      render: () => (
        <TitleScene
          label="Options Strategy"
          title="Straddles and Strangles: Trading Volatility"
          subtitle="How to profit from large moves regardless of which direction the stock goes"
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(20),
      render: () => (
        <BulletScene
          heading="Straddle vs Strangle: The Key Difference"
          bullets={[
            "Straddle: buy both the ATM call AND the ATM put at the same strike",
            "Strangle: buy OTM call AND OTM put at different strikes (cheaper but needs bigger move)",
            "Both profit from large moves OR from IV expansion before the move",
            "Straddles cost more and need a smaller move to profit",
            "Strangles cost less but need a larger stock move to break even",
          ]}
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(55),
      render: () => (
        <PayoffDiagramScene
          heading="TSLA Long Straddle: Buy Both at $240"
          subheading="Buy $240 call for $12, buy $240 put for $11. Total cost $23. Need $23 move to break even."
          legs={[
            { type: "long-call", strike: 240, premium: 12 },
            { type: "long-put", strike: 240, premium: 11 },
          ]}
          priceMin={200}
          priceMax={280}
          currentPrice={240}
          accent={accent}
          footnote="Lower breakeven $217. Upper breakeven $263. Outside that range: profit. Maximum loss is the $23 debit if TSLA pins at exactly $240 at expiry."
        />
      ),
    },
    {
      durationInFrames: sec(55),
      render: () => (
        <PayoffDiagramScene
          heading="TSLA Long Strangle: $230 Put plus $250 Call"
          subheading="Buy $250 call for $7, buy $230 put for $8. Total cost $15. Need $25 move to break even."
          legs={[
            { type: "long-call", strike: 250, premium: 7 },
            { type: "long-put", strike: 230, premium: 8 },
          ]}
          priceMin={200}
          priceMax={280}
          currentPrice={240}
          accent={accent}
          footnote="Strangle costs $15 vs $23 for straddle. But needs TSLA below $215 or above $265 to profit. 8 extra points required."
        />
      ),
    },
    {
      durationInFrames: sec(55),
      render: () => (
        <CalculationScene
          heading="Straddle vs Strangle: Head to Head"
          steps={[
            { label: "Straddle cost", formula: "$12 call plus $11 put", result: "$23" },
            { label: "Straddle upper BE", formula: "$240 plus $23", result: "$263" },
            { label: "Straddle lower BE", formula: "$240 minus $23", result: "$217" },
            { label: "Strangle cost", formula: "$7 call plus $8 put", result: "$15" },
            { label: "Strangle upper BE", formula: "$250 plus $15", result: "$265" },
            { label: "Strangle lower BE", formula: "$230 minus $15", result: "$215" },
            { label: "Straddle advantage", formula: "Needs 8 fewer points to profit", result: "Better precision", highlight: true },
          ]}
          conclusion="Straddle wins when the move is between 23 and 25 points. Strangle wins when the move exceeds 25 points because of its lower cost."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(50),
      render: () => (
        <ComparisonTableScene
          heading="Long vs Short Straddle and Strangle"
          columns={["Position", "Profit When", "Max Loss", "IV Preference", "Typical Use"]}
          rows={[
            { cells: ["Long straddle", "Big move either way", "$2,300", "Rising IV", "Pre earnings"], winner: 2 },
            { cells: ["Short straddle", "Stock stays flat", "Unlimited", "Falling IV", "Selling premium"] },
            { cells: ["Long strangle", "Very big move", "$1,500", "Rising IV", "Cheap earnings play"], highlight: true, winner: 2 },
            { cells: ["Short strangle", "Stays in range", "Unlimited", "Falling IV", "Income strategy"] },
          ]}
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(65),
      render: () => (
        <WorkedExampleScene
          heading="TSLA Pre Earnings Straddle: The IV Timing Play"
          subheading="Buy straddle 2 weeks before earnings, sell the day before. Capture IV rise, avoid crush."
          company="Tesla"
          ticker="TSLA"
          trades={[
            { day: "2 weeks before", event: "TSLA at $240, earnings in 14 days, IV at 55% (rank 60th)", action: "Buy ATM straddle for $23.00 total cost", pl: -2300, cumPl: -2300 },
            { day: "1 week before", event: "IV rises to 65% as earnings approach. TSLA flat.", action: "Straddle now worth $28.00 on vega alone. Up $5.", pl: 500, cumPl: -1800 },
            { day: "Day before", event: "IV at 80%, TSLA drops $4 to $236.", action: "Straddle worth $34.00 (vega $8 plus delta $4 from put).", pl: 600, cumPl: -1200 },
            { day: "Sell before earnings", event: "Exit at $34.00. Avoid IV crush risk.", action: "$11 profit per share. Return 48% on risk in 13 days.", pl: 1100, cumPl: -100 },
            { day: "Earnings day", event: "TSLA beats and rallies $18 to $254. IV crushes to 42%.", action: "Straddle worth $25.00 after crush. Selling before was correct call.", pl: -900, cumPl: -1000 },
          ]}
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(55),
      render: () => (
        <MistakeHighlightScene
          heading="The Earnings Straddle Timing Mistake"
          mistake={{
            label: "Buying a straddle the day before earnings",
            detail: "A trader sees TSLA earnings tomorrow and buys an ATM straddle for $34.00 when IV is at peak 80%. Even though TSLA moves $18 on earnings (a large move), the IV crushes 38 points instantly the next morning. The straddle is worth $25.00 despite the big move. The trader loses $9 per share.",
          }}
          correction={{
            label: "Buy straddles 2 weeks before earnings when IV is still at 50 to 60% rank",
            detail: "The goal is to ride the IV expansion from 60% to 80% rank before earnings. Sell the day before earnings to capture that IV increase. Do not hold through the IV crush. The straddle you buy cheap gets expensive from IV alone without needing the stock to move.",
          }}
          insight="IV expansion trades are not directional bets. They are bets that the market will price in more uncertainty as the event approaches. That usually happens reliably. The crush after the event always happens. Never hold through it."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(35),
      render: () => (
        <StatsScene
          heading="Straddle and Strangle Statistics"
          stats={[
            { label: "Avg TSLA earnings move", value: "8 to 14%", color: accent },
            { label: "IV crush post earnings", value: "30 to 50%", color: "#ef4444" },
            { label: "Straddle win rate", value: "~40%", color: "#f59e0b" },
            { label: "Pre earnings IV play win", value: "~65%", color: "#22c55e" },
          ]}
          footnote="Win rate for straddle held through earnings is below 50% because IV crush often exceeds the directional gain. Pre earnings IV trade win rate is higher."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(30),
      render: () => (
        <BulletScene
          heading="Straddle and Strangle Rules"
          bullets={[
            "Buy when IV rank is below 40: you are entering before the expensive phase",
            "Sell the day before earnings or events to avoid the IV crush",
            "Straddle for moves you expect to be 8 to 12 percent",
            "Strangle for moves you expect to be 12 to 20 percent (lower cost, needs bigger move)",
          ]}
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(30),
      render: () => (
        <SummaryScene
          heading="Straddles and Strangles: Betting on Movement Not Direction"
          takeaways={[
            "Both profit from large moves or IV expansion regardless of direction",
            "Buy low IV (below 40th rank), sell before peak IV events",
            "Straddle is lower cost way to profit from moves over 8 to 12 percent",
            "Never hold through earnings IV crush: the income from selling beats holding every time",
          ]}
          accent={accent}
          closingLine="Next: Borrow costs and the mechanics of short selling."
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

// ─────────────────────────────────────────────────────────────────────────────
// 6. BorrowLocateLong
// ─────────────────────────────────────────────────────────────────────────────

export type BorrowLocateLongProps = { accent?: string };
export const BorrowLocateLong: React.FC<BorrowLocateLongProps> = ({
  accent = "#3b82f6",
}) => {
  useVideoConfig();
  const scenes: SceneDef[] = [
    {
      durationInFrames: sec(30),
      render: () => (
        <TitleScene
          label="Short Selling"
          title="Borrow and Locate: The Hidden Cost of Short Selling"
          subtitle="What brokers charge you to borrow shares and how it affects your P and L"
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(20),
      render: () => (
        <BulletScene
          heading="How Short Selling Actually Works"
          bullets={[
            "Borrow shares from another investor through your broker",
            "Sell those shares immediately at current market price",
            "Wait for price to fall, then buy back at lower price",
            "Return shares to lender and keep the difference",
            "Pay a daily borrow fee for the entire duration you hold the short",
          ]}
          accent={accent}
          icon="🔄"
        />
      ),
    },
    {
      durationInFrames: sec(60),
      render: () => (
        <ComparisonTableScene
          heading="Borrow Rates: Easy vs Hard to Borrow"
          subheading="Annual borrow rate estimates. Rates change daily based on supply and demand."
          columns={["Stock", "Annual Borrow Rate", "Why", "Cost on $10,000 Short"]}
          rows={[
            { cells: ["AAPL", "0.30%", "Large float, easy to borrow", "$30 per year"] },
            { cells: ["SPY", "0.10%", "ETF, always available", "$10 per year"] },
            { cells: ["NVDA (sometimes)", "2 to 5%", "High demand, squeezed", "$200 to $500"] },
            { cells: ["GME at peak (2021)", "50 to 100%", "Extremely HTB", "$5,000 to $10,000"], highlight: true },
            { cells: ["AMC (2021)", "25 to 40%", "High short interest", "$2,500 to $4,000"] },
          ]}
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(65),
      render: () => (
        <CalculationScene
          heading="Borrow Cost Reality: GME in January 2021"
          steps={[
            { label: "Short 100 shares of GME", formula: "At $20 per share", result: "$2,000 position" },
            { label: "Annual borrow rate", formula: "Hard to borrow rate", result: "50%" },
            { label: "Daily borrow cost", formula: "$2,000 times 0.50 divided by 365", result: "$2.74 per day" },
            { label: "Weekly borrow cost", formula: "$2.74 times 7", result: "$19.18 per week" },
            { label: "Stock must fall to cover borrow", formula: "$2.74 per day breakeven decline", result: "$0.0274 per day" },
            { label: "If held for 30 days", formula: "$2.74 times 30", result: "$82.20 borrow cost", highlight: true, color: "#ef4444" },
            { label: "Plus if GME rose $20", formula: "$20 times 100 shares", result: "$2,000 additional loss" },
          ]}
          conclusion="GME shorts paid $82 in borrow fees over 30 days AND lost thousands when the squeeze hit. The borrow cost was the least of their problems."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(55),
      render: () => (
        <SetupScene
          heading="Factors That Determine Borrow Rate"
          items={[
            { label: "Short interest ratio", value: "High SI = high borrow" },
            { label: "Float size", value: "Small float = harder to borrow" },
            { label: "Broker inventory", value: "Each broker varies" },
            { label: "Market demand", value: "More shorts = higher rate" },
            { label: "Locate availability", value: "HTB requires daily locate" },
          ]}
          description="Hard to borrow stocks require your broker to locate shares before you can short. If no shares are available, you cannot short even if you want to. This is the locate requirement."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(65),
      render: () => (
        <WorkedExampleScene
          heading="AMC Short Gone Wrong: Borrow Cost Ruins the Trade"
          subheading="Shorting AMC at $15 in early 2021 expecting it to fall back to $5"
          company="AMC Entertainment"
          ticker="AMC"
          trades={[
            { day: "Day 1", event: "Short 1000 AMC shares at $15. Borrow rate 30% annualized.", action: "Daily borrow cost: $1,500 times 0.30 / 365 = $1.23 per day", pl: -1230, cumPl: -1230 },
            { day: "Day 14", event: "AMC moves sideways between $12 and $16. Flat trade.", action: "Borrow has cost $17.22 so far. Position down $0 on stock.", pl: -172, cumPl: -1402 },
            { day: "Day 21", event: "AMC spikes to $25 on retail momentum. Short now losing.", action: "Stock loss: $10 times 1000 = $10,000. Borrow: $25.20.", pl: -10025, cumPl: -11427 },
            { day: "Day 28", event: "Margin call received. Must add capital or cover.", action: "Forced to cover at $23. Total loss including borrow: $8,025.", pl: -8025, cumPl: -19452 },
            { day: "Lesson", event: "The borrow rate made the trade worse on every losing day", action: "Never short high borrow stocks without factoring daily cost into your maximum loss.", pl: 0, cumPl: -19452 },
          ]}
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(55),
      render: () => (
        <MistakeHighlightScene
          heading="The Locate Trap: Assuming You Can Always Short"
          mistake={{
            label: "Not checking borrow availability before deciding to short",
            detail: "A trader analyzes a stock and decides to short it. They wait for the right entry and then try to enter the trade. Their broker says the stock is not available to borrow. They miss the trade entirely, or worse, they short a stock that costs 30 percent per year in borrow fees without knowing it.",
          }}
          correction={{
            label: "Check borrow cost and availability in your broker before analysis",
            detail: "Most brokers show a borrow indicator (Easy to Borrow, Hard to Borrow, Not Available) on the options or stock trading page. Check this first. If borrow rate is above 10 percent annually, recalculate your breakeven price factoring in the daily cost.",
          }}
          insight="Borrow rates can change overnight. A stock that is easy to borrow at 0.5% on Monday can become hard to borrow at 20% by Wednesday if short interest surges. Your existing short position automatically pays the new higher rate."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(40),
      render: () => (
        <StatsScene
          heading="Short Selling Quick Reference"
          stats={[
            { label: "Easy to borrow threshold", value: "Below 1% APR", color: "#22c55e" },
            { label: "Hard to borrow warning", value: "Above 10% APR", color: accent },
            { label: "Extreme HTB", value: "Above 30% APR", color: "#ef4444" },
            { label: "Typical ETF borrow", value: "0.10 to 0.30%", color: "#6366f1" },
          ]}
          footnote="Borrow rates are quoted annually but charged daily: rate / 365 times position value."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(35),
      render: () => (
        <BulletScene
          heading="Short Selling Borrow Rules"
          bullets={[
            "Always check borrow rate before entering a short: ask your broker or check the platform",
            "Borrow cost above 5% per year requires an additional 5% stock decline just to break even",
            "HTB stocks are typically the highest short squeeze risk: two dangers in one position",
            "Use puts instead of shorting stock for defined risk without borrow cost",
            "Borrow rates are not fixed: hedge funds can and do squeeze shorts by restricting supply",
          ]}
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(30),
      render: () => (
        <SummaryScene
          heading="Borrow Cost: The Short Seller Tax You Cannot Avoid"
          takeaways={[
            "Borrow fees are charged daily and reduce your profit or increase your loss every single day",
            "Hard to borrow stocks (over 10% APR) require much larger price declines to be profitable",
            "Borrow availability can disappear overnight leaving you with a position you cannot exit",
            "Use put options instead of shorting stock to get short exposure without borrow cost",
          ]}
          accent={accent}
          closingLine="Next: Short risk and what happens when a short squeeze hits your position."
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

// ─────────────────────────────────────────────────────────────────────────────
// 7. ShortRiskLong
// ─────────────────────────────────────────────────────────────────────────────

export type ShortRiskLongProps = { accent?: string };
export const ShortRiskLong: React.FC<ShortRiskLongProps> = ({
  accent = "#ef4444",
}) => {
  useVideoConfig();
  const scenes: SceneDef[] = [
    {
      durationInFrames: sec(30),
      render: () => (
        <TitleScene
          label="Short Selling"
          title="Short Risk: What Can Go Wrong"
          subtitle="Unlimited loss potential margin calls and the anatomy of a short squeeze"
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(20),
      render: () => (
        <BulletScene
          heading="Why Short Selling Is Uniquely Risky"
          bullets={[
            "Maximum gain is 100% if stock goes to zero",
            "Maximum loss is unlimited because stock can rise infinitely",
            "Margin calls force you to buy back at the worst possible moment",
            "Dividends declared by the company must be paid to the lender",
            "Short interest reporting creates a public visibility target for squeezes",
          ]}
          accent={accent}
          icon="⚠️"
        />
      ),
    },
    {
      durationInFrames: sec(60),
      render: () => (
        <CalculationScene
          heading="Unlimited Loss: Running the Math"
          steps={[
            { label: "Short 100 AAPL shares at $185", formula: "Short position value", result: "$18,500" },
            { label: "AAPL rallies to $200", formula: "Loss = $15 times 100", result: "−$1,500" },
            { label: "AAPL rallies to $250", formula: "Loss = $65 times 100", result: "−$6,500", highlight: true, color: "#ef4444" },
            { label: "AAPL rallies to $400", formula: "Loss = $215 times 100", result: "−$21,500", color: "#ef4444" },
            { label: "AAPL rallies to $1,000", formula: "Loss = $815 times 100", result: "−$81,500", color: "#ef4444" },
            { label: "Long stock max loss", formula: "If you own 100 shares at $185", result: "−$18,500" },
          ]}
          conclusion="A long stock position has limited loss (to zero). A short position has unlimited loss. This asymmetry makes risk management critical for short sellers."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(60),
      render: () => (
        <ComparisonTableScene
          heading="Long Stock vs Short Stock vs Long Put"
          columns={["Position", "Max Gain", "Max Loss", "Margin Required", "Squeeze Risk"]}
          rows={[
            { cells: ["Long stock", "Unlimited", "Investment ($18,500)", "50% margin", "None"] },
            { cells: ["Short stock", "100% ($18,500)", "Unlimited", "150% initial", "High"], highlight: true },
            { cells: ["Long put", "Strike times 100", "Premium ($350)", "Full premium", "None"], winner: 1 },
          ]}
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(65),
      render: () => (
        <SvgLineChartScene
          heading="GME Short Squeeze: Price From $20 to $483 in 14 Days"
          subheading="January 2021. Massive short interest met coordinated retail buying."
          data={[
            { label: "Jan 4", value: 17.25 },
            { label: "Jan 8", value: 20.0 },
            { label: "Jan 13", value: 31.4 },
            { label: "Jan 19", value: 39.36 },
            { label: "Jan 22", value: 65.01 },
            { label: "Jan 25", value: 76.79 },
            { label: "Jan 26", value: 147.98 },
            { label: "Jan 27", value: 354.83 },
            { label: "Jan 28", value: 483.0 },
            { label: "Feb 1", value: 225.0 },
            { label: "Feb 5", value: 63.77 },
          ]}
          yLabel="GME Price ($)"
          xLabel="Date"
          highlightIdx={8}
          footnote="Short sellers who did not cover by Jan 22 lost 10 to 15 times their initial risk. Margin calls accelerated the squeeze as shorts were forced to buy."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(70),
      render: () => (
        <WorkedExampleScene
          heading="GME Short Squeeze: Anatomy of a Wipeout"
          subheading="Following a short seller who entered at $20 and held too long"
          company="GameStop"
          ticker="GME"
          trades={[
            { day: "Jan 4", event: "Short 500 GME shares at $20. Short interest already 140% of float.", action: "Position: short $10,000. Borrow rate 50% annualized.", pl: -1370, cumPl: -1370 },
            { day: "Jan 13", event: "GME at $31.40. Reddit discussion intensifying. Cover stop not placed.", action: "Loss $5,700. Thesis still intact (company declining). Hold.", pl: -5700, cumPl: -7070 },
            { day: "Jan 22", event: "GME at $65. Margin call received.", action: "Broker demands $15,000 additional margin. Forced to partially cover 200 shares at $65.", pl: -9000, cumPl: -16070 },
            { day: "Jan 27", event: "GME at $354. Remaining 300 shares.", action: "Emergency cover at $354. Loss on remaining: $100,200.", pl: -100200, cumPl: -116270 },
            { day: "Total", event: "Total loss on GME short", action: "$116,270 loss on original $10,000 position. 11.6x the initial capital lost.", pl: -116270, cumPl: -232540 },
          ]}
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(55),
      render: () => (
        <MistakeHighlightScene
          heading="The No Stop Loss Short"
          mistake={{
            label: "Shorting without a hard stop loss buy order",
            detail: "The GME short seller in our example had no stop loss. They had a thesis that the stock would decline to $5. When the stock went against them at $31, they held because the thesis was intact. The fundamental thesis being correct does not prevent a short squeeze. Markets can stay irrational longer than a short seller can stay solvent.",
          }}
          correction={{
            label: "Always place a hard stop loss buy order immediately after entering a short",
            detail: "Set a buy stop order 15 to 20 percent above your entry price when you enter any short. For GME at $20, that means a buy stop at $23 to $24. The loss is $3 to $4 per share maximum. If triggered, the stock has proven your thesis wrong in the near term and you exit with a defined small loss.",
          }}
          insight="Short selling requires both a correct fundamental thesis AND the ability to survive the timing. Even if GME was ultimately worth $5, a short entered at $20 with no stop would have been wiped out long before the stock ever reached $5."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(40),
      render: () => (
        <StatsScene
          heading="Short Squeeze Statistics"
          stats={[
            { label: "Average squeeze magnitude", value: "60 to 200%", color: accent },
            { label: "Duration", value: "5 to 20 days", color: "#f59e0b" },
            { label: "Short interest trigger", value: "Above 20% of float", color: "#6366f1" },
            { label: "Forced covering impact", value: "30 to 50% of rally", color: "#22c55e" },
          ]}
          footnote="Short squeezes are rare but catastrophic. The combination of high short interest and coordinated buying is the most dangerous scenario for short sellers."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(35),
      render: () => (
        <BulletScene
          heading="Short Selling Risk Rules You Cannot Skip"
          bullets={[
            "Never short without a hard stop loss buy order placed immediately at entry",
            "Check short interest before entering: above 20% of float significantly increases squeeze risk",
            "Size position so a 20% adverse move is your maximum portfolio loss (1 to 2% of account)",
            "Use puts instead of short stock for defined risk without margin requirements",
            "Avoid shorting during earnings week: gap ups can exceed your stop level instantly",
          ]}
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(30),
      render: () => (
        <SummaryScene
          heading="Short Risk: The Asymmetric Danger in Every Short Trade"
          takeaways={[
            "Short selling has unlimited maximum loss: the stock can always go higher",
            "Margin calls force buying at the worst prices during a squeeze",
            "Short interest above 20% of float signals meaningful squeeze risk",
            "Use put options instead of shorting stock to limit maximum loss to the premium paid",
          ]}
          accent={accent}
          closingLine="Next: Earnings quality signals and how to read between the lines of a quarterly report."
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

// ─────────────────────────────────────────────────────────────────────────────
// 8. FundamentalsEarningsLong
// ─────────────────────────────────────────────────────────────────────────────

export type FundamentalsEarningsLongProps = { accent?: string };
export const FundamentalsEarningsLong: React.FC<FundamentalsEarningsLongProps> = ({
  accent = "#ec4899",
}) => {
  useVideoConfig();
  const scenes: SceneDef[] = [
    {
      durationInFrames: sec(30),
      render: () => (
        <TitleScene
          label="Fundamental Analysis"
          title="Earnings Quality Signals"
          subtitle="How to read between the lines of a quarterly earnings report"
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(20),
      render: () => (
        <BulletScene
          heading="Five Quality Signals That Matter More Than EPS"
          bullets={[
            "Revenue growth rate year over year (sustainable vs one time)",
            "Operating margin trend (expanding or contracting)",
            "Guidance raised or lowered for next quarter",
            "Free cash flow vs net income alignment (confirms earnings quality)",
            "Revenue composition: recurring vs project based vs hardware",
          ]}
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(55),
      render: () => (
        <CalculationScene
          heading="AAPL Q4 2023 Earnings Quality Check"
          steps={[
            { label: "Revenue actual", formula: "Q4 2023 reported", result: "$89.5B" },
            { label: "Revenue estimate", formula: "Wall Street consensus", result: "$89.3B" },
            { label: "Revenue surprise", formula: "($89.5B minus $89.3B) / $89.3B", result: "+0.2% beat" },
            { label: "EPS actual", formula: "Q4 2023 reported", result: "$1.46" },
            { label: "EPS estimate", formula: "Wall Street consensus", result: "$1.39" },
            { label: "EPS surprise", formula: "($1.46 minus $1.39) / $1.39", result: "+5.0% beat", highlight: true },
            { label: "Services revenue growth", formula: "Year over year change", result: "+16.3% (high quality)", highlight: true, color: "#22c55e" },
          ]}
          conclusion="EPS beat and revenue beat are both present. More importantly, Services (recurring revenue) grew 16.3% proving high quality recurring growth not just hardware cycle."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(55),
      render: () => (
        <ComparisonTableScene
          heading="High Quality vs Low Quality Earnings"
          columns={["Signal", "High Quality Earnings", "Low Quality Earnings"]}
          rows={[
            { cells: ["Revenue", "Beat on organic growth", "Miss or beat on one time sale"], winner: 1 },
            { cells: ["EPS", "Beat on operating leverage", "Beat from share buybacks only"] },
            { cells: ["Guidance", "Raised for next quarter", "In line or lowered"], winner: 1, highlight: true },
            { cells: ["Cash flow", "FCF exceeds net income", "FCF lags net income significantly"] },
            { cells: ["Margins", "Expanding year over year", "Contracting or flat"], winner: 1 },
          ]}
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(60),
      render: () => (
        <SvgLineChartScene
          heading="AAPL Quarterly EPS: 8 Quarter Beat Track Record"
          subheading="Analyst estimates vs actual EPS over 8 consecutive quarters"
          data={[
            { label: "Q1 22", value: 2.1 },
            { label: "Q2 22", value: 1.52 },
            { label: "Q3 22", value: 1.29 },
            { label: "Q4 22", value: 1.29 },
            { label: "Q1 23", value: 1.52 },
            { label: "Q2 23", value: 1.26 },
            { label: "Q3 23", value: 1.4 },
            { label: "Q4 23", value: 1.46 },
          ]}
          yLabel="EPS ($)"
          xLabel="Quarter"
          highlightIdx={7}
          footnote="AAPL beat EPS estimates in all 8 of these quarters. However the stock dropped on 3 of those earnings days because guidance or revenue disappointed."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(65),
      render: () => (
        <WorkedExampleScene
          heading="Analyzing NVDA Q4 2024 Earnings in Real Time"
          subheading="Walking through the report section by section as a real investor would"
          company="NVIDIA"
          ticker="NVDA"
          trades={[
            { day: "Step 1", event: "Headline: $5.16 EPS vs $4.60 estimate (12.2% beat)", action: "Positive: meaningful beat. Check if it is recurring.", pl: 0, cumPl: 0 },
            { day: "Step 2", event: "Data center revenue $18.4B vs $17.2B estimate", action: "Positive: Data center (core business) beat significantly.", pl: 0, cumPl: 0 },
            { day: "Step 3", event: "Gross margin 76.7% vs 75.5% estimate", action: "Positive: margin expansion means pricing power intact.", pl: 0, cumPl: 0 },
            { day: "Step 4", event: "Next quarter guidance $24.0B vs $21.9B estimate", action: "Very positive: guidance raised 9.6% above consensus. Best part of report.", pl: 1000, cumPl: 1000 },
            { day: "Step 5", event: "Free cash flow $11.5B. Net income $12.3B.", action: "Near perfect alignment confirms earnings quality.", pl: 500, cumPl: 1500 },
          ]}
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(55),
      render: () => (
        <MistakeHighlightScene
          heading="The EPS Only Mistake"
          mistake={{
            label: "Buying or selling based solely on the EPS headline number",
            detail: "A trader sees Company X beat EPS by 8 percent and buys the stock. What they missed: revenue missed by 3%, guidance was in line (not raised), and the EPS beat came entirely from a $2B asset sale not from operations. The stock drops 6% after opening higher.",
          }}
          correction={{
            label: "Read the full earnings release in this order: revenue, margins, guidance, then EPS",
            detail: "Professional earnings traders read the release in this priority order: (1) revenue vs estimate and year over year growth, (2) operating margin vs prior year, (3) guidance vs current consensus, (4) EPS headline. EPS headline is last because it is most easily manipulated through accounting adjustments.",
          }}
          insight="Revenue and guidance drive stocks. EPS drives headlines. When AAPL raises guidance for the next quarter that is more bullish than a 10% EPS beat with flat guidance. Context always matters more than the headline number."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(40),
      render: () => (
        <StatsScene
          heading="Earnings Reaction Statistics"
          stats={[
            { label: "Stocks that beat EPS and rally", value: "~62%", color: "#22c55e" },
            { label: "Stocks that beat but drop on guidance", value: "~38%", color: accent },
            { label: "Average move magnitude", value: "5 to 8%", color: "#6366f1" },
            { label: "Direction prediction accuracy", value: "~55%", color: "#f59e0b" },
          ]}
          footnote="Direction prediction is only slightly better than a coin flip even with full earnings analysis. This is why defined risk options strategies are preferred for earnings."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(35),
      render: () => (
        <BulletScene
          heading="Earnings Quality Checklist"
          bullets={[
            "Check: is revenue growing faster or slower than last quarter? (trend matters)",
            "Check: did operating margins expand or contract year over year?",
            "Check: was guidance raised, maintained, or lowered? (most important signal)",
            "Check: does free cash flow confirm net income? (divergence = lower quality)",
            "Avoid trading earnings direction with naked options: use defined risk spreads",
          ]}
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(30),
      render: () => (
        <SummaryScene
          heading="Earnings Quality: Reading Beyond the Headline"
          takeaways={[
            "Revenue quality (recurring growth) matters more than EPS headline beats",
            "Guidance direction drives stock reaction more than current quarter numbers",
            "Free cash flow vs net income divergence signals low quality earnings",
            "Use defined risk options strategies for earnings plays not naked directional bets",
          ]}
          accent={accent}
          closingLine="Next: Valuation versus volatility and two different ways a stock can be expensive."
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

// ─────────────────────────────────────────────────────────────────────────────
// 9. ValuationVsVolLong
// ─────────────────────────────────────────────────────────────────────────────

export type ValuationVsVolLongProps = { accent?: string };
export const ValuationVsVolLong: React.FC<ValuationVsVolLongProps> = ({
  accent = "#6366f1",
}) => {
  useVideoConfig();
  const scenes: SceneDef[] = [
    {
      durationInFrames: sec(30),
      render: () => (
        <TitleScene
          label="Market Analysis"
          title="Valuation vs Volatility: Two Kinds of Expensive"
          subtitle="Forward PE and IV rank tell completely different stories about risk"
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(20),
      render: () => (
        <BulletScene
          heading="Two Independent Measures of Expensive"
          bullets={[
            "Valuation: how expensive the stock is relative to earnings (forward PE, PS ratio, EV/EBITDA)",
            "Implied volatility: how expensive options are relative to historical movement (IV rank, IV percentile)",
            "A stock can be expensive on both, cheap on both, or expensive on one and cheap on the other",
            "The best entry is cheap valuation AND cheap options (low IV)",
            "The worst entry is expensive valuation AND expensive options (high IV)",
          ]}
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(55),
      render: () => (
        <ComparisonTableScene
          heading="Four Scenarios: Valuation vs Options Pricing"
          columns={["Scenario", "Forward PE", "IV Rank", "Best Strategy", "Expected Return"]}
          rows={[
            { cells: ["Cheap val, cheap IV", "Below 20x", "Below 30%", "Buy stock or buy options", "High potential"], winner: 4, highlight: true },
            { cells: ["Cheap val, expensive IV", "Below 20x", "Above 70%", "Buy stock, sell options", "Moderate potential"] },
            { cells: ["Expensive val, cheap IV", "Above 30x", "Below 30%", "Cautious: small directional options", "Low potential"] },
            { cells: ["Expensive val, expensive IV", "Above 30x", "Above 70%", "Avoid long: sell spreads only", "Very low potential"] },
          ]}
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(60),
      render: () => (
        <CalculationScene
          heading="IV Rank Formula: Putting Current IV in Context"
          steps={[
            { label: "Current AAPL implied volatility", formula: "30 day IV today", result: "28%" },
            { label: "52 week low IV", formula: "Lowest IV this year", result: "16%" },
            { label: "52 week high IV", formula: "Highest IV this year", result: "46%" },
            { label: "IV range", formula: "High minus low", result: "30 percentage points" },
            { label: "Current position in range", formula: "(28% minus 16%)", result: "12 points above low" },
            { label: "IV rank", formula: "12 divided by 30", result: "40%", highlight: true },
          ]}
          conclusion="IV rank of 40% means current options pricing is at the 40th percentile of its past year range. Not cheap, not expensive. A reading above 60% suggests elevated options pricing worth selling."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(60),
      render: () => (
        <SvgLineChartScene
          heading="NVDA IV Rank Over 12 Months: When Options Were Cheap vs Expensive"
          subheading="IV rank from 0 percent to 100 percent across the year. Above 70 is expensive, below 30 is cheap."
          data={[
            { label: "Jan", value: 35 },
            { label: "Feb", value: 28 },
            { label: "Mar", value: 45 },
            { label: "Apr", value: 20 },
            { label: "May", value: 15 },
            { label: "Jun", value: 48 },
            { label: "Jul", value: 75 },
            { label: "Aug", value: 80 },
            { label: "Sep", value: 65 },
            { label: "Oct", value: 30 },
            { label: "Nov", value: 85 },
            { label: "Dec", value: 40 },
          ]}
          yLabel="IV Rank (%)"
          xLabel="Month"
          highlightIdx={10}
          footnote="The spikes in July to August and November correspond to NVDA earnings. Those were the most expensive times to buy options and the best times to sell spreads."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(60),
      render: () => (
        <WorkedExampleScene
          heading="NVDA: Finding the Best Entry Using Both Metrics"
          subheading="Combining forward PE analysis with IV rank to time entry"
          company="NVIDIA"
          ticker="NVDA"
          trades={[
            { day: "April check", event: "NVDA at $450. Forward PE 35x (expensive). IV rank 20% (cheap options).", action: "Valuation expensive but options cheap. Buy spreads not naked options. Small size.", pl: -500, cumPl: -500 },
            { day: "May dip", event: "NVDA drops to $400. Forward PE now 31x. IV rank still 15%.", action: "Valuation closer to fair value. Buy call debit spread $400 to $420.", pl: 0, cumPl: -500 },
            { day: "July rally", event: "NVDA at $500. PE 40x (very expensive). IV spikes to 75% before earnings.", action: "Both metrics now extreme: reduce long exposure significantly. Close spread.", pl: 2000, cumPl: 1500 },
            { day: "Post earnings", event: "NVDA beats, rallies to $525. IV crushes to 38%.", action: "PE still 42x but IV now moderate. Not ideal entry.", pl: 0, cumPl: 1500 },
            { day: "October", event: "NVDA consolidates at $460. PE 37x. IV rank 30%.", action: "Still expensive on valuation. Wait for better entry.", pl: 0, cumPl: 1500 },
          ]}
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(55),
      render: () => (
        <MistakeHighlightScene
          heading="The Cheap Options Trap"
          mistake={{
            label: "Buying options when IV rank is low thinking options are on sale",
            detail: "A trader sees IV rank at 15% and thinks options are cheap so they buy NVDA calls. The problem is that IV rank only measures how cheap options are relative to their own history. NVDA forward PE is 38x and growing. The stock faces valuation compression risk even if the options are cheap. Cheap options on an overvalued stock is still a bad trade.",
          }}
          correction={{
            label: "Require BOTH low IV rank and reasonable valuation before buying options",
            detail: "Low IV rank means options are priced cheaply. But you also need the underlying business to be reasonably valued so the stock has upside potential. The ideal setup is forward PE below the sector average AND IV rank below 30. Both conditions together create a much higher probability long trade.",
          }}
          insight="The relationship between valuation and volatility is often inverse: when stocks fall (getting cheaper on valuation) IV typically spikes (making options expensive). The window when both are favorable is relatively rare and valuable. Patience pays."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(40),
      render: () => (
        <StatsScene
          heading="Valuation and IV Combined Statistics"
          stats={[
            { label: "SPX forward PE average", value: "18 to 20x", color: accent },
            { label: "Above 25x historically expensive", value: "Underperforms 5 yr", color: "#ef4444" },
            { label: "Cheap IV rank (below 30)", value: "Buy options zone", color: "#22c55e" },
            { label: "Expensive IV rank (above 70)", value: "Sell options zone", color: accent },
          ]}
          footnote="Historical SPX data shows forward PE above 22x has lower 5 year forward returns than below 18x. These are general tendencies, not predictions."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(35),
      render: () => (
        <BulletScene
          heading="Combining Valuation and IV: A Simple Framework"
          bullets={[
            "Check forward PE vs sector average: above average means expensive",
            "Check IV rank vs 52 week range: above 60 means options are expensive relative to recent history",
            "If both cheap: buy the stock and buy options with high conviction",
            "If both expensive: sell defined risk premium or stay flat",
            "Use this dual check before every long options entry",
          ]}
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(30),
      render: () => (
        <SummaryScene
          heading="Two Lenses on Every Investment Decision"
          takeaways={[
            "Valuation tells you if the stock is expensive relative to earnings",
            "IV rank tells you if options are expensive relative to their own history",
            "The best options buying opportunity is low PE plus low IV rank",
            "Never buy options in high IV without checking if the underlying valuation also justifies the risk",
          ]}
          accent={accent}
          closingLine="Next: Liquidity runway and why your ability to exit matters as much as your entry."
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

// ─────────────────────────────────────────────────────────────────────────────
// 10. LiquidityRunwayLong
// ─────────────────────────────────────────────────────────────────────────────

export type LiquidityRunwayLongProps = { accent?: string };
export const LiquidityRunwayLong: React.FC<LiquidityRunwayLongProps> = ({
  accent = "#10b981",
}) => {
  useVideoConfig();
  const scenes: SceneDef[] = [
    {
      durationInFrames: sec(30),
      render: () => (
        <TitleScene
          label="Market Mechanics"
          title="Liquidity: Your Exit Door Size"
          subtitle="Why getting out of a trade can cost more than getting in"
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(20),
      render: () => (
        <BulletScene
          heading="Five Liquidity Metrics That Matter"
          bullets={[
            "Open interest: total outstanding contracts at this strike (need above 500)",
            "Bid and ask spread: width tells you the immediate round trip cost",
            "Average daily volume: how many contracts trade per day (need above 100)",
            "Underlying stock volume: low stock volume means low option liquidity too",
            "Time of day: spreads widen in first and last 30 minutes of trading session",
          ]}
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(55),
      render: () => (
        <ComparisonTableScene
          heading="Liquidity Spectrum: SPY vs AAPL vs Small Cap"
          columns={["Metric", "SPY (Excellent)", "AAPL (Good)", "Small Cap (Poor)"]}
          rows={[
            { cells: ["Bid/ask spread", "$0.01", "$0.10", "$0.40 to $0.80"], winner: 1 },
            { cells: ["Open interest", "Over 500,000", "Over 10,000", "100 to 500"] },
            { cells: ["Daily volume", "Over 100,000", "Over 5,000", "Under 200"] },
            { cells: ["Round trip cost", "0.1% of premium", "1 to 2%", "10 to 20%"], winner: 1 },
            { cells: ["Slippage risk", "Very low", "Low", "High to extreme"] },
          ]}
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(60),
      render: () => (
        <CalculationScene
          heading="Illiquidity Cost: What You Actually Lose"
          steps={[
            { label: "Option premium", formula: "ATM call on small cap", result: "$2.00" },
            { label: "Bid price", formula: "Market maker bid", result: "$1.60" },
            { label: "Ask price", formula: "Market maker ask", result: "$2.40" },
            { label: "Spread width", formula: "$2.40 minus $1.60", result: "$0.80" },
            { label: "Round trip cost", formula: "Full spread on entry and exit", result: "$0.80" },
            { label: "As percentage of premium", formula: "$0.80 divided by $2.00", result: "40%", highlight: true, color: "#ef4444" },
            { label: "10 contracts round trip", formula: "10 times $0.80 times 100", result: "$800 friction" },
          ]}
          conclusion="Paying 40% of your option's value in bid/ask spread before the stock moves a dollar means you start every trade down significantly. The stock must move enough to overcome this drag."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(60),
      render: () => (
        <SvgLineChartScene
          heading="Bid/Ask Spread as Percentage of Premium by Open Interest"
          subheading="Lower open interest means wider spreads and higher hidden cost"
          data={[
            { label: "100", value: 25 },
            { label: "500", value: 18 },
            { label: "1000", value: 12 },
            { label: "2500", value: 8 },
            { label: "5000", value: 5 },
            { label: "10000", value: 3 },
            { label: "25000", value: 1.5 },
            { label: "50000", value: 0.8 },
            { label: "100000", value: 0.4 },
          ]}
          yLabel="Spread as % of Premium"
          xLabel="Open Interest"
          highlightIdx={5}
          footnote="Above 10,000 open interest the spread as a percentage of premium drops below 3%. Below 1,000 you are often paying more than 10% just to enter."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(65),
      render: () => (
        <WorkedExampleScene
          heading="Liquidity Trap: Getting Stuck in an Illiquid Option"
          subheading="Buying options on a low volume name and trying to exit"
          company="Regional Bank Example"
          ticker="REGB"
          trades={[
            { day: "Entry", event: "Buy 10 contracts on regional bank at $1.80 mid price", action: "Bid $1.60, ask $2.00. Paid $2.00 (ask). Immediate slip from mid.", pl: -200, cumPl: -200 },
            { day: "Day 5", event: "Stock moves in your favor. Option theoretical value $2.80.", action: "Try to sell at $2.80. Market maker bids only $2.20.", pl: -60, cumPl: -260 },
            { day: "Day 5", event: "Place limit at $2.80. No fill for 2 hours.", action: "Lower to $2.60. Still no fill. Market has moved on.", pl: 0, cumPl: -260 },
            { day: "Day 5", event: "Stock dips slightly. Option now $2.40 theoretical.", action: "Accept $2.00 bid to exit. Barely better than entry price.", pl: 0, cumPl: -260 },
            { day: "Lesson", event: "Made the right call on direction but lost to illiquidity", action: "$0.80 spread width destroyed the profit. Only trade liquid options.", pl: -200, cumPl: -460 },
          ]}
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(50),
      render: () => (
        <MistakeHighlightScene
          heading="The Cheap Options Liquidity Trap"
          mistake={{
            label: "Buying cheap OTM options on illiquid names for low dollar risk",
            detail: "A trader buys 50 contracts of a low volume stock for $0.30 each. Total cost $1,500. The bid/ask is $0.10 to $0.50, a $0.40 spread. The stock moves but they cannot get out at a good price. The spread eats 67% of their potential profit every time they try to exit.",
          }}
          correction={{
            label: "Always check open interest and spread before entering. Minimum 1000 open interest.",
            detail: "For every options trade, click on the option and check: (1) bid to ask spread as percentage of premium. Keep it below 5%. (2) open interest above 1000. (3) daily volume above 100. If any of these fail, trade a more liquid name or adjust to a different strike where liquidity is better.",
          }}
          insight="Liquidity is a one way door: easy to get in, hard to get out when you need it most. During fast market conditions, bid/ask spreads on illiquid options can widen 2 to 3 times. That is exactly when you need to exit and exactly when it costs the most."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(35),
      render: () => (
        <StatsScene
          heading="Liquidity Thresholds for Safe Trading"
          stats={[
            { label: "Minimum open interest", value: "1,000 contracts", color: "#22c55e" },
            { label: "Maximum bid/ask", value: "5% of premium", color: accent },
            { label: "Minimum daily volume", value: "100 contracts", color: "#6366f1" },
            { label: "Trade hours", value: "9:45am to 3:45pm", color: "#f59e0b" },
          ]}
          footnote="The first and last 15 minutes of the trading day have the widest spreads. Avoid entries and exits during market open and close."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(35),
      render: () => (
        <BulletScene
          heading="Liquidity Rules for Every Trade"
          bullets={[
            "Never trade options with open interest below 1,000 at your strike",
            "Check bid/ask spread as percentage of premium: above 5% is too expensive",
            "Avoid market orders on options: always use limit orders at mid or better",
            "Do not trade in the first or last 15 minutes when spreads are widest",
            "Liquid underlyings (SPY, QQQ, AAPL, NVDA) are almost always better than obscure names",
          ]}
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(30),
      render: () => (
        <SummaryScene
          heading="Liquidity: The Silent Killer of Options Profits"
          takeaways={[
            "Illiquid options charge you 10 to 40% of premium in bid/ask spread alone",
            "Open interest above 1,000 and spread below 5% of premium are minimum requirements",
            "Getting out of an illiquid position at a fair price can be impossible in fast markets",
            "Stick to liquid names: SPY, QQQ, AAPL, NVDA, MSFT, AMZN for reliable fills",
          ]}
          accent={accent}
          closingLine="Next: Momentum box trades and identifying breakout setups before they happen."
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

// ─────────────────────────────────────────────────────────────────────────────
// 11. MomentumBoxLong
// ─────────────────────────────────────────────────────────────────────────────

export type MomentumBoxLongProps = { accent?: string };
export const MomentumBoxLong: React.FC<MomentumBoxLongProps> = ({
  accent = "#3b82f6",
}) => {
  useVideoConfig();
  const scenes: SceneDef[] = [
    {
      durationInFrames: sec(30),
      render: () => (
        <TitleScene
          label="Technical Analysis"
          title="The Momentum Box Trade"
          subtitle="Using price consolidation zones to identify high probability breakouts"
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(20),
      render: () => (
        <BulletScene
          heading="Why Momentum Boxes Work"
          bullets={[
            "Institutional buyers accumulate shares quietly during consolidation",
            "Volume contracts as selling pressure exhausts itself during box formation",
            "A breakout above the box triggers stop losses and FOMO buying simultaneously",
            "The measured move target (box height added to breakout) has high historical accuracy",
            "Momentum boxes work best when they form in the direction of a larger trend",
          ]}
          accent={accent}
          icon="📦"
        />
      ),
    },
    {
      durationInFrames: sec(55),
      render: () => (
        <SetupScene
          heading="Box Formation Requirements"
          items={[
            { label: "Price range", value: "Under 5% wide" },
            { label: "Formation days", value: "5 to 20 days" },
            { label: "Volume trend", value: "Declining during box" },
            { label: "Prior trend", value: "Clear uptrend or catalyst" },
            { label: "Catalyst context", value: "Earnings, sector rotation, macro" },
          ]}
          description="A valid momentum box requires all five elements. Missing any one reduces the probability of a sustained breakout. The declining volume during formation is the most critical element."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(60),
      render: () => (
        <CalculationScene
          heading="NVDA Momentum Box: Reading the Setup"
          steps={[
            { label: "Box high", formula: "NVDA resistance level", result: "$510.00" },
            { label: "Box low", formula: "NVDA support level", result: "$495.00" },
            { label: "Box width", formula: "$510 minus $495", result: "$15.00" },
            { label: "Box as percent of price", formula: "$15 / $500", result: "3.0% (tight box)", highlight: true, color: "#22c55e" },
            { label: "Breakout trigger", formula: "Close above $510 with volume", result: "$510.00" },
            { label: "Measured move target", formula: "$510 plus $15 box height", result: "$525.00" },
            { label: "Risk if failed breakout", formula: "Close back below $505", result: "Exit level" },
          ]}
          conclusion="The measured move target of $525 gives a 10 point reward on a 5 point risk, or 2:1. With volume confirmation the probability of reaching target is approximately 65%."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(65),
      render: () => (
        <SvgLineChartScene
          heading="NVDA Momentum Box: 12 Day Formation to Breakout"
          subheading="Price contained between $495 and $510 for 12 days before volume breakout"
          data={[
            { label: "D1", value: 508 },
            { label: "D2", value: 506 },
            { label: "D3", value: 504 },
            { label: "D4", value: 502 },
            { label: "D5", value: 503 },
            { label: "D6", value: 505 },
            { label: "D7", value: 507 },
            { label: "D8", value: 504 },
            { label: "D9", value: 501 },
            { label: "D10", value: 503 },
            { label: "D11", value: 506 },
            { label: "D12", value: 509 },
            { label: "D13 (Breakout)", value: 515 },
            { label: "D14", value: 520 },
            { label: "D15", value: 524 },
          ]}
          yLabel="NVDA Price ($)"
          xLabel="Day"
          highlightIdx={12}
          footnote="Volume on day 13 was 3.2x average daily volume confirming the breakout was institutional not retail driven."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(65),
      render: () => (
        <WorkedExampleScene
          heading="NVDA Box Breakout: Full Trade From Detection to Target"
          subheading="Entering on confirmation, managing to target, exiting with discipline"
          company="NVIDIA"
          ticker="NVDA"
          trades={[
            { day: "Day 1 to 12", event: "NVDA forms tight box between $495 and $510. Volume declining.", action: "Identify the box. Set alert for close above $510 with volume.", pl: 0, cumPl: 0 },
            { day: "Day 13", event: "NVDA closes at $515 on 3.2x average volume.", action: "Breakout confirmed. Buy 5 contracts of NVDA $510 call at $8.50.", pl: -850, cumPl: -850 },
            { day: "Day 14", event: "NVDA at $520. Following through above breakout level.", action: "Hold. Measured move target is $525. Stop at $507 (below box).", pl: 0, cumPl: -850 },
            { day: "Day 15", event: "NVDA reaches $524.50, within $0.50 of target.", action: "Close position at $524.50 area. Option worth $15.20.", pl: 670, cumPl: -180 },
            { day: "Exit", event: "Sell 5 contracts at $15.20. Net gain on options position.", action: "$670 profit on $850 risk. 78% return. Target achieved.", pl: 670, cumPl: 490 },
          ]}
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(55),
      render: () => (
        <MistakeHighlightScene
          heading="The False Breakout Trap"
          mistake={{
            label: "Entering on an intraday breakout without waiting for daily close above box",
            detail: "A trader sees NVDA touch $511 intraday and enters immediately. By end of day NVDA closes at $508, back inside the box. This is a false breakout. The trade triggered but the confirmation was premature. The position often results in a stop out below the box level.",
          }}
          correction={{
            label: "Only enter on a daily CLOSE above the box high with above average volume",
            detail: "The daily close is the definitive confirmation. Intraday pokes above the box are frequently tested and rejected. Waiting for the closing price costs some upside but eliminates the majority of false breakout entries. Volume above the 20 day average on the breakout day is also required.",
          }}
          insight="Failed breakouts are actually useful signals: if a stock closes above the box and then falls back through the next day, that is a bearish reversal signal. The bulls tried and failed. The subsequent move is often sharply lower."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(35),
      render: () => (
        <StatsScene
          heading="Momentum Box Statistics"
          stats={[
            { label: "Breakout success rate (volume confirm)", value: "~65%", color: "#22c55e" },
            { label: "Measured move achieved", value: "~55%", color: accent },
            { label: "Typical hold time", value: "5 to 15 days", color: "#6366f1" },
            { label: "Average risk/reward", value: "1.5 to 2.5:1", color: "#f59e0b" },
          ]}
          footnote="Statistics based on large cap breakouts with volume confirmation. Low volume breakouts fail approximately 55% of the time."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(30),
      render: () => (
        <BulletScene
          heading="Momentum Box Trade Rules"
          bullets={[
            "Entry only on daily close above box high with above average volume",
            "Stop loss placed below the box low, not below the breakout candle",
            "Target is box height added to breakout level (measured move)",
            "Take 50% off at target: let the remaining 50% run for an extended move",
            "Avoid breakouts against a strong market downtrend: trend alignment matters",
          ]}
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(30),
      render: () => (
        <SummaryScene
          heading="Momentum Box: Probabilities in Your Favor"
          takeaways={[
            "Boxes with declining volume during formation signal institutional accumulation",
            "Volume on the breakout day is the most important confirmation signal",
            "Measured move target gives a clear, objective profit level",
            "False breakouts are bearish signals: the stock often reverses sharply downward after failing",
          ]}
          accent={accent}
          closingLine="Next: RSI and MACD confirmation signals and how to use both indicators together."
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

// ─────────────────────────────────────────────────────────────────────────────
// 12. RsiMacdLong
// ─────────────────────────────────────────────────────────────────────────────

export type RsiMacdLongProps = { accent?: string };
export const RsiMacdLong: React.FC<RsiMacdLongProps> = ({
  accent = "#f59e0b",
}) => {
  useVideoConfig();
  const scenes: SceneDef[] = [
    {
      durationInFrames: sec(30),
      render: () => (
        <TitleScene
          label="Technical Indicators"
          title="RSI and MACD: The Dual Confirmation System"
          subtitle="Two indicators that work better together than either does alone"
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(20),
      render: () => (
        <BulletScene
          heading="What Each Indicator Measures"
          bullets={[
            "RSI measures recent gains versus recent losses over 14 periods as a percentage",
            "Above 70 is traditionally overbought, below 30 is oversold (but context matters)",
            "MACD line = 12 period EMA minus 26 period EMA (trend momentum)",
            "Signal line = 9 period EMA of MACD (trigger for crossovers)",
            "Histogram = MACD minus signal: positive means momentum building, negative means fading",
          ]}
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(55),
      render: () => (
        <CalculationScene
          heading="RSI Formula Step by Step"
          steps={[
            { label: "Average gain (14 periods)", formula: "Sum of all up closes / 14", result: "$0.42" },
            { label: "Average loss (14 periods)", formula: "Sum of all down closes / 14", result: "$0.28" },
            { label: "Relative strength", formula: "Average gain / average loss", result: "1.50" },
            { label: "RSI formula", formula: "100 minus (100 / (1 plus RS))", result: "100 minus 40 = 60" },
            { label: "RSI at 60", formula: "Neutral to bullish territory", result: "60", highlight: true },
            { label: "MACD line", formula: "12 EMA ($187.50) minus 26 EMA ($186.20)", result: "+$1.30" },
            { label: "Signal line (9 EMA of MACD)", formula: "Yesterday signal was $0.90", result: "+$1.05" },
          ]}
          conclusion="RSI at 60 shows positive momentum. MACD above signal line confirms momentum direction. Both agree: bullish trend intact."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(55),
      render: () => (
        <ComparisonTableScene
          heading="Signal Quality: Single Indicator vs Dual Confirmation"
          columns={["Signal Type", "False Positive Rate", "Win Rate", "Example Trigger"]}
          rows={[
            { cells: ["RSI below 30 alone", "40 to 45%", "~55%", "Buy when RSI crosses 30"] },
            { cells: ["MACD cross alone", "35 to 40%", "~60%", "Buy when MACD crosses signal"] },
            { cells: ["RSI plus MACD both bullish", "~20%", "~72%", "Both conditions met simultaneously"], highlight: true, winner: 2 },
            { cells: ["With price confirmation", "~15%", "~76%", "RSI plus MACD plus close above level"], winner: 2 },
          ]}
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(60),
      render: () => (
        <SvgLineChartScene
          heading="SPY RSI Over 30 Days: Oversold Signal With Context"
          subheading="RSI dropped below 30 in April and October. Both generated different outcomes based on market context."
          data={[
            { label: "D1", value: 65 },
            { label: "D3", value: 58 },
            { label: "D5", value: 52 },
            { label: "D7", value: 42 },
            { label: "D9", value: 32 },
            { label: "D11", value: 28 },
            { label: "D13", value: 24 },
            { label: "D15", value: 31 },
            { label: "D17", value: 41 },
            { label: "D19", value: 50 },
            { label: "D21", value: 58 },
            { label: "D23", value: 63 },
            { label: "D25", value: 67 },
            { label: "D27", value: 62 },
            { label: "D29", value: 57 },
          ]}
          yLabel="RSI Value"
          xLabel="Day"
          highlightIdx={6}
          footnote="RSI touched 24 at day 13 (oversold). Confirmation came when RSI crossed back above 30 at day 15 AND MACD histogram turned positive at the same time."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(60),
      render: () => (
        <WorkedExampleScene
          heading="SPY Trade Using RSI Plus MACD Dual Signal"
          subheading="Only enter when BOTH indicators confirm the signal simultaneously"
          company="S and P 500 ETF"
          ticker="SPY"
          trades={[
            { day: "Day 13", event: "SPY at $487. RSI at 24 (oversold). MACD still below signal.", action: "RSI oversold but MACD not confirmed. Wait. Do not enter yet.", pl: 0, cumPl: 0 },
            { day: "Day 15", event: "SPY at $488.50. RSI now at 31 (crossing above 30). MACD histogram turns positive.", action: "Both conditions met. Enter long SPY $490 call at $3.20.", pl: -320, cumPl: -320 },
            { day: "Day 19", event: "SPY at $494. RSI at 50 (neutral). MACD histogram strongly positive.", action: "Trend intact. Hold. Momentum building.", pl: 150, cumPl: -170 },
            { day: "Day 23", event: "SPY at $499. RSI at 63. MACD still positive.", action: "Near profit target. RSI approaching overbought.", pl: 250, cumPl: 80 },
            { day: "Day 25", event: "SPY at $501. RSI at 67. MACD histogram starting to shrink.", action: "MACD histogram shrinking is warning. Close at $501.", pl: 110, cumPl: 190 },
          ]}
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(55),
      render: () => (
        <MistakeHighlightScene
          heading="The Single Indicator Trap"
          mistake={{
            label: "Acting on RSI alone when it reaches 30 in a downtrend",
            detail: "During a significant market downtrend like the 2022 SPY decline from $480 to $350, RSI touched below 30 seven times. Each time looked like an oversold buy signal. But MACD was consistently below its signal line throughout the entire decline. Every single buy at RSI 30 lost money because the trend was still down.",
          }}
          correction={{
            label: "Require MACD confirmation before acting on RSI oversold readings",
            detail: "The rule is simple: when RSI drops below 30 (oversold), put it on watch. Only enter long when RSI crosses back above 30 AND the MACD histogram is positive (or just turned positive from negative). The MACD confirmation filters out the majority of downtrend false signals.",
          }}
          insight="Indicators measure the past. RSI says the last 14 days saw more selling than buying. MACD says momentum shifted in direction X. Neither predicts the future. They reduce probability of false signals when used together but cannot eliminate all losses."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(35),
      render: () => (
        <StatsScene
          heading="Dual Signal Statistics: RSI plus MACD"
          stats={[
            { label: "False positive reduction", value: "50 to 55%", color: "#22c55e" },
            { label: "Win rate improvement", value: "+15 to 20%", color: accent },
            { label: "Signal frequency reduction", value: "40% fewer trades", color: "#6366f1" },
            { label: "Average holding period", value: "8 to 15 days", color: "#a855f7" },
          ]}
          footnote="Dual confirmation trades fewer signals but with meaningfully higher win rate. Fewer better trades outperforms many mediocre ones."
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(35),
      render: () => (
        <BulletScene
          heading="RSI and MACD Rules for Clean Signals"
          bullets={[
            "RSI oversold (below 30) is a watch signal: wait for MACD histogram to turn positive before entering",
            "RSI overbought (above 70) is a watch signal: wait for MACD to cross below signal before shorting",
            "Always check the broader market trend: indicators work better with the trend than against it",
            "Use weekly chart for trend direction and daily chart for entry timing",
            "Divergence: price makes new high but RSI makes lower high = caution signal even in an uptrend",
          ]}
          accent={accent}
        />
      ),
    },
    {
      durationInFrames: sec(30),
      render: () => (
        <SummaryScene
          heading="Dual Confirmation: Better Signals Through Agreement"
          takeaways={[
            "Single indicator signals have 35 to 45% false positive rates",
            "RSI and MACD together reduce false positives by approximately 50%",
            "Require both indicators to agree before entering: if they disagree wait",
            "RSI identifies the oversold or overbought condition, MACD confirms momentum direction",
          ]}
          accent={accent}
          closingLine="Next: Stocks 101 and the fundamentals of equity ownership."
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
