import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { LatarEmas } from "../components/LatarEmas";
import { Produk } from "../components/Produk";
import { fonSans, fonSerif, warna } from "../tema";

/** EFEK 3: ORBIT — produk di tengah, label berpusing 3D mengelilinginya. */
export const Orbit: React.FC<{ namaProduk: string; gambarProduk: string; labelOrbit: string[] }> = ({ namaProduk, gambarProduk, labelOrbit }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const masuk = spring({ frame, fps, config: { damping: 14 } });
  const sudutAsas = frame * 1.6;
  const rx = 400;
  const ry = 140;

  const label = labelOrbit.map((t, i) => {
    const sudut = ((sudutAsas + (360 / labelOrbit.length) * i) * Math.PI) / 180;
    const z = Math.cos(sudut); // 1 = depan, -1 = belakang
    return { t, x: Math.sin(sudut) * rx, y: z * ry, z };
  });

  const papar = (depan: boolean) =>
    label
      .filter((l) => (l.z >= 0) === depan)
      .map((l) => (
        <div
          key={l.t}
          style={{
            position: "absolute",
            left: "50%",
            top: "50%",
            transform: `translate(-50%, -50%) translate(${l.x}px, ${l.y + 40}px) scale(${interpolate(l.z, [-1, 1], [0.6, 1.15])})`,
            opacity: interpolate(l.z, [-1, 1], [0.35, 1]) * masuk,
            filter: `blur(${interpolate(l.z, [-1, 1], [3, 0])}px)`,
            padding: "18px 38px",
            borderRadius: 999,
            border: `3px solid ${warna.emas}`,
            background: "rgba(20,15,8,0.6)",
            color: warna.emasTerang,
            fontFamily: fonSans,
            fontWeight: 700,
            fontSize: 48,
            whiteSpace: "nowrap",
          }}
        >
          {l.t}
        </div>
      ));

  return (
    <AbsoluteFill>
      <LatarEmas />
      {/* gelang orbit */}
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
        <div style={{ width: rx * 2, height: ry * 2, borderRadius: "50%", border: `2px dashed ${warna.emas}55`, transform: "translateY(40px)" }} />
      </AbsoluteFill>
      {papar(false)}
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
        <div style={{ transform: `scale(${masuk}) rotate(${Math.sin(frame / 20) * 6}deg)`, filter: "drop-shadow(0 30px 50px rgba(232,195,106,0.45))" }}>
          <Produk gambar={gambarProduk} saiz={520} />
        </div>
      </AbsoluteFill>
      {papar(true)}
      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 260 }}>
        <div style={{ fontFamily: fonSerif, fontSize: 92, fontWeight: 800, color: warna.krim, textAlign: "center", opacity: masuk, transform: `translateY(${(1 - masuk) * 80}px)` }}>
          {namaProduk}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
