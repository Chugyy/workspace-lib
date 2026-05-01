import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { fadeIn, fadeOut } from "../lib/animations";

type Props = {};

export const PointAPointB: React.FC<Props> = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const exitOpacity = fadeOut(frame, durationInFrames, 15);

  // Point A appears
  const aScale = spring({ frame: frame - 5, fps, config: { damping: 12 } });

  // Question mark
  const qOpacity = fadeIn(frame, 20, 15);

  // Point B appears (blurry first)
  const bScale = spring({ frame: frame - 30, fps, config: { damping: 12 } });

  // Both points clarify
  const clarifyProgress = interpolate(frame, [60, 85], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Arrow draws
  const arrowWidth = interpolate(frame, [85, 110], [0, 500], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Label "ROADMAP" on the arrow
  const roadmapOpacity = fadeIn(frame, 110, 15);

  const pointStyle: React.CSSProperties = {
    width: 160,
    height: 160,
    borderRadius: "50%",
    display: "flex",
    flexDirection: "column",
    justifyContent: "center",
    alignItems: "center",
    gap: 8,
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
      <div style={{ display: "flex", alignItems: "center", gap: 0, position: "relative" }}>
        {/* Point A */}
        <div
          style={{
            ...pointStyle,
            backgroundColor: `rgba(239,68,68,${0.1 + clarifyProgress * 0.1})`,
            border: `3px solid rgba(239,68,68,${0.3 + clarifyProgress * 0.7})`,
            transform: `scale(${aScale})`,
            filter: `blur(${(1 - clarifyProgress) * 4}px)`,
          }}
        >
          <span style={{ fontFamily: "Inter, sans-serif", fontSize: 48, fontWeight: 800, color: "#ef4444" }}>A</span>
          <span
            style={{
              fontFamily: "Inter, sans-serif",
              fontSize: 14,
              fontWeight: 600,
              color: "#fca5a5",
              opacity: clarifyProgress,
            }}
          >
            Aujourd'hui
          </span>
        </div>

        {/* Arrow zone */}
        <div style={{ width: 500, position: "relative", height: 60, margin: "0 24px" }}>
          {/* Question mark (fades out as arrow appears) */}
          <span
            style={{
              position: "absolute",
              left: "50%",
              top: "50%",
              transform: "translate(-50%, -50%)",
              fontFamily: "Inter, sans-serif",
              fontSize: 64,
              fontWeight: 800,
              color: "#475569",
              opacity: qOpacity * (1 - clarifyProgress),
            }}
          >
            ?
          </span>

          {/* Arrow line */}
          <div
            style={{
              position: "absolute",
              left: 0,
              top: "50%",
              transform: "translateY(-50%)",
              width: arrowWidth,
              height: 4,
              background: "linear-gradient(90deg, #ef4444, #3b82f6)",
              borderRadius: 2,
            }}
          />
          {/* Arrow head */}
          {arrowWidth > 480 && (
            <div
              style={{
                position: "absolute",
                right: 0,
                top: "50%",
                transform: "translateY(-50%)",
                width: 0,
                height: 0,
                borderTop: "12px solid transparent",
                borderBottom: "12px solid transparent",
                borderLeft: "18px solid #3b82f6",
              }}
            />
          )}
          {/* ROADMAP label */}
          <span
            style={{
              position: "absolute",
              left: "50%",
              top: -30,
              transform: "translateX(-50%)",
              fontFamily: "Inter, sans-serif",
              fontSize: 22,
              fontWeight: 800,
              color: "#3b82f6",
              opacity: roadmapOpacity,
              letterSpacing: 4,
            }}
          >
            ROADMAP
          </span>
        </div>

        {/* Point B */}
        <div
          style={{
            ...pointStyle,
            backgroundColor: `rgba(59,130,246,${0.1 + clarifyProgress * 0.1})`,
            border: `3px solid rgba(59,130,246,${0.3 + clarifyProgress * 0.7})`,
            transform: `scale(${bScale})`,
            filter: `blur(${(1 - clarifyProgress) * 4}px)`,
          }}
        >
          <span style={{ fontFamily: "Inter, sans-serif", fontSize: 48, fontWeight: 800, color: "#3b82f6" }}>B</span>
          <span
            style={{
              fontFamily: "Inter, sans-serif",
              fontSize: 14,
              fontWeight: 600,
              color: "#93c5fd",
              opacity: clarifyProgress,
            }}
          >
            Objectif
          </span>
        </div>
      </div>
    </AbsoluteFill>
  );
};
