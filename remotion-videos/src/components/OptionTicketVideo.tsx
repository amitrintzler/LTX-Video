import {
    AbsoluteFill,
    interpolate,
    useCurrentFrame,
    useVideoConfig,
} from "remotion";
import { SceneManager, TitleScene, BulletScene, SummaryScene, SvgLineChartScene, RealWorldExampleScene, type SceneDef } from "./SceneSystem";
import React from "react";

export type OptionTicketProps = {
    title: string;
    subtitle: string;
    accent: string;
    ticketType: "strike-zones" | "contract-details" | "contract-decomposition";
    underlyingPrice?: number;
    strikePrice?: number;
    daysToExpiry?: number;
};

// ─── Per-lesson data record ──────────────────────────────────────────────────

type TicketEntry = {
    lessonTitle: string;
    label: string;
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

const TICKET_DATA: Record<string, TicketEntry> = {
    "strike-zones": {
        lessonTitle: "Strike Selection",
        label: "Strike Zones: ITM, ATM, OTM",
        description: "Strike selection determines your risk/reward profile, breakeven point, and probability of profit. ITM, ATM, OTM each serve different strategies.",
        bullets: [
            "ITM (high delta): more expensive, higher probability of profit, lower leverage",
            "ATM (delta ~0.50): balanced risk/reward, ~50% probability, most liquid",
            "OTM (cheap): lottery ticket — high leverage but most expire worthless",
            "Strike price directly determines your breakeven point at expiration",
        ],
        takeaways: [
            "Start with ATM or slightly ITM for the best probability/cost balance",
            "OTM options need a large move — don't buy them hoping for miracles",
            "Use delta as your probability estimate: 0.50 delta = ~50% chance ITM",
            "Higher strike = cheaper premium but lower win rate — know your tradeoff",
        ],
        chartHeading: "Strike Moneyness vs Delta",
        chartSubheading: "AAPL Option Chain — Delta S-Curve",
        chartData: [
            { label: "$130 ITM", value: 0.85 },
            { label: "$140", value: 0.72 },
            { label: "$148", value: 0.55 },
            { label: "$150 ATM", value: 0.50 },
            { label: "$152", value: 0.44 },
            { label: "$160", value: 0.28 },
            { label: "$170 OTM", value: 0.12 },
        ],
        chartXLabel: "Strike Price",
        chartYLabel: "Delta",
        chartHighlightIdx: 3,
        chartFootnote: "ATM strike ($150) sits at delta 0.50 — the inflection point. Delta decays rapidly as strikes move OTM.",
        rwCompany: "AAPL",
        rwScenario: "AAPL trading at $190. Comparing $185 ATM call vs $195 OTM call on a $5 stock move over 2 weeks.",
        rwSetupItems: [
            { label: "$185 ATM Call", value: "$3.20 premium", color: "#3b82f6" },
            { label: "$195 OTM Call", value: "$0.85 premium" },
            { label: "Stock Move", value: "+$5 (to $195)" },
            { label: "ATM Delta", value: "0.52 at entry", color: "#3b82f6" },
        ],
        rwOutcome: "ATM returned +130%; OTM expired worthless",
        rwOutcomeDetail: "The $185 ATM call rose from $3.20 to $7.35 — a +130% gain. The $195 OTM call expired worthless with no intrinsic value despite the $5 move.",
        rwOutcomeColor: "#3b82f6",
    },
    "contract-details": {
        lessonTitle: "Contracts Walkthrough",
        label: "Understanding Options Contracts",
        description: "One options contract controls 100 shares. Understanding contract specs — expiry, multiplier, settlement — prevents costly mistakes.",
        bullets: [
            "1 contract = 100 shares: always multiply premium × 100 for the true cost",
            "Expiry date is the deadline — time value decays to zero by then",
            "American-style options can be exercised any time before expiration",
            "Assignment risk: short ITM options near expiry can be assigned unexpectedly",
        ],
        takeaways: [
            "Always multiply premium × 100 — a $1.00 option costs $100, not $1",
            "Never let short ITM options expire unmanaged near expiry",
            "Time value (extrinsic) is what you're paying beyond intrinsic value",
            "Even a $1 mistake in premium sizing = $100 minimum real-money impact",
        ],
        chartHeading: "Contract Time Value Decay",
        chartSubheading: "8-Week Extrinsic Value Countdown",
        chartData: [
            { label: "8wk", value: 4.80 },
            { label: "7wk", value: 4.20 },
            { label: "6wk", value: 3.65 },
            { label: "5wk", value: 3.10 },
            { label: "4wk", value: 2.55 },
            { label: "3wk", value: 1.95 },
            { label: "2wk", value: 1.30 },
            { label: "1wk", value: 0.65 },
        ],
        chartXLabel: "Weeks to Expiry",
        chartYLabel: "Extrinsic Value ($)",
        chartHighlightIdx: 7,
        chartFootnote: "Extrinsic value drops 87% from 8wk to 1wk. The last week sees accelerating theta decay — every day costs more.",
        rwCompany: "TSLA",
        rwScenario: "Bought 1 contract of TSLA $250 call for $8.50 ($850 total cost). Stock rose $20 over 3 weeks from $248 to $268.",
        rwSetupItems: [
            { label: "Contract", value: "1× TSLA $250 call", color: "#8b5cf6" },
            { label: "Entry Cost", value: "$8.50 × 100 = $850" },
            { label: "Stock Move", value: "+$20 (to $268)" },
            { label: "Exit Premium", value: "$15.20 per share", color: "#8b5cf6" },
        ],
        rwOutcome: "+$670 profit on 1 contract",
        rwOutcomeDetail: "The option rose from $8.50 to $15.20. Total exit value: $1,520. Profit: $670. The 100x multiplier turned an $8.50 gain into $670 real dollars.",
        rwOutcomeColor: "#10b981",
    },
    // Legacy key for backward compatibility
    "contract-decomposition": {
        lessonTitle: "Contracts Walkthrough",
        label: "Understanding Options Contracts",
        description: "One options contract controls 100 shares. Understanding contract specs — expiry, multiplier, settlement — prevents costly mistakes.",
        bullets: [
            "1 contract = 100 shares: always multiply premium × 100 for the true cost",
            "Expiry date is the deadline — time value decays to zero by then",
            "American-style options can be exercised any time before expiration",
            "Assignment risk: short ITM options near expiry can be assigned unexpectedly",
        ],
        takeaways: [
            "Always multiply premium × 100 — a $1.00 option costs $100, not $1",
            "Never let short ITM options expire unmanaged near expiry",
            "Time value (extrinsic) is what you're paying beyond intrinsic value",
            "Even a $1 mistake in premium sizing = $100 minimum real-money impact",
        ],
        chartHeading: "Contract Time Value Decay",
        chartSubheading: "8-Week Extrinsic Value Countdown",
        chartData: [
            { label: "8wk", value: 4.80 },
            { label: "7wk", value: 4.20 },
            { label: "6wk", value: 3.65 },
            { label: "5wk", value: 3.10 },
            { label: "4wk", value: 2.55 },
            { label: "3wk", value: 1.95 },
            { label: "2wk", value: 1.30 },
            { label: "1wk", value: 0.65 },
        ],
        chartXLabel: "Weeks to Expiry",
        chartYLabel: "Extrinsic Value ($)",
        chartHighlightIdx: 7,
        chartFootnote: "Extrinsic value drops 87% from 8wk to 1wk. The last week sees accelerating theta decay — every day costs more.",
        rwCompany: "TSLA",
        rwScenario: "Bought 1 contract of TSLA $250 call for $8.50 ($850 total cost). Stock rose $20 over 3 weeks from $248 to $268.",
        rwSetupItems: [
            { label: "Contract", value: "1× TSLA $250 call", color: "#8b5cf6" },
            { label: "Entry Cost", value: "$8.50 × 100 = $850" },
            { label: "Stock Move", value: "+$20 (to $268)" },
            { label: "Exit Premium", value: "$15.20 per share", color: "#8b5cf6" },
        ],
        rwOutcome: "+$670 profit on 1 contract",
        rwOutcomeDetail: "The option rose from $8.50 to $15.20. Total exit value: $1,520. Profit: $670. The 100x multiplier turned an $8.50 gain into $670 real dollars.",
        rwOutcomeColor: "#10b981",
    },
};

// ─── Strike Zone custom viz scene ────────────────────────────────────────────
const StrikeZoneScene: React.FC<{
    title: string; subtitle: string; accent: string;
    underlyingPrice: number;
}> = ({ title, subtitle, accent, underlyingPrice }) => {
    const frame = useCurrentFrame();
    const { fps, durationInFrames } = useVideoConfig();

    const titleOp = interpolate(frame, [0, fps], [0, 1], { extrapolateRight: "clamp" });
    const bodyOp = interpolate(frame, [fps, fps * 2], [0, 1], { extrapolateRight: "clamp" });
    const animProgress = interpolate(frame, [fps * 2, durationInFrames - fps], [0, 1], {
        extrapolateLeft: "clamp", extrapolateRight: "clamp",
    });

    const sliderOffset = interpolate(animProgress, [0, 1], [-15, 15]);
    const currentStrike = underlyingPrice + sliderOffset;
    const currentDelta = Math.max(0.05, Math.min(0.95, 0.5 + sliderOffset / 30));
    const probability = (currentDelta * 100).toFixed(0);
    const isITM = currentStrike < underlyingPrice;
    const isATM = Math.abs(currentStrike - underlyingPrice) < 2;
    const zone = isATM ? "ATM" : isITM ? "ITM" : "OTM";
    const zoneColor = isATM ? "#fbbf24" : isITM ? "#10b981" : "#94a3b8";

    return (
        <AbsoluteFill style={{ backgroundColor: "#080c12", fontFamily: "'Inter', sans-serif" }}>
            <div style={{ position: "absolute", top: 50, left: 0, right: 0, textAlign: "center", opacity: titleOp }}>
                <div style={{ fontSize: 13, fontWeight: 700, letterSpacing: "0.25em", color: accent, textTransform: "uppercase", marginBottom: 10 }}>Options Basics</div>
                <h1 style={{ fontSize: 68, fontWeight: 900, color: "#fff", margin: 0 }}>{title}</h1>
                <p style={{ fontSize: 32, color: "rgba(255,255,255,0.5)", marginTop: 12 }}>{subtitle}</p>
            </div>
            <div style={{ position: "absolute", top: 230, left: 0, right: 0, opacity: bodyOp, display: "flex", flexDirection: "column", alignItems: "center" }}>
                <div style={{ width: 1400, height: 100, borderRadius: 20, background: "linear-gradient(to right, #10b981, #fbbf24, #64748b)", position: "relative", overflow: "hidden" }}>
                    {["Deep ITM", "ITM", "ATM", "OTM", "Deep OTM"].map((label, i) => (
                        <span key={i} style={{
                            position: "absolute", top: "50%", left: `${i * 25}%`,
                            transform: "translate(-50%, -50%)", color: "#fff", fontSize: 22, fontWeight: 700, textShadow: "0 2px 8px #0006",
                        }}>{label}</span>
                    ))}
                </div>
                <div style={{ width: 1400, position: "relative", height: 60, marginTop: 0 }}>
                    <div style={{
                        position: "absolute", left: `calc(${((sliderOffset + 15) / 30) * 100}% - 20px)`,
                        top: 0, width: 4, height: 60, backgroundColor: "#fff", borderRadius: 4,
                        boxShadow: `0 0 24px ${zoneColor}`,
                    }} />
                </div>
                <div style={{
                    marginTop: 32, width: 900, borderRadius: 24, border: `2px solid ${zoneColor}`,
                    background: "rgba(255,255,255,0.04)", padding: "40px 60px", textAlign: "center",
                }}>
                    <div style={{ fontSize: 80, fontWeight: 900, color: zoneColor, marginBottom: 12 }}>{zone}</div>
                    <div style={{ display: "flex", justifyContent: "space-around", marginTop: 20 }}>
                        <div>
                            <div style={{ fontSize: 22, color: "rgba(255,255,255,0.4)" }}>Strike Price</div>
                            <div style={{ fontSize: 52, fontWeight: 800, color: "#fff" }}>${currentStrike.toFixed(0)}</div>
                        </div>
                        <div>
                            <div style={{ fontSize: 22, color: "rgba(255,255,255,0.4)" }}>Δ Delta</div>
                            <div style={{ fontSize: 52, fontWeight: 800, color: zoneColor }}>{currentDelta.toFixed(2)}</div>
                        </div>
                        <div>
                            <div style={{ fontSize: 22, color: "rgba(255,255,255,0.4)" }}>Prob. ITM</div>
                            <div style={{ fontSize: 52, fontWeight: 800, color: zoneColor }}>{probability}%</div>
                        </div>
                    </div>
                    <div style={{ marginTop: 24, fontSize: 26, color: "rgba(255,255,255,0.5)" }}>
                        {isITM ? "Option has real intrinsic value" : isATM ? "Maximum uncertainty — 50/50" : "All extrinsic (time) value only"}
                    </div>
                </div>
            </div>
        </AbsoluteFill>
    );
};

// ─── Contract Decomposition Scene (legacy viz) ──────────────────────────────
const DecompositionScene: React.FC<{
    title: string; subtitle: string; accent: string;
    underlyingPrice: number; strikePrice: number;
}> = ({ title, subtitle, accent, underlyingPrice, strikePrice }) => {
    const frame = useCurrentFrame();
    const { fps, durationInFrames } = useVideoConfig();

    const titleOp = interpolate(frame, [0, fps], [0, 1], { extrapolateRight: "clamp" });
    const bodyOp = interpolate(frame, [fps, fps * 2], [0, 1], { extrapolateRight: "clamp" });
    const animProgress = interpolate(frame, [fps * 2, durationInFrames - fps], [0, 1], {
        extrapolateLeft: "clamp", extrapolateRight: "clamp",
    });

    const dteSlide = interpolate(animProgress, [0, 1], [60, 1]);
    const extrinsic = (dteSlide / 60) * 3.2;
    const intrinsic = Math.max(0, underlyingPrice - strikePrice - 1);
    const totalPremium = intrinsic + extrinsic;
    const maxBar = 500;
    const intrinsicH = Math.min(maxBar, (intrinsic / 6) * maxBar);
    const extrinsicH = Math.min(maxBar, (extrinsic / 6) * maxBar);

    return (
        <AbsoluteFill style={{ backgroundColor: "#080c12", fontFamily: "'Inter', sans-serif" }}>
            <div style={{ position: "absolute", top: 50, left: 0, right: 0, textAlign: "center", opacity: titleOp }}>
                <div style={{ fontSize: 13, fontWeight: 700, letterSpacing: "0.25em", color: accent, textTransform: "uppercase", marginBottom: 10 }}>Options Basics</div>
                <h1 style={{ fontSize: 68, fontWeight: 900, color: "#fff", margin: 0 }}>{title}</h1>
                <p style={{ fontSize: 32, color: "rgba(255,255,255,0.5)", marginTop: 12 }}>{subtitle}</p>
            </div>
            <div style={{ position: "absolute", top: 250, left: 0, right: 0, display: "flex", alignItems: "flex-end", justifyContent: "center", gap: 80, opacity: bodyOp }}>
                <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                    <div style={{ fontSize: 48, fontWeight: 900, color: "#10b981", marginBottom: 12 }}>${intrinsic.toFixed(2)}</div>
                    <div style={{ width: 200, height: intrinsicH, backgroundColor: "#10b981", borderRadius: "12px 12px 0 0", minHeight: 4 }} />
                    <div style={{ width: 200, height: 4, backgroundColor: "rgba(255,255,255,0.1)" }} />
                    <div style={{ marginTop: 16, fontSize: 28, color: "#10b981", fontWeight: 700 }}>Intrinsic Value</div>
                    <div style={{ fontSize: 20, color: "rgba(255,255,255,0.4)", marginTop: 6 }}>Real, immediate worth</div>
                </div>
                <div style={{ fontSize: 72, color: "rgba(255,255,255,0.2)", marginBottom: 40 }}>+</div>
                <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                    <div style={{ fontSize: 48, fontWeight: 900, color: "#3b82f6", marginBottom: 12 }}>${extrinsic.toFixed(2)}</div>
                    <div style={{ width: 200, height: extrinsicH, backgroundColor: "#3b82f6", borderRadius: "12px 12px 0 0", minHeight: 4 }} />
                    <div style={{ width: 200, height: 4, backgroundColor: "rgba(255,255,255,0.1)" }} />
                    <div style={{ marginTop: 16, fontSize: 28, color: "#3b82f6", fontWeight: 700 }}>Extrinsic Value</div>
                    <div style={{ fontSize: 20, color: "rgba(255,255,255,0.4)", marginTop: 6 }}>Time + Volatility premium</div>
                </div>
                <div style={{ fontSize: 72, color: "rgba(255,255,255,0.2)", marginBottom: 40 }}>=</div>
                <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                    <div style={{ fontSize: 48, fontWeight: 900, color: accent, marginBottom: 12 }}>${totalPremium.toFixed(2)}</div>
                    <div style={{ width: 200, height: intrinsicH + extrinsicH, background: "linear-gradient(to top, #10b981, #3b82f6)", borderRadius: "12px 12px 0 0", minHeight: 4 }} />
                    <div style={{ width: 200, height: 4, backgroundColor: "rgba(255,255,255,0.1)" }} />
                    <div style={{ marginTop: 16, fontSize: 28, color: accent, fontWeight: 700 }}>Total Premium</div>
                    <div style={{ fontSize: 20, color: "rgba(255,255,255,0.4)", marginTop: 6, textAlign: "center" }}>DTE: {Math.floor(dteSlide)} days left</div>
                </div>
            </div>
            <div style={{ position: "absolute", bottom: 60, left: 0, right: 0, textAlign: "center", opacity: bodyOp }}>
                <div style={{ fontSize: 28, color: "rgba(255,255,255,0.4)" }}>← As time passes, extrinsic value decays toward zero (Theta)</div>
            </div>
        </AbsoluteFill>
    );
};

export const OptionTicketVideo: React.FC<OptionTicketProps> = ({
    title, subtitle, accent = "#3b82f6",
    ticketType = "strike-zones",
    underlyingPrice = 150, strikePrice = 150, daysToExpiry = 30,
}) => {
    const { durationInFrames } = useVideoConfig();
    const data = TICKET_DATA[ticketType] ?? TICKET_DATA["strike-zones"];

    const VisualizationScene = ticketType === "strike-zones"
        ? () => <StrikeZoneScene title={title} subtitle={subtitle} accent={accent} underlyingPrice={underlyingPrice} />
        : () => <DecompositionScene title={title} subtitle={subtitle} accent={accent} underlyingPrice={underlyingPrice} strikePrice={strikePrice} />;

    const scenes: SceneDef[] = [
        {
            render: () => (
                <TitleScene
                    label="Options Basics"
                    title={data.label}
                    subtitle={data.description}
                    accent={accent}
                />
            ),
        },
        {
            render: () => (
                <BulletScene
                    heading="How It Works"
                    bullets={data.bullets}
                    accent={accent}
                />
            ),
        },
        {
            durationInFrames: Math.floor(durationInFrames * 0.20),
            render: () => <VisualizationScene />,
        },
        {
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
                    accent={accent}
                />
            ),
        },
        {
            render: () => (
                <SummaryScene
                    heading="Key Takeaways"
                    takeaways={data.takeaways}
                    accent={accent}
                    closingLine="Understanding contracts and strike selection is fundamental to options trading success."
                />
            ),
        },
    ];

    return <SceneManager scenes={scenes} background="#080c12" />;
};
