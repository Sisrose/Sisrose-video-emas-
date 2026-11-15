"""Caption: teks DIBETULKAN manual, masa dari Whisper pada audio akhir (voice_edit.wav).
Guna: python3 make_captions.py transcript_edit.json edit16k.raw captions.json"""
import sys, json, numpy as np
tj, raw, out = sys.argv[1:4]
ws = [w for s in json.load(open(tj)) for w in s["words"]]
a = np.fromfile(raw, dtype=np.float32); SR = 16000
def db(t0, t1):
    x = a[int(t0*SR):int(t1*SR)]; return 20*np.log10(np.sqrt((x**2).mean())+1e-9) if len(x) else -99
# Betulkan permulaan perkataan: frame pertama yang bersuara (> -32 dB)
T = []
for w in ws:
    s, e = w["s"], w["e"]; t = s
    while t < e - 0.04 and db(t, t+0.02) < -32: t += 0.02
    T.append([round(t, 2), round(e, 2)])
# (indeks perkataan pertama, indeks terakhir, teks caption dibetulkan; *kata* = sorotan emas)
P = [
 (0, 3, "Kepada semua dealer-dealer"),
 (4, 5, "*UMAR* *JEWELLERIES*,"),
 (6, 10, "jom kita ramai-ramai meriahkan"),
 (11, 13, "*Malam* *Mega* *Rezeki*"),
 (14, 15, "*UMAR* *JEWELLERIES*"),
 (16, 20, "pada *19* *Disember* *2026* nanti."),
 (21, 26, "Pada malam tu kita akan berkumpul"),
 (27, 31, "di *HQ* *Bertam*, Pulau Pinang."),
 (32, 37, "Malam tu bukan sekadar tentang hadiah,"),
 (38, 41, "tapi juga tentang *kenangan*,"),
 (42, 44, "*persahabatan* dan *ukhuwah*"),
 (45, 50, "yang kita bina sepanjang bersama *UJ*."),
 (51, 55, "Tapi mestilah kita teruja juga,"),
 (56, 60, "sebab ada hadiah yang menarik"),
 (61, 64, "iaitu *Grand* *Prize*, *Myvi*,"),
 (65, 69, "lepas tu *3* *buah* *motor*,"),
 (70, 72, "*goldbar*, *barang* *kemas*"),
 (73, 76, "dan macam-macam lagi."),
 (77, 80, "Tiket hanyalah *RM20* seorang,"),
 (81, 86, "kanak-kanak di bawah 6 tahun"),
 (87, 88, "*percuma* je."),
 (89, 91, "Jangan lupa tau,"),
 (92, 95, "pakai pakaian *Melayu* *Klasik*."),
 (96, 98, "Jom kita meriahkan"),
 (99, 102, "malam ni bersama-sama."),
 (103, 106, "Dealer dari negeri mana"),
 (107, 109, "yang akan hadir?"),
 (110, 114, "Cuba komen negeri masing-masing."),
 (115, 115, "*Jom!*"),
]
caps = []
for k, (i0, i1, text) in enumerate(P):
    toks = text.split(" ")
    idx = list(range(i0, i1+1))
    # padankan token caption dengan masa perkataan (gabung "dealer-dealer" dsb.)
    n = len(idx); m = len(toks)
    words = []
    for j, tok in enumerate(toks):
        wi = idx[min(n-1, round(j*(n-1)/(m-1)) if m > 1 else 0)] if m != n else idx[j]
        hl = tok.startswith("*")
        words.append({"t": T[wi][0], "w": tok.replace("*", ""), "hl": hl})
    for j in range(1, len(words)):  # masa mesti menaik
        words[j]["t"] = max(words[j]["t"], words[j-1]["t"])
    start = T[i0][0] - 0.06
    end = T[i1][1] + 0.35
    caps.append({"s": round(start, 2), "e": round(end, 2), "words": words})
for k in range(len(caps)-1):
    caps[k]["e"] = min(caps[k]["e"], caps[k+1]["s"])
json.dump(caps, open(out, "w"), ensure_ascii=False, indent=1)
for c in caps: print(f"{c['s']:6.2f}-{c['e']:6.2f}", " ".join(w["w"] for w in c["words"]))
