import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { fadeIn, fadeOut } from "../lib/animations";

type Props = {};

export const SouveraineteSaas: React.FC<Props> = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const exitOpacity = fadeOut(frame, durationInFrames, 15);

  const saasTools = [
    { name: "CRM", price: "$49/mo" },
    { name: "Gestion projet", price: "$99/mo" },
    { name: "Automatisation", price: "$199/mo" },
    { name: "Facturation", price: "$79/mo" },
    { name: "Communication", price: "$149/mo" },
  ];

  // Left side appears
  const leftOpacity = fadeIn(frame, 5, 15);

  // Total price counter
  const totalTarget = 575;
  const totalProgress = interpolate(frame, [40, 70], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const totalPrice = Math.round(totalTarget * totalProgress);

  // Left grays out
  const grayProgress = interpolate(frame, [90, 110], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Right side appears
  const rightScale = spring({ frame: frame - 80, fps, config: { damping: 12 } });

  // "10%" label
  const usageOpacity = fadeIn(frame, 60, 15);

  // VS
  const vsOpacity = fadeIn(frame, 75, 10);

  const columnStyle: React.CSSProperties = {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: 16,
    width: 400,
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
      <div style={{ display: "flex", alignItems: "flex-start", gap: 80 }}>
        {/* SaaS stack — left */}
        <div
          style={{
            ...columnStyle,
            opacity: leftOpacity,
            filter: `grayscale(${grayProgress * 0.8}) brightness(${1 - grayProgress * 0.3})`,
          }}
        >
          <h3
            style={{
              fontFamily: "Inter, sans-serif",
              fontSize: 24,
              fontWeight: 700,
              color: "#ef4444",
              margin: 0,
              marginBottom: 8,
            }}
          >
            SaaS externes
          </h3>

          {saasTools.map((tool, i) => {
            const s = spring({ frame: frame - 10 - i * 8, fps, config: { damping: 14 } });
            return (
              <div
                key={i}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  width: "100%",
                  backgroundColor: "rgba(239,68,68,0.06)",
                  border: "1px solid rgba(239,68,68,0.2)",
                  borderRadius: 10,
                  padding: "14px 20px",
                  opacity: s,
                  transform: `scale(${s})`,
                }}
              >
                <span style={{ fontFamily: "Inter, sans-serif", fontSize: 18, color: "#e2e8f0", fontWeight: 500 }}>
                  {tool.name}
                </span>
                <span style={{ fontFamily: "Inter, sans-serif", fontSize: 18, color: "#ef4444", fontWeight: 700 }}>
                  {tool.price}
                </span>
              </div>
            );
          })}

          {/* Total */}
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              width: "100%",
              borderTop: "2px solid #ef4444",
              paddingTop: 12,
              marginTop: 4,
            }}
          >
            <span style={{ fontFamily: "Inter, sans-serif", fontSize: 20, color: "#fca5a5", fontWeight: 600 }}>
              Total / mois
            </span>
            <span style={{ fontFamily: "Inter, sans-serif", fontSize: 24, color: "#ef4444", fontWeight: 800 }}>
              ${totalPrice}
            </span>
          </div>

          {/* Usage label */}
          <span
            style={{
              fontFamily: "Inter, sans-serif",
              fontSize: 16,
              color: "#f87171",
              fontWeight: 700,
              opacity: usageOpacity,
              backgroundColor: "rgba(239,68,68,0.1)",
              padding: "6px 16px",
              borderRadius: 20,
            }}
          >
            Utilise a 10%
          </span>
        </div>

        {/* VS */}
        <span
          style={{
            fontFamily: "Inter, sans-serif",
            fontSize: 28,
            fontWeight: 700,
            color: "#475569",
            opacity: vsOpacity,
            marginTop: 200,
          }}
        >
          VS
        </span>

        {/* Own system — right */}
        <div
          style={{
            ...columnStyle,
            transform: `scale(${rightScale})`,
            opacity: rightScale,
          }}
        >
          <h3
            style={{
              fontFamily: "Inter, sans-serif",
              fontSize: 24,
              fontWeight: 700,
              color: "#22c55e",
              margin: 0,
              marginBottom: 8,
            }}
          >
            Ton systeme
          </h3>

          <div
            style={{
              width: "100%",
              backgroundColor: "rgba(34,197,94,0.08)",
              border: "2px solid #22c55e",
              borderRadius: 16,
              padding: "40px 32px",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 20,
            }}
          >
            <span style={{ fontSize: 56 }}>🖥️</span>
            <span style={{ fontFamily: "Inter, sans-serif", fontSize: 22, color: "#f8fafc", fontWeight: 700 }}>
              TON SERVEUR
            </span>
            <span style={{ fontFamily: "Inter, sans-serif", fontSize: 16, color: "#86efac", fontWeight: 500 }}>
              CRM + Gestion + Auto + Factu + Com
            </span>
            <div style={{ width: "80%", height: 2, backgroundColor: "#22c55e", margin: "4px 0" }} />
            <span style={{ fontFamily: "Inter, sans-serif", fontSize: 28, color: "#22c55e", fontWeight: 800 }}>
              ~$15/mo
            </span>
          </div>

          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              marginTop: 8,
            }}
          >
            <span style={{ fontSize: 20 }}>🔒</span>
            <span
              style={{
                fontFamily: "Inter, sans-serif",
                fontSize: 18,
                color: "#22c55e",
                fontWeight: 700,
              }}
            >
              100% souverain
            </span>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
