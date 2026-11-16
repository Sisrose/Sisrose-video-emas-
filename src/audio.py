"""Muzik latar instrumental (piano + pad) dan sound effect — dijana sepenuhnya, tiada suara."""
import numpy as np
import wave
import sys

SR = 44100
DUR = 45.0
rng = np.random.default_rng(7)


def note_hz(n):  # MIDI -> Hz
    return 440.0 * 2 ** ((n - 69) / 12)


def piano(freq, dur, vel=0.5):
    t = np.arange(int(dur * SR)) / SR
    sig = np.zeros_like(t)
    for h, a in [(1, 1.0), (2, 0.45), (3, 0.22), (4, 0.12), (5, 0.06), (6, 0.03)]:
        f = freq * h * (1 + 0.0004 * h * h)
        sig += a * np.sin(2 * np.pi * f * t) * np.exp(-t * (1.2 + 0.9 * h))
    att = np.minimum(1, t / 0.006)
    return sig * att * vel


def pad(freqs, dur, vel=0.12):
    t = np.arange(int(dur * SR)) / SR
    sig = np.zeros_like(t)
    for f in freqs:
        for d in (-0.15, 0.0, 0.17):
            ff = f * 2 ** (d / 12)
            sig += np.sin(2 * np.pi * ff * t + rng.uniform(0, 6)) + 0.25 * np.sin(4 * np.pi * ff * t)
    env = np.minimum(1, t / 1.2) * np.minimum(1, (dur - t) / 1.2)
    return sig * env * vel / len(freqs)


def add(buf, sig, start):
    i = int(start * SR)
    if i >= len(buf):
        return
    n = min(len(sig), len(buf) - i)
    buf[i:i + n] += sig[:n]


def lowpass(x, cutoff):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / (1 + (f / cutoff) ** 4)
    return np.fft.irfft(X, len(x))


def reverb(x, secs=2.8, mix=0.35):
    n = int(secs * SR)
    ir = rng.standard_normal(n) * np.exp(-np.arange(n) / SR * 3.2)
    ir = lowpass(ir, 5000)
    ir /= np.sqrt((ir ** 2).sum())
    L = len(x) + n
    nfft = 1 << (L - 1).bit_length()
    wet = np.fft.irfft(np.fft.rfft(x, nfft) * np.fft.rfft(ir, nfft), nfft)[:len(x)]
    return x * (1 - mix) + wet * mix * 3


def music():
    buf = np.zeros(int(DUR * SR))
    beat = 60 / 70
    bar = beat * 4
    # Am - F - C - G  (vi IV I V) : sayu tapi penuh harapan
    chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]
    bass = [45, 41, 36, 43]
    nbars = int(DUR / bar) + 1
    for b in range(nbars):
        t0 = b * bar
        ch = chords[b % 4]
        add(buf, pad([note_hz(n) for n in ch], bar + 1.0, 0.10 if b < 6 else 0.14), t0)
        if b >= 1:  # piano arpeggio masuk selepas intro
            arp = [ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[1] + 24, ch[2] + 12, ch[1] + 12, ch[0] + 24, ch[2] + 12]
            for i, n in enumerate(arp):
                v = 0.16 + 0.05 * (i == 0)
                add(buf, piano(note_hz(n), 2.5, v), t0 + i * beat / 2)
        if b >= 4:
            add(buf, piano(note_hz(bass[b % 4]), 3.5, 0.22), t0)
        if b >= 7:  # string-like swell di bahagian TERUSKAN
            add(buf, pad([note_hz(n + 12) for n in ch], bar + 0.5, 0.07), t0)
    # resolusi di hujung: akord C major
    add(buf, pad([note_hz(n) for n in [48, 52, 55, 60]], 5.0, 0.12), DUR - 5.0)
    for i, n in enumerate([72, 76, 79, 84]):
        add(buf, piano(note_hz(n), 4.0, 0.14), DUR - 4.8 + i * 0.18)
    buf = lowpass(buf, 6000)
    buf = reverb(buf)
    t = np.arange(len(buf)) / SR
    buf *= np.minimum(1, t / 2.0) * np.minimum(1, (DUR - t) / 2.5)
    return buf


# ---------- sound effects ----------
def whoosh(dur=0.9, vol=0.25):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = rng.standard_normal(n)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    X *= np.exp(-((f - 1800) / 2500) ** 2) + 0.3 * np.exp(-((f - 600) / 500) ** 2)
    x = np.fft.irfft(X, n)
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2
    x = x * env
    return x / np.abs(x).max() * vol


def shimmer(dur=1.6, vol=0.12, base=84):
    out = np.zeros(int(dur * SR))
    for i, n in enumerate([base, base + 4, base + 7, base + 12, base + 16]):
        s = piano(note_hz(n), dur - i * 0.07, 0.5)
        add(out, s, i * 0.07)
    return out * vol


def chime(vol=0.18, n=88):
    t = np.arange(int(2.5 * SR)) / SR
    f = note_hz(n)
    s = (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 3)
         + 0.3 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 6)) * np.exp(-t * 1.6)
    return s * vol * np.minimum(1, t / 0.003)


def paper(dur=0.6, vol=0.22):
    n = int(dur * SR)
    x = rng.standard_normal(n)
    # bunyi kertas: noise ber-crackle
    crack = (rng.random(n) < 0.004) * rng.standard_normal(n) * 4
    x = x * 0.5 + crack
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    X *= np.clip((f - 900) / 3000, 0, 1) * np.exp(-f / 9000)
    x = np.fft.irfft(X, n)
    t = np.arange(n) / SR
    x *= np.sin(np.pi * t / dur) ** 0.6
    return x / np.abs(x).max() * vol


def glass(vol=0.16):
    out = np.zeros(int(2.5 * SR))
    for n, d in [(91, 0.0), (96, 0.05), (100, 0.09)]:
        add(out, chime(vol, n), d)
    return out


def click(vol=0.35):
    n = int(0.06 * SR)
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 120) + rng.standard_normal(n) * np.exp(-t * 300) * 0.4
    return s * vol


def sfx():
    buf = np.zeros(int(DUR * SR))
    add(buf, shimmer(2.0, 0.10, 79), 0.2)
    # transisi
    for t, kind in [(6.0, 'paper'), (11.0, 'whoosh'), (16.5, 'glass'), (23.0, 'whoosh'),
                    (30.0, 'paper'), (36.5, 'glass'), (40.5, 'whoosh')]:
        add(buf, whoosh(0.9, 0.16), t - 0.45)
        if kind == 'paper':
            add(buf, paper(0.7, 0.2), t - 0.35)
        if kind == 'glass':
            add(buf, glass(0.10), t - 0.05)
    # highlight perkataan penting
    for t in (7.55, 27.2, 33.6):
        add(buf, shimmer(1.6, 0.11, 86), t)
    # follow tap
    add(buf, click(0.4), 42.55)
    add(buf, shimmer(1.8, 0.13, 88), 42.6)
    add(buf, chime(0.08, 96), 43.6)
    return reverb(buf, 1.5, 0.25)


if __name__ == '__main__':
    out = sys.argv[1]
    m = music()
    m /= np.abs(m).max()
    s = sfx()
    mix = m * 0.55 + s
    mix /= max(1.0, np.abs(mix).max() / 0.92)
    # stereo lebar sikit
    d = int(0.012 * SR)
    L = mix
    R = np.concatenate([mix[d:], np.zeros(d)]) * 0.5 + mix * 0.5
    st = np.stack([L, R], 1)
    pcm = (st * 32767).astype(np.int16)
    with wave.open(out, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print('wrote', out)
