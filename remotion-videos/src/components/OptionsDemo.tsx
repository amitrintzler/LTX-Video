import { KineticShowcase } from "./KineticShowcase";
import type { DemoConfig } from "../data/demoScenes";
import { PayoffDiagramAnimator } from "./PayoffDiagramAnimator";

export const OptionsDemo = (props: DemoConfig) => {
  return (
    <KineticShowcase {...props}>
      <div className="absolute top-[20%] left-[25%] opacity-90 scale-125 z-0" style={{ filter: "drop-shadow(0 0 40px rgba(56, 189, 248, 0.4))" }}>
        <PayoffDiagramAnimator
          underlyingPrice={150}
          legs={[
            { type: "call", action: "buy", strike: 155, premium: 3.5 }
          ]}
          accentColor="#38bdf8"
        />
      </div>
    </KineticShowcase>
  );
};
