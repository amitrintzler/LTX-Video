export type OpenWorldGameSimSceneId =
  | "city_establish"
  | "arrival_briefing"
  | "first_ticket_lab"
  | "volatility_adjustment"
  | "debrief_agenda"
  | "cta_close";

export type OpenWorldGameSimScene = {
  id: OpenWorldGameSimSceneId;
  title: string;
  subtitle: string;
  startSec: number;
  endSec: number;
  accent: string;
  bullets: string[];
};

export type OpenWorldGameSimCaptionCue = {
  fromSec: number;
  toSec: number;
  text: string;
};

export const OPEN_WORLD_GAME_SIM_90_TITLE = "Open-World Options City: 90s Game Simulation";

export const OPEN_WORLD_GAME_SIM_SCENES: OpenWorldGameSimScene[] = [
  {
    id: "city_establish",
    title: "Scene A: City Establish",
    subtitle: "Read market regime and mission focus at a glance.",
    startSec: 0,
    endSec: 12,
    accent: "#47d8ff",
    bullets: [
      "Regime beacon shifts city tone from calm to panic.",
      "Objective rail highlights next actionable task.",
      "Billboards mirror live market context and educational media.",
    ],
  },
  {
    id: "arrival_briefing",
    title: "Scene B: Arrival Briefing",
    subtitle: "What / Where / Why / Reward is always visible.",
    startSec: 12,
    endSec: 30,
    accent: "#8bf2c4",
    bullets: [
      "What: lock directional thesis before ticket construction.",
      "Where: Regime Beacon in Old Town.",
      "Reward: credits + campaign progression unlock.",
    ],
  },
  {
    id: "first_ticket_lab",
    title: "Scene C: First Ticket Lab",
    subtitle: "Build a defined-risk setup with strike + expiry intent.",
    startSec: 30,
    endSec: 52,
    accent: "#70c0ff",
    bullets: [
      "Choose structure first, then strike ladder ring.",
      "Select expiry lane and confirm risk budget fit.",
      "Execute with routing choice to control slippage.",
    ],
  },
  {
    id: "volatility_adjustment",
    title: "Scene D: Volatility Event + Adjustment",
    subtitle: "React to IV expansion and protect downside quickly.",
    startSec: 52,
    endSec: 70,
    accent: "#ffb36d",
    bullets: [
      "Volatility dome spikes and catalyst feed updates.",
      "Adjustment clinic proposes roll, hedge, or close.",
      "Outcome updates drawdown and expectancy in real time.",
    ],
  },
  {
    id: "debrief_agenda",
    title: "Scene E: Debrief + Agenda Progress",
    subtitle: "Cause/effect feedback turns actions into mastery.",
    startSec: 70,
    endSec: 85,
    accent: "#9f8cff",
    bullets: [
      "Debrief card links P/L, IV shift, and Greeks behavior.",
      "Agenda tracks concept completion and daily objective.",
      "Next mission path remains single-focus and explicit.",
    ],
  },
  {
    id: "cta_close",
    title: "Scene F: CTA + Compliance",
    subtitle: "Campaign continues with daily city pulse refresh.",
    startSec: 85,
    endSec: 90,
    accent: "#ffd68b",
    bullets: [
      "Start campaign and complete first meaningful options action.",
      "Educational content only. Not investment advice.",
    ],
  },
];

export const OPEN_WORLD_GAME_SIM_CAPTIONS: OpenWorldGameSimCaptionCue[] = [
  {
    fromSec: 0,
    toSec: 12,
    text: "Options City boots with a visible objective and regime-aware world state.",
  },
  {
    fromSec: 12,
    toSec: 20,
    text: "Arrival Briefing defines what to do, where to go, and why the step matters.",
  },
  {
    fromSec: 20,
    toSec: 30,
    text: "Reward clarity keeps momentum into the first hands-on trade decision.",
  },
  {
    fromSec: 30,
    toSec: 42,
    text: "First Ticket Lab maps thesis to structure, strike, and expiry in one flow.",
  },
  {
    fromSec: 42,
    toSec: 52,
    text: "Execution quality is visible through slippage and fill-probability feedback.",
  },
  {
    fromSec: 52,
    toSec: 61,
    text: "Volatility shock hits; adjustment choices branch to roll, hedge, or close.",
  },
  {
    fromSec: 61,
    toSec: 70,
    text: "Risk controls cap drawdown and keep the trade within plan.",
  },
  {
    fromSec: 70,
    toSec: 80,
    text: "Debrief explains P and L, IV reaction, and Greeks movement in plain language.",
  },
  {
    fromSec: 80,
    toSec: 85,
    text: "Agenda progress converts this run into long-term options mastery.",
  },
  {
    fromSec: 85,
    toSec: 90,
    text: "Start your next campaign mission. Educational content only. Not investment advice.",
  },
];

