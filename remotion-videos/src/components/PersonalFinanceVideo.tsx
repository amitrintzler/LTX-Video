import { useVideoConfig } from "remotion";
import {
    SceneManager, TitleScene, BulletScene, SummaryScene,
    SvgLineChartScene, RealWorldExampleScene, type SceneDef,
} from "./SceneSystem";
import React from "react";
import { TEMPLATE_STYLES } from "../lib/templateStyles";

const S = TEMPLATE_STYLES["money-basics"];

export type PersonalFinanceProps = {
    title: string;
    subtitle: string;
    accent: string;
    metric: string;
    value: string;
};

type PFData = {
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

const PF_DATA: Record<string, PFData> = {
    "Savings Rate": {
        description: "A budget is a spending plan, not a restriction. Knowing where every dollar goes is the foundation of building wealth, and the savings rate is the most important number.",
        bullets: [
            "Savings rate = (Income minus Expenses) ÷ Income × 100",
            "A 20%+ savings rate accelerates wealth building dramatically",
            "Track every dollar for 30 days before optimizing",
            "Automate savings first, pay yourself before bills",
        ],
        chartHeading: "Wealth Accumulation at 20% Savings Rate",
        chartSubheading: "Account value over 8 years at 20% savings rate + 7% annual return",
        chartData: [
            { label: "Yr1", value: 6000 },
            { label: "Yr2", value: 12360 },
            { label: "Yr3", value: 19091 },
            { label: "Yr4", value: 26215 },
            { label: "Yr5", value: 33761 },
            { label: "Yr6", value: 41754 },
            { label: "Yr7", value: 50218 },
            { label: "Yr8", value: 59174 },
        ],
        chartXLabel: "Year",
        chartYLabel: "Savings ($)",
        chartHighlightIdx: 7,
        chartFootnote: "Year 8 (★): $59k saved at 20% savings rate. Same income at 5% rate = only $14k. Savings rate is the biggest lever.",
        realWorldHeading: "Real Example: Subscription Audit",
        realWorldCompany: "Monthly Budget Optimization",
        realWorldScenario: "Reduced subscriptions from $340/mo to $85/mo (-$255). Invested the difference every month for 5 years at 7% return, turning waste into $18,540.",
        realWorldSetup: [
            { label: "Monthly Income", value: "$5,500" },
            { label: "Before Budget", value: "$340/mo waste" },
            { label: "After Budget", value: "$85/mo" },
            { label: "Monthly Saved", value: "+$255" },
            { label: "Savings Rate", value: "22%" },
        ],
        realWorldOutcome: "+$18,540 in 5 years",
        realWorldOutcomeDetail: "Cutting $255/mo in waste and investing it at 7% compounded into $18,540 over 5 years, with zero lifestyle sacrifice.",
        realWorldOutcomeColor: "#10b981",
        takeaways: [
            "Track spending for 30 days, you'll be surprised where it goes",
            "Automate savings, willpower runs out but systems don't",
            "Every 1% increase in savings rate = years off your working life",
            "Savings rate matters more than investment returns at first",
        ],
    },

    "Cash Flow": {
        description: "Cash flow is the difference between money coming in and money going out. Positive cash flow = financial freedom. Negative cash flow = financial stress, regardless of income.",
        bullets: [
            "Cash flow = all income minus all expenses (monthly)",
            "Assets generate cash flow; liabilities consume it",
            "High income doesn't equal positive cash flow, spending decides",
            "Track cash flow monthly, it changes faster than you think",
        ],
        chartHeading: "Cash Flow Improvement Over 8 Months",
        chartSubheading: "Monthly net cash flow as recurring expenses are eliminated",
        chartData: [
            { label: "Jan", value: -320 },
            { label: "Feb", value: -180 },
            { label: "Mar", value: 85 },
            { label: "Apr", value: 240 },
            { label: "May", value: 410 },
            { label: "Jun", value: 580 },
            { label: "Jul", value: 720 },
            { label: "Aug", value: 850 },
        ],
        chartXLabel: "Month",
        chartYLabel: "Monthly Cash Flow ($)",
        chartHighlightIdx: 7,
        chartFootnote: "August (★): $850 positive cash flow after 8 month optimization. Started at -$320/mo. Compounded over a year = +$10,200 available to invest.",
        realWorldHeading: "Real Example: 3 Step Cash Flow Fix",
        realWorldCompany: "Monthly Expense Optimization",
        realWorldScenario: "Refinanced car loan (-$180/mo), cancelled unused gym (-$45/mo), and meal prepped to cut food spend (-$280/mo). Total swing: +$505/mo in recovered cash flow.",
        realWorldSetup: [
            { label: "Starting CF", value: "-$320/mo" },
            { label: "Car Refi", value: "+$180/mo" },
            { label: "Subscriptions", value: "+$45/mo" },
            { label: "Food", value: "+$280/mo" },
            { label: "Ending CF", value: "+$850/mo" },
        ],
        realWorldOutcome: "+$1,170/mo swing",
        realWorldOutcomeDetail: "Three targeted cuts produced $1,170/mo in recovered cash flow, without a raise, new job, or side hustle.",
        realWorldOutcomeColor: "#10b981",
        takeaways: [
            "Positive cash flow is the foundation, get there before investing",
            "Every recurring expense is a cash flow drain, audit quarterly",
            "A $200/mo expense cut = $2,400/yr = $36k over 15 years invested",
            "Cash flow, not income, determines financial health",
        ],
    },

    "Emergency Fund": {
        description: "An emergency fund is your financial shock absorber. 3 to 6 months of expenses in a high yield savings account prevents one bad event from destroying years of progress.",
        bullets: [
            "Target 3 to 6 months of essential expenses (not income)",
            "Keep it in a high yield savings account, earn 4 to 5% while it sits",
            "Only for true emergencies: job loss, medical, car or home repair",
            "Build it before investing, market crashes require cash reserves",
        ],
        chartHeading: "Emergency Fund Growth: $1,000/mo",
        chartSubheading: "High yield savings account balance over 8 months at $1,000/mo contributions",
        chartData: [
            { label: "Mo1", value: 1000 },
            { label: "Mo2", value: 2000 },
            { label: "Mo3", value: 3000 },
            { label: "Mo4", value: 4000 },
            { label: "Mo5", value: 5000 },
            { label: "Mo6", value: 6000 },
            { label: "Mo7", value: 7000 },
            { label: "Mo8", value: 8000 },
        ],
        chartXLabel: "Month",
        chartYLabel: "Emergency Fund ($)",
        chartHighlightIdx: 5,
        chartFootnote: "Month 6 (★): 6 month emergency fund fully funded at $8,000. At 5% HYSA rate, earns $400/yr just sitting there.",
        realWorldHeading: "Real Example: Car Emergency Test",
        realWorldCompany: "HYSA Emergency Fund in Action",
        realWorldScenario: "Saved $1,000/mo in HYSA at 5%. After 6 months: $6,072 with interest. Used $2,800 for unexpected car repair, no debt taken on, fund rebuilt in 3 months.",
        realWorldSetup: [
            { label: "Monthly Savings", value: "$1,000" },
            { label: "HYSA Rate", value: "5.0%" },
            { label: "Target", value: "6 months" },
            { label: "Car Emergency", value: "$2,800" },
            { label: "Rebuilt In", value: "3 months" },
        ],
        realWorldOutcome: "Zero debt taken",
        realWorldOutcomeDetail: "A $2,800 car repair that would have gone on a credit card at 22% APR was paid in cash, and the fund was rebuilt in just 3 months.",
        realWorldOutcomeColor: "#10b981",
        takeaways: [
            "Emergency fund is financial insurance, it has a real cost without it",
            "HYSA earns 4 to 5%, your emergency fund should pay you",
            "3 months minimum; 6 months if self-employed or variable income",
            "Never invest money you might need within 12 months",
        ],
    },
};

const DEFAULT_DATA = PF_DATA["Savings Rate"];

export const PersonalFinanceVideo: React.FC<PersonalFinanceProps> = (props) => {
    const { durationInFrames } = useVideoConfig();
    const { accent = S.accent, metric } = props;
    const data = PF_DATA[metric] || DEFAULT_DATA;

    const scenes: SceneDef[] = [
        {
            render: () => (
                <TitleScene
                    label="Personal Finance"
                    title={props.title}
                    subtitle={data.description}
                    accent={accent}
                />
            ),
        },
        {
            render: () => (
                <BulletScene
                    heading="How It Works"
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
                    closingLine="Small, consistent financial habits compound into life-changing results."
                />
            ),
        },
    ];

    return <SceneManager scenes={scenes} theme={S} />;
};
