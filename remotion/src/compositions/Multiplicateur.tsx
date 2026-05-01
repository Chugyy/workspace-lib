import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate, spring } from "remotion";
import { fadeIn, fadeOut } from "../lib/animations";

type Props = {};

export const Multiplicateur: React.FC<Props> = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const exitOpacity = fadeOut(frame, durationInFrames, 15);

  // Left side: 1 x 10 = 10
  const leftOpacity = fadeIn(frame, 10, 15);
  const leftScale = spring({ frame: frame - 10, fps, config: { damping: 12 } });

  // Right side: 20 x 10 = 200
  const rightOpacity = fadeIn(frame, 40, 15);
  const rightScale = spring({ frame: frame - 40, fps, config: { damping: 12 } });

  // "x10" multiplier appears
  const multOpacity = fadeIn(frame, 25, 12);

  // Result emphasis — right result pulses
  const pulseScale = frame > 70
    ? interpolate(Math.sin((frame - 70) * 0.15), [-1, 1], [1, 1.08])
    : 1;

  // "VS" label
  const vsOpacity = fadeIn(frame, 30, 10);

  // Bottom label
  const labelOpacity = fadeIn(frame, 80, 20);

  const boxStyle: React.CSSProperties = {
    borderRadius: 20,
    padding: "48px 56px",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: 16,
    minWidth: 380,
  };

  const numStyle: React.CSSProperties = {
    fontFamily: "Inter, sans-serif",
    fontWeight: 800,
    color: "#f8fafc",
    margin: 0,
    lineHeight: 1,
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
      <div style={{ display: "flex", alignItems: "center", gap: 80 }}>
        {/* Left — small multiplier */}
        <div
          style={{
            ...boxStyle,
            backgroundColor: "rgba(51,65,85,0.5)",
            border: "2px solid #334155",
            opacity: leftOpacity,
            transform: `scale(${leftScale})`,
          }}
        >
          <span style={{ ...numStyle, fontSize: 48, color: "#94a3b8" }}>1</span>
          <span style={{ ...numStyle, fontSize: 28, color: "#64748b", opacity: multOpacity }}>x 10</span>
          <div style={{ width: 60, height: 3, backgroundColor: "#475569", margin: "8px 0" }} />
          <span style={{ ...numStyle, fontSize: 64, color: "#94a3b8" }}>=  10</span>
        </div>

        {/* VS */}
        <span
          style={{
            fontFamily: "Inter, sans-serif",
            fontSize: 32,
            fontWeight: 700,
            color: "#475569",
            opacity: vsOpacity,
          }}
        >
          VS
        </span>

        {/* Right — big multiplier */}
        <div
          style={{
            ...boxStyle,
            backgroundColor: "rgba(59,130,246,0.1)",
            border: "2px solid #3b82f6",
            opacity: rightOpacity,
            transform: `scale(${rightScale * pulseScale})`,
          }}
        >
          <span style={{ ...numStyle, fontSize: 48, color: "#3b82f6" }}>20</span>
          <span style={{ ...numStyle, fontSize: 28, color: "#60a5fa", opacity: multOpacity }}>x 10</span>
          <div style={{ width: 60, height: 3, backgroundColor: "#3b82f6", margin: "8px 0" }} />
          <span style={{ ...numStyle, fontSize: 72, color: "#f8fafc" }}>=  200</span>
        </div>
      </div>

      {/* Bottom label */}
      <p
        style={{
          fontFamily: "Inter, sans-serif",
          fontSize: 28,
          color: "#94a3b8",
          fontWeight: 500,
          marginTop: 56,
          opacity: labelOpacity,
        }}
      >
        Focus sur le <span style={{ color: "#3b82f6", fontWeight: 700 }}>QUOI</span> et le{" "}
        <span style={{ color: "#3b82f6", fontWeight: 700 }}>POURQUOI</span> avant le comment.
      </p>
    </AbsoluteFill>
  );
};
