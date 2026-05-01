import React from "react";
import { Composition } from "remotion";
import { TextOverlay } from "./compositions/TextOverlay";
import { TitleCard } from "./compositions/TitleCard";
import { ChapterTitle } from "./compositions/ChapterTitle";
import { LowerThird } from "./compositions/LowerThird";
import { KeyPoint } from "./compositions/KeyPoint";
import { Multiplicateur } from "./compositions/Multiplicateur";
import { DashboardControlPanel } from "./compositions/DashboardControlPanel";
import { ButtonTypes } from "./compositions/ButtonTypes";
import { DecisionFlow } from "./compositions/DecisionFlow";
import { RoadmapExecution } from "./compositions/RoadmapExecution";
import { PointAPointB } from "./compositions/PointAPointB";
import { SeriePlaylist } from "./compositions/SeriePlaylist";
import { SouveraineteSaas } from "./compositions/SouveraineteSaas";

/**
 * Registry of all compositions.
 * Add new compositions here to make them available for rendering.
 *
 * To create a custom composition:
 * 1. Create a new file in src/compositions/
 * 2. Export a React component + a defaultProps object
 * 3. Register it below with a <Composition>
 */
export const Root: React.FC = () => {
  return (
    <>
      {/* Simple text overlay — fade in/out centered text */}
      <Composition
        id="TextOverlay"
        component={TextOverlay}
        durationInFrames={90}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          text: "Your text here",
          fontSize: 64,
          color: "#FFFFFF",
          backgroundColor: "rgba(0,0,0,0.7)",
        }}
      />

      {/* Full-screen title card with subtitle */}
      <Composition
        id="TitleCard"
        component={TitleCard}
        durationInFrames={120}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          title: "Title",
          subtitle: "",
          backgroundColor: "#0f172a",
          accentColor: "#3b82f6",
        }}
      />

      {/* Chapter title — slides in from left */}
      <Composition
        id="ChapterTitle"
        component={ChapterTitle}
        durationInFrames={75}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          number: "01",
          title: "Chapter Title",
          accentColor: "#3b82f6",
        }}
      />

      {/* Lower third — name/title bar at bottom */}
      <Composition
        id="LowerThird"
        component={LowerThird}
        durationInFrames={150}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          name: "Hugo Hoarau",
          role: "Lead Developer",
          accentColor: "#3b82f6",
        }}
      />

      {/* Key point — highlight a key idea with icon */}
      <Composition
        id="KeyPoint"
        component={KeyPoint}
        durationInFrames={120}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          icon: "💡",
          text: "Key insight here",
          backgroundColor: "rgba(15,23,42,0.9)",
          accentColor: "#3b82f6",
        }}
      />
      {/* --- Video 04: Structurer son agence --- */}

      <Composition
        id="Multiplicateur"
        component={Multiplicateur}
        durationInFrames={150}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{}}
      />

      <Composition
        id="DashboardControlPanel"
        component={DashboardControlPanel}
        durationInFrames={150}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{}}
      />

      <Composition
        id="ButtonTypes"
        component={ButtonTypes}
        durationInFrames={150}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{}}
      />

      <Composition
        id="DecisionFlow"
        component={DecisionFlow}
        durationInFrames={150}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{}}
      />

      <Composition
        id="RoadmapExecution"
        component={RoadmapExecution}
        durationInFrames={180}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{}}
      />

      <Composition
        id="PointAPointB"
        component={PointAPointB}
        durationInFrames={180}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{}}
      />

      <Composition
        id="SeriePlaylist"
        component={SeriePlaylist}
        durationInFrames={180}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{}}
      />

      <Composition
        id="SouveraineteSaas"
        component={SouveraineteSaas}
        durationInFrames={180}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{}}
      />
    </>
  );
};
