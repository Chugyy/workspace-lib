import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring } from "remotion";
import { fadeOut } from "../lib/animations";

type Props = {};

export const DecisionFlow: React.FC<Props> = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const exitOpacity = fadeOut(frame, durationInFrames, 15);

  const steps = [
    { icon: "📊", label: "Dashboard", color: "#22d3ee", delay: 5 },
    { icon: "🧠", label: "Decision", color: "#f59e0b", delay: 25 },
    { icon: "🎛️", label: "Control Panel", color: "#3b82f6", delay: 45 },
    { icon: "⚡", label: "Action", color: "#a78bfa", delay: 65 },
    { icon: "✅", label: "Resultat", color: "#22c55e", delay: 85 },
  ];

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#0f172a",
        justifyContent: "center",
        alignItems: "center",
        opacity: exitOpacity,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 0 }}>
        {steps.map((step, i) => {
          const s = spring({ frame: frame - step.delay, fps, config: { damping: 12 } });

          // Arrow between steps
          const arrowS = i < steps.length - 1
            ? spring({ frame: frame - step.delay - 12, fps, config: { damping: 15 } })
            : 0;

          // Active glow when "current"
          const isActive = frame >= step.delay + 15 && frame < step.delay + 35;
          const glowOpacity = isActive ? 0.4 : 0;

          return (
            <React.Fragment key={i}>
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  gap: 16,
                  transform: `scale(${s})`,
                  opacity: s,
                }}
              >
                <div
                  style={{
                    width: 90,
                    height: 90,
                    borderRadius: 22,
                    backgroundColor: `${step.color}15`,
                    border: `2px solid ${step.color}`,
                    display: "flex",
                    justifyContent: "center",
                    alignItems: "center",
                    boxShadow: `0 0 ${isActive ? 30 : 0}px ${step.color}${isActive ? "80" : "00"}`,
                    transition: "box-shadow 0.3s",
                  }}
                >
                  <span style={{ fontSize: 36 }}>{step.icon}</span>
                </div>
                <span
                  style={{
                    fontFamily: "Inter, sans-serif",
                    fontSize: 18,
                    fontWeight: 700,
                    color: step.color,
                    textAlign: "center",
                    maxWidth: 120,
                  }}
                >
                  {step.label}
                </span>
              </div>
              {/* Arrow */}
              {i < steps.length - 1 && (
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    margin: "0 16px",
                    marginBottom: 36,
                    opacity: arrowS,
                    transform: `scaleX(${arrowS})`,
                  }}
                >
                  <div style={{ width: 48, height: 3, backgroundColor: "#475569" }} />
                  <div
                    style={{
                      width: 0,
                      height: 0,
                      borderTop: "8px solid transparent",
                      borderBottom: "8px solid transparent",
                      borderLeft: "12px solid #475569",
                    }}
                  />
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
