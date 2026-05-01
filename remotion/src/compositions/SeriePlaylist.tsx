import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring } from "remotion";
import { fadeIn, fadeOut, slideIn } from "../lib/animations";

type Props = {};

export const SeriePlaylist: React.FC<Props> = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const exitOpacity = fadeOut(frame, durationInFrames, 15);
  const titleOpacity = fadeIn(frame, 0, 15);

  const videos = [
    { num: "#0", title: "Structurer son agence — Roadmap", icon: "🗺️", status: "current", delay: 15 },
    { num: "#1", title: "Process de developpement avec l'IA", icon: "🤖", status: "next", delay: 30 },
    { num: "#2", title: "Infrastructure & serveur souverain", icon: "🖥️", status: "next", delay: 45 },
    { num: "#3", title: "Onboarding client automatise", icon: "📋", status: "next", delay: 60 },
    { num: "#4", title: "Scoring & assignation prestataires", icon: "📊", status: "next", delay: 75 },
    { num: "#5", title: "Dashboard & KPIs en temps reel", icon: "📈", status: "next", delay: 90 },
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
      <div style={{ display: "flex", flexDirection: "column", gap: 16, width: 700 }}>
        {/* Title */}
        <h2
          style={{
            fontFamily: "Inter, sans-serif",
            fontSize: 32,
            fontWeight: 800,
            color: "#f8fafc",
            margin: 0,
            marginBottom: 16,
            opacity: titleOpacity,
          }}
        >
          Serie : Structurer son agence
        </h2>

        {videos.map((video, i) => {
          const s = spring({ frame: frame - video.delay, fps, config: { damping: 14 } });
          const x = slideIn(frame, fps, 80, video.delay);
          const isCurrent = video.status === "current";

          return (
            <div
              key={i}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 20,
                backgroundColor: isCurrent
                  ? "rgba(59,130,246,0.12)"
                  : "rgba(51,65,85,0.3)",
                border: isCurrent
                  ? "2px solid #3b82f6"
                  : "1px solid #334155",
                borderRadius: 14,
                padding: "18px 24px",
                opacity: s,
                transform: `translateX(${x}px)`,
              }}
            >
              <span style={{ fontSize: 28 }}>{video.icon}</span>
              <span
                style={{
                  fontFamily: "Inter, sans-serif",
                  fontSize: 16,
                  fontWeight: 700,
                  color: isCurrent ? "#3b82f6" : "#64748b",
                  minWidth: 32,
                }}
              >
                {video.num}
              </span>
              <span
                style={{
                  fontFamily: "Inter, sans-serif",
                  fontSize: 20,
                  fontWeight: 500,
                  color: isCurrent ? "#f8fafc" : "#cbd5e1",
                  flex: 1,
                }}
              >
                {video.title}
              </span>
              {isCurrent && (
                <span
                  style={{
                    fontFamily: "Inter, sans-serif",
                    fontSize: 12,
                    fontWeight: 700,
                    color: "#3b82f6",
                    backgroundColor: "rgba(59,130,246,0.15)",
                    padding: "4px 12px",
                    borderRadius: 20,
                    textTransform: "uppercase",
                    letterSpacing: 1,
                  }}
                >
                  En cours
                </span>
              )}
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
