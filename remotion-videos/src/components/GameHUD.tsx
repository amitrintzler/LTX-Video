import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import type { DemoPalette } from "../data/demoScenes";

type GameHUDVariant = "score" | "combo" | "correct" | "levelup";

const hudCardStyle = (palette: DemoPalette) => ({
  background: "rgba(5, 9, 20, 0.65)",
  border: `1px solid ${palette.accent}`,
  borderRadius: 14,
  padding: "10px 16px",
  boxShadow: "0 12px 32px rgba(0,0,0,0.35)",
});

export const GameHUD = ({
  variant,
  palette,
  durationInFrames,
}: {
  variant: GameHUDVariant;
  palette: DemoPalette;
  durationInFrames: number;
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const enter = spring({
    frame,
    fps,
    config: { damping: 16, stiffness: 220 },
  });

  const fadeOut = interpolate(frame, [durationInFrames - fps * 0.6, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const opacity = interpolate(enter, [0, 1], [0, 1]) * fadeOut;
  const lift = interpolate(frame, [0, fps * 1.2], [16, 0], { extrapolateRight: "clamp" });

  const scoreValue = Math.round(
    interpolate(frame, [0, durationInFrames], [120, 1640], {
      extrapolateRight: "clamp",
    })
  );

  const comboValue = Math.min(5, 2 + Math.floor(frame / (fps * 0.8)));
  const comboPulse = 1 + Math.sin(frame / 3) * 0.06;

  const xpProgress = interpolate(frame, [0, durationInFrames * 0.8], [0.08, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity }}>
      {variant === "score" && (
        <>
          <div
            style={{
              position: "absolute",
              top: 34,
              left: 40,
              display: "flex",
              alignItems: "center",
              gap: 12,
              transform: `translateY(${lift}px)`,
              ...hudCardStyle(palette),
            }}
          >
            <span style={{ fontSize: 12, letterSpacing: 1.4, textTransform: "uppercase", color: "#c7d7ff" }}>
              Score
            </span>
            <span style={{ fontSize: 24, fontWeight: 700, color: "#ffffff" }}>{scoreValue}</span>
          </div>
          <div
            style={{
              position: "absolute",
              bottom: 40,
              left: 40,
              width: 320,
              height: 10,
              borderRadius: 999,
              background: "rgba(255,255,255,0.12)",
              overflow: "hidden",
              border: `1px solid ${palette.accentAlt}`,
            }}
          >
            <div
              style={{
                height: "100%",
                width: `${Math.max(6, Math.floor(xpProgress * 100))}%`,
                background: `linear-gradient(90deg, ${palette.accent}, ${palette.accentAlt})`,
                boxShadow: `0 0 16px ${palette.accent}`,
              }}
            />
          </div>
        </>
      )}

      {variant === "combo" && (
        <div
          style={{
            position: "absolute",
            top: 36,
            right: 40,
            transform: `translateY(${lift}px) scale(${comboPulse})`,
            ...hudCardStyle(palette),
            borderColor: palette.accentAlt,
          }}
        >
          <div style={{ fontSize: 12, letterSpacing: 1.2, textTransform: "uppercase", color: "#ffddc2" }}>Combo</div>
          <div style={{ fontSize: 26, fontWeight: 800, color: "#fff" }}>x{comboValue}</div>
        </div>
      )}

      {variant === "correct" && (
        <div
          style={{
            position: "absolute",
            top: "42%",
            left: "50%",
            transform: `translate(-50%, -50%) scale(${interpolate(enter, [0, 1], [0.6, 1.1])})`,
            padding: "16px 30px",
            borderRadius: 999,
            background: `linear-gradient(90deg, ${palette.accent}, ${palette.accentAlt})`,
            color: "#050914",
            fontSize: 32,
            fontWeight: 900,
            letterSpacing: 1.2,
            boxShadow: `0 16px 40px rgba(0,0,0,0.35)`,
          }}
        >
          Correct!
        </div>
      )}

      {variant === "levelup" && (
        <div
          style={{
            position: "absolute",
            bottom: 60,
            right: 40,
            transform: `translateY(${lift}px)`,
            ...hudCardStyle(palette),
            borderColor: palette.accentAlt,
          }}
        >
          <div style={{ fontSize: 12, letterSpacing: 1.4, textTransform: "uppercase", color: "#c9b8ff" }}>Level Up</div>
          <div style={{ fontSize: 24, fontWeight: 800, color: "#ffffff" }}>+ XP Boost</div>
          <div
            style={{
              marginTop: 8,
              height: 8,
              borderRadius: 999,
              background: "rgba(255,255,255,0.12)",
              overflow: "hidden",
              border: `1px solid ${palette.accent}`,
            }}
          >
            <div
              style={{
                height: "100%",
                width: `${Math.max(6, Math.floor(xpProgress * 100))}%`,
                background: `linear-gradient(90deg, ${palette.accentAlt}, ${palette.accent})`,
              }}
            />
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};
