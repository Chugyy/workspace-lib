import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { fadeInOut, scaleIn } from "../lib/animations";

type Props = {
  icon: string;
  text: string;
  backgroundColor: string;
  accentColor: string;
};

export const KeyPoint: React.FC<Props> = ({
  icon,
  text,
  backgroundColor,
  accentColor,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const opacity = fadeInOut(frame, durationInFrames, 15);
  const scale = scaleIn(frame, fps, 0);

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        backgroundColor: "transparent",
      }}
    >
      <div
        style={{
          opacity,
          transform: `scale(${scale})`,
          backgroundColor,
          borderLeft: `4px solid ${accentColor}`,
          borderRadius: 16,
          padding: "40px 56px",
          display: "flex",
          alignItems: "center",
          gap: 28,
          maxWidth: "70%",
        }}
      >
        <span style={{ fontSize: 56 }}>{icon}</span>
        <span
          style={{
            fontSize: 40,
            fontWeight: 600,
            color: "#f1f5f9",
            fontFamily: "Inter, sans-serif",
            lineHeight: 1.4,
          }}
        >
          {text}
        </span>
      </div>
    </AbsoluteFill>
  );
};
