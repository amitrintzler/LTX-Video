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

// ── OptionsChainReadingLong ───────────────────────────────────────────────────
// Lesson: options-chain-reading — "The Options Chain Decoded"

export type OptionsChainReadingLongProps = {
  accent?: string;
};

export const OptionsChainReadingLong: React.FC<OptionsChainReadingLongProps> = ({
  accent = "#10b981",
}) => {
  useVideoConfig();

  const scenes: SceneDef[] = [
    // Scene 1 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <TitleScene
          label="Options Chain"
          title="The Options Chain Decoded"
          subtitle="Reading every column and making smarter entries"
          accent={accent}
        />
      ),
    },

    // Scene 2 (20s)
    {
      durationInFrames: sec(20),
      render: () => (
        <BulletScene
          heading="Six Columns Every Trader Must Read"
          bullets={[
            "Bid and Ask spread: the market maker fee built into every trade",
            "Volume: total contracts traded today across all participants",
            "Open Interest: total outstanding contracts not yet closed or exercised",
            "IV: implied volatility embedded in the current option price",
            "Delta: your directional exposure per one dollar stock move",
            "Strike: the agreed transaction price if the option is exercised",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 3 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <ComparisonTableScene
          heading="AAPL Chain at $185: Reading 5 Strikes"
          columns={["Strike", "Call Bid/Ask", "Call OI", "Call IV", "Put Bid/Ask"]}
          rows={[
            { cells: ["$175", "$10.50 / $10.70", "12,500", "22%", "$0.40 / $0.55"] },
            { cells: ["$180", "$6.20 / $6.40", "9,800", "24%", "$1.10 / $1.30"] },
            { cells: ["$185", "$3.30 / $3.50", "18,200", "27%", "$3.30 / $3.50"], highlight: true },
            { cells: ["$190", "$1.40 / $1.60", "7,400", "30%", "$6.40 / $6.60"] },
            { cells: ["$195", "$0.45 / $0.55", "3,800", "34%", "$10.50 / $10.70"] },
          ]}
          accent={accent}
          subheading="ATM strike at $185 shows the tightest spread and highest open interest"
        />
      ),
    },

    // Scene 4 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <CalculationScene
          heading="Breakeven from Chain Prices"
          steps={[
            {
              label: "AAPL $185 Call at $3.50",
              formula: "Strike + Premium = Breakeven",
              result: "$188.50",
              highlight: true,
              color: accent,
            },
            {
              label: "AAPL $185 Put at $3.10",
              formula: "Strike minus Premium = Breakeven",
              result: "$181.90",
              highlight: false,
            },
            {
              label: "Expected Move from Strangle",
              formula: "Call + Put = $3.50 + $3.10",
              result: "$6.60",
              highlight: false,
            },
            {
              label: "Upper and Lower Expected Range",
              formula: "$185 plus or minus $6.60",
              result: "$178 to $192",
              highlight: true,
              color: accent,
            },
          ]}
          conclusion="The chain tells you exactly what the market expects before you place a single trade"
          accent={accent}
        />
      ),
    },

    // Scene 5 (60s)
    {
      durationInFrames: sec(60),
      render: () => (
        <BulletScene
          heading="Open Interest vs Volume: The Difference That Matters"
          bullets={[
            "Open Interest is cumulative: all contracts currently outstanding across all expiries",
            "Volume is a single day count: resets to zero at the start of each session",
            "High OI at a specific strike creates a magnet effect near expiry",
            "High volume without a change in OI means traders are closing and opening equal positions",
            "Use both signals together: high OI confirms liquidity, high volume confirms activity",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 6 (65s)
    {
      durationInFrames: sec(65),
      render: () => (
        <SvgLineChartScene
          heading="IV Skew: Why OTM Puts Cost More Than Models Predict"
          subheading="Implied volatility by strike showing the classic skew shape"
          data={[
            { label: "$165", value: 42 },
            { label: "$170", value: 38 },
            { label: "$175", value: 34 },
            { label: "$180", value: 31 },
            { label: "$185", value: 27 },
            { label: "$190", value: 25 },
            { label: "$195", value: 24 },
            { label: "$200", value: 23 },
          ]}
          accent={accent}
          yLabel="IV %"
          xLabel="Strike Price"
          highlightIdx={4}
          footnote="OTM puts carry a premium because the market prices in crash and tail risk that models underestimate"
        />
      ),
    },

    // Scene 7 (60s)
    {
      durationInFrames: sec(60),
      render: () => (
        <WorkedExampleScene
          heading="Reading the Chain Before an Earnings Trade"
          company="Tesla"
          ticker="TSLA"
          trades={[
            {
              day: "Day 1",
              event: "IV Rank at 85 percent before earnings",
              action: "Note elevated premiums across all strikes",
              pl: 0,
              cumPl: 0,
            },
            {
              day: "Day 1",
              event: "ATM straddle at $700 strike priced at $38",
              action: "Expected move confirmed as plus or minus $38",
              pl: 0,
              cumPl: 0,
            },
            {
              day: "Day 1",
              event: "Highest OI concentrated at $700 and $720 strikes",
              action: "Sell spread between $720 call and $740 call for $4.20 credit",
              pl: 420,
              cumPl: 420,
            },
            {
              day: "Day 2",
              event: "TSLA reports earnings, stock gaps to $715",
              action: "Spread stays below $720 breakeven, profit intact",
              pl: 0,
              cumPl: 420,
            },
            {
              day: "Day 3",
              event: "Expiry day, TSLA closes at $712",
              action: "Both legs expire worthless, keep full credit",
              pl: 420,
              cumPl: 840,
            },
          ]}
          accent={accent}
          subheading="Chain reading guided strike selection and position sizing"
        />
      ),
    },

    // Scene 8 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <MistakeHighlightScene
          heading="The Liquidity Trap in the Options Chain"
          mistake={{
            label: "Buying illiquid options with wide spreads",
            detail:
              "A $0.40 wide spread on a $1.00 option means you lose 40 percent of premium on entry alone. The market maker collects that cost before the stock moves at all.",
          }}
          correction={{
            label: "Only trade options with spreads under 10 percent of premium",
            detail:
              "On a $3.50 option the maximum acceptable spread is $0.35. Filter out any chain row where the spread exceeds this threshold before considering a trade.",
          }}
          insight="The round trip cost on an illiquid option can exceed the maximum reward on the trade. Liquidity is not optional, it is the first filter."
          accent={accent}
        />
      ),
    },

    // Scene 9 (45s)
    {
      durationInFrames: sec(45),
      render: () => (
        <StatsScene
          heading="Options Chain Quick Reference Facts"
          stats={[
            { label: "Market Hours", value: "9:30 to 4:00 ET", color: accent },
            { label: "Settlement Day", value: "3rd Friday", color: "#3b82f6" },
            { label: "Contract Multiplier", value: "100 shares", color: "#f59e0b" },
            { label: "Penny Pilot Spread", value: "$0.01 min", color: "#22c55e" },
          ]}
          accent={accent}
          footnote="Non penny pilot options trade in $0.05 increments, creating wider spreads and higher entry costs"
        />
      ),
    },

    // Scene 10 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <CalculationScene
          heading="Expected Move Calculation from the Chain"
          steps={[
            {
              label: "ATM Call Premium",
              formula: "AAPL $185 Call = $3.50",
              result: "$3.50",
            },
            {
              label: "ATM Put Premium",
              formula: "AAPL $185 Put = $3.10",
              result: "$3.10",
            },
            {
              label: "Raw Straddle Price",
              formula: "$3.50 + $3.10",
              result: "$6.60",
            },
            {
              label: "1 Standard Deviation Move",
              formula: "$6.60 times 0.85 adjustment",
              result: "$5.61",
              highlight: true,
              color: accent,
            },
          ]}
          conclusion="The chain prices in a $5.61 expected move. Any strategy must pay off if the stock stays within this range."
          accent={accent}
        />
      ),
    },

    // Scene 11 (35s)
    {
      durationInFrames: sec(35),
      render: () => (
        <BulletScene
          heading="Chain Reading Checklist Before Every Trade"
          bullets={[
            "Bid and ask spread below 10 percent of premium for adequate liquidity",
            "Open Interest above 500 contracts to ensure real two sided market",
            "IV rank versus 52 week range to gauge if premiums are cheap or expensive",
            "Volume confirms directional interest not just stale open positions",
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
          heading="Reading the Chain Is Your First Edge"
          takeaways={[
            "Six columns contain everything you need: spread, volume, OI, IV, delta and strike",
            "Breakeven is always strike plus premium for calls and strike minus premium for puts",
            "Open Interest at a strike is a magnet that attracts price near expiry",
            "Never trade options where the spread exceeds 10 percent of the premium",
          ]}
          accent={accent}
          closingLine="Master the chain and you will never enter a trade without knowing the odds first"
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

// ── StrikePriceMasteryLong ────────────────────────────────────────────────────
// Lesson: strike-price-mastery — "Choosing the Right Strike"

export type StrikePriceMasteryLongProps = {
  accent?: string;
};

export const StrikePriceMasteryLong: React.FC<StrikePriceMasteryLongProps> = ({
  accent = "#3b82f6",
}) => {
  useVideoConfig();

  const scenes: SceneDef[] = [
    // Scene 1 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <TitleScene
          label="Strike Price Mastery"
          title="Choosing the Right Strike"
          subtitle="ITM, ATM and OTM defined with real probability math"
          accent={accent}
        />
      ),
    },

    // Scene 2 (25s)
    {
      durationInFrames: sec(25),
      render: () => (
        <BulletScene
          heading="Three Strike Zones: What Each One Means"
          bullets={[
            "In the Money (ITM): strike already past current stock price, high delta, expensive premium",
            "At the Money (ATM): strike closest to current price, delta near 0.50, default starting point",
            "Out of the Money (OTM): strike past current price, low delta, cheap premium but low probability",
            "Delta is the probability proxy: a 0.30 delta call has roughly 30 percent chance of expiring in the money",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 3 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <ComparisonTableScene
          heading="SPY at $500: Five Strikes Side by Side"
          columns={["Strike", "Type", "Delta", "Premium", "Breakeven"]}
          rows={[
            { cells: ["$480", "Deep ITM", "0.82", "$24.50", "$504.50"] },
            { cells: ["$490", "ITM", "0.68", "$14.50", "$504.50"] },
            { cells: ["$500", "ATM", "0.50", "$8.50", "$508.50"], highlight: true },
            { cells: ["$510", "OTM", "0.32", "$4.20", "$514.20"] },
            { cells: ["$520", "Deep OTM", "0.16", "$1.80", "$521.80"] },
          ]}
          accent={accent}
          subheading="SPY 30 day calls, current price $500"
        />
      ),
    },

    // Scene 4 (60s)
    {
      durationInFrames: sec(60),
      render: () => (
        <PayoffDiagramScene
          heading="Three Strikes, Three Payoff Profiles"
          subheading="Long call at $180 ITM vs $185 ATM vs $190 OTM, same expiry"
          legs={[{ type: "long-call", strike: 185, premium: 3.5 }]}
          priceMin={165}
          priceMax={215}
          currentPrice={185}
          accent={accent}
          footnote="ATM breakeven at $188.50. OTM requires a larger move to profit but costs less upfront."
        />
      ),
    },

    // Scene 5 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <CalculationScene
          heading="How Much Move Does Each Strike Need?"
          steps={[
            {
              label: "ATM $500 Call at $8.50",
              formula: "$500 + $8.50 = breakeven",
              result: "$508.50",
              highlight: false,
            },
            {
              label: "OTM $510 Call at $4.20",
              formula: "$510 + $4.20 = breakeven",
              result: "$514.20",
              highlight: false,
            },
            {
              label: "Deep OTM $520 Call at $1.80",
              formula: "$520 + $1.80 = breakeven",
              result: "$521.80",
              highlight: true,
              color: "#ef4444",
            },
            {
              label: "Move Needed Above ATM",
              formula: "$521.80 minus $500 current price",
              result: "4.4% move",
              highlight: false,
            },
          ]}
          conclusion="The cheap deep OTM option needs a 4.4 percent move just to break even. The ATM only needs 1.7 percent."
          accent={accent}
        />
      ),
    },

    // Scene 6 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <SvgLineChartScene
          heading="Probability of Profit Drops as Strike Goes Further OTM"
          subheading="Delta as probability proxy across SPY strikes"
          data={[
            { label: "$470", value: 92 },
            { label: "$480", value: 82 },
            { label: "$490", value: 68 },
            { label: "$500", value: 50 },
            { label: "$510", value: 32 },
            { label: "$520", value: 16 },
            { label: "$530", value: 7 },
          ]}
          accent={accent}
          yLabel="Probability %"
          xLabel="Strike (calls)"
          highlightIdx={3}
          footnote="Delta below 0.20 means the option expires worthless 80 percent of the time. Cheap is not the same as good value."
        />
      ),
    },

    // Scene 7 (45s)
    {
      durationInFrames: sec(45),
      render: () => (
        <MistakeHighlightScene
          heading="Cheap Options Are Not Bargains"
          mistake={{
            label: "Buying deep OTM options because they are cheap",
            detail:
              "A $1.80 option looks affordable but delta below 0.20 means an 80 percent chance of expiring worthless. The math does not improve just because the dollar amount is small.",
          }}
          correction={{
            label: "Focus on delta not dollar cost when selecting a strike",
            detail:
              "A 0.30 or higher delta gives you a real probability of profit. Start at the money and move OTM only when a defined reason exists, not because the premium looks low.",
          }}
          insight="Probability of profit is determined by delta, not by how much you paid. A strike with delta 0.15 is almost always a lottery ticket regardless of price."
          accent={accent}
        />
      ),
    },

    // Scene 8 (60s)
    {
      durationInFrames: sec(60),
      render: () => (
        <WorkedExampleScene
          heading="Three Strike Choices on the Same SPY Trade"
          company="S and P 500 ETF"
          ticker="SPY"
          trades={[
            {
              day: "Entry",
              event: "SPY at $500, bullish view for 2 weeks",
              action: "Compare three call strikes before choosing",
              pl: 0,
              cumPl: 0,
            },
            {
              day: "Result A",
              event: "SPY moves to $510, ITM $490 call at $14.50",
              action: "Option worth $22.00, gain of $7.50 per share",
              pl: 750,
              cumPl: 750,
            },
            {
              day: "Result B",
              event: "SPY moves to $510, ATM $500 call at $8.50",
              action: "Option worth $11.50, gain of $3.00 per share",
              pl: 300,
              cumPl: 300,
            },
            {
              day: "Result C",
              event: "SPY moves to $510, OTM $510 call at $4.20",
              action: "Option worth $1.80 at expiry, loss of $2.40 per share",
              pl: -240,
              cumPl: -240,
            },
            {
              day: "Lesson",
              event: "ITM won in dollar terms, OTM lost despite correct direction",
              action: "Strike selection determined the outcome, not direction",
              pl: 0,
              cumPl: 0,
            },
          ]}
          accent={accent}
          subheading="Correct direction, three different outcomes based on strike alone"
        />
      ),
    },

    // Scene 9 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <StatsScene
          heading="Strike Selection Key Numbers"
          stats={[
            { label: "ATM Delta", value: "0.50", color: accent },
            { label: "Min Delta Threshold", value: "0.20", color: "#ef4444" },
            { label: "ITM Delta Range", value: "0.60 to 0.90", color: "#22c55e" },
            { label: "OTM Delta Range", value: "0.10 to 0.40", color: "#f59e0b" },
          ]}
          accent={accent}
          footnote="These delta ranges apply to standard equity options. Index options may show slightly different skew patterns."
        />
      ),
    },

    // Scene 10 (35s)
    {
      durationInFrames: sec(35),
      render: () => (
        <BulletScene
          heading="When to Choose Each Strike Zone"
          bullets={[
            "ATM: default choice when you want balanced risk and clean delta exposure",
            "ITM: when you want stock replacement or delta above 0.65 with less time decay risk",
            "OTM: only when you have a defined catalyst and accept a lower probability of profit",
            "Never go below 0.20 delta without acknowledging you are taking a speculative position",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 11 (35s)
    {
      durationInFrames: sec(35),
      render: () => (
        <RealWorldExampleScene
          heading="SPY Breakout Trade: Strike Selection in Practice"
          company="SPDR S and P 500 ETF Trust"
          scenario="SPY breaks above $500 resistance on strong volume. Bullish setup with 2 week target of $515."
          setupItems={[
            { label: "Entry Price", value: "$500", color: accent },
            { label: "Target", value: "$515", color: "#22c55e" },
            { label: "Strike Chosen", value: "$500 ATM", color: accent },
            { label: "Premium Paid", value: "$8.50", color: "#f59e0b" },
            { label: "Delta", value: "0.50", color: "#94a3b8" },
          ]}
          outcome="+$300 per contract"
          outcomeDetail="SPY reached $511, ATM call worth $11.80, sold for $3.30 gain on $8.50 cost. OTM alternative expired worthless."
          outcomeColor="#22c55e"
          accent={accent}
        />
      ),
    },

    // Scene 12 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <SummaryScene
          heading="Strike Selection Is Half the Trade"
          takeaways={[
            "Delta is your probability proxy: 0.50 delta means 50 percent chance of expiry in the money",
            "Start at the money and move OTM only with a specific reason, not to save premium",
            "Cheap options cost you probability, not just dollars",
            "A correct directional view can still lose money at the wrong strike",
          ]}
          accent={accent}
          closingLine="Pick the strike first, pick the premium second. Probability drives profitability."
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

// ── ContractsWalkthroughLong ──────────────────────────────────────────────────
// Lesson: contracts-walkthrough — "Inside One Options Contract"

export type ContractsWalkthroughLongProps = {
  accent?: string;
};

export const ContractsWalkthroughLong: React.FC<ContractsWalkthroughLongProps> = ({
  accent = "#f59e0b",
}) => {
  useVideoConfig();

  const scenes: SceneDef[] = [
    // Scene 1 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <TitleScene
          label="Options Contracts"
          title="Inside One Options Contract"
          subtitle="Every field explained with real numbers from entry to expiry"
          accent={accent}
        />
      ),
    },

    // Scene 2 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <SetupScene
          heading="All 7 Fields of a Standard Options Contract"
          items={[
            { label: "Underlying", value: "AAPL", color: accent },
            { label: "Type", value: "Call", color: "#22c55e" },
            { label: "Strike", value: "$185", color: accent },
            { label: "Expiry", value: "Jan 17 2025", color: "#94a3b8" },
            { label: "Style", value: "American", color: "#3b82f6" },
            { label: "Multiplier", value: "100 shares", color: "#f59e0b" },
            { label: "Premium", value: "$3.50", color: "#ef4444" },
          ]}
          accent={accent}
          description="One AAPL January 185 Call: the full specification of a single contract"
        />
      ),
    },

    // Scene 3 (25s)
    {
      durationInFrames: sec(25),
      render: () => (
        <BulletScene
          heading="The 100 Share Multiplier and Why It Matters"
          bullets={[
            "Every standard equity option controls exactly 100 shares of the underlying stock",
            "A $3.50 quoted premium costs $350 total per contract, not $3.50",
            "One lot of 10 contracts controls 1,000 shares and costs $3,500 in premium",
            "The multiplier means small premium moves create large dollar swings in P and L",
            "Always multiply the quoted price by 100 before calculating any position size",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 4 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <CalculationScene
          heading="Breaking Down the $3.50 Premium"
          steps={[
            {
              label: "Total Cost of 1 Contract",
              formula: "$3.50 premium times 100 shares",
              result: "$350",
              highlight: false,
            },
            {
              label: "Intrinsic Value (AAPL at $186)",
              formula: "$186 stock minus $185 strike",
              result: "$1.00",
              highlight: false,
            },
            {
              label: "Time Value (Extrinsic)",
              formula: "$3.50 premium minus $1.00 intrinsic",
              result: "$2.50",
              highlight: true,
              color: "#ef4444",
            },
            {
              label: "Position Size for $1,000 Max Risk",
              formula: "$1,000 divided by $350 per contract",
              result: "2 contracts",
              highlight: true,
              color: accent,
            },
          ]}
          conclusion="The $2.50 of time value evaporates to zero by expiry regardless of where the stock goes. That is the cost of holding this right."
          accent={accent}
        />
      ),
    },

    // Scene 5 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <ComparisonTableScene
          heading="American vs European vs FLEX Contracts"
          columns={["Feature", "American", "European", "FLEX"]}
          rows={[
            { cells: ["Exercise Timing", "Any day before expiry", "Expiry day only", "Custom agreed date"] },
            { cells: ["Common Underlying", "Equities and ETFs", "Index options (SPX)", "Institutional custom"] },
            { cells: ["Assignment Risk", "Any day possible", "No early assignment", "Defined by contract"] },
            { cells: ["Time Value Captured", "Sell to avoid loss", "Auto settled in cash", "Per agreement"] },
            { cells: ["Best Practice", "Sell before expiry", "Hold until expiry", "Institutional only"] },
          ]}
          accent={accent}
          subheading="Most retail traders use American style equity options exclusively"
        />
      ),
    },

    // Scene 6 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <BulletScene
          heading="Exercise and Assignment: What Actually Happens"
          bullets={[
            "Exercise means the option holder demands the right to buy or sell at the strike price",
            "Assignment means the option seller must fulfill the obligation on the other side",
            "When you exercise a $185 call you receive 100 shares of AAPL and pay $185 each",
            "Cash settled options (SPX) close for the intrinsic value in cash with no share delivery",
            "Early exercise destroys time value: almost always better to sell the option instead",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 7 (45s)
    {
      durationInFrames: sec(45),
      render: () => (
        <MistakeHighlightScene
          heading="Exercising Early and Destroying Time Value"
          mistake={{
            label: "Exercising an in the money option before expiry",
            detail:
              "An AAPL $185 call with stock at $195 has $10 intrinsic plus $1.50 of remaining time value. Exercising early captures only $10 and wastes the $1.50.",
          }}
          correction={{
            label: "Sell the option to capture full value including time premium",
            detail:
              "Selling a long option at market price captures both intrinsic and time value in one transaction. You receive more than exercise would give you in almost all scenarios.",
          }}
          insight="Time value is free money when you close by selling. Exercising always forfeits whatever time value remains. Sell first, exercise almost never."
          accent={accent}
        />
      ),
    },

    // Scene 8 (60s)
    {
      durationInFrames: sec(60),
      render: () => (
        <WorkedExampleScene
          heading="AAPL Earnings Play: Contract Selection to Expiry"
          company="Apple Inc"
          ticker="AAPL"
          trades={[
            {
              day: "Day 1",
              event: "AAPL at $185, earnings in 14 days, IV at 35 percent",
              action: "Buy 1 AAPL Jan 185 Call at $3.50, total cost $350",
              pl: -350,
              cumPl: -350,
            },
            {
              day: "Day 7",
              event: "Stock rises to $189, option worth $5.80",
              action: "Decide: sell for $230 gain or hold through earnings",
              pl: 230,
              cumPl: -120,
            },
            {
              day: "Day 14",
              event: "Earnings beat, stock gaps to $196, IV crushes to 22 percent",
              action: "Option worth $11.20 despite IV drop due to large intrinsic gain",
              pl: 760,
              cumPl: 640,
            },
            {
              day: "Day 15",
              event: "Time value still at $0.60 with 3 days to expiry",
              action: "Sell option at $11.20 to capture remaining time value",
              pl: 60,
              cumPl: 820,
            },
            {
              day: "Lesson",
              event: "Held through earnings and sold before expiry",
              action: "Captured $820 on $350 risk by understanding the contract structure",
              pl: 0,
              cumPl: 820,
            },
          ]}
          accent={accent}
          subheading="30 day ATM call, held through earnings catalyst"
        />
      ),
    },

    // Scene 9 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <StatsScene
          heading="Contract Specification Quick Reference"
          stats={[
            { label: "Standard Multiplier", value: "100x", color: accent },
            { label: "Max Loss (Long)", value: "Premium Paid", color: "#ef4444" },
            { label: "Expiry Cycle", value: "3rd Friday", color: "#3b82f6" },
            { label: "Settlement", value: "T plus 1 day", color: "#22c55e" },
          ]}
          accent={accent}
          footnote="Mini options trade in 10 share lots at some brokers but standard contracts are always 100 shares per contract"
        />
      ),
    },

    // Scene 10 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <BulletScene
          heading="Moneyness: ITM, ATM and OTM for Calls and Puts"
          bullets={[
            "Call is ITM when stock price is above the strike: has positive intrinsic value",
            "Put is ITM when stock price is below the strike: has positive intrinsic value",
            "ATM options have no intrinsic value, only time value and implied volatility premium",
            "Deep ITM options trade nearly dollar for dollar with the stock: high delta, small time value",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 11 (35s)
    {
      durationInFrames: sec(35),
      render: () => (
        <RealWorldExampleScene
          heading="AAPL Contract: Full Lifecycle in 30 Days"
          company="Apple Inc"
          scenario="Buy 1 AAPL 30 day $185 call at $3.50. Stock moves from $185 to $192 by expiry."
          setupItems={[
            { label: "Cost", value: "$350 total", color: accent },
            { label: "Stock Move", value: "+$7", color: "#22c55e" },
            { label: "Intrinsic at Expiry", value: "$7.00", color: "#22c55e" },
            { label: "Time Value at Expiry", value: "$0.00", color: "#ef4444" },
          ]}
          outcome="+$350 profit"
          outcomeDetail="Option worth $7.00 at expiry on $3.50 cost. 100 percent return in 30 days on a 3.8 percent stock move."
          outcomeColor="#22c55e"
          accent={accent}
        />
      ),
    },

    // Scene 12 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <SummaryScene
          heading="Every Contract Has Seven Fields and One Rule"
          takeaways={[
            "Underlying, type, strike, expiry, style, multiplier and premium define every contract",
            "The 100 share multiplier turns small premium moves into meaningful dollar changes",
            "Time value is real money that exists until expiry and then disappears permanently",
            "Selling the option before expiry almost always beats early exercise for the buyer",
          ]}
          accent={accent}
          closingLine="Read all seven fields before any trade. Understand the contract before you commit the premium."
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

// ── BidAskRealityLong ─────────────────────────────────────────────────────────
// Lesson: bid-ask-reality — "The Hidden Cost in Every Trade"

export type BidAskRealityLongProps = {
  accent?: string;
};

export const BidAskRealityLong: React.FC<BidAskRealityLongProps> = ({
  accent = "#ef4444",
}) => {
  useVideoConfig();

  const scenes: SceneDef[] = [
    // Scene 1 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <TitleScene
          label="Bid and Ask Reality"
          title="The Hidden Cost in Every Trade"
          subtitle="How the spread silently erodes returns and how to fight back"
          accent={accent}
        />
      ),
    },

    // Scene 2 (25s)
    {
      durationInFrames: sec(25),
      render: () => (
        <BulletScene
          heading="What the Bid and Ask Actually Represent"
          bullets={[
            "Bid price: the highest price any buyer is currently willing to pay",
            "Ask price: the lowest price any seller is currently willing to accept",
            "Mid price: the exact midpoint between bid and ask, the fair value estimate",
            "Spread: ask minus bid, represents the market maker profit on every transaction",
            "Natural price: where the option would trade if both sides agreed on mid",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 3 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <ComparisonTableScene
          heading="Spread Comparison: SPY vs AAPL vs Small Cap"
          columns={["Metric", "SPY Options", "AAPL Options", "Small Cap Options"]}
          rows={[
            { cells: ["Bid / Ask Example", "$8.95 / $9.00", "$3.40 / $3.60", "$0.60 / $1.00"], winner: 1 },
            { cells: ["Spread Width", "$0.05", "$0.20", "$0.40"] },
            { cells: ["Spread as Percent of Premium", "0.6%", "5.7%", "40%"], winner: 1 },
            { cells: ["Round Trip Cost 10 contracts", "$50", "$200", "$400"], winner: 1 },
            { cells: ["Liquidity Rating", "Excellent", "Good", "Poor"], winner: 1 },
          ]}
          accent={accent}
          subheading="Spread as a percentage of premium is the real cost metric, not the raw dollar spread"
        />
      ),
    },

    // Scene 4 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <CalculationScene
          heading="Real Cost of a 10 Contract AAPL Trade"
          steps={[
            {
              label: "AAPL Call Ask Price (buy at market)",
              formula: "$3.60 per share times 100 times 10 contracts",
              result: "$3,600 paid",
              highlight: false,
            },
            {
              label: "AAPL Call Bid Price (sell at market)",
              formula: "$3.40 per share times 100 times 10 contracts",
              result: "$3,400 received",
              highlight: false,
            },
            {
              label: "Round Trip Spread Cost",
              formula: "$3,600 minus $3,400",
              result: "$200 lost",
              highlight: true,
              color: "#ef4444",
            },
            {
              label: "At Mid Price Round Trip Cost",
              formula: "0 spread loss, enter and exit at $3.50",
              result: "$0 spread",
              highlight: true,
              color: "#22c55e",
            },
          ]}
          conclusion="Paying the spread twice on 10 AAPL contracts costs $200 before the stock moves at all. Mid price execution eliminates that loss entirely."
          accent={accent}
        />
      ),
    },

    // Scene 5 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <SvgLineChartScene
          heading="Round Trip Spread Cost as Percent of Premium"
          subheading="How spread width destroys premium value across different options"
          data={[
            { label: "$0.02 spread", value: 0.5 },
            { label: "$0.05 spread", value: 1.2 },
            { label: "$0.10 spread", value: 2.9 },
            { label: "$0.20 spread", value: 5.7 },
            { label: "$0.30 spread", value: 8.6 },
            { label: "$0.40 spread", value: 11.4 },
            { label: "$0.50 spread", value: 14.3 },
          ]}
          accent={accent}
          yLabel="Round Trip %"
          xLabel="Spread Width"
          highlightIdx={3}
          footnote="Above 10 percent round trip cost the option is not worth trading at market orders. Use limit orders at mid price exclusively."
        />
      ),
    },

    // Scene 6 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <BulletScene
          heading="Penny Pilot vs Nickel Pilot: The Two Markets"
          bullets={[
            "Penny pilot options trade in $0.01 increments: SPY, QQQ, AAPL, MSFT and 400 other liquid names",
            "Standard options trade in $0.05 increments: creates minimum $0.05 spreads on a $1.00 option",
            "Nickel minimum spread means 5 percent round trip cost on a $1.00 option before any move",
            "Always check if your option is in the penny pilot program before entering a position",
            "Penny pilot membership is not permanent: some names are added or removed each year",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 7 (45s)
    {
      durationInFrames: sec(45),
      render: () => (
        <MistakeHighlightScene
          heading="Market Orders on Options: An Expensive Habit"
          mistake={{
            label: "Using market orders when entering or exiting options",
            detail:
              "A market order on AAPL options executes at the ask when buying ($3.60) and at the bid when selling ($3.40). That is a guaranteed $0.20 per share loss on entry and exit combined.",
          }}
          correction={{
            label: "Always use limit orders priced at mid or one cent inside mid",
            detail:
              "Set your limit buy at $3.50 (mid). If not filled in 30 seconds, move up by $0.01 increments. You will almost always get mid price on liquid options with patience.",
          }}
          insight="A limit order at mid is not aggressive. Market makers will often fill at mid or better because they prefer any fill over holding inventory risk."
          accent={accent}
        />
      ),
    },

    // Scene 8 (60s)
    {
      durationInFrames: sec(60),
      render: () => (
        <WorkedExampleScene
          heading="Five Trades: Ask Price vs Mid Price Over One Month"
          company="Apple Inc"
          ticker="AAPL"
          trades={[
            {
              day: "Trade 1",
              event: "Bought at ask $3.60, sold at bid $3.90 (stock rose)",
              action: "Gross gain $0.30, spread cost $0.20, net $0.10 per share",
              pl: 100,
              cumPl: 100,
            },
            {
              day: "Trade 1 Mid",
              event: "Bought at mid $3.50, sold at mid $4.00 (same stock move)",
              action: "Full $0.50 gain captured with no spread cost",
              pl: 500,
              cumPl: 500,
            },
            {
              day: "Trade 2",
              event: "Asked in at $3.60, trade went flat, sold at bid $3.40",
              action: "Stock went nowhere but lost $0.20 to the spread",
              pl: -200,
              cumPl: -200,
            },
            {
              day: "Trade 2 Mid",
              event: "Entered at mid, stock flat, sold at mid",
              action: "No spread cost, breakeven trade preserves capital",
              pl: 0,
              cumPl: 0,
            },
            {
              day: "5 Trade Total",
              event: "Market order trader loses $200 extra per round trip",
              action: "Mid price trader keeps $200 more per trade on identical setups",
              pl: 200,
              cumPl: 200,
            },
          ]}
          accent={accent}
          subheading="Identical directional calls, different execution discipline"
        />
      ),
    },

    // Scene 9 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <StatsScene
          heading="Bid and Ask by the Numbers"
          stats={[
            { label: "SPY Typical Spread", value: "$0.01 to $0.05", color: "#22c55e" },
            { label: "AAPL Typical Spread", value: "$0.10 to $0.25", color: accent },
            { label: "Illiquid Option Spread", value: "$0.30 to $1.00", color: "#ef4444" },
            { label: "Max Acceptable Spread", value: "10% of Premium", color: "#f59e0b" },
          ]}
          accent={accent}
          footnote="During news events spreads can widen 3 to 5 times. Avoid market orders during the first 30 minutes of any major announcement."
        />
      ),
    },

    // Scene 10 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <CalculationScene
          heading="How to Estimate Mid Price Before Submitting"
          steps={[
            {
              label: "AAPL Call Bid",
              formula: "Current best bid in the options chain",
              result: "$3.40",
            },
            {
              label: "AAPL Call Ask",
              formula: "Current best ask in the options chain",
              result: "$3.60",
            },
            {
              label: "Mid Price",
              formula: "($3.40 + $3.60) divided by 2",
              result: "$3.50",
              highlight: true,
              color: accent,
            },
            {
              label: "Entry Limit Order",
              formula: "Submit buy limit at $3.50, adjust by $0.01 if not filled",
              result: "Save $0.10",
              highlight: false,
            },
          ]}
          conclusion="Mid price execution on a 10 contract trade saves $100 in spread cost versus buying at the ask. Over 20 trades per month that is $2,000 saved annually."
          accent={accent}
        />
      ),
    },

    // Scene 11 (35s)
    {
      durationInFrames: sec(35),
      render: () => (
        <BulletScene
          heading="Execution Checklist for Every Options Entry"
          bullets={[
            "Calculate mid price before submitting any order",
            "Check that spread is below 10 percent of premium or skip the trade",
            "Submit limit order at mid and wait up to 60 seconds before adjusting",
            "Move limit up by $0.01 increments, never jump to the full ask immediately",
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
          heading="The Spread Is a Controllable Cost"
          takeaways={[
            "Every market order on options hands money to the market maker for free",
            "Mid price limit orders eliminate spread cost and improve returns on every trade",
            "Spread as a percent of premium is the only cost metric that matters",
            "Penny pilot options keep spread costs below 1 percent for the most liquid names",
          ]}
          accent={accent}
          closingLine="Execution discipline adds up faster than picking better trades. Never use a market order on options."
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

// ── TapeSpeedLong ─────────────────────────────────────────────────────────────
// Lesson: tape-speed — "Reading Tape Speed and Order Flow"

export type TapeSpeedLongProps = {
  accent?: string;
};

export const TapeSpeedLong: React.FC<TapeSpeedLongProps> = ({
  accent = "#8b5cf6",
}) => {
  useVideoConfig();

  const scenes: SceneDef[] = [
    // Scene 1 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <TitleScene
          label="Tape Speed"
          title="Reading Tape Speed and Order Flow"
          subtitle="Decoding institutional intent from the time and sales feed"
          accent={accent}
        />
      ),
    },

    // Scene 2 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <BulletScene
          heading="Five Signals That Distinguish Institutional from Retail Flow"
          bullets={[
            "Size: prints above 10,000 shares in a single transaction are almost never retail",
            "Speed: institutional algos fire hundreds of smaller prints per second in rapid bursts",
            "Price location: buying at the ask aggressively signals urgency, not casual interest",
            "Repeat prints at the same price: accumulation or distribution at a defended level",
            "Dark to lit crossover: dark pool activity confirmed on the visible tape signals intent to move",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 3 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <ComparisonTableScene
          heading="Retail Order vs Institutional Order: 4 Dimensions"
          columns={["Dimension", "Retail Order", "Institutional Order"]}
          rows={[
            { cells: ["Size", "100 to 500 shares", "10,000 to 500,000 shares"], winner: 2 },
            { cells: ["Speed", "Single print, manual entry", "Burst of 50 to 500 prints per second"] },
            { cells: ["Venue", "Directly to exchange lit market", "Dark pool first, lit market to confirm"] },
            { cells: ["Price Impact", "No visible market impact", "Moves the bid or ask on contact"], winner: 2 },
          ]}
          accent={accent}
          subheading="Institutional flow leaves a fingerprint even when it is designed to hide"
        />
      ),
    },

    // Scene 4 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <SetupScene
          heading="5 Tape Signals That Actually Matter"
          items={[
            { label: "Signal 1", value: "Large Single Print", color: accent },
            { label: "Signal 2", value: "Repeat Same Price", color: "#22c55e" },
            { label: "Signal 3", value: "Sweep Across Levels", color: "#f59e0b" },
            { label: "Signal 4", value: "Time Cluster", color: "#3b82f6" },
            { label: "Signal 5", value: "Pre Market Activity", color: "#ef4444" },
          ]}
          accent={accent}
          description="Each signal has a different implication. Context determines which interpretation applies."
        />
      ),
    },

    // Scene 5 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <BulletScene
          heading="Level 2 Depth of Market and What It Shows"
          bullets={[
            "Level 2 shows the full order book: all bids and asks stacked by price and size",
            "Large bid walls can signal institutional support or a spoof to attract sellers",
            "Disappearing bid walls just before a downtick signal spoofing not real support",
            "Thin book with few orders at any level means the stock can move fast on any catalyst",
            "Real institutional flow does not advertise itself in the open book it uses dark pools",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 6 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <SvgLineChartScene
          heading="SPY Tape Activity Pattern on a CPI Morning"
          subheading="Volume prints by 5 minute interval showing institutional burst then retail chase"
          data={[
            { label: "8:00am", value: 120 },
            { label: "8:30am", value: 890 },
            { label: "9:00am", value: 1450 },
            { label: "9:30am", value: 3200 },
            { label: "9:35am", value: 5800 },
            { label: "9:40am", value: 2400 },
            { label: "9:45am", value: 980 },
            { label: "10:00am", value: 620 },
          ]}
          accent={accent}
          yLabel="Print Volume"
          xLabel="Time"
          highlightIdx={5}
          footnote="The spike at open is institutional algo flow. The drop by 9:45 is retail chasing the move after institutions have already repositioned."
        />
      ),
    },

    // Scene 7 (60s)
    {
      durationInFrames: sec(60),
      render: () => (
        <WorkedExampleScene
          heading="SPY Tape Read on a CPI Morning"
          company="SPDR S and P 500 ETF"
          ticker="SPY"
          trades={[
            {
              day: "8:29am",
              event: "CPI data prints above expectations",
              action: "Watch tape, no action yet, wait for opening reaction",
              pl: 0,
              cumPl: 0,
            },
            {
              day: "9:31am",
              event: "SPY opens with 500,000 share institutional sell sweep",
              action: "Tape shows asks hit aggressively, signal: institutional distribution",
              pl: 0,
              cumPl: 0,
            },
            {
              day: "9:33am",
              event: "SPY drops $2, tape slows to retail prints only",
              action: "Institutional selling done, retail panic starts",
              pl: -200,
              cumPl: -200,
            },
            {
              day: "9:40am",
              event: "Dark pool prints appear on tape at prior support $498",
              action: "Buy SPY puts as bounce trade fades, institutions not buying yet",
              pl: 350,
              cumPl: 150,
            },
            {
              day: "10:00am",
              event: "Tape confirms bid wall at $496, institutional accumulation starting",
              action: "Close puts at 35 percent gain, flip long into confirmed support",
              pl: 480,
              cumPl: 630,
            },
          ]}
          accent={accent}
          subheading="Reading flow direction before committing capital"
        />
      ),
    },

    // Scene 8 (45s)
    {
      durationInFrames: sec(45),
      render: () => (
        <MistakeHighlightScene
          heading="Every Large Print Is Not a Directional Signal"
          mistake={{
            label: "Assuming every big print means a directional bet",
            detail:
              "A 200,000 share SPY print could be a hedge against an existing equity portfolio, a rebalance for a pension fund, or an arbitrage trade. None of those are directional signals.",
          }}
          correction={{
            label: "Context and price action confirm flow direction, not size alone",
            detail:
              "A large print at the ask, followed by the stock moving up, followed by more large prints, is a directional signal. Size alone without price confirmation is just noise.",
          }}
          insight="Read the response to the print, not just the print itself. Stocks that absorb large sells and hold price are showing institutional buying. That is the real signal."
          accent={accent}
        />
      ),
    },

    // Scene 9 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <StatsScene
          heading="Tape Reading Quick Reference"
          stats={[
            { label: "Institutional Print Threshold", value: "10,000 shares", color: accent },
            { label: "Dark Pool Avg Daily Volume", value: "35 to 40%", color: "#3b82f6" },
            { label: "Retail Order Avg Size", value: "100 to 500 shares", color: "#94a3b8" },
            { label: "Level 2 Refresh Rate", value: "250ms or faster", color: "#22c55e" },
          ]}
          accent={accent}
          footnote="Dark pool prints that appear on the lit tape represent already completed institutional transactions, not pending orders"
        />
      ),
    },

    // Scene 10 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <BulletScene
          heading="Uptick vs Downtick Patterns and What They Signal"
          bullets={[
            "Uptick volume: shares trading at a price above the previous transaction, buying pressure",
            "Downtick volume: shares trading below the previous transaction, selling pressure",
            "Sustained uptick prints with rising price confirms institutional accumulation",
            "High downtick volume with price holding flat signals strong underlying buy support",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 11 (35s)
    {
      durationInFrames: sec(35),
      render: () => (
        <BulletScene
          heading="Tape Reading Rules Before Any Entry"
          bullets={[
            "Identify whether large prints are hitting bid or lifting ask before interpreting direction",
            "Wait for at least three confirming prints before reading a tape signal as real",
            "Compare tape speed to the prior 5 minute average to detect acceleration",
            "Never chase a print already 2 percent away from your planned entry price",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 12 (35s)
    {
      durationInFrames: sec(35),
      render: () => (
        <SummaryScene
          heading="The Tape Shows What Price Cannot"
          takeaways={[
            "Institutional flow leaves identifiable fingerprints in size, speed and price location",
            "Dark pool prints on the lit tape are completed trades, not previews of future orders",
            "Context determines meaning: hedges, rebalances and arb are not directional bets",
            "Three confirming signals beat one large print when building a tape read thesis",
          ]}
          accent={accent}
          closingLine="The tape never lies but it does not speak plainly. Learn to read context and you read intent."
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

// ── EventsEarningsLong ────────────────────────────────────────────────────────
// Lesson: events-earnings — "The Earnings Gap Playbook"

export type EventsEarningsLongProps = {
  accent?: string;
};

export const EventsEarningsLong: React.FC<EventsEarningsLongProps> = ({
  accent = "#22c55e",
}) => {
  useVideoConfig();

  const scenes: SceneDef[] = [
    // Scene 1 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <TitleScene
          label="Events and Earnings"
          title="The Earnings Gap Playbook"
          subtitle="IV crush mechanics, expected move and strategies that survive reporting day"
          accent={accent}
        />
      ),
    },

    // Scene 2 (25s)
    {
      durationInFrames: sec(25),
      render: () => (
        <BulletScene
          heading="Why Options Behave Differently Around Earnings"
          bullets={[
            "Market makers raise IV before earnings to charge more premium for the unknown outcome",
            "After the print, uncertainty resolves instantly and IV drops sharply in an IV crush",
            "A correct directional call can still lose money if IV crush destroys more than the stock move gains",
            "The expected move from the chain is the market collective forecast of the earnings gap size",
            "Strategies that sell premium before earnings benefit from the IV crush that follows",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 3 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <SvgLineChartScene
          heading="NVDA Historical Earnings Moves: 8 Quarters"
          subheading="Percentage move in stock price the day after each earnings report"
          data={[
            { label: "Q1 2023", value: 12 },
            { label: "Q2 2023", value: 16 },
            { label: "Q3 2023", value: 9 },
            { label: "Q4 2023", value: 24 },
            { label: "Q1 2024", value: 5 },
            { label: "Q2 2024", value: 15 },
            { label: "Q3 2024", value: 8 },
            { label: "Q4 2024", value: 18 },
          ]}
          accent={accent}
          yLabel="Move %"
          xLabel="Quarter"
          highlightIdx={3}
          footnote="Average move of 13.4 percent. The options chain expected move averaged 11 percent across these quarters, slightly underpricing the actual moves."
        />
      ),
    },

    // Scene 4 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <CalculationScene
          heading="Expected Move Calculation for NVDA Earnings"
          steps={[
            {
              label: "NVDA ATM Call at $500 Strike",
              formula: "30 day call with 2 days to earnings",
              result: "$12.00",
              highlight: false,
            },
            {
              label: "NVDA ATM Put at $500 Strike",
              formula: "Same expiry as the call above",
              result: "$11.00",
              highlight: false,
            },
            {
              label: "Raw Straddle Price",
              formula: "$12.00 + $11.00",
              result: "$23.00",
              highlight: false,
            },
            {
              label: "Expected Move (0.85 adjustment)",
              formula: "$23.00 times 0.85",
              result: "$19.55",
              highlight: true,
              color: accent,
            },
          ]}
          conclusion="The chain predicts NVDA will move plus or minus $19.55, putting the expected range at $480 to $520 around the $500 current price."
          accent={accent}
        />
      ),
    },

    // Scene 5 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <PayoffDiagramScene
          heading="Long Straddle at NVDA $500 Before Earnings"
          subheading="Buy $500 call at $12 and $500 put at $11, total premium $23"
          legs={[
            { type: "long-call", strike: 500, premium: 12 },
            { type: "long-put", strike: 500, premium: 11 },
          ]}
          priceMin={450}
          priceMax={550}
          currentPrice={500}
          accent={accent}
          footnote="Breakeven at $477 on the downside and $523 on the upside. Stock must move more than 4.6 percent for profitability."
        />
      ),
    },

    // Scene 6 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <ComparisonTableScene
          heading="Three Earnings Strategies: Straddle vs Spread vs Directional"
          columns={["Strategy", "Max Profit", "Max Loss", "IV Crush Risk"]}
          rows={[
            { cells: ["Long Straddle", "Unlimited", "$2,300 (100%)", "High, destroys both legs"] },
            { cells: ["Short Iron Condor", "$500 credit", "$1,500", "Low, benefits from crush"], winner: 3 },
            { cells: ["Long Call Only", "Unlimited", "$1,200", "High, destroys premium even if right"] },
            { cells: ["Bull Call Spread", "$800", "$700", "Moderate, spread offsets some crush"] },
          ]}
          accent={accent}
          subheading="Short premium strategies consistently outperform long premium around earnings"
        />
      ),
    },

    // Scene 7 (45s)
    {
      durationInFrames: sec(45),
      render: () => (
        <MistakeHighlightScene
          heading="Buying Options Right Before Earnings"
          mistake={{
            label: "Entering long straddles or directional calls the day before earnings",
            detail:
              "NVDA IV at 80 percent before earnings means you pay maximum premium. Even if the stock moves 10 percent the right way, IV crush from 80 to 42 percent destroys half or more of the gain.",
          }}
          correction={{
            label: "Buy options 2 weeks before earnings or sell premium instead",
            detail:
              "Entering a long straddle 14 days before earnings captures IV expansion as earnings approach. Alternatively sell a strangle or iron condor to profit from the IV crush after the print.",
          }}
          insight="IV crush is not optional. After every earnings report IV drops back to normal levels. Strategies that own premium must overcome this headwind. Strategies that sell premium ride it."
          accent={accent}
        />
      ),
    },

    // Scene 8 (60s)
    {
      durationInFrames: sec(60),
      render: () => (
        <WorkedExampleScene
          heading="NVDA Earnings Trade: IV Build to IV Crush"
          company="Nvidia Corp"
          ticker="NVDA"
          trades={[
            {
              day: "Day minus 14",
              event: "NVDA at $500, IV at 45 percent, earnings in 14 days",
              action: "Buy 1 ATM straddle at $500 strike for $18.50 total cost",
              pl: -1850,
              cumPl: -1850,
            },
            {
              day: "Day minus 7",
              event: "IV rises to 62 percent, stock flat at $502",
              action: "Straddle worth $21.80 due to IV expansion alone",
              pl: 330,
              cumPl: -1520,
            },
            {
              day: "Day minus 1",
              event: "IV peaks at 80 percent, straddle worth $26.00",
              action: "Decision: sell before earnings to lock in IV expansion gain",
              pl: 750,
              cumPl: -770,
            },
            {
              day: "Earnings Day",
              event: "NVDA beats estimates, stock gaps to $524 (+4.8%)",
              action: "IV crushes from 80 to 42 percent, straddle worth $23.50",
              pl: -250,
              cumPl: -1020,
            },
            {
              day: "Analysis",
              event: "Selling before earnings was better than holding through",
              action: "Pre earnings exit at $26.00 versus post crush at $23.50",
              pl: 250,
              cumPl: 750,
            },
          ]}
          accent={accent}
          subheading="IV expansion trade entered 14 days before earnings"
        />
      ),
    },

    // Scene 9 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <StatsScene
          heading="Earnings Options Statistics"
          stats={[
            { label: "IV Crush Typical Range", value: "30 to 60%", color: "#ef4444" },
            { label: "NVDA Avg Earnings Move", value: "13.4%", color: accent },
            { label: "Straddle Win Rate vs Expected Move", value: "42%", color: "#f59e0b" },
            { label: "Best Entry Window", value: "10 to 14 DTE", color: "#3b82f6" },
          ]}
          accent={accent}
          footnote="Straddles win only 42 percent of the time because the expected move is already priced in. Selling premium wins 58 percent of the time in back tests."
        />
      ),
    },

    // Scene 10 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <BulletScene
          heading="Gap Fill Probability After Earnings"
          bullets={[
            "A gap fill means the stock returns to its pre earnings close price within a defined period",
            "Earnings gaps of less than 5 percent fill within 10 days roughly 65 percent of the time",
            "Gaps above 10 percent fill within 10 days only 28 percent of the time",
            "Gap fill trades use short dated spreads in the direction opposite the gap after the crush settles",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 11 (35s)
    {
      durationInFrames: sec(35),
      render: () => (
        <BulletScene
          heading="Earnings Trade Checklist"
          bullets={[
            "Check IV rank: above 70 percent favors selling premium, below 30 percent favors buying",
            "Calculate expected move from ATM straddle price before choosing any strategy",
            "Never buy options the day before earnings unless you have a defined edge on the move",
            "Set your exit at 25 percent profit for short spreads immediately after the print",
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
          heading="Earnings Are a Volatility Event First"
          takeaways={[
            "IV builds before earnings and crushes after regardless of the stock move direction",
            "Expected move from the chain prices in what the market already knows",
            "Selling premium around earnings captures IV crush as structural income",
            "Buying options before earnings works only when entered 10 to 14 days before the print",
          ]}
          accent={accent}
          closingLine="Understand IV crush and you will never be surprised by a correct directional call that still loses money."
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

// ── MacroVolLong ──────────────────────────────────────────────────────────────
// Lesson: macro-vol — "When Macro Prints Move Markets"

export type MacroVolLongProps = {
  accent?: string;
};

export const MacroVolLong: React.FC<MacroVolLongProps> = ({
  accent = "#14b8a6",
}) => {
  useVideoConfig();

  const scenes: SceneDef[] = [
    // Scene 1 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <TitleScene
          label="Macro and Volatility"
          title="When Macro Prints Move Markets"
          subtitle="VIX cycles, FOMC positioning and managing portfolio vega around macro events"
          accent={accent}
        />
      ),
    },

    // Scene 2 (25s)
    {
      durationInFrames: sec(25),
      render: () => (
        <BulletScene
          heading="VIX: The Fear Gauge Explained"
          bullets={[
            "VIX measures the implied volatility of SPX options over the next 30 days",
            "VIX above 30 signals extreme fear and elevated options premiums across the market",
            "VIX below 15 signals complacency and compressed premiums, ideal for buying protection cheaply",
            "VIX does not predict direction, only the expected magnitude of future price swings",
            "A spike from 15 to 30 roughly doubles the cost of at the money SPX options",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 3 (60s)
    {
      durationInFrames: sec(60),
      render: () => (
        <SvgLineChartScene
          heading="VIX at Five Key Historical Events"
          subheading="Peak intraday VIX readings during major market dislocations"
          data={[
            { label: "Lehman 2008", value: 80 },
            { label: "Covid March 2020", value: 82 },
            { label: "Brexit June 2016", value: 26 },
            { label: "FOMC Dec 2022", value: 24 },
            { label: "SVB March 2023", value: 28 },
          ]}
          accent={accent}
          yLabel="VIX Level"
          xLabel="Event"
          highlightIdx={1}
          footnote="Normal VIX range is 12 to 20. Events above 30 signal systemic stress. Above 40 is crisis territory where spreads widen and liquidity disappears."
        />
      ),
    },

    // Scene 4 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <ComparisonTableScene
          heading="Five Macro Event Types: VIX Impact and Best Strategy"
          columns={["Event", "Typical VIX Impact", "Duration", "Best Strategy"]}
          rows={[
            { cells: ["FOMC Decision", "Plus 2 to 8 VIX points before", "1 to 2 days", "Sell short dated straddle after"] },
            { cells: ["CPI Print", "Plus 1 to 5 VIX points before", "4 to 8 hours", "Wait for open, trade the reaction"] },
            { cells: ["Payrolls", "Plus 1 to 4 VIX points before", "4 to 6 hours", "Sell SPY spreads day before"] },
            { cells: ["Geopolitical Shock", "Plus 10 to 40 VIX points", "3 to 10 days", "Buy puts before event if possible"] },
            { cells: ["Earnings Season", "Gradual 3 to 8 VIX points", "3 to 4 weeks", "Sell individual name spreads"] },
          ]}
          accent={accent}
          subheading="Scheduled events allow positioning; unscheduled shocks require reactive management"
        />
      ),
    },

    // Scene 5 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <CalculationScene
          heading="Portfolio Vega and a 10 VIX Point Spike"
          steps={[
            {
              label: "Retail Portfolio: 5 Long Calls at Vega 0.08 Each",
              formula: "5 contracts times 100 times $0.08 vega",
              result: "$40 per VIX point",
              highlight: false,
            },
            {
              label: "VIX Spike of 10 Points",
              formula: "$40 per VIX point times 10 points",
              result: "+$400 vega gain",
              highlight: true,
              color: "#22c55e",
            },
            {
              label: "Same Portfolio: 5 Short Puts at Vega 0.10 Each",
              formula: "5 contracts times 100 times $0.10 vega",
              result: "$50 per VIX point",
              highlight: false,
            },
            {
              label: "VIX Spike of 10 Points for Short Vega",
              formula: "$50 per VIX point times 10 points",
              result: "minus $500 vega loss",
              highlight: true,
              color: "#ef4444",
            },
          ]}
          conclusion="A 10 VIX point spike can add or remove hundreds of dollars from a position before the stock moves at all. Know your vega before every macro event."
          accent={accent}
        />
      ),
    },

    // Scene 6 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <BulletScene
          heading="VIX Term Structure: Contango vs Backwardation"
          bullets={[
            "Contango: near term VIX futures cheaper than far dated futures, normal market state",
            "Backwardation: near term VIX futures more expensive than far dated, signals acute fear",
            "Backwardation tells you traders expect volatility to resolve quickly after a shock",
            "Calendar spreads on VIX profit from the return to contango after backwardation spikes",
            "VIX ETPs that hold futures decay in contango, making them poor long term holds",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 7 (60s)
    {
      durationInFrames: sec(60),
      render: () => (
        <WorkedExampleScene
          heading="Navigating FOMC Week with Options Positions"
          company="Federal Reserve Event"
          ticker="SPX"
          trades={[
            {
              day: "Monday",
              event: "FOMC meeting starts, VIX rises from 16 to 18",
              action: "Reduce long vega exposure, close any naked long calls",
              pl: 0,
              cumPl: 0,
            },
            {
              day: "Tuesday",
              event: "VIX reaches 20, SPX options premiums elevated 20 percent",
              action: "Sell a short dated SPX iron condor for elevated credit",
              pl: 800,
              cumPl: 800,
            },
            {
              day: "Wednesday 2pm",
              event: "Fed holds rates, no surprise in statement",
              action: "VIX crushes from 20 to 14 in 30 minutes",
              pl: 600,
              cumPl: 1400,
            },
            {
              day: "Wednesday 4pm",
              event: "Iron condor at 60 percent of max profit",
              action: "Close condor early at 60 percent target, book profit",
              pl: 480,
              cumPl: 1880,
            },
            {
              day: "Thursday",
              event: "VIX settles at 13, normal market resumes",
              action: "Re enter longer dated positions at reduced premium cost",
              pl: 0,
              cumPl: 1880,
            },
          ]}
          accent={accent}
          subheading="Selling premium into elevated FOMC vol and capturing the crush"
        />
      ),
    },

    // Scene 8 (45s)
    {
      durationInFrames: sec(45),
      render: () => (
        <MistakeHighlightScene
          heading="Holding Naked Long Options Into FOMC"
          mistake={{
            label: "Buying naked calls or puts expecting a big move from the Fed",
            detail:
              "Even if the Fed surprises the market, IV crush after the announcement can destroy 30 to 50 percent of the premium on a naked long option within minutes of the decision.",
          }}
          correction={{
            label: "Use spreads to reduce vega before every scheduled macro event",
            detail:
              "A vertical spread costs less and has lower vega exposure than a naked option. Selling the further strike caps your vega and reduces the IV crush impact significantly.",
          }}
          insight="Macro events are scheduled. Preparation is not optional. Reduce vega before the event so you are trading the direction, not the volatility."
          accent={accent}
        />
      ),
    },

    // Scene 9 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <StatsScene
          heading="Macro Vol Key Reference Numbers"
          stats={[
            { label: "Normal VIX Range", value: "12 to 20", color: "#22c55e" },
            { label: "Elevated VIX Range", value: "20 to 30", color: "#f59e0b" },
            { label: "Crisis VIX Range", value: "30 and above", color: "#ef4444" },
            { label: "Avg FOMC VIX Crush", value: "2 to 6 points", color: accent },
          ]}
          accent={accent}
          footnote="VIX above 30 historically coincides with SPX forward returns that are above average over the following 12 months"
        />
      ),
    },

    // Scene 10 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <BulletScene
          heading="FOMC Vol Cycle: Four Phases to Trade"
          bullets={[
            "Phase 1 (2 weeks before): vol quietly builds, premiums start rising, good time to sell spreads",
            "Phase 2 (3 days before): vol accelerates, sell any remaining naked long options for elevated exit",
            "Phase 3 (event day): maximum vol, sell spreads or iron condors to capture the crush",
            "Phase 4 (day after): vol crushes, close short positions at 50 percent profit target and reset",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 11 (35s)
    {
      durationInFrames: sec(35),
      render: () => (
        <RealWorldExampleScene
          heading="FOMC December 2022: Playing the VIX Cycle"
          company="Federal Open Market Committee Event"
          scenario="Fed signals potential rate pivot. VIX at 24 heading into decision. Short SPX iron condor 3 days before."
          setupItems={[
            { label: "Entry VIX", value: "24", color: "#ef4444" },
            { label: "Credit Collected", value: "$620", color: accent },
            { label: "VIX Post Event", value: "18", color: "#22c55e" },
            { label: "Profit at Close", value: "$430", color: "#22c55e" },
          ]}
          outcome="+$430 in 4 days"
          outcomeDetail="VIX crushed 6 points post decision. Iron condor captured 70 percent of max profit through the vol event without any directional bet."
          outcomeColor="#22c55e"
          accent={accent}
        />
      ),
    },

    // Scene 12 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <SummaryScene
          heading="Macro Moves Vol Before It Moves Price"
          takeaways={[
            "VIX builds before every scheduled macro event and crushes after resolution",
            "Short vega strategies outperform long vega strategies around FOMC and CPI",
            "Know your portfolio vega before every macro print and reduce it if it is too large",
            "VIX backwardation signals acute fear. Contango is the normal profitable state for sellers.",
          ]}
          accent={accent}
          closingLine="The macro calendar is public information. Trade the vol cycle it creates before the event happens."
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

// ── RiskSizerLong ─────────────────────────────────────────────────────────────
// Lesson: risk-sizer — "Sizing Positions With Precision"

export type RiskSizerLongProps = {
  accent?: string;
};

export const RiskSizerLong: React.FC<RiskSizerLongProps> = ({
  accent = "#f59e0b",
}) => {
  useVideoConfig();

  const scenes: SceneDef[] = [
    // Scene 1 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <TitleScene
          label="Position Sizing"
          title="Sizing Positions With Precision"
          subtitle="The 1 to 2 percent rule, Kelly criterion and portfolio heat management"
          accent={accent}
        />
      ),
    },

    // Scene 2 (25s)
    {
      durationInFrames: sec(25),
      render: () => (
        <BulletScene
          heading="The Core Principle: Risk Dollars Not Option Dollars"
          bullets={[
            "Position sizing starts with your maximum dollar loss, not the premium cost",
            "The 1 to 2 percent rule: never risk more than 1 to 2 percent of your account on a single trade",
            "Max loss equals the total premium paid for long options or the max loss on a defined risk spread",
            "Contract count follows from the max loss calculation, not from how the trade looks",
            "Consistency in sizing protects the account when multiple trades lose simultaneously",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 3 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <CalculationScene
          heading="$50,000 Account: Sizing an AAPL Call Trade"
          steps={[
            {
              label: "Maximum Risk at 1 Percent",
              formula: "$50,000 account times 1 percent",
              result: "$500 max loss",
              highlight: false,
            },
            {
              label: "AAPL $185 Call at $3.50 Per Contract",
              formula: "$3.50 times 100 shares per contract",
              result: "$350 per contract",
              highlight: false,
            },
            {
              label: "Contracts to Fill $500 Risk Budget",
              formula: "$500 divided by $350 = 1.4 contracts",
              result: "1 contract",
              highlight: false,
            },
            {
              label: "Actual Risk with 1 Contract",
              formula: "1 contract times $350",
              result: "$350 used",
              highlight: true,
              color: "#22c55e",
            },
          ]}
          conclusion="The $500 risk budget supports 1 contract cleanly with $150 of buffer. Adding a second contract would risk $700, exceeding the 1 percent rule by 40 percent."
          accent={accent}
        />
      ),
    },

    // Scene 4 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <ComparisonTableScene
          heading="Risk Budget by Account Size and Risk Tolerance"
          columns={["Account Size", "1% Max Loss", "2% Max Loss", "3% Max Loss"]}
          rows={[
            { cells: ["$10,000", "$100 per trade", "$200 per trade", "$300 per trade"] },
            { cells: ["$25,000", "$250 per trade", "$500 per trade", "$750 per trade"] },
            { cells: ["$50,000", "$500 per trade", "$1,000 per trade", "$1,500 per trade"], highlight: true },
            { cells: ["$100,000", "$1,000 per trade", "$2,000 per trade", "$3,000 per trade"] },
            { cells: ["$250,000", "$2,500 per trade", "$5,000 per trade", "$7,500 per trade"] },
          ]}
          accent={accent}
          subheading="Start at 1 percent. Only move to 2 percent after 50 or more profitable trades prove your edge"
        />
      ),
    },

    // Scene 5 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <SvgLineChartScene
          heading="Account Value: Disciplined Sizer vs Aggressive Sizer Over 20 Trades"
          subheading="$50,000 starting balance, 10 winning trades and 10 losing trades in random order"
          data={[
            { label: "Start", value: 50000 },
            { label: "T5", value: 51200 },
            { label: "T8", value: 49800 },
            { label: "T10", value: 52400 },
            { label: "T13", value: 50100 },
            { label: "T15", value: 53600 },
            { label: "T18", value: 52200 },
            { label: "T20", value: 55800 },
          ]}
          accent={accent}
          yLabel="Account ($)"
          xLabel="Trade Number"
          highlightIdx={7}
          footnote="Aggressive 5 percent sizer on the same trades would have dropped below $35,000 during the losing streak. The 1 percent sizer never fell below $47,000."
        />
      ),
    },

    // Scene 6 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <BulletScene
          heading="Kelly Criterion Simplified for Options Traders"
          bullets={[
            "Kelly formula: edge divided by odds tells you the optimal fraction of capital to risk",
            "A strategy with 55 percent win rate and 1 to 1 win and loss ratio suggests 10 percent Kelly sizing",
            "Full Kelly is almost always too aggressive, use half Kelly in practice for drawdown protection",
            "Kelly assumes your edge is real and constant, reduce sizing when you are in a drawdown",
            "For most retail traders, 1 to 2 percent fixed fractional sizing is safer than Kelly in live trading",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 7 (45s)
    {
      durationInFrames: sec(45),
      render: () => (
        <MistakeHighlightScene
          heading="Sizing Based on How Cheap the Option Looks"
          mistake={{
            label: "Buying more contracts because the option premium is small",
            detail:
              "A $0.50 option seems cheap so you buy 20 contracts. That is $1,000 of premium on a $50,000 account, representing 2 percent risk before commissions. Still violates the 1 percent rule.",
          }}
          correction={{
            label: "Calculate max loss in dollars before deciding on contract count",
            detail:
              "20 contracts at $0.50 premium each cost $1,000 total. That is 2 percent of a $50,000 account. The rule is percentage of account, not whether the option feels cheap.",
          }}
          insight="Cheap options seduce traders into over sizing. The 1 percent rule applies in dollar terms always. Premium level is irrelevant to position sizing math."
          accent={accent}
        />
      ),
    },

    // Scene 8 (60s)
    {
      durationInFrames: sec(60),
      render: () => (
        <WorkedExampleScene
          heading="5 Consecutive Trades: Disciplined vs Undisciplined Sizing"
          company="Mixed Positions"
          ticker="PORTFOLIO"
          trades={[
            {
              day: "Trade 1",
              event: "AAPL call, disciplined trader risked $500 (1%), winner",
              action: "Disciplined: $350 profit. Undisciplined risked $2,500 (5%), profit $1,750",
              pl: 350,
              cumPl: 350,
            },
            {
              day: "Trade 2",
              event: "SPY put, both traders take a loss on this trade",
              action: "Disciplined: lost $480. Undisciplined: lost $2,400",
              pl: -480,
              cumPl: -130,
            },
            {
              day: "Trade 3",
              event: "NVDA call, another winner for both",
              action: "Disciplined: $420 profit. Undisciplined: $2,100 profit",
              pl: 420,
              cumPl: 290,
            },
            {
              day: "Trade 4",
              event: "QQQ spread, full loss for both traders",
              action: "Disciplined: lost $500. Undisciplined: lost $2,500",
              pl: -500,
              cumPl: -210,
            },
            {
              day: "Trade 5",
              event: "MSFT call, winner closes the series",
              action: "Disciplined: $380 profit, at $80 net. Undisciplined at $80 net but down $9,000 at worst point",
              pl: 380,
              cumPl: 170,
            },
          ]}
          accent={accent}
          subheading="Same trades, same outcomes, dramatically different drawdown experience"
        />
      ),
    },

    // Scene 9 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <StatsScene
          heading="Position Sizing Key Numbers"
          stats={[
            { label: "Starting Risk Rule", value: "1% per trade", color: accent },
            { label: "Max Portfolio Heat", value: "5 to 6% at risk", color: "#ef4444" },
            { label: "Correlation Buffer", value: "3 trades per sector", color: "#3b82f6" },
            { label: "Drawdown Trigger", value: "5% reduce size 50%", color: "#22c55e" },
          ]}
          accent={accent}
          footnote="Portfolio heat is the sum of all current maximum losses. Never let total portfolio heat exceed 6 percent of account value at any one time."
        />
      ),
    },

    // Scene 10 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <BulletScene
          heading="Correlation and Portfolio Heat Management"
          bullets={[
            "Correlation risk: holding three bullish tech calls means one sector downturn hits all three",
            "Limit to two or three positions in the same sector to reduce correlated loss events",
            "Portfolio heat is total current max loss across all open positions, track it daily",
            "When heat exceeds 6 percent close the oldest or most correlated position first",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 11 (35s)
    {
      durationInFrames: sec(35),
      render: () => (
        <CalculationScene
          heading="Sizing a Spread Trade to Exactly $500 Max Loss"
          steps={[
            {
              label: "AAPL Bull Call Spread: Buy $185 Call, Sell $190 Call",
              formula: "Max loss = premium paid minus credit received",
              result: "$2.40 per share",
              highlight: false,
            },
            {
              label: "Max Loss Per Contract",
              formula: "$2.40 times 100 shares",
              result: "$240 per contract",
              highlight: false,
            },
            {
              label: "Contracts for $500 Max Loss",
              formula: "$500 divided by $240",
              result: "2 contracts",
              highlight: true,
              color: accent,
            },
          ]}
          conclusion="Two contracts on this spread risk exactly $480 total, staying within the $500 budget. This is position sizing done correctly."
          accent={accent}
        />
      ),
    },

    // Scene 12 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <SummaryScene
          heading="Sizing Is the Most Underrated Trading Skill"
          takeaways={[
            "The 1 percent rule limits any single trade loss to 1 percent of account regardless of option price",
            "Max loss calculation always comes before contract count, not after",
            "Portfolio heat is the sum of all open max losses and should never exceed 6 percent",
            "Consistent small sizing compounds over time. Inconsistent large sizing destroys accounts.",
          ]}
          accent={accent}
          closingLine="You control nothing about the market and everything about your position size. Size correctly on every trade without exception."
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

// ── ExitPlaybookLong ──────────────────────────────────────────────────────────
// Lesson: exit-playbook — "When and How to Exit Every Trade"

export type ExitPlaybookLongProps = {
  accent?: string;
};

export const ExitPlaybookLong: React.FC<ExitPlaybookLongProps> = ({
  accent = "#ec4899",
}) => {
  useVideoConfig();

  const scenes: SceneDef[] = [
    // Scene 1 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <TitleScene
          label="Exit Playbook"
          title="When and How to Exit Every Trade"
          subtitle="Profit targets, stop losses, time stops and rolling mechanics for every scenario"
          accent={accent}
        />
      ),
    },

    // Scene 2 (25s)
    {
      durationInFrames: sec(25),
      render: () => (
        <BulletScene
          heading="The Four Exit Rules That Apply to Every Trade"
          bullets={[
            "Profit target for short options: close at 50 percent of maximum profit, do not wait for expiry",
            "Profit target for long options: close at 100 percent gain or when directional thesis is proven",
            "Stop loss rule: close any trade that reaches 2 times the original credit received as a loss",
            "Time stop: any short options position at 21 DTE should be evaluated for early exit regardless of P and L",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 3 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <ComparisonTableScene
          heading="Four Exit Scenarios and the Action for Each"
          columns={["Scenario", "Trigger", "Action", "Reason"]}
          rows={[
            { cells: ["Profit Target Hit", "50% of max profit for short", "Close immediately, take the win", "Better risk adjusted return than holding"], winner: 3 },
            { cells: ["Stop Loss Hit", "Loss equals 2x credit received", "Close, accept defined loss", "Prevents catastrophic outlier loss"] },
            { cells: ["Time Stop", "21 DTE remaining on short", "Evaluate and often close or roll", "Gamma risk accelerates near expiry"] },
            { cells: ["Expiry Day", "Zero DTE remaining", "Close or let expire worthless", "Assignment risk exists on in the money options"] },
          ]}
          accent={accent}
          subheading="Every trade needs an exit plan before entry, not after the position moves"
        />
      ),
    },

    // Scene 4 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <BulletScene
          heading="Why 50 Percent Target Beats Holding to Expiry"
          bullets={[
            "Closing at 50 percent max profit frees up buying power for the next trade",
            "The last 50 percent of profit takes much longer to earn than the first 50 percent",
            "Holding through expiry exposes the position to gamma acceleration and assignment risk",
            "Studies of iron condors show closing at 50 percent improves annual returns by 15 to 20 percent",
            "Time saved by early close multiplied by more trades per year compounds the edge significantly",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 5 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <SvgLineChartScene
          heading="Win Rate vs Average Profit: With and Without 50 Percent Target Rule"
          subheading="Iron condor performance simulation over 100 trades"
          data={[
            { label: "No Target", value: 68 },
            { label: "75% Target", value: 74 },
            { label: "50% Target", value: 82 },
            { label: "25% Target", value: 87 },
            { label: "10% Target", value: 92 },
          ]}
          accent={accent}
          yLabel="Win Rate %"
          xLabel="Profit Target Rule"
          highlightIdx={2}
          footnote="50 percent target rule gives 82 percent win rate. Holding to expiry gives only 68 percent win rate because more trades get tested by late moves."
        />
      ),
    },

    // Scene 6 (60s)
    {
      durationInFrames: sec(60),
      render: () => (
        <WorkedExampleScene
          heading="AAPL Iron Condor: Three Outcome Scenarios"
          company="Apple Inc"
          ticker="AAPL"
          trades={[
            {
              day: "Entry",
              event: "AAPL at $185, sell $175 put and $195 call, buy $170 put and $200 call",
              action: "Collect $5.00 credit per share, max profit $500 per contract",
              pl: 500,
              cumPl: 500,
            },
            {
              day: "Scenario A",
              event: "AAPL stays between $175 and $195 for 21 days",
              action: "50 percent target hit at $250 profit, close the entire condor early",
              pl: 250,
              cumPl: 250,
            },
            {
              day: "Scenario B",
              event: "AAPL rallies to $193, nearing the $195 call wing",
              action: "Stop loss triggered at $1,000 loss (2x credit), close to prevent max loss",
              pl: -1000,
              cumPl: -1000,
            },
            {
              day: "Scenario C",
              event: "AAPL stays near $185, reaches 21 DTE time stop",
              action: "Time stop: close for $320 profit even though max profit not yet reached",
              pl: 320,
              cumPl: 320,
            },
            {
              day: "Lesson",
              event: "All three scenarios had a defined exit plan from day one",
              action: "No decisions made under pressure because rules were set at entry",
              pl: 0,
              cumPl: 0,
            },
          ]}
          accent={accent}
          subheading="$500 max profit iron condor with defined exits for every scenario"
        />
      ),
    },

    // Scene 7 (45s)
    {
      durationInFrames: sec(45),
      render: () => (
        <CalculationScene
          heading="Rolling a Threatened Short Call: The Math"
          steps={[
            {
              label: "Current Position: Short AAPL $195 Call at $2.50 credit",
              formula: "Original credit collected per share",
              result: "$250 per contract",
              highlight: false,
            },
            {
              label: "Roll Cost: Buy Back $195 Call Now at $4.80",
              formula: "$4.80 minus $2.50 original credit = $2.30 debit",
              result: "minus $230 per contract",
              highlight: false,
            },
            {
              label: "Sell New $200 Call at Next Expiry for $3.20",
              formula: "New credit collected on the roll",
              result: "+$320 per contract",
              highlight: false,
            },
            {
              label: "Net Roll Credit",
              formula: "$3.20 minus $2.30 roll cost",
              result: "+$0.90 net credit",
              highlight: true,
              color: "#22c55e",
            },
          ]}
          conclusion="The roll collects an additional $90 net credit per contract and gives more time and distance. Only roll when you receive a net credit, never for a debit."
          accent={accent}
        />
      ),
    },

    // Scene 8 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <MistakeHighlightScene
          heading="Holding Winners Too Long for Maximum Profit"
          mistake={{
            label: "Refusing to close a winning short options trade before expiry",
            detail:
              "An iron condor at 80 percent of max profit needs the last 20 percent but takes 2 more weeks to earn it. In those 2 weeks anything can go wrong and wipe out all the gains.",
          }}
          correction={{
            label: "Booking 50 percent of max profit has better risk adjusted returns than holding to expiry",
            detail:
              "Closing at $250 on a $500 max profit trade frees up capital for a new trade in the same time period. Two 50 percent wins on separate trades outperform one full win attempt.",
          }}
          insight="The 50 percent target rule is not about being satisfied with less. It is about running a higher win rate strategy that compounds capital faster over the full year."
          accent={accent}
        />
      ),
    },

    // Scene 9 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <StatsScene
          heading="Exit Management Key Numbers"
          stats={[
            { label: "Short Options Target", value: "50% of max profit", color: accent },
            { label: "Stop Loss Level", value: "2x credit received", color: "#ef4444" },
            { label: "Time Stop Trigger", value: "21 DTE", color: "#f59e0b" },
            { label: "Roll Rule", value: "Net credit only", color: "#22c55e" },
          ]}
          accent={accent}
          footnote="The 21 DTE time stop was developed by TastyTrade research showing gamma risk accelerates sharply inside 21 days to expiry"
        />
      ),
    },

    // Scene 10 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <BulletScene
          heading="Assignment Risk Near Expiry: What to Watch"
          bullets={[
            "American style options can be exercised at any time, risk increases as they move in the money",
            "Deep in the money calls near expiry face the highest assignment risk from dividend capture strategies",
            "The day before an ex dividend date is the highest assignment risk day of the year for short calls",
            "Close or roll any short in the money option before the ex dividend date to eliminate assignment risk",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 11 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <BulletScene
          heading="Rolling Rules: When to Roll and When to Close"
          bullets={[
            "Roll only when you can collect a net credit after the cost of buying back the current position",
            "Never roll a losing position forward in time just to delay accepting the loss",
            "Rolling out in time extends duration risk, only do it when the thesis is still valid",
            "If a roll requires a debit, close the entire trade and start fresh with a new position",
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
          heading="Exits Are Where Trading Discipline Lives"
          takeaways={[
            "50 percent target on short options produces higher win rates than holding to expiry",
            "Stop loss at 2 times credit received prevents any single trade from damaging the account",
            "21 DTE time stop removes gamma risk before it becomes unmanageable",
            "Roll only for net credits and only when the original thesis is still intact",
          ]}
          accent={accent}
          closingLine="Plan every exit before you enter. The best traders are not smarter about entries, they are ruthlessly disciplined about exits."
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
