"""Bina senarai potongan audio (masa asal) dan render audio akhir.
Guna: python3 edit_audio.py <audio_asal> <raw16k_mono_f32> <out_dir>"""
import sys, json, subprocess, numpy as np
src, raw, out = sys.argv[1:4]
a = np.fromfile(raw, dtype=np.float32); SR = 16000
DUR = len(a) / SR
# Keputusan dikunci (lihat 01-transkrip-draf.md)
REMOVE = [(0.0, 0.98),          # senyap awal
          (15.32, 17.39),       # "mana tau, di lokasinya dekat"
          (49.20, 54.16),       # take pertama "Jom kita meriahkan..." (ulangan) + "Okey" sebelum take kedua
          (60.32, DUR)]         # senyap akhir
# Kesan senyap (RMS 20ms < -30 dB), abaikan bunyi < 60ms
fr = 0.02; n = int(DUR / fr)
db = np.array([20*np.log10(np.sqrt((a[int(i*fr*SR):int((i+1)*fr*SR)]**2).mean())+1e-9) for i in range(n)])
sil = db < -30
i = 0; runs = []
while i < n:
    if sil[i]:
        j = i
        while j < n and (sil[j] or (not sil[j:j+3].all() and sil[j:min(n,j+4)].any() and False)):
            j += 1
        runs.append([i*fr, j*fr]); i = j
    else: i += 1
merged = []
for r in runs:
    if merged and r[0] - merged[-1][1] <= 0.06: merged[-1][1] = r[1]
    else: merged.append(r)
MAXP, KEEP = 0.40, 0.14   # jeda > 0.40s dipendekkan, kekal 0.14s tiap sisi (~0.28s)
for s, e in merged:
    if e - s > MAXP: REMOVE.append((s + KEEP, e - KEEP))
REMOVE.sort()
rm = []
for s, e in REMOVE:
    if rm and s <= rm[-1][1]: rm[-1][1] = max(rm[-1][1], e)
    else: rm.append([s, e])
keep = []; t = 0.0
for s, e in rm:
    if s > t: keep.append([round(t, 3), round(s, 3)])
    t = max(t, e)
if t < DUR: keep.append([round(t, 3), round(DUR, 3)])
keep = [k for k in keep if k[1] - k[0] > 0.03]
json.dump({"keep": keep}, open(f"{out}/edl.json", "w"), indent=1)
# Render: setiap klip fade 12ms masuk/keluar untuk elak klik, kemudian concat
F = 0.012; parts = []; fc = []
for k, (s, e) in enumerate(keep):
    d = e - s
    fc.append(f"[0:a]atrim={s}:{e},asetpts=N/SR/TB,afade=t=in:d={F},afade=t=out:st={d-F:.4f}:d={F}[p{k}]")
    parts.append(f"[p{k}]")
fc.append("".join(parts) + f"concat=n={len(keep)}:v=0:a=1[cat]")
fc.append("[cat]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[outa]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex", ";".join(fc),
                "-map", "[outa]", "-c:a", "pcm_s16le", "-ac", "2", f"{out}/voice_edit.wav"], check=True)
tot = sum(e - s for s, e in keep)
print(f"klip={len(keep)} asal={DUR:.2f}s akhir={tot:.2f}s")
