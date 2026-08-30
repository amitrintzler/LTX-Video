import {
    AbsoluteFill,
    interpolate,
    useCurrentFrame,
    useVideoConfig,
} from "remotion";
import React from "react";
import { SceneManager, TitleScene, BulletScene, SummaryScene, SvgLineChartScene, RealWorldExampleScene, type SceneDef, useSceneInfo } from "./SceneSystem";
import { TEMPLATE_STYLES } from "../lib/templateStyles";

const S = TEMPLATE_STYLES["options"];

/** Props controlling which strategy is shown */
export type PayoffDiagramProps = {
    title: string;
    subtitle: string;
    accent: string;
    strategyType:
    | "long-call"
    | "vertical"
    | "iron-condor"
    | "butterfly"
    | "calendar"
    | "straddle"
    | "strangle";
    underlyingPrice?: number;
    strike1?: number;
    strike2?: number;
    strike3?: number;
    strike4?: number;
    premium?: number;
    premium2?: number;
};

// ─── Layout constants ────────────────────────────────────────────────────────
const W = 1920;
const H = 1080;
const CHART_LEFT = 160;
const CHART_TOP = 200;
const CHART_W = 1600;
const CHART_H = 540;
const MIN_P = -10;
const MAX_P = 14;

function priceToX(price: number, minPrice: number, maxPrice: number) {
    return CHART_LEFT + ((price - minPrice) / (maxPrice - minPrice)) * CHART_W;
}
function plToY(pl: number) {
    return CHART_TOP + CHART_H - ((pl - MIN_P) / (MAX_P - MIN_P)) * CHART_H;
}

function buildPayoff(
    strategy: PayoffDiagramProps["strategyType"],
    s1: number, s2: number, s3: number, s4: number,
    premium: number, premium2: number,
    minPrice: number, maxPrice: number
): Array<{ x: number; pl: number; price: number }> {
    const steps = 200;
    const points = [];
    for (let i = 0; i <= steps; i++) {
        const price = minPrice + ((maxPrice - minPrice) * i) / steps;
        let pl = 0;
        if (strategy === "long-call") {
            pl = Math.max(0, price - s1) - premium;
        } else if (strategy === "vertical") {
            pl = Math.max(0, price - s1) - Math.max(0, price - s2) - premium;
        } else if (strategy === "iron-condor") {
            const putSpread = Math.max(0, s2 - price) - Math.max(0, s1 - price);
            const callSpread = Math.max(0, price - s3) - Math.max(0, price - s4);
            pl = premium - putSpread - callSpread;
        } else if (strategy === "butterfly") {
            pl = Math.max(0, price - s1) - 2 * Math.max(0, price - s2) + Math.max(0, price - s3) - premium;
        } else if (strategy === "calendar") {
            const dist = Math.abs(price - s1);
            pl = premium - (dist > 5 ? dist - 5 : 0) * 0.4 - 0.5;
        } else if (strategy === "straddle") {
            pl = Math.max(0, price - s1) + Math.max(0, s1 - price) - premium - premium2;
        } else if (strategy === "strangle") {
            pl = Math.max(0, price - s2) + Math.max(0, s1 - price) - premium - premium2;
        }
        points.push({ x: priceToX(price, minPrice, maxPrice), pl, price });
    }
    return points;
}

function pointsToPath(points: Array<{ x: number; pl: number }>, revealFraction: number) {
    const count = Math.floor(points.length * revealFraction);
    if (count < 2) return "";
    return points
        .slice(0, count)
        .map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)},${plToY(p.pl).toFixed(1)}`)
        .join(" ");
}

// ─── Rich per-strategy content data ──────────────────────────────────────────
const STRATEGY_DATA: Record<string, {
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
    "long-call": {
        description: "Buy a call option to profit from upward price movement with strictly limited downside risk equal to the premium paid.",
        bullets: [
            "Pay a premium upfront, this is your maximum possible loss",
            "You profit when stock rises above the strike + premium (breakeven)",
            "Leverage: control 100 shares for a fraction of the stock cost",
            "Call options gain intrinsic value dollar for dollar once in the money",
        ],
        chartData: [
            { label: "$90", value: -3.5 },
            { label: "$95", value: -3.5 },
            { label: "$100", value: -3.5 },
            { label: "$103.50★", value: 0 },
            { label: "$107", value: 3.5 },
            { label: "$112", value: 8.5 },
            { label: "$120", value: 16.5 },
        ],
        chartHeading: "Long Call P&L, Strike $100, Premium $3.50",
        chartSubheading: "Stock price at expiration vs. profit/loss per share",
        chartXLabel: "Stock Price at Expiration",
        chartYLabel: "P&L ($)",
        chartHighlightIdx: 3,
        chartFootnote: "Breakeven (★) = $103.50. Below $100 the option expires worthless. Above $103.50 every dollar is pure profit.",
        example: {
            heading: "Real Trade: AAPL $185 Call",
            company: "AAPL Bullish Earnings Play",
            scenario: "AAPL trading at $180. Bought the $185 call (21 DTE) for $3.50/share. Stock surged from $180 to $197 after a blowout earnings report.",
            setupItems: [
                { label: "Entry Price", value: "$180", color: "#94a3b8" },
                { label: "Strike", value: "$185", color: "#10b981" },
                { label: "Premium Paid", value: "$3.50", color: "#f59e0b" },
                { label: "Breakeven", value: "$188.50", color: "#6366f1" },
                { label: "Exit Price", value: "$197", color: "#10b981" },
            ],
            outcome: "+$4.50 per share (+128%)",
            outcomeDetail: "Stock moved from $180 to $197 (+$17). Option intrinsic value: $197 minus $185 = $12. Sold at $8.00. Net gain: $8.00 minus $3.50 = +$4.50. A 6.7% stock move turned into a 128% option return.",
            outcomeColor: "#10b981",
        },
        takeaways: [
            "Know your breakeven before entering, it's strike + premium paid",
            "Time works against you; buy enough DTE for your thesis to develop",
            "Take profits at 50 to 100% gain, don't let a winner expire worthless",
            "Size small, options expire; never risk more than you can afford to lose",
        ],
        closingLine: "The long call is the foundational options trade, limited risk and unlimited upside potential.",
    },

    "vertical": {
        description: "A bull call spread combines a long lower strike call with a short higher strike call to reduce cost and cap both risk and reward.",
        bullets: [
            "Buy the lower strike call, sell the higher strike call, net debit",
            "Max profit = spread width minus the net debit paid",
            "Max loss = the net debit, fully defined before you enter",
            "Breakeven = lower strike + net debit paid",
        ],
        chartData: [
            { label: "$460", value: -8.5 },
            { label: "$465", value: -8.5 },
            { label: "$470", value: -5.0 },
            { label: "$478.50★", value: 0 },
            { label: "$485", value: 12.0 },
            { label: "$490", value: 21.5 },
            { label: "$495+", value: 21.5 },
        ],
        chartHeading: "Bull Call Spread P&L, NVDA $470/$500 Spread",
        chartSubheading: "Net debit $8.50, max profit $21.50 if NVDA above $500 at expiry",
        chartXLabel: "Stock Price at Expiration",
        chartYLabel: "P&L ($)",
        chartHighlightIdx: 3,
        chartFootnote: "Breakeven (★) at $478.50. Max loss capped at $8.50 paid. Max profit capped at $21.50 above $500.",
        example: {
            heading: "Real Trade: NVDA $470/$500 Call Spread",
            company: "NVDA Earnings Momentum Trade",
            scenario: "NVDA at $465 before earnings. Bought the $470/$500 bull call spread for $8.50 net debit. AI demand thesis, expected a strong upward move.",
            setupItems: [
                { label: "Long Strike", value: "$470", color: "#10b981" },
                { label: "Short Strike", value: "$500", color: "#ef4444" },
                { label: "Net Debit", value: "$8.50", color: "#f59e0b" },
                { label: "Max Profit", value: "$21.50", color: "#10b981" },
                { label: "NVDA at Expiry", value: "$502", color: "#10b981" },
            ],
            outcome: "+$21.50 per share (+252%)",
            outcomeDetail: "NVDA surged to $502. Both legs were ITM, spread reached max value of $30. Paid $8.50, received $30.00. Net: +$21.50. Defined risk of $8.50 turned into 252% return.",
            outcomeColor: "#10b981",
        },
        takeaways: [
            "Vertical spreads cut premium cost vs. naked calls while keeping direction",
            "Max profit is capped at the short strike, pick it at your target price",
            "Break even is predictable before entry, plan your trade in advance",
            "Close at 50 to 75% of max profit to avoid gamma risk near expiry",
        ],
        closingLine: "Vertical spreads are the professional's tool, defined risk, defined reward, no surprises.",
    },

    "iron-condor": {
        description: "Sell both a put credit spread and a call credit spread simultaneously to collect premium and profit from a range-bound stock.",
        bullets: [
            "Sell an OTM put spread and an OTM call spread simultaneously",
            "Max profit = total credit received if stock stays between short strikes",
            "Max loss = spread width minus credit, only if stock breaks outside wings",
            "Theta positive: time decay works in your favor every day",
        ],
        chartData: [
            { label: "$400", value: -2.6 },
            { label: "$405", value: 2.4 },
            { label: "$410★", value: 2.4 },
            { label: "$420", value: 2.4 },
            { label: "$430★", value: 2.4 },
            { label: "$435", value: 2.4 },
            { label: "$440", value: -2.6 },
        ],
        chartHeading: "Iron Condor P&L, SPY $405p/$410p/$430c/$435c",
        chartSubheading: "$2.40 credit received, profit zone $410–$430 at expiration",
        chartXLabel: "SPY Price at Expiration",
        chartYLabel: "P&L ($)",
        chartHighlightIdx: 3,
        chartFootnote: "Short strikes (★) at $410 and $430 bracket the profit zone. SPY must stay inside for max $2.40 profit.",
        example: {
            heading: "Real Trade: SPY Iron Condor",
            company: "SPY Low Volatility Income Trade",
            scenario: "SPY at $420. IV Rank = 55. Sold the $405p/$410p/$430c/$435c iron condor for $2.40 credit. Expected SPY to stay in a $20 range through expiration.",
            setupItems: [
                { label: "SPY Price", value: "$420", color: "#94a3b8" },
                { label: "Short Put", value: "$410", color: "#10b981" },
                { label: "Short Call", value: "$430", color: "#10b981" },
                { label: "Credit Received", value: "$2.40", color: "#f59e0b" },
                { label: "SPY at Expiry", value: "$422", color: "#10b981" },
            ],
            outcome: "+$2.40 credit (+100% of premium)",
            outcomeDetail: "SPY expired at $422, squarely inside the $410 to $430 profit zone. Both spreads expired worthless. Full $2.40 credit kept. Max possible loss was $2.60. Risk/reward was 1:0.92, high probability, controlled risk.",
            outcomeColor: "#10b981",
        },
        takeaways: [
            "Set short strikes at the 1-sigma expected move for ~68% probability",
            "Collect at least 1/3 of the spread width in credit, otherwise skip it",
            "Close at 50% of max profit to eliminate tail risk in the last week",
            "Never hold iron condors through binary events like earnings or FOMC",
        ],
        closingLine: "The iron condor is the income trader's core tool, profit from time, not direction.",
    },

    "butterfly": {
        description: "A butterfly spread earns maximum profit when the stock pins exactly at the middle strike at expiration, delivering low cost and high reward.",
        bullets: [
            "Buy one call at lower strike, sell two calls at middle, buy one at upper",
            "Net debit is small, typically 10 to 25% of the spread width",
            "Max profit peaks at the middle strike at expiration",
            "Best used when expecting a quiet stock near a specific price target",
        ],
        chartData: [
            { label: "$440", value: -2.0 },
            { label: "$450", value: -2.0 },
            { label: "$460", value: 3.5 },
            { label: "$470★", value: 8.0 },
            { label: "$480", value: 3.5 },
            { label: "$490", value: -2.0 },
            { label: "$500", value: -2.0 },
        ],
        chartHeading: "Butterfly Spread P&L, SPX $450/$470/$490 Call Butterfly",
        chartSubheading: "Max profit $8.00 if SPX pins at $470, debit paid $2.00",
        chartXLabel: "SPX Price at Expiration",
        chartYLabel: "P&L ($)",
        chartHighlightIdx: 3,
        chartFootnote: "Peak profit (★) at $470, the middle strike. Move even $10 away and profit shrinks rapidly.",
        example: {
            heading: "Real Trade: SPX ATM Butterfly",
            company: "SPX Weekly Expiry Pin Trade",
            scenario: "SPX at $4,700 on Monday. Bought the ATM $4,680/$4,700/$4,720 weekly call butterfly for $2.00 debit. Thesis: SPX would close near $4,700 by Friday expiry.",
            setupItems: [
                { label: "Lower Wing", value: "$4,680", color: "#94a3b8" },
                { label: "Body (Short)", value: "$4,700", color: "#ec4899" },
                { label: "Upper Wing", value: "$4,720", color: "#94a3b8" },
                { label: "Debit Paid", value: "$2.00", color: "#f59e0b" },
                { label: "SPX at Expiry", value: "$4,703", color: "#10b981" },
            ],
            outcome: "+$6.00 per spread (+300%)",
            outcomeDetail: "SPX closed at $4,703, within $3 of the $4,700 body. Butterfly was worth $8.00. Paid $2.00, received $8.00. Net: +$6.00 on a $2.00 risk. 300% return in one week.",
            outcomeColor: "#10b981",
        },
        takeaways: [
            "Butterflies offer outstanding risk/reward but require precise price prediction",
            "Enter when you have a specific price target near current price",
            "Use weekly expirations, time decay collapses the wings rapidly",
            "Keep position size small, this is a probability trade, not a sure thing",
        ],
        closingLine: "The butterfly rewards patience and precision, low cost and asymmetric payoff at the pin.",
    },

    "calendar": {
        description: "A calendar spread profits from the difference in time decay between a near term short option and a longer dated long option at the same strike.",
        bullets: [
            "Sell a short dated option, buy a longer dated option at the same strike",
            "Near term option decays faster (higher theta), that gap is your profit",
            "Max profit occurs when stock is near the strike at near term expiration",
            "Net debit is small, the cost difference between the two expirations",
        ],
        chartData: [
            { label: "45 DTE", value: 3.80 },
            { label: "30 DTE", value: 3.20 },
            { label: "21 DTE", value: 2.55 },
            { label: "14 DTE★", value: 1.85 },
            { label: "7 DTE", value: 1.10 },
            { label: "3 DTE", value: 0.55 },
            { label: "0 DTE", value: 0.00 },
        ],
        chartHeading: "Near-Month vs Far-Month Theta Decay, SPY $440 Calendar",
        chartSubheading: "Short leg (near-month) decays faster, creating the calendar spread profit",
        chartXLabel: "Days to Near Expiration",
        chartYLabel: "Near-Leg Time Value ($)",
        chartHighlightIdx: 3,
        chartFootnote: "At 14 DTE (★) decay accelerates sharply, the sweet spot for calendar spread profit capture.",
        example: {
            heading: "Real Trade: SPY Calendar Spread",
            company: "SPY Theta Differential Harvest",
            scenario: "SPY at $440. Sold the 14 DTE $440 call for $2.80. Bought the 45 DTE $440 call for $4.00. Net debit: $1.20. Theta difference working daily in our favor.",
            setupItems: [
                { label: "Short Leg (14 DTE)", value: "$2.80 credit", color: "#10b981" },
                { label: "Long Leg (45 DTE)", value: "$4.00 debit", color: "#ef4444" },
                { label: "Net Debit", value: "$1.20", color: "#f59e0b" },
                { label: "Daily Theta Edge", value: "$0.06/day", color: "#8b5cf6" },
                { label: "SPY at Near Expiry", value: "$441", color: "#10b981" },
            ],
            outcome: "+$0.85 profit (+71% of debit)",
            outcomeDetail: "Near-month $440 call expired nearly worthless at $0.12. Far-month $440 call still worth $3.73. Closed the position: $3.73 − $0.12 − $1.20 net debit = +$0.85 profit. Theta differential delivered as planned.",
            outcomeColor: "#10b981",
        },
        takeaways: [
            "Calendar spreads earn from theta, time decay works for you, not against you",
            "Enter when stock is near the strike and you expect a quiet period",
            "IV term structure matters, best when near term IV is elevated vs far term",
            "Roll the short leg monthly to keep harvesting theta differential",
        ],
        closingLine: "Calendar spreads turn time decay into your ally, sell near, buy far, collect the difference.",
    },

    "straddle": {
        description: "Buy both a call and a put at the same strike to profit from a large move in either direction. Direction doesn't matter, magnitude does.",
        bullets: [
            "Buy one call AND one put at the same strike, total cost = both premiums",
            "Profit if stock moves sharply in either direction beyond the breakevens",
            "Ideal before binary events: earnings, FDA decisions, macro data",
            "Max loss = total premium paid if stock doesn't move at all",
        ],
        chartData: [
            { label: "$132", value: 14.0 },
            { label: "$140", value: 6.0 },
            { label: "$147", value: -1.0 },
            { label: "$150★", value: -8.0 },
            { label: "$153", value: -1.0 },
            { label: "$160", value: 6.0 },
            { label: "$168", value: 14.0 },
        ],
        chartHeading: "Straddle P&L, TSLA $150 Strike, $8 Total Premium",
        chartSubheading: "Breakeven at $142 and $158, stock must move ±$8 to profit",
        chartXLabel: "Stock Price at Expiration",
        chartYLabel: "P&L ($)",
        chartHighlightIdx: 3,
        chartFootnote: "Maximum loss (★) occurs at exactly the strike price. Any large move in either direction profits.",
        example: {
            heading: "Real Trade: TSLA Pre-Earnings Straddle",
            company: "TSLA Earnings Volatility Play",
            scenario: "TSLA at $250 before earnings. Bought the $250 straddle (call $10.20 + put $7.80) for $18.00 total. Breakeven: $232 and $268. Expected a big move from the print.",
            setupItems: [
                { label: "TSLA Pre-Earnings", value: "$250", color: "#94a3b8" },
                { label: "Call Premium", value: "$10.20", color: "#10b981" },
                { label: "Put Premium", value: "$7.80", color: "#ef4444" },
                { label: "Total Cost", value: "$18.00", color: "#f59e0b" },
                { label: "Breakevens", value: "±$18", color: "#6366f1" },
            ],
            outcome: "+$17.00 profit per share",
            outcomeDetail: "TSLA dropped $35 post-earnings to $215. Put was worth $35.00. Call expired worthless. Sold put for $35.00. Net: $35.00 − $18.00 paid = +$17.00. Stock moved $35, breakeven was ±$18. Thesis confirmed.",
            outcomeColor: "#10b981",
        },
        takeaways: [
            "Buy straddles when IV is low, expensive premium kills the trade",
            "Earnings and macro events are the classic straddle setup",
            "The move must exceed the total premium paid in either direction to profit",
            "Sell before expiry, straddles lose value rapidly from theta after the event",
        ],
        closingLine: "The straddle is pure volatility, when you know something will move but not which way.",
    },

    "strangle": {
        description: "Buy an OTM call and OTM put to profit from a large move at lower cost than a straddle, but requiring a bigger price swing to break even.",
        bullets: [
            "Buy an OTM put below and an OTM call above the current price",
            "Cheaper than a straddle but needs a larger move to profit",
            "Wider breakevens mean lower probability but higher reward if it moves big",
            "Implied volatility crushes both legs after a catalyst, time them right",
        ],
        chartData: [
            { label: "$125", value: 10.0 },
            { label: "$135", value: 2.0 },
            { label: "$140", value: -6.0 },
            { label: "$150★", value: -8.0 },
            { label: "$160", value: -6.0 },
            { label: "$165", value: 2.0 },
            { label: "$175", value: 10.0 },
        ],
        chartHeading: "Strangle P&L, OTM Put $140 / OTM Call $160, $8 Total",
        chartSubheading: "Breakeven at $132 and $168, wider than a straddle, lower cost",
        chartXLabel: "Stock Price at Expiration",
        chartYLabel: "P&L ($)",
        chartHighlightIdx: 3,
        chartFootnote: "Maximum loss (★) across the center zone. Profit only if stock moves well beyond the strikes.",
        example: {
            heading: "Real Trade: Strangle vs. Straddle Comparison",
            company: "AMZN Pre Earnings Strangle",
            scenario: "AMZN at $180 before earnings. Bought the $170p/$190c strangle for $6.00 total (vs $10.00 for the straddle). Wider breakevens: $164 and $196. Big move needed.",
            setupItems: [
                { label: "OTM Put", value: "$170 (−$3.20)", color: "#ef4444" },
                { label: "OTM Call", value: "$190 (+$2.80)", color: "#10b981" },
                { label: "Total Cost", value: "$6.00", color: "#f59e0b" },
                { label: "Breakevens", value: "$164 / $196", color: "#6366f1" },
                { label: "AMZN at Expiry", value: "$198", color: "#10b981" },
            ],
            outcome: "+$2.00 profit per share",
            outcomeDetail: "AMZN surged to $198. Call worth $8.00, put expired worthless. Sold call: $8.00 − $6.00 total paid = +$2.00. Compare to straddle: would have paid $10.00, net loss of −$2.00. Cheaper entry saved the trade.",
            outcomeColor: "#10b981",
        },
        takeaways: [
            "Strangles cost less than straddles but need bigger moves, know the tradeoff",
            "Use strangles when expecting a huge gap, not just a moderate move",
            "Monitor implied volatility, IV crush after an event destroys both legs",
            "Sell the profitable leg quickly, don't wait for the other to recover",
        ],
        closingLine: "The strangle is the high octane volatility bet, cheaper entry and bigger move required.",
    },
};

// ─── Payoff Diagram Animator (Scene 3) ───────────────────────────────────────
const PayoffDiagramAnimator: React.FC<{
    accent: string;
    strategyType: PayoffDiagramProps["strategyType"];
    underlyingPrice: number;
    strike1: number; strike2: number; strike3: number; strike4: number;
    premium: number; premium2: number;
    title: string;
    subtitle: string;
}> = ({ accent, strategyType, underlyingPrice, strike1, strike2, strike3, strike4, premium, premium2, title, subtitle }) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();
    const { sceneDuration } = useSceneInfo();

    const minPrice = underlyingPrice - 15;
    const maxPrice = underlyingPrice + 15;

    const titleOpacity = interpolate(frame, [0, Math.floor(sceneDuration * 0.06)], [0, 1], { extrapolateRight: "clamp" });

    const drawStart = Math.floor(sceneDuration * 0.06);
    const drawEnd   = Math.floor(sceneDuration * 0.35);
    const drawProgress = interpolate(frame, [drawStart, drawEnd], [0, 1], {
        extrapolateLeft: "clamp", extrapolateRight: "clamp",
    });

    const dotStart = drawEnd;
    const dotEnd   = Math.floor(sceneDuration * 0.90);
    const dotPrice = interpolate(frame, [dotStart, dotEnd], [minPrice, maxPrice], {
        extrapolateLeft: "clamp", extrapolateRight: "clamp",
    });

    const points = buildPayoff(strategyType, strike1, strike2, strike3, strike4, premium, premium2, minPrice, maxPrice);
    const dotPl = points[Math.floor((dotPrice - minPrice) / 30 * 200)]?.pl ?? 0;
    const dotX = priceToX(dotPrice, minPrice, maxPrice);
    const dotY = plToY(dotPl);
    const dotOpacity = interpolate(frame, [dotStart, dotStart + Math.floor(sceneDuration * 0.04)], [0, 1], { extrapolateRight: "clamp" });

    const zeroY = plToY(0);
    const pathStr = pointsToPath(points, drawProgress);
    const isProfit = dotPl > 0;

    return (
        <AbsoluteFill style={{ backgroundColor: S.bg, fontFamily: "'Inter', 'SF Pro', sans-serif" }}>
            <svg width={W} height={H} style={{ position: "absolute", top: 0, left: 0 }}>
                {/* Grid lines */}
                {[-8, -4, 0, 4, 8, 12].map((pl) => (
                    <g key={pl}>
                        <line x1={CHART_LEFT} y1={plToY(pl)} x2={CHART_LEFT + CHART_W} y2={plToY(pl)}
                            stroke={pl === 0 ? "rgba(255,255,255,0.3)" : "rgba(255,255,255,0.06)"}
                            strokeWidth={pl === 0 ? 2 : 1} strokeDasharray={pl === 0 ? "none" : "8 6"} />
                        <text x={CHART_LEFT - 12} y={plToY(pl) + 5} fill="rgba(255,255,255,0.4)" fontSize={22} textAnchor="end">
                            {pl > 0 ? `+$${pl}` : pl === 0 ? "$0" : `-$${Math.abs(pl)}`}
                        </text>
                    </g>
                ))}
                {[-10, -5, 0, 5, 10].map((offset) => {
                    const p = underlyingPrice + offset;
                    const x = priceToX(p, minPrice, maxPrice);
                    return (
                        <g key={offset}>
                            <line x1={x} y1={CHART_TOP} x2={x} y2={CHART_TOP + CHART_H} stroke="rgba(255,255,255,0.06)" strokeWidth={1} strokeDasharray="8 6" />
                            <text x={x} y={CHART_TOP + CHART_H + 36} fill="rgba(255,255,255,0.4)" fontSize={22} textAnchor="middle">${p}</text>
                        </g>
                    );
                })}

                {/* Fill areas */}
                <clipPath id="profitClip"><rect x={CHART_LEFT} y={CHART_TOP} width={CHART_W} height={zeroY - CHART_TOP} /></clipPath>
                <clipPath id="lossClip"><rect x={CHART_LEFT} y={zeroY} width={CHART_W} height={CHART_TOP + CHART_H - zeroY} /></clipPath>
                {pathStr && (
                    <>
                        <path d={pathStr} fill={S.accent} opacity={0.12} stroke="none" clipPath="url(#profitClip)" />
                        <path d={pathStr} fill="rgba(239,68,68,0.18)" stroke="none" clipPath="url(#lossClip)" />
                        <path d={pathStr} fill="none" stroke={S.accent} strokeWidth={4} strokeLinecap="round" strokeLinejoin="round" filter={`drop-shadow(0 0 18px ${S.glow})`} />
                    </>
                )}

                {/* Sliding dot */}
                {dotOpacity > 0 && (
                    <>
                        <line x1={dotX} y1={Math.min(dotY, zeroY)} x2={dotX} y2={Math.max(dotY, zeroY)}
                            stroke={isProfit ? "#10b981" : "#ef4444"} strokeWidth={2} strokeDasharray="6 4" opacity={dotOpacity} />
                        <circle cx={dotX} cy={dotY} r={12} fill={isProfit ? "#10b981" : "#ef4444"} opacity={dotOpacity} />
                        <circle cx={dotX} cy={dotY} r={6} fill="white" opacity={dotOpacity} />
                        <rect x={dotX - 52} y={CHART_TOP + CHART_H + 48} width={104} height={36} rx={8} fill={isProfit ? "#10b981" : "#ef4444"} opacity={dotOpacity} />
                        <text x={dotX} y={CHART_TOP + CHART_H + 72} fill="white" fontSize={20} fontWeight="bold" textAnchor="middle" opacity={dotOpacity}>${dotPrice.toFixed(0)}</text>
                        <rect x={dotX - 70} y={dotY - 36} width={140} height={32} rx={8} fill={isProfit ? "#10b981" : "#ef4444"} opacity={dotOpacity} />
                        <text x={dotX} y={dotY - 14} fill="white" fontSize={20} fontWeight="bold" textAnchor="middle" opacity={dotOpacity}>
                            {isProfit ? "+" : "-"}${Math.abs(dotPl).toFixed(2)}
                        </text>
                    </>
                )}

                {/* Strike lines */}
                {[strike1, strategyType !== "long-call" ? strike2 : null, ["iron-condor", "butterfly"].includes(strategyType) ? strike3 : null].filter(Boolean).map((s, i) => {
                    const sx = priceToX(s as number, minPrice, maxPrice);
                    return (
                        <g key={i}>
                            <line x1={sx} y1={CHART_TOP} x2={sx} y2={CHART_TOP + CHART_H}
                                stroke="rgba(255,255,255,0.2)" strokeWidth={1.5} strokeDasharray="10 6" />
                            <text x={sx} y={CHART_TOP - 12} fill="rgba(255,255,255,0.5)" fontSize={20} textAnchor="middle">${s}</text>
                        </g>
                    );
                })}
            </svg>

            {/* Title */}
            <div style={{ position: "absolute", top: 60, left: 0, right: 0, textAlign: "center", opacity: titleOpacity }}>
                <div style={{ fontSize: 14, fontWeight: 700, letterSpacing: "0.25em", color: S.accent, textTransform: "uppercase", marginBottom: 12 }}>Payoff Diagram</div>
                <h1 style={{ fontSize: 64, fontWeight: 900, color: S.textPrimary, margin: 0, lineHeight: 1.1 }}>{title}</h1>
                <p style={{ fontSize: 30, color: S.textSecondary, marginTop: 12, fontWeight: 400 }}>{subtitle}</p>
            </div>

            {/* Axis labels */}
            <div style={{ position: "absolute", left: CHART_LEFT + CHART_W / 2, top: CHART_TOP + CHART_H + 90, transform: "translateX(-50%)", color: "rgba(255,255,255,0.35)", fontSize: 20, fontWeight: 500 }}>Underlying Price at Expiration</div>
            <div style={{ position: "absolute", left: 28, top: CHART_TOP + CHART_H / 2, transform: "translateY(-50%) rotate(-90deg)", color: "rgba(255,255,255,0.35)", fontSize: 20, fontWeight: 500, transformOrigin: "center center", whiteSpace: "nowrap" }}>Profit / Loss</div>
        </AbsoluteFill>
    );
};

// ─── Main Component ───────────────────────────────────────────────────────────
export const PayoffDiagramVideo: React.FC<PayoffDiagramProps> = ({
    title,
    subtitle,
    accent = S.accent,
    strategyType = "long-call",
    underlyingPrice = 150,
    strike1 = 150,
    strike2 = 155,
    strike3 = 160,
    strike4 = 165,
    premium = 2.0,
    premium2 = 2.0,
}) => {
    const { durationInFrames } = useVideoConfig();

    // Use strategyType as the key into STRATEGY_DATA
    const data = STRATEGY_DATA[strategyType] || STRATEGY_DATA["long-call"];
    const ex = data.example;

    const scenes: SceneDef[] = [
        // Scene 1: Title
        {
            render: () => (
                <TitleScene
                    label="Options Strategy"
                    title={title}
                    subtitle={data.description}
                    accent={accent}
                />
            ),
        },
        // Scene 2: Key concepts bullet points
        {
            render: () => (
                <BulletScene
                    heading="Key Concepts"
                    bullets={data.bullets}
                    accent={accent}
                />
            ),
        },
        // Scene 3: Live payoff diagram animator (~20%)
        {
            durationInFrames: Math.floor(durationInFrames * 0.20),
            render: () => (
                <PayoffDiagramAnimator
                    accent={accent}
                    strategyType={strategyType}
                    underlyingPrice={underlyingPrice}
                    strike1={strike1}
                    strike2={strike2}
                    strike3={strike3}
                    strike4={strike4}
                    premium={premium}
                    premium2={premium2}
                    title={title}
                    subtitle={subtitle}
                />
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

    return <SceneManager scenes={scenes} theme={S} />;
};
