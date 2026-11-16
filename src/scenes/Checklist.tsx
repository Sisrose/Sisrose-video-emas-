import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { LatarEmas } from "../components/LatarEmas";
import { fonSans, fonSerif, kecerunanEmas, warna } from "../tema";

/** EFEK 7: CHECKLIST — senarai ditanda ✓ satu demi satu, diakhiri CTA. */
export const Checklist: React.FC<{ tajuk: string; senarai: string[]; cta: string }> = ({ tajuk, senarai, cta }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const jarak = senarai.length > 5 ? 9 : 14; // jarak antara setiap tanda ✓ (frame)
  const ctaMasuk = spring({ frame: frame - (12 + senarai.length * jarak), fps, config: { damping: 10 } });

  return (
    <AbsoluteFill>
      <LatarEmas />
      <AbsoluteFill style={{ padding: "260px 90px", gap: 46 }}>
        <div style={{ fontFamily: fonSerif, fontWeight: 900, fontSize: 104, color: warna.emasTerang, marginBottom: 20 }}>{tajuk}</div>
        {senarai.map((item, i) => {
          const mula = 12 + i * jarak;
          const m = spring({ frame: frame - mula, fps, config: { damping: 14 } });
          const tanda = interpolate(frame - mula - 5, [0, 10], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          return (
            <div key={item} style={{ display: "flex", alignItems: "center", gap: 36, opacity: m, transform: `translateX(${(1 - m) * -120}px)` }}>
              <svg width={96} height={96} viewBox="0 0 100 100" style={{ flexShrink: 0 }}>
                <rect x="6" y="6" width="88" height="88" rx="22" fill="none" stroke={warna.emas} strokeWidth="7" />
                <path d="M26 52 L44 70 L76 32" fill="none" stroke={warna.emasTerang} strokeWidth="11" strokeLinecap="round" strokeLinejoin="round" strokeDasharray="80" strokeDashoffset={80 * (1 - tanda)} />
              </svg>
              <div style={{ fontFamily: fonSans, fontWeight: 600, fontSize: 60, color: warna.krim }}>{item}</div>
            </div>
          );
        })}
      </AbsoluteFill>
      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 230 }}>
        <div
          style={{
            fontFamily: fonSans,
            fontWeight: 800,
            fontSize: 58,
            color: warna.hitam,
            backgroundImage: kecerunanEmas,
            padding: "30px 56px",
            borderRadius: 999,
            transform: `scale(${ctaMasuk * (1 + Math.sin(frame / 5) * 0.03)})`,
            boxShadow: "0 0 60px rgba(232,195,106,0.6)",
          }}
        >
          {cta}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
