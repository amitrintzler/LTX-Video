import React, { useMemo } from "react";
import {
  AbsoluteFill,
  Audio,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { Video } from "@remotion/media";
import {
  OPEN_WORLD_GAMEPLAY_PROOF_CALLOUTS,
  OPEN_WORLD_GAMEPLAY_PROOF_CAPTIONS,
  OPEN_WORLD_GAMEPLAY_PROOF_TITLE,
} from "../data/openWorldGameplayProofScript";

const gameplayMasterSrc = staticFile("assets/videos/open-world/game-demo/raw/openworld-gameplay-proof-master.mp4");
const musicTrack = staticFile("assets/videos/open-world/game-demo/music/cinematic-ambient.mp3");

const CaptionBand: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const second = frame / fps;

  const cue = useMemo(
    () => OPEN_WORLD_GAMEPLAY_PROOF_CAPTIONS.find((row) => second >= row.fromSec && second < row.toSec) ?? null,
    [second]
  );

  if (!cue) return null;

  return (
    <div
      style={{
        position: "absolute",
        left: "6%",
        right: "6%",
        bottom: 30,
        padding: "14px 18px",
        borderRadius: 12,
        border: "1px solid rgba(96, 196, 255, 0.52)",
        background: "rgba(4, 14, 26, 0.88)",
        color: "#eff9ff",
        fontSize: 34,
        fontWeight: 600,
        lineHeight: 1.14,
        textAlign: "center",
      }}
    >
      {cue.text}
    </div>
  );
};

const CalloutCard: React.FC<{
  title: string;
  detail: string;
  accent: string;
}> = ({ title, detail, accent }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = spring({
    frame,
    fps,
    config: { damping: 190, stiffness: 150, mass: 0.75 },
  });

  return (
    <div
      style={{
        position: "absolute",
        left: 44,
        bottom: 160,
        maxWidth: 620,
        borderRadius: 16,
        border: `1px solid ${accent}99`,
        background: "rgba(4, 13, 28, 0.84)",
        boxShadow: `0 0 24px ${accent}33`,
        padding: "18px 20px",
        transform: `translateY(${(1 - pop) * 20}px) scale(${0.96 + pop * 0.04})`,
        opacity: interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" }),
      }}
    >
      <p style={{ margin: 0, color: accent, fontSize: 28, fontWeight: 700 }}>{title}</p>
      <p style={{ margin: "6px 0 0", color: "#e6f5ff", fontSize: 32, fontWeight: 600, lineHeight: 1.1 }}>{detail}</p>
    </div>
  );
};

export const OpenWorldGameplayProof90: React.FC = () => {
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill
      style={{
        background: "#030a14",
        fontFamily: '"Space Grotesk", "Manrope", system-ui, sans-serif',
      }}
    >
      <Video src={gameplayMasterSrc} muted style={{ width: "100%", height: "100%", objectFit: "cover" }} trimAfter={90 * fps} />
      <Audio src={musicTrack} volume={0.24} loop />

      <AbsoluteFill
        style={{
          background:
            "linear-gradient(180deg, rgba(2,8,18,0.72) 0%, rgba(2,8,18,0.24) 24%, rgba(2,8,18,0.2) 64%, rgba(2,8,18,0.74) 100%)",
        }}
      />

      <AbsoluteFill style={{ padding: "30px 34px", pointerEvents: "none" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 14 }}>
          <div style={{ border: "1px solid rgba(97, 212, 255, 0.45)", borderRadius: 12, background: "rgba(7, 18, 36, 0.75)", padding: "10px 14px" }}>
            <p style={{ margin: 0, color: "#9fe7ff", fontSize: 20, letterSpacing: 0.7 }}>Open-World Options City</p>
            <p style={{ margin: "4px 0 0", color: "#eff9ff", fontSize: 32, fontWeight: 700 }}>{OPEN_WORLD_GAMEPLAY_PROOF_TITLE}</p>
          </div>
          <div style={{ border: "1px solid rgba(255, 208, 140, 0.5)", borderRadius: 12, background: "rgba(20, 14, 7, 0.72)", padding: "10px 14px", maxWidth: 510 }}>
            <p style={{ margin: 0, color: "#ffe8bf", fontSize: 18, textTransform: "uppercase" }}>Live Gameplay Proof</p>
            <p style={{ margin: "4px 0 0", color: "#fff4de", fontSize: 23, lineHeight: 1.2 }}>
              Objective → Action → Market Reaction → Debrief
            </p>
          </div>
        </div>
      </AbsoluteFill>

      {OPEN_WORLD_GAMEPLAY_PROOF_CALLOUTS.map((row) => (
        <Sequence
          key={row.id}
          from={Math.round(row.fromSec * fps)}
          durationInFrames={Math.max(1, Math.round((row.toSec - row.fromSec) * fps))}
          premountFor={Math.round(0.5 * fps)}
        >
          <CalloutCard title={row.title} detail={row.detail} accent={row.accent} />
        </Sequence>
      ))}

      <CaptionBand />

      <div
        style={{
          position: "absolute",
          right: 20,
          bottom: 18,
          borderRadius: 10,
          border: "1px solid rgba(255, 207, 125, 0.48)",
          background: "rgba(22, 15, 6, 0.74)",
          color: "#ffdca1",
          padding: "8px 12px",
          fontSize: 16,
          fontWeight: 600,
        }}
      >
        Educational content only. Not investment advice.
      </div>
    </AbsoluteFill>
  );
};

export default OpenWorldGameplayProof90;
