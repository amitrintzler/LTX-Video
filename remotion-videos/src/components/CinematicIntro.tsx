import { AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { KineticTypography } from "./KineticTypography";
import React from "react";

export const CinematicIntro = ({
    title,
    subtitle,
    subjectLabel,
    posterUrl,
    accent,
    glow,
}: {
    title: string;
    subtitle: string;
    subjectLabel?: string;
    posterUrl: string;
    accent?: string;
    glow?: string;
}) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();

    const zoom = interpolate(frame, [0, 150], [1.1, 1.0], { extrapolateRight: "clamp" });
    const overlayOpacity = interpolate(frame, [0, 30], [0, 0.6], { extrapolateRight: "clamp" });

    const resolvedPoster = posterUrl ? staticFile(posterUrl.replace(/^\//, "")) : null;

    return (
        <AbsoluteFill style={{ backgroundColor: "#000" }}>
            {resolvedPoster && (
                <AbsoluteFill style={{ transform: `scale(${zoom})` }}>
                    <Img
                        src={resolvedPoster}
                        style={{
                            width: "100%",
                            height: "100%",
                            objectFit: "cover",
                        }}
                    />
                </AbsoluteFill>
            )}

            {/* Vignette & Gradient Overlay */}
            <AbsoluteFill
                style={{
                    background: `linear-gradient(to top, rgba(0,0,0,${overlayOpacity + 0.3}) 0%, rgba(0,0,0,${overlayOpacity}) 50%, rgba(0,0,0,0) 100%)`,
                }}
            />

            {/* Title block */}
            <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
                {/* Optional Accent Subject Label */}
                {subjectLabel && (
                    <div
                        className="text-2xl font-bold uppercase tracking-[0.2em] mb-4"
                        style={{ color: accent || "#3b82f6" }}
                    >
                        {subjectLabel}
                    </div>
                )}

                <h1 className="text-7xl font-black text-transparent bg-clip-text bg-gradient-to-r from-white to-white/70 mb-6 drop-shadow-2xl">
                    {title}
                </h1>
                <KineticTypography text={subtitle} delay={30} fontSize={48} color="#e2e8f0" style={{ top: "60%", position: "absolute" }} />
            </AbsoluteFill>
        </AbsoluteFill>
    );
};
