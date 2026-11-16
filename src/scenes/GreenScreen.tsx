import { useCallback, useRef } from "react";
import { AbsoluteFill, Img, OffthreadVideo, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { LatarEmas } from "../components/LatarEmas";
import { fonSans, warna } from "../tema";

const LEBAR = 1080;
const TINGGI = 1920;

/**
 * EFEK 5: GREEN SCREEN — buang latar hijau dari video Kak Ros
 * dan letak Kak Ros di atas latar emas / gambar kedai.
 */
export const GreenScreen: React.FC<{ video: string; latar: string; kapsyen: string }> = ({ video, latar, kapsyen }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const kanvas = useRef<HTMLCanvasElement>(null);
  const masuk = spring({ frame: frame - 8, fps, config: { damping: 14 } });

  const onVideoFrame = useCallback((imej: CanvasImageSource) => {
    const ctx = kanvas.current?.getContext("2d", { willReadFrequently: true });
    if (!ctx) return;
    ctx.clearRect(0, 0, LEBAR, TINGGI);
    ctx.drawImage(imej, 0, 0, LEBAR, TINGGI);
    const data = ctx.getImageData(0, 0, LEBAR, TINGGI);
    const p = data.data;
    for (let i = 0; i < p.length; i += 4) {
      const r = p[i], g = p[i + 1], b = p[i + 2];
      const lebihan = g - Math.max(r, b); // berapa "hijau" piksel ini
      if (lebihan > 60) {
        p[i + 3] = 0; // latar hijau → lut sinar
      } else if (lebihan > 20) {
        p[i + 3] = Math.round(255 * (1 - (lebihan - 20) / 40)); // tepi lembut
        p[i + 1] = Math.max(r, b); // buang limpahan hijau di tepi
      }
    }
    ctx.putImageData(data, 0, 0);
  }, []);

  return (
    <AbsoluteFill>
      {latar ? <Img src={staticFile(latar)} style={{ width: "100%", height: "100%", objectFit: "cover" }} /> : <LatarEmas terang />}
      <AbsoluteFill style={{ opacity: 0 }}>
        <OffthreadVideo src={staticFile(video)} onVideoFrame={onVideoFrame} style={{ width: LEBAR, height: TINGGI, objectFit: "cover" }} />
      </AbsoluteFill>
      <AbsoluteFill>
        <canvas ref={kanvas} width={LEBAR} height={TINGGI} style={{ width: "100%", height: "100%", filter: "drop-shadow(0 20px 40px rgba(0,0,0,0.5))" }} />
      </AbsoluteFill>
      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 240 }}>
        <div
          style={{
            fontFamily: fonSans,
            fontWeight: 800,
            fontSize: 62,
            color: warna.hitam,
            background: warna.krim,
            padding: "22px 44px",
            borderRadius: 24,
            border: `5px solid ${warna.emas}`,
            textAlign: "center",
            maxWidth: 900,
            transform: `scale(${masuk}) rotate(-2deg)`,
          }}
        >
          {kapsyen}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
