# Build v1 — Malam Mega Rezeki UMAR JEWELLERIES 2026

Output: `output/Malam_Mega_Rezeki_UMAR_JEWELLERIES_2026.mp4` (1080x1920, 30fps, H.264 + AAC, ~53.3s)

## Audio (suara asal sahaja — tiada muzik/SFX)
- `build/edit_audio.py` -> `build/edl.json` (senarai klip, masa asal) -> `build/voice_edit.wav`
- Dibuang: senyap awal/akhir; "mana tau, di lokasinya dekat"; take pertama "Jom kita meriahkan malam ni bersama-sama" + "Okey" sebelum take kedua (dikesan semasa QA)
- Jeda > 0.40s dipendekkan ke ~0.28s; fade 12ms di setiap sambungan
- Loudness dinormalkan ke -14 LUFS (aras TikTok); tiada EQ/efek lain pada suara
- 61.0s -> 50.0s; disahkan dengan transkrip semula Whisper (`build/transcript_edit.json`)

## Caption
- `build/make_captions.py` -> `build/captions.json`; teks dibetulkan manual, masa per perkataan dari audio akhir
- UMAR JEWELLERIES dieja tepat setiap kali; "UJ" kekal; "ukhuwah"; "goldbar"; "Grand Prize"; "Myvi"
- Animasi: perkataan muncul ikut suara, perkataan aktif disorot

## Visual (`build/video.html`, render `build/render.js`)
| Masa | Adegan |
|---|---|
| 0-11.4 | Logo, "Jemputan Khas untuk Semua Dealer", tajuk Malam Mega Rezeki, ribbon UMAR JEWELLERIES 2026, kad tarikh 19 Dis 2026 · Sabtu · 7ptg-11.30mlm |
| 11.4-15.9 | Kad lokasi HQ UMAR JEWELLERIES + alamat penuh |
| 15.9-23.0 | Kenangan · Persahabatan · Ukhuwah, "bersama UJ" |
| 23.0-35.7 | Hadiah menarik -> Myvi 1.5X -> Motosikal -> senarai penuh 5 hadiah |
| 35.7-44.0 | Tiket RM20 seorang, jamuan makan, bawah 6 tahun PERCUMA -> Tema Melayu Klasik |
| 44.0-50.0 | Jom meriahkan, "Dealer dari negeri mana? Komen negeri anda", ringkasan tarikh/masa/tempat |
| 50.05-53.3 | Ending Sis Rose: foto asal (crop atas teks bercetak, tiada perubahan wajah), latar sage/krim/ungu lembut/champagne gold, SIS ROSE / ICON LEADER UMAR JEWELLERIES |

Gambar produk/visual dipotong (crop CSS) dari poster asal; tiada imej dijana.
Font (OFL, Google Fonts): Cinzel, Playfair Display, Montserrat, Great Vibes.

## Bina semula
python3 build/edit_audio.py <m4a> <raw16k> build ; python3 build/make_captions.py ... ; node build/render.js output/<nama>.mp4
