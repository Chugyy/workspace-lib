import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { fadeInOut } from "../lib/animations";

type Props = {
  text: string;
  fontSize: number;
  color: string;
  backgroundColor: string;
};

export const TextOverlay: React.FC<Props> = ({
  text,
  fontSize,
  color,
  backgroundColor,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const opacity = fadeInOut(frame, durationInFrames);

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
          backgroundColor,
          padding: "24px 48px",
          borderRadius: 12,
        }}
      >
        <span style={{ fontSize, color, fontFamily: "Inter, sans-serif", fontWeight: 600 }}>
          {text}
        </span>
      </div>
    </AbsoluteFill>
  );
};
