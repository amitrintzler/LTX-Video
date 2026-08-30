import { sfxFiles } from "./sfxCues";

export type SfxCue = {
  atFrame: number;
  file: string;
  volume?: number;
};

export type DemoScene = {
  id: string;
  clipSrc?: string;
  mock?: "idea" | "pipeline" | "cards";
  mockCards?: string[];
  title: string;
  lines: string[];
  badges: string[];
  durationSeconds: number;
  focus?: "left" | "right";
  accent?: "cyan" | "purple" | "orange";
  tag?: string;
  hud?: "score" | "combo" | "correct" | "levelup";
  sfx?: SfxCue[];
};

export type DemoIntro = {
  eyebrow: string;
  title: string;
  subtitle: string;
};

export type DemoOutro = {
  eyebrow: string;
  title: string;
  subtitle: string;
  ctas: string[];
};

export type DemoPalette = {
  base: string;
  glowA: string;
  glowB: string;
  accent: string;
  accentAlt: string;
};

export type DemoConfig = {
  id: "OptionsEducatorDemo" | "FrameworkDemo";
  scenes: DemoScene[];
  intro: DemoIntro;
  outro: DemoOutro;
  audioSrc: string;
  bpm: number;
  palette: DemoPalette;
  introSeconds: number;
  outroSeconds: number;
};

const optionsScenes: DemoScene[] = [
  {
    id: "options-pattern",
    clipSrc: "/assets/videos/clips/options/options-01-pattern.mp4",
    title: "Options chain pattern drill",
    lines: ["Spot strike patterns fast.", "Chain logic in 60 seconds."],
    badges: ["Strike logic", "Pattern XP"],
    durationSeconds: 6,
    focus: "right",
    accent: "cyan",
    hud: "combo",
    tag: "Options Chain",
    sfx: [
      { atFrame: 8, file: sfxFiles.click, volume: 0.55 },
      { atFrame: 30, file: sfxFiles.pop, volume: 0.6 },
    ],
  },
  {
    id: "options-memory",
    clipSrc: "/assets/videos/clips/options/options-02-memory.mp4",
    title: "Bid/ask memory sprint",
    lines: ["Match bid, ask, OI, spread.", "Speed drills make it stick."],
    badges: ["Term lock", "Fast flips"],
    durationSeconds: 6,
    focus: "right",
    accent: "cyan",
    hud: "combo",
    tag: "Terms",
    sfx: [
      { atFrame: 8, file: sfxFiles.click, volume: 0.5 },
      { atFrame: 20, file: sfxFiles.click, volume: 0.45 },
      { atFrame: 34, file: sfxFiles.pop, volume: 0.55 },
    ],
  },
  {
    id: "options-decision",
    clipSrc: "/assets/videos/clips/options/options-03-decision.mp4",
    title: "Short selling decisions",
    lines: ["Choose the risk path.", "Learn downside discipline."],
    badges: ["Decision tree", "Points"],
    durationSeconds: 6,
    focus: "left",
    accent: "cyan",
    hud: "correct",
    tag: "Short Selling",
    sfx: [
      { atFrame: 10, file: sfxFiles.click, volume: 0.55 },
      { atFrame: 36, file: sfxFiles.levelup, volume: 0.6 },
    ],
  },
  {
    id: "options-logic",
    clipSrc: "/assets/videos/clips/options/options-04-logic.mp4",
    title: "Rho + rates logic",
    lines: ["Solve the rate shock puzzle.", "Quick math, instant feedback."],
    badges: ["Rho logic", "Clue hints"],
    durationSeconds: 6,
    focus: "left",
    accent: "cyan",
    hud: "correct",
    tag: "Rates",
    sfx: [
      { atFrame: 12, file: sfxFiles.click, volume: 0.5 },
      { atFrame: 32, file: sfxFiles.pop, volume: 0.6 },
    ],
  },
  {
    id: "options-storybook",
    clipSrc: "/assets/videos/clips/options/options-05-storybook.mp4",
    title: "Storybook: stock basics",
    lines: ["Flip the story pages.", "Narratives make concepts stick."],
    badges: ["Story mode", "Page flips"],
    durationSeconds: 5,
    focus: "left",
    accent: "cyan",
    tag: "Storybook",
    sfx: [
      { atFrame: 10, file: sfxFiles.whoosh, volume: 0.4 },
      { atFrame: 36, file: sfxFiles.pop, volume: 0.5 },
    ],
  },
  {
    id: "options-learn",
    clipSrc: "/assets/videos/clips/options/options-06-learn.mp4",
    title: "Playbook lessons, real steps",
    lines: ["Exit playbooks with action steps.", "Learn the why + the how."],
    badges: ["Playbooks", "Step-by-step"],
    durationSeconds: 7,
    focus: "right",
    accent: "cyan",
    tag: "Learn",
    sfx: [
      { atFrame: 12, file: sfxFiles.click, volume: 0.45 },
      { atFrame: 44, file: sfxFiles.pop, volume: 0.5 },
    ],
  },
  {
    id: "options-examples",
    clipSrc: "/assets/videos/clips/options/options-07-examples.mp4",
    title: "Real earnings case studies",
    lines: ["Meta-style guidance shocks.", "Lessons tied to outcomes."],
    badges: ["Case studies", "Outcomes"],
    durationSeconds: 7,
    focus: "right",
    accent: "cyan",
    tag: "Examples",
    sfx: [
      { atFrame: 12, file: sfxFiles.click, volume: 0.45 },
      { atFrame: 40, file: sfxFiles.pop, volume: 0.5 },
    ],
  },
  {
    id: "options-graphs",
    clipSrc: "/assets/videos/clips/options/options-08-graphs.mp4",
    title: "Greeks visualized",
    lines: ["Delta scaling curves show impact.", "See the slope shift."],
    badges: ["Graphs", "Greeks"],
    durationSeconds: 6,
    focus: "left",
    accent: "cyan",
    tag: "Graphs",
    sfx: [
      { atFrame: 10, file: sfxFiles.whoosh, volume: 0.4 },
      { atFrame: 40, file: sfxFiles.pop, volume: 0.5 },
    ],
  },
  {
    id: "options-quiz",
    clipSrc: "/assets/videos/clips/options/options-09-quiz.mp4",
    title: "Quiz checks + feedback",
    lines: ["Answer and lock it in.", "Immediate corrections."],
    badges: ["Quiz", "Fast checks"],
    durationSeconds: 6,
    focus: "right",
    accent: "cyan",
    hud: "correct",
    tag: "Quiz",
    sfx: [
      { atFrame: 8, file: sfxFiles.click, volume: 0.5 },
      { atFrame: 32, file: sfxFiles.pop, volume: 0.6 },
    ],
  },
  {
    id: "options-sim",
    clipSrc: "/assets/videos/clips/options/options-10-sim.mp4",
    title: "Payoff Lab: drag to learn",
    lines: ["Drag strikes and watch P&L move.", "Instant what-if curves."],
    badges: ["Live payoff", "What-if"],
    durationSeconds: 8,
    focus: "right",
    accent: "cyan",
    hud: "score",
    tag: "Payoff Lab",
    sfx: [
      { atFrame: 6, file: sfxFiles.whoosh, volume: 0.4 },
      { atFrame: 40, file: sfxFiles.hit, volume: 0.55 },
    ],
  },
  {
    id: "options-assistant",
    clipSrc: "/assets/videos/clips/options/options-11-assistant.mp4",
    title: "Ask + cite knowledge",
    lines: ["Knowledge base answers fast.", "Sources included."],
    badges: ["AI copilot", "Cited"],
    durationSeconds: 6,
    focus: "right",
    accent: "cyan",
    tag: "Assistant",
    sfx: [
      { atFrame: 12, file: sfxFiles.click, volume: 0.45 },
      { atFrame: 36, file: sfxFiles.pop, volume: 0.5 },
    ],
  },
];

const frameworkScenes: DemoScene[] = [
  {
    id: "framework-blueprint",
    clipSrc: "/assets/videos/clips/framework/framework-01-blueprint.mp4",
    title: "Blueprint engine",
    lines: ["Idea → audience → outcome in minutes.", "Auto-build your learning map."],
    badges: ["Blueprints", "Auto-map"],
    durationSeconds: 10,
    focus: "left",
    accent: "purple",
    tag: "Framework",
    sfx: [
      { atFrame: 8, file: sfxFiles.whoosh, volume: 0.4 },
      { atFrame: 44, file: sfxFiles.pop, volume: 0.5 },
    ],
  },
  {
    id: "framework-physics-story",
    clipSrc: "/assets/videos/clips/framework/framework-02-physics-story.mp4",
    title: "Physics in story mode",
    lines: ["Gravity becomes a narrative + glossary.", "Any domain can plug in."],
    badges: ["Story mode", "Glossary"],
    durationSeconds: 10,
    focus: "right",
    accent: "orange",
    tag: "Physics",
    sfx: [
      { atFrame: 12, file: sfxFiles.click, volume: 0.4 },
      { atFrame: 52, file: sfxFiles.pop, volume: 0.5 },
    ],
  },
  {
    id: "framework-math-game",
    clipSrc: "/assets/videos/clips/framework/framework-03-math-game.mp4",
    title: "Math: Algebra Sprint",
    lines: ["Pattern streaks turn into algebra speed rounds.", "Same engine, new domain."],
    badges: ["Math sprint", "Game layer"],
    durationSeconds: 10,
    focus: "left",
    accent: "purple",
    hud: "combo",
    tag: "Math",
    sfx: [
      { atFrame: 10, file: sfxFiles.click, volume: 0.5 },
      { atFrame: 38, file: sfxFiles.pop, volume: 0.55 },
    ],
  },
  {
    id: "framework-sim",
    clipSrc: "/assets/videos/clips/framework/framework-04-sim.mp4",
    title: "Physics: Motion Lab",
    lines: ["Adjust forces, angles, and time.", "See outcomes instantly."],
    badges: ["Motion Lab", "What-if"],
    durationSeconds: 10,
    focus: "right",
    accent: "orange",
    hud: "score",
    tag: "Physics Lab",
    sfx: [
      { atFrame: 8, file: sfxFiles.whoosh, volume: 0.4 },
      { atFrame: 40, file: sfxFiles.hit, volume: 0.5 },
    ],
  },
  {
    id: "framework-pipeline",
    mock: "cards",
    mockCards: ["Sim Challenge", "Strategy Builder", "Risk Ladder", "Scenario Sprint"],
    title: "Sim-first templates",
    lines: ["Launch new games fast with reusable templates.", "Score, combo, and mastery baked in."],
    badges: ["Template engine", "Sim-first"],
    durationSeconds: 10,
    focus: "left",
    accent: "purple",
    hud: "levelup",
    sfx: [
      { atFrame: 12, file: sfxFiles.whoosh, volume: 0.4 },
      { atFrame: 48, file: sfxFiles.levelup, volume: 0.6 },
    ],
  },
  {
    id: "framework-locales",
    clipSrc: "/assets/videos/clips/framework/framework-06-locales.mp4",
    title: "Global rollout built in",
    lines: ["Locale switching + RTL ready.", "Translation-in-progress states show."],
    badges: ["Global", "i18n"],
    durationSeconds: 9,
    focus: "right",
    accent: "orange",
    tag: "Worldwide",
    sfx: [
      { atFrame: 12, file: sfxFiles.click, volume: 0.45 },
      { atFrame: 36, file: sfxFiles.whoosh, volume: 0.4 },
    ],
  },
  {
    id: "framework-deploy",
    clipSrc: "/assets/videos/clips/framework/framework-07-deploy.mp4",
    title: "Ship & iterate fast",
    lines: ["Publish in minutes.", "Netlify previews keep teams aligned."],
    badges: ["Deploy", "Preview"],
    durationSeconds: 11,
    focus: "left",
    accent: "purple",
    tag: "Launch",
    sfx: [
      { atFrame: 10, file: sfxFiles.hit, volume: 0.5 },
      { atFrame: 44, file: sfxFiles.pop, volume: 0.55 },
    ],
  },
];

export const optionsDemoConfig: DemoConfig = {
  id: "OptionsEducatorDemo",
  scenes: optionsScenes,
  intro: {
    eyebrow: "OptionsEducator",
    title: "Play the Market. Master Options.",
    subtitle: "Games + simulators + AI coaching",
  },
  outro: {
    eyebrow: "Ready to level up?",
    title: "Start the Journey",
    subtitle: "Or jump straight into the simulator.",
    ctas: ["Start Journey", "Launch Simulator"],
  },
  audioSrc: "/assets/videos/audio-options.mp3",
  bpm: 150,
  palette: {
    base: "#050914",
    glowA: "rgba(0, 255, 194, 0.2)",
    glowB: "rgba(111, 124, 255, 0.22)",
    accent: "#7ae4ff",
    accentAlt: "#6f7cff",
  },
  introSeconds: 3,
  outroSeconds: 7,
};

export const frameworkDemoConfig: DemoConfig = {
  id: "FrameworkDemo",
  scenes: frameworkScenes,
  intro: {
    eyebrow: "The Framework",
    title: "Any Idea → Simplified Learning Engine",
    subtitle: "Physics + Math + any domain you can name",
  },
  outro: {
    eyebrow: "Build your own domain",
    title: "Turn Any Topic Into A Platform",
    subtitle: "Options today. Physics and Math tomorrow.",
    ctas: ["Design a Journey", "Launch a Demo"],
  },
  audioSrc: "/assets/videos/audio-framework.mp3",
  bpm: 144,
  palette: {
    base: "#0a0617",
    glowA: "rgba(167, 110, 255, 0.22)",
    glowB: "rgba(255, 162, 0, 0.22)",
    accent: "#a76eff",
    accentAlt: "#ff9f1a",
  },
  introSeconds: 3,
  outroSeconds: 7,
};

export const getDemoDurationFrames = (config: DemoConfig, fps: number) => {
  const scenesSeconds = config.scenes.reduce((sum, scene) => sum + scene.durationSeconds, 0);
  const totalSeconds = config.introSeconds + config.outroSeconds + scenesSeconds;
  return Math.round(totalSeconds * fps);
};
