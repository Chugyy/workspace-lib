import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

/**
 * Shared animation helpers.
 * Use these in compositions to keep animation behavior consistent.
 */

/** Fade in over `durationFrames` starting at `delay` */
export const fadeIn = (
  frame: number,
  delay = 0,
  durationFrames = 15
): number =>
  interpolate(frame, [delay, delay + durationFrames], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

/** Fade out ending at `endFrame` over `durationFrames` */
export const fadeOut = (
  frame: number,
  endFrame: number,
  durationFrames = 15
): number =>
  interpolate(
    frame,
    [endFrame - durationFrames, endFrame],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

/** Fade in + fade out (full lifecycle) */
export const fadeInOut = (
  frame: number,
  totalFrames: number,
  fadeDuration = 15
): number => {
  const inOpacity = fadeIn(frame, 0, fadeDuration);
  const outOpacity = fadeOut(frame, totalFrames, fadeDuration);
  return Math.min(inOpacity, outOpacity);
};

/** Slide from offset to 0 with spring physics */
export const slideIn = (
  frame: number,
  fps: number,
  from: number,
  delay = 0
): number => {
  const s = spring({ frame: frame - delay, fps, config: { damping: 15 } });
  return interpolate(s, [0, 1], [from, 0]);
};

/** Scale up from 0 to 1 with spring */
export const scaleIn = (
  frame: number,
  fps: number,
  delay = 0
): number =>
  spring({
    frame: frame - delay,
    fps,
    config: { damping: 12, stiffness: 100 },
  });
