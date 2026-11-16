import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { fonSans, warna } from "../tema";

/** Bentuk "bukit" kertas berlapis dengan tepi beralun. */
const Lapisan: React.FC<{ warnaKertas: string; tinggi: number; fasa: number; tunda: number }> = ({ warnaKertas, tinggi, fasa, tunda }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const naik = spring({ frame: frame - tunda, fps, config: { damping: 15 } });
  const titik = Array.from({ length: 13 }).map((_, i) => {
    const x = (i / 12) * 1080;
    const y = 60 + Math.sin(i * 0.9 + fasa + frame / 25) * 40;
    return `${x},${y}`;
  });
  return (
    <svg
      width={1080}
      height={tinggi + 120}
      viewBox={`0 0 1080 ${tinggi + 120}`}
      style={{ position: "absolute", bottom: 0, transform: `translateY(${(1 - naik) * (tinggi + 150)}px)`, filter: "drop-shadow(0 -12px 14px rgba(0,0,0,0.35))" }}
    >
      <polygon points={`0,${tinggi + 120} ${titik.join(" ")} 1080,${tinggi + 120}`} fill={warnaKertas} />
    </svg>
  );
};

/** EFEK 6: PAPER CUT — lapisan kertas bertingkat + teks potongan kertas. */
export const PaperCut: React.FC<{ baris: string[] }> = ({ baris }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const lapisan = ["#F7E3B5", "#EDC97A", "#D9A84A", "#B98325", "#8E5E14"];

  return (
    <AbsoluteFill style={{ background: "#FBF1DC", overflow: "hidden" }}>
      {/* tekstur kertas */}
      <AbsoluteFill style={{ backgroundImage: "repeating-linear-gradient(45deg, rgba(0,0,0,0.025) 0 2px, transparent 2px 6px)" }} />
      {lapisan.map((w, i) => (
        <Lapisan key={w} warnaKertas={w} tinggi={1500 - i * 260} fasa={i * 1.7} tunda={i * 4} />
      ))}
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", gap: 26, paddingBottom: 300 }}>
        {baris.map((t, i) => {
          const m = spring({ frame: frame - 14 - i * 6, fps, config: { damping: 11 } });
          const condong = i % 2 === 0 ? -4 : 3;
          const akhir = i === baris.length - 1;
          return (
            <div
              key={i}
              style={{
                fontFamily: fonSans,
                fontWeight: 900,
                fontSize: akhir ? 230 : 120,
                color: akhir ? "white" : warna.hitam,
                background: akhir ? "#B3261E" : "white",
                padding: "6px 46px",
                transform: `rotate(${condong}deg) scale(${m}) translateY(${interpolate(m, [0, 1], [80, 0])}px)`,
                boxShadow: "8px 10px 0 rgba(0,0,0,0.25)",
                clipPath: "polygon(1% 4%, 99% 0%, 100% 92%, 96% 100%, 3% 97%, 0% 50%)",
              }}
            >
              {t}
            </div>
          );
        })}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
