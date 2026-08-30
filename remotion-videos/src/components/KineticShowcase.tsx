import { AbsoluteFill, Audio, Easing, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Video } from "@remotion/media";
import type { CSSProperties } from "react";
import type { DemoConfig, DemoScene, DemoPalette } from "../data/demoScenes";
import { GameHUD } from "./GameHUD";

const badgeBase: CSSProperties = {
  padding: "6px 12px",
  borderRadius: 999,
  fontSize: 14,
  letterSpacing: 0.4,
  textTransform: "uppercase",
  boxShadow: "0 0 20px rgba(0,0,0,0.35)",
};

const Chip = ({ label, tone = "primary", palette }: { label: string; tone?: "primary" | "accent"; palette: DemoPalette }) => {
  const colors =
    tone === "accent"
      ? { bg: `${palette.glowA}`, border: palette.accent, text: "#e9f7ff" }
      : { bg: `${palette.glowB}`, border: palette.accentAlt, text: "#f3ecff" };
  return (
    <div
      style={{
        ...badgeBase,
        border: `1px solid ${colors.border}`,
        background: colors.bg,
        color: colors.text,
      }}
    >
      {label}
    </div>
  );
};

const KineticLines = ({ lines, align, localFrame }: { lines: string[]; align: "left" | "right"; localFrame: number }) => {
  const { fps } = useVideoConfig();
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6, textAlign: align }}>
      {lines.map((line, idx) => {
        const start = 8 + idx * 8;
        const progress = spring({
          fps,
          frame: Math.max(localFrame - start, 0),
          config: { damping: 14, stiffness: 120 },
        });
        const translate = interpolate(progress, [0, 1], [12, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
        const opacity = interpolate(progress, [0, 1], [0, 1]);
        return (
          <div
            key={idx}
            style={{
              fontSize: 24,
              color: "#d8e1ff",
              letterSpacing: 0.3,
              opacity,
              transform: `translateY(${translate}px)`,
            }}
          >
            {line}
          </div>
        );
      })}
    </div>
  );
};

const MockBoard = ({
  variant,
  palette,
  localFrame,
  cardsOverride,
}: {
  variant: NonNullable<DemoScene["mock"]>;
  palette: DemoPalette;
  localFrame: number;
  cardsOverride?: string[];
}) => {
  const { fps } = useVideoConfig();
  const progress = spring({ fps, frame: localFrame, config: { damping: 18, stiffness: 140 } });
  const float = interpolate(localFrame, [0, fps * 6], [0, -12], { extrapolateRight: "clamp" });
  const cards =
    cardsOverride && cardsOverride.length > 0
      ? cardsOverride
      : variant === "idea"
      ? ["Idea: Physics", "Audience: 16-18", "Outcome: Gravity intuition"]
      : variant === "pipeline"
      ? ["Template", "Story mode", "Game layer", "Simulator"]
      : ["Blueprint", "Lesson nodes", "Assessments"];

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        background: `radial-gradient(circle at 20% 20%, ${palette.glowA}, transparent 40%), radial-gradient(circle at 80% 70%, ${palette.glowB}, transparent 35%)`,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(2, minmax(260px, 1fr))",
          gap: 18,
          transform: `translateY(${float}px) scale(${interpolate(progress, [0, 1], [0.96, 1])})`,
          opacity: progress,
        }}
      >
        {cards.map((label, idx) => (
          <div
            key={label}
            style={{
              padding: "20px 22px",
              borderRadius: 16,
              border: `1px solid ${idx % 2 === 0 ? palette.accent : palette.accentAlt}`,
              background: "rgba(7, 12, 30, 0.75)",
              color: "#e7e2ff",
              fontSize: 20,
              fontWeight: 600,
              boxShadow: "0 20px 40px rgba(0,0,0,0.35)",
            }}
          >
            {label}
          </div>
        ))}
      </div>
    </div>
  );
};

const SceneFrame = ({
  scene,
  palette,
  sceneDuration,
}: {
  scene: DemoScene;
  palette: DemoPalette;
  sceneDuration: number;
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const localFrame = frame;

  const slowDrift = interpolate(localFrame, [0, sceneDuration], [-24, 18], {
    easing: Easing.bezier(0.65, 0, 0.35, 1),
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const scale = interpolate(localFrame, [0, sceneDuration * 0.6, sceneDuration], [1.05, 1.12, 1.08], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const shakeIntensity = interpolate(localFrame, [0, 12, 24], [10, 6, 0], {
    extrapolateRight: "clamp",
  });
  const shakeX = Math.sin(localFrame * 0.9) * shakeIntensity;
  const shakeY = Math.cos(localFrame * 1.2) * shakeIntensity * 0.6;
  const spin = interpolate(localFrame, [0, sceneDuration], [0.4, -0.4], {
    extrapolateRight: "clamp",
  });

  const glowPulse = interpolate(localFrame, [0, sceneDuration / 2, sceneDuration], [0.25, 0.85, 0.3]);
  const flashOpacity = interpolate(localFrame, [0, 6, 16], [0.75, 0.25, 0], {
    extrapolateRight: "clamp",
  });

  const titleSpring = spring({
    fps,
    frame: localFrame,
    config: { damping: 18, stiffness: 180 },
  });

  const badgeStagger = spring({
    fps,
    frame: localFrame - 8,
    config: { damping: 16, stiffness: 160 },
  });

  const chipAlign = scene.focus === "right" ? "flex-end" : "flex-start";
  const textAlign = scene.focus === "right" ? "right" : "left";

  return (
    <AbsoluteFill style={{ background: palette.base, overflow: "hidden" }}>
      {scene.clipSrc ? (
        <Video
          src={staticFile(scene.clipSrc)}
          muted
          style={{
            width: "110%",
            height: "110%",
            objectFit: "cover",
            position: "absolute",
            top: "-5%",
            left: "-5%",
            transform: `translate(${slowDrift + shakeX}px, ${shakeY}px) scale(${scale}) rotate(${spin}deg)`,
            filter: "brightness(1.02) contrast(1.12) saturate(1.1)",
          }}
        />
      ) : (
        <MockBoard
          variant={scene.mock ?? "cards"}
          palette={palette}
          localFrame={localFrame}
          cardsOverride={scene.mockCards}
        />
      )}

      <div
        style={{
          position: "absolute",
          inset: 0,
          background: `radial-gradient(circle at 20% 20%, ${palette.glowA}, transparent 35%), radial-gradient(circle at 80% 80%, ${palette.glowB}, transparent 32%)`,
          mixBlendMode: "screen",
          opacity: glowPulse,
        }}
      />
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "linear-gradient(180deg, rgba(5,9,20,0.15) 0%, rgba(5,9,20,0.7) 75%), radial-gradient(circle at 50% 0%, rgba(0,0,0,0.25), transparent 45%)",
        }}
      />
      {flashOpacity > 0 && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            background: "rgba(255,255,255,0.2)",
            mixBlendMode: "screen",
            opacity: flashOpacity,
          }}
        />
      )}

      <div
        style={{
          position: "absolute",
          top: 44,
          left: 60,
          right: 60,
          display: "flex",
          justifyContent: chipAlign,
          gap: 10,
        }}
      >
        <Chip label="Live gameplay" palette={palette} />
        <Chip label="Hands-on" tone="accent" palette={palette} />
      </div>

      {scene.tag && (
        <div
          style={{
            position: "absolute",
            top: 110,
            left: scene.focus === "right" ? "auto" : 80,
            right: scene.focus === "right" ? 80 : "auto",
            padding: "6px 12px",
            borderRadius: 12,
            border: `1px solid ${palette.accentAlt}`,
            background: "rgba(12, 15, 34, 0.7)",
            color: "#f5e9ff",
            fontSize: 14,
            textTransform: "uppercase",
            letterSpacing: 0.4,
          }}
        >
          {scene.tag}
        </div>
      )}

      <div
        style={{
          position: "absolute",
          bottom: 150,
          left: scene.focus === "right" ? "auto" : 80,
          right: scene.focus === "right" ? 80 : "auto",
          maxWidth: 820,
          color: "white",
          textShadow: "0 8px 28px rgba(0,0,0,0.4)",
          textAlign,
        }}
      >
        <div style={{ display: "inline-flex", gap: 10, alignItems: "center", marginBottom: 10 }}>
          <div
            style={{
              height: 8,
              width: 48,
              background: `linear-gradient(90deg, ${palette.accent}, ${palette.accentAlt})`,
              borderRadius: 999,
              boxShadow: "0 0 18px rgba(122,228,255,0.6)",
            }}
          />
          <span style={{ fontSize: 18, letterSpacing: 0.4, color: "#d7e8ff", textTransform: "uppercase" }}>
            Interactive walkthrough
          </span>
        </div>
        <h1
          style={{
            fontSize: 60,
            fontWeight: 800,
            lineHeight: 1.04,
            margin: 0,
            letterSpacing: -0.5,
            opacity: titleSpring,
            transform: `translateY(${interpolate(titleSpring, [0, 1], [12, 0])}px)`,
          }}
        >
          {scene.title}
        </h1>
        <div style={{ marginTop: 12 }}>
          <KineticLines lines={scene.lines} align={textAlign} localFrame={localFrame} />
        </div>
      </div>

      <div
        style={{
          position: "absolute",
          bottom: 60,
          left: scene.focus === "right" ? "auto" : 80,
          right: scene.focus === "right" ? 80 : "auto",
          display: "flex",
          gap: 10,
          opacity: badgeStagger,
        }}
      >
        {scene.badges.map((label, idx) => (
          <div key={label} style={{ transform: `translateY(${interpolate(badgeStagger, [0, 1], [14, 0])}px)` }}>
            <Chip label={label} tone={idx % 2 === 0 ? "primary" : "accent"} palette={palette} />
          </div>
        ))}
      </div>

      {scene.hud && <GameHUD variant={scene.hud} palette={palette} durationInFrames={sceneDuration} />}

      {scene.sfx?.map((cue, idx) => (
        <Sequence
          key={`${scene.id}-sfx-${idx}`}
          from={cue.atFrame}
          durationInFrames={Math.max(1, sceneDuration - cue.atFrame)}
          layout="none"
          premountFor={Math.min(12, fps)}
        >
          <Audio src={staticFile(cue.file)} volume={cue.volume ?? 0.5} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};

const GridGlitch = ({ start, end, palette }: { start: number; end: number; palette: DemoPalette }) => {
  const frame = useCurrentFrame();
  if (frame < start || frame > end) return null;
  const t = frame - start;
  const opacity = interpolate(t, [0, 10, 25, end - start], [0, 0.8, 0.4, 0], {
    extrapolateRight: "clamp",
  });
  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        background:
          "linear-gradient(90deg, rgba(255,255,255,0.07) 1px, transparent 1px), linear-gradient(0deg, rgba(255,255,255,0.07) 1px, transparent 1px)",
        backgroundSize: "80px 80px",
        mixBlendMode: "screen",
        opacity,
      }}
    />
  );
};

const IntroSting = ({ intro, palette, durationInFrames }: { intro: DemoConfig["intro"]; palette: DemoPalette; durationInFrames: number }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const opacity = spring({ fps, frame, config: { damping: 18, stiffness: 220 } });
  const scale = interpolate(opacity, [0, 1], [1.1, 1]);
  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(circle at 20% 20%, ${palette.glowA}, transparent 45%), radial-gradient(circle at 80% 60%, ${palette.glowB}, transparent 40%), linear-gradient(145deg,${palette.base},#0c1327 40%,${palette.base})`,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <div style={{ textAlign: "center", color: "white", transform: `scale(${scale})`, textShadow: "0 20px 50px rgba(0,0,0,0.45)" }}>
        <div style={{ letterSpacing: 4, textTransform: "uppercase", fontSize: 20, color: "#d7e8ff" }}>{intro.eyebrow}</div>
        <h1 style={{ fontSize: 84, margin: "12px 0 8px", fontWeight: 900, letterSpacing: -1 }}>{intro.title}</h1>
        <div style={{ fontSize: 28, color: "#b8c4ff" }}>{intro.subtitle}</div>
      </div>
      <GridGlitch start={0} end={durationInFrames} palette={palette} />
    </AbsoluteFill>
  );
};

const OutroCta = ({ outro, palette, durationInFrames }: { outro: DemoConfig["outro"]; palette: DemoPalette; durationInFrames: number }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const opacity = spring({ fps, frame, config: { damping: 16, stiffness: 140 } });
  return (
    <AbsoluteFill
      style={{
        background:
          "linear-gradient(135deg, rgba(7,17,43,0.92) 0%, rgba(8,25,60,0.92) 60%, rgba(7,17,43,0.92) 100%), radial-gradient(circle at 30% 30%, rgba(111,124,255,0.14), transparent 38%)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        color: "white",
        textAlign: "center",
        gap: 18,
        opacity,
      }}
    >
      <div style={{ letterSpacing: 3, textTransform: "uppercase", fontSize: 18, color: "#c6d4ff" }}>{outro.eyebrow}</div>
      <h2 style={{ fontSize: 70, margin: 0, fontWeight: 900, letterSpacing: -0.8 }}>{outro.title}</h2>
      <p style={{ fontSize: 24, margin: 0, color: "#d0dcff" }}>{outro.subtitle}</p>
      <div style={{ display: "flex", gap: 16 }}>
        {outro.ctas.map((cta, idx) => (
          <Chip key={cta} label={cta} tone={idx === 0 ? "accent" : "primary"} palette={palette} />
        ))}
      </div>
      <GridGlitch start={0} end={durationInFrames} palette={palette} />
    </AbsoluteFill>
  );
};

const buildBeatFrames = (totalFrames: number, bpm: number, fps: number) => {
  const framesPerBeat = Math.round((fps * 60) / bpm);
  const beats: number[] = [];
  for (let i = 0; i <= totalFrames; i += framesPerBeat) {
    beats.push(i);
  }
  return beats;
};

export const KineticShowcase: React.FC<DemoConfig> = (config) => {
  const { fps, durationInFrames } = useVideoConfig();
  const introFrames = Math.round(config.introSeconds * fps);
  const outroFrames = Math.round(config.outroSeconds * fps);
  const beatFrames = buildBeatFrames(durationInFrames, config.bpm, fps);

  let cursor = introFrames;

  return (
    <AbsoluteFill style={{ backgroundColor: config.palette.base }}>
      <Audio
        src={staticFile(config.audioSrc)}
        volume={(f) => {
          const maxVolume = 0.7;
          const fadeIn = interpolate(f, [0, fps * 0.5], [0, maxVolume], { extrapolateRight: "clamp" });
          const fadeOut = interpolate(f, [durationInFrames - fps * 1.2, durationInFrames], [maxVolume, 0], {
            extrapolateLeft: "clamp",
          });
          return Math.min(fadeIn, fadeOut);
        }}
      />

      <Sequence from={0} durationInFrames={introFrames} premountFor={Math.min(20, fps)}>
        <IntroSting intro={config.intro} palette={config.palette} durationInFrames={introFrames} />
      </Sequence>

      {config.scenes.map((scene) => {
        const duration = Math.round(scene.durationSeconds * fps);
        const start = cursor;
        cursor += duration;
        return (
          <Sequence key={scene.id} from={start} durationInFrames={duration} premountFor={Math.min(18, fps)}>
            <SceneFrame scene={scene} sceneDuration={duration} palette={config.palette} />
          </Sequence>
        );
      })}

      <Sequence from={cursor} durationInFrames={outroFrames} premountFor={Math.min(20, fps)}>
        <OutroCta outro={config.outro} palette={config.palette} durationInFrames={outroFrames} />
      </Sequence>

      {beatFrames.map((f, idx) => (
        <Sequence key={idx} from={f} durationInFrames={6} premountFor={2}>
          <div
            style={{
              position: "absolute",
              inset: 0,
              background: `linear-gradient(90deg, ${
                idx % 4 === 0 ? config.palette.glowB : config.palette.glowA
              }, transparent 45%)`,
              mixBlendMode: "screen",
              opacity: idx % 4 === 0 ? 0.35 : 0.18,
            }}
          />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
