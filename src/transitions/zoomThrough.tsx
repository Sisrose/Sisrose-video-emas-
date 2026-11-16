import type { TransitionPresentation, TransitionPresentationComponentProps } from "@remotion/transitions";
import { AbsoluteFill, interpolate } from "remotion";

type Props = Record<string, never>;

/**
 * EFEK 1: ZOOM THROUGH CUT
 * Babak lama "ditembusi" kamera (zoom masuk besar + kabur),
 * babak baru muncul dari jauh ke depan.
 */
const ZoomThrough: React.FC<TransitionPresentationComponentProps<Props>> = ({
  children,
  presentationDirection,
  presentationProgress: p,
}) => {
  const keluar = presentationDirection === "exiting";
  const scale = keluar ? interpolate(p, [0, 1], [1, 6]) : interpolate(p, [0, 1], [0.35, 1]);
  const blur = keluar ? interpolate(p, [0, 1], [0, 30]) : interpolate(p, [0, 1], [20, 0]);
  const opacity = keluar ? interpolate(p, [0.4, 1], [1, 0], { extrapolateLeft: "clamp" }) : interpolate(p, [0, 0.5], [0, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ transform: `scale(${scale})`, filter: `blur(${blur}px)`, opacity, zIndex: keluar ? 1 : 0 }}>
      {children}
    </AbsoluteFill>
  );
};

export const zoomThrough = (): TransitionPresentation<Props> => ({ component: ZoomThrough, props: {} });
