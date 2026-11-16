import { linearTiming, TransitionSeries } from "@remotion/transitions";
import { AbsoluteFill, useVideoConfig } from "remotion";
import { Kandungan } from "./kandungan";
import { Checklist } from "./scenes/Checklist";
import { Glass } from "./scenes/Glass";
import { GreenScreen } from "./scenes/GreenScreen";
import { HeadlineWall } from "./scenes/HeadlineWall";
import { Orbit } from "./scenes/Orbit";
import { PaperCut } from "./scenes/PaperCut";
import { zoomThrough } from "./transitions/zoomThrough";

export const BILANGAN_BABAK = 6;

/** Urutan babak — setiap peralihan menggunakan Zoom Through Cut. */
export const VideoEmas: React.FC<Kandungan> = (k) => {
  const { fps } = useVideoConfig();
  const babak = Math.round(k.saatSetiapBabak * fps);
  const peralihan = Math.round(k.saatPeralihan * fps);

  const senarai = [
    <HeadlineWall {...k.headlineWall} />,
    <Orbit {...k.orbit} />,
    <Glass {...k.glass} gambarProduk={k.orbit.gambarProduk} />,
    <GreenScreen {...k.greenScreen} />,
    <PaperCut {...k.paperCut} />,
    <Checklist {...k.checklist} />,
  ];

  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      <TransitionSeries>
        {senarai.flatMap((el, i) => {
          const keping = [
            <TransitionSeries.Sequence key={`s${i}`} durationInFrames={babak}>
              {el}
            </TransitionSeries.Sequence>,
          ];
          if (i < senarai.length - 1) {
            keping.push(
              <TransitionSeries.Transition key={`t${i}`} presentation={zoomThrough()} timing={linearTiming({ durationInFrames: peralihan })} />,
            );
          }
          return keping;
        })}
      </TransitionSeries>
    </AbsoluteFill>
  );
};
