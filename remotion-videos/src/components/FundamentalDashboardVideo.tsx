import { AbsoluteFill, Sequence, useVideoConfig, useCurrentFrame, interpolate, spring } from "remotion";
import { CinematicIntro } from "./CinematicIntro";
import { SceneManager, TitleScene, BulletScene, SummaryScene, RealWorldExampleScene, SvgLineChartScene, type SceneDef } from "./SceneSystem";
import React from "react";
import { TEMPLATE_STYLES } from "../lib/templateStyles";

const S = TEMPLATE_STYLES["fundamentals"];

export type FundamentalDashboardProps = {
  title: string;
  subtitle: string;
  subjectLabel: string;
  posterUrl: string;
  accent: string;
  glow: string;
  metric: string;
  value: string;
};

// ── Multi-metric dashboard panel ──────────────────────────────────────────────
const MultiMetricScene: React.FC<{
  heading: string;
  description: string;
  metrics: Array<{ label: string; value: string; change?: string; changeUp?: boolean; color: string }>;
  accent: string;
}> = ({ heading, description, metrics, accent }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const headAnim = spring({ frame: frame - 10, fps, config: { damping: 14, stiffness: 160 } });
  const descAnim = spring({ frame: frame - 25, fps, config: { damping: 14, stiffness: 140 } });

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: "0 80px" }}>
      <div style={{ width: "100%", maxWidth: 1600 }}>
        <h2 style={{ fontSize: 52, fontWeight: 800, color: S.textPrimary, margin: "0 0 16px", opacity: headAnim, transform: `translateY(${(1 - headAnim) * 20}px)` }}>{heading}</h2>
        <p style={{ fontSize: 28, color: S.textSecondary, margin: "0 0 48px", lineHeight: 1.5, opacity: descAnim }}>{description}</p>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 28 }}>
          {metrics.map((m, i) => {
            const anim = spring({ frame: frame - 50 - i * 18, fps, config: { damping: 14, stiffness: 130 } });
            return (
              <div key={i} style={{
                background: "rgba(255,255,255,0.04)", border: `1.5px solid ${m.color}35`,
                borderRadius: 20, padding: "32px 36px",
                opacity: anim, transform: `translateY(${(1 - anim) * 32}px) scale(${0.92 + anim * 0.08})`
              }}>
                <div style={{ fontSize: 17, color: S.textSecondary, marginBottom: 12, fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.08em" }}>{m.label}</div>
                <div style={{ fontSize: 52, fontWeight: 900, color: m.color, marginBottom: 8 }}>{m.value}</div>
                {m.change && (
                  <div style={{ fontSize: 22, fontWeight: 600, color: m.changeUp ? "#10b981" : "#ef4444" }}>
                    {m.changeUp ? "▲" : "▼"} {m.change}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ── Topic data ────────────────────────────────────────────────────────────────
const TOPIC_DATA: Record<string, {
  description: string;
  bullets: string[];
  multiMetrics: { heading: string; description: string; metrics: Array<{ label: string; value: string; change?: string; changeUp?: boolean; color: string }> };
  chart: { heading: string; subheading: string; data: Array<{ label: string; value: number }>; xLabel: string; yLabel: string; highlightIdx: number; footnote: string };
  example: { heading: string; company: string; scenario: string; setupItems: Array<{ label: string; value: string; color?: string }>; outcome: string; outcomeDetail: string; outcomeColor: string };
  takeaways: string[];
}> = {
  "Expected Move": {
    description: "Earnings gaps can make or break a position overnight. Understanding expected move and IV crush lets you defend or profit regardless of direction.",
    bullets: [
      "Expected move = what options market prices as the likely post earnings range",
      "IV inflates before earnings, then collapses (IV crush) after the print",
      "A stock can beat earnings and still drop if IV crush > directional move",
      "Selling premium into earnings captures inflated IV if you manage the risk",
    ],
    multiMetrics: {
      heading: "NVDA Q3 FY2024 Earnings Event Anatomy",
      description: "How the options market priced the move and what actually happened",
      metrics: [
        { label: "Expected Move (±)", value: "±$28", change: "6.1% of stock price", changeUp: true, color: "#ef4444" },
        { label: "IV Pre Earnings", value: "82%", change: "vs 44% post", changeUp: false, color: "#f59e0b" },
        { label: "Actual Move", value: "+$42", change: "+9.3% gap up", changeUp: true, color: "#10b981" },
        { label: "IV Crush", value: "-38pp", change: "82% → 44%", changeUp: false, color: "#ef4444" },
        { label: "Straddle P&L", value: "+$14", change: "if held through", changeUp: true, color: "#6366f1" },
        { label: "ATM Call P&L", value: "-$5.60", change: "despite correct dir", changeUp: false, color: "#ef4444" },
      ],
    },
    chart: {
      heading: "NVDA IV, 30 Days Around Earnings",
      subheading: "Implied volatility collapses immediately after the print, the IV crush effect",
      data: [
        { label: "T-30", value: 45 }, { label: "T-21", value: 52 }, { label: "T-14", value: 61 },
        { label: "T-7", value: 72 }, { label: "T-2", value: 82 }, { label: "T+1", value: 44 },
        { label: "T+7", value: 38 }, { label: "T+14", value: 35 },
      ],
      xLabel: "Days to/from Earnings",
      yLabel: "Implied Volatility (%)",
      highlightIdx: 4,
      footnote: "T-2 (★) = peak IV at 82%, the optimal sell point. Post-earnings IV crushed to 44% in a single session",
    },
    example: {
      heading: "Earnings Defense: Strangle Sell",
      company: "NVDA Pre-Earnings IV Harvest",
      scenario: "Sold a NVDA 1 week $440/$510 strangle for $22 total credit with IV at 80%. Expected move priced at ±$28. You collected premium on both sides, betting the move stays inside the range.",
      setupItems: [
        { label: "Call Strike", value: "$510", color: "#10b981" },
        { label: "Put Strike", value: "$440", color: "#ef4444" },
        { label: "Credit", value: "$22.00", color: "#10b981" },
        { label: "Expected Move", value: "±$28", color: "#f59e0b" },
        { label: "Actual Move", value: "+$42", color: "#ef4444" },
      ],
      outcome: "-$20 loss",
      outcomeDetail: "NVDA gapped +$42, outside the expected move. The $510 call was breached, loss on that side offset partially by the put premium kept. Lesson: selling premium around earnings works most of the time, but tail risk is real. Size small.",
      outcomeColor: "#ef4444",
    },
    takeaways: [
      "Sell expected move to collect IV crush, works about 70% of the time",
      "Size positions smaller for earnings, undefined risk can blow up",
      "IV crush destroys long premium even when direction is correct",
      "Know the expected move before entering any earnings trade",
    ],
  },

  "VIX Level": {
    description: "Macro events (CPI, FOMC, NFP) cause volatility spikes that ripple through the entire options market. Learning to trade around macro prints separates pros from amateurs.",
    bullets: [
      "VIX spikes before macro events and crushes after, just like individual earnings",
      "CPI and FOMC are the two biggest recurring volatility catalysts",
      "Term structure inverts when short term fear exceeds long term uncertainty",
      "Trading index options (SPX/SPY) around macro events = pure vol play",
    ],
    multiMetrics: {
      heading: "FOMC March 2023 Volatility Event Map",
      description: "Fed hiked 25bps, market expected it, but Powell's hawkish tone sent VIX spiking",
      metrics: [
        { label: "VIX (Pre-FOMC)", value: "21.4", change: "vs 18 week avg", changeUp: false, color: "#f59e0b" },
        { label: "VIX (Post-spike)", value: "26.8", change: "+25% intraday", changeUp: false, color: "#ef4444" },
        { label: "SPY Move", value: "-1.8%", change: "hawkish surprise", changeUp: false, color: "#ef4444" },
        { label: "SPY 0DTE Put", value: "+340%", change: "$0.30 → $1.32", changeUp: true, color: "#10b981" },
        { label: "30d IV (pre)", value: "18.2%", change: "SPY options", changeUp: true, color: "#6366f1" },
        { label: "30d IV (post)", value: "22.6%", change: "+4.4pp jump", changeUp: false, color: "#3b82f6" },
      ],
    },
    chart: {
      heading: "VIX, 8 Major Macro Events (2023)",
      subheading: "VIX level around key Fed/CPI dates, spikes are predictable and timing is the edge",
      data: [
        { label: "Jan CPI", value: 19.4 }, { label: "Feb FOMC", value: 21.2 }, { label: "Mar FOMC", value: 26.8 },
        { label: "Apr CPI", value: 17.1 }, { label: "May FOMC", value: 17.9 }, { label: "Jul FOMC", value: 13.9 },
        { label: "Sep CPI", value: 17.5 }, { label: "Nov FOMC", value: 14.9 },
      ],
      xLabel: "Event Date",
      yLabel: "VIX Level",
      highlightIdx: 2,
      footnote: "Mar FOMC (★) peak VIX 26.8, Powell flagged higher for longer. Best vol sell opportunity of 2023 in hindsight",
    },
    example: {
      heading: "Macro Trade: FOMC Vol Sell",
      company: "SPY FOMC Day Iron Condor",
      scenario: "Sold a SPY 1-week $408/$405 put spread + $420/$423 call spread for $1.85 credit. VIX at 21.4, implied 1-day move ±$3.20. SPY was at $413.",
      setupItems: [
        { label: "SPY Price", value: "$413", color: "#94a3b8" },
        { label: "Credit", value: "$1.85", color: "#10b981" },
        { label: "Put Wing", value: "$408/$405", color: "#ef4444" },
        { label: "Call Wing", value: "$420/$423", color: "#10b981" },
        { label: "Implied Move", value: "±$3.20", color: "#f59e0b" },
      ],
      outcome: "+$1.85 full credit",
      outcomeDetail: "SPY fell to $411 after FOMC, within the condor range. Both spreads expired worthless. Collected full $1.85 credit. Vol crush post-announcement worked perfectly. Iron condors on FOMC day: high win rate, small credit each time.",
      outcomeColor: "#10b981",
    },
    takeaways: [
      "Sell premium before macro events, VIX inflates predictably",
      "Use defined risk structures (condors, spreads) to cap tail risk",
      "Post-event vol crush is your profit engine, close early if possible",
      "Track the macro calendar like an earnings calendar",
    ],
  },

  "EPS Beat": {
    description: "Earnings quality goes beyond the headline beat. Revenue growth, margin trends, and guidance revisions are the real signals professional traders track.",
    bullets: [
      "EPS beats can be manufactured through buybacks, revenue beats cannot",
      "Margin expansion shows pricing power; margin compression signals trouble",
      "Guidance raise after a beat is the strongest bullish signal possible",
      "Miss on revenue but beat on EPS = red flag (cost cutting, not growth)",
    ],
    multiMetrics: {
      heading: "META Q4 FY2023 Earnings Quality Deep Dive",
      description: "Meta's Year of Efficiency delivered one of the highest quality beats of 2023",
      metrics: [
        { label: "Revenue", value: "$40.1B", change: "+25% YoY", changeUp: true, color: "#10b981" },
        { label: "EPS", value: "$5.33", change: "+203% YoY", changeUp: true, color: "#6366f1" },
        { label: "Op. Margin", value: "41%", change: "+22pp YoY", changeUp: true, color: "#f59e0b" },
        { label: "MAU Growth", value: "+6%", change: "3.19B users", changeUp: true, color: "#10b981" },
        { label: "Guidance", value: "+17%", change: "Q1 rev raise", changeUp: true, color: "#3b82f6" },
        { label: "Stock Reaction", value: "+20%", change: "next-day gap", changeUp: true, color: "#10b981" },
      ],
    },
    chart: {
      heading: "META Operating Margin, 8 Quarters",
      subheading: "Margin expansion through the Year of Efficiency, quality earnings in action",
      data: [
        { label: "Q1'22", value: 31 }, { label: "Q2'22", value: 29 }, { label: "Q3'22", value: 20 },
        { label: "Q4'22", value: 20 }, { label: "Q1'23", value: 25 }, { label: "Q2'23", value: 29 },
        { label: "Q3'23", value: 40 }, { label: "Q4'23", value: 41 },
      ],
      xLabel: "Quarter",
      yLabel: "Operating Margin (%)",
      highlightIdx: 7,
      footnote: "Q4'23 (★): 41% operating margin, up from 20% just 5 quarters earlier. Cost discipline drove EPS +203% YoY",
    },
    example: {
      heading: "Earnings Play: Quality Beat Setup",
      company: "META Q4 FY2023 Earnings Trade",
      scenario: "META trading at $374 pre earnings. Bought a $380/$410 call spread for $8.20 debit. Thesis: margin recovery story intact, guidance likely to raise.",
      setupItems: [
        { label: "META Price", value: "$374", color: "#94a3b8" },
        { label: "Spread Paid", value: "$8.20", color: "#f59e0b" },
        { label: "Strategy", value: "$380/$410 CS", color: "#6366f1" },
        { label: "Max Risk", value: "$8.20", color: "#ef4444" },
        { label: "Post-Earn Move", value: "+20%", color: "#10b981" },
      ],
      outcome: "+$21.80 profit",
      outcomeDetail: "META gapped to $450. Spread maxed: $30 - $8.20 = +$21.80. +266% return on defined risk. The quality earnings signal (margin + guidance) was the real edge, not just guessing direction.",
      outcomeColor: "#10b981",
    },
    takeaways: [
      "Revenue quality > EPS quality, focus on top-line beats",
      "Margin trends reveal operational health over multiple quarters",
      "Guidance raise post-beat is the strongest catalyst signal",
      "Read the earnings call transcript, management tone matters",
    ],
  },

  "Implied Vol": {
    description: "Valuation multiples and implied volatility are linked. When P/E expands, IV often compresses, and vice versa. Trading this relationship is a professional level edge.",
    bullets: [
      "High P/E stocks carry higher IV, more expectations means more risk premium",
      "P/E compression (multiple contraction) often comes with IV expansion",
      "In rising rate environments, multiples contract and options get expensive",
      "Use IV rank to see if options are cheap or expensive relative to history",
    ],
    multiMetrics: {
      heading: "TSLA Valuation vs. IV, 2023 Snapshot",
      description: "Tesla: a masterclass in how valuation and volatility move together",
      metrics: [
        { label: "P/E (peak 2021)", value: "1,100×", change: "bubble valuation", changeUp: false, color: "#ef4444" },
        { label: "P/E (2023)", value: "72×", change: "-93% compression", changeUp: false, color: "#f59e0b" },
        { label: "IV Rank", value: "68th %ile", change: "historically high", changeUp: false, color: "#ef4444" },
        { label: "30d IV", value: "58%", change: "vs 35% SPY", changeUp: false, color: "#a855f7" },
        { label: "Stock vs SPY", value: "-65%", change: "from 2021 peak", changeUp: false, color: "#ef4444" },
        { label: "Options Cost", value: "2.1×", change: "SPY equivalent", changeUp: false, color: "#f59e0b" },
      ],
    },
    chart: {
      heading: "TSLA P/E Ratio vs. IV, 2021 to 2023",
      subheading: "As valuation compressed from bubble levels, IV stayed elevated, creating a persistent premium sell opportunity",
      data: [
        { label: "Q1'21", value: 85 }, { label: "Q3'21", value: 78 }, { label: "Q1'22", value: 72 },
        { label: "Q3'22", value: 65 }, { label: "Q1'23", value: 62 }, { label: "Q3'23", value: 55 },
        { label: "Q1'24", value: 52 }, { label: "Q3'24", value: 48 },
      ],
      xLabel: "Quarter",
      yLabel: "30-Day IV (%)",
      highlightIdx: 0,
      footnote: "Q1'21 (★): peak valuation period, IV also highest at 85%. As P/E compressed, IV stayed elevated relative to peers",
    },
    example: {
      heading: "Valuation Trade: IV Rank Entry",
      company: "TSLA Premium Sell on High IVR",
      scenario: "TSLA at $220, IV rank 68th percentile (historically expensive). Sold a $200/$195 put spread for $1.45 credit. Thesis: valuation compressed, stock stabilizing, IV rich.",
      setupItems: [
        { label: "TSLA Price", value: "$220", color: "#94a3b8" },
        { label: "IV Rank", value: "68th %ile", color: "#ef4444" },
        { label: "Credit", value: "$1.45", color: "#10b981" },
        { label: "Put Spread", value: "$200/$195", color: "#6366f1" },
        { label: "Max Risk", value: "$3.55", color: "#ef4444" },
      ],
      outcome: "+$1.45 full credit",
      outcomeDetail: "TSLA stayed above $205 through expiry. Spread expired worthless, kept full $1.45 credit. IV rank identifies when options are expensive relative to history. Sell premium when IVR > 50, buy when IVR < 20.",
      outcomeColor: "#10b981",
    },
    takeaways: [
      "High P/E stocks carry structurally higher IV, sell that premium",
      "IV rank tells you if options are historically cheap or expensive",
      "Multiple contraction plus IV expansion = double headwind for longs",
      "Combine valuation analysis with IV rank for highest conviction trades",
    ],
  },

  "Cash Runway": {
    description: "Liquidity is the oxygen of a company. Running out of cash before profitability destroys equity value fast, and option holders get hit hardest.",
    bullets: [
      "Cash runway = months of operating expenses covered by current cash",
      "Debt wall = large debt maturity coming due that may require refinancing",
      "Burn rate acceleration signals deteriorating business fundamentals",
      "Short runway + high IV = dangerous long option setup",
    ],
    multiMetrics: {
      heading: "RIVN FY2023 Liquidity Runway Audit",
      description: "Rivian: a high-profile EV company managing a tight liquidity runway",
      metrics: [
        { label: "Cash on Hand", value: "$7.9B", change: "vs $11.6B prior year", changeUp: false, color: "#3b82f6" },
        { label: "Quarterly Burn", value: "-$1.4B", change: "improving trend", changeUp: true, color: "#ef4444" },
        { label: "Runway", value: "~14 mo", change: "at current burn", changeUp: false, color: "#f59e0b" },
        { label: "Debt Load", value: "$4.3B", change: "2026 maturity wall", changeUp: false, color: "#ef4444" },
        { label: "Production", value: "57k units", change: "+149% YoY", changeUp: true, color: "#10b981" },
        { label: "Stock Reaction", value: "-52%", change: "FY2023 vs SPY", changeUp: false, color: "#ef4444" },
      ],
    },
    chart: {
      heading: "RIVN Quarterly Cash Burn, 6 Quarters",
      subheading: "Cash burn improving but still deeply negative, watch the runway clock",
      data: [
        { label: "Q2'22", value: -1.7 }, { label: "Q3'22", value: -1.7 }, { label: "Q4'22", value: -1.9 },
        { label: "Q1'23", value: -1.6 }, { label: "Q2'23", value: -1.4 }, { label: "Q3'23", value: -1.4 },
      ],
      xLabel: "Quarter",
      yLabel: "Cash Burn ($B)",
      highlightIdx: 4,
      footnote: "Q2'23 (★): burn rate improving to -$1.4B. Still, at this pace, roughly 14 months runway without new capital raise",
    },
    example: {
      heading: "Liquidity Trade: Runway Risk Short",
      company: "RIVN Runway Risk Put Spread",
      scenario: "RIVN at $22, 14-month runway with $4.3B debt wall in 2026. IV rank 72nd percentile (dilution risk priced in but not fully). Bought $20/$15 put spread for $1.80 debit.",
      setupItems: [
        { label: "RIVN Price", value: "$22", color: "#94a3b8" },
        { label: "Runway", value: "~14 mo", color: "#ef4444" },
        { label: "Put Spread", value: "$20/$15", color: "#6366f1" },
        { label: "Debit Paid", value: "$1.80", color: "#f59e0b" },
        { label: "Debt Wall", value: "2026", color: "#ef4444" },
      ],
      outcome: "+$3.20 profit",
      outcomeDetail: "RIVN fell to $13 over 6 months as dilution concerns grew. Spread maxed: $5 - $1.80 = +$3.20. +178% return. Liquidity runway analysis provided a fundamental thesis that options amplified.",
      outcomeColor: "#10b981",
    },
    takeaways: [
      "Always check cash runway before buying stock in pre profit companies",
      "Burn rate trend matters more than the absolute level",
      "Debt maturity walls create predictable stress points, trade around them",
      "Short runway + high IV = put spread opportunity with fundamental backing",
    ],
  },

  "Free Cash Flow": {
    description: "Free cash flow is the single most important number in fundamental analysis. It is the cash a company actually generates after maintaining and growing its business.",
    bullets: [
      "FCF = Operating cash flow minus capital expenditures",
      "Unlike earnings, FCF is hard to manipulate with accounting tricks",
      "FCF yield = FCF / market cap, compare to Treasury yield for context",
      "Consistent FCF growth drives share buybacks, dividends, and multiple expansion",
    ],
    multiMetrics: {
      heading: "AAPL FY2024 Free Cash Flow Deep Dive",
      description: "Apple: the gold standard for FCF generation among large-cap companies",
      metrics: [
        { label: "Revenue", value: "$391B", change: "+2% YoY", changeUp: true, color: "#10b981" },
        { label: "Operating CF", value: "$122B", change: "+7% YoY", changeUp: true, color: "#6366f1" },
        { label: "CapEx", value: "$11B", change: "only 3% of rev", changeUp: true, color: "#f59e0b" },
        { label: "Free Cash Flow", value: "$111B", change: "Record high", changeUp: true, color: "#10b981" },
        { label: "FCF Yield", value: "3.3%", change: "vs 4.3% Treasury", changeUp: false, color: "#3b82f6" },
        { label: "Buybacks", value: "$90B", change: "81% of FCF returned", changeUp: true, color: "#8b5cf6" },
      ],
    },
    chart: {
      heading: "AAPL Free Cash Flow, 6 Year Trend",
      subheading: "Annual FCF ($B), consistent growth with only one dip in FY23",
      data: [
        { label: "FY19", value: 58.9 }, { label: "FY20", value: 73.4 }, { label: "FY21", value: 93.0 },
        { label: "FY22", value: 111.4 }, { label: "FY23", value: 99.6 }, { label: "FY24", value: 111.4 },
      ],
      xLabel: "Fiscal Year",
      yLabel: "Free Cash Flow ($B)",
      highlightIdx: 3,
      footnote: "FY22 (★) peak FCF $111B. Apple returned most via buybacks and dividends. FY23 dip was temporary; FY24 matched the peak",
    },
    example: {
      heading: "FCF Trade: Valuation-Driven Entry",
      company: "AAPL FCF Yield vs Treasury Decision",
      scenario: "FY24: AAPL at $220/share, market cap $3.4T, FCF $111B → FCF yield 3.3%. 10Y Treasury at 4.3%. Risk free rate pays more than AAPL's FCF yield.",
      setupItems: [
        { label: "FCF Yield", value: "3.3%", color: "#f59e0b" },
        { label: "10Y Treasury", value: "4.3%", color: "#ef4444" },
        { label: "P/E", value: "28×", color: "#3b82f6" },
        { label: "Services Mix", value: "26%", color: "#10b981" },
      ],
      outcome: "Hold, not add",
      outcomeDetail: "Strong FCF but valuation stretched vs risk free rate. Services growth (26% of revenue) justifies some premium. Lesson: use FCF yield vs Treasury yield to anchor valuation decisions. Great business does not mean great stock at any price.",
      outcomeColor: "#f59e0b",
    },
    takeaways: [
      "FCF is harder to manipulate than reported earnings, trust it more",
      "Compare FCF yield to the 10 year Treasury to assess relative value",
      "Consistent FCF growth leads to buybacks, EPS growth, and multiple expansion",
      "Low CapEx + high FCF = asset light business model (most valuable kind)",
    ],
  },

  "P/E Ratio": {
    description: "Valuation ratios translate a company's fundamentals into a price you pay for each dollar of earnings, assets, or cash flow. Master these and you'll never overpay again.",
    bullets: [
      "P/E = price per dollar of earnings, context depends on growth rate",
      "PEG ratio = P/E divided by growth rate, adjusts for growth expectations",
      "EV/EBITDA is sector agnostic and better for comparing capital structures",
      "Low P/B can signal deep value or a dying business, always check FCF",
    ],
    multiMetrics: {
      heading: "Sector Valuation Snapshot, Q1 2024",
      description: "Comparing key ratios across sectors reveals where the market is pricing in growth vs value",
      metrics: [
        { label: "Tech (avg P/E)", value: "34×", change: "vs 21× S&P", changeUp: false, color: "#6366f1" },
        { label: "Energy (avg P/E)", value: "12×", change: "value territory", changeUp: true, color: "#10b981" },
        { label: "NVDA P/E", value: "65×", change: "AI growth premium", changeUp: false, color: "#f59e0b" },
        { label: "NVDA PEG", value: "1.1×", change: "fair despite P/E", changeUp: true, color: "#10b981" },
        { label: "S&P EV/EBITDA", value: "16×", change: "historical avg 14×", changeUp: false, color: "#3b82f6" },
        { label: "Banks avg P/B", value: "1.2×", change: "near tangible book", changeUp: true, color: "#8b5cf6" },
      ],
    },
    chart: {
      heading: "S&P 500 P/E Ratio, 8 Year History",
      subheading: "Market valuation cycles, expensive at peaks and cheap at troughs",
      data: [
        { label: "2017", value: 22 }, { label: "2018", value: 18 }, { label: "2019", value: 23 },
        { label: "2020", value: 38 }, { label: "2021", value: 27 }, { label: "2022", value: 17 },
        { label: "2023", value: 22 }, { label: "2024", value: 24 },
      ],
      xLabel: "Year",
      yLabel: "S&P 500 P/E",
      highlightIdx: 3,
      footnote: "2020 (★): P/E hit 38x as earnings collapsed during COVID. The ratio is useless during earnings troughs; use EV/EBITDA instead",
    },
    example: {
      heading: "Valuation Trade: PEG-Driven Entry",
      company: "NVDA High P/E but Fair PEG",
      scenario: "NVDA at 65× P/E looked expensive. But EPS growing 200%+ YoY → PEG = 65 / 200 = 0.33. A PEG below 1.0 traditionally signals undervaluation relative to growth.",
      setupItems: [
        { label: "NVDA P/E", value: "65×", color: "#f59e0b" },
        { label: "EPS Growth", value: "+200%", color: "#10b981" },
        { label: "PEG Ratio", value: "0.33×", color: "#10b981" },
        { label: "EV/EBITDA", value: "48×", color: "#3b82f6" },
      ],
      outcome: "Buy conviction",
      outcomeDetail: "Despite the headline P/E of 65x, the PEG of 0.33 showed NVDA was actually cheap relative to its growth rate. Stock tripled over the next 12 months. Lesson: never use P/E in isolation, always divide by growth rate.",
      outcomeColor: "#10b981",
    },
    takeaways: [
      "P/E without PEG is like speed without direction, incomplete",
      "Use EV/EBITDA to compare companies with different debt levels",
      "P/B below 1.0 can be deep value or a value trap, verify with FCF",
      "Sector context is everything, a 12x P/E is cheap in tech but expensive in utilities",
    ],
  },

  "Revenue Beat": {
    description: "Earnings surprises are the single biggest short term stock price catalyst. Learning to read earnings quality separates reactive traders from anticipatory ones.",
    bullets: [
      "Revenue beat = company sold more than analysts expected (top line)",
      "EPS beat = company earned more per share than expected (bottom line)",
      "Guidance raise is often more important than the beat itself",
      "A beat on earnings but a miss on revenue is often a red flag",
    ],
    multiMetrics: {
      heading: "NVDA Q3 FY2024 Earnings Breakdown",
      description: "NVIDIA's Q3 2024 earnings report: a masterclass in what an earnings beat looks like",
      metrics: [
        { label: "Revenue (Actual)", value: "$18.1B", change: "vs $16.9B est.", changeUp: true, color: "#10b981" },
        { label: "EPS (Actual)", value: "$4.02", change: "+7% beat", changeUp: true, color: "#6366f1" },
        { label: "Data Center Rev", value: "$14.5B", change: "+279% YoY", changeUp: true, color: "#f59e0b" },
        { label: "Revenue Beat", value: "+7.1%", change: "above consensus", changeUp: true, color: "#10b981" },
        { label: "Gross Margin", value: "74.0%", change: "+4pp YoY", changeUp: true, color: "#3b82f6" },
        { label: "Stock Reaction", value: "+9.3%", change: "next-day move", changeUp: true, color: "#10b981" },
      ],
    },
    chart: {
      heading: "NVDA Revenue Growth, 8 Quarters",
      subheading: "Quarterly revenue ($B), each beat sent the stock higher",
      data: [
        { label: "Q4'22", value: 6.1 }, { label: "Q1'23", value: 7.2 }, { label: "Q2'23", value: 13.5 },
        { label: "Q3'23", value: 18.1 }, { label: "Q4'23", value: 22.1 }, { label: "Q1'24", value: 26.0 },
        { label: "Q2'24", value: 30.0 }, { label: "Q3'24", value: 35.1 },
      ],
      xLabel: "Quarter",
      yLabel: "Revenue ($B)",
      highlightIdx: 3,
      footnote: "Q3'23 (★) was the inflection earnings where AI demand became undeniable, +279% YoY in Data Center",
    },
    example: {
      heading: "Earnings Trade: Pre-Report Positioning",
      company: "NVDA Q3 FY2024 Earnings Play",
      scenario: "You anticipated the beat by buying NVDA 1-week before earnings. Stock at $460. You bought a $470/$500 call spread at $8.50 debit, capping max risk.",
      setupItems: [
        { label: "NVDA Price", value: "$460", color: "#94a3b8" },
        { label: "Spread Paid", value: "$8.50", color: "#f59e0b" },
        { label: "Strategy", value: "$470/$500 CS", color: "#6366f1" },
        { label: "Max Risk", value: "$8.50", color: "#ef4444" },
        { label: "Post-Earn Move", value: "+9.3%", color: "#10b981" },
      ],
      outcome: "+$21.50 profit",
      outcomeDetail: "NVDA beat by 7.1% on revenue. Stock gapped to $502. Spread maxed out: collected $30 - $8.50 paid = $21.50 per spread. +252% return on defined risk. Earnings research paid off.",
      outcomeColor: "#10b981",
    },
    takeaways: [
      "Revenue beats matter more than EPS beats, revenue is harder to manipulate",
      "Read the guidance commentary, forward outlook moves the stock more than the beat",
      "Use defined risk spreads (not naked options) for earnings plays",
      "Close positions after the print, IV crush destroys premium regardless of direction",
    ],
  },

  default: {
    description: "Fundamental analysis evaluates a company's financial health to determine if its stock is fairly valued, the foundation of long term investing.",
    bullets: [
      "Revenue and earnings growth show business momentum",
      "Margins reveal operational efficiency and pricing power",
      "Debt levels indicate financial risk and flexibility",
      "Free cash flow is the lifeblood, harder to manipulate than reported profits",
    ],
    multiMetrics: {
      heading: "AAPL FY2024 Core Fundamentals",
      description: "Apple's annual financial snapshot, a benchmark for what healthy fundamentals look like",
      metrics: [
        { label: "Revenue", value: "$391B", change: "+2% YoY", changeUp: true, color: "#10b981" },
        { label: "Net Income", value: "$101B", change: "+8% YoY", changeUp: true, color: "#6366f1" },
        { label: "Gross Margin", value: "46.2%", change: "+1.2pp", changeUp: true, color: "#f59e0b" },
        { label: "Free Cash Flow", value: "$111B", change: "Record high", changeUp: true, color: "#10b981" },
        { label: "P/E Ratio", value: "28×", change: "vs S&P 21×", changeUp: false, color: "#3b82f6" },
        { label: "Dividend Yield", value: "0.5%", change: "+5% YoY raise", changeUp: true, color: "#8b5cf6" },
      ],
    },
    chart: {
      heading: "Free Cash Flow, 6 Year Trend",
      subheading: "AAPL free cash flow ($B), the number that matters most for long term investors",
      data: [
        { label: "FY19", value: 58.9 }, { label: "FY20", value: 73.4 }, { label: "FY21", value: 93.0 },
        { label: "FY22", value: 111.4 }, { label: "FY23", value: 99.6 }, { label: "FY24", value: 111.4 },
      ],
      xLabel: "Fiscal Year",
      yLabel: "Free Cash Flow ($B)",
      highlightIdx: 3,
      footnote: "FY22 (★) peak FCF of $111B. Apple returned most of it to shareholders via buybacks and dividends",
    },
    example: {
      heading: "Valuation Trade: FCF Based Conviction",
      company: "AAPL Long Thesis Built on Fundamentals",
      scenario: "FY24: AAPL generating $111B free cash flow on $391B revenue. At $220/share, market cap = $3.4T. FCF yield = 3.3%. Compared to 10yr Treasury at 4.3%, AAPL appeared fully valued.",
      setupItems: [
        { label: "FCF Yield", value: "3.3%", color: "#f59e0b" },
        { label: "10Y Treasury", value: "4.3%", color: "#ef4444" },
        { label: "P/E", value: "28×", color: "#3b82f6" },
        { label: "Services Mix", value: "26%", color: "#10b981" },
      ],
      outcome: "Hold, not add",
      outcomeDetail: "Fundamentals are strong but valuation is stretched. The services segment growing to 26% of revenue justifies a premium. Lesson: great business does not mean great stock at any price. Entry point matters.",
      outcomeColor: "#f59e0b",
    },
    takeaways: [
      "Fundamentals drive stock prices over the long term, short term is noise",
      "Look at trends, not just single quarter snapshots",
      "Compare against sector peers, context is everything",
      "Great fundamentals with bad valuation = waiting game",
    ],
  },
};

// ── Short-form card (for small durationInFrames) ───────────────────────────────
const DashboardCardScene: React.FC<{ metric: string; value: string; accent: string; title: string }> = ({ metric, value, accent, title }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const cardAnim = spring({ frame: frame - 20, fps, config: { damping: 14, stiffness: 140 } });
  const valueAnim = spring({ frame: frame - 50, fps, config: { damping: 12, stiffness: 120 } });
  return (
    <AbsoluteFill style={{ backgroundColor: S.bg, justifyContent: "center", alignItems: "center" }}>
      <div style={{ background: "rgba(255,255,255,0.04)", border: `2px solid ${accent}40`, borderRadius: 32, padding: "64px 80px", minWidth: 600, textAlign: "center", opacity: cardAnim, transform: `scale(${0.9 + cardAnim * 0.1})`, boxShadow: `0 0 80px ${accent}15` }}>
        <div style={{ fontSize: 18, fontWeight: 700, letterSpacing: "0.2em", color: accent, textTransform: "uppercase", marginBottom: 16 }}>{title}</div>
        <div style={{ fontSize: 28, color: "#94a3b8", marginBottom: 24, fontWeight: 500 }}>{metric}</div>
        <div style={{ fontSize: 96, fontWeight: 900, color: "#fff", opacity: valueAnim, transform: `translateY(${(1 - valueAnim) * 20}px)` }}>{value}</div>
        <div style={{ width: interpolate(valueAnim, [0, 1], [0, 120]), height: 4, borderRadius: 2, backgroundColor: accent, margin: "24px auto 0" }} />
      </div>
    </AbsoluteFill>
  );
};

// ── Main export ─────────────────────────────────────────────────────────────────
export const FundamentalDashboardVideo = ({
  title, subtitle, subjectLabel, posterUrl, accent, glow, metric, value,
}: FundamentalDashboardProps) => {
  const { fps, durationInFrames } = useVideoConfig();
  const info = TOPIC_DATA[metric] || TOPIC_DATA["default"];

  if (durationInFrames < 600) {
    return (
      <AbsoluteFill style={{ backgroundColor: S.bg, color: "white", fontFamily: "Inter, sans-serif" }}>
        <Sequence from={0} durationInFrames={4 * fps}>
          <CinematicIntro title={title} subtitle={subtitle} subjectLabel={subjectLabel} posterUrl={posterUrl} accent={accent} glow={glow} />
        </Sequence>
        <Sequence from={4 * fps} durationInFrames={8 * fps}>
          <DashboardCardScene metric={metric} value={value} accent={accent} title={title} />
        </Sequence>
      </AbsoluteFill>
    );
  }

  const mm = info.multiMetrics;
  const ch = info.chart;
  const ex = info.example;

  const scenes: SceneDef[] = [
    // Scene 1: Title + concept
    { render: () => <TitleScene label="Fundamental Analysis" title={title} subtitle={info.description} accent={accent} /> },
    // Scene 2: What to look for
    { render: () => <BulletScene heading="What to Look For" bullets={info.bullets} accent={accent} /> },
    // Scene 3: Multi-metric dashboard (real company data)
    { durationInFrames: Math.floor(durationInFrames * 0.24), render: () => (
      <MultiMetricScene heading={mm.heading} description={mm.description} metrics={mm.metrics} accent={accent} />
    )},
    // Scene 4: Animated trend chart
    { durationInFrames: Math.floor(durationInFrames * 0.22), render: () => (
      <SvgLineChartScene
        heading={ch.heading}
        subheading={ch.subheading}
        data={ch.data}
        accent={accent}
        xLabel={ch.xLabel}
        yLabel={ch.yLabel}
        highlightIdx={ch.highlightIdx}
        footnote={ch.footnote}
      />
    )},
    // Scene 5: Real-world trade example
    { durationInFrames: Math.floor(durationInFrames * 0.24), render: () => (
      <RealWorldExampleScene
        heading={ex.heading}
        company={ex.company}
        scenario={ex.scenario}
        setupItems={ex.setupItems}
        outcome={ex.outcome}
        outcomeDetail={ex.outcomeDetail}
        outcomeColor={ex.outcomeColor}
        accent={accent}
      />
    )},
    // Scene 6: Takeaways
    { render: () => <SummaryScene heading="Key Takeaways" takeaways={info.takeaways} accent={accent} closingLine="Great fundamentals + right entry price = the foundation of every winning trade." /> },
  ];

  return <SceneManager scenes={scenes} theme={S} />;
};
