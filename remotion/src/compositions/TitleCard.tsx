import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { fadeIn, fadeOut, slideIn } from "../lib/animations";

type Props = {
  title: string;
  subtitle: string;
  backgroundColor: string;
  accentColor: string;
};

export const TitleCard: React.FC<Props> = ({
  title,
  subtitle,
  backgroundColor,
  accentColor,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const titleY = slideIn(frame, fps, 60, 0);
  const subtitleOpacity = fadeIn(frame, 15, 20);
  const exitOpacity = fadeOut(frame, durationInFrames, 15);

  return (
    <AbsoluteFill style={{ backgroundColor, justifyContent: "center", alignItems: "center" }}>
      {/* Accent line */}
      <div
        style={{
          width: 80,
          height: 4,
          backgroundColor: accentColor,
          marginBottom: 32,
          opacity: exitOpacity,
        }}
      />
      {/* Title */}
      <h1
        style={{
          fontSize: 72,
          color: "#f8fafc",
          fontFamily: "Inter, sans-serif",
          fontWeight: 800,
          transform: `translateY(${titleY}px)`,
          opacity: exitOpacity,
          margin: 0,
          textAlign: "center",
          maxWidth: "80%",
        }}
      >
        {title}
      </h1>
      {/* Subtitle */}
      {subtitle && (
        <p
          style={{
            fontSize: 28,
            color: "#94a3b8",
            fontFamily: "Inter, sans-serif",
            fontWeight: 400,
            opacity: subtitleOpacity * exitOpacity,
            marginTop: 16,
          }}
        >
          {subtitle}
        </p>
      )}
    </AbsoluteFill>
  );
};
