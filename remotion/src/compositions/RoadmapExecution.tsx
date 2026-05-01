import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { fadeIn, fadeOut } from "../lib/animations";

type Props = {};

export const RoadmapExecution: React.FC<Props> = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const exitOpacity = fadeOut(frame, durationInFrames, 15);

  // Phase 1: static document (frames 0-50)
  const docOpacity = fadeIn(frame, 5, 15);

  // Phase 2: document grays out (frames 50-70)
  const grayAmount = interpolate(frame, [50, 70], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Label "juste un document"
  const labelOpacity = interpolate(frame, [55, 65], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Phase 3: alive document appears right (frames 70+)
  const aliveScale = spring({ frame: frame - 75, fps, config: { damping: 12 } });

  const tasks = [
    { label: "Cartographier le business", delay: 85 },
    { label: "Definir inputs / outputs", delay: 95 },
    { label: "Lister problemes", delay: 105 },
    { label: "Prioriser la roadmap", delay: 115 },
  ];

  // VS label
  const vsOpacity = fadeIn(frame, 70, 12);

  const docStyle: React.CSSProperties = {
    width: 360,
    borderRadius: 16,
    padding: "36px 32px",
    display: "flex",
    flexDirection: "column",
    gap: 16,
  };

  const lineStyle: React.CSSProperties = {
    height: 12,
    borderRadius: 6,
    backgroundColor: "#334155",
  };

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#0f172a",
        justifyContent: "center",
        alignItems: "center",
        opacity: exitOpacity,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 64 }}>
        {/* Dead document */}
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 20 }}>
          <div
            style={{
              ...docStyle,
              backgroundColor: "rgba(51,65,85,0.3)",
              border: "2px solid #334155",
              opacity: docOpacity,
              filter: `grayscale(${grayAmount}) brightness(${1 - grayAmount * 0.4})`,
            }}
          >
            <div style={{ ...lineStyle, width: "70%" }} />
            <div style={{ ...lineStyle, width: "100%" }} />
            <div style={{ ...lineStyle, width: "85%" }} />
            <div style={{ ...lineStyle, width: "60%" }} />
            <div style={{ ...lineStyle, width: "90%" }} />
            <div style={{ ...lineStyle, width: "45%" }} />
          </div>
          <span
            style={{
              fontFamily: "Inter, sans-serif",
              fontSize: 20,
              color: "#ef4444",
              fontWeight: 700,
              opacity: labelOpacity,
            }}
          >
            Juste un document
          </span>
        </div>

        {/* VS */}
        <span
          style={{
            fontFamily: "Inter, sans-serif",
            fontSize: 28,
            fontWeight: 700,
            color: "#475569",
            opacity: vsOpacity,
          }}
        >
          VS
        </span>

        {/* Alive document */}
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 20 }}>
          <div
            style={{
              ...docStyle,
              backgroundColor: "rgba(59,130,246,0.08)",
              border: "2px solid #3b82f6",
              transform: `scale(${aliveScale})`,
              opacity: aliveScale,
            }}
          >
            {tasks.map((task, i) => {
              const checked = frame > task.delay;
              const checkScale = spring({ frame: frame - task.delay, fps, config: { damping: 10 } });
              return (
                <div
                  key={i}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 14,
                    padding: "10px 0",
                  }}
                >
                  <div
                    style={{
                      width: 24,
                      height: 24,
                      borderRadius: 6,
                      border: `2px solid ${checked ? "#22c55e" : "#475569"}`,
                      backgroundColor: checked ? "#22c55e" : "transparent",
                      display: "flex",
                      justifyContent: "center",
                      alignItems: "center",
                      transform: `scale(${checked ? checkScale : 1})`,
                    }}
                  >
                    {checked && (
                      <span style={{ color: "#fff", fontSize: 14, fontWeight: 800 }}>✓</span>
                    )}
                  </div>
                  <span
                    style={{
                      fontFamily: "Inter, sans-serif",
                      fontSize: 18,
                      color: checked ? "#e2e8f0" : "#64748b",
                      fontWeight: 500,
                    }}
                  >
                    {task.label}
                  </span>
                </div>
              );
            })}
          </div>
          <span
            style={{
              fontFamily: "Inter, sans-serif",
              fontSize: 20,
              color: "#22c55e",
              fontWeight: 700,
              opacity: aliveScale,
            }}
          >
            Roadmap actionnable
          </span>
        </div>
      </div>
    </AbsoluteFill>
  );
};
