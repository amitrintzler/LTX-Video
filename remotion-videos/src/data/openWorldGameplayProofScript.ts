export type OpenWorldGameplayProofCue = {
  fromSec: number;
  toSec: number;
  text: string;
};

export type OpenWorldGameplayProofCallout = {
  id: string;
  title: string;
  detail: string;
  fromSec: number;
  toSec: number;
  accent: string;
};

export const OPEN_WORLD_GAMEPLAY_PROOF_TITLE = "Open-World Options City: How To Play in 90 Seconds";

export const OPEN_WORLD_GAMEPLAY_PROOF_CAPTIONS: OpenWorldGameplayProofCue[] = [
  {
    fromSec: 0,
    toSec: 10,
    text: "Spawn in city view. Focus the Mission Guide and read the active objective.",
  },
  {
    fromSec: 10,
    toSec: 24,
    text: "Use Go To Objective, then Accept Briefing to lock your directional thesis.",
  },
  {
    fromSec: 24,
    toSec: 42,
    text: "Execute one defined-risk options action from the action controls.",
  },
  {
    fromSec: 42,
    toSec: 60,
    text: "Watch immediate impact: fill quality, slippage, market shift, and agenda progress.",
  },
  {
    fromSec: 60,
    toSec: 78,
    text: "Complete debrief and mission follow-up to convert action into learning progress.",
  },
  {
    fromSec: 78,
    toSec: 90,
    text: "Repeat daily loop: objective, execution, review. Educational content only.",
  },
];

export const OPEN_WORLD_GAMEPLAY_PROOF_CALLOUTS: OpenWorldGameplayProofCallout[] = [
  {
    id: "objective",
    title: "Step 1",
    detail: "Read objective: What / Where / Why / Reward",
    fromSec: 2,
    toSec: 12,
    accent: "#61d4ff",
  },
  {
    id: "briefing",
    title: "Step 2",
    detail: "Accept Briefing in Mission Guide",
    fromSec: 12,
    toSec: 24,
    accent: "#8ef0c5",
  },
  {
    id: "first-action",
    title: "Step 3",
    detail: "Run first options action (defined risk)",
    fromSec: 24,
    toSec: 42,
    accent: "#ffc987",
  },
  {
    id: "reaction",
    title: "Step 4",
    detail: "Observe market + agenda reaction",
    fromSec: 42,
    toSec: 60,
    accent: "#9db2ff",
  },
  {
    id: "debrief",
    title: "Step 5",
    detail: "Debrief and lock next mission",
    fromSec: 60,
    toSec: 78,
    accent: "#ffb6c6",
  },
  {
    id: "cta",
    title: "Next",
    detail: "Play campaign and complete one full loop",
    fromSec: 78,
    toSec: 90,
    accent: "#ffd98f",
  },
];
