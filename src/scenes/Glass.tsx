import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Produk } from "../components/Produk";
import { fonSans, fonSerif, warna } from "../tema";

/** EFEK 4: GLASS — kad kaca lut sinar (glassmorphism) dengan kilauan cahaya. */
export const Glass: React.FC<{ tajuk: string; harga: string; butiran: string[]; gambarProduk: string }> = ({ tajuk, harga, butiran, gambarProduk }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const masuk = spring({ frame, fps, config: { damping: 16 } });
  const kilau = interpolate(frame % 75, [0, 75], [-120, 220]);

  const gelembung = [
    { x: 15, y: 20, s: 420, c: warna.emas },
    { x: 80, y: 35, s: 360, c: warna.merahJambu },
    { x: 30, y: 75, s: 480, c: warna.emasGelap },
    { x: 85, y: 85, s: 300, c: warna.emasTerang },
  ];

  return (
    <AbsoluteFill style={{ background: `linear-gradient(160deg, #2b1e0a, ${warna.hitam})` }}>
      {gelembung.map((g, i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            left: `${g.x + Math.sin((frame + i * 30) / 30) * 6}%`,
            top: `${g.y + Math.cos((frame + i * 20) / 35) * 5}%`,
            width: g.s,
            height: g.s,
            marginLeft: -g.s / 2,
            marginTop: -g.s / 2,
            borderRadius: "50%",
            background: g.c,
            filter: "blur(10px)",
          }}
        />
      ))}
      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center", paddingTop: 260 }}>
        <div style={{ filter: "drop-shadow(0 30px 40px rgba(0,0,0,0.5))", transform: `translateY(${(1 - masuk) * -200}px)` }}>
          <Produk gambar={gambarProduk} saiz={380} />
        </div>
      </AbsoluteFill>
      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 280 }}>
        <div
          style={{
            position: "relative",
            overflow: "hidden",
            width: 860,
            padding: "60px 70px",
            borderRadius: 56,
            background: "rgba(255,255,255,0.14)",
            border: "2px solid rgba(255,255,255,0.45)",
            backdropFilter: "blur(28px) saturate(160%)",
            WebkitBackdropFilter: "blur(28px) saturate(160%)",
            boxShadow: "0 30px 80px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.6)",
            transform: `translateY(${(1 - masuk) * 400}px) rotateX(${(1 - masuk) * 30}deg)`,
            opacity: masuk,
          }}
        >
          <div style={{ position: "absolute", top: 0, bottom: 0, left: `${kilau}%`, width: 120, background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.45), transparent)", transform: "skewX(-20deg)" }} />
          <div style={{ fontFamily: fonSans, fontSize: 44, color: warna.krim, letterSpacing: 4, textTransform: "uppercase" }}>{tajuk}</div>
          <div style={{ fontFamily: fonSerif, fontSize: 140, fontWeight: 900, color: warna.emasTerang, margin: "10px 0 24px" }}>{harga}</div>
          {butiran.map((b, i) => {
            const m = spring({ frame: frame - 12 - i * 6, fps, config: { damping: 18 } });
            return (
              <div key={b} style={{ fontFamily: fonSans, fontSize: 46, color: "white", opacity: m, transform: `translateX(${(1 - m) * 60}px)`, marginTop: 10 }}>
                ✦ {b}
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
