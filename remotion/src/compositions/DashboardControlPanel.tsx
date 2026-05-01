import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { fadeIn, fadeOut, slideIn } from "../lib/animations";

type Props = {};

export const DashboardControlPanel: React.FC<Props> = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const exitOpacity = fadeOut(frame, durationInFrames, 15);

  // Divider line
  const dividerHeight = interpolate(
    spring({ frame: frame - 5, fps, config: { damping: 15 } }),
    [0, 1],
    [0, 500]
  );

  // Dashboard side
  const dashOpacity = fadeIn(frame, 15, 15);
  const dashItems = [
    { icon: "📊", label: "Donnees", delay: 30 },
    { icon: "📈", label: "Insights", delay: 40 },
    { icon: "🎯", label: "KPIs", delay: 50 },
    { icon: "💬", label: "Messages", delay: 60 },
  ];

  // Control panel side
  const ctrlOpacity = fadeIn(frame, 20, 15);
  const ctrlItems = [
    { label: "Onboarding", delay: 35 },
    { label: "Production", delay: 45 },
    { label: "Livraison", delay: 55 },
    { label: "Relance", delay: 65 },
  ];

  // Subtitles
  const subDashOpacity = fadeIn(frame, 75, 15);
  const subCtrlOpacity = fadeIn(frame, 80, 15);

  const sectionStyle: React.CSSProperties = {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: 24,
    padding: "0 60px",
  };

  const titleStyle: React.CSSProperties = {
    fontFamily: "Inter, sans-serif",
    fontWeight: 800,
    fontSize: 36,
    margin: 0,
    marginBottom: 16,
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
      <div style={{ display: "flex", alignItems: "flex-start", width: "85%", position: "relative" }}>
        {/* Dashboard */}
        <div style={{ ...sectionStyle, opacity: dashOpacity }}>
          <h2 style={{ ...titleStyle, color: "#22d3ee" }}>DASHBOARD</h2>
          {dashItems.map((item, i) => {
            const s = spring({ frame: frame - item.delay, fps, config: { damping: 12 } });
            return (
              <div
                key={i}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 16,
                  backgroundColor: "rgba(34,211,238,0.08)",
                  border: "1px solid rgba(34,211,238,0.2)",
                  borderRadius: 12,
                  padding: "16px 28px",
                  width: "100%",
                  transform: `scale(${s}) translateY(${(1 - s) * 20}px)`,
                  opacity: s,
                }}
              >
                <span style={{ fontSize: 28 }}>{item.icon}</span>
                <span style={{ fontFamily: "Inter, sans-serif", fontSize: 22, color: "#e2e8f0", fontWeight: 500 }}>
                  {item.label}
                </span>
              </div>
            );
          })}
          <p
            style={{
              fontFamily: "Inter, sans-serif",
              fontSize: 18,
              color: "#22d3ee",
              fontWeight: 600,
              opacity: subDashOpacity,
              marginTop: 8,
            }}
          >
            Voir &middot; Comprendre &middot; Decider
          </p>
        </div>

        {/* Divider */}
        <div
          style={{
            width: 3,
            height: dividerHeight,
            backgroundColor: "#334155",
            borderRadius: 4,
            alignSelf: "center",
          }}
        />

        {/* Control Panel */}
        <div style={{ ...sectionStyle, opacity: ctrlOpacity }}>
          <h2 style={{ ...titleStyle, color: "#3b82f6" }}>CONTROL PANEL</h2>
          {ctrlItems.map((item, i) => {
            const s = spring({ frame: frame - item.delay, fps, config: { damping: 12 } });
            return (
              <div
                key={i}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 16,
                  backgroundColor: "rgba(59,130,246,0.1)",
                  border: "1px solid rgba(59,130,246,0.3)",
                  borderRadius: 12,
                  padding: "16px 28px",
                  width: "100%",
                  transform: `scale(${s}) translateY(${(1 - s) * 20}px)`,
                  opacity: s,
                  cursor: "pointer",
                }}
              >
                <div
                  style={{
                    width: 16,
                    height: 16,
                    borderRadius: 4,
                    backgroundColor: "#3b82f6",
                    boxShadow: "0 0 12px rgba(59,130,246,0.5)",
                  }}
                />
                <span style={{ fontFamily: "Inter, sans-serif", fontSize: 22, color: "#e2e8f0", fontWeight: 500 }}>
                  {item.label}
                </span>
              </div>
            );
          })}
          <p
            style={{
              fontFamily: "Inter, sans-serif",
              fontSize: 18,
              color: "#3b82f6",
              fontWeight: 600,
              opacity: subCtrlOpacity,
              marginTop: 8,
            }}
          >
            Agir &middot; Executer &middot; Controler
          </p>
        </div>
      </div>
    </AbsoluteFill>
  );
};
