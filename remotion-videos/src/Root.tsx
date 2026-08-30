import { Composition } from "remotion";
import { OptionsDemo } from "./components/OptionsDemo";
import { FrameworkDemo } from "./components/FrameworkDemo";
import { LessonWalkthrough, type LessonWalkthroughProps } from "./components/LessonWalkthrough";
import { BasicsFlowVideo } from "./components/BasicsFlowVideo";
import { MarketMechanicsVideo } from "./components/MarketMechanicsVideo";
import { TechnicalChartVideo } from "./components/TechnicalChartVideo";
import { FundamentalDashboardVideo } from "./components/FundamentalDashboardVideo";
import { CoreConceptVideo } from "./components/CoreConceptVideo";
import { StrategyBuilderVideo, type StrategyBuilderProps } from "./components/StrategyBuilderVideo";
import { GreekVisualizerVideo, type GreekVisualizerProps } from "./components/GreekVisualizerVideo";
import { PayoffDiagramVideo, type PayoffDiagramProps } from "./components/PayoffDiagramVideo";
import { GreekCurveVideo, type GreekCurveProps } from "./components/GreekCurveVideo";
import { OptionTicketVideo, type OptionTicketProps } from "./components/OptionTicketVideo";
import { PersonalFinanceVideo, type PersonalFinanceProps } from "./components/PersonalFinanceVideo";
import { StocksSlideVideo, STOCKS_SLIDE_TOTAL_FRAMES } from "./components/StocksSlideVideo";
import { CityPulse60 } from "./components/CityPulse60";
import { OpenWorldGameSim90 } from "./components/OpenWorldGameSim90";
import { OpenWorldGameplayProof90 } from "./components/OpenWorldGameplayProof90";
import { frameworkDemoConfig, getDemoDurationFrames, optionsDemoConfig } from "./data/demoScenes";

export const RemotionRoot = () => {
  const lessonDefaults: LessonWalkthroughProps = {
    title: "Lesson Walkthrough",
    subtitle: "Learn the concept, then apply it in practice mode.",
    objectives: ["Review the core concept", "Apply one practical step", "Track your result"],
    subjectLabel: "Options & Markets",
    posterUrl: "/assets/lessons/basics-flow.svg",
    accent: "#22D3EE",
    glow: "rgba(34, 211, 238, 0.65)",
  };

  return (
    <>
      <Composition
        id="OptionsEducatorDemo"
        component={OptionsDemo}
        durationInFrames={getDemoDurationFrames(optionsDemoConfig, 30)}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={optionsDemoConfig}
      />
      <Composition
        id="FrameworkDemo"
        component={FrameworkDemo}
        durationInFrames={getDemoDurationFrames(frameworkDemoConfig, 30)}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={frameworkDemoConfig}
      />
      <Composition
        id="LessonWalkthrough"
        component={LessonWalkthrough}
        durationInFrames={8 * 30}
        fps={30}
        width={1280}
        height={720}
        defaultProps={lessonDefaults}
      />
      <Composition
        id="BasicsFlowVideo"
        component={BasicsFlowVideo}
        durationInFrames={840} // 28 seconds at 30fps
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="StrategyBuilderVideo"
        component={StrategyBuilderVideo}
        durationInFrames={360} // 12 seconds
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          title: "Iron Condor",
          subtitle: "Defined-risk neutral options strategy",
          subjectLabel: "Options Strategies",
          posterUrl: "/assets/lessons/iron-condor.svg",
          accent: "#22D3EE",
          glow: "rgba(34, 211, 238, 0.65)",
          underlyingPrice: 150,
          legs: [
            { type: "put", action: "buy", strike: 130, premium: 1.5 },
            { type: "put", action: "sell", strike: 140, premium: 3.5 },
            { type: "call", action: "sell", strike: 160, premium: 3.0 },
            { type: "call", action: "buy", strike: 170, premium: 1.2 },
          ]
        }}
      />
      <Composition
        id="GreekVisualizerVideo"
        component={GreekVisualizerVideo}
        durationInFrames={360} // 12 seconds
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          title: "Delta",
          subtitle: "Directional price sensitivity",
          subjectLabel: "The Greeks",
          posterUrl: "/assets/lessons/delta-scaling.svg",
          accent: "#10b981",
          glow: "rgba(16, 185, 129, 0.65)",
          greekName: "Delta",
          startValue: 0.1,
          endValue: 0.85,
          explanation: "As the stock price moves deeper in-the-money, Delta accelerates towards 1.0 (or -1.0 for puts), increasing the option's sensitivity to further price changes."
        }}
      />
      <Composition
        id="MarketMechanicsVideo"
        component={MarketMechanicsVideo}
        durationInFrames={360}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          title: "Order Book",
          subtitle: "Level 2 Market Data",
          subjectLabel: "Market Mechanics",
          posterUrl: "/assets/lessons/order-types.svg",
          accent: "#f43f5e",
          glow: "rgba(244, 63, 94, 0.65)",
          mechanicType: "order-book",
          dataPoints: []
        }}
      />
      <Composition
        id="TechnicalChartVideo"
        component={TechnicalChartVideo}
        durationInFrames={360}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          title: "Candlesticks",
          subtitle: "Reading price action",
          subjectLabel: "Technical Analysis",
          posterUrl: "/assets/lessons/candlesticks-101.svg",
          accent: "#3b82f6",
          glow: "rgba(59, 130, 246, 0.65)",
          indicator: "candlesticks",
          candles: []
        }}
      />
      <Composition
        id="FundamentalDashboardVideo"
        component={FundamentalDashboardVideo}
        durationInFrames={360}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          title: "P/E Ratios",
          subtitle: "Valuation vs Volatility",
          subjectLabel: "Fundamentals",
          posterUrl: "/assets/lessons/valuation-vs-vol.svg",
          accent: "#a855f7",
          glow: "rgba(168, 85, 247, 0.65)",
          metric: "pe-ratio",
          value: "35.4"
        }}
      />
      <Composition
        id="CoreConceptVideo"
        component={CoreConceptVideo}
        durationInFrames={360}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          title: "Risk Sizer",
          subtitle: "Capital preservation",
          subjectLabel: "Core Basics",
          posterUrl: "/assets/lessons/risk-sizer.svg",
          accent: "#fbbf24",
          glow: "rgba(251, 191, 36, 0.65)",
          conceptHeadline: "Never risk more than 2% of your portfolio on a single trade."
        }}
      />
      {/* ─── New Specialist Components ─────────────────────────────────────── */}
      <Composition
        id="PayoffDiagramVideo"
        component={PayoffDiagramVideo}
        durationInFrames={360}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          title: "Options Flow",
          subtitle: "Watch payoff reshape as price moves",
          accent: "#10b981",
          strategyType: "long-call" as const,
          underlyingPrice: 150,
          strike1: 150,
          strike2: 155,
          strike3: 160,
          strike4: 165,
          premium: 2.0,
          premium2: 2.0,
        }}
      />
      <Composition
        id="GreekCurveVideo"
        component={GreekCurveVideo}
        durationInFrames={360}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          title: "Gamma Acceleration",
          subtitle: "Delta speeds up near the strike",
          accent: "#f43f5e",
          greekType: "gamma" as const,
          strike: 150,
          ivLow: 20,
          ivHigh: 55,
          rateLow: 3.5,
          rateHigh: 6.0,
        }}
      />
      <Composition
        id="GreekCurveVegaVideo"
        component={GreekCurveVideo}
        durationInFrames={360}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          title: "Vega Sensitivity",
          subtitle: "Longer-dated options react more to IV changes",
          accent: "#8b5cf6",
          greekType: "vega" as const,
          strike: 150,
          ivLow: 20,
          ivHigh: 55,
          rateLow: 3.5,
          rateHigh: 6.0,
        }}
      />
      <Composition
        id="GreekCurveRhoVideo"
        component={GreekCurveVideo}
        durationInFrames={360}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          title: "Rho & Rate Risk",
          subtitle: "LEAPS are dramatically more sensitive to rate changes",
          accent: "#06b6d4",
          greekType: "rho" as const,
          strike: 150,
          ivLow: 20,
          ivHigh: 55,
          rateLow: 3.5,
          rateHigh: 6.0,
        }}
      />
      <Composition
        id="OptionTicketVideo"
        component={OptionTicketVideo}
        durationInFrames={360}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          title: "Strike Selection",
          subtitle: "ITM, ATM, OTM explained",
          accent: "#3b82f6",
          ticketType: "strike-zones" as const,
          underlyingPrice: 150,
          strikePrice: 150,
          daysToExpiry: 30,
        }}
      />
      <Composition
        id="PersonalFinanceVideo"
        component={PersonalFinanceVideo}
        durationInFrames={360}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          title: "Budgeting Basics",
          subtitle: "The 50/30/20 rule",
          accent: "#6366f1",
          financeType: "budget" as const,
        }}
      />
      {/* ─── Stocks Education ──────────────────────────────────────────────── */}
      <Composition
        id="StocksSlideVideo"
        component={StocksSlideVideo}
        durationInFrames={STOCKS_SLIDE_TOTAL_FRAMES}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          title:        "What Is a Stock?",
          subtitle:     "Equity ownership, exchanges, bull/bear cycles",
          subjectLabel: "Stock Basics",
          accent:       "#6366f1",
          glow:         "rgba(99,102,241,0.65)",
        }}
      />
      <Composition
        id="CityPulse60"
        component={CityPulse60}
        durationInFrames={1800}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          title: "City Pulse: Regime + Ticket + Execution",
          regime: "trending" as const,
          headline: "Opening liquidity pockets widen spreads while implied move remains elevated.",
          checklist: [
            "Lock directional thesis before strike and expiry selection.",
            "Use defined-risk structure for first action.",
            "Route entry with limit when spread is wide.",
          ],
        }}
      />
      <Composition
        id="OpenWorldGameSim90"
        component={OpenWorldGameSim90}
        durationInFrames={2700}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="OpenWorldGameplayProof90"
        component={OpenWorldGameplayProof90}
        durationInFrames={2700}
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};

export default RemotionRoot;
