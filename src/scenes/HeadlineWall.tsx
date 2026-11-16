import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { LatarEmas } from "../components/LatarEmas";
import { fonSans, fonSerif, kecerunanEmas, warna } from "../tema";

/** EFEK 2: HEADLINE WALL — dinding tajuk bergerak + tajuk utama "pop". */
export const HeadlineWall: React.FC<{ tajukUtama: string; perkataanDinding: string[] }> = ({ tajukUtama, perkataanDinding }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const baris = 11;
  const pop = spring({ frame: frame - 10, fps, config: { damping: 12, mass: 0.7 } });

  return (
    <AbsoluteFill>
      <LatarEmas />
      <AbsoluteFill style={{ transform: "rotate(-12deg) scale(1.35)", justifyContent: "center", gap: 18, opacity: 0.9 }}>
        {Array.from({ length: baris }).map((_, i) => {
          const arah = i % 2 === 0 ? -1 : 1;
          const x = arah * frame * 6 - 600 + (i * 137) % 400;
          const teks = Array.from({ length: 10 }).map((__, j) => perkataanDinding[(i + j) % perkataanDinding.length]);
          return (
            <div key={i} style={{ display: "flex", gap: 40, whiteSpace: "nowrap", transform: `translateX(${x}px)` }}>
              {teks.map((t, j) => (
                <span
                  key={j}
                  style={{
                    fontFamily: fonSans,
                    fontWeight: 900,
                    fontSize: 110,
                    color: (i + j) % 3 === 0 ? warna.emas : "transparent",
                    WebkitTextStroke: `2px ${warna.emas}`,
                    opacity: (i + j) % 3 === 0 ? 0.55 : 0.3,
                  }}
                >
                  {t}
                </span>
              ))}
            </div>
          );
        })}
      </AbsoluteFill>
      <AbsoluteFill style={{ background: "radial-gradient(circle, rgba(20,15,8,0.85) 25%, rgba(20,15,8,0) 70%)" }} />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
        <div
          style={{
            transform: `scale(${interpolate(pop, [0, 1], [3, 1])})`,
            opacity: pop,
            fontFamily: fonSerif,
            fontWeight: 900,
            fontSize: 150,
            lineHeight: 1.05,
            textAlign: "center",
            whiteSpace: "pre-line",
            backgroundImage: kecerunanEmas,
            backgroundSize: "200% 100%",
            backgroundPosition: `${(frame * 2) % 200}% 0`,
            WebkitBackgroundClip: "text",
            color: "transparent",
            filter: "drop-shadow(0 10px 30px rgba(0,0,0,0.8))",
            padding: "0 40px",
          }}
        >
          {tajukUtama}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
