import {
    AbsoluteFill,
    interpolate,
    useCurrentFrame,
    useVideoConfig,
} from "remotion";
import { SceneManager, TitleScene, BulletScene, SummaryScene, SvgLineChartScene, RealWorldExampleScene, type SceneDef } from "./SceneSystem";
import React from "react";

export type GreekCurveProps = {
    title: string;
    subtitle: string;
    accent: string;
    greekType: "gamma" | "vega" | "rho";
    strike?: number;
    ivLow?: number;
    ivHigh?: number;
    rateLow?: number;
    rateHigh?: number;
};

const W = 1920;
const H = 1080;
const CX = 960;
const CY = 540;

const CURVE_DATA: Record<string, {
    description: string;
    bullets: string[];
    takeaways: string[];
    chart: { heading: string; subheading: string; data: Array<{ label: string; value: number }>; xLabel: string; yLabel: string; highlightIdx: number; footnote: string };
    example: { heading: string; company: string; scenario: string; setupItems: Array<{ label: string; value: string; color?: string }>; outcome: string; outcomeDetail: string; outcomeColor: string };
}> = {
    gamma: {
        description: "Gamma measures how fast your delta changes — it's the accelerator pedal of your options position. It peaks at-the-money and explodes near expiration.",
        bullets: [
            "Gamma is highest for ATM options — delta changes fastest near the strike",
            "Deep ITM and far OTM options have near-zero gamma (delta barely moves)",
            "Gamma increases as expiration approaches — last-week options are gamma bombs",
            "Long gamma benefits you: delta moves in your favor on both up and down moves",
        ],
        chart: {
            heading: "Gamma Acceleration Near Expiry",
            subheading: "ATM option gamma vs days-to-expiration — the closer to expiry, the more explosive",
            data: [
                { label: "60d", value: 0.02 }, { label: "45d", value: 0.03 }, { label: "30d", value: 0.05 },
                { label: "21d", value: 0.07 }, { label: "14d", value: 0.10 }, { label: "7d", value: 0.18 },
                { label: "3d", value: 0.31 }, { label: "1d", value: 0.52 },
            ],
            xLabel: "Days to Expiry",
            yLabel: "Gamma (Δ per $1)",
            highlightIdx: 5,
            footnote: "7 DTE (★) — gamma is 9× higher than at 60 DTE. Short gamma positions become extremely dangerous in final week",
        },
        example: {
            heading: "Real Trade: Gamma Risk at Expiry",
            company: "SPY — Short Put Near Expiry",
            scenario: "Sold a SPY $415 put for $1.20 with 3 DTE. SPY was at $418. Trade looked safe — only $3 OTM. Then SPY dropped $6 in one session.",
            setupItems: [
                { label: "SPY Price", value: "$418", color: "#94a3b8" },
                { label: "Strike", value: "$415", color: "#6366f1" },
                { label: "Premium Sold", value: "$1.20", color: "#10b981" },
                { label: "Gamma (entry)", value: "0.09", color: "#f59e0b" },
                { label: "SPY Drop", value: "-$6", color: "#ef4444" },
            ],
            outcome: "-$3.40 loss",
            outcomeDetail: "SPY fell to $412, put went ITM. Gamma exploded from 0.09 to 0.18 as it crossed the strike. Option surged from $1.20 to $4.60. Short gamma + fast move = max pain. Always respect gamma near expiry.",
            outcomeColor: "#ef4444",
        },
        takeaways: [
            "ATM options near expiry have explosive gamma risk",
            "Short gamma positions can blow up on large moves",
            "Use gamma to understand how your delta hedge will behave",
            "Gamma scalping profits from large moves in either direction",
        ],
    },
    vega: {
        description: "Vega measures how much an option's price changes for every 1% change in implied volatility. Longer-dated options carry dramatically more vega exposure.",
        bullets: [
            "A 45-DTE option has roughly 3× the vega of a 7-DTE option",
            "ATM options have the highest vega at any given expiration",
            "Buying options before earnings is primarily a vega bet",
            "IV crush after events can destroy option value even if direction is correct",
        ],
        chart: {
            heading: "Option Price vs. Implied Volatility",
            subheading: "45-DTE ATM call price as IV rises — each 1% IV change = vega dollars",
            data: [
                { label: "20%", value: 2.1 }, { label: "30%", value: 3.8 }, { label: "40%", value: 5.5 },
                { label: "50%", value: 7.2 }, { label: "60%", value: 8.9 }, { label: "70%", value: 10.6 },
                { label: "80%", value: 12.3 }, { label: "90%", value: 14.0 },
            ],
            xLabel: "Implied Volatility",
            yLabel: "Option Price ($)",
            highlightIdx: 3,
            footnote: "IV at 50% (★) — option worth $7.20. If IV collapses to 20% post-event, same option worth only $2.10. Direction-neutral IV crush = -71%",
        },
        example: {
            heading: "Real Trade: NVDA Earnings IV Crush",
            company: "NVDA — Earnings Call Buy",
            scenario: "NVDA reported Q3 FY2024 earnings. You bought a $460 call 2 days before the print for $18.40. IV was running at 82%. NVDA beat by 7.1% and jumped +9.3% — but something went wrong.",
            setupItems: [
                { label: "NVDA Price", value: "$460", color: "#94a3b8" },
                { label: "Call Paid", value: "$18.40", color: "#f59e0b" },
                { label: "IV (pre)", value: "82%", color: "#ef4444" },
                { label: "NVDA Move", value: "+9.3%", color: "#10b981" },
                { label: "IV (post)", value: "44%", color: "#6366f1" },
            ],
            outcome: "-$5.60 loss",
            outcomeDetail: "NVDA beat and jumped to $502. But IV collapsed from 82% to 44% — a 38-point crush. The call dropped from $18.40 to $12.80 despite correct direction. IV crush wiped more than the directional gain. Lesson: buying premium into earnings is a vega trap.",
            outcomeColor: "#ef4444",
        },
        takeaways: [
            "Buy options when IV is low relative to historical levels",
            "Sell options when IV is elevated (earnings, events)",
            "Calendar spreads exploit vega differences between expirations",
            "Vega risk is often underestimated by new traders",
        ],
    },
    rho: {
        description: "Rho measures sensitivity to interest rate changes. Usually negligible for short-dated options, it becomes significant for LEAPS (1+ year options) in high-rate environments.",
        bullets: [
            "Rising rates increase call values and decrease put values",
            "A 365-DTE option has ~8× the rho of a 30-DTE option",
            "In high-rate environments, rho's impact on LEAPS is meaningful",
            "Fed rate decisions directly affect long-dated option pricing",
        ],
        chart: {
            heading: "Rho Sensitivity vs. Days to Expiry",
            subheading: "Call option rho ($ change per 1% rate move) — grows dramatically with time",
            data: [
                { label: "7d", value: 0.01 }, { label: "30d", value: 0.05 }, { label: "60d", value: 0.12 },
                { label: "90d", value: 0.19 }, { label: "120d", value: 0.26 }, { label: "180d", value: 0.38 },
                { label: "270d", value: 0.52 }, { label: "365d", value: 0.58 },
            ],
            xLabel: "Days to Expiry",
            yLabel: "Rho ($ per 1% rate)",
            highlightIdx: 7,
            footnote: "365 DTE (★) — rho of $0.58. A 0.75% Fed hike on 10 LEAPS contracts = +$435 gain from rho alone",
        },
        example: {
            heading: "Real Trade: LEAPS and Fed Hike",
            company: "SPY — Long Call LEAPS",
            scenario: "Bought 10 SPY 365-DTE $400 calls when Fed funds rate was 3.5%. Each contract had rho = $0.58. Fed hiked 0.75% unexpectedly — a full three-quarter point move.",
            setupItems: [
                { label: "SPY Strike", value: "$400", color: "#6366f1" },
                { label: "DTE", value: "365d", color: "#94a3b8" },
                { label: "Rho/contract", value: "$0.58", color: "#0ea5e9" },
                { label: "Contracts", value: "10", color: "#f59e0b" },
                { label: "Rate Hike", value: "+0.75%", color: "#10b981" },
            ],
            outcome: "+$435 from rho",
            outcomeDetail: "0.75% hike × $0.58 rho × 10 contracts × 100 multiplier = +$435 purely from the rate move. Short-dated traders saw $0. LEAPS holders captured a $435 tailwind with zero stock movement. In rising rate cycles, long call LEAPS benefit — factor rho into your thesis.",
            outcomeColor: "#10b981",
        },
        takeaways: [
            "Rho is the least important Greek for short-term traders",
            "LEAPS holders must monitor Fed policy and rate expectations",
            "Rising rates are a tailwind for long call LEAPS",
            "Factor rho into cost-basis calculations for multi-year positions",
        ],
    },
};

// ─── Curve Scene (original visualization) ─────────────────────────────────────
const CurveScene: React.FC<GreekCurveProps> = ({
    title, subtitle, accent = "#f43f5e", greekType = "gamma",
    strike = 150, ivLow = 20, ivHigh = 55, rateLow = 3.5, rateHigh = 6.0,
}) => {
    const frame = useCurrentFrame();
    const { fps, durationInFrames } = useVideoConfig();

    const titleOpacity = interpolate(frame, [0, fps], [0, 1], { extrapolateRight: "clamp" });
    const chartProgress = interpolate(frame, [fps, fps * 3], [0, 1], {
        extrapolateLeft: "clamp", extrapolateRight: "clamp",
    });
    const animProgress = interpolate(frame, [fps * 3, durationInFrames - fps], [0, 1], {
        extrapolateLeft: "clamp", extrapolateRight: "clamp",
    });

    const chartL = 200, chartT = 200, chartW = 1520, chartH = 600;

    const renderGamma = () => {
        const steps = 300;
        const minP = strike - 15, maxP = strike + 15;
        const points = Array.from({ length: steps + 1 }, (_, i) => {
            const price = minP + (i / steps) * (maxP - minP);
            const dist = price - strike;
            const gamma = Math.exp(-0.5 * (dist * dist) / 4) * 0.12;
            const x = chartL + (i / steps) * chartW;
            const y = chartT + chartH - gamma * chartH * 0.9;
            return { x, y, price, gamma };
        });

        const sliderI = Math.floor(animProgress * steps);
        const sliderPt = points[Math.min(sliderI, points.length - 1)];
        const drawCount = Math.floor(chartProgress * points.length);
        const pathStr = points.slice(0, drawCount).map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ");
        const deltaApprox = (sliderPt?.price ?? strike) > strike ? 0.85 : 0.15;
        const gammaVal = (sliderPt?.gamma ?? 0).toFixed(4);
        const atATM = Math.abs((sliderPt?.price ?? 0) - strike) < 1.5;

        return (
            <svg width={W} height={H} style={{ position: "absolute", top: 0, left: 0 }}>
                <line x1={chartL} y1={chartT + chartH} x2={chartL + chartW} y2={chartT + chartH} stroke="rgba(255,255,255,0.15)" strokeWidth={2} />
                <line x1={chartL} y1={chartT} x2={chartL} y2={chartT + chartH} stroke="rgba(255,255,255,0.15)" strokeWidth={2} />
                <line x1={CX} y1={chartT} x2={CX} y2={chartT + chartH} stroke="rgba(255,255,255,0.2)" strokeWidth={1.5} strokeDasharray="12 8" />
                <text x={CX} y={chartT + chartH + 40} fill="rgba(255,255,255,0.4)" fontSize={24} textAnchor="middle">ATM (${strike})</text>
                {pathStr && <path d={pathStr} fill={`${accent}25`} stroke={accent} strokeWidth={5} strokeLinecap="round" />}
                {animProgress > 0 && sliderPt && (
                    <>
                        <line x1={sliderPt.x} y1={chartT} x2={sliderPt.x} y2={chartT + chartH} stroke="white" strokeWidth={2.5} strokeDasharray="10 6" opacity={0.7} />
                        <circle cx={sliderPt.x} cy={sliderPt.y} r={14} fill={atATM ? "#fbbf24" : accent} />
                        <circle cx={sliderPt.x} cy={sliderPt.y} r={7} fill="white" />
                        <rect x={sliderPt.x + 20} y={sliderPt.y - 50} width={240} height={96} rx={12} fill="rgba(0,0,0,0.75)" stroke={atATM ? "#fbbf24" : accent} strokeWidth={2} />
                        <text x={sliderPt.x + 35} y={sliderPt.y - 22} fill="rgba(255,255,255,0.6)" fontSize={20}>{`Δ Delta`}</text>
                        <text x={sliderPt.x + 35} y={sliderPt.y + 8} fill="#fff" fontWeight="bold" fontSize={28}>{deltaApprox.toFixed(2)}</text>
                        <text x={sliderPt.x + 35} y={sliderPt.y + 34} fill="rgba(255,255,255,0.5)" fontSize={18}>{`Γ Gamma: ${gammaVal}`}</text>
                    </>
                )}
                {atATM && animProgress > 0.3 && (
                    <text x={CX} y={chartT + 50} fill="#fbbf24" fontSize={32} textAnchor="middle" fontWeight="bold">⚡ GAMMA PEAKS AT ATM</text>
                )}
                <text x={chartL + chartW / 2} y={chartT + chartH + 80} fill="rgba(255,255,255,0.3)" fontSize={22} textAnchor="middle">Underlying Price</text>
                <text x={chartL - 50} y={chartT + chartH / 2} fill="rgba(255,255,255,0.3)" fontSize={22} textAnchor="middle" transform={`rotate(-90, ${chartL - 50}, ${chartT + chartH / 2})`}>Gamma Value</text>
            </svg>
        );
    };

    const renderVega = () => {
        const ivCurrent = interpolate(animProgress, [0, 1], [ivLow, ivHigh]);
        const shortPrice = 1.2 + (ivCurrent - ivLow) * 0.03;
        const longPrice = 3.8 + (ivCurrent - ivLow) * 0.22;
        const barMaxH = chartH * 0.7;
        const shortBarH = Math.min(barMaxH, (shortPrice / 8) * barMaxH);
        const longBarH = Math.min(barMaxH, (longPrice / 8) * barMaxH);
        const barY = chartT + chartH;

        return (
            <svg width={W} height={H} style={{ position: "absolute", top: 0, left: 0 }}>
                <text x={CX} y={chartT - 10} fill="rgba(255,255,255,0.5)" fontSize={26} textAnchor="middle" fontWeight="600">
                    Implied Volatility: <tspan fill={accent} fontWeight="900">{ivCurrent.toFixed(1)}%</tspan>
                </text>
                <rect x={chartL + 200} y={barY - shortBarH} width={280} height={shortBarH} rx={12} fill="rgba(59,130,246,0.55)" />
                <rect x={chartL + 200} y={barY - shortBarH} width={280} height={4} rx={2} fill="#3b82f6" />
                <text x={chartL + 340} y={barY + 44} fill="rgba(255,255,255,0.6)" fontSize={24} textAnchor="middle">7-DTE Option</text>
                <text x={chartL + 340} y={barY - shortBarH - 18} fill="white" fontSize={36} textAnchor="middle" fontWeight="bold">${shortPrice.toFixed(2)}</text>
                <rect x={chartL + chartW - 480} y={barY - longBarH} width={280} height={longBarH} rx={12} fill={`${accent}88`} />
                <rect x={chartL + chartW - 480} y={barY - longBarH} width={280} height={4} rx={2} fill={accent} />
                <text x={chartL + chartW - 340} y={barY + 44} fill="rgba(255,255,255,0.6)" fontSize={24} textAnchor="middle">45-DTE Option</text>
                <text x={chartL + chartW - 340} y={barY - longBarH - 18} fill="white" fontSize={36} textAnchor="middle" fontWeight="bold">${longPrice.toFixed(2)}</text>
                <text x={CX} y={barY + 96} fill={accent} fontSize={28} textAnchor="middle" fontWeight="bold">
                    {`45-DTE has ${((longPrice - 3.8) / Math.max(0.01, shortPrice - 1.2)).toFixed(1)}× more Vega sensitivity`}
                </text>
                <line x1={chartL} y1={barY} x2={chartL + chartW} y2={barY} stroke="rgba(255,255,255,0.15)" strokeWidth={2} />
            </svg>
        );
    };

    const renderRho = () => {
        const rateCurrent = interpolate(animProgress, [0, 1], [rateLow, rateHigh]);
        const callChange = (rateCurrent - rateLow) * 0.04;
        const putChange = -(rateCurrent - rateLow) * 0.04;
        const barY = chartT + chartH;
        const barMaxH = chartH * 0.6;

        const makeBar = (x: number, val: number, color: string, label: string) => {
            const h = Math.abs(val / 5) * barMaxH;
            const isPos = val >= 0;
            return (
                <>
                    <rect x={x} y={isPos ? barY - h : barY} width={200} height={h} rx={10} fill={color + "88"} />
                    <rect x={x} y={isPos ? barY - h : barY + h - 4} width={200} height={4} rx={2} fill={color} />
                    <text x={x + 100} y={barY + 40} fill="rgba(255,255,255,0.55)" fontSize={20} textAnchor="middle">{label}</text>
                    <text x={x + 100} y={isPos ? barY - h - 14 : barY + h + 40} fill="white" fontSize={28} textAnchor="middle" fontWeight="bold">
                        {val >= 0 ? "+" : ""}{val.toFixed(2)}
                    </text>
                </>
            );
        };

        return (
            <svg width={W} height={H} style={{ position: "absolute", top: 0, left: 0 }}>
                <text x={CX} y={chartT - 10} fill="rgba(255,255,255,0.5)" fontSize={26} textAnchor="middle" fontWeight="600">
                    Fed Rate: <tspan fill={accent} fontWeight="900">{rateCurrent.toFixed(2)}%</tspan>
                </text>
                <line x1={chartL} y1={barY} x2={chartL + chartW} y2={barY} stroke="rgba(255,255,255,0.15)" strokeWidth={2} />
                {makeBar(chartL + 80, callChange, "#10b981", "30-DTE Call Δ")}
                {makeBar(chartL + 340, putChange, "#ef4444", "30-DTE Put Δ")}
                {makeBar(chartL + 880, callChange * 8, "#10b981", "365-DTE Call Δ")}
                {makeBar(chartL + 1140, putChange * 8, "#ef4444", "365-DTE Put Δ")}
                <text x={chartL + 260} y={barY - barMaxH * 0.7} fill="rgba(255,255,255,0.3)" fontSize={22} textAnchor="middle">30 DTE</text>
                <text x={chartL + 1060} y={barY - barMaxH * 0.7} fill="rgba(255,255,255,0.3)" fontSize={22} textAnchor="middle">365 DTE</text>
                <line x1={chartL + 620} y1={chartT} x2={chartL + 620} y2={barY + 60} stroke="rgba(255,255,255,0.1)" strokeWidth={1} strokeDasharray="12 8" />
                <text x={CX} y={barY + 90} fill={accent} fontSize={26} textAnchor="middle" fontWeight="bold">
                    LEAPS are dramatically more sensitive to rate changes
                </text>
            </svg>
        );
    };

    return (
        <AbsoluteFill style={{ backgroundColor: "#080c12", fontFamily: "'Inter', 'SF Pro', sans-serif" }}>
            <div style={{ position: "absolute", top: 52, left: 0, right: 0, textAlign: "center", opacity: titleOpacity }}>
                <div style={{ fontSize: 14, fontWeight: 700, letterSpacing: "0.25em", color: accent, textTransform: "uppercase", marginBottom: 10 }}>
                    The Greeks
                </div>
                <h1 style={{ fontSize: 68, fontWeight: 900, color: "#fff", margin: 0, lineHeight: 1.1 }}>{title}</h1>
                <p style={{ fontSize: 32, color: "rgba(255,255,255,0.5)", marginTop: 10, fontWeight: 400 }}>{subtitle}</p>
            </div>
            {greekType === "gamma" && renderGamma()}
            {greekType === "vega" && renderVega()}
            {greekType === "rho" && renderRho()}
        </AbsoluteFill>
    );
};

export const GreekCurveVideo: React.FC<GreekCurveProps> = (props) => {
    const { durationInFrames } = useVideoConfig();
    const { accent = "#f43f5e", greekType = "gamma" } = props;
    const info = CURVE_DATA[greekType] || CURVE_DATA["gamma"];

    const greekLabels: Record<string, string> = { gamma: "Gamma", vega: "Vega", rho: "Rho" };
    const greekLabel = greekLabels[greekType] || "Gamma";

    if (durationInFrames < 600) {
        return <CurveScene {...props} />;
    }

    const ch = info.chart;
    const ex = info.example;

    const scenes: SceneDef[] = [
        // Scene 1: Title + concept
        { render: () => <TitleScene label={`The Greeks: ${greekLabel}`} title={props.title} subtitle={info.description} accent={accent} /> },
        // Scene 2: Key concepts
        { render: () => <BulletScene heading={`How ${greekLabel} Works`} bullets={info.bullets} accent={accent} /> },
        // Scene 3: Animated curve visualization
        { durationInFrames: Math.floor(durationInFrames * 0.20), render: () => <CurveScene {...props} /> },
        // Scene 4: Data chart with real numbers
        { durationInFrames: Math.floor(durationInFrames * 0.22), render: () => (
            <SvgLineChartScene
                heading={ch.heading}
                subheading={ch.subheading}
                data={ch.data}
                accent={accent}
                xLabel={ch.xLabel}
                yLabel={ch.yLabel}
                highlightIdx={ch.highlightIdx}
                footnote={ch.footnote}
            />
        )},
        // Scene 5: Real-world trade example
        { durationInFrames: Math.floor(durationInFrames * 0.24), render: () => (
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
        // Scene 6: Takeaways
        { render: () => <SummaryScene heading="Key Takeaways" takeaways={info.takeaways} accent={accent} closingLine={`Understanding ${greekLabel} helps you manage risk and find real opportunities.`} /> },
    ];

    return <SceneManager scenes={scenes} background="#080c12" />;
};
