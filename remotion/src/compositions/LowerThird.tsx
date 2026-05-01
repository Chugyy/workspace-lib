import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { fadeIn, fadeOut, slideIn } from "../lib/animations";

type Props = {
  name: string;
  role: string;
  accentColor: string;
};

export const LowerThird: React.FC<Props> = ({ name, role, accentColor }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const barWidth = slideIn(frame, fps, -400, 0);
  const textOpacity = fadeIn(frame, 10, 15);
  const exitOpacity = fadeOut(frame, durationInFrames, 15);

  return (
    <AbsoluteFill style={{ backgroundColor: "transparent" }}>
      <div
        style={{
          position: "absolute",
          bottom: 80,
          left: 80,
          display: "flex",
          alignItems: "flex-end",
          gap: 0,
          opacity: exitOpacity,
        }}
      >
        {/* Accent bar */}
        <div
          style={{
            width: 6,
            height: 80,
            backgroundColor: accentColor,
            borderRadius: 3,
            transform: `translateX(${barWidth}px)`,
            marginRight: 20,
          }}
        />
        <div style={{ opacity: textOpacity }}>
          <div
            style={{
              fontSize: 36,
              fontWeight: 700,
              color: "#f8fafc",
              fontFamily: "Inter, sans-serif",
              lineHeight: 1.2,
            }}
          >
            {name}
          </div>
          <div
            style={{
              fontSize: 22,
              fontWeight: 400,
              color: "#94a3b8",
              fontFamily: "Inter, sans-serif",
            }}
          >
            {role}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
