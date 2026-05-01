import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { fadeOut, slideIn, fadeIn } from "../lib/animations";

type Props = {
  number: string;
  title: string;
  accentColor: string;
};

export const ChapterTitle: React.FC<Props> = ({ number, title, accentColor }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const slideX = slideIn(frame, fps, -200, 0);
  const numberOpacity = fadeIn(frame, 0, 10);
  const exitOpacity = fadeOut(frame, durationInFrames, 12);

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "transparent",
        justifyContent: "center",
        paddingLeft: 120,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 32, opacity: exitOpacity }}>
        {/* Number badge */}
        <div
          style={{
            width: 80,
            height: 80,
            borderRadius: 16,
            backgroundColor: accentColor,
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            opacity: numberOpacity,
          }}
        >
          <span
            style={{
              fontSize: 36,
              fontWeight: 800,
              color: "#fff",
              fontFamily: "Inter, sans-serif",
            }}
          >
            {number}
          </span>
        </div>
        {/* Title */}
        <h2
          style={{
            fontSize: 56,
            fontWeight: 700,
            color: "#f8fafc",
            fontFamily: "Inter, sans-serif",
            margin: 0,
            transform: `translateX(${slideX}px)`,
          }}
        >
          {title}
        </h2>
      </div>
    </AbsoluteFill>
  );
};
