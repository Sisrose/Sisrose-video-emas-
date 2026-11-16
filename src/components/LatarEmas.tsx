import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { warna } from "../tema";

/** Latar gelap mewah dengan cahaya emas yang bergerak perlahan. */
export const LatarEmas: React.FC<{ terang?: boolean }> = ({ terang }) => {
  const frame = useCurrentFrame();
  const x = interpolate(Math.sin(frame / 40), [-1, 1], [30, 70]);
  const y = interpolate(Math.cos(frame / 55), [-1, 1], [30, 60]);
  return (
    <AbsoluteFill
      style={{
        background: terang
          ? `radial-gradient(circle at ${x}% ${y}%, ${warna.emasTerang} 0%, ${warna.emas} 40%, ${warna.emasGelap} 100%)`
          : `radial-gradient(circle at ${x}% ${y}%, #5a4115 0%, #2a1d0b 45%, ${warna.hitam} 100%)`,
      }}
    />
  );
};
