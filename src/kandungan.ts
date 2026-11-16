/**
 * ============================================================
 *  KANDUNGAN VIDEO — Kak Ros ubah teks di sini sahaja.
 *  Semua 7 efek akan keluar secara automatik setiap kali render.
 * ============================================================
 *
 *  Gambar / video: letak fail dalam folder `public/`, kemudian
 *  tulis nama fail sahaja (contoh: "cincin.png").
 */
export const kandungan = {
  jenama: "Umar Jewelleries",

  // Panjang setiap babak (saat) dan panjang peralihan Zoom Through (saat)
  saatSetiapBabak: 3.6,
  saatPeralihan: 0.6,

  // 1) HEADLINE WALL — pembuka video (hook)
  headlineWall: {
    tajukUtama: "EMAS 916\nKOLEKSI BARU",
    perkataanDinding: ["EMAS 916", "TULEN", "BERKILAU", "ELEGAN", "BARU", "HADIAH", "PELABURAN", "EKSKLUSIF"],
  },

  // 2) ORBIT — produk di tengah, label berpusing mengelilinginya
  orbit: {
    namaProduk: "Cincin Bunga Emas",
    gambarProduk: "", // contoh: "cincin.png" (kosong = guna cincin lukisan)
    labelOrbit: ["916", "Ringan", "Berkilat", "Muat Semua Jari", "Tahan Lama"],
  },

  // 3) GLASS — kad kaca (glassmorphism) untuk harga & butiran
  glass: {
    tajuk: "Harga Istimewa",
    harga: "RM 1,280",
    butiran: ["Berat: 3.2g", "Ketulenan: 916", "Saiz: 6 – 18"],
  },

  // 4) GREEN SCREEN — video Kak Ros (latar hijau akan dibuang)
  greenScreen: {
    video: "greenscreen-contoh.mp4", // ganti dengan video Kak Ros berlatar hijau
    latar: "", // gambar latar belakang (kosong = latar emas)
    kapsyen: "Kak Ros pilih sendiri untuk anda!",
  },

  // 5) PAPER CUT — promosi gaya potongan kertas berlapis
  paperCut: {
    baris: ["PROMO", "HUJUNG", "MINGGU", "-20%"],
  },

  // 6) CHECKLIST — kenapa beli + ajakan bertindak (CTA)
  checklist: {
    tajuk: "Kenapa Pilih Kami?",
    senarai: ["Emas 916 tulen", "Boleh trade-in", "Pos seluruh Malaysia", "Ansuran tersedia"],
    cta: "WhatsApp Kak Ros sekarang!",
  },
};

export type Kandungan = typeof kandungan;
