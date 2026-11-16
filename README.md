# Sisrose-video-emas-
Projek video emas Umar Jewelleries menggunakan Claude AI.

Templat video menegak (1080x1920, sesuai TikTok / Instagram Reels / Shorts) yang
setiap kali dirender akan mengandungi 7 efek:

| Babak | Efek |
|---|---|
| Peralihan | **Zoom Through Cut** (antara setiap babak) |
| 1 | **Headline Wall** — dinding tajuk + tajuk utama |
| 2 | **Orbit** — produk di tengah, label berpusing |
| 3 | **Glass** — kad kaca harga & butiran |
| 4 | **Green Screen** — video Kak Ros tanpa latar hijau |
| 5 | **Paper Cut** — promosi gaya kertas berlapis |
| 6 | **Checklist** — senarai ✓ + ajakan WhatsApp |

## Cara guna
1. Tukar teks dalam `src/kandungan.ts`.
2. Letak gambar produk / video green screen dalam folder `public/`.
3. `npm install` (sekali sahaja), kemudian `npm run render`.
4. Video siap di `out/video-emas.mp4`. Untuk tengok & ubah secara langsung: `npm run studio`.

**Tip rakam green screen:** latar hijau rata tanpa bayang, cahaya terang, elak pakai baju hijau.
