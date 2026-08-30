import React from "react";
import {
  AbsoluteFill,
  interpolate,
  Sequence,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

declare global {
  interface Window {
    __sceneDurations?: number[];
  }
}


// ── Theme engine ──────────────────────────────────────────────────────────────

export type VideoTheme = {
  bg: string;
  accent: string;
  textPrimary: string;
  textSecondary: string;
};

const DEFAULT_THEME: VideoTheme = {
  bg: "#080c12",
  accent: "#6366f1",
  textPrimary: "#f8fafc",
  textSecondary: "#94a3b8",
};

const VideoThemeContext = React.createContext<VideoTheme>(DEFAULT_THEME);
export const useVideoTheme = () => React.useContext(VideoThemeContext);

// ── Scene Info Context ────────────────────────────────────────────────────────

type SceneInfo = { sceneFrame: number; sceneDuration: number };
const SceneInfoContext = React.createContext<SceneInfo>({ sceneFrame: 0, sceneDuration: 450 });
export const useSceneInfo = () => React.useContext(SceneInfoContext);

// ── Scene Manager ─────────────────────────────────────────────────────────────

export type SceneDef = {
  /** Duration in frames for this scene. If omitted, duration is split equally. */
  durationInFrames?: number;
  render: (sceneFrame: number, sceneDuration: number) => React.ReactNode;
};

/**
 * Renders scenes sequentially with cross-fade transitions.
 * Pass `theme` to propagate colors to all child scenes via React Context.
 * The legacy `background` prop is kept for backward compatibility.
 */
export const SceneManager: React.FC<{
  scenes: SceneDef[];
  background?: string;
  theme?: VideoTheme;
}> = ({ scenes, background, theme }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const resolved: VideoTheme = theme ?? {
    ...DEFAULT_THEME,
    bg: background ?? DEFAULT_THEME.bg,
  };

  const withoutExplicit = scenes.filter((s) => !s.durationInFrames).length;
  const explicitTotal = scenes.reduce(
    (sum, s) => sum + (s.durationInFrames || 0),
    0
  );
  const autoLen = withoutExplicit > 0
    ? Math.floor((durationInFrames - explicitTotal) / withoutExplicit)
    : 0;

  let offset = 0;
  const sceneRanges = scenes.map((s, i) => {
    const measured = typeof window !== "undefined" ? window.__sceneDurations?.[i] : undefined;
    const dur = measured ?? s.durationInFrames ?? autoLen;
    const start = offset;
    offset += dur;
    return { start, dur, scene: s };
  });

  const idx = sceneRanges.findIndex(
    (r, i) =>
      frame >= r.start &&
      (i === sceneRanges.length - 1 || frame < sceneRanges[i + 1].start)
  );
  if (idx < 0) return null;

  const { start, dur, scene } = sceneRanges[idx];
  const sceneFrame = frame - start;

  const FADE = 20;
  const isLastScene = idx === sceneRanges.length - 1;
  const fadeIn = interpolate(sceneFrame, [0, FADE], [0, 1], {
    extrapolateRight: "clamp",
  });
  const fadeOut = isLastScene
    ? 1
    : interpolate(sceneFrame, [dur - FADE, dur], [1, 0], { extrapolateRight: "clamp" });
  const opacity = Math.min(fadeIn, fadeOut);

  return (
    <VideoThemeContext.Provider value={resolved}>
      <AbsoluteFill
        style={{ backgroundColor: resolved.bg, fontFamily: "'Inter', sans-serif" }}
      >
        <SceneInfoContext.Provider value={{ sceneFrame, sceneDuration: dur }}>
          <Sequence from={start} durationInFrames={dur} layout="none">
            <AbsoluteFill style={{ opacity }}>
              {scene.render(sceneFrame, dur)}
            </AbsoluteFill>
          </Sequence>
        </SceneInfoContext.Provider>
      </AbsoluteFill>
    </VideoThemeContext.Provider>
  );
};

// ── Reusable Scene Templates ──────────────────────────────────────────────────

export const TitleScene: React.FC<{
  label: string;
  title: string;
  subtitle: string;
  accent: string;
}> = ({ label, title, subtitle, accent }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const theme = useVideoTheme();
  const { sceneDuration } = useSceneInfo();

  const labelAnim = spring({ frame: frame - Math.floor(sceneDuration * 0.04), fps, config: { damping: 14, stiffness: 160 } });
  const titleAnim = spring({ frame: frame - Math.floor(sceneDuration * 0.08), fps, config: { damping: 14, stiffness: 140 } });
  const subAnim   = spring({ frame: frame - Math.floor(sceneDuration * 0.12), fps, config: { damping: 14, stiffness: 120 } });

  const barWidth = titleAnim < 0.98
    ? interpolate(titleAnim, [0, 1], [0, 120])
    : 120 + 15 * Math.sin((Math.max(0, frame - Math.floor(sceneDuration * 0.20)) / fps) * Math.PI * 0.7);

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <div style={{ textAlign: "center", maxWidth: 1400 }}>
        <div
          style={{
            fontSize: 18,
            fontWeight: 700,
            letterSpacing: "0.25em",
            color: accent,
            textTransform: "uppercase",
            marginBottom: 24,
            opacity: labelAnim,
            transform: `translateY(${(1 - labelAnim) * 30}px)`,
          }}
        >
          {label}
        </div>
        <h1
          style={{
            fontSize: 80,
            fontWeight: 900,
            color: theme.textPrimary,
            margin: 0,
            lineHeight: 1.1,
            opacity: titleAnim,
            transform: `translateY(${(1 - titleAnim) * 40}px)`,
          }}
        >
          {title}
        </h1>
        <p
          style={{
            fontSize: 36,
            color: theme.textSecondary,
            marginTop: 20,
            fontWeight: 400,
            opacity: subAnim,
            transform: `translateY(${(1 - subAnim) * 30}px)`,
          }}
        >
          {subtitle}
        </p>

        <div
          style={{
            width: barWidth,
            height: 4,
            borderRadius: 2,
            backgroundColor: accent,
            margin: "32px auto 0",
          }}
        />
      </div>
    </AbsoluteFill>
  );
};

export const BulletScene: React.FC<{
  heading: string;
  bullets: string[];
  accent: string;
  icon?: string;
}> = ({ heading, bullets, accent, icon }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const theme = useVideoTheme();
  const { sceneDuration } = useSceneInfo();

  const headAnim = spring({ frame: frame - Math.floor(sceneDuration * 0.06), fps, config: { damping: 14, stiffness: 160 } });

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <div style={{ maxWidth: 1200, padding: "0 80px" }}>
        {icon && (
          <div style={{ fontSize: 64, marginBottom: 20, opacity: headAnim }}>
            {icon}
          </div>
        )}
        <h2
          style={{
            fontSize: 56,
            fontWeight: 800,
            color: theme.textPrimary,
            marginBottom: 40,
            opacity: headAnim,
            transform: `translateY(${(1 - headAnim) * 30}px)`,
          }}
        >
          {heading}
        </h2>
        {bullets.map((bullet, i) => {
          const bulletDelay = Math.min(
            Math.floor(sceneDuration * 0.14 + i * (sceneDuration * 0.14)),
            Math.floor(sceneDuration * 0.70)
          );
          const bulletAnim = spring({
            frame: frame - bulletDelay,
            fps,
            config: { damping: 14, stiffness: 140 },
          });
          const shimmer = 0.75 + 0.25 * Math.sin(((Math.max(0, frame - bulletDelay)) / fps) * Math.PI * 0.8 + i);
          return (
            <div
              key={i}
              style={{
                display: "flex",
                alignItems: "flex-start",
                gap: 20,
                marginBottom: 28,
                opacity: bulletAnim,
                transform: `translateX(${(1 - bulletAnim) * 40}px)`,
              }}
            >
              <div
                style={{
                  width: 12,
                  height: 12,
                  borderRadius: 6,
                  backgroundColor: accent,
                  marginTop: 14,
                  flexShrink: 0,
                  opacity: shimmer,
                }}
              />
              <span
                style={{
                  fontSize: 32,
                  color: theme.textSecondary,
                  lineHeight: 1.5,
                }}
              >
                {bullet}
              </span>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

export const StatsScene: React.FC<{
  heading: string;
  stats: Array<{ label: string; value: string; color?: string }>;
  accent: string;
  footnote?: string;
}> = ({ heading, stats, accent, footnote }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const theme = useVideoTheme();
  const { sceneDuration } = useSceneInfo();

  const headAnim = spring({ frame: frame - Math.floor(sceneDuration * 0.06), fps, config: { damping: 14, stiffness: 160 } });

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <div style={{ textAlign: "center", maxWidth: 1600 }}>
        <h2
          style={{
            fontSize: 52,
            fontWeight: 800,
            color: theme.textPrimary,
            marginBottom: 60,
            opacity: headAnim,
            transform: `translateY(${(1 - headAnim) * 30}px)`,
          }}
        >
          {heading}
        </h2>
        <div style={{ display: "flex", justifyContent: "center", gap: 40 }}>
          {stats.map((stat, i) => {
            const cardDelay = Math.min(
              Math.floor(sceneDuration * 0.14 + i * (sceneDuration * 0.14)),
              Math.floor(sceneDuration * 0.70)
            );
            const cardAnim = spring({
              frame: frame - cardDelay,
              fps,
              config: { damping: 14, stiffness: 140 },
            });
            return (
              <div
                key={i}
                style={{
                  background: "rgba(255,255,255,0.04)",
                  border: `2px solid ${stat.color || accent}40`,
                  borderRadius: 24,
                  padding: "40px 48px",
                  minWidth: 260,
                  opacity: cardAnim,
                  transform: `translateY(${(1 - cardAnim) * 40}px) scale(${0.9 + cardAnim * 0.1})`,
                }}
              >
                <div
                  style={{
                    fontSize: 22,
                    color: theme.textSecondary,
                    marginBottom: 12,
                    fontWeight: 500,
                  }}
                >
                  {stat.label}
                </div>
                <div
                  style={{
                    fontSize: 52,
                    fontWeight: 900,
                    color: stat.color || accent,
                  }}
                >
                  {stat.value}
                </div>
              </div>
            );
          })}
        </div>
        {footnote && (
          <p
            style={{
              fontSize: 24,
              color: theme.textSecondary,
              marginTop: 48,
              opacity: spring({
                frame: frame - Math.floor(sceneDuration * 0.60),
                fps,
                config: { damping: 14, stiffness: 120 },
              }),
            }}
          >
            {footnote}
          </p>
        )}
      </div>
    </AbsoluteFill>
  );
};

export const SetupScene: React.FC<{
  heading: string;
  items: Array<{ label: string; value: string; color?: string }>;
  accent: string;
  description?: string;
}> = ({ heading, items, accent, description }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const theme = useVideoTheme();
  const { sceneDuration } = useSceneInfo();

  const headAnim = spring({ frame: frame - Math.floor(sceneDuration * 0.06), fps, config: { damping: 14, stiffness: 160 } });

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <div style={{ textAlign: "center", maxWidth: 1400 }}>
        <h2
          style={{
            fontSize: 52,
            fontWeight: 800,
            color: theme.textPrimary,
            marginBottom: 20,
            opacity: headAnim,
          }}
        >
          {heading}
        </h2>
        {description && (
          <p
            style={{
              fontSize: 28,
              color: theme.textSecondary,
              marginBottom: 48,
              opacity: spring({ frame: frame - Math.floor(sceneDuration * 0.12), fps, config: { damping: 14, stiffness: 140 } }),
            }}
          >
            {description}
          </p>
        )}
        <div
          style={{
            display: "flex",
            justifyContent: "center",
            gap: 32,
            flexWrap: "wrap",
          }}
        >
          {items.map((item, i) => {
            const itemDelay = Math.min(
              Math.floor(sceneDuration * 0.14 + i * (sceneDuration * 0.12)),
              Math.floor(sceneDuration * 0.70)
            );
            const anim = spring({
              frame: frame - itemDelay,
              fps,
              config: { damping: 14, stiffness: 140 },
            });
            return (
              <div
                key={i}
                style={{
                  background: "rgba(255,255,255,0.04)",
                  border: `1.5px solid ${item.color || accent}40`,
                  borderRadius: 20,
                  padding: "32px 40px",
                  minWidth: 200,
                  opacity: anim,
                  transform: `translateY(${(1 - anim) * 30}px)`,
                }}
              >
                <div style={{ fontSize: 18, color: theme.textSecondary, marginBottom: 8, fontWeight: 500 }}>
                  {item.label}
                </div>
                <div style={{ fontSize: 40, fontWeight: 800, color: item.color || theme.textPrimary }}>
                  {item.value}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const RealWorldExampleScene: React.FC<{
  heading: string;
  company: string;
  scenario: string;
  setupItems: Array<{ label: string; value: string; color?: string }>;
  outcome: string;
  outcomeDetail: string;
  outcomeColor: string;
  accent: string;
}> = ({ heading, company, scenario, setupItems, outcome, outcomeDetail, outcomeColor, accent }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const theme = useVideoTheme();
  const { sceneDuration } = useSceneInfo();

  const headAnim = spring({ frame: frame - Math.floor(sceneDuration * 0.04), fps, config: { damping: 14, stiffness: 160 } });
  const companyAnim = spring({ frame: frame - Math.floor(sceneDuration * 0.08), fps, config: { damping: 14, stiffness: 140 } });
  const outcomeAnim = spring({ frame: frame - Math.floor(sceneDuration * 0.60), fps, config: { damping: 12, stiffness: 100 } });

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: "0 80px" }}>
      <div style={{ width: "100%", maxWidth: 1600 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 20, marginBottom: 32, opacity: headAnim, transform: `translateY(${(1 - headAnim) * 20}px)` }}>
          <div style={{ width: 8, height: 52, backgroundColor: accent, borderRadius: 4 }} />
          <h2 style={{ fontSize: 48, fontWeight: 800, color: theme.textPrimary, margin: 0 }}>{heading}</h2>
        </div>

        <div style={{
          background: `${accent}12`, border: `1.5px solid ${accent}35`, borderRadius: 16,
          padding: "28px 36px", marginBottom: 36,
          opacity: companyAnim, transform: `translateY(${(1 - companyAnim) * 20}px)`
        }}>
          <div style={{ fontSize: 20, fontWeight: 700, color: accent, marginBottom: 10, letterSpacing: "0.08em", textTransform: "uppercase" }}>{company}</div>
          <div style={{ fontSize: 30, color: theme.textSecondary, lineHeight: 1.6 }}>{scenario}</div>
        </div>

        <div style={{ display: "flex", gap: 20, marginBottom: 36, flexWrap: "wrap" }}>
          {setupItems.map((item, i) => {
            const itemDelay = Math.min(
              Math.floor(sceneDuration * 0.20 + i * (sceneDuration * 0.08)),
              Math.floor(sceneDuration * 0.65)
            );
            const anim = spring({ frame: frame - itemDelay, fps, config: { damping: 14, stiffness: 140 } });
            return (
              <div key={i} style={{
                background: "rgba(255,255,255,0.04)", border: `1.5px solid ${item.color || accent}30`,
                borderRadius: 14, padding: "20px 28px", minWidth: 160,
                opacity: anim, transform: `translateY(${(1 - anim) * 24}px)`
              }}>
                <div style={{ fontSize: 16, color: theme.textSecondary, marginBottom: 8, fontWeight: 500 }}>{item.label}</div>
                <div style={{ fontSize: 38, fontWeight: 800, color: item.color || theme.textPrimary }}>{item.value}</div>
              </div>
            );
          })}
        </div>

        <div style={{
          background: `${outcomeColor}15`, border: `2px solid ${outcomeColor}50`, borderRadius: 16, padding: "28px 40px",
          opacity: outcomeAnim, transform: `translateY(${(1 - outcomeAnim) * 24}px)`
        }}>
          <div style={{ fontSize: 18, fontWeight: 700, color: outcomeColor, marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.1em" }}>Outcome</div>
          <div style={{ fontSize: 44, fontWeight: 900, color: outcomeColor, marginBottom: 10 }}>{outcome}</div>
          <div style={{ fontSize: 28, color: theme.textSecondary, lineHeight: 1.5 }}>{outcomeDetail}</div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const SvgLineChartScene: React.FC<{
  heading: string;
  subheading?: string;
  data: Array<{ label: string; value: number }>;
  accent: string;
  yLabel?: string;
  xLabel?: string;
  highlightIdx?: number;
  footnote?: string;
}> = ({ heading, subheading, data, accent, yLabel, xLabel, highlightIdx, footnote }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const theme = useVideoTheme();
  const { sceneDuration } = useSceneInfo();

  const W = 1200, H = 440;
  const padL = 90, padR = 50, padT = 30, padB = 70;
  const chartW = W - padL - padR;
  const chartH = H - padT - padB;

  const maxVal = Math.max(...data.map(d => d.value));
  const minVal = Math.min(...data.map(d => d.value));
  const range = (maxVal - minVal) || 1;

  const pts = data.map((d, i) => ({
    x: padL + (i / Math.max(data.length - 1, 1)) * chartW,
    y: padT + (1 - (d.value - minVal) / range) * chartH,
    v: d.value,
    label: d.label,
  }));

  const drawEndFrame = Math.floor(sceneDuration * 0.72);
  // Interpolate across segments continuously so the line draws smoothly regardless of data point count
  const rawProgress = interpolate(frame, [15, drawEndFrame], [0, pts.length - 1], { extrapolateRight: "clamp", extrapolateLeft: "clamp" });
  const fullIdx = Math.min(Math.floor(rawProgress), pts.length - 2);
  const frac = rawProgress - fullIdx;
  const drawPts = [
    ...pts.slice(0, fullIdx + 1),
    ...(fullIdx < pts.length - 1 ? [{
      x: pts[fullIdx].x + frac * (pts[fullIdx + 1].x - pts[fullIdx].x),
      y: pts[fullIdx].y + frac * (pts[fullIdx + 1].y - pts[fullIdx].y),
      v: 0, label: "",
    }] : []),
  ];
  const pathD = drawPts.map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ");
  const visiblePts = drawPts.length;

  const pulsePhase = Math.max(0, frame - drawEndFrame);
  const endPulse = 1 + 0.4 * Math.sin((pulsePhase / fps) * Math.PI * 1.8);

  const headAnim = spring({ frame: frame - Math.floor(sceneDuration * 0.01), fps, config: { damping: 14, stiffness: 160 } });
  const subAnim  = spring({ frame: frame - Math.floor(sceneDuration * 0.04), fps, config: { damping: 14, stiffness: 140 } });

  const gridLines = [0, 0.25, 0.5, 0.75, 1];

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <div style={{ maxWidth: 1400, width: "100%", padding: "0 80px" }}>
        <h2 style={{ fontSize: 52, fontWeight: 800, color: theme.textPrimary, margin: "0 0 8px", opacity: headAnim, transform: `translateY(${(1 - headAnim) * 20}px)` }}>{heading}</h2>
        {subheading && (
          <p style={{ fontSize: 26, color: theme.textSecondary, margin: "0 0 32px", opacity: subAnim }}>{subheading}</p>
        )}
        <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ overflow: "visible", display: "block" }}>
          {gridLines.map((t, gi) => {
            const y = padT + t * chartH;
            const val = maxVal - t * range;
            return (
              <g key={gi}>
                <line x1={padL} y1={y} x2={padL + chartW} y2={y} stroke="rgba(255,255,255,0.07)" strokeWidth={1} strokeDasharray={gi === 0 ? "none" : "4,4"} />
                <text x={padL - 12} y={y + 6} textAnchor="end" fill={theme.textSecondary} fontSize={17} fontFamily="Inter, sans-serif">{val % 1 === 0 ? val.toFixed(0) : val.toFixed(2)}</text>
              </g>
            );
          })}
          {pts.map((p, i) => (
            <text key={i} x={p.x} y={padT + chartH + 28} textAnchor="middle" fill={theme.textSecondary} fontSize={16} fontFamily="Inter, sans-serif">{p.label}</text>
          ))}
          <line x1={padL} y1={padT + chartH} x2={padL + chartW} y2={padT + chartH} stroke="rgba(255,255,255,0.18)" strokeWidth={1.5} />
          <line x1={padL} y1={padT} x2={padL} y2={padT + chartH} stroke="rgba(255,255,255,0.18)" strokeWidth={1.5} />
          {visiblePts > 1 && (
            <path d={`${pathD} L${pts[visiblePts-1].x},${padT+chartH} L${pts[0].x},${padT+chartH} Z`} fill={`${accent}12`} />
          )}
          {visiblePts > 1 && (
            <path d={pathD} stroke={accent} strokeWidth={3.5} fill="none" strokeLinecap="round" strokeLinejoin="round" />
          )}
          {pts.slice(0, visiblePts).map((p, i) => {
            const isHL = i === highlightIdx;
            return (
              <g key={i}>
                <circle cx={p.x} cy={p.y} r={isHL ? 10 * endPulse : 5} fill={isHL ? accent : `${accent}70`} />
                {isHL && (
                  <text x={p.x} y={p.y - 18} textAnchor="middle" fill={accent} fontSize={18} fontWeight={700} fontFamily="Inter, sans-serif">{p.v % 1 === 0 ? p.v : p.v.toFixed(2)}</text>
                )}
              </g>
            );
          })}
          {yLabel && <text x={22} y={padT + chartH / 2} transform={`rotate(-90 22 ${padT + chartH / 2})`} textAnchor="middle" fill={theme.textSecondary} fontSize={17} fontFamily="Inter, sans-serif">{yLabel}</text>}
          {xLabel && <text x={padL + chartW / 2} y={H - 4} textAnchor="middle" fill={theme.textSecondary} fontSize={17} fontFamily="Inter, sans-serif">{xLabel}</text>}
        </svg>
        {footnote && (
          <p style={{ fontSize: 22, color: theme.textSecondary, marginTop: 16, opacity: interpolate(frame, [drawEndFrame * 0.85, drawEndFrame], [0, 1], { extrapolateRight: "clamp" }) }}>{footnote}</p>
        )}
      </div>
    </AbsoluteFill>
  );
};

export const SummaryScene: React.FC<{
  heading: string;
  takeaways: string[];
  accent: string;
  closingLine?: string;
}> = ({ heading, takeaways, accent, closingLine }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const theme = useVideoTheme();
  const { sceneDuration } = useSceneInfo();

  const headAnim = spring({ frame: frame - Math.floor(sceneDuration * 0.05), fps, config: { damping: 14, stiffness: 160 } });

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <div style={{ maxWidth: 1200, textAlign: "left", padding: "0 100px" }}>
        <div
          style={{
            width: interpolate(headAnim, [0, 1], [0, 80]),
            height: 4,
            borderRadius: 2,
            backgroundColor: accent,
            marginBottom: 24,
          }}
        />
        <h2
          style={{
            fontSize: 56,
            fontWeight: 800,
            color: theme.textPrimary,
            marginBottom: 48,
            opacity: headAnim,
          }}
        >
          {heading}
        </h2>
        {takeaways.map((t, i) => {
          const itemDelay = Math.min(
            Math.floor(sceneDuration * 0.12 + i * (sceneDuration * 0.12)),
            Math.floor(sceneDuration * 0.68)
          );
          const anim = spring({
            frame: frame - itemDelay,
            fps,
            config: { damping: 14, stiffness: 140 },
          });
          return (
            <div
              key={i}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 20,
                marginBottom: 24,
                opacity: anim,
                transform: `translateX(${(1 - anim) * 30}px)`,
              }}
            >
              <div
                style={{
                  fontSize: 28,
                  color: accent,
                  fontWeight: 800,
                  width: 36,
                  flexShrink: 0,
                }}
              >
                {i + 1}.
              </div>
              <span style={{ fontSize: 30, color: theme.textSecondary, lineHeight: 1.5 }}>
                {t}
              </span>
            </div>
          );
        })}
        {closingLine && (
          <p
            style={{
              fontSize: 32,
              color: accent,
              fontWeight: 700,
              marginTop: 48,
              opacity: spring({
                frame: frame - Math.min(
                  Math.floor(sceneDuration * 0.12 + takeaways.length * (sceneDuration * 0.12)),
                  Math.floor(sceneDuration * 0.78)
                ),
                fps,
                config: { damping: 14, stiffness: 120 },
              }),
            }}
          >
            {closingLine}
          </p>
        )}
      </div>
    </AbsoluteFill>
  );
};

// ── PayoffDiagramScene ────────────────────────────────────────────────────────
// Animated options payoff curve. Computes P&L points from trade parameters.

export type PayoffLeg = {
  type: "long-call" | "short-call" | "long-put" | "short-put";
  strike: number;
  premium: number;
  quantity?: number; // default 1 contract (100 shares)
};

function computePayoff(legs: PayoffLeg[], price: number): number {
  return legs.reduce((total, leg) => {
    const qty = (leg.quantity ?? 1) * 100;
    let perShare = 0;
    if (leg.type === "long-call") {
      perShare = Math.max(0, price - leg.strike) - leg.premium;
    } else if (leg.type === "short-call") {
      perShare = leg.premium - Math.max(0, price - leg.strike);
    } else if (leg.type === "long-put") {
      perShare = Math.max(0, leg.strike - price) - leg.premium;
    } else {
      perShare = leg.premium - Math.max(0, leg.strike - price);
    }
    return total + perShare * qty;
  }, 0);
}

export const PayoffDiagramScene: React.FC<{
  heading: string;
  subheading?: string;
  legs: PayoffLeg[];
  priceMin: number;
  priceMax: number;
  currentPrice?: number;
  accent: string;
  footnote?: string;
}> = ({ heading, subheading, legs, priceMin, priceMax, currentPrice, accent, footnote }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const theme = useVideoTheme();
  const { sceneDuration } = useSceneInfo();

  const NUM_PTS = 80;
  const prices = Array.from({ length: NUM_PTS + 1 }, (_, i) => priceMin + (i / NUM_PTS) * (priceMax - priceMin));
  const payoffs = prices.map(p => computePayoff(legs, p));
  const maxPL = Math.max(...payoffs);
  const minPL = Math.min(...payoffs);
  const plRange = (maxPL - minPL) || 1;

  const W = 1280, H = 480;
  const padL = 100, padR = 60, padT = 40, padB = 80;
  const chartW = W - padL - padR;
  const chartH = H - padT - padB;

  const toX = (price: number) => padL + ((price - priceMin) / (priceMax - priceMin)) * chartW;
  const toY = (pl: number) => padT + (1 - (pl - minPL) / plRange) * chartH;

  const zeroY = toY(0);

  const drawEndFrame = Math.floor(sceneDuration * 0.65);
  const progress = interpolate(frame, [20, drawEndFrame], [0, 1], { extrapolateRight: "clamp", extrapolateLeft: "clamp" });
  const visibleCount = Math.max(2, Math.floor(progress * (NUM_PTS + 1)));

  const visiblePrices = prices.slice(0, visibleCount);
  const visiblePayoffs = payoffs.slice(0, visibleCount);

  const pathD = visiblePrices.map((p, i) => `${i === 0 ? "M" : "L"}${toX(p).toFixed(1)},${toY(visiblePayoffs[i]).toFixed(1)}`).join(" ");
  const profitPath = visiblePrices.map((p, i) => {
    const pl = visiblePayoffs[i];
    const y = pl >= 0 ? toY(pl) : zeroY;
    return `${i === 0 ? "M" : "L"}${toX(p).toFixed(1)},${y.toFixed(1)}`;
  }).join(" ") + ` L${toX(visiblePrices[visiblePrices.length - 1]).toFixed(1)},${zeroY.toFixed(1)} L${toX(visiblePrices[0]).toFixed(1)},${zeroY.toFixed(1)} Z`;

  const lossPath = visiblePrices.map((p, i) => {
    const pl = visiblePayoffs[i];
    const y = pl < 0 ? toY(pl) : zeroY;
    return `${i === 0 ? "M" : "L"}${toX(p).toFixed(1)},${y.toFixed(1)}`;
  }).join(" ") + ` L${toX(visiblePrices[visiblePrices.length - 1]).toFixed(1)},${zeroY.toFixed(1)} L${toX(visiblePrices[0]).toFixed(1)},${zeroY.toFixed(1)} Z`;

  const breakevenPrices = prices.filter((p, i) => i > 0 && Math.sign(payoffs[i]) !== Math.sign(payoffs[i - 1]));
  const labelOpacity = interpolate(frame, [drawEndFrame, drawEndFrame + 20], [0, 1], { extrapolateRight: "clamp" });

  const headAnim = spring({ frame: frame - Math.floor(sceneDuration * 0.02), fps, config: { damping: 14, stiffness: 160 } });

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <div style={{ maxWidth: 1440, width: "100%", padding: "0 80px" }}>
        <h2 style={{ fontSize: 48, fontWeight: 800, color: theme.textPrimary, margin: "0 0 6px", opacity: headAnim }}>{heading}</h2>
        {subheading && <p style={{ fontSize: 24, color: theme.textSecondary, margin: "0 0 20px", opacity: headAnim }}>{subheading}</p>}
        <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ overflow: "visible", display: "block" }}>
          {/* Grid */}
          {[-1, -0.5, 0, 0.5, 1].map((t, gi) => {
            const pl = minPL + (t + 1) / 2 * plRange;
            const y = toY(pl);
            return (
              <g key={gi}>
                <line x1={padL} y1={y} x2={padL + chartW} y2={y} stroke={t === 0 ? "rgba(255,255,255,0.25)" : "rgba(255,255,255,0.06)"} strokeWidth={t === 0 ? 1.5 : 1} />
                <text x={padL - 10} y={y + 5} textAnchor="end" fill={theme.textSecondary} fontSize={14} fontFamily="Inter, sans-serif">
                  {pl >= 0 ? "+" : ""}{(pl / 100).toFixed(0) === "0" ? "0" : (pl / 100).toFixed(0)}
                </text>
              </g>
            );
          })}
          {/* X axis labels */}
          {prices.filter((_, i) => i % Math.floor(NUM_PTS / 6) === 0).map((p, i) => (
            <text key={i} x={toX(p)} y={padT + chartH + 28} textAnchor="middle" fill={theme.textSecondary} fontSize={14} fontFamily="Inter, sans-serif">${p.toFixed(0)}</text>
          ))}
          {/* Current price marker */}
          {currentPrice && (
            <line x1={toX(currentPrice)} y1={padT} x2={toX(currentPrice)} y2={padT + chartH} stroke={accent} strokeWidth={1} strokeDasharray="6,4" />
          )}
          {/* Profit fill */}
          <path d={profitPath} fill="#22c55e18" />
          {/* Loss fill */}
          <path d={lossPath} fill="#ef444418" />
          {/* Main payoff curve */}
          <path d={pathD} stroke={accent} strokeWidth={3.5} fill="none" strokeLinecap="round" strokeLinejoin="round" />
          {/* Breakeven markers */}
          {breakevenPrices.map((bp, i) => (
            <g key={i} style={{ opacity: labelOpacity }}>
              <circle cx={toX(bp)} cy={zeroY} r={7} fill={accent} />
              <text x={toX(bp)} y={zeroY - 16} textAnchor="middle" fill={accent} fontSize={14} fontWeight={700} fontFamily="Inter, sans-serif">BE ${bp.toFixed(0)}</text>
            </g>
          ))}
          {/* Max profit/loss labels */}
          <text x={padL + chartW + 8} y={toY(maxPL) + 5} fill="#22c55e" fontSize={13} fontWeight={700} fontFamily="Inter, sans-serif" style={{ opacity: labelOpacity }}>Max +${(maxPL / 100).toFixed(0)}</text>
          {minPL < 0 && <text x={padL + chartW + 8} y={toY(minPL) + 5} fill="#ef4444" fontSize={13} fontWeight={700} fontFamily="Inter, sans-serif" style={{ opacity: labelOpacity }}>Max -${(Math.abs(minPL) / 100).toFixed(0)}</text>}
          {/* Axes */}
          <line x1={padL} y1={padT + chartH} x2={padL + chartW} y2={padT + chartH} stroke="rgba(255,255,255,0.18)" strokeWidth={1.5} />
          <line x1={padL} y1={padT} x2={padL} y2={padT + chartH} stroke="rgba(255,255,255,0.18)" strokeWidth={1.5} />
          {/* Y label */}
          <text x={18} y={padT + chartH / 2} transform={`rotate(-90 18 ${padT + chartH / 2})`} textAnchor="middle" fill={theme.textSecondary} fontSize={14} fontFamily="Inter, sans-serif">P&L ($)</text>
          <text x={padL + chartW / 2} y={H - 4} textAnchor="middle" fill={theme.textSecondary} fontSize={14} fontFamily="Inter, sans-serif">Stock Price at Expiry</text>
        </svg>
        {footnote && (
          <p style={{ fontSize: 20, color: theme.textSecondary, marginTop: 12, opacity: labelOpacity }}>{footnote}</p>
        )}
      </div>
    </AbsoluteFill>
  );
};

// ── CalculationScene ──────────────────────────────────────────────────────────
// Step-by-step math: formula → values → result. Each step fades in timed to narration.

export const CalculationScene: React.FC<{
  heading: string;
  steps: Array<{
    label: string;
    formula: string;
    result: string;
    highlight?: boolean;
    color?: string;
  }>;
  conclusion?: string;
  accent: string;
}> = ({ heading, steps, conclusion, accent }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const theme = useVideoTheme();
  const { sceneDuration } = useSceneInfo();

  const headAnim = spring({ frame: frame - Math.floor(sceneDuration * 0.04), fps, config: { damping: 14, stiffness: 160 } });
  const stepSlice = Math.floor(sceneDuration * 0.75) / steps.length;
  const conclusionDelay = Math.floor(sceneDuration * 0.80);

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <div style={{ maxWidth: 1300, width: "100%", padding: "0 80px" }}>
        <h2 style={{ fontSize: 52, fontWeight: 800, color: theme.textPrimary, marginBottom: 48, opacity: headAnim, transform: `translateY(${(1 - headAnim) * 24}px)` }}>{heading}</h2>
        {steps.map((step, i) => {
          const delay = Math.floor(sceneDuration * 0.12 + i * stepSlice);
          const anim = spring({ frame: frame - delay, fps, config: { damping: 14, stiffness: 130 } });
          const color = step.color ?? (step.highlight ? accent : theme.textPrimary);
          return (
            <div
              key={i}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 0,
                marginBottom: 20,
                opacity: anim,
                transform: `translateX(${(1 - anim) * 32}px)`,
                background: step.highlight ? `${accent}12` : "rgba(255,255,255,0.03)",
                border: `1.5px solid ${step.highlight ? accent + "40" : "rgba(255,255,255,0.07)"}`,
                borderRadius: 14,
                padding: "20px 28px",
              }}
            >
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 14, fontWeight: 600, color: theme.textSecondary, letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 6 }}>{step.label}</div>
                <div style={{ fontSize: 28, color: theme.textSecondary, fontFamily: "monospace" }}>{step.formula}</div>
              </div>
              <div style={{ fontSize: 44, fontWeight: 900, color, minWidth: 180, textAlign: "right", fontFamily: "monospace" }}>{step.result}</div>
            </div>
          );
        })}
        {conclusion && (
          <div style={{
            marginTop: 24,
            padding: "24px 32px",
            background: `${accent}18`,
            border: `2px solid ${accent}50`,
            borderRadius: 16,
            opacity: spring({ frame: frame - conclusionDelay, fps, config: { damping: 14, stiffness: 120 } }),
          }}>
            <div style={{ fontSize: 30, fontWeight: 700, color: accent, lineHeight: 1.5 }}>{conclusion}</div>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};

// ── ComparisonTableScene ──────────────────────────────────────────────────────
// Side-by-side table with animated row reveals.

export const ComparisonTableScene: React.FC<{
  heading: string;
  columns: string[];
  rows: Array<{ cells: string[]; winner?: number; highlight?: boolean }>;
  accent: string;
  subheading?: string;
}> = ({ heading, columns, rows, accent, subheading }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const theme = useVideoTheme();
  const { sceneDuration } = useSceneInfo();

  const headAnim = spring({ frame: frame - Math.floor(sceneDuration * 0.04), fps, config: { damping: 14, stiffness: 160 } });
  const headerDelay = Math.floor(sceneDuration * 0.10);
  const rowSlice = Math.floor(sceneDuration * 0.60) / Math.max(rows.length, 1);

  const COLORS = [accent, "#22c55e", "#f59e0b", "#ef4444", "#a855f7"];

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <div style={{ maxWidth: 1400, width: "100%", padding: "0 80px" }}>
        <h2 style={{ fontSize: 52, fontWeight: 800, color: theme.textPrimary, marginBottom: subheading ? 8 : 36, opacity: headAnim }}>{heading}</h2>
        {subheading && <p style={{ fontSize: 26, color: theme.textSecondary, marginBottom: 28, opacity: headAnim }}>{subheading}</p>}
        <div style={{ width: "100%", borderRadius: 16, overflow: "hidden", border: "1.5px solid rgba(255,255,255,0.10)" }}>
          {/* Header row */}
          <div style={{
            display: "grid",
            gridTemplateColumns: `repeat(${columns.length}, 1fr)`,
            background: "rgba(255,255,255,0.06)",
            opacity: spring({ frame: frame - headerDelay, fps, config: { damping: 14, stiffness: 140 } }),
          }}>
            {columns.map((col, ci) => (
              <div key={ci} style={{
                padding: "18px 24px",
                fontSize: 18,
                fontWeight: 700,
                color: COLORS[ci % COLORS.length],
                textTransform: "uppercase",
                letterSpacing: "0.08em",
                borderRight: ci < columns.length - 1 ? "1px solid rgba(255,255,255,0.08)" : "none",
              }}>{col}</div>
            ))}
          </div>
          {/* Data rows */}
          {rows.map((row, ri) => {
            const delay = Math.floor(sceneDuration * 0.18 + ri * rowSlice);
            const anim = spring({ frame: frame - delay, fps, config: { damping: 14, stiffness: 130 } });
            return (
              <div
                key={ri}
                style={{
                  display: "grid",
                  gridTemplateColumns: `repeat(${columns.length}, 1fr)`,
                  borderTop: "1px solid rgba(255,255,255,0.06)",
                  background: row.highlight ? `${accent}10` : (ri % 2 === 0 ? "transparent" : "rgba(255,255,255,0.02)"),
                  opacity: anim,
                  transform: `translateX(${(1 - anim) * 20}px)`,
                }}
              >
                {row.cells.map((cell, ci) => {
                  const isWinner = row.winner === ci;
                  return (
                    <div key={ci} style={{
                      padding: "16px 24px",
                      fontSize: 24,
                      color: isWinner ? COLORS[ci % COLORS.length] : theme.textSecondary,
                      fontWeight: isWinner ? 700 : 400,
                      borderRight: ci < columns.length - 1 ? "1px solid rgba(255,255,255,0.06)" : "none",
                    }}>{cell}{isWinner && " ✓"}</div>
                  );
                })}
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ── MistakeHighlightScene ─────────────────────────────────────────────────────
// Wrong vs right split, then insight text.

export const MistakeHighlightScene: React.FC<{
  heading: string;
  mistake: { label: string; detail: string };
  correction: { label: string; detail: string };
  insight: string;
  accent: string;
}> = ({ heading, mistake, correction, insight, accent }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const theme = useVideoTheme();
  const { sceneDuration } = useSceneInfo();

  const headAnim = spring({ frame: frame - Math.floor(sceneDuration * 0.04), fps, config: { damping: 14, stiffness: 160 } });
  const mistakeAnim = spring({ frame: frame - Math.floor(sceneDuration * 0.12), fps, config: { damping: 14, stiffness: 140 } });
  const correctionAnim = spring({ frame: frame - Math.floor(sceneDuration * 0.30), fps, config: { damping: 14, stiffness: 140 } });
  const insightAnim = spring({ frame: frame - Math.floor(sceneDuration * 0.60), fps, config: { damping: 12, stiffness: 110 } });

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: "0 80px" }}>
      <div style={{ maxWidth: 1440, width: "100%" }}>
        <h2 style={{ fontSize: 52, fontWeight: 800, color: theme.textPrimary, marginBottom: 40, opacity: headAnim }}>{heading}</h2>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 32, marginBottom: 32 }}>
          {/* Mistake */}
          <div style={{
            background: "#ef444412",
            border: "2px solid #ef444450",
            borderRadius: 20,
            padding: "32px 36px",
            opacity: mistakeAnim,
            transform: `translateY(${(1 - mistakeAnim) * 30}px)`,
          }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: "#ef4444", letterSpacing: "0.15em", textTransform: "uppercase", marginBottom: 12 }}>Common Mistake</div>
            <div style={{ fontSize: 26, fontWeight: 700, color: "#ef4444", marginBottom: 16 }}>{mistake.label}</div>
            <div style={{ fontSize: 22, color: theme.textSecondary, lineHeight: 1.6 }}>{mistake.detail}</div>
          </div>
          {/* Correction */}
          <div style={{
            background: "#22c55e12",
            border: "2px solid #22c55e50",
            borderRadius: 20,
            padding: "32px 36px",
            opacity: correctionAnim,
            transform: `translateY(${(1 - correctionAnim) * 30}px)`,
          }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: "#22c55e", letterSpacing: "0.15em", textTransform: "uppercase", marginBottom: 12 }}>Better Approach</div>
            <div style={{ fontSize: 26, fontWeight: 700, color: "#22c55e", marginBottom: 16 }}>{correction.label}</div>
            <div style={{ fontSize: 22, color: theme.textSecondary, lineHeight: 1.6 }}>{correction.detail}</div>
          </div>
        </div>
        {/* Insight */}
        <div style={{
          background: `${accent}14`,
          border: `2px solid ${accent}50`,
          borderRadius: 16,
          padding: "28px 36px",
          opacity: insightAnim,
          transform: `translateY(${(1 - insightAnim) * 20}px)`,
        }}>
          <div style={{ fontSize: 28, fontWeight: 600, color: accent, lineHeight: 1.6 }}>{insight}</div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ── WorkedExampleScene ────────────────────────────────────────────────────────
// Step-by-step trade simulation with running P&L counter.

export const WorkedExampleScene: React.FC<{
  heading: string;
  company: string;
  ticker: string;
  trades: Array<{
    day: string;
    event: string;
    action: string;
    pl: number;
    cumPl: number;
  }>;
  accent: string;
  subheading?: string;
}> = ({ heading, company, ticker, trades, accent, subheading }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const theme = useVideoTheme();
  const { sceneDuration } = useSceneInfo();

  const headAnim = spring({ frame: frame - Math.floor(sceneDuration * 0.04), fps, config: { damping: 14, stiffness: 160 } });
  const tradeSlice = Math.floor(sceneDuration * 0.70) / Math.max(trades.length, 1);

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: "0 80px" }}>
      <div style={{ maxWidth: 1440, width: "100%" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 32, opacity: headAnim }}>
          <div>
            <h2 style={{ fontSize: 48, fontWeight: 800, color: theme.textPrimary, margin: 0 }}>{heading}</h2>
            {subheading && <p style={{ fontSize: 22, color: theme.textSecondary, margin: "6px 0 0" }}>{subheading}</p>}
          </div>
          <div style={{ background: `${accent}18`, border: `1.5px solid ${accent}40`, borderRadius: 12, padding: "12px 24px", textAlign: "right" }}>
            <div style={{ fontSize: 14, color: theme.textSecondary, fontWeight: 600, letterSpacing: "0.1em" }}>{ticker}</div>
            <div style={{ fontSize: 22, fontWeight: 800, color: accent }}>{company}</div>
          </div>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {trades.map((trade, i) => {
            const delay = Math.floor(sceneDuration * 0.14 + i * tradeSlice);
            const anim = spring({ frame: frame - delay, fps, config: { damping: 14, stiffness: 130 } });
            const plColor = trade.cumPl >= 0 ? "#22c55e" : "#ef4444";
            return (
              <div
                key={i}
                style={{
                  display: "grid",
                  gridTemplateColumns: "100px 1fr 1fr 140px",
                  alignItems: "center",
                  gap: 0,
                  background: "rgba(255,255,255,0.03)",
                  border: "1px solid rgba(255,255,255,0.07)",
                  borderRadius: 12,
                  padding: "18px 24px",
                  opacity: anim,
                  transform: `translateX(${(1 - anim) * 28}px)`,
                }}
              >
                <div style={{ fontSize: 13, fontWeight: 700, color: accent, letterSpacing: "0.06em", textTransform: "uppercase" }}>{trade.day}</div>
                <div>
                  <div style={{ fontSize: 15, color: theme.textSecondary, marginBottom: 4 }}>{trade.event}</div>
                  <div style={{ fontSize: 20, fontWeight: 600, color: theme.textPrimary }}>{trade.action}</div>
                </div>
                <div style={{ fontSize: 18, color: trade.pl >= 0 ? "#22c55e" : "#ef4444", fontWeight: 600, fontFamily: "monospace" }}>
                  {trade.pl >= 0 ? "+" : ""}{trade.pl >= 0 ? "$" + trade.pl.toLocaleString() : "-$" + Math.abs(trade.pl).toLocaleString()}
                </div>
                <div style={{ textAlign: "right" }}>
                  <div style={{ fontSize: 13, color: theme.textSecondary, marginBottom: 2 }}>Cumulative</div>
                  <div style={{ fontSize: 26, fontWeight: 900, color: plColor, fontFamily: "monospace" }}>
                    {trade.cumPl >= 0 ? "+" : ""}{trade.cumPl >= 0 ? "$" + trade.cumPl.toLocaleString() : "-$" + Math.abs(trade.cumPl).toLocaleString()}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};
