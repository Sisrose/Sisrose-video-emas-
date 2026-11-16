"""Bina audio akhir: suara asal Kak Ros (dipotong ikut timeline) + muzik energetic
(disintesis, bebas hak cipta) + SFX whoosh/sparkle, dengan ducking automatik."""
import json, subprocess, sys, wave
import numpy as np
from timeline import SEGMENTS, OUT_DUR, TRANSITIONS_OUT, POPS_OUT, END_CARD_OUT

SR = 44100
src, out_wav = sys.argv[1], sys.argv[2]

# ---------- suara ----------
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-ac", "1", "-ar", str(SR),
                      "-f", "s16le", "-"], capture_output=True, check=True).stdout
voice_src = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
parts = []
for a, b in SEGMENTS:
    seg = voice_src[int(a * SR):int(b * SR)].copy()
    f = int(0.02 * SR)
    seg[:f] *= np.linspace(0, 1, f); seg[-f:] *= np.linspace(1, 0, f)
    parts.append(seg)
voice = np.concatenate(parts)
N = int(OUT_DUR * SR)
voice = np.pad(voice, (0, max(0, N - len(voice))))[:N]
# high-pass ringan + normalise
voice = voice - np.convolve(voice, np.ones(200) / 200, mode="same")
voice *= 0.5 / (np.percentile(np.abs(voice), 99.9) + 1e-9)

# ---------- muzik (124 BPM, I-V-vi-IV dalam C) ----------
t_all = np.arange(N) / SR
bpm = 124; beat = 60 / bpm
rng = np.random.default_rng(7)
music = np.zeros(N, np.float32)

def add(sig, start):
    i = int(start * SR)
    if i >= N: return
    e = min(N, i + len(sig)); music[i:e] += sig[:e - i]

def kick():
    t = np.arange(int(0.35 * SR)) / SR
    f = 45 + 90 * np.exp(-t * 30)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9) * 0.9).astype(np.float32)

def noise_hit(dur, decay, hp):
    n = rng.standard_normal(int(dur * SR)).astype(np.float32)
    for _ in range(hp): n = np.diff(n, prepend=0)
    t = np.arange(len(n)) / SR
    return n * np.exp(-t * decay) / (np.abs(n).max() + 1e-9)

def tone(freq, dur, decay, harm=(1, .5, .25)):
    t = np.arange(int(dur * SR)) / SR
    s = sum(a * np.sin(2 * np.pi * freq * (k + 1) * t) for k, a in enumerate(harm))
    return (s * np.exp(-t * decay)).astype(np.float32)

K, CL, HH = kick(), noise_hit(0.2, 18, 1) * 0.35, noise_hit(0.06, 60, 2) * 0.12
note = lambda m: 440 * 2 ** ((m - 69) / 12)
chords = [[48, 52, 55], [43, 47, 50], [45, 48, 52], [41, 45, 48]]  # C G Am F
n_beats = int(OUT_DUR / beat) + 1
pump = np.ones(N, np.float32)
for b in range(n_beats):
    tb = b * beat
    ch = chords[(b // 4) % 4]
    add(K, tb)
    i = int(tb * SR); L = int(0.3 * SR)
    if i < N:
        e = min(N, i + L); pump[i:e] = np.minimum(pump[i:e], 0.35 + 0.65 * np.linspace(0, 1, L)[:e - i])
    if b % 2 == 1: add(CL, tb)
    add(HH, tb + beat / 2); add(HH * 0.6, tb + beat * 0.25 if b % 4 == 3 else tb + beat * 0.75)
    # bass offbeat 8ths
    add(tone(note(ch[0] - 12), beat / 2, 6, (1, .6, .3, .15)) * 0.32, tb + beat / 2)
    # pluck arp 16ths
    arp = [ch[0] + 24, ch[1] + 24, ch[2] + 24, ch[1] + 24]
    for k in range(4):
        add(tone(note(arp[k]), 0.25, 14, (1, .3, .1)) * 0.10, tb + k * beat / 4)
# pad
for bar in range(n_beats // 4 + 1):
    ch = chords[bar % 4]
    for m in ch:
        t = np.arange(int(4 * beat * SR)) / SR
        s = (np.sin(2 * np.pi * note(m + 12) * t) + 0.3 * np.sin(2 * np.pi * note(m + 24) * t + .3))
        env = np.minimum(1, t / 0.1) * np.minimum(1, (4 * beat - t) / 0.1)
        add((s * env * 0.045).astype(np.float32), bar * 4 * beat)
music *= pump  # sidechain pumping
music /= np.abs(music).max() + 1e-9

# ---------- SFX ----------
sfx = np.zeros(N, np.float32)
def add_sfx(sig, start):
    i = int(start * SR)
    if 0 <= i < N:
        e = min(N, i + len(sig)); sfx[i:e] += sig[:e - i]
def whoosh():
    L = int(0.45 * SR); n = rng.standard_normal(L).astype(np.float32)
    n = np.convolve(n, np.ones(6) / 6, "same")
    t = np.linspace(0, 1, L)
    return n * np.sin(np.pi * t) ** 2 * 0.22
def sparkle():
    return (tone(2093, 0.5, 7, (1, .2)) + 0.6 * tone(3136, 0.5, 9, (1,))) * 0.10
def impact():
    t = np.arange(int(1.2 * SR)) / SR
    f = 35 + 70 * np.exp(-t * 6)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3) * 0.6).astype(np.float32) + noise_hit(1.2, 5, 1) * 0.12
for tt in TRANSITIONS_OUT: add_sfx(whoosh(), tt - 0.22)
for tt in POPS_OUT: add_sfx(sparkle(), tt)
add_sfx(impact(), END_CARD_OUT)

# ---------- ducking ----------
win = int(0.05 * SR)
env = np.sqrt(np.convolve(voice ** 2, np.ones(win) / win, "same"))
speaking = (env > 0.02).astype(np.float32)
sm = int(0.25 * SR)
speaking = np.convolve(speaking, np.ones(sm) / sm, "same")
mgain = 0.30 - 0.19 * np.clip(speaking * 1.5, 0, 1)
# fade out muzik di hujung
fo = int(1.0 * SR); mgain[-fo:] *= np.linspace(1, 0, fo)
mix = voice + music * mgain + sfx
mix /= max(1.0, np.abs(mix).max() / 0.95)
with wave.open(out_wav, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("audio ok", OUT_DUR)
