import { AbsoluteFill, Sequence, useVideoConfig, useCurrentFrame } from "remotion";
import { CinematicIntro } from "./CinematicIntro";
import { TEMPLATE_STYLES } from "../lib/templateStyles";
import React from "react";

const S = TEMPLATE_STYLES["strategy"];

export type OptionLeg = {
    type: "call" | "put";
    action: "buy" | "sell";
    strike: number;
    premium: number;
};

export type StrategyBuilderProps = {
    title: string;
    subtitle: string;
    subjectLabel: string;
    posterUrl: string;
    accent: string;
    glow: string;
    underlyingPrice: number;
    legs: OptionLeg[];
};

function strategyPLCurve(progress: number, legs: OptionLeg[], underlyingPrice: number): string {
    const W = 800, H = 520, mid = H / 2, scale = 18;
    const under = underlyingPrice || (legs[0]?.strike ?? 150);
    const points: string[] = [];
    const steps = 100;
    for (let i = 0; i <= steps; i++) {
        const price = under * 0.7 + (under * 0.6 * i) / steps;
        let pl = 0;
        for (const leg of legs) {
            const intrinsic = leg.type === "call"
                ? Math.max(0, price - leg.strike)
                : Math.max(0, leg.strike - price);
            pl += leg.action === "buy" ? intrinsic - leg.premium : leg.premium - intrinsic;
        }
        const x = (i / steps) * W;
        const y = mid - pl * scale * progress;
        points.push(`${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`);
    }
    return points.join(" ");
}

function strategyPLPath(progress: number, legs: OptionLeg[], underlyingPrice: number, zone: "profit" | "loss"): string {
    const W = 800, H = 520, mid = H / 2, scale = 18;
    const under = underlyingPrice || (legs[0]?.strike ?? 150);
    const pts: string[] = [];
    const steps = 100;
    for (let i = 0; i <= steps; i++) {
        const price = under * 0.7 + (under * 0.6 * i) / steps;
        let pl = 0;
        for (const leg of legs) {
            const intrinsic = leg.type === "call"
                ? Math.max(0, price - leg.strike)
                : Math.max(0, leg.strike - price);
            pl += leg.action === "buy" ? intrinsic - leg.premium : leg.premium - intrinsic;
        }
        const inZone = zone === "profit" ? pl > 0 : pl < 0;
        const x = (i / steps) * W;
        const y = mid - pl * scale * progress;
        if (inZone) pts.push(`${pts.length === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`);
    }
    if (pts.length) pts.push(`L${W},${mid} L0,${mid} Z`);
    return pts.join(" ");
}

const StrategyScene: React.FC<{
    title: string;
    subtitle: string;
    legs: OptionLeg[];
    underlyingPrice: number;
}> = ({ title, subtitle, legs, underlyingPrice }) => {
    const frame = useCurrentFrame();
    const legsVisible = Math.min(Math.floor(frame / 40) + 1, legs.length);
    const plProgress = Math.min((frame - legs.length * 40) / 90, 1);

    return (
        <AbsoluteFill style={{ background: S.bg, fontFamily: "Inter, sans-serif", display: "flex" }}>
            {/* Left: Legs panel */}
            <div style={{ width: 1056, padding: "80px 64px", display: "flex", flexDirection: "column", gap: 24 }}>
                <div style={{ fontSize: S.fontSizeTitle, fontWeight: 800, color: S.textPrimary, marginBottom: 8 }}>{title}</div>
                <div style={{ fontSize: S.fontSizeSubtitle, color: S.textSecondary, marginBottom: 40 }}>{subtitle}</div>
                {legs.slice(0, legsVisible).map((leg, i) => (
                    <div key={i} style={{
                        display: "flex", alignItems: "center", gap: 24,
                        background: leg.action === "buy" ? "rgba(245,158,11,0.12)" : "rgba(239,68,68,0.12)",
                        border: `2px solid ${leg.action === "buy" ? S.accent : "#ef4444"}`,
                        borderRadius: 12, padding: "20px 32px",
                    }}>
                        <span style={{ fontSize: 28, fontWeight: 700, color: leg.action === "buy" ? S.accent : "#ef4444", width: 80, textTransform: "uppercase" }}>
                            {leg.action}
                        </span>
                        <span style={{ fontSize: 28, color: S.textPrimary }}>
                            ${leg.strike} {leg.type.toUpperCase()}
                        </span>
                        <span style={{ marginLeft: "auto", fontSize: 28, color: S.textSecondary }}>
                            ${leg.premium.toFixed(2)}
                        </span>
                    </div>
                ))}
            </div>

            {/* Divider */}
            <div style={{ width: 2, background: S.accentDim, margin: "60px 0" }} />

            {/* Right: P&L diagram */}
            <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center" }}>
                <svg width={800} height={520} viewBox="0 0 800 520">
                    {/* Zero line */}
                    <line x1={0} y1={260} x2={800} y2={260} stroke={S.accentDim} strokeWidth={2} strokeDasharray="10 6" />
                    {/* Profit zone fill */}
                    <path d={strategyPLPath(Math.max(0, plProgress), legs, underlyingPrice, "profit")} fill={S.accent} opacity={0.18} />
                    {/* Loss zone fill */}
                    <path d={strategyPLPath(Math.max(0, plProgress), legs, underlyingPrice, "loss")} fill="#ef4444" opacity={0.18} />
                    {/* P&L curve */}
                    <path d={strategyPLCurve(Math.max(0, plProgress), legs, underlyingPrice)} fill="none" stroke={S.accent} strokeWidth={4}
                        filter={`drop-shadow(0 0 12px ${S.glow})`} />
                </svg>
            </div>
        </AbsoluteFill>
    );
};

export const StrategyBuilderVideo = ({
    title,
    subtitle,
    subjectLabel,
    posterUrl,
    accent,
    glow,
    underlyingPrice,
    legs,
}: StrategyBuilderProps) => {
    const { fps } = useVideoConfig();

    const introDuration = 4 * fps;
    const buildDuration = 8 * fps;

    return (
        <AbsoluteFill style={{ background: S.bg }}>
            {/* Scene 1: Cinematic Intro */}
            <Sequence from={0} durationInFrames={introDuration}>
                <CinematicIntro
                    title={title}
                    subtitle={subtitle}
                    subjectLabel={subjectLabel}
                    posterUrl={posterUrl}
                    accent={S.accent}
                    glow={S.glow}
                />
            </Sequence>

            {/* Scene 2: Strategy split layout */}
            <Sequence from={introDuration} durationInFrames={buildDuration}>
                <StrategyScene
                    title={title}
                    subtitle={subtitle}
                    legs={legs}
                    underlyingPrice={underlyingPrice}
                />
            </Sequence>
        </AbsoluteFill>
    );
};
