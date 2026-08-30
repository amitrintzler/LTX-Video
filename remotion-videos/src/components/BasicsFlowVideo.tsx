import React from "react";
import { AbsoluteFill, Sequence, Audio, staticFile } from "remotion";
import { CinematicIntro } from "./CinematicIntro";
import { KineticTypography } from "./KineticTypography";
import { PayoffDiagramAnimator } from "./PayoffDiagramAnimator";

export const BasicsFlowVideo: React.FC = () => {
    return (
        <AbsoluteFill style={{ backgroundColor: "#020617", color: "white", fontFamily: "Inter, sans-serif" }}>

            {/* Scene 1: Cinematic Intro (0 to 4 seconds) -> 0 to 120 frames */}
            <Sequence from={0} durationInFrames={120}>
                <CinematicIntro
                    title="Options Flow in 90 Seconds"
                    subtitle="Visualize Calls, Puts & Payoffs"
                    posterUrl="/assets/lessons/basics-flow.png" // using the existing poster
                />
            </Sequence>

            {/* Scene 2: Concept - What is a Call? (4 to 8 seconds) -> 120 to 240 */}
            <Sequence from={120} durationInFrames={120}>
                <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
                    <KineticTypography text="A CALL is the right to BUY" delay={15} fontSize={80} color="#4ade80" />
                </AbsoluteFill>
            </Sequence>

            {/* Scene 3: Payoff Diagram for Call (8 to 14 seconds) -> 240 to 420 */}
            <Sequence from={240} durationInFrames={180}>
                <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
                    <h2 style={{ position: "absolute", top: "10%", fontSize: 48, color: "#cbd5e1" }}>
                        Call Option Payoff
                    </h2>
                    <PayoffDiagramAnimator type="call" strikePrice={150} currentPrice={155} premium={2} />
                </AbsoluteFill>
            </Sequence>

            {/* Scene 4: Concept - What is a Put? (14 to 18 seconds) -> 420 to 540 */}
            <Sequence from={420} durationInFrames={120}>
                <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
                    <KineticTypography text="A PUT is the right to SELL" delay={15} fontSize={80} color="#f87171" />
                </AbsoluteFill>
            </Sequence>

            {/* Scene 5: Payoff Diagram for Put (18 to 24 seconds) -> 540 to 720 */}
            <Sequence from={540} durationInFrames={180}>
                <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
                    <h2 style={{ position: "absolute", top: "10%", fontSize: 48, color: "#cbd5e1" }}>
                        Put Option Payoff
                    </h2>
                    <PayoffDiagramAnimator type="put" strikePrice={150} currentPrice={145} premium={2} />
                </AbsoluteFill>
            </Sequence>

            {/* Scene 6: Outro CTA (24 to 28 seconds) -> 720 to 840 */}
            <Sequence from={720} durationInFrames={120}>
                <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", background: "linear-gradient(to top, #081226, #020617)" }}>
                    <KineticTypography text="Now it's your turn." delay={0} fontSize={64} color="#e2e8f0" />
                    <KineticTypography text="Launch the Payoff Sandbox!" delay={30} fontSize={80} color="#38bdf8" style={{ marginTop: 120 }} />
                </AbsoluteFill>
            </Sequence>

            {/* Optional: Add background music or VO */}
            {/* <Audio src={staticFile("audio/background-track.mp3")} volume={0.3} /> */}

        </AbsoluteFill>
    );
};
