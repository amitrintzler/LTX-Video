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

// ── Stocks101Long ─────────────────────────────────────────────────────────────
// Lesson: stocks-101 — "What Is a Stock?"

export type Stocks101LongProps = {
  accent?: string;
};

export const Stocks101Long: React.FC<Stocks101LongProps> = ({ accent = "#3b82f6" }) => {
  useVideoConfig();

  const scenes: SceneDef[] = [
    // Scene 1 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <TitleScene
          label="Stock Market Basics"
          title="What Is a Stock?"
          subtitle="Equity ownership, market cap, dividends, and splits explained with real data"
          accent={accent}
        />
      ),
    },

    // Scene 2 (25s)
    {
      durationInFrames: sec(25),
      render: () => (
        <BulletScene
          heading="What You Actually Own When You Buy a Share"
          bullets={[
            "A share is a fractional ownership stake in a real business",
            "Buy 1 AAPL share and you own 1 of 15.4 billion outstanding shares",
            "Shareholders receive dividends if declared and can vote on major company decisions",
            "Stock price reflects what the market believes future earnings are worth today",
            "Equity holders are last in line in bankruptcy but first in upside when the company thrives",
          ]}
          accent={accent}
          icon="📈"
        />
      ),
    },

    // Scene 3 (45s)
    {
      durationInFrames: sec(45),
      render: () => (
        <StatsScene
          heading="Market Cap Leaders: The Biggest Public Companies"
          stats={[
            { label: "MSFT", value: "$3.1 trillion", color: "#22c55e" },
            { label: "AAPL", value: "$2.9 trillion", color: accent },
            { label: "NVDA", value: "$2.4 trillion", color: "#f59e0b" },
            { label: "AMZN", value: "$1.9 trillion", color: "#ef4444" },
          ]}
          accent={accent}
          footnote="SPY tracks 504 companies in the S and P 500. These 4 alone represent roughly 25 percent of the index weight."
        />
      ),
    },

    // Scene 4 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <CalculationScene
          heading="Market Cap: Shares Outstanding Times Stock Price"
          steps={[
            { label: "AAPL shares outstanding", formula: "Total shares in circulation", result: "15.4 billion" },
            { label: "AAPL stock price", formula: "Market closing price", result: "$192" },
            { label: "Market cap formula", formula: "15.4B shares × $192 per share", result: "$2.96 trillion", highlight: true },
            { label: "Comparison: if price drops to $180", formula: "15.4B × $180", result: "$2.77 trillion" },
            { label: "Comparison: if price rises to $210", formula: "15.4B × $210", result: "$3.23 trillion" },
            { label: "Key insight", formula: "Buybacks reduce shares outstanding", result: "Raises EPS and market cap per share", highlight: true },
          ]}
          conclusion="Market cap is the total price the market places on a company at this instant. It changes every second the stock trades."
          accent={accent}
        />
      ),
    },

    // Scene 5 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <BulletScene
          heading="Dividends and Stock Splits: Two Ways Value Flows to Shareholders"
          bullets={[
            "Dividends: AAPL pays $0.25 per share quarterly, roughly $1.00 per year in cash",
            "Dividend yield = annual dividend divided by stock price ($1.00 / $192 = 0.52 percent)",
            "Stock splits: AAPL split 7 for 1 in 2014 and 4 for 1 in 2020",
            "Split adjusted price: AAPL traded at $5 in 2003 before all historical splits",
            "Splits do not change company value: more shares at proportionally lower price",
          ]}
          accent={accent}
          icon="💰"
        />
      ),
    },

    // Scene 6 (65s)
    {
      durationInFrames: sec(65),
      render: () => (
        <SvgLineChartScene
          heading="AAPL Price History: 5 Year Split Adjusted"
          subheading="From 2019 through 2024, split adjusted closing prices"
          data={[
            { label: "2019", value: 70 },
            { label: "2020", value: 122 },
            { label: "2021", value: 177 },
            { label: "2022", value: 130 },
            { label: "2023", value: 183 },
            { label: "2024", value: 195 },
          ]}
          accent={accent}
          yLabel="Price ($)"
          xLabel="Year"
          highlightIdx={5}
          footnote="The 2022 dip was driven by rising interest rates compressing tech valuations. 2023 recovery followed Fed pause signals."
        />
      ),
    },

    // Scene 7 (60s)
    {
      durationInFrames: sec(60),
      render: () => (
        <RealWorldExampleScene
          heading="Buying 10 Shares of AAPL: What You Actually Get"
          company="Apple Inc"
          scenario="An investor buys 10 shares of AAPL at $192. Total cost is $1,920. This represents 0.000000065 percent ownership of a $2.9 trillion business."
          setupItems={[
            { label: "Shares purchased", value: "10" },
            { label: "Price per share", value: "$192.00" },
            { label: "Total cost", value: "$1,920", color: accent },
            { label: "Annual dividend income", value: "$10.00", color: "#22c55e" },
            { label: "Dividend yield on cost", value: "0.52%", color: "#22c55e" },
          ]}
          outcome="Ownership with income and upside"
          outcomeDetail="If AAPL grows to $250 in 3 years the position is worth $2,500, a $580 gain (30 percent return) plus $30 in dividends collected. Total return: $610 on a $1,920 investment."
          outcomeColor="#22c55e"
          accent={accent}
        />
      ),
    },

    // Scene 8 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <ComparisonTableScene
          heading="Stocks vs Bonds vs Cash: Three Asset Classes"
          subheading="10 year historical averages across asset types"
          columns={["Asset", "Historical Return", "Risk Level", "Best For"]}
          rows={[
            { cells: ["S and P 500 stocks", "10.5% per year", "High", "Long term growth"], winner: 1, highlight: true },
            { cells: ["Investment grade bonds", "4.5% per year", "Low to medium", "Income stability"], winner: 3 },
            { cells: ["Treasury bills (cash)", "2.5% per year", "Very low", "Preservation"], winner: 3 },
            { cells: ["Dividends stocks", "7% total return", "Medium", "Income and growth"], winner: 3 },
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
          heading="Confusing a High Stock Price with a High Stock Value"
          mistake={{
            label: "Thinking a $1,000 stock is more expensive than a $10 stock",
            detail: "A beginner avoids Booking Holdings at $3,500 per share thinking it is too expensive and buys a $10 stock instead. Absolute price per share tells you nothing about valuation. A $10 stock with a tiny float and no earnings can be wildly overpriced.",
          }}
          correction={{
            label: "Compare market cap, P/E, and fundamentals not share price",
            detail: "Valuation is about what you pay for what you get. A $3,500 share might be cheap if the company earns $200 per share. A $5 stock with no earnings and 500 million shares is a $2.5 billion market cap with nothing backing it."
          }}
          insight="Stock splits prove the point: AAPL at $192 post splits is the same business as $12,544 pre splits. The price is arbitrary. The business value is what matters."
          accent={accent}
        />
      ),
    },

    // Scene 10 (70s)
    {
      durationInFrames: sec(70),
      render: () => (
        <WorkedExampleScene
          heading="Tracking an AAPL Position Over 3 Months"
          subheading="10 shares purchased at $185, held through a dividend and a dip"
          company="Apple Inc"
          ticker="AAPL"
          trades={[
            { day: "Month 1 entry", event: "Buy 10 AAPL at $185 per share", action: "Total cost $1,850. Position established.", pl: -1850, cumPl: -1850 },
            { day: "Month 1 end", event: "Dividend payment of $0.25 per share", action: "Receive $2.50 cash dividend into account", pl: 250, cumPl: -1600 },
            { day: "Month 2", event: "Market sell off, AAPL drops to $172", action: "Paper loss: 10 × ($185 minus $172) = $130 unrealized", pl: -1300, cumPl: -2900 },
            { day: "Month 2 end", event: "Second quarterly dividend paid", action: "Receive another $2.50. AAPL recovering to $180.", pl: 250, cumPl: -2650 },
            { day: "Month 3 end", event: "AAPL recovers to $195 on earnings beat", action: "Sell 10 shares at $195 per share", pl: 1950, cumPl: -700 },
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
          heading="Connecting Stocks to Options and the Broader Market"
          bullets={[
            "Options are priced on top of stocks: you must understand the underlying first",
            "High market cap stocks like AAPL and SPY have the most liquid options markets",
            "Dividends affect call and put pricing: ex dividend dates lower call premiums",
            "Earnings reports are the biggest stock catalyst and drive implied volatility spikes",
            "Index funds like SPY and QQQ track baskets of individual stocks weighted by cap",
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
          heading="Stocks Are Ownership Slices in Real Businesses"
          takeaways={[
            "Market cap equals shares outstanding times stock price, not a fixed number",
            "Dividends provide income; splits lower price without changing company value",
            "AAPL 5 year return of 179 percent versus S and P 500 average of 10.5 percent per year",
            "Compare valuation ratios not share prices when deciding between two stocks",
            "Stock fundamentals drive options pricing: know the stock before trading its options",
          ]}
          accent={accent}
          closingLine="Next: Order types and how your trade reaches the market."
        />
      ),
    },

    // Scene 13 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <RealWorldExampleScene
          heading="Stock Split in Action: AAPL 4 for 1 in August 2020"
          company="Apple Inc"
          scenario="On August 31 2020, AAPL executed a 4 for 1 stock split. Every shareholder received 3 additional shares for each share held. The price adjusted from $500 to $125 automatically. Company value did not change by one dollar."
          setupItems={[
            { label: "Pre split price", value: "$499.23", color: "#94a3b8" },
            { label: "Post split price", value: "$124.81 (divided by 4)", color: accent },
            { label: "Shares before (example)", value: "10 shares", color: "#94a3b8" },
            { label: "Shares after split", value: "40 shares", color: "#22c55e" },
            { label: "Total value before and after", value: "$4,992.30 unchanged", color: "#22c55e" },
          ]}
          outcome="More accessible price attracts more retail investors"
          outcomeDetail="After the split, AAPL's lower per share price attracted more retail buyers. The stock rose 25 percent in the 3 months following the split, though this was driven by earnings and broader market momentum rather than the split itself."
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

// ── OrderTypesLong ────────────────────────────────────────────────────────────
// Lesson: order-types — "Market, Limit, Stop, Stop Limit"

export type OrderTypesLongProps = {
  accent?: string;
};

export const OrderTypesLong: React.FC<OrderTypesLongProps> = ({ accent = "#f59e0b" }) => {
  useVideoConfig();

  const scenes: SceneDef[] = [
    // Scene 1 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <TitleScene
          label="Order Types"
          title="Market, Limit, Stop, Stop Limit"
          subtitle="How your trade reaches the exchange and why order type changes everything"
          accent={accent}
        />
      ),
    },

    // Scene 2 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <BulletScene
          heading="The Four Core Order Types Every Trader Must Know"
          bullets={[
            "Market order: execute immediately at whatever price is available right now",
            "Limit order: execute only if price reaches your specified level or better",
            "Stop order: trigger a market order when price crosses a threshold",
            "Stop limit order: trigger a limit order (not market) when threshold is crossed",
          ]}
          accent={accent}
          icon="🎯"
        />
      ),
    },

    // Scene 3 (45s)
    {
      durationInFrames: sec(45),
      render: () => (
        <SetupScene
          heading="Inside the Order Book: AAPL Live Bid and Ask"
          items={[
            { label: "Best Bid", value: "$192.45 (500 shares)", color: "#22c55e" },
            { label: "Best Ask", value: "$192.48 (300 shares)", color: "#ef4444" },
            { label: "Spread", value: "$0.03 (1.6 cents per $100)", color: accent },
            { label: "Last Trade", value: "$192.47", color: "#94a3b8" },
            { label: "Market Order Buy", value: "Fills at $192.48 ask immediately", color: accent },
            { label: "Limit Buy $191.50", value: "Waits in queue until AAPL dips to $191.50", color: "#3b82f6" },
          ]}
          accent={accent}
          description="The bid is what buyers will pay. The ask is what sellers want. You pay the ask to buy and receive the bid to sell."
        />
      ),
    },

    // Scene 4 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <CalculationScene
          heading="Slippage and Spread Cost: The Hidden Tax on Every Trade"
          steps={[
            { label: "AAPL bid ask spread", formula: "$192.48 ask minus $192.45 bid", result: "$0.03" },
            { label: "Position size", formula: "100 shares per trade", result: "100 shares" },
            { label: "Cost to buy then sell", formula: "Buy at ask, sell at bid: 2 × $0.03", result: "$0.06 per share" },
            { label: "Round trip cost 100 shares", formula: "100 × $0.06", result: "$6.00", highlight: true },
            { label: "Active trader 5 trades per day", formula: "5 × $6.00", result: "$30 per day in spread" },
            { label: "Annualized (250 trading days)", formula: "250 × $30", result: "$7,500 per year in spread", color: "#ef4444" },
          ]}
          conclusion="Spread cost compounds quietly. A frequent trader using only market orders on AAPL pays thousands per year in slippage before any strategy gains or losses."
          accent={accent}
        />
      ),
    },

    // Scene 5 (45s)
    {
      durationInFrames: sec(45),
      render: () => (
        <ComparisonTableScene
          heading="Order Types: Execution Certainty vs Price Certainty"
          subheading="AAPL trading near $192 with bid $192.45 and ask $192.48"
          columns={["Order Type", "Execution Certainty", "Price Certainty", "Best Use Case"]}
          rows={[
            { cells: ["Market buy", "Guaranteed", "None", "Urgent entry in liquid stock"], winner: 1, highlight: true },
            { cells: ["Limit buy", "Not guaranteed", "Exact or better", "Patient entry at support"], winner: 3 },
            { cells: ["Stop market sell", "Triggered guaranteed", "None", "Emergency loss control"], winner: 1 },
            { cells: ["Stop limit sell", "Not guaranteed", "Bounded", "Controlled loss in volatile stock"], winner: 3 },
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 6 (60s)
    {
      durationInFrames: sec(60),
      render: () => (
        <RealWorldExampleScene
          heading="Limit Order Catching a Dip: AAPL Example"
          company="Apple Inc"
          scenario="AAPL trading at $192.48. A trader wants to buy 100 shares but only at $191.50 or below. They place a limit buy order and wait for a pullback."
          setupItems={[
            { label: "Current price", value: "$192.48" },
            { label: "Limit buy price", value: "$191.50", color: accent },
            { label: "Target sell price", value: "$196.00", color: "#22c55e" },
            { label: "Stop loss", value: "$189.00", color: "#ef4444" },
            { label: "Risk per share", value: "$2.50", color: "#ef4444" },
          ]}
          outcome="Limit fills on afternoon dip"
          outcomeDetail="AAPL dips to $191.38 during a morning sell off. The limit order fills at $191.50. Stock recovers to $196 in two days. Gain: $450 on 100 shares. The limit order saved $98 versus buying at market open."
          outcomeColor="#22c55e"
          accent={accent}
        />
      ),
    },

    // Scene 7 (65s)
    {
      durationInFrames: sec(65),
      render: () => (
        <SvgLineChartScene
          heading="AAPL Intraday: Limit Order Trigger Zone"
          subheading="15 minute candles showing morning sell off and limit fill at $191.50"
          data={[
            { label: "9:30", value: 192.48 },
            { label: "9:45", value: 192.10 },
            { label: "10:00", value: 191.80 },
            { label: "10:15", value: 191.38 },
            { label: "10:30", value: 191.75 },
            { label: "11:00", value: 192.50 },
            { label: "12:00", value: 193.20 },
            { label: "2:00", value: 194.80 },
            { label: "3:00", value: 195.40 },
            { label: "4:00", value: 195.90 },
          ]}
          accent={accent}
          yLabel="Price ($)"
          xLabel="Time"
          highlightIdx={3}
          footnote="The limit buy at $191.50 filled near the 10:15 low. Market order buyers at open paid $1.10 more per share."
        />
      ),
    },

    // Scene 8 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <MistakeHighlightScene
          heading="Using Market Orders in Illiquid Stocks"
          mistake={{
            label: "Placing a market order on a stock with a wide bid ask spread",
            detail: "A trader wants to buy 500 shares of a small cap stock with a bid of $8.20 and an ask of $8.75. A market order fills at $8.75. The spread is $0.55 per share, or $275 on entry alone. If they sell immediately they lose $275 before the stock even moves.",
          }}
          correction={{
            label: "Always use limit orders on stocks with wide spreads or low volume",
            detail: "Check the bid ask spread before entering any order. If the spread exceeds 0.2 percent of price, a market order is a gift to the market maker. Use a limit order between the bid and ask to get a fair fill or walk away.",
          }}
          insight="AAPL with a $0.03 spread on a $192 stock is 0.016 percent. A small cap biotech with a $0.50 spread on a $10 stock is 5 percent. Market orders hurt most on the stocks retail traders are most excited about."
          accent={accent}
        />
      ),
    },

    // Scene 9 (70s)
    {
      durationInFrames: sec(70),
      render: () => (
        <WorkedExampleScene
          heading="Stop Limit Order on TSLA Earnings"
          subheading="Protecting a long position through a binary event with a stop limit"
          company="Tesla"
          ticker="TSLA"
          trades={[
            { day: "Pre earnings", event: "Long 50 TSLA at $245. Earnings tomorrow after close.", action: "Place stop limit: stop at $238, limit at $237.50", pl: -12250, cumPl: -12250 },
            { day: "Earnings day", event: "TSLA beats EPS but misses revenue guidance", action: "Stock drops to $240 in after hours. Stop not triggered yet.", pl: -250, cumPl: -12500 },
            { day: "Next morning", event: "Pre market selling pushes TSLA to $236.80", action: "Stop triggers at $238. Limit order sits at $237.50.", pl: 0, cumPl: -12500 },
            { day: "Market open", event: "TSLA opens at $238.20, briefly trades at $237.80", action: "Limit order fills at $237.80 (better than limit price)", pl: -365, cumPl: -12865 },
            { day: "End of week", event: "TSLA falls to $228 on analyst downgrade", action: "Stop limit saved $480 versus holding through the drop", pl: 480, cumPl: -12385 },
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 10 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <StatsScene
          heading="Typical Bid Ask Spreads by Market Cap Tier"
          stats={[
            { label: "AAPL (mega cap)", value: "$0.01 to $0.03", color: "#22c55e" },
            { label: "Mid cap stock", value: "$0.05 to $0.15", color: accent },
            { label: "Small cap stock", value: "$0.20 to $0.75", color: "#f59e0b" },
            { label: "Micro cap penny stock", value: "$0.50 to $2.00", color: "#ef4444" },
          ]}
          accent={accent}
          footnote="Options spreads on the same stocks are 5 to 20 times wider than equity spreads. Limit orders are even more critical when trading options."
        />
      ),
    },

    // Scene 11 (35s)
    {
      durationInFrames: sec(35),
      render: () => (
        <BulletScene
          heading="How Order Types Connect to Options Trading"
          bullets={[
            "Options orders use the same limit and market mechanics as stock orders",
            "Always use limit orders when buying or selling options: spreads are wide",
            "Stop orders on options can cause unwanted fills during premarket volatility",
            "The options mid price (bid plus ask divided by 2) is your target fill price",
            "Day orders expire at close; GTC orders stay open until you cancel them",
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
          heading="Order Types: Execution Is Half the Trade"
          takeaways={[
            "Market orders guarantee execution but not price: use only on liquid mega cap stocks",
            "Limit orders give price control but may not fill: ideal for planned entries and exits",
            "Stop orders protect positions automatically but can fill at bad prices on gaps",
            "Always check bid ask spread before entering: wide spread means limit orders only",
            "Options require limit orders every time: the spread on options is rarely negotiable",
          ]}
          accent={accent}
          closingLine="Next: Candlestick charts and reading price action in real time."
        />
      ),
    },

    // Scene 13 (45s)
    {
      durationInFrames: sec(45),
      render: () => (
        <SetupScene
          heading="GTC vs Day Orders: Duration Settings Every Trader Needs"
          items={[
            { label: "Day order", value: "Expires at market close (4pm ET) if not filled", color: accent },
            { label: "GTC order", value: "Good Till Canceled: stays open until you cancel or it fills", color: "#22c55e" },
            { label: "GTC typical limit", value: "Most brokers cancel GTC orders after 60 to 90 days", color: "#94a3b8" },
            { label: "Extended hours order", value: "Pre market (4am to 9:30am) and after hours (4pm to 8pm)", color: "#3b82f6" },
            { label: "Fill or kill", value: "Must fill entire order immediately or cancel completely", color: "#f59e0b" },
            { label: "Immediate or cancel", value: "Fill whatever quantity is available immediately, cancel the rest", color: "#a855f7" },
          ]}
          accent={accent}
          description="GTC limit orders work overnight. A limit buy placed Friday evening can fill Monday at open if the stock gaps down to your price target."
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

// ── Candlesticks101Long ───────────────────────────────────────────────────────
// Lesson: candlesticks-101 — "Reading Candlestick Charts"

export type Candlesticks101LongProps = {
  accent?: string;
};

export const Candlesticks101Long: React.FC<Candlesticks101LongProps> = ({ accent = "#22c55e" }) => {
  useVideoConfig();

  const scenes: SceneDef[] = [
    // Scene 1 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <TitleScene
          label="Technical Analysis"
          title="Reading Candlestick Charts"
          subtitle="OHLC anatomy, key patterns, and what each candle tells you about market psychology"
          accent={accent}
        />
      ),
    },

    // Scene 2 (25s)
    {
      durationInFrames: sec(25),
      render: () => (
        <BulletScene
          heading="The Four Numbers Inside Every Candle"
          bullets={[
            "Open: the first trade price at the start of the time period",
            "High: the highest price reached during the entire candle period",
            "Low: the lowest price reached during the entire candle period",
            "Close: the last trade price before the candle period ended",
            "Body: the rectangle between open and close. Wick: the thin lines beyond the body.",
          ]}
          accent={accent}
          icon="🕯️"
        />
      ),
    },

    // Scene 3 (45s)
    {
      durationInFrames: sec(45),
      render: () => (
        <SetupScene
          heading="Candle Color Rules and What They Reveal"
          items={[
            { label: "Green candle", value: "Close is above open (buyers won the session)", color: "#22c55e" },
            { label: "Red candle", value: "Close is below open (sellers won the session)", color: "#ef4444" },
            { label: "Long body", value: "Strong conviction in one direction", color: accent },
            { label: "Small body (doji)", value: "Indecision: buyers and sellers were equal", color: "#94a3b8" },
            { label: "Long upper wick", value: "Price rejected higher levels and retreated", color: "#f59e0b" },
            { label: "Long lower wick", value: "Price rejected lower levels and recovered", color: "#3b82f6" },
          ]}
          accent={accent}
          description="AAPL 2024 01 15: Open $183.42, High $185.01, Low $182.80, Close $184.37. Green candle, buyers in control."
        />
      ),
    },

    // Scene 4 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <CalculationScene
          heading="Body Size Ratio: Measuring Conviction from the Candle"
          steps={[
            { label: "AAPL candle: Open", formula: "First trade of the session", result: "$183.42" },
            { label: "AAPL candle: Close", formula: "Last trade of the session", result: "$184.37" },
            { label: "Body size", formula: "$184.37 close minus $183.42 open", result: "$0.95" },
            { label: "Total range", formula: "$185.01 high minus $182.80 low", result: "$2.21" },
            { label: "Body to range ratio", formula: "$0.95 divided by $2.21", result: "43 percent", highlight: true },
            { label: "Interpretation", formula: "Body covers 43 percent of range", result: "Moderate conviction, not a decisive day", highlight: true },
          ]}
          conclusion="A body ratio above 70 percent signals strong directional conviction. Below 20 percent signals indecision or a doji. Context always matters."
          accent={accent}
        />
      ),
    },

    // Scene 5 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <ComparisonTableScene
          heading="Key Candlestick Patterns and What They Signal"
          subheading="Single and two candle patterns used in technical analysis"
          columns={["Pattern", "Structure", "Signal", "Reliability"]}
          rows={[
            { cells: ["Doji", "Open equals close, long wicks", "Indecision, reversal watch", "Medium"], winner: 2 },
            { cells: ["Hammer", "Small top body, long lower wick", "Bullish reversal at support", "Medium to high"], winner: 2, highlight: true },
            { cells: ["Shooting star", "Small bottom body, long upper wick", "Bearish reversal at resistance", "Medium to high"], winner: 2 },
            { cells: ["Bullish engulfing", "Red candle fully covered by next green", "Strong bullish reversal", "High"], winner: 3, highlight: true },
            { cells: ["Bearish engulfing", "Green candle fully covered by next red", "Strong bearish reversal", "High"], winner: 3 },
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 6 (60s)
    {
      durationInFrames: sec(60),
      render: () => (
        <RealWorldExampleScene
          heading="Hammer at Support on SPY: The Setup That Works"
          company="S and P 500 ETF"
          scenario="SPY pulls back to $480 support level over 3 days. On day 4, a hammer candle forms: open $480.20, low $477.50, close $481.00. Long lower wick shows buyers defending the support zone."
          setupItems={[
            { label: "Support level", value: "$480.00", color: accent },
            { label: "Hammer low", value: "$477.50", color: "#ef4444" },
            { label: "Hammer close", value: "$481.00", color: "#22c55e" },
            { label: "Lower wick length", value: "$2.70 (rejection zone)", color: accent },
          ]}
          outcome="Support confirmed, rally follows"
          outcomeDetail="SPY rallied from the $480 hammer close to $491 over the next 5 sessions. The long lower wick proved buyers stepped in aggressively when price dipped below $480. Stop loss below the hammer low at $477 risked only $4 to target $11."
          outcomeColor="#22c55e"
          accent={accent}
        />
      ),
    },

    // Scene 7 (65s)
    {
      durationInFrames: sec(65),
      render: () => (
        <SvgLineChartScene
          heading="AAPL 30 Day Chart: Three Key Pattern Locations"
          subheading="Closing prices with doji, hammer, and engulfing pattern timestamps"
          data={[
            { label: "Day 1", value: 185.40 },
            { label: "Day 3", value: 186.20 },
            { label: "Day 5", value: 185.80 },
            { label: "Day 8", value: 183.50 },
            { label: "Day 10", value: 182.40 },
            { label: "Day 12", value: 182.80 },
            { label: "Day 15", value: 184.30 },
            { label: "Day 18", value: 187.10 },
            { label: "Day 20", value: 188.50 },
            { label: "Day 23", value: 187.80 },
            { label: "Day 25", value: 189.20 },
            { label: "Day 28", value: 191.00 },
            { label: "Day 30", value: 192.40 },
          ]}
          accent={accent}
          yLabel="Price ($)"
          xLabel="Day"
          highlightIdx={5}
          footnote="Day 12 was a hammer after the dip to $182.40. Day 20 to 23 showed a shooting star. Each preceded a directional shift."
        />
      ),
    },

    // Scene 8 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <MistakeHighlightScene
          heading="Over Relying on Single Candle Signals"
          mistake={{
            label: "Trading every hammer or doji as if it guarantees a reversal",
            detail: "A trader sees a hammer on NVDA after a 5 day decline. They buy immediately expecting a reversal. But NVDA gaps down the next morning because a macro event occurred overnight. One candle never works in isolation.",
          }}
          correction={{
            label: "Require confluence: candle pattern plus support level plus volume confirmation",
            detail: "A hammer is meaningful when it forms at a documented support level AND volume on the hammer day is above average AND the next candle confirms by closing above the hammer close. Three conditions, not one.",
          }}
          insight="Candles are probability enhancers not certainties. A bullish engulfing at a key support level after a 10 percent pullback with above average volume is a strong setup. The same pattern in the middle of a range after 2 green candles is noise."
          accent={accent}
        />
      ),
    },

    // Scene 9 (70s)
    {
      durationInFrames: sec(70),
      render: () => (
        <WorkedExampleScene
          heading="Reading 5 Candles in Sequence on NVDA"
          subheading="Interpreting the story told by five consecutive daily candles"
          company="NVIDIA"
          ticker="NVDA"
          trades={[
            { day: "Candle 1", event: "Strong green body, NVDA $820 to $838, small wicks", action: "Bullish momentum, buyers firmly in control, continuation likely", pl: 1800, cumPl: 1800 },
            { day: "Candle 2", event: "Doji: open $839, close $839.50, long wicks both sides", action: "Indecision after strong run, potential pause or reversal forming", pl: 50, cumPl: 1850 },
            { day: "Candle 3", event: "Red candle $839 open, $824 close, moderate body", action: "Sellers taking profits after the doji warned of weakness", pl: -1500, cumPl: 350 },
            { day: "Candle 4", event: "Hammer: open $822, close $826, low $818, small upper wick", action: "Buyers defending the $820 area, long lower wick shows demand", pl: 400, cumPl: 750 },
            { day: "Candle 5", event: "Bullish engulfing: opens below candle 4 open, closes above it", action: "Confirmation of hammer. Strong reversal signal. Buy trigger.", pl: 1200, cumPl: 1950 },
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 10 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <BulletScene
          heading="Connecting Candlesticks to Support and Resistance"
          bullets={[
            "Candle patterns are strongest when they form exactly at documented S and R levels",
            "Volume confirmation on the pattern candle increases reliability significantly",
            "The wick beyond a support level shows the level was tested and held",
            "Engulfing patterns at resistance signal the level is rejecting price",
            "Dojis at prior highs or lows signal indecision at key decision zones",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 11 (35s)
    {
      durationInFrames: sec(35),
      render: () => (
        <StatsScene
          heading="Candlestick Pattern Reliability by Category"
          stats={[
            { label: "Bullish engulfing at support", value: "68% hit rate", color: "#22c55e" },
            { label: "Hammer at support", value: "62% hit rate", color: accent },
            { label: "Doji in middle of range", value: "51% hit rate", color: "#94a3b8" },
            { label: "Isolated single candle", value: "48 to 52% (coin flip)", color: "#ef4444" },
          ]}
          accent={accent}
          footnote="These hit rates assume the next candle confirms direction. Context and volume matter more than the pattern in isolation."
        />
      ),
    },

    // Scene 12 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <SummaryScene
          heading="Candles Tell the Story of Buyers vs Sellers"
          takeaways={[
            "Every candle encodes Open, High, Low, Close into a visual structure you can read instantly",
            "Body size shows conviction; wick length shows rejection at extremes",
            "Hammers and engulfing patterns at key levels are the most reliable single signals",
            "Never trade a pattern without checking where it appears on the price chart",
            "Combine candlestick signals with support levels and volume for highest probability setups",
          ]}
          accent={accent}
          closingLine="Next: Support and resistance, the foundation of every technical trade."
        />
      ),
    },

    // Scene 13 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <RealWorldExampleScene
          heading="Shooting Star at Resistance: Bearish Reversal on SPY"
          company="S and P 500 ETF"
          scenario="SPY reaches the $510 resistance zone after a 6 day rally. On the 7th day a shooting star forms: opens at $509.80, rallies to $513.40 (long upper wick), then closes at $510.20 near the open. Sellers rejected the push higher."
          setupItems={[
            { label: "Resistance zone", value: "$510.00", color: "#ef4444" },
            { label: "Shooting star high", value: "$513.40 (rejection point)", color: "#ef4444" },
            { label: "Shooting star close", value: "$510.20 (near open)", color: "#f59e0b" },
            { label: "Upper wick length", value: "$3.20 (strong rejection)", color: "#ef4444" },
          ]}
          outcome="SPY dropped 3.8 percent over the next 4 sessions"
          outcomeDetail="The shooting star at $510 resistance gave traders a clear short entry with a stop above $513.50. SPY fell to $490.60 in the following 4 sessions. Risk was $3.30 per share (stop to entry), reward was $19.60 to the $490 target."
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

// ── SupportResistanceLong ─────────────────────────────────────────────────────
// Lesson: support-resistance — "Support, Resistance, and Role Reversal"

export type SupportResistanceLongProps = {
  accent?: string;
};

export const SupportResistanceLong: React.FC<SupportResistanceLongProps> = ({ accent = "#ec4899" }) => {
  useVideoConfig();

  const scenes: SceneDef[] = [
    // Scene 1 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <TitleScene
          label="Technical Analysis"
          title="Support, Resistance, and Role Reversal"
          subtitle="Where buyers step in, where sellers dominate, and how levels flip their role"
          accent={accent}
        />
      ),
    },

    // Scene 2 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <BulletScene
          heading="What Creates Support and Resistance Levels"
          bullets={[
            "Prior swing highs and lows: prices that reversed direction before create memory in the market",
            "Round numbers: $100, $500, $1000 attract orders because traders anchor to them",
            "Volume nodes: high volume at a price level creates a supply and demand anchor",
            "Moving averages: dynamic levels that move with price and act as floating support",
            "Previous resistance becomes support after a confirmed breakout (role reversal)",
          ]}
          accent={accent}
          icon="🗺️"
        />
      ),
    },

    // Scene 3 (45s)
    {
      durationInFrames: sec(45),
      render: () => (
        <SetupScene
          heading="How to Draw Support and Resistance Levels Correctly"
          items={[
            { label: "Step 1", value: "Use weekly chart first to find major levels", color: accent },
            { label: "Step 2", value: "Mark swing highs where price reversed down at least twice", color: "#22c55e" },
            { label: "Step 3", value: "Mark swing lows where price reversed up at least twice", color: "#3b82f6" },
            { label: "Step 4", value: "Zoom into daily chart to refine exact price zones", color: "#f59e0b" },
            { label: "Step 5", value: "Treat levels as zones (2 to 3 dollar range) not exact prices", color: "#a855f7" },
            { label: "Step 6", value: "Delete levels that have not been tested in more than 6 months", color: "#94a3b8" },
          ]}
          accent={accent}
          description="Fewer high quality levels are more useful than 20 lines cluttering the chart."
        />
      ),
    },

    // Scene 4 (65s)
    {
      durationInFrames: sec(65),
      render: () => (
        <SvgLineChartScene
          heading="SPY 2024: Key Support and Resistance Zones"
          subheading="Three levels that defined the year and multiple breakout attempts"
          data={[
            { label: "Jan", value: 468 },
            { label: "Feb", value: 497 },
            { label: "Mar", value: 521 },
            { label: "Apr", value: 495 },
            { label: "May", value: 527 },
            { label: "Jun", value: 548 },
            { label: "Jul", value: 543 },
            { label: "Aug", value: 562 },
            { label: "Sep", value: 571 },
            { label: "Oct", value: 569 },
            { label: "Nov", value: 598 },
            { label: "Dec", value: 588 },
          ]}
          accent={accent}
          yLabel="Price ($)"
          xLabel="Month"
          highlightIdx={4}
          footnote="SPY found support near $480 in January, built resistance at $510, broke out and that $510 became support through May. Classic role reversal."
        />
      ),
    },

    // Scene 5 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <ComparisonTableScene
          heading="Strong vs Weak vs False Support: How to Tell the Difference"
          subheading="Not all support levels are equal in strength or reliability"
          columns={["Type", "Characteristics", "Volume", "Reliability"]}
          rows={[
            { cells: ["Strong support", "Tested 3 or more times, high volume bounces", "Above average", "High"], winner: 3, highlight: true },
            { cells: ["Moderate support", "Tested twice, average volume", "Average", "Medium"], winner: 3 },
            { cells: ["Weak support", "Only tested once, below average volume", "Below average", "Low"] },
            { cells: ["False support", "Held briefly then broke sharply lower", "Volume surge on break", "None"], winner: 3, highlight: false },
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 6 (60s)
    {
      durationInFrames: sec(60),
      render: () => (
        <RealWorldExampleScene
          heading="AAPL Bouncing Off $180 Support: The Trade Setup"
          company="Apple Inc"
          scenario="AAPL has touched $180 support twice in 8 weeks and bounced both times. On the third touch it forms a hammer candle with above average volume. This is a high probability long setup."
          setupItems={[
            { label: "Support level", value: "$180.00", color: accent },
            { label: "Entry price", value: "$181.00 (day after hammer)", color: "#22c55e" },
            { label: "Stop loss", value: "$178.00 (below support zone)", color: "#ef4444" },
            { label: "Target", value: "$195.00 (prior resistance)", color: "#22c55e" },
            { label: "Risk per share", value: "$3.00", color: "#ef4444" },
          ]}
          outcome="Classic support bounce with 4.7 to 1 reward"
          outcomeDetail="AAPL rallied from $181 entry to $195 target over 3 weeks. Stop at $178 never threatened. The third test of $180 support confirmed institutional buyers defending that level. Risk $3 to make $14."
          outcomeColor="#22c55e"
          accent={accent}
        />
      ),
    },

    // Scene 7 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <CalculationScene
          heading="Risk and Reward at Support: The Numbers Behind the Trade"
          steps={[
            { label: "Entry price at support", formula: "Buy the day after hammer close", result: "$181.00" },
            { label: "Stop loss placement", formula: "Below support zone, 2 percent buffer", result: "$178.00" },
            { label: "Risk per share", formula: "$181.00 minus $178.00", result: "$3.00", color: "#ef4444" },
            { label: "Target: prior resistance", formula: "AAPL prior high at $195", result: "$195.00" },
            { label: "Reward per share", formula: "$195.00 minus $181.00", result: "$14.00", color: "#22c55e" },
            { label: "Risk to reward ratio", formula: "$14.00 divided by $3.00", result: "4.7 to 1", highlight: true },
          ]}
          conclusion="At 4.7 to 1 you only need to win 18 percent of these trades to break even. Strong support setups with defined risk are among the best reward structures in technical trading."
          accent={accent}
        />
      ),
    },

    // Scene 8 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <MistakeHighlightScene
          heading="Drawing Too Many Lines: Chart Paralysis"
          mistake={{
            label: "Marking every minor swing high and low on the chart",
            detail: "A trader marks 15 support and resistance levels on a SPY daily chart. When price approaches any level, three other lines are nearby too. They cannot decide which level matters, miss the entry, or take contradictory trades triggered by overlapping levels.",
          }}
          correction={{
            label: "Keep only the 3 to 5 most significant levels on any chart",
            detail: "Major levels are tested 3 or more times, came from prior market structure, and have clear price memory. Minor levels add noise. When you have 3 clean levels you can trade confidently. When you have 15 you are frozen.",
          }}
          insight="The best technical traders have cleaner charts, not more complex ones. Every line you draw is a hypothesis that must be verified by market behavior. Unverified lines are just noise you convinced yourself was signal."
          accent={accent}
        />
      ),
    },

    // Scene 9 (70s)
    {
      durationInFrames: sec(70),
      render: () => (
        <WorkedExampleScene
          heading="QQQ $430 Resistance Breakout: The Full Trade"
          subheading="Three failed tests of resistance, then a confirmed breakout and role reversal"
          company="Nasdaq 100 ETF"
          ticker="QQQ"
          trades={[
            { day: "Test 1", event: "QQQ reaches $430 resistance, sold off to $418", action: "Resistance confirmed. Note the level and wait for more data.", pl: 0, cumPl: 0 },
            { day: "Test 2", event: "QQQ back to $430, again rejected, drops to $422", action: "Double top pattern forming. Resistance increasingly confirmed.", pl: 0, cumPl: 0 },
            { day: "Test 3", event: "QQQ approaches $430 on above average volume", action: "Watch closely: high volume tests of resistance often precede breakouts", pl: 0, cumPl: 0 },
            { day: "Breakout day", event: "QQQ closes at $433.50, above $430 with strong volume", action: "Enter long at $434. Stop at $428 (below old resistance, now support)", pl: 4340, cumPl: 4340 },
            { day: "Role reversal", event: "QQQ pulls back to $430 and holds, confirming role reversal", action: "The old resistance is now acting as support. Trail stop up to $431.", pl: 0, cumPl: 4340 },
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 10 (35s)
    {
      durationInFrames: sec(35),
      render: () => (
        <BulletScene
          heading="Connecting Support and Resistance to Moving Averages"
          bullets={[
            "The 200 day moving average is a dynamic support level used by institutions worldwide",
            "When SPY breaks below its 200 day MA, bear market behavior typically follows",
            "Moving averages confirm horizontal S and R levels when they converge at the same price",
            "A horizontal support level holding at the same price as the 50 day MA is triple confirmed",
            "Volume spikes at MA crossings signal institutional participation, not retail noise",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 11 (35s)
    {
      durationInFrames: sec(35),
      render: () => (
        <StatsScene
          heading="QQQ and SPY Key Technical Levels in 2024"
          stats={[
            { label: "SPY 2024 support", value: "$480 (held 3 times)", color: "#22c55e" },
            { label: "SPY 2024 resistance", value: "$510 (broke then became support)", color: accent },
            { label: "QQQ 2024 support", value: "$430 (broke out in May)", color: "#3b82f6" },
            { label: "AAPL 2024 support", value: "$180 (held twice, bounced to $195)", color: "#f59e0b" },
          ]}
          accent={accent}
          footnote="Support levels that have held 3 times and then been confirmed by a moving average carry the highest probability of holding again."
        />
      ),
    },

    // Scene 12 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <SummaryScene
          heading="Support and Resistance: The Map Every Trader Uses"
          takeaways={[
            "Support is where buyers historically stepped in; resistance is where sellers dominated",
            "Levels tested 3 or more times with high volume carry the most trading significance",
            "When resistance breaks and price confirms above it, the level becomes new support",
            "Risk reward at support is naturally favorable: stop below, target at next resistance",
            "Clean charts with 3 to 5 key levels beat cluttered charts with 20 minor lines",
          ]}
          accent={accent}
          closingLine="Next: Moving averages as dynamic support and the golden cross signal."
        />
      ),
    },

    // Scene 13 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <RealWorldExampleScene
          heading="False Breakout Setup: How to Avoid Getting Trapped"
          company="Nasdaq 100 ETF"
          scenario="QQQ breaks above the $430 resistance level intraday but closes back below it on low volume. The next day it gaps down to $424. This is a false breakout: price breached the level but sellers immediately reclaimed control."
          setupItems={[
            { label: "Resistance level", value: "$430.00", color: "#ef4444" },
            { label: "Intraday high (false break)", value: "$431.50", color: "#ef4444" },
            { label: "Closing price", value: "$429.30 (back below resistance)", color: "#f59e0b" },
            { label: "Volume on breakout day", value: "30% below 20 day average", color: "#ef4444" },
          ]}
          outcome="False breakout confirmed, 3 percent drop followed"
          outcomeDetail="Waiting for a daily close above resistance with above average volume would have kept traders out of this trap. QQQ fell to $416 over the next 6 sessions. The rule: never buy a breakout until the daily candle closes above the level."
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

// ── MovingAveragesLong ────────────────────────────────────────────────────────
// Lesson: moving-averages — "SMA, EMA, and the Golden Cross"

export type MovingAveragesLongProps = {
  accent?: string;
};

export const MovingAveragesLong: React.FC<MovingAveragesLongProps> = ({ accent = "#14b8a6" }) => {
  useVideoConfig();

  const scenes: SceneDef[] = [
    // Scene 1 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <TitleScene
          label="Technical Analysis"
          title="Moving Averages: SMA, EMA, and the Golden Cross"
          subtitle="Dynamic support levels, trend confirmation, and the most watched crossover signal in markets"
          accent={accent}
        />
      ),
    },

    // Scene 2 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <BulletScene
          heading="SMA vs EMA: Two Ways to Smooth Price Data"
          bullets={[
            "SMA (Simple Moving Average) weights every day equally over the lookback period",
            "EMA (Exponential Moving Average) weights recent days more heavily than older days",
            "EMA reacts faster to price changes, SMA is smoother and slower to change direction",
            "Most institutional traders use the 50 day and 200 day SMA as benchmark levels",
            "Day traders favor the 9 and 21 day EMA for faster entry and exit signals",
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
          heading="5 Day SMA Calculation with Real AAPL Prices"
          steps={[
            { label: "Day 1 close", formula: "AAPL closing price", result: "$188.40" },
            { label: "Day 2 close", formula: "AAPL closing price", result: "$190.10" },
            { label: "Day 3 close", formula: "AAPL closing price", result: "$189.55" },
            { label: "Day 4 close", formula: "AAPL closing price", result: "$191.20" },
            { label: "Day 5 close", formula: "AAPL closing price", result: "$192.30" },
            { label: "5 day SMA", formula: "(188.40 + 190.10 + 189.55 + 191.20 + 192.30) / 5", result: "$190.31", highlight: true },
          ]}
          conclusion="When day 6 closes, day 1 drops off and day 6 is added. The average rolls forward every day, creating a smooth trend line from raw price data."
          accent={accent}
        />
      ),
    },

    // Scene 4 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <StatsScene
          heading="Key Moving Average Periods and Their Uses"
          stats={[
            { label: "20 day MA", value: "Short term trend (1 month)", color: "#22c55e" },
            { label: "50 day MA", value: "Medium term trend (2.5 months)", color: accent },
            { label: "200 day MA", value: "Long term trend (10 months)", color: "#3b82f6" },
            { label: "AAPL vs 200d MA", value: "Price $192 vs MA $178 (bullish)", color: "#f59e0b" },
          ]}
          accent={accent}
          footnote="Institutional investors monitor whether the S and P 500 is above or below its 200 day SMA as a primary bull or bear indicator."
        />
      ),
    },

    // Scene 5 (65s)
    {
      durationInFrames: sec(65),
      render: () => (
        <SvgLineChartScene
          heading="AAPL Price with 50 Day and 200 Day MA Overlaid"
          subheading="2023 to 2024 showing golden cross zone and bounces off the 50 day MA"
          data={[
            { label: "Jan 23", value: 145 },
            { label: "Mar 23", value: 157 },
            { label: "Jun 23", value: 189 },
            { label: "Aug 23", value: 178 },
            { label: "Oct 23", value: 171 },
            { label: "Dec 23", value: 193 },
            { label: "Feb 24", value: 184 },
            { label: "Apr 24", value: 171 },
            { label: "Jun 24", value: 195 },
            { label: "Aug 24", value: 226 },
            { label: "Oct 24", value: 229 },
            { label: "Dec 24", value: 254 },
          ]}
          accent={accent}
          yLabel="Price ($)"
          xLabel="Month"
          highlightIdx={5}
          footnote="NVDA bounced off the 50 day SMA 4 times in 2024. Each bounce was a confirmed entry point for trend followers."
        />
      ),
    },

    // Scene 6 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <ComparisonTableScene
          heading="SMA vs EMA: Responsiveness Compared"
          subheading="After a 5 percent stock drop, which average reacts faster?"
          columns={["Metric", "20 day SMA", "20 day EMA", "Winner"]}
          rows={[
            { cells: ["Days to reflect drop fully", "20 days", "5 to 8 days", "EMA"], winner: 3 },
            { cells: ["False signals in choppy markets", "Fewer", "More frequent", "SMA"], winner: 1, highlight: true },
            { cells: ["Trend following accuracy", "Strong", "Strong", "Tie"], winner: 0 },
            { cells: ["Whipsaw risk", "Lower", "Higher", "SMA"], winner: 1 },
            { cells: ["Best for day trading", "No", "Yes", "EMA"], winner: 3, highlight: true },
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 7 (60s)
    {
      durationInFrames: sec(60),
      render: () => (
        <RealWorldExampleScene
          heading="SPY Golden Cross January 2023: 18 Percent Rally Followed"
          company="S and P 500 ETF"
          scenario="January 2023: SPY 50 day SMA crossed above the 200 day SMA for the first time since before the 2022 bear market. This golden cross signal historically precedes extended rallies."
          setupItems={[
            { label: "50 day SMA at cross", value: "$392.80", color: "#22c55e" },
            { label: "200 day SMA at cross", value: "$392.60", color: accent },
            { label: "SPY price at cross", value: "$393.50" },
            { label: "Target: prior all time high", value: "$479.00", color: "#22c55e" },
            { label: "Stop: below 200 day MA", value: "$385.00", color: "#ef4444" },
          ]}
          outcome="18 percent rally over 11 months"
          outcomeDetail="SPY ran from $393 at the golden cross to $463 by December 2023, an 18 percent gain. The 200 day MA provided support on pullbacks throughout the year. Traders who entered on the golden cross confirmation captured the bulk of the year's gains."
          outcomeColor="#22c55e"
          accent={accent}
        />
      ),
    },

    // Scene 8 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <MistakeHighlightScene
          heading="Using Moving Averages Alone Without Volume Confirmation"
          mistake={{
            label: "Buying a golden cross signal without checking volume",
            detail: "A trader sees the 50 day cross above the 200 day on a mid cap stock and immediately buys. But the crossover happened on the lowest volume day in 3 months. Low volume crossovers are frequently false signals: price drifted into the cross without conviction.",
          }}
          correction={{
            label: "Require above average volume on or near the crossover day",
            detail: "A valid golden cross needs buying volume at least 20 percent above the 20 day average volume. If volume is below average at the cross, wait for a high volume confirmation candle before entering. One extra day of patience filters out most false crosses.",
          }}
          insight="Golden crosses on SPY with above average volume led to positive 3 month returns 73 percent of the time historically. Golden crosses with below average volume had a positive 3 month rate of only 54 percent, barely above a coin flip."
          accent={accent}
        />
      ),
    },

    // Scene 9 (70s)
    {
      durationInFrames: sec(70),
      render: () => (
        <WorkedExampleScene
          heading="NVDA Bounce Off 50 Day SMA: Four Times in One Year"
          subheading="Tracking the repeating pattern of pullback to MA and recovery"
          company="NVIDIA"
          ticker="NVDA"
          trades={[
            { day: "Q1 bounce", event: "NVDA pulls back from $650 to 50d MA at $580", action: "Enter at $582 on hammer candle. Target prior high $650. Stop $565.", pl: 5820, cumPl: 5820 },
            { day: "Q1 exit", event: "NVDA recovers to $648. Close near target.", action: "Exit at $645. Gain $63 per share on 100 share position.", pl: 6300, cumPl: 12120 },
            { day: "Q2 bounce", event: "NVDA dips again to 50d MA near $650", action: "New 50d MA level after prior run. Same setup with new anchor.", pl: 6500, cumPl: 18620 },
            { day: "Q3 bounce", event: "50d MA now at $750 after summer rally. NVDA touches $752.", action: "Pattern repeating: 50d MA acting as reliable institutional floor.", pl: 7500, cumPl: 26120 },
            { day: "Q4 bounce", event: "50d MA at $870. NVDA dips to $875 on rotation news.", action: "Fourth consecutive bounce off 50d. Exit $920 for $45 gain.", pl: 4500, cumPl: 30620 },
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 10 (35s)
    {
      durationInFrames: sec(35),
      render: () => (
        <BulletScene
          heading="Connecting Moving Averages to MACD and Momentum"
          bullets={[
            "MACD is built entirely from two EMAs: 12 day EMA minus 26 day EMA",
            "When the MACD line crosses above zero, the 12 day EMA is above the 26 day EMA",
            "Combining the 50 day SMA bounce with a positive MACD cross is a high confluence entry",
            "The 200 day MA slope indicates the primary trend: rising means bull, falling means bear",
            "Price above all three MAs (20, 50, 200) is the cleanest bull market configuration",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 11 (35s)
    {
      durationInFrames: sec(35),
      render: () => (
        <StatsScene
          heading="AAPL and SPY Moving Average Data Points (2024)"
          stats={[
            { label: "AAPL 200d SMA", value: "$178 (price $192, 7.9% above)", color: "#22c55e" },
            { label: "SPY golden cross", value: "January 2023, led to 18% rally", color: accent },
            { label: "NVDA 50d bounces", value: "4 confirmed bounces in 2024", color: "#f59e0b" },
            { label: "S and P 500 200d MA", value: "Below = bear market warning signal", color: "#ef4444" },
          ]}
          accent={accent}
          footnote="The 200 day MA is the single most watched technical level by institutional portfolio managers and hedge funds globally."
        />
      ),
    },

    // Scene 12 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <SummaryScene
          heading="Moving Averages: The Trend Is Your Friend Until It Is Not"
          takeaways={[
            "SMA weights all days equally; EMA weights recent days more and reacts faster",
            "The 50 day and 200 day SMA are the most important levels for swing and position traders",
            "Golden cross (50d crosses above 200d) historically precedes sustained rallies",
            "Always confirm MA signals with volume: low volume crossovers are frequently false",
            "NVDA bounced off its 50 day MA four separate times in 2024, each a tradeable entry",
          ]}
          accent={accent}
          closingLine="Next: Fundamental analysis and reading what the numbers inside a company tell you."
        />
      ),
    },

    // Scene 13 (45s)
    {
      durationInFrames: sec(45),
      render: () => (
        <ComparisonTableScene
          heading="Death Cross vs Golden Cross: Historical Hit Rates on SPY"
          subheading="50 day vs 200 day SMA crossover outcomes measured over 30 years of S and P 500 data"
          columns={["Signal", "Forward 3 Months", "Forward 12 Months", "With Volume Confirm"]}
          rows={[
            { cells: ["Golden cross", "+6.2% average", "+14.1% average", "+17.8% average"], winner: 3, highlight: true },
            { cells: ["Golden cross (low vol)", "+1.8% average", "+6.3% average", "N/A"], winner: 2 },
            { cells: ["Death cross", "minus 3.4% average", "minus 5.8% average", "minus 9.2% average"], winner: 3, highlight: false },
            { cells: ["Death cross (low vol)", "minus 0.9% average", "+1.2% average", "N/A"], winner: 3 },
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

// ── FundamentalAnalysis101Long ────────────────────────────────────────────────
// Lesson: fundamental-analysis-101 — "Reading a Company's Financial Health"

export type FundamentalAnalysis101LongProps = {
  accent?: string;
};

export const FundamentalAnalysis101Long: React.FC<FundamentalAnalysis101LongProps> = ({ accent = "#6366f1" }) => {
  useVideoConfig();

  const scenes: SceneDef[] = [
    // Scene 1 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <TitleScene
          label="Fundamental Analysis"
          title="Reading a Company's Financial Health"
          subtitle="P/E ratio, EPS, revenue growth, free cash flow, and return on equity explained with AAPL data"
          accent={accent}
        />
      ),
    },

    // Scene 2 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <BulletScene
          heading="Five Metrics That Define a Company's Financial Strength"
          bullets={[
            "P/E ratio: what you pay for each dollar of earnings (AAPL 31x, S and P 500 average 22x)",
            "EPS (Earnings Per Share): total net profit divided by total shares outstanding",
            "Revenue growth: is the business getting bigger and how fast",
            "Free cash flow: what is left after all expenses, taxes, and capital spending",
            "Return on equity: how efficiently management turns shareholder capital into profit",
          ]}
          accent={accent}
          icon="💼"
        />
      ),
    },

    // Scene 3 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <CalculationScene
          heading="P/E Ratio: What You Pay for Each Dollar of Earnings"
          steps={[
            { label: "AAPL stock price", formula: "Current market price per share", result: "$192.00" },
            { label: "AAPL annual EPS", formula: "Net income divided by shares outstanding", result: "$6.43" },
            { label: "P/E ratio", formula: "$192.00 divided by $6.43", result: "29.9x", highlight: true },
            { label: "Meaning", formula: "Paying $29.90 for every $1.00 AAPL earns", result: "Premium to S and P 500 at 22x" },
            { label: "MSFT comparison", formula: "$415 price divided by $11.45 EPS", result: "36.2x (higher growth premium)" },
            { label: "S and P 500 average", formula: "Market consensus fair value", result: "22x (historical average)", highlight: true },
          ]}
          conclusion="P/E tells you how expensive a stock is relative to its earnings. A P/E above the market average requires evidence of faster growth or a durable competitive advantage to justify."
          accent={accent}
        />
      ),
    },

    // Scene 4 (45s)
    {
      durationInFrames: sec(45),
      render: () => (
        <StatsScene
          heading="AAPL Fundamentals Dashboard (Fiscal Year 2023)"
          stats={[
            { label: "Revenue", value: "$383 billion", color: "#22c55e" },
            { label: "EPS", value: "$6.43 per share", color: accent },
            { label: "Free Cash Flow", value: "$99 billion", color: "#f59e0b" },
            { label: "Return on Equity", value: "87 percent", color: "#3b82f6" },
          ]}
          accent={accent}
          footnote="AAPL ROE of 87 percent is exceptional. NVDA ROE reached 123 percent in 2024 due to explosive GPU demand from AI infrastructure build out."
        />
      ),
    },

    // Scene 5 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <ComparisonTableScene
          heading="AAPL vs MSFT vs NVDA: Fundamental Comparison"
          subheading="Key metrics side by side for the three largest US companies by market cap"
          columns={["Metric", "AAPL", "MSFT", "NVDA"]}
          rows={[
            { cells: ["P/E ratio", "31x", "36x", "65x"], winner: 0, highlight: false },
            { cells: ["Annual EPS", "$6.43", "$11.45", "$12.96"], winner: 3, highlight: true },
            { cells: ["Revenue (annual)", "$383B", "$227B", "$61B"], winner: 1 },
            { cells: ["Free cash flow", "$99B", "$87B", "$27B"], winner: 1, highlight: true },
            { cells: ["Return on equity", "87%", "38%", "123%"], winner: 3 },
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
          heading="AAPL EPS Growth 2019 to 2024"
          subheading="Earnings per share growing from $2.97 to $6.43 over five years"
          data={[
            { label: "2019", value: 2.97 },
            { label: "2020", value: 3.28 },
            { label: "2021", value: 5.61 },
            { label: "2022", value: 6.11 },
            { label: "2023", value: 6.43 },
            { label: "2024E", value: 7.00 },
          ]}
          accent={accent}
          yLabel="EPS ($)"
          xLabel="Year"
          highlightIdx={4}
          footnote="AAPL EPS more than doubled from 2019 to 2023 driven by share buybacks, margin expansion, and services revenue growth."
        />
      ),
    },

    // Scene 7 (60s)
    {
      durationInFrames: sec(60),
      render: () => (
        <RealWorldExampleScene
          heading="Reading an AAPL 10 Q in 5 Minutes"
          company="Apple Inc"
          scenario="The 10 Q quarterly filing contains 4 key pages every investor should read: income statement (revenue and EPS), balance sheet (cash and debt), cash flow statement (free cash flow), and management discussion (forward outlook)."
          setupItems={[
            { label: "Revenue this quarter", value: "$94.9B vs $90.1B year ago", color: "#22c55e" },
            { label: "Gross margin", value: "45.2% (expanding)", color: accent },
            { label: "Operating income", value: "$26.1B", color: "#22c55e" },
            { label: "Cash and equivalents", value: "$162B (war chest)", color: "#3b82f6" },
            { label: "Long term debt", value: "$96B (manageable)", color: "#f59e0b" },
          ]}
          outcome="Strong quarter: buy, hold, or watch"
          outcomeDetail="Revenue growth of 5.3 percent year over year with expanding margins and $162B in cash signals financial strength. The debt is fully covered by one and a half quarters of free cash flow. This is a company that funds its own growth."
          outcomeColor="#22c55e"
          accent={accent}
        />
      ),
    },

    // Scene 8 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <MistakeHighlightScene
          heading="Ignoring Debt When Looking at P/E Ratio"
          mistake={{
            label: "Comparing P/E ratios between companies without looking at balance sheet debt",
            detail: "A trader sees Company A at P/E 15x and Company B at P/E 22x and buys Company A thinking it is cheap. But Company A carries $8B in debt with $500M in annual interest expense that is eating the earnings, while Company B has no debt and growing cash. The P/E comparison is apples to oranges.",
          }}
          correction={{
            label: "Use EV/EBITDA to compare companies across different capital structures",
            detail: "Enterprise Value equals market cap plus total debt minus cash. EV/EBITDA neutralizes the effect of debt financing and gives a cleaner comparison. A company with no debt and the same EBITDA as a leveraged peer is genuinely cheaper, even if its P/E looks higher.",
          }}
          insight="Warren Buffett focuses on return on invested capital and free cash flow, not P/E ratios in isolation. A business that earns $10 free cash flow on $100 of capital is far better than one that earns the same $10 on $200 of capital financed with debt."
          accent={accent}
        />
      ),
    },

    // Scene 9 (70s)
    {
      durationInFrames: sec(70),
      render: () => (
        <WorkedExampleScene
          heading="Comparing Two Biotech Stocks by Free Cash Flow"
          subheading="Using FCF instead of earnings to find the financially stronger company"
          company="Biotech Comparison"
          ticker="BIOTECH"
          trades={[
            { day: "Company A screen", event: "BioTech A: P/E 45x but reports GAAP loss due to R and D write offs", action: "GAAP earnings negative, but operating FCF is $800M positive. P/E useless here.", pl: 0, cumPl: 0 },
            { day: "Company B screen", event: "BioTech B: P/E 30x and reports $400M GAAP profit", action: "GAAP profit positive, but $600M in stock based compensation inflates earnings.", pl: 0, cumPl: 0 },
            { day: "FCF analysis A", event: "Company A FCF: $800M on $12B market cap", action: "FCF yield = 800/12,000 = 6.7 percent. Strong cash generation despite GAAP loss.", pl: 800, cumPl: 800 },
            { day: "FCF analysis B", event: "Company B FCF: $200M on $9B market cap", action: "FCF yield = 200/9,000 = 2.2 percent. Weaker actual cash despite better GAAP profit.", pl: 200, cumPl: 1000 },
            { day: "Decision", event: "Company A has 3x the FCF yield at a comparable market cap", action: "Company A is the better fundamental buy despite the GAAP loss headline.", pl: 0, cumPl: 1000 },
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 10 (35s)
    {
      durationInFrames: sec(35),
      render: () => (
        <BulletScene
          heading="Connecting Fundamentals to Earnings Analysis and Options"
          bullets={[
            "Strong fundamental companies command premium P/E because investors pay for certainty",
            "Earnings beats versus misses drive implied volatility and options pricing",
            "Free cash flow growth is the primary driver of long term stock price appreciation",
            "High ROE companies with low debt are the safest underlying stocks for covered calls",
            "Read the 10 Q before any earnings options trade: know what the market expects",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 11 (35s)
    {
      durationInFrames: sec(35),
      render: () => (
        <StatsScene
          heading="S and P 500 Fundamental Benchmarks"
          stats={[
            { label: "S and P 500 P/E", value: "22x historical average", color: accent },
            { label: "S and P 500 EPS growth", value: "8 to 10% per year long term", color: "#22c55e" },
            { label: "S and P 500 FCF yield", value: "3.5 to 4.5% typical range", color: "#f59e0b" },
            { label: "Investment grade ROE", value: "15 to 20% median", color: "#3b82f6" },
          ]}
          accent={accent}
          footnote="Stocks with P/E ratios more than 2x the market average require above average growth rates to justify the premium. Check the PEG ratio to see if growth explains the premium."
        />
      ),
    },

    // Scene 12 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <SummaryScene
          heading="Fundamentals: Know What You Own Before You Trade It"
          takeaways={[
            "P/E ratio measures what you pay per dollar of earnings: AAPL 31x vs S and P 500 22x average",
            "Free cash flow is more reliable than GAAP earnings for measuring real business health",
            "AAPL FCF of $99B funds buybacks, dividends, and acquisitions without issuing debt",
            "Return on equity above 20 percent signals a high quality business with durable advantages",
            "Always read the 10 Q before trading options on earnings: the numbers tell the real story",
          ]}
          accent={accent}
          closingLine="Next: Valuation ratios and how to compare companies across different sectors."
        />
      ),
    },

    // Scene 13 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <RealWorldExampleScene
          heading="AAPL Buybacks: How Share Repurchases Boost EPS Without Revenue Growth"
          company="Apple Inc"
          scenario="AAPL spent $90 billion on share buybacks in fiscal 2023. This reduced shares outstanding from 16.2 billion to 15.4 billion. With the same total net income, EPS rose by 5 percent from buybacks alone with no business growth required."
          setupItems={[
            { label: "Shares outstanding (prior year)", value: "16.2 billion", color: "#94a3b8" },
            { label: "Shares outstanding (after buybacks)", value: "15.4 billion", color: accent },
            { label: "Net income (same both years)", value: "$99.8 billion", color: "#22c55e" },
            { label: "EPS increase from buybacks alone", value: "5.1 percent improvement", color: "#22c55e" },
            { label: "Capital returned to shareholders", value: "$90B buybacks plus $15B dividends", color: "#f59e0b" },
          ]}
          outcome="EPS beats driven partly by financial engineering"
          outcomeDetail="When AAPL reports EPS growth, always check how much came from revenue growth versus buyback driven share count reduction. In FY2023, roughly 30 percent of EPS growth was engineering from buybacks. The business still grew, but the mechanics matter for valuation."
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

// ── ValuationRatios101Long ────────────────────────────────────────────────────
// Lesson: valuation-ratios-101 — "P/E, P/S, P/B, EV/EBITDA, and PEG"

export type ValuationRatios101LongProps = {
  accent?: string;
};

export const ValuationRatios101Long: React.FC<ValuationRatios101LongProps> = ({ accent = "#a855f7" }) => {
  useVideoConfig();

  const scenes: SceneDef[] = [
    // Scene 1 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <TitleScene
          label="Fundamental Analysis"
          title="Valuation Ratios: P/E, P/S, P/B, EV/EBITDA, PEG"
          subtitle="Five ratios that tell you whether a stock is cheap, fair, or expensive for what you get"
          accent={accent}
        />
      ),
    },

    // Scene 2 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <BulletScene
          heading="Five Valuation Ratios and When to Use Each"
          bullets={[
            "P/E (Price to Earnings): use for profitable companies with stable earnings",
            "P/S (Price to Sales): use when earnings are negative or distorted by write offs",
            "P/B (Price to Book): use for banks, insurers, and asset heavy businesses",
            "EV/EBITDA: use to compare companies with different debt levels fairly",
            "PEG (P/E to Growth): use to judge if a high P/E is justified by growth rate",
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
          heading="EV/EBITDA: The Debt Neutral Valuation for AAPL"
          steps={[
            { label: "AAPL market cap", formula: "15.4B shares × $192", result: "$2.96 trillion" },
            { label: "AAPL total debt", formula: "From balance sheet", result: "$108 billion" },
            { label: "AAPL cash and equivalents", formula: "From balance sheet", result: "$162 billion" },
            { label: "Enterprise value", formula: "$2,960B + $108B minus $162B", result: "$2,906 billion", highlight: true },
            { label: "AAPL EBITDA (annual)", formula: "Operating income plus depreciation", result: "$125 billion" },
            { label: "EV/EBITDA ratio", formula: "$2,906B divided by $125B", result: "23.2x", highlight: true },
          ]}
          conclusion="EV/EBITDA of 23x for AAPL is slightly above the S and P 500 average of 17x, reflecting the quality premium investors pay for Apple's brand and ecosystem."
          accent={accent}
        />
      ),
    },

    // Scene 4 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <StatsScene
          heading="Sector Median Valuation Multiples"
          stats={[
            { label: "Technology P/E", value: "28x median", color: "#3b82f6" },
            { label: "Energy P/E", value: "12x median", color: "#f59e0b" },
            { label: "Banks P/B", value: "1.2x median", color: "#22c55e" },
            { label: "SaaS P/S", value: "8x median", color: accent },
          ]}
          accent={accent}
          footnote="Comparing a tech company P/E to an energy company P/E is meaningless. Always compare within sectors using the ratio appropriate for that sector's business model."
        />
      ),
    },

    // Scene 5 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <ComparisonTableScene
          heading="Growth vs Value Valuation Benchmarks"
          subheading="Where these stocks sit relative to sector and market averages"
          columns={["Stock", "P/E", "P/S", "Classification"]}
          rows={[
            { cells: ["AAPL", "31x", "8x", "Quality growth"], winner: 0, highlight: false },
            { cells: ["AMZN", "45x", "3x", "Revenue heavy growth"], winner: 3, highlight: true },
            { cells: ["NVDA", "65x PEG 1.8x", "25x", "High growth premium"], winner: 0 },
            { cells: ["Bank of America", "12x P/B 1.3x", "2.5x", "Value: asset heavy"], winner: 3, highlight: true },
            { cells: ["S and P 500 avg", "22x", "2.3x", "Market benchmark"], winner: 0 },
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
          heading="AAPL P/E Ratio 2019 to 2024: From 20x to 34x"
          subheading="How the market re rated Apple as it pivoted to services and recurring revenue"
          data={[
            { label: "2019", value: 20 },
            { label: "2020", value: 28 },
            { label: "2021", value: 30 },
            { label: "2022", value: 22 },
            { label: "2023", value: 30 },
            { label: "2024", value: 33 },
          ]}
          accent={accent}
          yLabel="P/E Ratio (x)"
          xLabel="Year"
          highlightIdx={5}
          footnote="The 2022 compression to 22x came from rising interest rates. Higher rates reduce the present value of future earnings, compressing P/E multiples across all growth stocks."
        />
      ),
    },

    // Scene 7 (60s)
    {
      durationInFrames: sec(60),
      render: () => (
        <RealWorldExampleScene
          heading="PEG Analysis on NVDA: Does the High P/E Make Sense?"
          company="NVIDIA"
          scenario="NVDA trades at a P/E of 65x, which looks extreme versus the S and P 500 average of 22x. But NVDA is growing EPS at 95 percent per year on AI demand. The PEG ratio adjusts for this growth."
          setupItems={[
            { label: "NVDA P/E ratio", value: "65x", color: "#ef4444" },
            { label: "NVDA 3 year EPS growth rate", value: "95% per year", color: "#22c55e" },
            { label: "PEG ratio", value: "65 divided by 95 = 0.68x", color: accent },
            { label: "PEG below 1.0", value: "Suggests growth more than justifies price", color: "#22c55e" },
            { label: "AAPL PEG comparison", value: "31 P/E divided by 10% growth = 3.1x", color: "#f59e0b" },
          ]}
          outcome="NVDA looks expensive but the PEG says otherwise"
          outcomeDetail="A PEG of 0.68 means NVDA is actually cheap relative to its growth rate. AAPL at PEG 3.1x looks expensive on the same measure. The market is paying 3.1x for each percent of AAPL growth but only 0.68x for each percent of NVDA growth."
          outcomeColor="#22c55e"
          accent={accent}
        />
      ),
    },

    // Scene 8 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <MistakeHighlightScene
          heading="Comparing P/E Ratios Across Different Sectors"
          mistake={{
            label: "Saying a bank at P/E 12x is cheap and a SaaS company at P/E 40x is expensive",
            detail: "Banks have low P/E ratios because their growth is slow and their earnings are cyclical. SaaS companies have high P/E ratios because their revenue is recurring, margins expand with scale, and switching costs are high. Comparing these two P/E ratios is like comparing apples to oil barrels.",
          }}
          correction={{
            label: "Always compare within sector and use the ratio appropriate for the business model",
            detail: "For banks: use P/B and P/TBV. For SaaS: use P/S and EV/revenue. For energy: use P/FCF and EV/EBITDA. For REITs: use P/FFO. Each sector has the right tool. A universal P/E comparison destroys signal.",
          }}
          insight="Warren Buffett buying Occidental Petroleum at a P/E of 8x and Coca Cola at a P/E of 25x simultaneously shows the point. He did not compare them to each other. He compared each one to its own sector, its own history, and its own business model."
          accent={accent}
        />
      ),
    },

    // Scene 9 (70s)
    {
      durationInFrames: sec(70),
      render: () => (
        <WorkedExampleScene
          heading="Screening for Undervalued REITs by P/FFO"
          subheading="Why standard P/E is useless for REITs and what to use instead"
          company="REIT Sector Screener"
          ticker="REIT"
          trades={[
            { day: "Why P/E fails REITs", event: "REITs must distribute 90 percent of income as dividends and take heavy depreciation", action: "GAAP earnings are near zero after depreciation. P/E of 100x or higher is meaningless.", pl: 0, cumPl: 0 },
            { day: "What FFO measures", event: "FFO = Funds From Operations: earnings plus depreciation minus property gains", action: "FFO is the real cash the REIT generates before mandatory payouts.", pl: 0, cumPl: 0 },
            { day: "Realty Income O", event: "P/FFO of 14x vs sector average of 16x. Dividend yield 5.8 percent.", action: "Below sector average P/FFO with above average yield. Potentially undervalued.", pl: 580, cumPl: 580 },
            { day: "VICI Properties", event: "P/FFO of 13x. Gaming REIT with long term triple net leases.", action: "13x P/FFO is near historical low. Strong tenant base. Add to watchlist.", pl: 0, cumPl: 580 },
            { day: "Comparison", event: "Both names below 16x sector average P/FFO with yields above 5 percent", action: "Screen identified two undervalued REITs in 15 minutes using the right metric.", pl: 0, cumPl: 580 },
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 10 (35s)
    {
      durationInFrames: sec(35),
      render: () => (
        <BulletScene
          heading="Connecting Valuation Ratios to DCF and Earnings Trades"
          bullets={[
            "P/E expansion is when investors pay more per dollar of earnings than before: powerful return driver",
            "DCF (Discounted Cash Flow) is the theoretical foundation behind all relative valuation ratios",
            "When the Fed raises rates, discount rates rise and P/E ratios compress across the market",
            "Before an earnings options trade, check if P/E is near historical highs: compression risk is real",
            "PEG below 1.0 often precedes periods of multiple expansion and strong stock outperformance",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 11 (35s)
    {
      durationInFrames: sec(35),
      render: () => (
        <StatsScene
          heading="Ratio Reference Card: Normal Ranges by Sector"
          stats={[
            { label: "AMZN P/S", value: "3x (revenue heavy, P/E misleading)", color: "#f59e0b" },
            { label: "NVDA PEG", value: "1.8x (growth more than justifies premium)", color: "#22c55e" },
            { label: "Bank of America P/B", value: "1.3x (asset heavy, P/E secondary)", color: "#3b82f6" },
            { label: "SaaS sector P/S", value: "8x median (recurring revenue premium)", color: accent },
          ]}
          accent={accent}
          footnote="Energy sector median P/E is 12x reflecting cyclicality and capital intensity. Do not compare energy stocks to tech stocks on P/E without sector adjustment."
        />
      ),
    },

    // Scene 12 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <SummaryScene
          heading="Valuation Ratios: The Right Tool for the Right Business"
          takeaways={[
            "P/E works for stable earners; P/S for unprofitable growth; P/B for asset heavy financials",
            "EV/EBITDA is the most neutral comparison across companies with different debt levels",
            "PEG below 1.0 signals growth is outpacing the price premium investors are paying",
            "NVDA PEG of 1.8 and AAPL PEG of 3.1 show NVDA is cheaper on a growth adjusted basis",
            "Never compare valuation ratios across sectors: use sector medians as your benchmark always",
          ]}
          accent={accent}
          closingLine="You now have the full toolkit: from what a stock is to how to value any company in any sector."
        />
      ),
    },

    // Scene 13 (45s)
    {
      durationInFrames: sec(45),
      render: () => (
        <RealWorldExampleScene
          heading="Buffett Buying OXY at Low P/E: Value Investing in Practice"
          company="Occidental Petroleum"
          scenario="In 2022, Warren Buffett bought over $10 billion in Occidental Petroleum (OXY) at an average price near $55 per share. OXY traded at a P/E of 8x versus the S and P 500 at 20x. Energy sector median was 12x. At 8x with strong free cash flow yield of 12 percent, OXY screened as deeply undervalued."
          setupItems={[
            { label: "OXY P/E at purchase", value: "8x (vs energy sector 12x)", color: "#22c55e" },
            { label: "OXY FCF yield", value: "12 percent (very high)", color: "#22c55e" },
            { label: "Buffett avg purchase price", value: "~$55 per share", color: accent },
            { label: "OXY price 18 months later", value: "$68 per share (plus dividends)", color: "#22c55e" },
            { label: "Return including preferred", value: "Estimated 40 percent total return", color: "#22c55e" },
          ]}
          outcome="Sector appropriate P/E identified a value opportunity"
          outcomeDetail="Buffett did not compare OXY to NVDA or AAPL on P/E. He compared OXY to its own sector history and to oil price assumptions. At $55 with oil above $80, the FCF yield made it compelling. This is how to use valuation ratios: in context, within sector, with the right denominator."
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

// ── EarningsAnalysis101Long ───────────────────────────────────────────────────
// Lesson: earnings-analysis-101 — "Reading Earnings Reports"

export type EarningsAnalysis101LongProps = {
  accent?: string;
};

export const EarningsAnalysis101Long: React.FC<EarningsAnalysis101LongProps> = ({ accent = "#ef4444" }) => {
  useVideoConfig();

  const scenes: SceneDef[] = [
    // Scene 1 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <TitleScene
          label="Earnings Season"
          title="Reading Earnings Reports"
          subtitle="EPS beats, revenue guidance, IV crush, and how the market reacts with real AAPL, META, and NVDA data"
          accent={accent}
        />
      ),
    },

    // Scene 2 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <BulletScene
          heading="Anatomy of an Earnings Report"
          bullets={[
            "EPS (earnings per share): net income divided by diluted shares outstanding",
            "Revenue: total sales in the quarter, compared against analyst consensus",
            "Guidance: management forecast for next quarter or full year revenue and EPS",
            "Conference call: CEO and CFO color on trends, margins, and competitive environment",
            "IV crush: implied volatility collapses the moment earnings are released",
          ]}
          accent={accent}
          icon="📋"
        />
      ),
    },

    // Scene 3 (45s)
    {
      durationInFrames: sec(45),
      render: () => (
        <SetupScene
          heading="How to Read the Headline Numbers"
          items={[
            { label: "EPS Estimate", value: "Wall Street analyst consensus (e.g. $2.10 for AAPL Q1 2024)", color: "#94a3b8" },
            { label: "EPS Actual", value: "Reported result ($2.18 AAPL Q1 2024)", color: "#22c55e" },
            { label: "EPS Surprise", value: "+$0.08 or +3.8 percent beat", color: "#22c55e" },
            { label: "Revenue Estimate", value: "$119.7B consensus for AAPL Q1 2024", color: "#94a3b8" },
            { label: "Revenue Actual", value: "$119.6B (missed by $100M)", color: accent },
            { label: "Stock reaction", value: "AAPL fell 3 percent despite EPS beat on revenue miss and weak China guidance", color: accent },
          ]}
          accent={accent}
          description="The market trades on the full picture: EPS, revenue, and most critically, forward guidance. An EPS beat with a revenue miss or weak outlook can still send the stock lower."
        />
      ),
    },

    // Scene 4 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <CalculationScene
          heading="EPS Surprise Percentage: AAPL Q1 2024"
          steps={[
            { label: "EPS estimate (consensus)", formula: "Wall Street analyst average forecast", result: "$2.10" },
            { label: "EPS actual reported", formula: "Diluted net income divided by shares", result: "$2.18" },
            { label: "EPS surprise amount", formula: "$2.18 minus $2.10", result: "+$0.08" },
            { label: "EPS surprise percent", formula: "(actual minus estimate) divided by |estimate| times 100", result: "+3.8%", highlight: true },
            { label: "Revenue vs estimate", formula: "$119.6B actual vs $119.7B estimate", result: "Miss of $100M (0.08%)", color: "#ef4444" },
            { label: "Stock reaction", formula: "Despite EPS beat, revenue miss plus China concerns", result: "AAPL fell 3 percent next day", color: "#ef4444" },
          ]}
          conclusion="A 3.8 percent EPS beat could not overcome a revenue miss and negative China revenue guidance. The market punishes disappointment in guidance more than it rewards EPS surprises."
          accent={accent}
        />
      ),
    },

    // Scene 5 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <StatsScene
          heading="Earnings Reactions: AAPL, META, NVDA Q1 2024"
          stats={[
            { label: "AAPL: EPS beat 3.8%, revenue miss 0.08%", value: "Down 3%", color: accent },
            { label: "META: EPS beat 9%, revenue beat 0.8%", value: "Up 12%", color: "#22c55e" },
            { label: "NVDA Q4 2024: EPS beat 11.2%", value: "Up 16%", color: "#22c55e" },
          ]}
          accent={accent}
          footnote="AAPL: revenue $119.6B vs $119.7B estimate plus weak China. META EPS $4.71 vs $4.32 estimate, revenue $36.5B vs $36.2B. NVDA EPS $5.16 vs $4.64 estimate. Guidance matters as much as the headline beat."
        />
      ),
    },

    // Scene 6 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <SvgLineChartScene
          heading="AAPL Stock Around Earnings: 3 Quarters of IV Spikes"
          subheading="Stock price pattern before and after each earnings event"
          data={[
            { label: "6 wks before Q1", value: 185 },
            { label: "2 wks before Q1", value: 191 },
            { label: "Earnings Q1", value: 188 },
            { label: "2 wks after Q1", value: 174 },
            { label: "2 wks before Q2", value: 180 },
            { label: "Earnings Q2", value: 191 },
            { label: "2 wks after Q2", value: 195 },
            { label: "2 wks before Q3", value: 193 },
            { label: "Earnings Q3", value: 197 },
            { label: "2 wks after Q3", value: 195 },
          ]}
          accent={accent}
          yLabel="Price ($)"
          xLabel="Timeline"
          highlightIdx={3}
          footnote="IV spikes to 35 to 50 percent the week before earnings then crushes back to 20 to 25 percent the morning after the report. Option buyers pay a premium for event risk that vanishes instantly."
        />
      ),
    },

    // Scene 7 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <ComparisonTableScene
          heading="Four Earnings Outcomes and Typical Market Reactions"
          subheading="Based on historical S and P 500 earnings reactions"
          columns={["Outcome", "EPS vs Est", "Revenue vs Est", "Guidance", "Typical Move"]}
          rows={[
            { cells: ["Clean beat", "Above", "Above", "Raised", "Up 4 to 15%"], winner: 4, highlight: true },
            { cells: ["EPS beat only", "Above", "Miss", "In line", "Up 0 to 3% or flat"], winner: 3 },
            { cells: ["In line", "Meets", "Meets", "In line", "Up or down 1 to 2%"], winner: 3 },
            { cells: ["Guidance cut", "Beat or miss", "Any", "Lowered", "Down 5 to 20%"], winner: 4 },
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 8 (60s)
    {
      durationInFrames: sec(60),
      render: () => (
        <RealWorldExampleScene
          heading="NVDA Earnings Play with Options: Q4 2024"
          company="NVIDIA Corporation"
          scenario="NVDA reports Q4 2024 earnings. EPS estimate was $4.64. Actual EPS came in at $5.16, an 11.2 percent beat. Revenue surpassed estimates by 5.6 percent. Data center revenue doubled year over year. A trader bought the $600 call expiring 2 days after earnings for $8.00 premium before the report."
          setupItems={[
            { label: "NVDA price before earnings", value: "$620", color: "#94a3b8" },
            { label: "EPS beat magnitude", value: "+11.2 percent ($5.16 vs $4.64 est)", color: "#22c55e" },
            { label: "Call strike purchased", value: "$600 call, 2 days to expiry", color: accent },
            { label: "Premium paid", value: "$8.00 per share ($800 per contract)", color: "#ef4444" },
            { label: "NVDA next day price", value: "$719 (up 16 percent)", color: "#22c55e" },
            { label: "Call intrinsic value at $719", value: "$119.00 per share", color: "#22c55e" },
          ]}
          outcome="$800 into $11,900 in 24 hours on a massive EPS beat"
          outcomeDetail="The call went from $8.00 to over $119. But this trade had a 50 to 60 percent chance of total loss. If NVDA had only met estimates or given flat guidance, the call would have expired worthless due to IV crush. High reward means high risk of losing the entire premium."
          outcomeColor="#22c55e"
          accent={accent}
        />
      ),
    },

    // Scene 9 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <MistakeHighlightScene
          heading="Ignoring Guidance and Focusing Only on EPS"
          mistake={{
            label: "Buying calls on an EPS beat without reading the guidance section",
            detail: "A trader sees AAPL beat EPS by 3.8 percent and buys calls expecting a rally. AAPL drops 3 percent because China revenue fell 13 percent year over year and management guided next quarter below consensus. The EPS beat was irrelevant against the forward guidance miss.",
          }}
          correction={{
            label: "Read the guidance section and conference call transcript before taking a position",
            detail: "Guidance is the forward-looking signal markets price immediately. An EPS beat on a revenue miss with lowered guidance is bearish regardless of the headline. Always check: what did management say about NEXT quarter?"
          }}
          insight="Rule: the guidance section of the earnings release is more important than the EPS headline. A beat with a cut to next quarter guidance will send most stocks lower."
          accent={accent}
        />
      ),
    },

    // Scene 10 (70s)
    {
      durationInFrames: sec(70),
      render: () => (
        <WorkedExampleScene
          heading="Full Earnings Week Plan: Before, During, and After"
          subheading="NVDA earnings coming in 10 days: a complete preparation framework"
          company="NVIDIA Corporation"
          ticker="NVDA"
          trades={[
            { day: "10 days before", event: "Note earnings date and set IV watch", action: "Log current IV rank (e.g. 45%). Set alert for when IV crosses 70% (elevated)", pl: 0, cumPl: 0 },
            { day: "5 days before", event: "Review analyst estimates and whisper numbers", action: "EPS estimate $4.64. Revenue estimate $22.1B. Data center key metric. Read prior quarter transcript.", pl: 0, cumPl: 0 },
            { day: "2 days before", event: "Check options market implied move", action: "Straddle at-the-money: $620 call plus $620 put = $42. Implied move = 6.8%", pl: 0, cumPl: 0 },
            { day: "Night before", event: "Decide: trade into earnings or wait for post report", action: "If trading: define max risk. Prefer spreads over naked long options to reduce IV crush impact.", pl: 0, cumPl: 0 },
            { day: "Earnings day", event: "Report released after market close. EPS $5.16, beat 11.2%", action: "Revenue beat 5.6%. Guidance raised. Stock gaps up 16% in after hours.", pl: 1190, cumPl: 1190 },
            { day: "Day after", event: "IV crushes from 80% back to 35%", action: "Any long options lost 50%+ in IV even if directionally correct. Position closed.", pl: 400, cumPl: 1590 },
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
          heading="Connecting Earnings to Options, IV, and Stock Selection"
          bullets={[
            "Earnings are the single largest catalyst for individual stock implied volatility spikes",
            "IV crush destroys long option value even when the direction is correct",
            "Iron condors and short strangles profit from IV crush if the move stays inside the expected range",
            "Guidance quality determines whether an EPS beat becomes a buy or sell event",
            "Annual earnings cycles matter: Q4 reports include next year guidance and are highest impact",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 12 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <SummaryScene
          heading="Earnings Analysis: What to Remember"
          bullets={[
            "EPS surprise percent = (actual minus estimate) divided by |estimate| times 100",
            "Revenue miss can wipe out an EPS beat: AAPL fell 3% on Q1 2024 beat plus miss combo",
            "Forward guidance outweighs backward-looking EPS in stock price reactions",
            "IV crushes immediately after earnings: option sellers profit, option buyers must be right on direction AND magnitude",
            "Clean beats (EPS, revenue, and raised guidance) produce the strongest reactions: META up 12%, NVDA up 16%",
          ]}
          accent={accent}
          closingLine="Earnings season is volatility season. Know the anatomy of a report, read the guidance, and size your risk before the number drops."
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

// ── RsiMacdMasteryLong ────────────────────────────────────────────────────────
// Lesson: rsi-macd-mastery — "RSI and MACD: Momentum Indicators"

export type RsiMacdMasteryLongProps = {
  accent?: string;
};

export const RsiMacdMasteryLong: React.FC<RsiMacdMasteryLongProps> = ({ accent = "#8b5cf6" }) => {
  useVideoConfig();

  const scenes: SceneDef[] = [
    // Scene 1 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <TitleScene
          label="Technical Analysis"
          title="RSI and MACD: Momentum Mastery"
          subtitle="Divergence, signal line crossovers, histogram analysis, and combining both indicators with real AAPL, SPY, and NVDA data"
          accent={accent}
        />
      ),
    },

    // Scene 2 (45s)
    {
      durationInFrames: sec(45),
      render: () => (
        <BulletScene
          heading="RSI: What It Measures and How to Read It"
          bullets={[
            "RSI (Relative Strength Index) measures momentum on a 0 to 100 scale over 14 periods",
            "Above 70: overbought signal. Below 30: oversold signal. Neutral zone: 40 to 60",
            "RSI divergence: price makes new high but RSI makes lower high = weakening momentum",
            "AAPL RSI hit 78 in November 2021, a warning signal before a 30 percent correction",
            "SPY RSI hit 28 in October 2022, signaling extreme oversold before a 25 percent rally",
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
          heading="RSI Formula with 5 Sample Closes"
          steps={[
            { label: "5 sample closes", formula: "100, 102, 101, 104, 107", result: "4 up days, 1 down day" },
            { label: "Average gain (up days)", formula: "(2 + 0 + 3 + 3) divided by 5", result: "1.60 per period" },
            { label: "Average loss (down days)", formula: "(1) divided by 5", result: "0.20 per period" },
            { label: "Relative Strength (RS)", formula: "Average gain divided by average loss = 1.60 / 0.20", result: "RS = 8.0" },
            { label: "RSI formula", formula: "100 minus (100 divided by (1 plus RS))", result: "100 minus 11.1 = 88.9", highlight: true },
            { label: "Interpretation", formula: "RSI of 88.9 is deeply overbought", result: "Caution: momentum may be exhausted", color: accent },
          ]}
          conclusion="Real RSI uses smoothed averages over 14 periods. This 5-bar example shows the core math: compare average gains to average losses and normalize to 0 to 100."
          accent={accent}
        />
      ),
    },

    // Scene 4 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <SetupScene
          heading="MACD Anatomy: Three Components"
          items={[
            { label: "MACD Line", value: "12-period EMA minus 26-period EMA", color: "#22c55e" },
            { label: "Signal Line", value: "9-period EMA of the MACD Line", color: accent },
            { label: "Histogram", value: "MACD Line minus Signal Line (momentum acceleration)", color: "#f59e0b" },
            { label: "Bullish crossover", value: "MACD Line crosses above Signal Line from below", color: "#22c55e" },
            { label: "Bearish crossover", value: "MACD Line crosses below Signal Line from above", color: "#ef4444" },
            { label: "Zero line cross", value: "MACD crossing zero = trend change confirmation", color: "#94a3b8" },
          ]}
          accent={accent}
          description="MACD measures the distance between two exponential moving averages. When the faster 12 EMA moves away from the slower 26 EMA, momentum is accelerating. The signal line smooths MACD for cleaner crossover signals."
        />
      ),
    },

    // Scene 5 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <SvgLineChartScene
          heading="AAPL RSI Over 2021 to 2022: Overbought Signal Before 30 Percent Correction"
          subheading="AAPL RSI monthly readings showing the November 2021 peak at 78 and October 2022 trough at 28"
          data={[
            { label: "Jan 2021", value: 40 },
            { label: "Mar 2021", value: 45 },
            { label: "May 2021", value: 50 },
            { label: "Jul 2021", value: 55 },
            { label: "Sep 2021", value: 65 },
            { label: "Nov 2021", value: 78 },
            { label: "Jan 2022", value: 70 },
            { label: "Mar 2022", value: 58 },
            { label: "May 2022", value: 45 },
            { label: "Jul 2022", value: 38 },
            { label: "Oct 2022", value: 28 },
          ]}
          accent={accent}
          yLabel="RSI Value"
          xLabel="Month"
          highlightIdx={5}
          footnote="RSI 78 in November 2021 was a multi-month high reading. AAPL peaked near $180 then fell 30 percent to $124 by June 2022. RSI 28 in October 2022 marked the bottom before a 25 percent rally."
        />
      ),
    },

    // Scene 6 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <ComparisonTableScene
          heading="RSI vs MACD: Different Momentum Tools for Different Signals"
          subheading="When to use each indicator and what they measure"
          columns={["Attribute", "RSI", "MACD"]}
          rows={[
            { cells: ["What it measures", "Speed of price change (momentum)", "Distance between two EMAs (trend strength)"], highlight: true },
            { cells: ["Key signals", "Overbought 70, oversold 30, divergence", "Signal line crossover, zero cross, histogram"], winner: 1 },
            { cells: ["Lag", "Low lag (14 periods)", "Moderate lag (26 periods)"], winner: 1 },
            { cells: ["Best in", "Ranging markets with clear reversals", "Trending markets with sustained moves"], winner: 2 },
            { cells: ["Weakness", "Can stay overbought for months in uptrend", "Generates false crossovers in choppy markets"], winner: 1 },
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 7 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <StatsScene
          heading="NVDA MACD Bullish Crossover: January 2023 to December 2023"
          stats={[
            { label: "NVDA price at MACD crossover (Jan 2023)", value: "$150", color: "#22c55e" },
            { label: "NVDA price December 2023", value: "$495", color: "#22c55e" },
            { label: "Return in 12 months", value: "+230%", color: "#22c55e" },
            { label: "QQQ MACD bearish cross Jan 2022", value: "QQQ fell 35%", color: accent },
          ]}
          accent={accent}
          footnote="NVDA MACD crossed bullish in January 2023 when the 12 EMA crossed above the 26 EMA as AI chip demand became clear. QQQ MACD crossed bearish in January 2022 at the start of the rate hike cycle. Neither signal is perfect but both aligned with major trend shifts."
        />
      ),
    },

    // Scene 8 (60s)
    {
      durationInFrames: sec(60),
      render: () => (
        <RealWorldExampleScene
          heading="RSI Divergence Trade on SPY: October 2022"
          company="SPDR S and P 500 ETF"
          scenario="SPY made a new price low in October 2022 near $357. However, RSI only dropped to 28, whereas in June 2022 when SPY was higher at $362, RSI had reached 30. Price lower but RSI higher = bullish divergence. This divergence suggested the selling was losing momentum even as new lows were being printed."
          setupItems={[
            { label: "SPY price low June 2022", value: "$362", color: "#94a3b8" },
            { label: "RSI at June 2022 low", value: "30 (oversold)", color: "#ef4444" },
            { label: "SPY price low Oct 2022", value: "$357 (new low)", color: "#94a3b8" },
            { label: "RSI at Oct 2022 low", value: "28 (higher than June reading)", color: "#22c55e" },
            { label: "Bullish divergence signal", value: "Lower price, higher RSI = momentum slowing", color: "#22c55e" },
            { label: "SPY 6 months after Oct 2022", value: "$425 (up 19%)", color: "#22c55e" },
          ]}
          outcome="Divergence identified the bear market bottom before the 25 percent rally"
          outcomeDetail="A trader using bullish RSI divergence plus MACD histogram flipping positive in November 2022 had two confirming signals to go long SPY. The risk was SPY continuing lower. Stop loss below $350."
          outcomeColor="#22c55e"
          accent={accent}
        />
      ),
    },

    // Scene 9 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <MistakeHighlightScene
          heading="Using RSI Overbought Signals in Strong Uptrends"
          mistake={{
            label: "Shorting NVDA every time RSI crossed above 70 in 2023",
            detail: "NVDA RSI crossed above 70 in February 2023 at $200. A trader shorts expecting a reversal. NVDA RSI stayed above 70 for 8 weeks while the stock ran from $200 to $420. In a strong trend, RSI can stay overbought for months and the short loses 100 percent before stopping out.",
          }}
          correction={{
            label: "Use RSI divergence signals, not absolute levels, in trending markets",
            detail: "In strong uptrends, RSI above 70 is a sign of strength, not an automatic sell signal. Wait for RSI to make a lower high while price makes a higher high (bearish divergence) before considering a reversal trade."
          }}
          insight="Rule: RSI overbought and oversold levels work best in ranging markets. In trending markets, use RSI divergence and MACD crossovers instead of absolute levels."
          accent={accent}
        />
      ),
    },

    // Scene 10 (70s)
    {
      durationInFrames: sec(70),
      render: () => (
        <WorkedExampleScene
          heading="Building a RSI Plus MACD Entry Checklist"
          subheading="Using both indicators together to filter higher probability entries"
          company="SPDR S and P 500 ETF"
          ticker="SPY"
          trades={[
            { day: "Step 1", event: "Check the trend on the daily chart (20 SMA vs 50 SMA)", action: "SPY: 20 SMA above 50 SMA. Trend is up. Only look for long entries.", pl: 0, cumPl: 0 },
            { day: "Step 2", event: "RSI check: is RSI between 40 and 60 (neutral pullback zone)?", action: "SPY RSI dipped to 44 on a 3-day pullback. In the neutral range. Green light.", pl: 0, cumPl: 0 },
            { day: "Step 3", event: "MACD check: is MACD histogram turning positive from below zero?", action: "MACD histogram just crossed from negative 0.3 to positive 0.1. Momentum shifting up.", pl: 0, cumPl: 0 },
            { day: "Step 4", event: "Entry signal: RSI neutral plus MACD histogram positive flip", action: "Both confirmed. Buy SPY at $445. Stop loss at $438 (below 20 SMA support).", pl: -4450, cumPl: -4450 },
            { day: "Step 5", event: "RSI climbs to 62, MACD histogram expanding positive", action: "Both indicators confirming uptrend continuation. Hold position.", pl: 0, cumPl: -4450 },
            { day: "Step 6", event: "RSI crosses 70 and MACD histogram begins shrinking", action: "Warning signal. Tighten stop to breakeven. Exit at $458 as RSI shows divergence.", pl: 1300, cumPl: -3150 },
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
          heading="Connecting RSI and MACD to Moving Averages and Bollinger Bands"
          bullets={[
            "RSI complements Bollinger Band analysis: oversold RSI at lower band = strong buy signal",
            "MACD crossovers align with 20 SMA and 50 SMA crossovers for trend confirmation",
            "Volume should confirm MACD crossovers: high volume crossover is more reliable than low volume",
            "RSI divergence works on all timeframes: 5-minute, daily, and weekly charts",
            "Combining three indicators (RSI, MACD, Bollinger Bands) reduces false signals significantly",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 12 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <SummaryScene
          heading="RSI and MACD Mastery: Core Takeaways"
          bullets={[
            "RSI = 100 minus (100 divided by (1 plus average gain divided by average loss)) over 14 periods",
            "NVDA MACD bullish cross Jan 2023: stock went from $150 to $495 in 12 months",
            "SPY RSI divergence Oct 2022 (lower price, higher RSI) identified the bear market bottom",
            "Do NOT short RSI overbought in strong trends: NVDA stayed above 70 for 8 weeks in 2023",
            "Best entries: RSI neutral pullback (40 to 60) plus MACD histogram flipping positive in an uptrend",
          ]}
          accent={accent}
          closingLine="RSI tells you momentum speed. MACD tells you trend direction. Use both together and you have two independent confirmation signals for every entry."
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

// ── BollingerVolume101Long ────────────────────────────────────────────────────
// Lesson: bollinger-volume-101 — "Bollinger Bands and Volume Analysis"

export type BollingerVolume101LongProps = {
  accent?: string;
};

export const BollingerVolume101Long: React.FC<BollingerVolume101LongProps> = ({ accent = "#0ea5e9" }) => {
  useVideoConfig();

  const scenes: SceneDef[] = [
    // Scene 1 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <TitleScene
          label="Technical Analysis"
          title="Bollinger Bands and Volume"
          subtitle="Bandwidth squeeze, breakout confirmation, and OBV analysis with real AAPL, TSLA, and SPY data"
          accent={accent}
        />
      ),
    },

    // Scene 2 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <BulletScene
          heading="Bollinger Bands: Three Lines That Measure Volatility"
          bullets={[
            "Middle band: 20-period simple moving average of closing prices",
            "Upper band: middle band plus 2 standard deviations",
            "Lower band: middle band minus 2 standard deviations",
            "When bands narrow (squeeze), the market is coiling for a breakout",
            "When bands widen dramatically, a volatile move is already underway",
          ]}
          accent={accent}
          icon="📉"
        />
      ),
    },

    // Scene 3 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <CalculationScene
          heading="Upper Bollinger Band Calculation: AAPL Example"
          steps={[
            { label: "AAPL 20-day SMA", formula: "Average of last 20 closing prices", result: "$189.50" },
            { label: "Standard deviation (20 days)", formula: "Measure of price spread around the average", result: "$3.20" },
            { label: "Upper band", formula: "$189.50 plus (2 times $3.20)", result: "$195.90", highlight: true },
            { label: "Lower band", formula: "$189.50 minus (2 times $3.20)", result: "$183.10", highlight: true },
            { label: "Band width", formula: "($195.90 minus $183.10) divided by $189.50", result: "6.7 percent" },
            { label: "Interpretation", formula: "Price above upper band = extended, below lower band = oversold", result: "Price at $196.50 = outside upper band", color: accent },
          ]}
          conclusion="Approximately 95 percent of price action falls within the bands when using 2 standard deviations. A close outside the bands is statistically unusual and often signals exhaustion or the start of a breakout."
          accent={accent}
        />
      ),
    },

    // Scene 4 (45s)
    {
      durationInFrames: sec(45),
      render: () => (
        <SetupScene
          heading="Bandwidth Formula: Measuring the Squeeze"
          items={[
            { label: "Bandwidth formula", value: "(Upper band minus Lower band) divided by Middle band", color: "#22c55e" },
            { label: "Normal bandwidth", value: "0.10 to 0.20 (10 to 20 percent range)", color: "#94a3b8" },
            { label: "Narrow squeeze", value: "Below 0.06 = extreme compression, breakout likely", color: accent },
            { label: "AAPL Dec 2023 squeeze", value: "Bandwidth reached 0.05 for 3 weeks, then broke out 18%", color: "#22c55e" },
            { label: "TSLA Aug 2023 squeeze", value: "Bandwidth 0.05 extreme, then rallied 40% in 6 weeks", color: "#22c55e" },
            { label: "Direction not predictable", value: "Squeeze only signals coiling, not the direction of breakout", color: "#f59e0b" },
          ]}
          accent={accent}
          description="Bandwidth is the key metric for squeeze detection. When it reaches extreme lows (0.05 or below), a large directional move is pending. Volume confirms which direction the breakout takes."
        />
      ),
    },

    // Scene 5 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <SvgLineChartScene
          heading="AAPL Bollinger Band Width: Squeeze in December 2023 Then 18 Percent Breakout"
          subheading="AAPL weekly Bollinger bandwidth showing compression then expansion"
          data={[
            { label: "Oct W1", value: 12.5 },
            { label: "Oct W2", value: 11.0 },
            { label: "Oct W3", value: 9.5 },
            { label: "Nov W1", value: 8.2 },
            { label: "Nov W2", value: 7.0 },
            { label: "Nov W3", value: 6.0 },
            { label: "Nov W4", value: 5.2 },
            { label: "Dec W1", value: 4.8 },
            { label: "Dec W2", value: 5.0 },
            { label: "Dec W3", value: 7.5 },
            { label: "Dec W4", value: 11.2 },
            { label: "Jan W2", value: 16.8 },
          ]}
          accent={accent}
          yLabel="Band Width (%)"
          xLabel="Week"
          highlightIdx={7}
          footnote="Bandwidth compressed to 4.8 percent in early December 2023 (a multi-year low). Volume surged on the breakout week. AAPL went from $189 to $222 over the next 3 weeks."
        />
      ),
    },

    // Scene 6 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <ComparisonTableScene
          heading="Three Bollinger Band Market States"
          subheading="How to trade each band configuration"
          columns={["State", "Bandwidth", "What It Means", "Trading Approach"]}
          rows={[
            { cells: ["Tight squeeze", "Below 0.06", "Coiling before big move", "Wait for breakout with volume confirmation"], highlight: true },
            { cells: ["Normal range", "0.10 to 0.18", "Regular volatility regime", "Mean reversion at upper and lower bands"], winner: 2 },
            { cells: ["Band walk", "0.15 to 0.25 steady", "Strong trend, price rides band", "Hold trend, do not fade the band touch"], winner: 3 },
            { cells: ["Wide expansion", "Above 0.25", "Volatile move underway", "Caution, late entry, wait for compression"], winner: 4 },
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 7 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <StatsScene
          heading="Squeeze Breakout Results: AAPL, TSLA, and QQQ"
          stats={[
            { label: "AAPL squeeze (Dec 2023, 3-week squeeze)", value: "+18% in 3 weeks", color: "#22c55e" },
            { label: "TSLA squeeze (Aug 2023, bandwidth 0.05)", value: "+40% in 6 weeks", color: "#22c55e" },
            { label: "QQQ squeeze (Oct 2023)", value: "+12% in 4 weeks", color: "#22c55e" },
          ]}
          accent={accent}
          footnote="Squeeze breakouts confirmed by above-average volume have historically shown 2 to 3 times the average weekly return in the following 4 weeks. Volume is the critical filter: a squeeze breakout on light volume often fails and reverses."
        />
      ),
    },

    // Scene 8 (60s)
    {
      durationInFrames: sec(60),
      render: () => (
        <RealWorldExampleScene
          heading="AAPL Bollinger Squeeze Breakout Trade: December 2023"
          company="Apple Inc"
          scenario="AAPL consolidated for 3 weeks in December 2023 with bandwidth compressing to 0.05, a multi-year low. On December 18, AAPL closed above the upper Bollinger Band at $197 on 2.5 times average volume. A trader recognizes the squeeze breakout signal."
          setupItems={[
            { label: "AAPL price at breakout day", value: "$197 (close above upper band)", color: "#22c55e" },
            { label: "Bollinger bandwidth", value: "0.05 (extreme squeeze)", color: accent },
            { label: "Volume on breakout day", value: "2.5x average daily volume", color: "#22c55e" },
            { label: "Entry: buy AAPL at close", value: "$197.00", color: accent },
            { label: "Stop loss: below middle band", value: "$189.50 (20-day SMA)", color: "#ef4444" },
            { label: "Target: 2 times risk reward", value: "$212 (if risk is $7.50, target $15 gain)", color: "#22c55e" },
          ]}
          outcome="AAPL reached $222 in 3 weeks, hitting 2x target and beyond"
          outcomeDetail="The combination of extreme bandwidth compression, a close above the upper band, and above-average volume confirmed the squeeze breakout. Stop at $189.50 was never triggered. Position closed at $212 for a $15 per share gain, or 7.6 percent return in 3 weeks."
          outcomeColor="#22c55e"
          accent={accent}
        />
      ),
    },

    // Scene 9 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <MistakeHighlightScene
          heading="Trading Every Band Touch Without Volume Confirmation"
          mistake={{
            label: "Shorting AAPL every time it touched the upper Bollinger Band in a strong uptrend",
            detail: "During AAPL's 2023 bull run, the price would touch and walk along the upper Bollinger Band for weeks at a time. A trader shorting every upper band touch would have been stopped out 6 times in a row as AAPL climbed from $140 to $195.",
          }}
          correction={{
            label: "Only trade band touches when combined with a volume and momentum divergence signal",
            detail: "An upper band touch in a band walk uptrend is a continuation signal, not a reversal signal. Short at the upper band only when RSI shows bearish divergence AND volume is declining on the touch, indicating institutional selling."
          }}
          insight="Rule: Bollinger Bands measure volatility, not direction. A squeeze gives you timing. A band touch gives context. Volume and RSI tell you whether to fade or follow."
          accent={accent}
        />
      ),
    },

    // Scene 10 (70s)
    {
      durationInFrames: sec(70),
      render: () => (
        <WorkedExampleScene
          heading="OBV Divergence Confirming a SPY Breakout: March 2024"
          subheading="On-Balance Volume rising while price was flat = institutional accumulation signal"
          company="SPDR S and P 500 ETF"
          ticker="SPY"
          trades={[
            { day: "Feb 2024", event: "SPY consolidating near $500, Bollinger bandwidth narrow at 0.06", action: "Price flat for 3 weeks. Watching for breakout signal.", pl: 0, cumPl: 0 },
            { day: "Feb W3", event: "OBV begins rising while SPY price holds flat", action: "Rising OBV means more volume on up days than down days. Institutional buying.", pl: 0, cumPl: 0 },
            { day: "Feb W4", event: "OBV makes 3-week high while SPY still near $500", action: "Bullish OBV divergence: accumulation happening below the surface.", pl: 0, cumPl: 0 },
            { day: "Mar W1", event: "SPY closes above upper Bollinger Band at $511 on above average volume", action: "Squeeze breakout confirmed by OBV divergence. Enter long at $511.", pl: -51100, cumPl: -51100 },
            { day: "Mar W2", event: "SPY rallies to $519, OBV continuing higher", action: "Both price and OBV confirming. Hold position.", pl: 0, cumPl: -51100 },
            { day: "Mar W3", event: "SPY hits $524, Bollinger bands widening significantly", action: "Target reached. Exit at $524. Return: 2.5% in 3 weeks from $511 entry.", pl: 1300, cumPl: -49800 },
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
          heading="Connecting Bollinger Bands and Volume to RSI and MACD"
          bullets={[
            "Bollinger squeeze plus RSI in neutral zone (45 to 55) = highest quality breakout setup",
            "MACD bullish crossover on the day of a Bollinger breakout adds strong confirmation",
            "OBV rising during a price squeeze = institutional accumulation before a markup",
            "Declining OBV during a price squeeze = distribution, watch for breakdown not breakout",
            "Three indicators together (Bollinger, RSI, MACD) reduce false signals by filtering for confirmation",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 12 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <SummaryScene
          heading="Bollinger Bands and Volume: Key Takeaways"
          bullets={[
            "Upper band = 20 SMA plus 2 standard deviations. Lower band = 20 SMA minus 2 standard deviations",
            "Bandwidth below 0.06 signals a squeeze: a large directional move is pending",
            "AAPL Dec 2023 squeeze to 0.05 bandwidth preceded an 18% breakout in 3 weeks",
            "TSLA Aug 2023 extreme squeeze (0.05) produced a 40% rally in 6 weeks",
            "OBV rising during a flat price = accumulation signal that confirms the impending breakout",
          ]}
          accent={accent}
          closingLine="Bollinger Bands show you when the market is coiling. Volume shows you who is building the position. Together, they tell you when a breakout is real."
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

// ── PfBudgeting101Long ────────────────────────────────────────────────────────
// Lesson: pf-budgeting-101 — "Budgeting Methods and the 50/30/20 Rule"

export type PfBudgeting101LongProps = {
  accent?: string;
};

export const PfBudgeting101Long: React.FC<PfBudgeting101LongProps> = ({ accent = "#10b981" }) => {
  useVideoConfig();

  const scenes: SceneDef[] = [
    // Scene 1 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <TitleScene
          label="Personal Finance"
          title="Budgeting Methods and the 50/30/20 Rule"
          subtitle="Zero-based budgeting, expense tracking, emergency fund basics, and the math behind financial freedom with real US household data"
          accent={accent}
        />
      ),
    },

    // Scene 2 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <BulletScene
          heading="Four Budgeting Methods: Pick the One That Sticks"
          bullets={[
            "50/30/20: 50% needs, 30% wants, 20% savings. Simple and flexible.",
            "Zero-based: every dollar is assigned a job. Income minus all allocations equals zero.",
            "Envelope method: physical or digital envelopes limit spending in each category",
            "Pay-yourself-first: savings come out automatically before any spending decision",
            "All four work. The best budget is the one you actually review every month.",
          ]}
          accent={accent}
          icon="💰"
        />
      ),
    },

    // Scene 3 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <CalculationScene
          heading="50/30/20 Rule Applied to $5,000 Net Monthly Income"
          steps={[
            { label: "Net monthly take-home pay", formula: "After taxes and benefits deductions", result: "$5,000" },
            { label: "Needs (50 percent)", formula: "$5,000 times 0.50", result: "$2,500 per month", highlight: true },
            { label: "Needs include", formula: "Rent $1,372, car payment $726, groceries $412", result: "$2,510 (close to target)" },
            { label: "Wants (30 percent)", formula: "$5,000 times 0.30", result: "$1,500 per month", highlight: true },
            { label: "Wants include", formula: "Dining, streaming, travel, clothing, entertainment", result: "Flexible discretionary spending" },
            { label: "Savings (20 percent)", formula: "$5,000 times 0.20", result: "$1,000 per month", highlight: true },
          ]}
          conclusion="At $5,000 net monthly income, the 50/30/20 rule allocates $1,000 per month to savings. That is $12,000 per year in savings before any investment returns."
          accent={accent}
        />
      ),
    },

    // Scene 4 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <StatsScene
          heading="Where the Average American Spends Every Dollar"
          stats={[
            { label: "Housing (rent or mortgage)", value: "33% of income", color: accent },
            { label: "Transportation (car, gas, insurance)", value: "17% of income", color: "#f59e0b" },
            { label: "Food (groceries plus dining)", value: "13% of income", color: "#22c55e" },
            { label: "Healthcare and insurance", value: "8% of income", color: "#0ea5e9" },
            { label: "Savings rate (actual)", value: "4% of income", color: "#ef4444" },
          ]}
          accent={accent}
          footnote="US median household income: $74,580. Median rent: $1,372 per month. Average car payment: $726 per month. Average grocery spend: $412 per month per household. Average credit card APR: 24.37% (2024). The 4% actual savings rate is far below the 20% target."
        />
      ),
    },

    // Scene 5 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <SetupScene
          heading="Building a Zero-Based Budget Step by Step"
          items={[
            { label: "Step 1: Write down total monthly net income", value: "All sources: salary, freelance, rental income", color: "#22c55e" },
            { label: "Step 2: List all fixed expenses first", value: "Rent, car payment, insurance, loan minimums", color: accent },
            { label: "Step 3: Estimate variable expenses", value: "Groceries, gas, utilities, dining, subscriptions", color: accent },
            { label: "Step 4: Assign savings and investment amounts", value: "Emergency fund, retirement, brokerage", color: "#22c55e" },
            { label: "Step 5: Income minus all allocations equals zero", value: "Every dollar has a job. Nothing is unassigned.", color: "#f59e0b" },
            { label: "Step 6: Review weekly and adjust monthly", value: "Real expenses will differ from estimates. Adjust.", color: "#94a3b8" },
          ]}
          accent={accent}
          description="Zero-based budgeting forces intentionality. You decide in advance where every dollar goes. Any surplus is explicitly allocated to savings or debt repayment, not left floating."
        />
      ),
    },

    // Scene 6 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <SvgLineChartScene
          heading="Savings Rate vs Years to Financial Independence"
          subheading="How increasing your savings rate from 5 percent to 50 percent dramatically shortens the path to FI at 7 percent real returns"
          data={[
            { label: "5% savings", value: 60 },
            { label: "10% savings", value: 51 },
            { label: "15% savings", value: 43 },
            { label: "20% savings", value: 37 },
            { label: "25% savings", value: 32 },
            { label: "30% savings", value: 28 },
            { label: "35% savings", value: 25 },
            { label: "40% savings", value: 22 },
            { label: "50% savings", value: 17 },
          ]}
          accent={accent}
          yLabel="Years to FI"
          xLabel="Savings Rate"
          highlightIdx={5}
          footnote="FI defined as 25x annual expenses (4% withdrawal rate). Historical 7% real market return assumed. Going from 5% to 30% savings rate cuts working years from 60 to 28. That is 32 years of freedom bought by disciplined budgeting."
        />
      ),
    },

    // Scene 7 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <ComparisonTableScene
          heading="50/30/20 vs Zero-Based vs Envelope Budgeting"
          subheading="Comparing effort, flexibility, and effectiveness for different financial situations"
          columns={["Method", "Effort Level", "Best For", "Main Weakness"]}
          rows={[
            { cells: ["50/30/20", "Low", "Beginners, stable incomes", "Too broad for problem spending"], highlight: true },
            { cells: ["Zero-based", "High", "Detailed control, irregular income", "Time-intensive monthly setup"], winner: 2 },
            { cells: ["Envelope", "Medium", "Overspenders in specific categories", "Rigid, hard to adjust mid-month"], winner: 3 },
            { cells: ["Pay-yourself-first", "Very low", "People who forget to save", "Does not address overspending"], winner: 1 },
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 8 (60s)
    {
      durationInFrames: sec(60),
      render: () => (
        <RealWorldExampleScene
          heading="Cutting $400 Per Month and Investing It for 20 Years"
          company="Personal Finance Example"
          scenario="A household earning $74,580 per year ($6,215 gross, $5,000 net) reviews their budget and finds $400 per month in cuttable expenses: streaming services ($45), unused gym ($50), impulse dining ($150), subscription boxes ($85), and overpriced phone plan ($70). They redirect that $400 to a brokerage account every month."
          setupItems={[
            { label: "Monthly savings redirected", value: "$400 per month", color: accent },
            { label: "Investment vehicle", value: "Index fund averaging 7% real annual return", color: "#22c55e" },
            { label: "Timeline", value: "20 years of consistent monthly investing", color: "#94a3b8" },
            { label: "Total contributions (no return)", value: "$96,000 over 20 years", color: "#94a3b8" },
            { label: "Value at 7% return after 20 years", value: "$207,000 (compound growth)", color: "#22c55e" },
            { label: "Extra wealth from compound returns", value: "$111,000 in investment gains", color: "#22c55e" },
          ]}
          outcome="$400 per month in budget cuts became $207,000 in 20 years"
          outcomeDetail="The $400 cuts cost nothing in quality of life (unused gym, forgotten subscriptions). Every dollar redirected to investing at 7% real return roughly doubles in 10 years by the Rule of 72. This is the math behind why budget discipline builds wealth."
          outcomeColor="#22c55e"
          accent={accent}
        />
      ),
    },

    // Scene 9 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <MistakeHighlightScene
          heading="Ignoring Small Recurring Subscriptions"
          mistake={{
            label: "The average American pays $219 per month in unused or forgotten subscriptions",
            detail: "A survey of 2,000 Americans found they underestimate their monthly subscription spending by $133 on average. Streaming (Netflix, Hulu, Disney, HBO, Spotify, Apple TV) alone average $86 per month. Add software, news, gym, boxes, and cloud storage and it exceeds $200 before noticing.",
          }}
          correction={{
            label: "Do a subscription audit every 6 months: cancel anything unused in the last 30 days",
            detail: "Log into your bank statement and filter for recurring charges. Cancel every subscription you did not use in the past 30 days. At $219 per month, eliminating unused subscriptions frees $2,628 per year that can go directly to savings."
          }}
          insight="At $219 per month redirected to a 7% index fund for 20 years, unused subscriptions cost you $113,000 in future wealth. The most expensive subscription is the forgotten one."
          accent={accent}
        />
      ),
    },

    // Scene 10 (70s)
    {
      durationInFrames: sec(70),
      render: () => (
        <WorkedExampleScene
          heading="3-Month Budget Audit Process"
          subheading="A systematic review of 90 days of spending to find savings and redirect them"
          company="Household Budget Example"
          ticker="BUDGET"
          trades={[
            { day: "Month 1", event: "Download 3 months of bank and credit card statements", action: "Export to spreadsheet. Do not judge yet. Categorize every transaction into needs, wants, or savings.", pl: 0, cumPl: 0 },
            { day: "Month 1", event: "Categorize all recurring charges (subscriptions, auto-pay bills)", action: "Found $219 in recurring charges. $87 was genuinely used. $132 was unused or forgotten.", pl: 132, cumPl: 132 },
            { day: "Month 2", event: "Calculate average monthly spending in each category", action: "Dining out: $340 average. Groceries: $412. Coffee: $94. Total food: $846 vs 50/30/20 food guideline of $650.", pl: 0, cumPl: 132 },
            { day: "Month 2", event: "Identify the top 3 categories over target", action: "Dining $190 over, entertainment $110 over, subscriptions $132 over. Total excess: $432 per month.", pl: 432, cumPl: 564 },
            { day: "Month 3", event: "Set category spending caps and track weekly", action: "Dining cap $150 (down from $340). Entertainment cap $80. Subscriptions audited to $87. Saved $432.", pl: 432, cumPl: 996 },
            { day: "End of audit", event: "Redirect $400 per month to index fund investment", action: "Automatic transfer set. Budget now produces $400 surplus every month going to wealth building.", pl: 400, cumPl: 1396 },
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
          heading="Connecting Budgeting to Cash Flow and Investing"
          bullets={[
            "Budgeting creates positive cash flow. Positive cash flow creates investable capital.",
            "Emergency fund (3 to 6 months expenses) is the foundation before any investing",
            "High credit card APR (24.37% average in 2024) means debt repayment beats most investments",
            "Index fund investing at 7% real returns only beats the bank if you consistently contribute",
            "A written budget is the starting point: wealth is built from cash flow surplus, not income size",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 12 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <SummaryScene
          heading="Budgeting: Core Principles to Remember"
          bullets={[
            "50/30/20 on $5,000 net: $2,500 needs, $1,500 wants, $1,000 savings per month",
            "Average American saves only 4% of income vs the 20% target: gap is found in subscriptions and dining",
            "30% savings rate reaches financial independence in 28 years at 7% real returns vs 60 years at 5%",
            "Subscription audit: average American wastes $132 per month on unused recurring charges",
            "Budget audit in 3 months: categorize, cap, and redirect the surplus to wealth building",
          ]}
          accent={accent}
          closingLine="A budget is not a restriction. It is written permission to spend guilt-free on what matters and redirect everything else to building your future."
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

// ── PfCashflowBasicsLong ──────────────────────────────────────────────────────
// Lesson: pf-cashflow-basics — "Personal Cash Flow Fundamentals"

export type PfCashflowBasicsLongProps = {
  accent?: string;
};

export const PfCashflowBasicsLong: React.FC<PfCashflowBasicsLongProps> = ({ accent = "#f59e0b" }) => {
  useVideoConfig();

  const scenes: SceneDef[] = [
    // Scene 1 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <TitleScene
          label="Personal Finance"
          title="Personal Cash Flow Fundamentals"
          subtitle="Income vs expenses, fixed vs variable costs, the personal cash flow statement, and how to go from negative to positive cash flow in 90 days"
          accent={accent}
        />
      ),
    },

    // Scene 2 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <BulletScene
          heading="Income Sources: Where Cash Flows In"
          bullets={[
            "W2 income: salary or hourly wages from an employer, most predictable",
            "Freelance or 1099 income: variable month to month, requires separate tax planning",
            "Rental income: passive cash flow from real estate after mortgage and expenses",
            "Dividends: quarterly cash payments from stock and fund holdings",
            "Business income: profit from a business or side income after expenses",
          ]}
          accent={accent}
          icon="💵"
        />
      ),
    },

    // Scene 3 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <CalculationScene
          heading="Personal Cash Flow Formula: Income Minus All Outflows"
          steps={[
            { label: "Gross monthly income", formula: "Salary before deductions", result: "$5,833 (avg American)" },
            { label: "Fixed costs (monthly)", formula: "Rent $1,920, car $726, insurance $210, loan minimums $150", result: "$3,006" },
            { label: "Variable costs (monthly)", formula: "Food $609, gas and transport $268, personal care $120", result: "$997" },
            { label: "Savings (target)", formula: "Emergency fund or retirement contribution", result: "$100 (avg actual)" },
            { label: "Free cash flow", formula: "$5,833 minus $3,006 minus $997 minus $100", result: "$1,730 remaining", highlight: true },
            { label: "After taxes and FICA", formula: "Gross $5,833 minus taxes ($1,600 avg) = $4,233 net", result: "True free cash: $4,233 minus $4,103 = $130", color: accent },
          ]}
          conclusion="The average American has roughly $130 in true monthly free cash flow after taxes, fixed costs, variable costs, and minimal savings. That $130 is what builds or destroys financial futures."
          accent={accent}
        />
      ),
    },

    // Scene 4 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <SetupScene
          heading="Personal Cash Flow Statement Template"
          items={[
            { label: "Section 1: Income", value: "W2 net, freelance, dividends, rental, other", color: "#22c55e" },
            { label: "Section 2: Fixed Costs", value: "Rent, mortgage, car payment, insurance premiums, loan minimums", color: accent },
            { label: "Section 3: Variable Costs", value: "Groceries, gas, dining, utilities, entertainment, clothing", color: "#f59e0b" },
            { label: "Section 4: Savings and Investments", value: "Emergency fund, 401k, IRA, brokerage", color: "#22c55e" },
            { label: "Section 5: Free Cash Flow", value: "Income minus fixed minus variable minus savings = surplus or deficit", color: "#94a3b8" },
            { label: "Review cadence", value: "Weekly 5-minute check, full monthly review", color: "#94a3b8" },
          ]}
          accent={accent}
          description="A personal cash flow statement is the financial version of a company income statement. Revenue in, costs out, profit or loss at the bottom. Knowing your exact monthly cash flow is the first step to improving it."
        />
      ),
    },

    // Scene 5 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <SvgLineChartScene
          heading="Cash Flow Over 12 Months: Seasonal Spending Spike in December"
          subheading="Monthly net cash flow for a household earning $5,833 gross, showing holiday spending impact"
          data={[
            { label: "Jan", value: 280 },
            { label: "Feb", value: 220 },
            { label: "Mar", value: 310 },
            { label: "Apr", value: 190 },
            { label: "May", value: 250 },
            { label: "Jun", value: 180 },
            { label: "Jul", value: 140 },
            { label: "Aug", value: 90 },
            { label: "Sep", value: 260 },
            { label: "Oct", value: 200 },
            { label: "Nov", value: 50 },
            { label: "Dec", value: -320 },
          ]}
          accent={accent}
          yLabel="Free Cash ($)"
          xLabel="Month"
          highlightIdx={11}
          footnote="The December holiday spending spike wipes out 3 months of surplus cash flow in one month. Budget a dedicated holiday fund of $200 per month starting in January to eliminate this pattern."
        />
      ),
    },

    // Scene 6 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <StatsScene
          heading="Average American Cash Flow Snapshot 2024"
          stats={[
            { label: "Gross monthly income", value: "$5,833", color: "#22c55e" },
            { label: "Housing (rent or mortgage)", value: "$1,920 (33%)", color: accent },
            { label: "Food (groceries plus dining)", value: "$609 (10%)", color: "#f59e0b" },
            { label: "Transportation (all-in)", value: "$994 (17%)", color: "#0ea5e9" },
            { label: "Average credit card debt", value: "$6,501 at 24.37% APR", color: "#ef4444" },
          ]}
          accent={accent}
          footnote="Average American net monthly cash flow after all expenses: approximately $124. Housing costs rose 7.2% in 2023. Gas averaged $3.45 per gallon in 2024. Average car payment $726 per month. Credit card APR 24.37% means $6,501 debt costs $1,584 per year in interest alone."
        />
      ),
    },

    // Scene 7 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <ComparisonTableScene
          heading="Positive vs Negative vs Break-Even Cash Flow"
          subheading="What each state means for your financial trajectory"
          columns={["Cash Flow State", "Monthly Result", "1 Year Impact", "Action Required"]}
          rows={[
            { cells: ["Positive", "Income exceeds all costs", "Building savings and wealth", "Invest the surplus"], winner: 1, highlight: true },
            { cells: ["Break-even", "Income equals all costs", "No savings growth", "Find $200 to cut or earn"], winner: 3 },
            { cells: ["Slightly negative", "Spending $100 to $300 more than income", "Credit card debt grows slowly", "Immediate budget audit"], winner: 4 },
            { cells: ["Deeply negative", "Spending $500 or more over income", "Debt spiral risk", "Emergency restructure needed"], winner: 4 },
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 8 (60s)
    {
      durationInFrames: sec(60),
      render: () => (
        <RealWorldExampleScene
          heading="Converting Negative Cash Flow to Positive in 90 Days"
          company="Household Turnaround Example"
          scenario="A household earning $5,833 gross ($4,200 net after taxes) is running $280 per month negative cash flow. Credit card balance is growing. Housing is $1,800, car is $680, food is $750, entertainment is $420, subscriptions are $190. Total outflows: $4,480. Cash flow: negative $280."
          setupItems={[
            { label: "Starting cash flow", value: "Negative $280 per month", color: "#ef4444" },
            { label: "Cut 1: subscriptions audit", value: "$190 reduced to $65 (cancel 10 unused)", color: "#22c55e" },
            { label: "Cut 2: dining and entertainment cap", value: "$420 capped at $200 (cook more, free events)", color: "#22c55e" },
            { label: "Cut 3: grocery optimization", value: "$750 reduced to $580 (meal plan, store brand)", color: "#22c55e" },
            { label: "Total monthly savings found", value: "$515 per month in cuts", color: "#22c55e" },
            { label: "New monthly cash flow", value: "Positive $235 per month", color: "#22c55e" },
          ]}
          outcome="From negative $280 to positive $235 in 90 days of budget discipline"
          outcomeDetail="The $515 in cuts required no income change. Subscriptions, dining, and grocery optimization alone flipped the household from debt accumulation to surplus. The $235 surplus goes to emergency fund first, then credit card paydown."
          outcomeColor="#22c55e"
          accent={accent}
        />
      ),
    },

    // Scene 9 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <MistakeHighlightScene
          heading="Confusing High Income with Positive Cash Flow"
          mistake={{
            label: "A $150,000 income household with negative monthly cash flow",
            detail: "A dual-income household earns $150,000 per year ($12,500 gross monthly, $9,500 net). They have a $4,200 mortgage, two car payments totaling $1,400, private school at $2,000, dining and lifestyle spending at $2,400. Total outflows: $10,000. Cash flow: negative $500 per month despite top-20-percent income.",
          }}
          correction={{
            label: "Track net monthly cash flow, not gross income. High income with high lifestyle costs = zero wealth building.",
            detail: "The $150,000 household is in worse financial shape than a $75,000 household with $800 monthly surplus. Lifestyle inflation that matches or exceeds income growth produces exactly zero wealth. Cash flow is king, not income."
          }}
          insight="Rule: your savings rate matters more than your income. A 20% savings rate on $50,000 builds more wealth than a 2% savings rate on $200,000. Cash flow discipline is the equalizer."
          accent={accent}
        />
      ),
    },

    // Scene 10 (70s)
    {
      durationInFrames: sec(70),
      render: () => (
        <WorkedExampleScene
          heading="Analyzing 3 Months of Bank Statements to Find Cash Flow Leaks"
          subheading="Step-by-step statement review that found $515 in monthly outflows to cut"
          company="Household Cash Flow Audit"
          ticker="CASHFLOW"
          trades={[
            { day: "Week 1", event: "Export 3 months of bank and credit card statements to spreadsheet", action: "All 247 transactions exported. Do not categorize yet, just gather the data.", pl: 0, cumPl: 0 },
            { day: "Week 1", event: "Filter for all recurring charges (auto-pay, subscriptions)", action: "Found 24 recurring charges totaling $634 per month. Listed every one.", pl: 0, cumPl: 0 },
            { day: "Week 2", event: "Mark each recurring charge as used in last 30 days or unused", action: "11 charges ($169) marked unused: forgotten streaming service, extra cloud storage, trial not cancelled.", pl: 169, cumPl: 169 },
            { day: "Week 2", event: "Calculate average monthly spend on dining and entertainment", action: "Average $420 per month over 3 months. Benchmark: 10 percent of net income = $420 (at limit but above comfort)", pl: 0, cumPl: 169 },
            { day: "Week 3", event: "Identify grocery over-spend vs benchmark", action: "Average $750. Meal planning target: $580. Potential savings: $170 per month.", pl: 170, cumPl: 339 },
            { day: "Week 4", event: "Set caps, cancel subscriptions, and redirect surplus", action: "Dining capped at $200. Subscriptions cancelled saving $125. Groceries targeted at $580. New surplus: $235 per month.", pl: 515, cumPl: 854 },
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
          heading="Connecting Cash Flow to Your Investing Timeline"
          bullets={[
            "You can only invest what your cash flow produces. Negative cash flow means zero investing.",
            "Emergency fund (3 to 6 months expenses) is built from cash flow surplus before investing",
            "Credit card debt at 24.37% APR must be paid before investing at 7 to 10% expected returns",
            "Every additional $100 in monthly positive cash flow adds $34,000 to your wealth over 20 years at 7%",
            "Cash flow is the engine. Budgeting is the fuel injection system. Investing is the output.",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 12 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <SummaryScene
          heading="Cash Flow Basics: Key Takeaways"
          bullets={[
            "Personal cash flow = income minus fixed minus variable minus savings. Know your number.",
            "Average American: $5,833 gross, $124 true monthly surplus after all costs",
            "Negative cash flow = debt growth. Even $500 above income starts a compounding debt problem.",
            "High income does not equal positive cash flow: lifestyle inflation is the wealth destroyer",
            "3-month bank statement audit finds the leaks. Most households find $300 to $500 in cuttable outflows.",
          ]}
          accent={accent}
          closingLine="Cash flow is the heartbeat of your financial life. Check it monthly, optimize it relentlessly, and invest every dollar of surplus."
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

// ── PfSavingsBasicsLong ───────────────────────────────────────────────────────
// Lesson: pf-savings-basics — "Emergency Funds, HYSAs, and Compound Interest"

export type PfSavingsBasicsLongProps = {
  accent?: string;
};

export const PfSavingsBasicsLong: React.FC<PfSavingsBasicsLongProps> = ({ accent = "#22c55e" }) => {
  useVideoConfig();

  const scenes: SceneDef[] = [
    // Scene 1 (30s)
    {
      durationInFrames: sec(30),
      render: () => (
        <TitleScene
          label="Personal Finance"
          title="Emergency Funds, HYSAs, and Compound Interest"
          subtitle="A 5% HYSA earned 10 times more than the average savings account in 2024. Here is how to capture that and build the foundation of your financial life."
          accent={accent}
        />
      ),
    },

    // Scene 2 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <BulletScene
          heading="Emergency Fund: The Non-Negotiable Foundation"
          bullets={[
            "Target: 3 to 6 months of essential living expenses in liquid, accessible savings",
            "Liquid means accessible within 1 to 2 business days without penalty",
            "Separate account from checking: out of sight, out of mind, not in the spending budget",
            "Funded before investing: an emergency fund prevents forced selling of investments at the worst time",
            "Fully funded benchmark: 6 months if self-employed or single income, 3 months if dual income",
          ]}
          accent={accent}
          icon="🏦"
        />
      ),
    },

    // Scene 3 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <CalculationScene
          heading="Compound Interest: HYSA vs Standard Savings Over 5 Years"
          steps={[
            { label: "Starting principal", formula: "Initial deposit into savings", result: "$10,000" },
            { label: "HYSA rate (2024)", formula: "Ally, Marcus, SoFi average", result: "5.00% APY" },
            { label: "HYSA value after 5 years", formula: "$10,000 times (1 + 0.05) to the power of 5", result: "$12,763", highlight: true },
            { label: "Standard savings rate (national avg 2024)", formula: "FDIC reported national average", result: "0.46% APY" },
            { label: "Standard savings after 5 years", formula: "$10,000 times (1 + 0.0046) to the power of 5", result: "$10,232" },
            { label: "HYSA advantage over 5 years", formula: "$12,763 minus $10,232", result: "$2,531 more earned", color: accent, highlight: true },
          ]}
          conclusion="The HYSA earns $2,531 more on the same $10,000 over 5 years. That is 10 times more interest than the standard savings account. The only cost is opening a new online account."
          accent={accent}
        />
      ),
    },

    // Scene 4 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <StatsScene
          heading="Savings Account Rates Compared: 2024"
          stats={[
            { label: "High-Yield Savings (HYSA)", value: "5.00 to 5.25% APY (Ally, Marcus, SoFi)", color: "#22c55e" },
            { label: "1-Year CD (certificate of deposit)", value: "5.30% APY", color: "#22c55e" },
            { label: "Money Market Account", value: "4.80% APY (top online banks)", color: "#22c55e" },
            { label: "National Average Savings Account", value: "0.46% APY (FDIC 2024)", color: "#ef4444" },
          ]}
          accent={accent}
          footnote="HYSA offers 5% vs 0.46% average: that is a 10x difference on the same deposit. CDs lock funds for a term. HYSAs stay liquid. Money market accounts may have check-writing but slightly lower rates. All are FDIC insured to $250,000."
        />
      ),
    },

    // Scene 5 (55s)
    {
      durationInFrames: sec(55),
      render: () => (
        <SvgLineChartScene
          heading="$10,000 Growth Over 10 Years: HYSA at 5% vs Standard Savings at 0.46%"
          subheading="Two growth curves showing the compounding gap between HYSA and standard savings account"
          data={[
            { label: "Year 0", value: 10000 },
            { label: "Year 1", value: 10500 },
            { label: "Year 2", value: 11025 },
            { label: "Year 3", value: 11576 },
            { label: "Year 4", value: 12155 },
            { label: "Year 5", value: 12763 },
            { label: "Year 6", value: 13401 },
            { label: "Year 7", value: 14071 },
            { label: "Year 8", value: 14775 },
            { label: "Year 9", value: 15513 },
            { label: "Year 10", value: 16289 },
          ]}
          accent={accent}
          yLabel="Account Value ($)"
          xLabel="Year"
          highlightIdx={10}
          footnote="Standard savings at 0.46% reaches $10,471 after 10 years. HYSA at 5% reaches $16,289. The gap is $5,818 earned on the same $10,000 deposit. This is free money left on the table by keeping savings in a traditional bank account."
        />
      ),
    },

    // Scene 6 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <SetupScene
          heading="How to Open a HYSA in 4 Steps"
          items={[
            { label: "Step 1: Choose a bank", value: "Ally, Marcus (Goldman), SoFi, Discover all offer 4.5% to 5.25% APY", color: "#22c55e" },
            { label: "Step 2: Apply online (10 minutes)", value: "Social Security number, government ID, linked checking account", color: accent },
            { label: "Step 3: Fund the account", value: "ACH transfer from checking takes 1 to 3 business days", color: accent },
            { label: "Step 4: Set up automatic transfers", value: "Schedule a monthly transfer equal to your savings target (e.g. $400 per month)", color: "#22c55e" },
            { label: "FDIC insured", value: "Up to $250,000 per depositor per bank. Zero risk to principal.", color: "#94a3b8" },
            { label: "APY review", value: "Check rate every 6 months. HYSA rates move with Federal Reserve decisions.", color: "#94a3b8" },
          ]}
          accent={accent}
          description="Opening a HYSA takes 10 minutes online and requires only a linked checking account and government ID. Rates are variable and move with the Federal Reserve but have historically stayed 10x or more above the national savings average."
        />
      ),
    },

    // Scene 7 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <ComparisonTableScene
          heading="HYSA vs Savings Account vs CD vs Money Market"
          subheading="Which savings vehicle fits which goal"
          columns={["Account Type", "2024 Rate", "Liquidity", "Best For"]}
          rows={[
            { cells: ["HYSA", "5.00 to 5.25%", "Instant withdrawal", "Emergency fund, general savings"], winner: 1, highlight: true },
            { cells: ["Standard savings", "0.46%", "Instant withdrawal", "Nothing (use HYSA instead)"], winner: 3 },
            { cells: ["1-year CD", "5.30%", "Locked for term (early exit penalty)", "Money not needed for 1 year"], winner: 2 },
            { cells: ["Money market", "4.80%", "Same as HYSA, may have check writing", "Large balances needing flexibility"], winner: 2 },
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 8 (60s)
    {
      durationInFrames: sec(60),
      render: () => (
        <RealWorldExampleScene
          heading="Redirecting Monthly Expenses to a HYSA After a Budget Audit"
          company="Personal Finance Example"
          scenario="After completing a 3-month budget audit, a household finds $400 per month in cuttable expenses. Instead of letting the surplus sit in checking (earning 0.01% at their traditional bank), they open a Marcus HYSA at 5.10% APY and auto-transfer $400 per month."
          setupItems={[
            { label: "Monthly surplus redirected", value: "$400 per month to HYSA", color: accent },
            { label: "HYSA APY (Marcus 2024)", value: "5.10% APY", color: "#22c55e" },
            { label: "Emergency fund target", value: "$15,000 (6 months of $2,500 essential costs)", color: "#94a3b8" },
            { label: "Months to reach 3-month emergency fund", value: "19 months to $7,500 (with interest)", color: "#22c55e" },
            { label: "Interest earned in first year", value: "$4,800 deposited, earns $144 in HYSA interest", color: "#22c55e" },
            { label: "vs keeping in checking", value: "$4,800 in checking earns $0 to $5", color: "#ef4444" },
          ]}
          outcome="$144 in free interest earned in year 1 just by switching accounts"
          outcomeDetail="The $144 is passive income that compounds every year. As the balance grows toward $15,000, annual interest at 5% reaches $750 per year: over $60 per month in passive income just from the emergency fund. This is the power of high-yield savings."
          outcomeColor="#22c55e"
          accent={accent}
        />
      ),
    },

    // Scene 9 (50s)
    {
      durationInFrames: sec(50),
      render: () => (
        <MistakeHighlightScene
          heading="Keeping Emergency Fund in a Checking Account"
          mistake={{
            label: "Holding $15,000 in a traditional checking account earning 0.01% APY",
            detail: "A household has $15,000 sitting in their Chase checking account earning 0.01% APY ($1.50 per year). They move it to their savings account at 0.46% APY ($69 per year). Both are far below the HYSA rate. Over 5 years, the difference between 0.01% and 5% on $15,000 is $3,685 in lost interest.",
          }}
          correction={{
            label: "Move emergency fund to a high-yield savings account. 10 minutes, 10x more interest.",
            detail: "At 5% HYSA, $15,000 earns $750 in year 1. At 0.46% standard savings, the same $15,000 earns $69. At 0.01% checking, it earns $1.50. The move to HYSA earns $681 more per year on the same money with zero risk."
          }}
          insight="Over 5 years, keeping $15,000 in checking versus HYSA at 5% costs you $3,685 in free interest. That is a month of salary for many Americans, lost to banking inertia."
          accent={accent}
        />
      ),
    },

    // Scene 10 (70s)
    {
      durationInFrames: sec(70),
      render: () => (
        <WorkedExampleScene
          heading="Rule of 72 at Various Savings and Investment Rates"
          subheading="How long to double $10,000 at different rates using the Rule of 72"
          company="Compound Interest Calculator"
          ticker="COMPOUND"
          trades={[
            { day: "Rate: 0.46%", event: "Standard savings account (national average 2024)", action: "Rule of 72: 72 divided by 0.46 = 156 years to double. $10,000 becomes $20,000 in 156 years.", pl: 0, cumPl: 0 },
            { day: "Rate: 5.00%", event: "High-yield savings account (Ally, Marcus, SoFi 2024)", action: "Rule of 72: 72 divided by 5 = 14.4 years to double. $10,000 becomes $20,000 in 14 years.", pl: 10000, cumPl: 10000 },
            { day: "Rate: 7.00%", event: "Historical S and P 500 real return (inflation adjusted avg)", action: "Rule of 72: 72 divided by 7 = 10.3 years to double. $10,000 becomes $20,000 in 10 years.", pl: 10000, cumPl: 20000 },
            { day: "Rate: 10.00%", event: "Historical S and P 500 nominal return", action: "Rule of 72: 72 divided by 10 = 7.2 years to double. $10,000 becomes $20,000 in 7 years.", pl: 10000, cumPl: 30000 },
            { day: "Rate: 24.37%", event: "Average credit card APR (2024): debt doubles AGAINST you", action: "Rule of 72: 72 divided by 24.37 = 3 years. $6,501 avg debt becomes $13,002 in 3 years if minimum payments only.", pl: -6501, cumPl: 23499 },
            { day: "Key insight", event: "30% savings rate reaches FI in 28 years vs 10% rate in 51 years", action: "At 7% real returns, savings rate is the most powerful variable in your financial plan.", pl: 0, cumPl: 23499 },
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
          heading="Connecting Savings to Investing and Budgeting"
          bullets={[
            "HYSA is the bridge between budget surplus and long-term investing: park cash here first",
            "Emergency fund eliminates the forced selling of investments during market downturns",
            "Once emergency fund is funded, surplus cash moves to tax-advantaged accounts (401k, IRA)",
            "Rule of 72 makes compound interest intuitive: use it to evaluate every financial decision",
            "30% savings rate reaches FI in 28 years at 7% real returns. Every 5% of savings rate buys 4 to 7 years of freedom.",
          ]}
          accent={accent}
        />
      ),
    },

    // Scene 12 (40s)
    {
      durationInFrames: sec(40),
      render: () => (
        <SummaryScene
          heading="Savings Basics: Build the Foundation First"
          bullets={[
            "HYSA at 5% vs standard savings at 0.46%: $10,000 earns $12,763 vs $10,232 after 5 years",
            "Emergency fund target: 3 to 6 months of essential expenses in a liquid, separate HYSA",
            "Rule of 72: at 5% HYSA, money doubles in 14.4 years. At 7% index fund, doubles in 10.3 years.",
            "Credit card at 24.37% APR: debt doubles against you in 3 years. Pay this first.",
            "30% savings rate reaches financial independence in 28 years vs 51 years at 10% savings rate",
          ]}
          accent={accent}
          closingLine="Savings is the foundation. The HYSA is the foundation of the foundation. Start there, build your emergency fund, then let compounding do the rest."
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
