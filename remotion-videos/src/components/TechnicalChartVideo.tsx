import { AbsoluteFill, useVideoConfig, useCurrentFrame, interpolate } from "remotion";
import { SceneManager, TitleScene, BulletScene, SummaryScene, SvgLineChartScene, RealWorldExampleScene, type SceneDef } from "./SceneSystem";
import React from "react";
import { TEMPLATE_STYLES } from "../lib/templateStyles";

const S = TEMPLATE_STYLES["technical"];

export type TechnicalChartProps = {
    title: string;
    subtitle: string;
    subjectLabel: string;
    posterUrl: string;
    accent: string;
    glow: string;
    indicator: "candlesticks" | "rsi-macd" | "moving-averages" | "bollinger" | "momentum" | "support-resistance";
    candles: { open: number; high: number; low: number; close: number; volume?: number }[];
};

const CHART_WIDTH = 1200;
const CHART_HEIGHT = 500;

// ─── Per-lesson data record ──────────────────────────────────────────────────

type ChartEntry = {
    lessonTitle: string;
    description: string;
    bullets: string[];
    takeaways: string[];
    chartHeading: string;
    chartSubheading: string;
    chartData: { label: string; value: number }[];
    chartXLabel: string;
    chartYLabel: string;
    chartHighlightIdx: number;
    chartFootnote: string;
    rwCompany: string;
    rwScenario: string;
    rwSetupItems: { label: string; value: string; color?: string }[];
    rwOutcome: string;
    rwOutcomeDetail: string;
    rwOutcomeColor: string;
};

const CHART_DATA: Record<string, ChartEntry> = {
    "candlesticks": {
        lessonTitle: "Candlestick Patterns 101",
        description: "Japanese candlestick charts reveal market psychology. Each candle shows the open, high, low, and close, and patterns like doji, hammer, and engulfing signal potential reversals or continuations.",
        bullets: [
            "Doji: open ≈ close, indecision and potential reversal signal",
            "Hammer: small body + long lower wick, buyers rejecting lower prices",
            "Engulfing: large candle completely covers the prior candle's body",
            "Shooting star: small body + long upper wick, sellers rejecting higher prices",
        ],
        takeaways: [
            "Candlestick patterns reveal market psychology and momentum",
            "Volume confirms the strength of each candlestick signal",
            "Look for hammer and engulfing patterns at key support levels",
            "Combine patterns with support/resistance for higher probability trades",
        ],
        chartHeading: "SPY Candle Body Sizes",
        chartSubheading: "8 Days, Pattern Recognition Drill",
        chartData: [
            { label: "Mon", value: 0.3 },
            { label: "Tue", value: 1.2 },
            { label: "Wed", value: 0.1 },
            { label: "Thu", value: 2.8 },
            { label: "Fri", value: 0.2 },
            { label: "Mon", value: 3.1 },
            { label: "Tue", value: 0.4 },
            { label: "Wed", value: 4.2 },
        ],
        chartXLabel: "Trading Day",
        chartYLabel: "Candle Body Size ($)",
        chartHighlightIdx: 7,
        chartFootnote: "Large body on Wed = strong directional conviction. Tiny bodies (doji) signal indecision.",
        rwCompany: "AAPL",
        rwScenario: "Hammer candle formed at $165 support on above-average volume after a 3-week downtrend.",
        rwSetupItems: [
            { label: "Pattern", value: "Hammer Candle", color: "#f59e0b" },
            { label: "Support Level", value: "$165", color: "#10b981" },
            { label: "Entry", value: "$166.50 call" },
            { label: "Volume", value: "2.4× average", color: "#f59e0b" },
        ],
        rwOutcome: "+8% stock move over next 5 days",
        rwOutcomeDetail: "Stock rallied from $165 to $178. The hammer at support with volume confirmation provided a high probability entry.",
        rwOutcomeColor: "#10b981",
    },
    "support-resistance": {
        lessonTitle: "Support & Resistance Levels",
        description: "Support and resistance are price zones where buying or selling pressure has historically concentrated. Mastering these levels is foundational to reading any chart.",
        bullets: [
            "Support: price level where demand exceeds supply, acts as a floor",
            "Resistance: price level where supply exceeds demand, acts as a ceiling",
            "Old resistance becomes new support after a breakout (polarity reversal)",
            "More touches = stronger level, especially on higher timeframes",
        ],
        takeaways: [
            "Trade bounces off support and rejections at resistance",
            "Breakouts through key levels signal potential trend changes",
            "Volume spike at S/R confirms the level's significance",
            "Round numbers ($420, $450) often act as psychological S/R",
        ],
        chartHeading: "SPY Price, Bouncing Between $420 and $450",
        chartSubheading: "8 Week S/R Channel",
        chartData: [
            { label: "Wk1", value: 422 },
            { label: "Wk2", value: 438 },
            { label: "Wk3", value: 449 },
            { label: "Wk4", value: 421 },
            { label: "Wk5", value: 435 },
            { label: "Wk6", value: 448 },
            { label: "Wk7", value: 420 },
            { label: "Wk8", value: 442 },
        ],
        chartXLabel: "Week",
        chartYLabel: "SPY Price ($)",
        chartHighlightIdx: 6,
        chartFootnote: "$420 held as support 3x, each bounce confirmed the level. $450 resistance capped rallies twice.",
        rwCompany: "SPY",
        rwScenario: "SPY bounced off $420 support for the third time, a triple bottom formation with increasing volume on the bounce.",
        rwSetupItems: [
            { label: "Support Level", value: "$420", color: "#10b981" },
            { label: "Resistance", value: "$450 target", color: "#ef4444" },
            { label: "Entry", value: "ATM call at $422" },
            { label: "Touches", value: "3× tested $420", color: "#10b981" },
        ],
        rwOutcome: "+12% gain on SPY call",
        rwOutcomeDetail: "SPY rallied from $422 to $448 over 4 weeks. Triple touch of $420 support was the high-probability signal.",
        rwOutcomeColor: "#10b981",
    },
    "momentum": {
        lessonTitle: "Momentum Box Strategy",
        description: "Momentum measures the rate of price change. The Momentum Box strategy uses consolidation zones followed by high-volume breakouts to time explosive moves.",
        bullets: [
            "Rising momentum = accelerating price move, trend continuation likely",
            "Falling momentum while price rises = weakening trend, watch for reversal",
            "Momentum divergence is one of the earliest warning signs of exhaustion",
            "Consolidation boxes highlight tight ranges before breakout explosions",
        ],
        takeaways: [
            "Strong momentum above 70 RSI confirms trend continuation",
            "Divergence between price and momentum warns of reversals",
            "Consolidation boxes often precede the most explosive moves",
            "Use momentum alongside volume for breakout confirmation",
        ],
        chartHeading: "NVDA RSI Momentum Score",
        chartSubheading: "8 Periods, Breakout Progression",
        chartData: [
            { label: "Day1", value: 45 },
            { label: "Day2", value: 52 },
            { label: "Day3", value: 58 },
            { label: "Day4", value: 65 },
            { label: "Day5", value: 71 },
            { label: "Day6", value: 68 },
            { label: "Day7", value: 74 },
            { label: "Day8", value: 78 },
        ],
        chartXLabel: "Day",
        chartYLabel: "RSI Momentum Score",
        chartHighlightIdx: 4,
        chartFootnote: "RSI crossing 70 confirmed bullish momentum. Note the brief dip to 68 (healthy pullback) before continuation to 78.",
        rwCompany: "NVDA",
        rwScenario: "NVDA formed a 3-week consolidation box at $800. RSI climbed from 45 to 65 during consolidation, signaling building momentum.",
        rwSetupItems: [
            { label: "Entry Signal", value: "RSI 65 + Box breakout", color: "#6366f1" },
            { label: "RSI at Entry", value: "65, rising momentum" },
            { label: "Volume", value: "1.8× average on breakout", color: "#6366f1" },
            { label: "Position", value: "NVDA $820 call" },
        ],
        rwOutcome: "+15% stock move post-breakout",
        rwOutcomeDetail: "NVDA broke above the consolidation box at $800 with heavy volume. The momentum entry at RSI 65 captured the entire move to $920.",
        rwOutcomeColor: "#6366f1",
    },
    "rsi-macd": {
        lessonTitle: "RSI & MACD Signals",
        description: "RSI and MACD are the two most powerful oscillators in technical analysis. RSI identifies overbought/oversold conditions; MACD shows momentum shifts through moving average crossovers.",
        bullets: [
            "RSI above 70 = overbought; below 30 = oversold, mean reversion likely",
            "MACD line crossing above signal line = bullish momentum shift",
            "RSI divergence from price is one of the earliest reversal warnings",
            "Confluence of RSI oversold + MACD bullish cross = high probability entry",
        ],
        takeaways: [
            "Use RSI for overbought/oversold identification at extremes",
            "MACD crossovers confirm momentum direction shifts",
            "Confluence between RSI and MACD dramatically increases confidence",
            "Divergence between price and indicators warns of upcoming reversals",
        ],
        chartHeading: "META RSI Readings, Oversold Bounce",
        chartSubheading: "8 Week RSI Journey from Oversold",
        chartData: [
            { label: "Wk1", value: 62 },
            { label: "Wk2", value: 48 },
            { label: "Wk3", value: 35 },
            { label: "Wk4", value: 28 },
            { label: "Wk5", value: 38 },
            { label: "Wk6", value: 52 },
            { label: "Wk7", value: 61 },
            { label: "Wk8", value: 65 },
        ],
        chartXLabel: "Week",
        chartYLabel: "RSI Reading",
        chartHighlightIdx: 3,
        chartFootnote: "RSI hit 28 (oversold) at Wk4, the buy signal. Recovery from 28 to 65 mirrored a +22% stock gain.",
        rwCompany: "META",
        rwScenario: "META sold off 18% over 5 weeks. RSI crashed to 28 (oversold territory) while MACD showed a bullish cross forming.",
        rwSetupItems: [
            { label: "RSI Signal", value: "28, extreme oversold", color: "#ef4444" },
            { label: "MACD", value: "Bullish crossover confirmed" },
            { label: "Entry", value: "META ATM call" },
            { label: "Confluence", value: "RSI + MACD aligned", color: "#ef4444" },
        ],
        rwOutcome: "RSI recovered to 65, +22% stock gain",
        rwOutcomeDetail: "META bounced from the oversold RSI reading. The MACD bullish cross confirmed the reversal. Stock gained 22% from the signal point.",
        rwOutcomeColor: "#10b981",
    },
    "rsi-macd-mastery": {
        lessonTitle: "RSI & MACD Mastery",
        description: "Mastering RSI and MACD together means reading confluence signals, and when both indicators align, the probability of a successful trade increases significantly.",
        bullets: [
            "Confluence: RSI oversold + MACD bullish cross = strong buy signal",
            "Divergence: price makes new high but RSI doesn't, reversal warning",
            "MACD histogram shrinking toward zero signals momentum exhaustion",
            "RSI between 40 and 60 during uptrend = healthy trend, not overbought",
        ],
        takeaways: [
            "Wait for RSI + MACD alignment before entering, don't act on one alone",
            "Histogram direction tells you if momentum is accelerating or decelerating",
            "Use daily chart for signal, hourly for timing the entry",
            "Divergence setups often produce the biggest reward to risk trades",
        ],
        chartHeading: "AAPL MACD Histogram",
        chartSubheading: "8 Bars, Crossover Signal Formation",
        chartData: [
            { label: "D1", value: -2.1 },
            { label: "D2", value: -1.8 },
            { label: "D3", value: -1.2 },
            { label: "D4", value: -0.4 },
            { label: "D5", value: 0.3 },
            { label: "D6", value: 0.8 },
            { label: "D7", value: 1.4 },
            { label: "D8", value: 1.9 },
        ],
        chartXLabel: "Day",
        chartYLabel: "MACD Histogram",
        chartHighlightIdx: 4,
        chartFootnote: "Histogram crossed zero at D5, the bullish crossover moment. Each rising bar confirmed accelerating upside momentum.",
        rwCompany: "AAPL",
        rwScenario: "AAPL pulled back 12%. RSI hit 32 (near oversold) while the MACD histogram began compressing toward zero, a classic setup.",
        rwSetupItems: [
            { label: "RSI", value: "32, near oversold", color: "#f43f5e" },
            { label: "MACD", value: "Histogram → bullish cross", color: "#f43f5e" },
            { label: "Entry", value: "AAPL $185 call" },
            { label: "Signal Type", value: "RSI + MACD confluence" },
        ],
        rwOutcome: "+18% stock move following dual signal",
        rwOutcomeDetail: "AAPL rallied from $185 to $218 after the RSI 32 + MACD bullish cross. The $185 call returned several hundred percent.",
        rwOutcomeColor: "#10b981",
    },
    "bollinger": {
        lessonTitle: "Bollinger Bands & Volume",
        description: "Bollinger Bands use standard deviation to create dynamic price channels that expand during volatility and contract during calm. The squeeze precedes the explosion.",
        bullets: [
            "Middle band = 20-period SMA; upper/lower = ±2 standard deviations",
            "Bollinger Squeeze: bands narrow → volatility compression → expect breakout",
            "Walking the band: price touching upper band repeatedly = strong uptrend",
            "Volume spike on band break confirms the direction of the breakout",
        ],
        takeaways: [
            "Trade the squeeze: wait for bands to narrow, then trade the breakout direction",
            "Band walk = trend continuation, don't fight it until bands start widening",
            "Mean reversion: price tends to return to the middle band after extremes",
            "Combine Bollinger Bands with volume to avoid false breakouts",
        ],
        chartHeading: "SPY Bollinger Band Width",
        chartSubheading: "8-Week Squeeze → Expansion",
        chartData: [
            { label: "Wk1", value: 8.2 },
            { label: "Wk2", value: 6.1 },
            { label: "Wk3", value: 4.3 },
            { label: "Wk4", value: 2.8 },
            { label: "Wk5", value: 1.9 },
            { label: "Wk6", value: 3.4 },
            { label: "Wk7", value: 6.8 },
            { label: "Wk8", value: 9.1 },
        ],
        chartXLabel: "Week",
        chartYLabel: "Band Width ($)",
        chartHighlightIdx: 4,
        chartFootnote: "Band width hit 1.9 at Wk5 (the squeeze low). The subsequent expansion to 9.1 produced a massive directional move.",
        rwCompany: "SPY",
        rwScenario: "SPY Bollinger Bands compressed to the tightest width in 6 months at Wk5, signaling an imminent explosive move.",
        rwSetupItems: [
            { label: "Signal", value: "Bollinger Squeeze", color: "#0ea5e9" },
            { label: "Band Width", value: "1.9 (6-month low)", color: "#0ea5e9" },
            { label: "Entry", value: "SPY ATM calls at squeeze" },
            { label: "Volume", value: "Confirmed on breakout" },
        ],
        rwOutcome: "+9% SPY move after the squeeze breakout",
        rwOutcomeDetail: "SPY exploded higher after the Bollinger squeeze. Calls bought at the tightest band width returned strong gains as band width expanded to 9.1.",
        rwOutcomeColor: "#10b981",
    },
    "moving-averages": {
        lessonTitle: "Moving Averages System",
        description: "Moving averages smooth price data to reveal trends and act as dynamic support/resistance. The 20, 50, and 200 MAs form the backbone of most trading systems.",
        bullets: [
            "20 MA: short term trend, price above = bullish momentum",
            "50 MA: intermediate trend, key support in healthy uptrends",
            "200 MA: long term trend, the ultimate bull/bear dividing line",
            "Golden Cross (50 > 200 MA) signals major long term bullish shift",
        ],
        takeaways: [
            "Use the 200 MA as the ultimate bull/bear market dividing line",
            "Golden Cross (50 > 200) and Death Cross (50 < 200) are major signals",
            "Price bouncing off MA with volume = high probability trade entry",
            "Longer periods = fewer signals but higher reliability",
        ],
        chartHeading: "SPY Price vs 20-Week Moving Average",
        chartSubheading: "8 Week Golden Cross Formation",
        chartData: [
            { label: "Wk1", value: 412 },
            { label: "Wk2", value: 418 },
            { label: "Wk3", value: 415 },
            { label: "Wk4", value: 422 },
            { label: "Wk5", value: 428 },
            { label: "Wk6", value: 435 },
            { label: "Wk7", value: 441 },
            { label: "Wk8", value: 448 },
        ],
        chartXLabel: "Week",
        chartYLabel: "SPY Price ($)",
        chartHighlightIdx: 5,
        chartFootnote: "Price consistently stayed above the 20 MA from Wk4 onward. The 50MA crossed the 200MA (Golden Cross) at Wk5.",
        rwCompany: "SPY",
        rwScenario: "SPY 50 day MA crossed above the 200 day MA, a Golden Cross. Institutional buyers flooded in as the signal confirmed the new bull trend.",
        rwSetupItems: [
            { label: "Signal", value: "Golden Cross (50>200 MA)", color: "#10b981" },
            { label: "Entry", value: "SPY ATM calls" },
            { label: "Price at Signal", value: "$435", color: "#10b981" },
            { label: "Target", value: "$448 (next resistance)" },
        ],
        rwOutcome: "+11% over 30 days following the Golden Cross",
        rwOutcomeDetail: "SPY gained 11% in 30 days after the Golden Cross formed. MA-based signals on SPY are among the most reliable setups in the market.",
        rwOutcomeColor: "#10b981",
    },
};

// ─── Chart sub-component (kept for custom viz scene) ────────────────────────
const IndicatorPane = ({ type, data, y, height, color }: { type: "rsi" | "macd"; data: number[]; y: number; height: number; color: string }) => {
    const frame = useCurrentFrame();
    const visibleCount = Math.floor(frame / 2);
    const min = type === "rsi" ? 0 : Math.min(...data) - 1;
    const max = type === "rsi" ? 100 : Math.max(...data) + 1;
    const range = max - min;
    const points = data.slice(0, Math.min(visibleCount, data.length)).map((val, i) => {
        const x = (i / data.length) * CHART_WIDTH;
        const yPos = height - ((val - min) / range) * height;
        return `${i === 0 ? "M" : "L"}${x},${yPos}`;
    }).join(" ");
    return (
        <g transform={`translate(0, ${y})`}>
            <rect width={CHART_WIDTH} height={height} fill="rgba(255,255,255,0.03)" rx={4} />
            {type === "rsi" && (
                <>
                    <line x1={0} y1={height * 0.3} x2={CHART_WIDTH} y2={height * 0.3} stroke="rgba(239,68,68,0.3)" strokeDasharray="4 4" />
                    <line x1={0} y1={height * 0.7} x2={CHART_WIDTH} y2={height * 0.7} stroke="rgba(16,185,129,0.3)" strokeDasharray="4 4" />
                </>
            )}
            <path d={points} fill="none" stroke={color} strokeWidth={2.5} strokeLinecap="round" />
            <text x={-10} y={15} fill="rgba(255,255,255,0.4)" fontSize={14} textAnchor="end">{type.toUpperCase()}</text>
        </g>
    );
};

const ChartScene: React.FC<TechnicalChartProps> = ({
    title, accent = S.accent, indicator = "candlesticks", candles,
}) => {
    const frame = useCurrentFrame();

    const dummyCandles = candles || Array.from({ length: 50 }, (_, i) => {
        const base = 150 + Math.sin(i * 0.15) * 15;
        return { open: base + (Math.random() * 4 - 2), close: base + (Math.random() * 4 - 2), high: base + 5 + Math.random() * 2, low: base - 5 - Math.random() * 2 };
    });

    const maxPrice = Math.max(...dummyCandles.map(c => c.high));
    const minPrice = Math.min(...dummyCandles.map(c => c.low));
    const priceRange = maxPrice - minPrice || 1;
    const mapY = (price: number) => CHART_HEIGHT - ((price - minPrice) / priceRange) * CHART_HEIGHT;
    const visibleCount = Math.floor(frame / 2);

    const rsiData = dummyCandles.map((_, i) => 50 + Math.sin(i * 0.2) * 25 + (Math.random() * 10 - 5));
    const macdLine = dummyCandles.map((_, i) => Math.sin(i * 0.15) * 4);
    const sma50 = dummyCandles.map((c, i) => {
        const slice = dummyCandles.slice(Math.max(0, i - 10), i + 1);
        return slice.reduce((sum, curr) => sum + curr.close, 0) / slice.length;
    });

    return (
        <AbsoluteFill style={{ backgroundColor: S.bg }}>
            <div style={{ padding: 60, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%" }}>
                <div style={{ fontSize: 18, fontWeight: 700, letterSpacing: "0.2em", color: S.accent, textTransform: "uppercase", marginBottom: 16, textAlign: "center" }}>
                    Technical Analysis
                </div>
                <h2 style={{ fontSize: 48, fontWeight: 900, color: S.textPrimary, marginBottom: 32, textAlign: "center" }}>{title}</h2>
                <svg width={CHART_WIDTH} height={indicator === "rsi-macd" ? CHART_HEIGHT + 240 : CHART_HEIGHT} style={{ overflow: "visible" }}>
                    {Array.from({ length: 6 }).map((_, i) => (
                        <line key={`grid-${i}`} x1="0" y1={i * (CHART_HEIGHT / 5)} x2={CHART_WIDTH} y2={i * (CHART_HEIGHT / 5)} stroke="rgba(255,255,255,0.05)" strokeWidth="1" strokeDasharray="8 6" />
                    ))}
                    {indicator === "bollinger" && (
                        <path d={dummyCandles.slice(0, Math.min(visibleCount, dummyCandles.length)).map((c, i) => `${i === 0 ? "M" : "L"}${(i / dummyCandles.length) * CHART_WIDTH},${mapY(c.high + 2)}`).join(" ") + " " + dummyCandles.slice(0, Math.min(visibleCount, dummyCandles.length)).reverse().map((c, i) => `L${((Math.min(visibleCount, dummyCandles.length) - 1 - i) / dummyCandles.length) * CHART_WIDTH},${mapY(c.low - 2)}`).join(" ")} fill={`${accent}15`} stroke={`${accent}33`} strokeWidth={1} />
                    )}
                    {indicator === "support-resistance" && (
                        <>
                            <line x1={0} y1={mapY(maxPrice - 2)} x2={CHART_WIDTH} y2={mapY(maxPrice - 2)} stroke="#f87171" strokeWidth={2} strokeDasharray="12 8" opacity={0.6} />
                            <line x1={0} y1={mapY(minPrice + 2)} x2={CHART_WIDTH} y2={mapY(minPrice + 2)} stroke="#10b981" strokeWidth={2} strokeDasharray="12 8" opacity={0.6} />
                        </>
                    )}
                    {indicator === "moving-averages" && (
                        <path d={sma50.slice(0, Math.min(visibleCount, sma50.length)).map((val, i) => `${i === 0 ? "M" : "L"}${(i / dummyCandles.length) * CHART_WIDTH},${mapY(val)}`).join(" ")} fill="none" stroke={accent} strokeWidth={3} />
                    )}
                    {dummyCandles.slice(0, Math.min(visibleCount, dummyCandles.length)).map((candle, i) => {
                        const isBullish = candle.close >= candle.open;
                        const topY = mapY(Math.max(candle.open, candle.close));
                        const bottomY = mapY(Math.min(candle.open, candle.close));
                        const highY = mapY(candle.high);
                        const lowY = mapY(candle.low);
                        const x = (i / dummyCandles.length) * CHART_WIDTH;
                        const candleWidth = (CHART_WIDTH / dummyCandles.length) * 0.7;
                        return (
                            <g key={i}>
                                <line x1={x + candleWidth / 2} y1={highY} x2={x + candleWidth / 2} y2={lowY} stroke={isBullish ? S.accent : "#ef4444"} strokeWidth="2" />
                                <rect x={x} y={topY} width={candleWidth} height={Math.max(bottomY - topY, 2)} fill={isBullish ? S.accent : "#ef4444"} rx="1" />
                            </g>
                        );
                    })}
                    {indicator === "rsi-macd" && (
                        <>
                            <IndicatorPane type="rsi" data={rsiData} y={CHART_HEIGHT + 20} height={100} color="#8b5cf6" />
                            <IndicatorPane type="macd" data={macdLine} y={CHART_HEIGHT + 140} height={100} color="#ec4899" />
                        </>
                    )}
                    {indicator === "momentum" && visibleCount > 35 && (
                        <rect x={(35 / dummyCandles.length) * CHART_WIDTH} y={mapY(maxPrice - 1)} width={(15 / dummyCandles.length) * CHART_WIDTH} height={CHART_HEIGHT - mapY(maxPrice - 1)} fill="none" stroke="#fbbf24" strokeWidth={3} strokeDasharray="8 4" opacity={interpolate(visibleCount - 35, [0, 15], [0, 1])} />
                    )}
                </svg>
                <div style={{ marginTop: 24, display: "flex", gap: 32 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <div style={{ width: 16, height: 16, borderRadius: 8, backgroundColor: S.accent }} />
                        <span style={{ fontSize: 18, color: S.textSecondary }}>Bullish</span>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <div style={{ width: 16, height: 16, borderRadius: 8, backgroundColor: "#ef4444" }} />
                        <span style={{ fontSize: 18, color: S.textSecondary }}>Bearish</span>
                    </div>
                </div>
            </div>
        </AbsoluteFill>
    );
};

// ─── Indicator key → CHART_DATA key mapping ─────────────────────────────────
const INDICATOR_TO_KEY: Record<string, string> = {
    "candlesticks": "candlesticks",
    "support-resistance": "support-resistance",
    "momentum": "momentum",
    "rsi-macd": "rsi-macd",
    "bollinger": "bollinger",
    "moving-averages": "moving-averages",
};

// ─── Per-lesson title override map (keyed by registry title prop) ────────────
// We use a separate override so "rsi-macd-mastery" (same indicator) gets its own data.
const TITLE_KEY_OVERRIDE: Record<string, string> = {
    "RSI & MACD Mastery": "rsi-macd-mastery",
    "RSI & MACD Mastery Video": "rsi-macd-mastery",
};

export const TechnicalChartVideo = (props: TechnicalChartProps) => {
    const { durationInFrames } = useVideoConfig();

    // Resolve which data entry to use:
    // 1. Check title override (handles rsi-macd-mastery which shares the same indicator as rsi-macd)
    // 2. Fall back to indicator-keyed lookup
    const dataKey = TITLE_KEY_OVERRIDE[props.title] ?? INDICATOR_TO_KEY[props.indicator] ?? "candlesticks";
    const data = CHART_DATA[dataKey] ?? CHART_DATA["candlesticks"];

    const scenes: SceneDef[] = [
        {
            render: () => (
                <TitleScene
                    label="Technical Analysis"
                    title={data.lessonTitle}
                    subtitle={data.description}
                    accent={props.accent}
                />
            ),
        },
        {
            render: () => (
                <BulletScene
                    heading={`Understanding ${data.lessonTitle}`}
                    bullets={data.bullets}
                    accent={props.accent}
                />
            ),
        },
        {
            durationInFrames: Math.floor(durationInFrames * 0.20),
            render: () => <ChartScene {...props} />,
        },
        {
            render: () => (
                <SvgLineChartScene
                    heading={data.chartHeading}
                    subheading={data.chartSubheading}
                    data={data.chartData}
                    accent={props.accent}
                    xLabel={data.chartXLabel}
                    yLabel={data.chartYLabel}
                    highlightIdx={data.chartHighlightIdx}
                    footnote={data.chartFootnote}
                />
            ),
        },
        {
            render: () => (
                <RealWorldExampleScene
                    heading="Real Trade Example"
                    company={data.rwCompany}
                    scenario={data.rwScenario}
                    setupItems={data.rwSetupItems}
                    outcome={data.rwOutcome}
                    outcomeDetail={data.rwOutcomeDetail}
                    outcomeColor={data.rwOutcomeColor}
                    accent={props.accent}
                />
            ),
        },
        {
            render: () => (
                <SummaryScene
                    heading="Key Takeaways"
                    takeaways={data.takeaways}
                    accent={props.accent}
                    closingLine="Apply these technical signals to improve your entry timing and trade confidence."
                />
            ),
        },
    ];

    return <SceneManager scenes={scenes} theme={S} />;
};
