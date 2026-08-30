import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";

import { OptionLeg } from "./StrategyBuilderVideo";

export type PayoffDiagramProps = {
    width?: number;
    height?: number;
    underlyingPrice: number;
    legs: OptionLeg[];
    accentColor?: string;
};

export const PayoffDiagramAnimator: React.FC<PayoffDiagramProps> = ({
    width = 1000,
    height = 600,
    underlyingPrice,
    legs,
    accentColor = "#4ade80"
}) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();

    // Animate the line drawing over 2 seconds (60 frames)
    const drawProgress = interpolate(frame, [15, 75], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

    // Compute the global breakeven and max/min strikes for scaling
    const strikes = legs.map(l => l.strike);
    const minStrike = Math.min(...strikes, underlyingPrice) - 20;
    const maxStrike = Math.max(...strikes, underlyingPrice) + 20;
    const priceRange = maxStrike - minStrike;

    // The logic to calculate profit at a specific price
    const calculateProfitAt = (price: number) => {
        return legs.reduce((acc, leg) => {
            const intrinsic = leg.type === "call"
                ? Math.max(0, price - leg.strike)
                : Math.max(0, leg.strike - price);

            const pnl = leg.action === "buy"
                ? intrinsic - leg.premium
                : leg.premium - intrinsic;

            return acc + pnl * 100; // x100 shares per contract
        }, 0);
    };

    // We'll draw an SVG path for the payoff curve.
    const mapX = (price: number) => ((price - minStrike) / priceRange) * width;

    // Find min/max profit to scale Y
    const samplePoints = Array.from({ length: 100 }, (_, i) => minStrike + (i * priceRange) / 100);
    const profits = samplePoints.map(calculateProfitAt);
    const maxProfit = Math.max(...profits, 100); // give some headroom
    const minProfit = Math.min(...profits, -100);
    const profitRange = maxProfit - minProfit;

    const zeroY = height * (maxProfit / profitRange);

    const mapY = (profit: number) => {
        return zeroY - (profit / profitRange) * height; // Invert Y because SVG 0 is at top
    };

    // Construct the SVG path
    let pathD = `M ${mapX(samplePoints[0])} ${mapY(profits[0])}`;
    for (let i = 1; i < samplePoints.length; i++) {
        pathD += ` L ${mapX(samplePoints[i])} ${mapY(profits[i])}`;
    }

    // Calculate total path length roughly
    const pathLength = 2000;
    const strokeDashoffset = pathLength - drawProgress * pathLength;

    return (
        <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
            <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{ overflow: "visible" }}>
                {/* Axes */}
                <line x1="0" y1={zeroY} x2={width} y2={zeroY} stroke="#334155" strokeWidth="4" />

                {/* Current Price Line */}
                <line
                    x1={mapX(underlyingPrice)}
                    y1="0"
                    x2={mapX(underlyingPrice)}
                    y2={height}
                    stroke="#334155"
                    strokeWidth="2"
                    strokeDasharray="10 10"
                />

                {/* Strikes Indicators */}
                {strikes.map((s, i) => (
                    <g key={i}>
                        <circle cx={mapX(s)} cy={zeroY} r="6" fill="#94a3b8" />
                        <text x={mapX(s)} y={zeroY + 30} fill="#94a3b8" fontSize="20" textAnchor="middle">${s}</text>
                    </g>
                ))}

                {/* Current Price Indicator */}
                <circle cx={mapX(underlyingPrice)} cy={zeroY} r="10" fill="#38bdf8" opacity={drawProgress} />
                <text x={mapX(underlyingPrice)} y={zeroY - 20} fill="#38bdf8" fontSize="24" textAnchor="middle" opacity={drawProgress}>
                    Stock: ${underlyingPrice}
                </text>

                {/* Payoff Curve */}
                <path
                    d={pathD}
                    fill="none"
                    stroke={accentColor}
                    strokeWidth="8"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeDasharray={pathLength}
                    strokeDashoffset={strokeDashoffset}
                    style={{ transition: "stroke-dashoffset 0.1s linear" }}
                />

                {/* Glow effect */}
                <path
                    d={pathD}
                    fill="none"
                    stroke={accentColor}
                    strokeWidth="20"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeDasharray={pathLength}
                    strokeDashoffset={strokeDashoffset}
                    opacity="0.2"
                    style={{ filter: "blur(8px)", transition: "stroke-dashoffset 0.1s linear" }}
                />
            </svg>
        </AbsoluteFill>
    );
};
