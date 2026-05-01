import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { fadeIn, fadeOut } from "../lib/animations";

type Props = {};

export const ButtonTypes: React.FC<Props> = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const exitOpacity = fadeOut(frame, durationInFrames, 15);

  // Central button
  const btnScale = spring({ frame: frame - 5, fps, config: { damping: 10, stiffness: 80 } });

  // Button press animation
  const pressFrame = 30;
  const isPressed = frame >= pressFrame && frame <= pressFrame + 8;
  const pressScale = isPressed ? 0.92 : 1;

  // Branches appear after press
  const branches = [
    { icon: "👤", label: "Humain", color: "#22d3ee", delay: 40, angle: -35 },
    { icon: "🤖", label: "IA", color: "#a78bfa", delay: 50, angle: 0 },
    { icon: "👤+🤖", label: "Humain + IA", color: "#3b82f6", delay: 60, angle: 35 },
  ];

  // Line from button to branch
  const lineLength = 160;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#0f172a",
        justifyContent: "center",
        alignItems: "center",
        opacity: exitOpacity,
      }}
    >
      {/* Title */}
      <p
        style={{
          position: "absolute",
          top: 100,
          fontFamily: "Inter, sans-serif",
          fontSize: 32,
          color: "#94a3b8",
          fontWeight: 600,
          opacity: fadeIn(frame, 0, 12),
        }}
      >
        Chaque bouton declenche...
      </p>

      {/* Central button */}
      <div
        style={{
          position: "absolute",
          top: 280,
          transform: `scale(${btnScale * pressScale})`,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
        }}
      >
        <div
          style={{
            width: 120,
            height: 120,
            borderRadius: 24,
            backgroundColor: "#3b82f6",
            boxShadow: isPressed
              ? "0 2px 8px rgba(59,130,246,0.4)"
              : "0 8px 32px rgba(59,130,246,0.4)",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
          }}
        >
          <span style={{ fontSize: 48 }}>⏻</span>
        </div>
      </div>

      {/* Branches */}
      {branches.map((branch, i) => {
        const s = spring({ frame: frame - branch.delay, fps, config: { damping: 12 } });
        const rad = (branch.angle * Math.PI) / 180;
        const x = Math.sin(rad) * (lineLength + 100);
        const y = Math.cos(rad) * (lineLength + 100);

        return (
          <React.Fragment key={i}>
            {/* Line */}
            <div
              style={{
                position: "absolute",
                top: 400,
                left: "50%",
                width: 3,
                height: lineLength * s,
                backgroundColor: branch.color,
                opacity: s * 0.5,
                transform: `translateX(-1.5px) rotate(${-branch.angle}deg)`,
                transformOrigin: "top center",
              }}
            />
            {/* Branch node */}
            <div
              style={{
                position: "absolute",
                top: 400 + y,
                left: `calc(50% + ${x}px)`,
                transform: `translate(-50%, 0) scale(${s})`,
                opacity: s,
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: 12,
              }}
            >
              <div
                style={{
                  width: 80,
                  height: 80,
                  borderRadius: 20,
                  backgroundColor: `${branch.color}15`,
                  border: `2px solid ${branch.color}`,
                  display: "flex",
                  justifyContent: "center",
                  alignItems: "center",
                }}
              >
                <span style={{ fontSize: 32 }}>{branch.icon}</span>
              </div>
              <span
                style={{
                  fontFamily: "Inter, sans-serif",
                  fontSize: 22,
                  color: branch.color,
                  fontWeight: 700,
                }}
              >
                {branch.label}
              </span>
            </div>
          </React.Fragment>
        );
      })}
    </AbsoluteFill>
  );
};
