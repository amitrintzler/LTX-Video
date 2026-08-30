import { KineticShowcase } from "./KineticShowcase";
import type { DemoConfig } from "../data/demoScenes";

export const FrameworkDemo = (props: DemoConfig) => {
  return <KineticShowcase {...props} />;
};
