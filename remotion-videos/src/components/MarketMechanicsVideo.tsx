import { AbsoluteFill, useVideoConfig, useCurrentFrame, interpolate } from "remotion";
import { SceneManager, TitleScene, BulletScene, SummaryScene, SvgLineChartScene, RealWorldExampleScene, type SceneDef } from "./SceneSystem";
import React from "react";

type OrderBookDataPoint = { price: number; bidSize: number; askSize: number };

export type MarketMechanicsProps = {
    title: string;
    subtitle: string;
    subjectLabel: string;
    posterUrl: string;
    accent: string;
    glow: string;
    mechanicType: "order-book" | "option-chain" | "tape";
    dataPoints: OrderBookDataPoint[];
};

// ─── Rich per-lesson content data ─────────────────────────────────────────────
const MECHANICS_DATA: Record<string, {
    label: string;
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
    closingLine: string;
}> = {
    "options-chain-reading": {
        label: "Options Chain Reading",
        description: "The options chain displays every available contract organized by strike and expiration, with open interest revealing where traders are concentrated.",
        bullets: [
            "Open interest (OI) shows total outstanding contracts — higher = more liquidity",
            "Max pain is the strike where OI is highest on both puts and calls",
            "ATM strikes have the tightest bid-ask spreads — cheapest to trade",
            "Volume spikes signal fresh money flowing into specific strikes",
        ],
        chartData: [
            { label: "$420", value: 1800 },
            { label: "$430", value: 4200 },
            { label: "$440", value: 7600 },
            { label: "$450★", value: 12450 },
            { label: "$460", value: 8900 },
            { label: "$470", value: 4100 },
            { label: "$480", value: 1200 },
        ],
        chartHeading: "AAPL Options Chain — Open Interest by Strike",
        chartSubheading: "OI distribution peaks at $450 — the max pain strike with 12,450 contracts",
        chartXLabel: "Strike Price",
        chartYLabel: "Open Interest (contracts)",
        chartHighlightIdx: 3,
        chartFootnote: "$450 strike (★) holds 12,450 open contracts — highest OI signals max pain and strong liquidity zone.",
        example: {
            heading: "Real Trade: Using OI to Find Max Pain",
            company: "AAPL — Max Pain Positioning",
            scenario: "AAPL at $448 with one week to expiration. Options chain showed massive OI at the $450 strike — 12,450 contracts combined. Max pain analysis suggested stock would pin near $450.",
            setupItems: [
                { label: "AAPL Price", value: "$448", color: "#94a3b8" },
                { label: "Max Pain Strike", value: "$450", color: "#3b82f6" },
                { label: "OI at $450", value: "12,450", color: "#10b981" },
                { label: "Strategy", value: "$448/$452 Call Spread", color: "#f59e0b" },
                { label: "Entry Cost", value: "$1.20 debit", color: "#f59e0b" },
            ],
            outcome: "+$1.80 profit (+150%)",
            outcomeDetail: "AAPL closed at $451 at expiry — pinned within $1 of the max pain strike as OI predicted. Spread maxed at $3.00. Net: $3.00 − $1.20 = +$1.80 profit. Reading the options chain OI gave a clear directional bias.",
            outcomeColor: "#10b981",
        },
        takeaways: [
            "Always check open interest before selecting a strike — avoid illiquid contracts",
            "Max pain is where MM delta hedging pressure pins the stock near expiry",
            "Volume vs OI ratio reveals whether flow is opening new positions or closing old ones",
            "Wide bid-ask on low-OI strikes means you're paying for the market maker's risk",
        ],
        closingLine: "The options chain is your map — open interest shows where the smart money is concentrated.",
    },

    "bid-ask-reality": {
        label: "Bid-Ask Spread Reality",
        description: "The bid-ask spread is a hidden transaction cost that compounds on every trade — using limit orders is non-negotiable for options traders.",
        bullets: [
            "Bid = highest buyer price, Ask = lowest seller price — spread is the difference",
            "Market orders fill at the ask (buying) or bid (selling) — paying full spread",
            "Limit orders mid-spread save $0.20–$0.50 per contract routinely",
            "Illiquid options (OI < 100) can have $1.00+ spreads — a massive hidden tax",
        ],
        chartData: [
            { label: "SPY", value: 0.01 },
            { label: "QQQ", value: 0.02 },
            { label: "AAPL", value: 0.05 },
            { label: "TSLA★", value: 0.45 },
            { label: "NVDA", value: 0.35 },
            { label: "Small Cap", value: 2.00 },
            { label: "Illiquid", value: 3.50 },
        ],
        chartHeading: "Bid-Ask Spread by Ticker — Cost to Enter One Contract",
        chartSubheading: "SPY at $0.01 vs small cap at $2.00+ — liquidity dictates your entry cost",
        chartXLabel: "Ticker / Liquidity Level",
        chartYLabel: "Bid-Ask Spread ($)",
        chartHighlightIdx: 3,
        chartFootnote: "TSLA (★) bid-ask of $0.45 means you pay $45/contract just to enter. SPY at $0.01 costs $1 per contract.",
        example: {
            heading: "Real Trade: Limit vs. Market Order Comparison",
            company: "TSLA — Limit Order Discipline",
            scenario: "TSLA $250 call bid $4.20 / ask $4.65. Spread = $0.45. Buying 5 contracts at market costs 5 × $0.45 × 100 = $225 in immediate slippage. Using a limit at the midpoint instead.",
            setupItems: [
                { label: "Bid Price", value: "$4.20", color: "#ef4444" },
                { label: "Ask Price", value: "$4.65", color: "#10b981" },
                { label: "Spread", value: "$0.45", color: "#f59e0b" },
                { label: "Limit (Mid)", value: "$4.42", color: "#6366f1" },
                { label: "Contracts", value: "5", color: "#94a3b8" },
            ],
            outcome: "Saved $0.38 per contract = $190 total",
            outcomeDetail: "Limit order at $4.42 (midpoint) filled within 30 seconds. Saved $0.23 vs ask on entry. Later sold at $4.80 using limit at midpoint. Total savings: $0.38 × 5 × 100 = $190. On a $2,100 position, that's 9% saved before the trade even moves.",
            outcomeColor: "#10b981",
        },
        takeaways: [
            "Never use market orders for options — always use limit orders at the midpoint",
            "Start at the mid-price and work toward the ask in $0.05 increments if unfilled",
            "Stick to liquid tickers: SPY, QQQ, AAPL, TSLA, NVDA — spreads are tight",
            "Wide spreads in illiquid options often mean the market maker is warning you",
        ],
        closingLine: "Limit orders are free alpha — never pay the full spread when the midpoint is right there.",
    },

    "tape-speed": {
        label: "Tape Speed Reading",
        description: "The time and sales tape shows every trade in real time. Unusual volume spikes — 3× normal or more — signal institutional positioning before major moves.",
        bullets: [
            "Volume ratio = current volume / 30-day average — above 3× is significant",
            "Call sweep (large, aggressive buy at ask) signals bullish institutional bet",
            "Tape speed (prints per second) indicates intensity — fast = big players moving",
            "Unusual options activity (UOA) in calls often precedes 5–15% stock moves",
        ],
        chartData: [
            { label: "Mon", value: 98000 },
            { label: "Tue", value: 115000 },
            { label: "Wed", value: 106000 },
            { label: "Thu AM", value: 142000 },
            { label: "Thu Mid★", value: 850000 },
            { label: "Thu PM", value: 310000 },
            { label: "Fri", value: 121000 },
        ],
        chartHeading: "NVDA Options Volume — Unusual Activity Spike Detection",
        chartSubheading: "3.2× normal volume spike on Thursday midday preceded an 8% stock move",
        chartXLabel: "Day / Session",
        chartYLabel: "Options Volume (contracts)",
        chartHighlightIdx: 4,
        chartFootnote: "Thursday midday (★): 850,000 contracts vs. 100k normal = 8.5× spike. Entry before the +8% surge netted 240% gain on calls.",
        example: {
            heading: "Real Trade: NVDA Unusual Call Buying",
            company: "NVDA — Tape Reading Entry",
            scenario: "NVDA at $620. Tape showed 850,000 call contracts printing in 90 minutes — 3.2× the 30-day average. Large sweeps at ask on $640 strike calls. Smart money was loading up.",
            setupItems: [
                { label: "NVDA Price", value: "$620", color: "#94a3b8" },
                { label: "Volume Ratio", value: "3.2×", color: "#f59e0b" },
                { label: "Strike Targeted", value: "$640 Call", color: "#10b981" },
                { label: "Entry Cost", value: "$4.20", color: "#f59e0b" },
                { label: "NVDA 2 days later", value: "$670", color: "#10b981" },
            ],
            outcome: "+$5.80 per contract (+138%)",
            outcomeDetail: "Entered $640 calls at $4.20 following the volume spike. NVDA ripped 8% to $670 in 2 days. $640 call worth $34.00. Sold at $10.00 for +$5.80 gain (+138%). Tape reading identified the setup before the move happened.",
            outcomeColor: "#10b981",
        },
        takeaways: [
            "Scan for volume > 3× average before any trade — institutional flow is your signal",
            "Large call sweeps at the ask are the most reliable bullish signal on the tape",
            "UOA in options often precedes stock moves by 1–3 trading days",
            "Combine tape reading with the options chain OI to confirm the thesis",
        ],
        closingLine: "The tape doesn't lie — when volume explodes 3×, something big is about to happen.",
    },

    "borrow-locate": {
        label: "Borrow & Locate",
        description: "Short selling requires borrowing shares, and the cost of that borrow rises as short interest builds — signaling danger for shorts before a squeeze.",
        bullets: [
            "Borrow rate = annualized % fee to hold a short position overnight",
            "Rates above 5% signal heavy short interest and potential squeeze risk",
            "Hard-to-borrow (HTB) stocks can see rates spike from 2% to 50%+ overnight",
            "Locate confirmation from your broker means shares are available — for now",
        ],
        chartData: [
            { label: "Week 1", value: 2.0 },
            { label: "Week 2", value: 2.8 },
            { label: "Week 3", value: 4.1 },
            { label: "Week 4", value: 5.9 },
            { label: "Week 5★", value: 8.4 },
            { label: "Week 6", value: 14.2 },
            { label: "Week 7", value: 31.0 },
        ],
        chartHeading: "Short Borrow Rate Escalation — HTB Stock Over 7 Weeks",
        chartSubheading: "Borrow cost rising from 2% to 8.4%+ signals mounting short-side danger",
        chartXLabel: "Week",
        chartYLabel: "Annualized Borrow Rate (%)",
        chartHighlightIdx: 4,
        chartFootnote: "Week 5 (★): borrow hits 8.4% — every 100 points of short = $8.40/year in carry. By week 7 at 31%, it's a short-side crisis.",
        example: {
            heading: "Real Trade: GME Borrow Rate Warning",
            company: "GME — Short Squeeze Anatomy",
            scenario: "GME trading at $20. Borrow rate spiked from 2% to 8.4% in 5 weeks as Reddit attention mounted. High borrow = shorts trapped with rising carry costs. Classic squeeze precursor.",
            setupItems: [
                { label: "GME Price", value: "$20", color: "#94a3b8" },
                { label: "Initial Borrow", value: "2%", color: "#10b981" },
                { label: "Week 5 Borrow", value: "8.4%", color: "#f59e0b" },
                { label: "Short Float", value: "140%", color: "#ef4444" },
                { label: "Days to Cover", value: "3.8 days", color: "#ef4444" },
            ],
            outcome: "GME squeezed from $20 to $483",
            outcomeDetail: "8.4% borrow rate + 140% short float + rising retail buying = impossible squeeze conditions. Shorts couldn't cover without driving price higher. Call buyers made 10,000%+. The borrow rate spike was the warning sign 3 weeks early.",
            outcomeColor: "#f59e0b",
        },
        takeaways: [
            "Always check the borrow rate before initiating a short position",
            "Borrow rates above 5% mean the short trade has a built-in carry cost drag",
            "Rates spiking week-over-week are a warning that a squeeze is building",
            "HTB stocks can have locates pulled overnight — never size short positions large",
        ],
        closingLine: "Borrow rates are the vital sign of short-side risk — rising rates mean the squeeze is loading.",
    },

    "short-risk": {
        label: "Short Squeeze Risk",
        description: "When a heavily shorted stock reverses upward, short sellers are forced to buy to cover — creating a feedback loop of explosive price gains.",
        bullets: [
            "Short float % = shares sold short / float — above 20% is high squeeze risk",
            "Days to cover = short interest / average volume — higher = harder to exit",
            "Short interest rising while price rises = dangerous squeeze setup forming",
            "Catalyst (earnings beat, analyst upgrade, news) can trigger the avalanche",
        ],
        chartData: [
            { label: "5%", value: 1.2 },
            { label: "10%", value: 1.8 },
            { label: "15%", value: 2.9 },
            { label: "20%", value: 4.7 },
            { label: "23%★", value: 7.2 },
            { label: "30%", value: 12.4 },
            { label: "50%+", value: 35.0 },
        ],
        chartHeading: "Short Float % vs. Squeeze Magnitude — Historical Cases",
        chartSubheading: "At 23% short float, squeeze multiplier averages 7.2× — explosive returns for longs",
        chartXLabel: "Short Float Percentage",
        chartYLabel: "Average Squeeze Magnitude (×)",
        chartHighlightIdx: 4,
        chartFootnote: "At 23% short float (★) historical squeezes average 7.2× from base. GME at 140% short float squeezed 24×.",
        example: {
            heading: "Real Trade: BBBY Short Squeeze",
            company: "BBBY — 23% Short Float Squeeze",
            scenario: "BBBY at $5.00 with 23% short float and 4.2 days to cover. Retail buying surged on social media — shorts couldn't exit without driving price higher. Classic high short-float setup.",
            setupItems: [
                { label: "BBBY Price", value: "$5.00", color: "#94a3b8" },
                { label: "Short Float", value: "23%", color: "#ef4444" },
                { label: "Days to Cover", value: "4.2 days", color: "#f59e0b" },
                { label: "Catalyst", value: "Retail Buying Wave", color: "#6366f1" },
                { label: "Peak Price", value: "$23.00", color: "#10b981" },
            ],
            outcome: "+$18 per share (+360%)",
            outcomeDetail: "BBBY squeezed from $5 to $23 in 4 days — a 360% move. Shorts who entered at $5 faced a 4.6× loss to cover. Call buyers on $7 strikes at $0.30 premium saw options worth $16+. Short float above 20% is the setup signal.",
            outcomeColor: "#10b981",
        },
        takeaways: [
            "Screen for short float above 20% + days-to-cover above 3 for squeeze candidates",
            "Never short a heavily shorted stock without a clear catalyst to the downside",
            "Squeezes are fast and violent — calls benefit from gamma acceleration",
            "Once a squeeze starts, covering pressure compounds with every $1 move higher",
        ],
        closingLine: "Short squeeze risk is asymmetric — identify it early and profit from forced covering.",
    },

    "order-types": {
        label: "Order Types Mastery",
        description: "Choosing the right order type eliminates slippage and gives you execution control — the difference between a 94% fill rate and a missed trade.",
        bullets: [
            "Market order: instant fill at any price — dangerous in illiquid options",
            "Limit order: specify your price — guaranteed not to pay more than stated",
            "Stop order: triggers at a price level — converts to market order when hit",
            "Day vs. GTC: day orders cancel at close; GTC persist until filled or cancelled",
        ],
        chartData: [
            { label: "SPY Limit", value: 0.00 },
            { label: "QQQ Limit", value: 0.01 },
            { label: "AAPL Limit", value: 0.03 },
            { label: "TSLA Limit", value: 0.08 },
            { label: "SPY Market★", value: 0.18 },
            { label: "TSLA Market", value: 0.52 },
            { label: "Small Market", value: 1.85 },
        ],
        chartHeading: "Slippage Comparison: Limit vs. Market Orders",
        chartSubheading: "Limit orders save $0.18–$1.85 per contract vs. market — compounding over a year",
        chartXLabel: "Order Type & Ticker",
        chartYLabel: "Slippage Per Contract ($)",
        chartHighlightIdx: 4,
        chartFootnote: "SPY market order on the open (★) = $0.18 slippage. Same SPY with limit at midpoint = $0. Fill rate: 94%+ on liquid names.",
        example: {
            heading: "Real Trade: SPY Open — Limit vs Market",
            company: "SPY — Order Execution Discipline",
            scenario: "9:32am — SPY $445 call bid $3.20 / ask $3.38. Spread = $0.18. Market order fills at $3.38. Limit order at $3.29 (midpoint) placed with 2-minute patience. Which strategy wins?",
            setupItems: [
                { label: "Bid", value: "$3.20", color: "#ef4444" },
                { label: "Ask", value: "$3.38", color: "#10b981" },
                { label: "Market Fill", value: "$3.38", color: "#ef4444" },
                { label: "Limit Placed", value: "$3.29", color: "#10b981" },
                { label: "Fill Time", value: "28 seconds", color: "#94a3b8" },
            ],
            outcome: "Limit saved $0.18/contract = $90 on 5 contracts",
            outcomeDetail: "Limit order at $3.29 filled in 28 seconds as SPY ticked slightly lower. 5 contracts × 100 × $0.18 = $90 saved instantly. Over 200 trades/year at this size: $18,000 in pure execution savings. Limit orders are free money.",
            outcomeColor: "#10b981",
        },
        takeaways: [
            "Limit orders are mandatory for options — never use market orders except in emergencies",
            "Start at mid-price; move 1 tick toward the market every 30 seconds if unfilled",
            "Stop-limit orders protect profits without the gap-through risk of stop-market",
            "GTC limit orders are ideal for low-premium entries on confirmed setups",
        ],
        closingLine: "Order discipline is edge — 94% fill rate with limit orders beats 100% fill at any price.",
    },
};

// ─── Visualization Scene: scrolling order book (for context) ─────────────────
const OrderBookVizScene: React.FC<{ color: string; dataPoints: OrderBookDataPoint[]; title: string }> = ({ color, dataPoints, title }) => {
    const frame = useCurrentFrame();
    const { durationInFrames } = useVideoConfig();
    const scrollOffset = interpolate(frame, [0, durationInFrames - 30], [0, -200], { extrapolateRight: "clamp" });

    return (
        <AbsoluteFill style={{ backgroundColor: "#0f1115", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
            <div style={{ fontSize: 14, fontWeight: 700, letterSpacing: "0.25em", color, textTransform: "uppercase", marginBottom: 20, opacity: 0.8 }}>Live Order Book</div>
            <h2 style={{ fontSize: 48, fontWeight: 800, color: "#f8fafc", margin: "0 0 32px", textAlign: "center" }}>{title}</h2>
            <div style={{
                display: "flex", flexDirection: "column", width: 700, height: 480,
                backgroundColor: "#1e293b", borderRadius: 16, border: "1px solid rgba(148,163,184,0.2)",
                overflow: "hidden",
            }}>
                <div style={{
                    display: "flex", flexDirection: "row", fontWeight: 700, color: "#94a3b8",
                    padding: "14px 20px", borderBottom: "1px solid rgba(148,163,184,0.2)",
                    textTransform: "uppercase", letterSpacing: "0.1em", fontSize: 18,
                }}>
                    <div style={{ flex: 1 }}>Bid Size</div>
                    <div style={{ flex: 1, textAlign: "center" }}>Price</div>
                    <div style={{ flex: 1, textAlign: "right" }}>Ask Size</div>
                </div>
                <div style={{ display: "flex", flexDirection: "column", position: "relative", flex: 1, transform: `translateY(${scrollOffset}px)` }}>
                    {dataPoints.slice(0, 15).map((dp, i) => (
                        <div key={i} style={{
                            display: "flex", flexDirection: "row", padding: "12px 20px",
                            borderBottom: "1px solid rgba(30,41,59,0.8)", fontSize: 22,
                            fontFamily: "monospace", alignItems: "center",
                        }}>
                            <div style={{ flex: 1, position: "relative", height: 28, display: "flex", alignItems: "center" }}>
                                {dp.bidSize > 0 && (
                                    <>
                                        <div style={{
                                            position: "absolute", right: 0, height: "100%",
                                            backgroundColor: "rgba(16,185,129,0.25)", borderRadius: "4px 0 0 4px",
                                            width: `${Math.min(100, dp.bidSize / 5)}%`,
                                        }} />
                                        <span style={{ position: "relative", zIndex: 1, color: "#4ade80", fontWeight: 700 }}>{dp.bidSize}</span>
                                    </>
                                )}
                            </div>
                            <div style={{ flex: 1, textAlign: "center", fontWeight: 700, color: "#fff" }}>{dp.price.toFixed(2)}</div>
                            <div style={{ flex: 1, position: "relative", height: 28, display: "flex", alignItems: "center", justifyContent: "flex-end" }}>
                                {dp.askSize > 0 && (
                                    <>
                                        <div style={{
                                            position: "absolute", left: 0, height: "100%",
                                            backgroundColor: "rgba(239,68,68,0.25)", borderRadius: "0 4px 4px 0",
                                            width: `${Math.min(100, dp.askSize / 5)}%`,
                                        }} />
                                        <span style={{ position: "relative", zIndex: 1, color: "#f87171", fontWeight: 700 }}>{dp.askSize}</span>
                                    </>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </AbsoluteFill>
    );
};

// ─── Main Component ────────────────────────────────────────────────────────────
export const MarketMechanicsVideo = ({
    title, subtitle, subjectLabel, posterUrl, accent, glow, mechanicType, dataPoints,
}: MarketMechanicsProps) => {
    const { durationInFrames } = useVideoConfig();

    // Map the registry's mechanicType + title to our MECHANICS_DATA keys
    // The registry entries use mechanicType but the actual lesson is identified by title.
    // We'll match on title keywords for robustness.
    const getMechanicsKey = (): string => {
        const t = title.toLowerCase();
        if (t.includes("chain") || t.includes("reading")) return "options-chain-reading";
        if (t.includes("bid") || t.includes("ask") || t.includes("spread")) return "bid-ask-reality";
        if (t.includes("tape") || t.includes("speed") || t.includes("volume")) return "tape-speed";
        if (t.includes("borrow") || t.includes("locate")) return "borrow-locate";
        if (t.includes("short") && t.includes("risk")) return "short-risk";
        if (t.includes("order") && t.includes("type")) return "order-types";
        // Fallback by mechanicType
        if (mechanicType === "tape") return "tape-speed";
        if (mechanicType === "option-chain") return "options-chain-reading";
        return "bid-ask-reality";
    };

    const key = getMechanicsKey();
    const data = MECHANICS_DATA[key] || MECHANICS_DATA["bid-ask-reality"];
    const ex = data.example;

    const defaultData = dataPoints || Array.from({ length: 15 }, (_, i) => ({
        price: 150.5 - i * 0.1 + 1.5,
        bidSize: Math.floor(Math.random() * 200),
        askSize: Math.floor(Math.random() * 200),
    }));

    const scenes: SceneDef[] = [
        // Scene 1: Title
        {
            render: () => (
                <TitleScene
                    label="Market Mechanics"
                    title={title}
                    subtitle={data.description}
                    accent={accent}
                />
            ),
        },
        // Scene 2: Key concepts bullets
        {
            render: () => (
                <BulletScene
                    heading="Key Concepts"
                    bullets={data.bullets}
                    accent={accent}
                />
            ),
        },
        // Scene 3: Order book / tape visualization (~20%)
        {
            durationInFrames: Math.floor(durationInFrames * 0.20),
            render: () => (
                <OrderBookVizScene color={accent} dataPoints={defaultData} title={data.label} />
            ),
        },
        // Scene 4: Animated SVG line chart (~22%)
        {
            durationInFrames: Math.floor(durationInFrames * 0.22),
            render: () => (
                <SvgLineChartScene
                    heading={data.chartHeading}
                    subheading={data.chartSubheading}
                    data={data.chartData}
                    accent={accent}
                    xLabel={data.chartXLabel}
                    yLabel={data.chartYLabel}
                    highlightIdx={data.chartHighlightIdx}
                    footnote={data.chartFootnote}
                />
            ),
        },
        // Scene 5: Real-world trade example (~24%)
        {
            durationInFrames: Math.floor(durationInFrames * 0.24),
            render: () => (
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
            ),
        },
        // Scene 6: Summary takeaways
        {
            render: () => (
                <SummaryScene
                    heading="Key Takeaways"
                    takeaways={data.takeaways}
                    accent={accent}
                    closingLine={data.closingLine}
                />
            ),
        },
    ];

    return <SceneManager scenes={scenes} background="#0f1115" />;
};
