import React, { useMemo } from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import {
  OPEN_WORLD_GAME_SIM_90_TITLE,
  OPEN_WORLD_GAME_SIM_CAPTIONS,
  OPEN_WORLD_GAME_SIM_SCENES,
} from "../data/openWorldGameSimScript";

const SCENE_FRAME = {
  city_establish: { from: 0, duration: 360 },
  arrival_briefing: { from: 360, duration: 540 },
  first_ticket_lab: { from: 900, duration: 660 },
  volatility_adjustment: { from: 1560, duration: 540 },
  debrief_agenda: { from: 2100, duration: 450 },
  cta_close: { from: 2550, duration: 150 },
} as const;

const backdropImage = staticFile("assets/videos/frame-home.png");
const worldImage = staticFile("assets/videos/frame-simulator.png");
const deskImage = staticFile("assets/videos/frame-pro-simulator.png");
const musicTrack = staticFile("assets/videos/audio-options.mp3");

const panelStyle = (accent: string): React.CSSProperties => ({
  border: `1px solid ${accent}88`,
  borderRadius: 18,
  padding: "24px 28px",
  background: "rgba(6,18,32,0.82)",
  boxShadow: `0 0 30px ${accent}2f`,
});

const ScenePanel: React.FC<{
  title: string;
  subtitle: string;
  bullets: string[];
  accent: string;
}> = ({ title, subtitle, bullets, accent }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const rise = spring({
    frame,
    fps,
    config: { damping: 180, stiffness: 120, mass: 0.8 },
  });

  return (
    <div
      style={{
        ...panelStyle(accent),
        transform: `translateY(${(1 - rise) * 26}px) scale(${0.96 + rise * 0.04})`,
        opacity: interpolate(frame, [0, 14], [0, 1], { extrapolateRight: "clamp" }),
      }}
    >
      <p style={{ margin: 0, color: accent, fontSize: 24, fontWeight: 700 }}>{title}</p>
      <p style={{ margin: "8px 0 0", color: "#d0ecff", fontSize: 34, fontWeight: 600, lineHeight: 1.12 }}>
        {subtitle}
      </p>
      <ul style={{ margin: "16px 0 0", paddingLeft: 22, color: "#ebf7ff", fontSize: 27, lineHeight: 1.22 }}>
        {bullets.map((bullet) => (
          <li key={bullet} style={{ marginBottom: 8 }}>
            {bullet}
          </li>
        ))}
      </ul>
    </div>
  );
};

const CaptionBand: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const second = frame / fps;

  const cue = useMemo(
    () => OPEN_WORLD_GAME_SIM_CAPTIONS.find((item) => second >= item.fromSec && second < item.toSec) ?? null,
    [second]
  );

  if (!cue) return null;

  return (
    <div
      style={{
        position: "absolute",
        left: "6%",
        right: "6%",
        bottom: 34,
        padding: "14px 18px",
        borderRadius: 12,
        border: "1px solid rgba(116, 219, 255, 0.5)",
        background: "rgba(4, 14, 26, 0.86)",
        color: "#eff9ff",
        fontSize: 32,
        fontWeight: 600,
        lineHeight: 1.18,
        textAlign: "center",
      }}
    >
      {cue.text}
    </div>
  );
};

export const OpenWorldGameSim90: React.FC = () => {
  const frame = useCurrentFrame();
  const pulse = 0.55 + Math.sin(frame * 0.03) * 0.2;
  const routeOffset = ((frame * 2.8) % 240) - 120;

  return (
    <AbsoluteFill
      style={{
        background:
          "radial-gradient(circle at 20% 14%, rgba(88,201,255,0.2), transparent 36%), radial-gradient(circle at 82% 86%, rgba(255,188,97,0.18), transparent 34%), linear-gradient(180deg, #0a1b2f 0%, #050d17 100%)",
        fontFamily: "\"Space Grotesk\", \"Manrope\", system-ui, sans-serif",
      }}
    >
      <Audio src={musicTrack} volume={0.28} />
      <Img src={backdropImage} style={{ width: "100%", height: "100%", objectFit: "cover", opacity: 0.23 }} />
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(110deg, rgba(66,182,255,0.18) 0%, transparent 44%), linear-gradient(300deg, rgba(255,177,101,0.14) 0%, transparent 40%)",
        }}
      />

      <AbsoluteFill style={{ pointerEvents: "none" }}>
        {Array.from({ length: 7 }, (_, i) => (
          <div
            key={`lane-${i}`}
            style={{
              position: "absolute",
              left: `${6 + i * 14}%`,
              top: 0,
              bottom: 0,
              width: 2,
              opacity: 0.14 + i * 0.02,
              background: `linear-gradient(180deg, rgba(112,212,255,${0.2 + pulse * 0.2}) 0%, transparent 100%)`,
              transform: `translateX(${routeOffset * (0.06 + i * 0.01)}px)`,
            }}
          />
        ))}
      </AbsoluteFill>

      <AbsoluteFill style={{ padding: "56px 64px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <p style={{ margin: 0, color: "#8fdfff", fontSize: 24, letterSpacing: 0.8 }}>Open-World Options City</p>
            <h1 style={{ margin: "8px 0 0", color: "#f0fbff", fontSize: 54, lineHeight: 1.05 }}>
              {OPEN_WORLD_GAME_SIM_90_TITLE}
            </h1>
          </div>
          <div style={{ ...panelStyle("#58d6ff"), padding: "12px 16px", minWidth: 280 }}>
            <p style={{ margin: 0, color: "#9fe7ff", fontSize: 18, textTransform: "uppercase" }}>Simulation Path</p>
            <p style={{ margin: "4px 0 0", color: "#e9f9ff", fontSize: 22, lineHeight: 1.2 }}>
              Objective → Action → Market Reaction → Debrief
            </p>
          </div>
        </div>
      </AbsoluteFill>

      <Sequence from={SCENE_FRAME.city_establish.from} durationInFrames={SCENE_FRAME.city_establish.duration} premountFor={30}>
        <AbsoluteFill style={{ padding: "180px 72px 120px", justifyContent: "flex-end" }}>
          <ScenePanel {...OPEN_WORLD_GAME_SIM_SCENES[0]} />
        </AbsoluteFill>
      </Sequence>

      <Sequence from={SCENE_FRAME.arrival_briefing.from} durationInFrames={SCENE_FRAME.arrival_briefing.duration} premountFor={30}>
        <AbsoluteFill style={{ padding: "170px 72px 120px", justifyContent: "flex-end" }}>
          <ScenePanel {...OPEN_WORLD_GAME_SIM_SCENES[1]} />
        </AbsoluteFill>
      </Sequence>

      <Sequence from={SCENE_FRAME.first_ticket_lab.from} durationInFrames={SCENE_FRAME.first_ticket_lab.duration} premountFor={30}>
        <AbsoluteFill style={{ padding: "138px 72px 124px", justifyContent: "space-between" }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18 }}>
            <Img src={worldImage} style={{ width: "100%", borderRadius: 14, opacity: 0.84, border: "1px solid rgba(117, 219, 255, 0.44)" }} />
            <Img src={deskImage} style={{ width: "100%", borderRadius: 14, opacity: 0.86, border: "1px solid rgba(117, 219, 255, 0.44)" }} />
          </div>
          <ScenePanel {...OPEN_WORLD_GAME_SIM_SCENES[2]} />
        </AbsoluteFill>
      </Sequence>

      <Sequence from={SCENE_FRAME.volatility_adjustment.from} durationInFrames={SCENE_FRAME.volatility_adjustment.duration} premountFor={30}>
        <AbsoluteFill style={{ padding: "170px 72px 120px", justifyContent: "flex-end" }}>
          <ScenePanel {...OPEN_WORLD_GAME_SIM_SCENES[3]} />
        </AbsoluteFill>
      </Sequence>

      <Sequence from={SCENE_FRAME.debrief_agenda.from} durationInFrames={SCENE_FRAME.debrief_agenda.duration} premountFor={30}>
        <AbsoluteFill style={{ padding: "170px 72px 120px", justifyContent: "flex-end" }}>
          <ScenePanel {...OPEN_WORLD_GAME_SIM_SCENES[4]} />
        </AbsoluteFill>
      </Sequence>

      <Sequence from={SCENE_FRAME.cta_close.from} durationInFrames={SCENE_FRAME.cta_close.duration} premountFor={20}>
        <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: 72 }}>
          <div style={{ ...panelStyle("#ffd68b"), maxWidth: 1280, textAlign: "center" }}>
            <p style={{ margin: 0, color: "#fff1d0", fontSize: 48, fontWeight: 700 }}>Launch Into Campaign Mode</p>
            <p style={{ margin: "12px 0 0", color: "#ffe7bb", fontSize: 30 }}>
              Complete your first meaningful options action in under 3 minutes.
            </p>
            <p style={{ margin: "18px 0 0", color: "#ffd68b", fontSize: 24 }}>
              Educational content only. Not investment advice.
            </p>
          </div>
        </AbsoluteFill>
      </Sequence>

      <CaptionBand />
    </AbsoluteFill>
  );
};

export default OpenWorldGameSim90;

