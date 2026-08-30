import { AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";

export type LessonWalkthroughProps = {
  title: string;
  subtitle: string;
  objectives: string[];
  subjectLabel: string;
  posterUrl?: string;
  accent: string;
  glow: string;
};

export const LessonWalkthrough = ({
  title,
  subtitle,
  objectives,
  subjectLabel,
  posterUrl,
  accent,
  glow,
}: LessonWalkthroughProps) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const enter = spring({
    frame,
    fps,
    config: {
      damping: 200,
      stiffness: 110,
      mass: 0.6,
    },
  });

  const overlayOpacity = interpolate(frame, [0, 24, 180, 220], [0.8, 0.35, 0.35, 0.65], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const safeObjectives = objectives.slice(0, 3);
  const resolvedPoster = posterUrl ? staticFile(posterUrl.replace(/^\//, "")) : null;

  return (
    <AbsoluteFill
      style={{
        background: "linear-gradient(140deg, #081226 0%, #0B1D3A 55%, #07162E 100%)",
        color: "#F8FAFC",
        fontFamily: "Inter, system-ui, sans-serif",
      }}
    >
      <AbsoluteFill
        style={{
          opacity: 0.26,
          background: `radial-gradient(circle at 78% 20%, ${glow} 0%, rgba(0,0,0,0) 48%)`,
        }}
      />

      {resolvedPoster ? (
        <AbsoluteFill>
          <Img
            src={resolvedPoster}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              opacity: 0.2,
            }}
          />
        </AbsoluteFill>
      ) : null}

      <AbsoluteFill
        style={{
          background: `linear-gradient(160deg, rgba(4,12,24,${overlayOpacity}) 0%, rgba(4,16,34,0.88) 100%)`,
        }}
      />

      <AbsoluteFill
        style={{
          padding: "64px 72px",
          transform: `translateY(${(1 - enter) * 20}px)`,
          opacity: enter,
          justifyContent: "space-between",
        }}
      >
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          <div
            style={{
              alignSelf: "flex-start",
              padding: "8px 14px",
              borderRadius: 999,
              border: `1px solid ${accent}`,
              backgroundColor: "rgba(8, 29, 58, 0.65)",
              fontSize: 22,
              letterSpacing: 0.8,
              textTransform: "uppercase",
            }}
          >
            Video Walkthrough
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            <div style={{ fontSize: 24, color: "#B7C7E7" }}>{subjectLabel}</div>
            <div style={{ fontSize: 64, lineHeight: 1.05, fontWeight: 800, maxWidth: 980 }}>{title}</div>
            <div style={{ fontSize: 30, color: "#D3DEEF", maxWidth: 920 }}>{subtitle}</div>
          </div>
        </div>

        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: 14,
            padding: "20px 24px",
            borderRadius: 24,
            border: "1px solid rgba(148, 163, 184, 0.36)",
            background: "rgba(8, 18, 38, 0.66)",
            maxWidth: 900,
          }}
        >
          <div style={{ fontSize: 24, color: "#A8B8D6", textTransform: "uppercase", letterSpacing: 0.8 }}>
            Practice Focus
          </div>
          {safeObjectives.map((objective, index) => (
            <div key={`${objective}-${index}`} style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
              <div
                style={{
                  width: 10,
                  height: 10,
                  marginTop: 12,
                  borderRadius: 999,
                  backgroundColor: accent,
                  boxShadow: `0 0 14px ${accent}`,
                  flexShrink: 0,
                }}
              />
              <div style={{ fontSize: 31, lineHeight: 1.25 }}>{objective}</div>
            </div>
          ))}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export default LessonWalkthrough;
