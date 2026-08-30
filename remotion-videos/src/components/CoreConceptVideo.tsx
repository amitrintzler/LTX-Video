import { useVideoConfig } from "remotion";
import {
    SceneManager, TitleScene, BulletScene, SummaryScene,
    SvgLineChartScene, RealWorldExampleScene, type SceneDef,
} from "./SceneSystem";
import React from "react";

export type CoreConceptProps = {
    title: string;
    subtitle: string;
    subjectLabel: string;
    posterUrl: string;
    accent: string;
    glow: string;
    conceptHeadline: string;
    conceptType?: "risk" | "exit" | "intro" | "default";
};

type ConceptData = {
    description: string;
    bullets: string[];
    chartHeading: string;
    chartSubheading: string;
    chartData: Array<{ label: string; value: number }>;
    chartXLabel: string;
    chartYLabel: string;
    chartHighlightIdx: number;
    chartFootnote: string;
    realWorldHeading: string;
    realWorldCompany: string;
    realWorldScenario: string;
    realWorldSetup: Array<{ label: string; value: string; color?: string }>;
    realWorldOutcome: string;
    realWorldOutcomeDetail: string;
    realWorldOutcomeColor: string;
    takeaways: string[];
};

const CONCEPT_DATA: Record<string, ConceptData> = {
    risk: {
        description: "Position sizing is the most important skill in trading. Risking 1-2% of your account per trade ensures no single loss can devastate your portfolio.",
        bullets: [
            "Risk 1-2% max per trade — never more, regardless of conviction",
            "Position size = (Account × risk%) ÷ distance to stop loss",
            "Smaller positions let you stay in the game through losing streaks",
            "Consistent sizing turns skill into compounding profits over time",
        ],
        chartHeading: "1% Risk vs 5% Risk: 10-Trade Sequence",
        chartSubheading: "Account value after a mixed 10-trade streak — 1% risk stays alive, 5% risk craters",
        chartData: [
            { label: "Start", value: 100000 },
            { label: "T2", value: 99000 },
            { label: "T4", value: 98010 },
            { label: "T6", value: 99990 },
            { label: "T8", value: 101990 },
            { label: "T10", value: 103009 },
        ],
        chartXLabel: "Trade #",
        chartYLabel: "Account ($)",
        chartHighlightIdx: 5,
        chartFootnote: "Trade 10 (★) — 1% risk account still at $103k after mixed results. 5% risk same sequence = $72k. Survival > optimization.",
        realWorldHeading: "Real Trade: SPY Put Spread",
        realWorldCompany: "$50K Account · 1% Risk Rule Applied",
        realWorldScenario: "SPY put spread with stop $2.00 away. Risk budget = $500. Sized to 2-3 contracts instead of 10 — trade worked for a controlled +$680 gain.",
        realWorldSetup: [
            { label: "Account", value: "$50,000" },
            { label: "Risk %", value: "1%" },
            { label: "Risk $", value: "$500" },
            { label: "Stop Distance", value: "$2.00" },
            { label: "Contracts", value: "2-3" },
        ],
        realWorldOutcome: "+$680 controlled gain",
        realWorldOutcomeDetail: "Without sizing rule: 10 contracts = unacceptable risk on same trade. 1% rule kept the loss survivable if it had gone wrong.",
        realWorldOutcomeColor: "#10b981",
        takeaways: [
            "1% rule: max loss per trade = 1% of total account",
            "Size down when losing, never up",
            "Consistency of sizing > quality of individual trade ideas",
            "Position size is the only risk you fully control",
        ],
    },

    exit: {
        description: "The exit determines your actual P&L — not the entry. Having a clear exit plan before you trade eliminates emotional decisions when it matters most.",
        bullets: [
            "Set profit target before entering — 50-100% of debit paid is common",
            "Stop loss at 50% of premium paid — cut and move on",
            "Time exit: close 7-14 DTE to avoid gamma risk on defined-risk trades",
            "Never hold through expiry hoping for recovery — IV crush kills",
        ],
        chartHeading: "P&L Over 21 Days: Hold vs. Exit",
        chartSubheading: "Same trade, 3 different exit strategies — peak P&L vs. holding to expiry",
        chartData: [
            { label: "Entry", value: 0 },
            { label: "Day3", value: 120 },
            { label: "Day7", value: 280 },
            { label: "Day10", value: 420 },
            { label: "Day14", value: 380 },
            { label: "Day17", value: 190 },
            { label: "Day19", value: 80 },
            { label: "Day21", value: -150 },
        ],
        chartXLabel: "Days Held",
        chartYLabel: "P&L ($)",
        chartHighlightIdx: 3,
        chartFootnote: "Day 10 (★) — maximum P&L of $420. Holding to expiry turned a winner into a loser. Time exits protect profits.",
        realWorldHeading: "Real Trade: AAPL Call Spread",
        realWorldCompany: "AAPL · Planned Exit Before Entry",
        realWorldScenario: "Bought AAPL call spread for $3.20. Set 100% profit target ($6.40) and 50% stop ($1.60). Target hit on day 8 — closed for +$3.20. Without a plan, theta eroded the gain.",
        realWorldSetup: [
            { label: "Debit Paid", value: "$3.20" },
            { label: "Profit Target", value: "$6.40 (100%)" },
            { label: "Stop Loss", value: "$1.60 (50%)" },
            { label: "Time Exit", value: "7 DTE" },
            { label: "Day Hit", value: "Day 8" },
        ],
        realWorldOutcome: "+$3.20 profit (100%)",
        realWorldOutcomeDetail: "Exit plan executed without emotion. Traders who held same position past day 10 saw gains evaporate as theta accelerated.",
        realWorldOutcomeColor: "#10b981",
        takeaways: [
            "Set exits before entering — remove emotion from the equation",
            "50% stop loss is the professional standard for defined-risk trades",
            "100% gain target on debit spreads = excellent risk/reward",
            "Time decay accelerates after 21 DTE — always have a time exit",
        ],
    },

    intro: {
        description: "Options give you the right — not the obligation — to buy or sell a stock at a specific price before a specific date. That right is what you pay premium for.",
        bullets: [
            "Call options: right to BUY at strike price — profits when stock rises",
            "Put options: right to SELL at strike price — profits when stock falls",
            "Every option expires — time is always working against the buyer",
            "Premium paid = maximum loss as a buyer. Always defined.",
        ],
        chartHeading: "$100 Call Option Value at Expiry",
        chartSubheading: "Call option payoff across different stock prices at expiration",
        chartData: [
            { label: "$80", value: 0 },
            { label: "$90", value: 0 },
            { label: "$95", value: 0 },
            { label: "$100", value: 0 },
            { label: "$105", value: 5 },
            { label: "$110", value: 10 },
            { label: "$115", value: 15 },
            { label: "$120", value: 20 },
        ],
        chartXLabel: "Stock Price at Expiry",
        chartYLabel: "Option Value ($)",
        chartHighlightIdx: 5,
        chartFootnote: "At $110 (★) — $100 call worth $10 at expiry. Paid $3 premium → net profit $7. Below $100, premium fully lost.",
        realWorldHeading: "Real Trade: SPY Call",
        realWorldCompany: "SPY · $415 → $432 Rally",
        realWorldScenario: "Bought SPY $420 call for $3.80 with SPY at $415. SPY rallied to $432 — call worth $12.80, a +237% gain. Max risk was only $380 (the premium paid).",
        realWorldSetup: [
            { label: "SPY Price", value: "$415" },
            { label: "Strike", value: "$420 call" },
            { label: "Premium", value: "$3.80" },
            { label: "Max Risk", value: "$380" },
            { label: "SPY at Expiry", value: "$432" },
        ],
        realWorldOutcome: "+$9.00 profit (+237%)",
        realWorldOutcomeDetail: "Controlled 100 shares of SPY for $380. Defined max loss from day one. No margin required, no surprise losses.",
        realWorldOutcomeColor: "#10b981",
        takeaways: [
            "Calls profit from rising stocks, puts from falling stocks",
            "Your max loss as a buyer = premium paid. No surprises.",
            "Leverage: control 100 shares for a fraction of the stock price",
            "Start with buying options before selling — understand the risk first",
        ],
    },

    default: {
        description: "Options are contracts that give you the right — but not the obligation — to buy or sell a stock at a specific price before a specific date.",
        bullets: [
            "Call options give the right to BUY at the strike price",
            "Put options give the right to SELL at the strike price",
            "Every option has an expiration date — time is a factor",
            "You pay a premium for this right — your maximum risk as a buyer",
        ],
        chartHeading: "$100 Call Option Value at Expiry",
        chartSubheading: "How a call option's value changes across stock prices at expiration",
        chartData: [
            { label: "$80", value: 0 },
            { label: "$90", value: 0 },
            { label: "$95", value: 0 },
            { label: "$100", value: 0 },
            { label: "$105", value: 5 },
            { label: "$110", value: 10 },
            { label: "$115", value: 15 },
            { label: "$120", value: 20 },
        ],
        chartXLabel: "Stock Price at Expiry",
        chartYLabel: "Option Value ($)",
        chartHighlightIdx: 5,
        chartFootnote: "At $110 (★) — $100 call worth $10 at expiry. Paid $3 premium → net profit $7.",
        realWorldHeading: "Real Trade: Options Basics",
        realWorldCompany: "SPY · Buying a Call",
        realWorldScenario: "Bought SPY $420 call for $3.80 with stock at $415. SPY rallied — call gained 237%. Max risk was always just the premium paid.",
        realWorldSetup: [
            { label: "SPY Price", value: "$415" },
            { label: "Strike", value: "$420 call" },
            { label: "Premium", value: "$3.80" },
            { label: "Max Risk", value: "$380" },
        ],
        realWorldOutcome: "+$9.00 profit (+237%)",
        realWorldOutcomeDetail: "Defined-risk leverage: control 100 shares for just the cost of the premium.",
        realWorldOutcomeColor: "#10b981",
        takeaways: [
            "Options provide leverage — control more stock with less capital",
            "They can be used for speculation, hedging, or income generation",
            "Risk management is essential — always know your max loss",
            "Start with defined-risk strategies before using undefined risk",
        ],
    },
};

export const CoreConceptVideo = ({
    title, subtitle, accent, conceptHeadline, conceptType = "default",
}: CoreConceptProps) => {
    const { durationInFrames } = useVideoConfig();
    const data = CONCEPT_DATA[conceptType] || CONCEPT_DATA["default"];

    const scenes: SceneDef[] = [
        {
            render: () => (
                <TitleScene
                    label="Core Concept"
                    title={title}
                    subtitle={data.description}
                    accent={accent}
                />
            ),
        },
        {
            render: () => (
                <BulletScene
                    heading="The Fundamentals"
                    bullets={data.bullets}
                    accent={accent}
                />
            ),
        },
        {
            durationInFrames: Math.floor(durationInFrames * 0.20),
            render: () => (
                <SvgLineChartScene
                    heading={data.chartHeading}
                    subheading={data.chartSubheading}
                    data={data.chartData}
                    accent={accent}
                    xLabel={data.chartXLabel}
                    yLabel={data.chartYLabel}
                    highlightIdx={data.chartHighlightIdx}
                    footnote={data.chartFootnote}
                />
            ),
        },
        {
            durationInFrames: Math.floor(durationInFrames * 0.22),
            render: () => (
                <SvgLineChartScene
                    heading={data.chartHeading}
                    subheading={data.chartSubheading}
                    data={data.chartData}
                    accent={accent}
                    xLabel={data.chartXLabel}
                    yLabel={data.chartYLabel}
                    highlightIdx={data.chartHighlightIdx}
                    footnote={data.chartFootnote}
                />
            ),
        },
        {
            durationInFrames: Math.floor(durationInFrames * 0.24),
            render: () => (
                <RealWorldExampleScene
                    heading={data.realWorldHeading}
                    company={data.realWorldCompany}
                    scenario={data.realWorldScenario}
                    setupItems={data.realWorldSetup}
                    outcome={data.realWorldOutcome}
                    outcomeDetail={data.realWorldOutcomeDetail}
                    outcomeColor={data.realWorldOutcomeColor}
                    accent={accent}
                />
            ),
        },
        {
            render: () => (
                <SummaryScene
                    heading="Key Takeaways"
                    takeaways={data.takeaways}
                    accent={accent}
                    closingLine="Understanding these core concepts is the foundation for everything else."
                />
            ),
        },
    ];

    return <SceneManager scenes={scenes} background="#0f1115" />;
};
