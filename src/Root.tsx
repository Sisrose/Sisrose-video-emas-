import { Composition } from "remotion";
import { kandungan } from "./kandungan";
import { BILANGAN_BABAK, VideoEmas } from "./VideoEmas";

const FPS = 30;

export const RemotionRoot: React.FC = () => (
  <Composition
    id="VideoEmas"
    component={VideoEmas}
    width={1080}
    height={1920}
    fps={FPS}
    defaultProps={kandungan}
    calculateMetadata={({ props }) => ({
      durationInFrames:
        BILANGAN_BABAK * Math.round(props.saatSetiapBabak * FPS) - (BILANGAN_BABAK - 1) * Math.round(props.saatPeralihan * FPS),
    })}
  />
);
