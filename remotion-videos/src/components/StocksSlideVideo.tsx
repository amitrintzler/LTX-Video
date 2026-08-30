/**
 * StocksSlideVideo — 89-second educational Remotion composition for "What Is a Stock?"
 *
 * Uses the lesson poster from /assets/lessons/stocks-101.svg (same pattern as all
 * other Remotion compositions) and builds every subsequent scene from pure Remotion
 * primitives — animated SVGs, spring-driven text, and interpolated shapes.
 * The story-illustration PNGs (page-0 through page-9) belong to the ChildrensBook
 * interactive storybook component and are intentionally NOT used here.
 *
 * Structure  (30 fps)
 *  [0   – 4  s]  Cinematic Intro   — stocks-101.svg poster + animated title
 *  [4   – 12 s]  Scene 1           — Ownership: fractional pie chart
 *  [12  – 20 s]  Scene 2           — Exchanges: buy / sell flow
 *  [20  – 28 s]  Scene 3           — Bull Market: rising candlestick bars
 *  [28  – 36 s]  Scene 4           — Bear Market: falling bars + recovery
 *  [36  – 44 s]  Scene 5           — IPO: private → public flow
 *  [44  – 52 s]  Scene 6           — Stock Quote: live ticker readout
 *  [52  – 60 s]  Scene 7           — Dividends: cash-flow animation
 *  [60  – 68 s]  Scene 8           — Indices: S&P 500 basket visualised
 *  [68  – 76 s]  Scene 9           — Diversification: sector grid
 *  [76  – 84 s]  Scene 10          — Compounding: exponential growth curve
 *  [84  – 89 s]  Outro CTA
 *
 *  Total: 120 + 10 × 240 + 150 = 2670 frames  ≈ 89 seconds
 */

import React from "react";
import {
  AbsoluteFill,
  Img,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  spring,
} from "remotion";
import { CinematicIntro } from "./CinematicIntro";
import { KineticTypography } from "./KineticTypography";

// ── Timing ────────────────────────────────────────────────────────────────────
const INTRO_FRAMES = 180;  // 6 s
const SCENE_FRAMES = 480;  // 16 s per educational scene
const OUTRO_FRAMES = 220;  // ~7 s
const NUM_SCENES   = 10;

export const STOCKS_SLIDE_TOTAL_FRAMES =
  INTRO_FRAMES + NUM_SCENES * SCENE_FRAMES + OUTRO_FRAMES; // 5200 ≈ 173s

// ── Design tokens ─────────────────────────────────────────────────────────────
const BG        = "#050714";
const CARD_BG   = "rgba(15,23,42,0.85)";
const BORDER    = "rgba(99,102,241,0.25)";
const TEXT_MAIN = "#f8fafc";
const TEXT_MUTED = "#94a3b8";

// ── Props ─────────────────────────────────────────────────────────────────────
export type StocksSlideVideoProps = {
  title?:        string;
  subtitle?:     string;
  subjectLabel?: string;
  accent?:       string;
  glow?:         string;
};

// ── Shared: scene wrapper with slide-in headline and subtext ──────────────────
const SceneWrapper: React.FC<{
  headline:   string;
  subtext:    string;
  accent:     string;
  children:   React.ReactNode;
}> = ({ headline, subtext, accent, children }) => {
  const frame       = useCurrentFrame();
  const { fps }     = useVideoConfig();

  const wrapOpacity = interpolate(
    frame,
    [0, 20, SCENE_FRAMES - 20, SCENE_FRAMES],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );
  const headlineAnim = spring({ frame: frame - 15, fps, config: { damping: 14, stiffness: 160 } });
  const subtextAnim  = spring({ frame: frame - 35, fps, config: { damping: 14, stiffness: 140 } });

  return (
    <AbsoluteFill style={{ opacity: wrapOpacity, backgroundColor: BG }}>
      {/* Visual area */}
      <AbsoluteFill style={{ bottom: 280, top: 0 }}>
        {children}
      </AbsoluteFill>

      {/* Bottom text strip */}
      <AbsoluteFill
        style={{
          justifyContent: "flex-end",
          alignItems:     "flex-start",
          padding:        "0 100px 64px",
        }}
      >
        <div
          style={{
            width:           interpolate(headlineAnim, [0, 1], [0, 64]),
            height:          4,
            borderRadius:    2,
            backgroundColor: accent,
            marginBottom:    20,
          }}
        />
        <div
          style={{
            fontSize:      60,
            fontWeight:    900,
            color:         TEXT_MAIN,
            lineHeight:    1.2,
            transform:     `translateY(${(1 - headlineAnim) * 40}px)`,
            opacity:       headlineAnim,
            textShadow:    "0 4px 20px rgba(0,0,0,0.8)",
            fontFamily:    "Inter, sans-serif",
            marginBottom:  14,
          }}
        >
          {headline}
        </div>
        <div
          style={{
            fontSize:   32,
            fontWeight: 500,
            color:      accent,
            transform:  `translateY(${(1 - subtextAnim) * 30}px)`,
            opacity:    subtextAnim,
            fontFamily: "Inter, sans-serif",
            maxWidth:   1400,
            lineHeight: 1.55,
          }}
        >
          {subtext}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ── Scene 1: Ownership — animated fractional pie ──────────────────────────────
const SceneOwnership: React.FC<{ accent: string }> = ({ accent }) => {
  const frame = useCurrentFrame();
  const sliceAngle = interpolate(frame, [30, 150], [0, 360 * 0.08], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const labelOpacity = interpolate(frame, [120, 160], [0, 1], { extrapolateRight: "clamp" });

  const cx = 960; const cy = 330; const r = 220;
  const toRad = (deg: number) => (deg - 90) * (Math.PI / 180);
  const sliceEnd = toRad(sliceAngle);
  const x1 = cx + r * Math.cos(toRad(0));
  const y1 = cy + r * Math.sin(toRad(0));
  const x2 = cx + r * Math.cos(sliceEnd);
  const y2 = cy + r * Math.sin(sliceEnd);
  const largeArc = sliceAngle > 180 ? 1 : 0;

  return (
    <AbsoluteFill>
      <svg width="1920" height="660" viewBox="0 0 1920 660">
        {/* Full circle (other shareholders) */}
        <circle cx={cx} cy={cy} r={r} fill="rgba(30,41,59,0.8)" stroke={accent} strokeWidth={2} />
        {/* Your slice */}
        {sliceAngle > 1 && (
          <path
            d={`M ${cx} ${cy} L ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2} Z`}
            fill={accent}
            opacity={0.9}
          />
        )}
        {/* Center label */}
        <text x={cx} y={cy + 8} textAnchor="middle" fill={TEXT_MAIN} fontSize={36} fontWeight={700} fontFamily="Inter, sans-serif">8%</text>
        <text x={cx} y={cy + 46} textAnchor="middle" fill={TEXT_MUTED} fontSize={22} fontFamily="Inter, sans-serif">Your Stake</text>

        {/* Left: company card */}
        <rect x={200} y={160} width={440} height={300} rx={20} fill={CARD_BG} stroke={BORDER} strokeWidth={1.5} />
        <text x={420} y={270} textAnchor="middle" fill={TEXT_MUTED} fontSize={22} fontFamily="Inter, sans-serif">Company Value</text>
        <text x={420} y={330} textAnchor="middle" fill={TEXT_MAIN} fontSize={52} fontWeight={800} fontFamily="Inter, sans-serif">$50B</text>
        <text x={420} y={380} textAnchor="middle" fill={TEXT_MUTED} fontSize={22} fontFamily="Inter, sans-serif">Total Market Cap</text>

        {/* Right: your value card */}
        <rect x={1280} y={160} width={440} height={300} rx={20} fill={CARD_BG} stroke={`${accent}60`} strokeWidth={1.5}
          opacity={labelOpacity} />
        <text x={1500} y={270} textAnchor="middle" fill={TEXT_MUTED} fontSize={22} fontFamily="Inter, sans-serif" opacity={labelOpacity}>Your Share Value</text>
        <text x={1500} y={330} textAnchor="middle" fill={accent} fontSize={52} fontWeight={800} fontFamily="Inter, sans-serif" opacity={labelOpacity}>$4B</text>
        <text x={1500} y={380} textAnchor="middle" fill={TEXT_MUTED} fontSize={22} fontFamily="Inter, sans-serif" opacity={labelOpacity}>Grows with the business</text>
      </svg>
    </AbsoluteFill>
  );
};

// ── Scene 2: Exchanges — buyer / seller matching ───────────────────────────────
const SceneExchanges: React.FC<{ accent: string }> = ({ accent }) => {
  const frame = useCurrentFrame();
  const arrowProgress = interpolate(frame, [40, 160], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const matchOpacity = interpolate(frame, [160, 200], [0, 1], { extrapolateRight: "clamp" });

  const arrowX = interpolate(arrowProgress, [0, 1], [440, 1100]);

  return (
    <AbsoluteFill>
      <svg width="1920" height="660" viewBox="0 0 1920 660">
        {/* Buyer box */}
        <rect x={80} y={160} width={360} height={300} rx={20} fill={CARD_BG} stroke="rgba(74,222,128,0.4)" strokeWidth={2} />
        <text x={260} y={290} textAnchor="middle" fill="#4ade80" fontSize={28} fontWeight={700} fontFamily="Inter, sans-serif">BUYER</text>
        <text x={260} y={340} textAnchor="middle" fill={TEXT_MAIN} fontSize={44} fontWeight={800} fontFamily="Inter, sans-serif">$152.40</text>
        <text x={260} y={390} textAnchor="middle" fill={TEXT_MUTED} fontSize={20} fontFamily="Inter, sans-serif">Bid Price</text>

        {/* Exchange box */}
        <rect x={760} y={100} width={400} height={420} rx={24} fill="rgba(99,102,241,0.15)" stroke={accent} strokeWidth={2} />
        <text x={960} y={220} textAnchor="middle" fill={accent} fontSize={22} fontWeight={700} fontFamily="Inter, sans-serif" letterSpacing={3}>EXCHANGE</text>
        <text x={960} y={290} textAnchor="middle" fill={TEXT_MAIN} fontSize={32} fontWeight={800} fontFamily="Inter, sans-serif">NYSE</text>
        <text x={960} y={340} textAnchor="middle" fill={TEXT_MUTED} fontSize={20} fontFamily="Inter, sans-serif">Matches Orders</text>
        <text x={960} y={460} textAnchor="middle" fill={TEXT_MUTED} fontSize={18} fontFamily="Inter, sans-serif" opacity={matchOpacity}>✓ Trade Executed</text>

        {/* Seller box */}
        <rect x={1480} y={160} width={360} height={300} rx={20} fill={CARD_BG} stroke="rgba(248,113,113,0.4)" strokeWidth={2} />
        <text x={1660} y={290} textAnchor="middle" fill="#f87171" fontSize={28} fontWeight={700} fontFamily="Inter, sans-serif">SELLER</text>
        <text x={1660} y={340} textAnchor="middle" fill={TEXT_MAIN} fontSize={44} fontWeight={800} fontFamily="Inter, sans-serif">$152.50</text>
        <text x={1660} y={390} textAnchor="middle" fill={TEXT_MUTED} fontSize={20} fontFamily="Inter, sans-serif">Ask Price</text>

        {/* Animated arrow */}
        <circle cx={arrowX} cy={310} r={14} fill={accent} opacity={0.9} />
        <text x={arrowX} y={354} textAnchor="middle" fill={accent} fontSize={16} fontFamily="Inter, sans-serif">order</text>
      </svg>
    </AbsoluteFill>
  );
};

// ── Scene 3: Bull Market — rising candle bars ─────────────────────────────────
const SceneBullMarket: React.FC<{ accent: string }> = ({ accent }) => {
  const frame      = useCurrentFrame();
  const numBars    = 12;
  const heights    = [80, 100, 90, 130, 120, 150, 140, 170, 160, 200, 190, 230];
  const revealed   = Math.floor(interpolate(frame, [20, 180], [0, numBars], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));

  return (
    <AbsoluteFill>
      <svg width="1920" height="660" viewBox="0 0 1920 660">
        <text x={960} y={80} textAnchor="middle" fill={TEXT_MUTED} fontSize={26} fontFamily="Inter, sans-serif">S&P 500 — 12-Month Uptrend</text>
        {heights.map((h, i) => {
          if (i >= revealed) return null;
          const x = 180 + i * 135;
          const barOpacity = interpolate(frame - 20 - i * 13, [0, 20], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          return (
            <g key={i}>
              <rect x={x} y={500 - h} width={80} height={h} rx={6} fill="#4ade80" opacity={barOpacity * 0.85} />
              <rect x={x + 32} y={490 - h - 20} width={16} height={24} rx={3} fill="#4ade80" opacity={barOpacity} />
            </g>
          );
        })}
        {/* +10% label */}
        {revealed >= numBars && (
          <text x={1720} y={260} fill="#4ade80" fontSize={40} fontWeight={800} fontFamily="Inter, sans-serif" opacity={interpolate(frame - 190, [0, 20], [0, 1], { extrapolateRight: "clamp" })}>+10%/yr</text>
        )}
        <line x1={160} y1={510} x2={1760} y2={510} stroke={BORDER} strokeWidth={1} />
      </svg>
    </AbsoluteFill>
  );
};

// ── Scene 4: Bear Market — falling bars with recovery signal ──────────────────
const SceneBearMarket: React.FC<{ accent: string }> = ({ accent }) => {
  const frame   = useCurrentFrame();
  const numBars = 10;
  const heights = [200, 180, 160, 140, 120, 100, 90, 110, 150, 200];
  const colors  = ["#f87171","#f87171","#f87171","#f87171","#f87171","#f87171","#f87171","#4ade80","#4ade80","#4ade80"];
  const revealed = Math.floor(interpolate(frame, [20, 180], [0, numBars], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));

  return (
    <AbsoluteFill>
      <svg width="1920" height="660" viewBox="0 0 1920 660">
        <text x={960} y={80} textAnchor="middle" fill={TEXT_MUTED} fontSize={26} fontFamily="Inter, sans-serif">Every Bear Market Has Recovered</text>
        {heights.map((h, i) => {
          if (i >= revealed) return null;
          const x = 260 + i * 145;
          const barOpacity = interpolate(frame - 20 - i * 16, [0, 20], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          return (
            <rect key={i} x={x} y={500 - h} width={90} height={h} rx={6} fill={colors[i]} opacity={barOpacity * 0.85} />
          );
        })}
        {/* -20% drawdown label */}
        <text x={520} y={170} fill="#f87171" fontSize={32} fontWeight={700} fontFamily="Inter, sans-serif"
          opacity={interpolate(frame - 80, [0, 20], [0, 1], { extrapolateRight: "clamp" })}>-20% drawdown</text>
        {/* Recovery label */}
        {revealed >= 9 && (
          <text x={1580} y={190} fill="#4ade80" fontSize={32} fontWeight={700} fontFamily="Inter, sans-serif"
            opacity={interpolate(frame - 160, [0, 20], [0, 1], { extrapolateRight: "clamp" })}>↗ Recovery</text>
        )}
        <line x1={160} y1={510} x2={1760} y2={510} stroke={BORDER} strokeWidth={1} />
      </svg>
    </AbsoluteFill>
  );
};

// ── Scene 5: IPO — private → public ──────────────────────────────────────────
const SceneIPO: React.FC<{ accent: string }> = ({ accent }) => {
  const frame   = useCurrentFrame();
  const arrowW  = interpolate(frame, [40, 140], [0, 400], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const rightOp = interpolate(frame, [140, 180], [0, 1], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill>
      <svg width="1920" height="660" viewBox="0 0 1920 660">
        {/* Private */}
        <rect x={80} y={140} width={480} height={360} rx={24} fill={CARD_BG} stroke={BORDER} strokeWidth={2} />
        <text x={320} y={260} textAnchor="middle" fill={TEXT_MUTED} fontSize={22} fontFamily="Inter, sans-serif">PRIVATE COMPANY</text>
        <text x={320} y={320} textAnchor="middle" fill={TEXT_MAIN} fontSize={48} fontWeight={800} fontFamily="Inter, sans-serif">🏢</text>
        <text x={320} y={390} textAnchor="middle" fill={TEXT_MUTED} fontSize={20} fontFamily="Inter, sans-serif">Founders &amp; VCs only</text>
        <text x={320} y={430} textAnchor="middle" fill={TEXT_MUTED} fontSize={20} fontFamily="Inter, sans-serif">Shares not tradeable</text>

        {/* Arrow */}
        <rect x={600} y={300} width={arrowW} height={8} rx={4} fill={accent} />
        {arrowW > 360 && (
          <polygon points={`${600 + arrowW},304 ${600 + arrowW - 24},288 ${600 + arrowW - 24},320`} fill={accent} />
        )}
        <text x={800} y={272} textAnchor="middle" fill={accent} fontSize={22} fontWeight={700} fontFamily="Inter, sans-serif"
          opacity={interpolate(frame - 60, [0, 20], [0, 1], { extrapolateRight: "clamp" })}>IPO</text>

        {/* Public */}
        <rect x={1040} y={140} width={800} height={360} rx={24} fill={CARD_BG} stroke={`${accent}60`} strokeWidth={2} opacity={rightOp} />
        <text x={1440} y={240} textAnchor="middle" fill={accent} fontSize={22} fontFamily="Inter, sans-serif" opacity={rightOp}>PUBLIC COMPANY</text>
        <text x={1440} y={300} textAnchor="middle" fill={TEXT_MAIN} fontSize={48} fontWeight={800} fontFamily="Inter, sans-serif" opacity={rightOp}>NYSE: XYZ</text>
        <text x={1440} y={360} textAnchor="middle" fill="#4ade80" fontSize={36} fontWeight={700} fontFamily="Inter, sans-serif" opacity={rightOp}>$18.00 / share</text>
        <text x={1440} y={420} textAnchor="middle" fill={TEXT_MUTED} fontSize={20} fontFamily="Inter, sans-serif" opacity={rightOp}>Anyone can buy a stake</text>
        <text x={1440} y={460} textAnchor="middle" fill={TEXT_MUTED} fontSize={20} fontFamily="Inter, sans-serif" opacity={rightOp}>Raised $500M in capital</text>
      </svg>
    </AbsoluteFill>
  );
};

// ── Scene 6: Stock Quote — animated ticker readout ────────────────────────────
const SceneStockQuote: React.FC<{ accent: string }> = ({ accent }) => {
  const frame      = useCurrentFrame();
  const rows = [
    { label: "Ticker",        value: "AAPL",     color: TEXT_MAIN },
    { label: "Last Price",    value: "$189.30",   color: "#4ade80" },
    { label: "Change",        value: "+$2.14 (+1.14%)", color: "#4ade80" },
    { label: "Volume",        value: "52.4M shares",    color: TEXT_MAIN },
    { label: "52-Week Range", value: "$124 — $199",     color: TEXT_MUTED },
    { label: "P/E Ratio",     value: "30.2×",     color: accent },
    { label: "Market Cap",    value: "$2.94T",    color: TEXT_MAIN },
  ];

  return (
    <AbsoluteFill>
      <svg width="1920" height="660" viewBox="0 0 1920 660">
        <rect x={360} y={60} width={1200} height={560} rx={28} fill={CARD_BG} stroke={BORDER} strokeWidth={2} />
        <text x={960} y={136} textAnchor="middle" fill={TEXT_MUTED} fontSize={24} fontFamily="Inter, sans-serif" letterSpacing={4}>LIVE QUOTE</text>
        {rows.map((row, i) => {
          const rowOpacity = interpolate(frame - 20 - i * 18, [0, 15], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          return (
            <g key={i} opacity={rowOpacity}>
              <text x={440} y={180 + i * 60} fill={TEXT_MUTED} fontSize={22} fontFamily="Inter, sans-serif">{row.label}</text>
              <text x={1480} y={180 + i * 60} textAnchor="end" fill={row.color} fontSize={26} fontWeight={700} fontFamily="Inter, sans-serif">{row.value}</text>
              <line x1={440} y1={190 + i * 60} x2={1480} y2={190 + i * 60} stroke={BORDER} strokeWidth={0.5} />
            </g>
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};

// ── Scene 7: Dividends — cash flow ────────────────────────────────────────────
const SceneDividends: React.FC<{ accent: string }> = ({ accent }) => {
  const frame   = useCurrentFrame();
  const numCoins = 8;

  return (
    <AbsoluteFill>
      <svg width="1920" height="660" viewBox="0 0 1920 660">
        {/* Company box */}
        <rect x={180} y={140} width={400} height={300} rx={24} fill={CARD_BG} stroke={BORDER} strokeWidth={2} />
        <text x={380} y={270} textAnchor="middle" fill={TEXT_MUTED} fontSize={22} fontFamily="Inter, sans-serif">COMPANY</text>
        <text x={380} y={330} textAnchor="middle" fill={TEXT_MAIN} fontSize={40} fontWeight={800} fontFamily="Inter, sans-serif">$8.2B</text>
        <text x={380} y={376} textAnchor="middle" fill={TEXT_MUTED} fontSize={20} fontFamily="Inter, sans-serif">Annual Profit</text>

        {/* Coins flying right */}
        {Array.from({ length: numCoins }).map((_, i) => {
          const delay = 40 + i * 18;
          const coinX = interpolate(frame - delay, [0, 100], [620, 1280], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          const coinY = 300 + Math.sin(i * 0.8) * 100;
          const coinOp = interpolate(frame - delay, [0, 10, 90, 100], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          return (
            <g key={i} opacity={coinOp}>
              <circle cx={coinX} cy={coinY} r={20} fill="#facc15" />
              <text x={coinX} y={coinY + 7} textAnchor="middle" fill="#0f172a" fontSize={16} fontWeight={800} fontFamily="Inter, sans-serif">$</text>
            </g>
          );
        })}

        {/* Investor box */}
        <rect x={1340} y={140} width={400} height={300} rx={24} fill={CARD_BG} stroke="rgba(250,204,21,0.4)" strokeWidth={2} />
        <text x={1540} y={270} textAnchor="middle" fill={TEXT_MUTED} fontSize={22} fontFamily="Inter, sans-serif">SHAREHOLDER</text>
        <text x={1540} y={330} textAnchor="middle" fill="#facc15" fontSize={40} fontWeight={800} fontFamily="Inter, sans-serif">$0.96</text>
        <text x={1540} y={376} textAnchor="middle" fill={TEXT_MUTED} fontSize={20} fontFamily="Inter, sans-serif">Per share / quarter</text>

        {/* Bottom note */}
        <text x={960} y={560} textAnchor="middle" fill={TEXT_MUTED} fontSize={24} fontFamily="Inter, sans-serif"
          opacity={interpolate(frame - 140, [0, 20], [0, 1], { extrapolateRight: "clamp" })}>
          Dividends = passive income on top of price appreciation
        </text>
      </svg>
    </AbsoluteFill>
  );
};

// ── Scene 8: Indices — S&P 500 basket ────────────────────────────────────────
const SceneIndices: React.FC<{ accent: string }> = ({ accent }) => {
  const frame   = useCurrentFrame();
  const tickers = ["AAPL","MSFT","AMZN","NVDA","GOOGL","META","TSLA","BRKA","UNH","XOM"];
  const weights  = [7.2, 6.8, 3.5, 5.9, 4.2, 2.3, 1.8, 1.7, 1.4, 1.2];

  return (
    <AbsoluteFill>
      <svg width="1920" height="660" viewBox="0 0 1920 660">
        {/* Index label */}
        <rect x={760} y={60} width={400} height={80} rx={16} fill={CARD_BG} stroke={accent} strokeWidth={2} />
        <text x={960} y={112} textAnchor="middle" fill={accent} fontSize={28} fontWeight={800} fontFamily="Inter, sans-serif">S&P 500 INDEX</text>

        {/* Stock tiles */}
        {tickers.map((t, i) => {
          const col = i % 5;
          const row = Math.floor(i / 5);
          const x = 160 + col * 330;
          const y = 190 + row * 200;
          const tileOpacity = interpolate(frame - 30 - i * 12, [0, 15], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          const barH = weights[i] * 8;
          return (
            <g key={t} opacity={tileOpacity}>
              <rect x={x} y={y} width={280} height={150} rx={14} fill={CARD_BG} stroke={BORDER} strokeWidth={1.5} />
              <text x={x + 140} y={y + 50} textAnchor="middle" fill={TEXT_MAIN} fontSize={24} fontWeight={700} fontFamily="Inter, sans-serif">{t}</text>
              <rect x={x + 20} y={y + 100} width={barH * 3} height={22} rx={4} fill={accent} opacity={0.8} />
              <text x={x + 20 + barH * 3 + 8} y={y + 116} fill={TEXT_MUTED} fontSize={17} fontFamily="Inter, sans-serif">{weights[i]}%</text>
            </g>
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};

// ── Scene 9: Diversification — sector grid ───────────────────────────────────
const SceneDiversification: React.FC<{ accent: string }> = ({ accent }) => {
  const frame   = useCurrentFrame();
  const sectors = [
    { name: "Technology",   color: "#818cf8", pct: "28%" },
    { name: "Healthcare",   color: "#34d399", pct: "13%" },
    { name: "Financials",   color: "#60a5fa", pct: "13%" },
    { name: "Industrials",  color: "#fb923c", pct: "9%"  },
    { name: "Consumer",     color: "#f472b6", pct: "10%" },
    { name: "Energy",       color: "#facc15", pct: "4%"  },
    { name: "Real Estate",  color: "#a78bfa", pct: "3%"  },
    { name: "Materials",    color: "#22d3ee", pct: "2%"  },
    { name: "Utilities",    color: "#4ade80", pct: "2%"  },
  ];

  return (
    <AbsoluteFill>
      <svg width="1920" height="660" viewBox="0 0 1920 660">
        <text x={960} y={72} textAnchor="middle" fill={TEXT_MUTED} fontSize={26} fontFamily="Inter, sans-serif">Spread risk across all sectors</text>
        {sectors.map((s, i) => {
          const col = i % 3;
          const row = Math.floor(i / 3);
          const x = 160 + col * 540;
          const y = 110 + row * 170;
          const sOp = interpolate(frame - 20 - i * 14, [0, 18], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          return (
            <g key={s.name} opacity={sOp}>
              <rect x={x} y={y} width={480} height={130} rx={16} fill={CARD_BG} stroke={`${s.color}40`} strokeWidth={2} />
              <rect x={x} y={y} width={14} height={130} rx={8} fill={s.color} />
              <text x={x + 40} y={y + 50} fill={s.color} fontSize={22} fontWeight={700} fontFamily="Inter, sans-serif">{s.name}</text>
              <text x={x + 40} y={y + 88} fill={TEXT_MUTED} fontSize={20} fontFamily="Inter, sans-serif">{s.pct} of S&P 500</text>
            </g>
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};

// ── Scene 10: Compounding — exponential growth curve ─────────────────────────
const SceneCompounding: React.FC<{ accent: string }> = ({ accent }) => {
  const frame   = useCurrentFrame();
  const progress = interpolate(frame, [20, 200], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const chartW = 1400; const chartH = 420;
  const chartX = 260; const chartY = 100;
  const years = 35;
  const initial = 10000;
  const rate = 0.10;

  const points = Array.from({ length: years + 1 }, (_, i) => {
    const value = initial * Math.pow(1 + rate, i);
    const maxValue = initial * Math.pow(1 + rate, years); // ~281000
    const x = chartX + (i / years) * chartW;
    const y = chartY + chartH - (value / maxValue) * chartH;
    return { x, y, value, year: 1990 + i };
  });

  const visiblePoints = points.slice(0, Math.floor(progress * years) + 2);
  const pathD = visiblePoints.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ");

  const lastPoint = visiblePoints[visiblePoints.length - 1];
  const labelOp = interpolate(frame - 200, [0, 20], [0, 1], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill>
      <svg width="1920" height="660" viewBox="0 0 1920 660">
        {/* Chart area */}
        <rect x={chartX - 10} y={chartY - 20} width={chartW + 20} height={chartH + 60} rx={16} fill={CARD_BG} stroke={BORDER} strokeWidth={1} />

        {/* Grid lines */}
        {[0, 0.25, 0.5, 0.75, 1].map((t) => (
          <line key={t} x1={chartX} y1={chartY + chartH * (1 - t)} x2={chartX + chartW} y2={chartY + chartH * (1 - t)}
            stroke={BORDER} strokeWidth={0.8} />
        ))}

        {/* Curve */}
        {visiblePoints.length > 1 && (
          <path d={pathD} fill="none" stroke={accent} strokeWidth={4} strokeLinejoin="round" />
        )}

        {/* Gradient fill under curve */}
        {visiblePoints.length > 1 && (
          <path
            d={`${pathD} L ${lastPoint.x} ${chartY + chartH} L ${chartX} ${chartY + chartH} Z`}
            fill={accent} opacity={0.12}
          />
        )}

        {/* Dot at current progress */}
        {lastPoint && (
          <circle cx={lastPoint.x} cy={lastPoint.y} r={10} fill={accent} />
        )}

        {/* Labels */}
        <text x={chartX} y={chartY + chartH + 48} fill={TEXT_MUTED} fontSize={20} fontFamily="Inter, sans-serif">1990</text>
        <text x={chartX + chartW} y={chartY + chartH + 48} textAnchor="end" fill={TEXT_MUTED} fontSize={20} fontFamily="Inter, sans-serif">2025</text>

        {/* Result label */}
        <text x={1750} y={180} textAnchor="end" fill={accent} fontSize={42} fontWeight={800} fontFamily="Inter, sans-serif" opacity={labelOp}>$281,000</text>
        <text x={1750} y={232} textAnchor="end" fill={TEXT_MUTED} fontSize={24} fontFamily="Inter, sans-serif" opacity={labelOp}>from $10,000 in 1990</text>
        <text x={1750} y={280} textAnchor="end" fill={TEXT_MUTED} fontSize={22} fontFamily="Inter, sans-serif" opacity={labelOp}>+10% per year, compounded</text>
      </svg>
    </AbsoluteFill>
  );
};

// ── Outro CTA ─────────────────────────────────────────────────────────────────
const OutroScene: React.FC<{ accent: string }> = ({ accent }) => {
  const frame   = useCurrentFrame();
  const { fps } = useVideoConfig();

  const bgOp    = interpolate(frame, [0, 30], [0, 1], { extrapolateRight: "clamp" });
  const glowSc  = interpolate(frame, [0, OUTRO_FRAMES], [0.7, 1.3], { extrapolateRight: "clamp" });
  const glowOp  = interpolate(frame, [0, 60, OUTRO_FRAMES], [0, 0.55, 0.35], { extrapolateRight: "clamp" });
  const barW    = interpolate(frame, [70, OUTRO_FRAMES - 10], [0, 400], { extrapolateRight: "clamp" });
  const barOp   = interpolate(frame, [60, 90], [0, 1], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill
      style={{
        background:     "linear-gradient(135deg, #050714 0%, #0f1225 50%, #050714 100%)",
        opacity:        bgOp,
        justifyContent: "center",
        alignItems:     "center",
        flexDirection:  "column",
      }}
    >
      <div
        style={{
          position:     "absolute",
          width:        700,
          height:       700,
          borderRadius: "50%",
          background:   `radial-gradient(circle, ${accent}28 0%, transparent 70%)`,
          transform:    `scale(${glowSc})`,
          opacity:      glowOp,
        }}
      />
      <KineticTypography
        text="Now you know what stocks are."
        delay={10}
        fontSize={72}
        color={TEXT_MAIN}
        style={{ position: "relative" }}
      />
      <KineticTypography
        text="Ready to practise?"
        delay={36}
        fontSize={60}
        color={accent}
        style={{ position: "relative", marginTop: 60 }}
      />
      <div
        style={{
          position:        "absolute",
          bottom:          80,
          left:            "50%",
          transform:       "translateX(-50%)",
          display:         "flex",
          alignItems:      "center",
          gap:             16,
          opacity:         barOp,
          fontFamily:      "Inter, sans-serif",
        }}
      >
        <div
          style={{
            height:          4,
            width:           barW,
            backgroundColor: accent,
            borderRadius:    2,
          }}
        />
        <span style={{ fontSize: 26, fontWeight: 600, color: "rgba(255,255,255,0.45)" }}>
          Lesson complete
        </span>
      </div>
    </AbsoluteFill>
  );
};

// ── Scene manifest ────────────────────────────────────────────────────────────
const SCENES: Array<{
  headline: string;
  subtext:  string;
  Component: React.FC<{ accent: string }>;
}> = [
  {
    headline:  "Owning a Stock = Owning Part of a Business",
    subtext:   "Every share is a fractional ownership stake — you benefit when the company grows and earns profit.",
    Component: SceneOwnership,
  },
  {
    headline:  "Stocks Trade on Exchanges",
    subtext:   "NYSE and NASDAQ match millions of buyers and sellers every second at the fairest available price.",
    Component: SceneExchanges,
  },
  {
    headline:  "Bull Markets: Prices Rise Over Time",
    subtext:   "When investor confidence grows, prices trend upward for months or years — S&P 500 averages ~10%/yr.",
    Component: SceneBullMarket,
  },
  {
    headline:  "Bear Markets: Prices Fall 20%+",
    subtext:   "Every bear market in history has recovered. Fear creates buying opportunities for patient investors.",
    Component: SceneBearMarket,
  },
  {
    headline:  "IPOs: When Companies Go Public",
    subtext:   "An Initial Public Offering lets a company raise capital by selling shares to outside investors for the first time.",
    Component: SceneIPO,
  },
  {
    headline:  "Reading a Stock Quote",
    subtext:   "Ticker, price, volume, 52-week range, P/E ratio — your real-time dashboard for any publicly traded company.",
    Component: SceneStockQuote,
  },
  {
    headline:  "Dividends: Getting Paid to Own",
    subtext:   "Profitable companies share earnings quarterly — passive income stacked on top of price appreciation.",
    Component: SceneDividends,
  },
  {
    headline:  "Indices Track the Whole Market",
    subtext:   "S&P 500, Dow Jones, NASDAQ Composite — each measures a basket of hundreds of stocks at once.",
    Component: SceneIndices,
  },
  {
    headline:  "Diversification Reduces Risk",
    subtext:   "Spreading across sectors and geographies lowers volatility without sacrificing long-run returns.",
    Component: SceneDiversification,
  },
  {
    headline:  "Long-Term Compounding Wins",
    subtext:   "$10,000 in the S&P 500 in 1990 is worth $281,000 today. Time in the market beats timing the market.",
    Component: SceneCompounding,
  },
];

// ── Main composition ──────────────────────────────────────────────────────────
export const StocksSlideVideo: React.FC<StocksSlideVideoProps> = ({
  title        = "What Is a Stock?",
  subtitle     = "Equity ownership, exchanges, bull/bear cycles",
  subjectLabel = "Stock Basics",
  accent       = "#6366f1",
  glow         = "rgba(99,102,241,0.65)",
}) => {
  return (
    <AbsoluteFill style={{ backgroundColor: BG, fontFamily: "Inter, sans-serif" }}>
      {/* ── Cinematic intro — uses the dedicated lesson poster ── */}
      <Sequence from={0} durationInFrames={INTRO_FRAMES}>
        <CinematicIntro
          title={title}
          subtitle={subtitle}
          subjectLabel={subjectLabel}
          posterUrl="assets/lessons/stocks-101.svg"
          accent={accent}
          glow={glow}
        />
      </Sequence>

      {/* ── 10 programmatic educational scenes ── */}
      {SCENES.map(({ headline, subtext, Component }, i) => (
        <Sequence
          key={i}
          from={INTRO_FRAMES + i * SCENE_FRAMES}
          durationInFrames={SCENE_FRAMES}
        >
          <SceneWrapper headline={headline} subtext={subtext} accent={accent}>
            <Component accent={accent} />
          </SceneWrapper>
        </Sequence>
      ))}

      {/* ── Outro CTA ── */}
      <Sequence
        from={INTRO_FRAMES + NUM_SCENES * SCENE_FRAMES}
        durationInFrames={OUTRO_FRAMES}
      >
        <OutroScene accent={accent} />
      </Sequence>
    </AbsoluteFill>
  );
};
