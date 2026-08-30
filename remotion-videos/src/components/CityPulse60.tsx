import React from "react";
import { AbsoluteFill, Sequence, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

export type CityPulse60Props = {
  title: string;
  regime: "calm" | "trending" | "panic";
  headline: string;
  checklist: string[];
};

const REGIME_COLOR: Record<CityPulse60Props["regime"], string> = {
  calm: "#39d7ff",
  trending: "#ffb664",
  panic: "#ff6d8e",
};

export const CityPulse60 = ({ title, regime, headline, checklist }: CityPulse60Props) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const glow = REGIME_COLOR[regime];
  const introOpacity = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: "clamp" });
  const panelScale = spring({
    frame,
    fps,
    config: { damping: 200, mass: 0.8 },
  });

  return (
    <AbsoluteFill
      style={{
        background:
          "radial-gradient(circle at 20% 20%, rgba(65,205,255,0.18), transparent 40%), linear-gradient(180deg, #041224 0%, #030b16 100%)",
        fontFamily: "Manrope, system-ui, sans-serif",
      }}
    >
      <AbsoluteFill
        style={{
          opacity: introOpacity,
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        <div
          style={{
            width: "82%",
            border: `1px solid ${glow}66`,
            borderRadius: 18,
            background: "rgba(6,20,36,0.9)",
            boxShadow: `0 0 30px ${glow}33`,
            transform: `scale(${0.9 + panelScale * 0.1})`,
            padding: "32px 36px",
          }}
        >
          <p style={{ margin: 0, color: "#9ddfff", fontSize: 28, letterSpacing: 0.6 }}>Options City Weekly Brief</p>
          <h1 style={{ margin: "8px 0 0", color: "#f2fbff", fontSize: 62, lineHeight: 1.05 }}>{title}</h1>
          <p style={{ margin: "16px 0 0", color: glow, fontSize: 30, fontWeight: 700 }}>
            Regime: {regime.toUpperCase()}
          </p>
        </div>
      </AbsoluteFill>

      <Sequence from={80}>
        <AbsoluteFill style={{ padding: "90px 110px" }}>
          <div
            style={{
              border: `1px solid ${glow}55`,
              borderRadius: 14,
              background: "rgba(8,24,40,0.92)",
              padding: "18px 22px",
              color: "#d7f5ff",
              fontSize: 34,
              lineHeight: 1.2,
              boxShadow: `0 0 24px ${glow}2f`,
            }}
          >
            {headline}
          </div>
        </AbsoluteFill>
      </Sequence>

      <Sequence from={260}>
        <AbsoluteFill style={{ padding: "120px 120px" }}>
          <div
            style={{
              border: "1px solid rgba(126,220,255,0.4)",
              borderRadius: 14,
              background: "rgba(8,23,38,0.9)",
              padding: "24px 28px",
            }}
          >
            <p style={{ margin: 0, color: "#8bd8ff", fontSize: 24, textTransform: "uppercase", letterSpacing: 1 }}>
              This Week Checklist
            </p>
            <ul style={{ margin: "14px 0 0", paddingLeft: 24, color: "#e9f9ff", fontSize: 34, lineHeight: 1.28 }}>
              {checklist.map((item, idx) => (
                <li key={idx} style={{ marginBottom: 10 }}>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </AbsoluteFill>
      </Sequence>

      <Sequence from={1450}>
        <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
          <div style={{ color: "#ffd68d", fontSize: 28 }}>Educational content only. Not investment advice.</div>
        </AbsoluteFill>
      </Sequence>
    </AbsoluteFill>
  );
};
