import { Img, staticFile } from "remotion";

/** Gambar produk dari folder public/, atau cincin emas lukisan jika tiada gambar. */
export const Produk: React.FC<{ gambar?: string; saiz: number }> = ({ gambar, saiz }) => {
  if (gambar) {
    return <Img src={staticFile(gambar)} style={{ width: saiz, height: saiz, objectFit: "contain" }} />;
  }
  return (
    <svg width={saiz} height={saiz} viewBox="0 0 200 200">
      <defs>
        <linearGradient id="emas" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#8a5a12" />
          <stop offset="0.35" stopColor="#E8C36A" />
          <stop offset="0.5" stopColor="#FFF1C4" />
          <stop offset="0.7" stopColor="#D9A93F" />
          <stop offset="1" stopColor="#7a4e0e" />
        </linearGradient>
        <radialGradient id="permata" cx="0.4" cy="0.35" r="0.7">
          <stop offset="0" stopColor="#ffffff" />
          <stop offset="0.5" stopColor="#ffe9f0" />
          <stop offset="1" stopColor="#d79bb0" />
        </radialGradient>
      </defs>
      <ellipse cx="100" cy="122" rx="62" ry="58" fill="none" stroke="url(#emas)" strokeWidth="16" />
      {[0, 72, 144, 216, 288].map((r) => (
        <ellipse key={r} cx="100" cy="52" rx="11" ry="20" fill="url(#emas)" transform={`rotate(${r} 100 70)`} />
      ))}
      <circle cx="100" cy="70" r="13" fill="url(#permata)" stroke="#b8862b" strokeWidth="2" />
    </svg>
  );
};
