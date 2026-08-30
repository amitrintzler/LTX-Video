import { spring, useCurrentFrame, useVideoConfig } from "remotion";

export const GreekDial = ({
    name,
    startValue,
    endValue,
    color,
    size = 300,
}: {
    name: string;
    startValue: number;
    endValue: number;
    color: string;
    size?: number;
}) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();

    const progress = spring({
        frame,
        fps,
        config: {
            damping: 12,
            stiffness: 90,
            mass: 0.5,
        },
    });

    const currentValue = startValue + (endValue - startValue) * progress;

    // Map value to an angle. Let's assume most Greeks we visualize go from 0 to 1 or -1 to 1.
    // We'll normalize to a half-circle (-90deg to +90deg)
    const isSymmetric = name === "Delta" || name === "Gamma";
    const displayMin = isSymmetric ? -1 : 0;
    const displayMax = 1;

    const range = displayMax - displayMin;
    const normalizedValue = Math.max(displayMin, Math.min(displayMax, currentValue));
    const angle = -90 + ((normalizedValue - displayMin) / range) * 180;

    const strokeWidth = size * 0.08;
    const radius = (size - strokeWidth) / 2;
    const cx = size / 2;
    const cy = size / 2;

    // SVG Arc calculation for the background track (half circle)
    const trackPath = `
    M ${strokeWidth / 2} ${cy}
    A ${radius} ${radius} 0 0 1 ${size - strokeWidth / 2} ${cy}
  `;

    return (
        <div style={{ width: size, height: size / 2 + 40, position: "relative" }}>
            <svg width={size} height={size / 2 + strokeWidth} viewBox={`0 0 ${size} ${size / 2 + strokeWidth}`}>
                {/* Track Background */}
                <path
                    d={trackPath}
                    fill="none"
                    stroke="rgba(255,255,255,0.1)"
                    strokeWidth={strokeWidth}
                    strokeLinecap="round"
                />

                {/* Filled Track Segment (optional, could animate arc length instead of needle) */}
            </svg>

            {/* Needle */}
            <div
                style={{
                    position: "absolute",
                    bottom: 0,
                    left: size / 2 - 4,
                    width: 8,
                    height: radius + 20,
                    backgroundColor: color,
                    borderRadius: 4,
                    transformOrigin: "bottom center",
                    transform: `rotate(${angle}deg)`,
                    boxShadow: `0 0 16px ${color}`,
                }}
            />

            {/* Center Hub */}
            <div
                style={{
                    position: "absolute",
                    bottom: -12,
                    left: size / 2 - 12,
                    width: 24,
                    height: 24,
                    backgroundColor: "#fff",
                    borderRadius: "50%",
                    boxShadow: "0 0 10px rgba(0,0,0,0.5)",
                }}
            />

            {/* Value Display */}
            <div
                className="absolute w-full text-center mt-6 font-mono font-bold"
                style={{ color, fontSize: size * 0.15 }}
            >
                {currentValue.toFixed(2)}
            </div>
        </div>
    );
};
