# Projek Video Emas — Umar Jewelleries (Kak Ros)

Bercakap dengan Kak Ros dalam Bahasa Melayu yang mesra dan mudah.

## PERATURAN WAJIB: setiap video mesti ada SEMUA efek ini

Setiap kali Kak Ros minta video baru, video itu MESTI mengandungi kesemua efek berikut.
Jangan buang mana-mana efek, walaupun video pendek:

1. **Zoom Through Cut** — peralihan antara setiap babak (`src/transitions/zoomThrough.tsx`)
2. **Headline Wall** — babak pembuka / hook (`src/scenes/HeadlineWall.tsx`)
3. **Orbit** — produk di tengah, label berpusing (`src/scenes/Orbit.tsx`)
4. **Glass** — kad kaca untuk harga & butiran (`src/scenes/Glass.tsx`)
5. **Green Screen** — video Kak Ros, latar hijau dibuang (`src/scenes/GreenScreen.tsx`)
6. **Paper Cut** — promosi gaya kertas berlapis (`src/scenes/PaperCut.tsx`)
7. **Checklist** — senarai ✓ + CTA penutup (`src/scenes/Checklist.tsx`)

## Cara buat video baru

1. Ubah teks / nama fail dalam `src/kandungan.ts` sahaja (kecuali Kak Ros minta reka bentuk baru).
2. Gambar produk dan video green screen Kak Ros diletak dalam `public/`.
3. Render: `npm run render` → hasil di `out/video-emas.mp4` (1080x1920, 9:16 untuk TikTok/Reels).
4. Hantar fail video kepada Kak Ros.

Jika Kak Ros tidak beri video green screen, guna `public/greenscreen-contoh.mp4` dan beritahu dia
bahawa babak itu masih guna video contoh.
