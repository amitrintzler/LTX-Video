import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig } from "remotion";
import React from "react";

export const KineticTypography: React.FC<{ text: string; delay?: number; fontSize?: number; color?: string; style?: React.CSSProperties }> = ({ text, delay = 0, fontSize = 64, color = "#FFFFFF", style }) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();

    const words = text.split(" ");

    return (
        <AbsoluteFill style={{ ...style, display: "flex", flexDirection: "row", flexWrap: "wrap", justifyContent: "center", alignItems: "center", gap: "10px" }}>
            {words.map((word, index) => {
                const wordDelay = delay + index * 5;
                const animation = spring({
                    frame: frame - wordDelay,
                    fps,
                    config: { damping: 12, stiffness: 200 },
                });

                const yOffset = (1 - animation) * 50;
                const opacity = Math.min(Math.max((frame - wordDelay) / 5, 0), 1);

                return (
                    <span
                        key={`${word}-${index}`}
                        style={{
                            display: "inline-block",
                            transform: `translateY(${yOffset}px)`,
                            opacity: opacity,
                            fontSize: `${fontSize}px`,
                            fontWeight: 800,
                            color: color,
                            textShadow: "0px 4px 12px rgba(0,0,0,0.5)",
                            fontFamily: "Inter, sans-serif",
                        }}
                    >
                        {word}
                    </span>
                );
            })}
        </AbsoluteFill>
    );
};
