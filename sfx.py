"""Synthesise subtle cinematic SFX (no music) and mix under the original voice.

Usage: python3 sfx.py <voice.m4a> <out_mix.wav> [<out_sfx_only.wav>]
The voice track is passed through untouched (gain 1.0); effects are added at
low level (peaks around -24..-30 dBFS vs voice peaks around -6 dBFS).
"""
import sys
import subprocess
import numpy as np

SR = 48000
rng = np.random.default_rng(7)


def db(x):
    return 10 ** (x / 20)


def norm(x, peak_db):
    m = np.max(np.abs(x)) or 1.0
    return x / m * db(peak_db)


def stft_filter_noise(n, center_fn, width_oct=1.0, nfft=2048, hop=256):
    """Noise whose spectral peak follows center_fn(t_frac) in Hz."""
    noise = rng.standard_normal(n + nfft)
    win = np.hanning(nfft)
    out = np.zeros(n + nfft)
    wsum = np.zeros(n + nfft)
    freqs = np.fft.rfftfreq(nfft, 1 / SR)
    lf = np.log2(np.maximum(freqs, 20))
    for start in range(0, n, hop):
        seg = noise[start:start + nfft] * win
        spec = np.fft.rfft(seg)
        c = np.log2(center_fn(start / n))
        mask = np.exp(-0.5 * ((lf - c) / width_oct) ** 2)
        out[start:start + nfft] += np.fft.irfft(spec * mask) * win
        wsum[start:start + nfft] += win ** 2
    out = out / np.maximum(wsum, 1e-6)
    return out[:n]


def reverb(x, wet=0.18, length=0.9):
    n = int(length * SR)
    t = np.arange(n) / SR
    ir = rng.standard_normal(n) * np.exp(-t * 6.0)
    ir = np.convolve(ir, np.ones(24) / 24, mode="same")  # darken
    ir /= np.sqrt(np.sum(ir ** 2))
    tail = np.convolve(x, ir)[: len(x) + n]
    tail = np.pad(tail, (0, len(x) + n - len(tail)))
    dry = np.concatenate([x, np.zeros(n)])
    return dry * (1 - wet) + tail * wet


def env_bell(n, peak=0.6, sharp=2.0):
    t = np.linspace(0, 1, n)
    a = np.where(t < peak, (t / peak) ** sharp, ((1 - t) / (1 - peak)) ** (sharp * 1.3))
    return a


def whoosh(dur=0.9, lo=250, hi=2600, peak=0.55):
    n = int(dur * SR)
    def c(f):
        # rise to hi at peak, fall a bit after
        return lo * (hi / lo) ** (np.sin(np.pi * min(f / peak, 1) / 2) if f < peak else 1 - 0.45 * (f - peak) / (1 - peak))
    x = stft_filter_noise(n, c, width_oct=0.9)
    x *= env_bell(n, peak, 2.2)
    return reverb(x, 0.22)


def pop(f0=820, f1=430, dur=0.12):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t * 55)
    ph = 2 * np.pi * np.cumsum(f) / SR
    e = (1 - np.exp(-t * 900)) * np.exp(-t * 38)
    x = np.sin(ph) * e + 0.25 * np.sin(2 * ph) * e * np.exp(-t * 60)
    return reverb(x, 0.15, 0.5)


def bell(f0, dur=1.0, decay=4.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for ratio, amp, dk in [(1, 1, 1), (2.76, 0.5, 1.6), (5.40, 0.28, 2.4), (8.93, 0.14, 3.2)]:
        x += amp * np.sin(2 * np.pi * f0 * ratio * t + rng.uniform(0, 6)) * np.exp(-t * decay * dk)
    x *= 1 - np.exp(-t * 400)
    return x


def shimmer(dur=1.4, count=9):
    n = int(dur * SR)
    out = np.zeros(n)
    for i in range(count):
        st = int((i / count) * 0.55 * SR + rng.uniform(0, 0.03) * SR)
        b = bell(rng.uniform(1500, 3200), dur=dur, decay=rng.uniform(3.5, 5.5)) * rng.uniform(0.5, 1.0)
        out[st:] += b[: n - st]
    # airy high noise swell for the "gold glint"
    air = stft_filter_noise(n, lambda f: 7000, width_oct=0.7) * env_bell(n, 0.35, 1.5) * 0.6
    out = out / np.max(np.abs(out)) + air / np.max(np.abs(air)) * 0.35
    return reverb(out, 0.3, 1.2)


def sparkle(dur=1.3, count=14):
    n = int(dur * SR)
    out = np.zeros(n)
    for i in range(count):
        st = int((i / count) * 0.75 * SR + rng.uniform(0, 0.04) * SR)
        f = 2600 + 3200 * (i / count) + rng.uniform(-300, 300)
        p = bell(f, dur=0.5, decay=9) * rng.uniform(0.4, 1.0)
        m = min(len(p), n - st)
        out[st:st + m] += p[:m]
    air = stft_filter_noise(n, lambda f: 8000, width_oct=0.6) * env_bell(n, 0.5, 1.4)
    out = out / np.max(np.abs(out)) + air / np.max(np.abs(air)) * 0.3
    return reverb(out, 0.35, 1.4)


def airy(dur=3.4):
    n = int(dur * SR)
    x = stft_filter_noise(n, lambda f: 700 + 900 * np.sin(np.pi * f), width_oct=1.2)
    x *= env_bell(n, 0.35, 1.6)
    return reverb(x, 0.4, 1.5)


def place(track, clip, t, gain_db):
    s = int(t * SR)
    clip = norm(clip, gain_db)
    m = min(len(clip), len(track) - s)
    track[s:s + m] += clip[:m]


# ---------------- cue sheet (seconds, synced to voice + visuals) -------------
CUES = [
    # HOOK
    ("whoosh", 0.12, -25), ("pop", 0.58, -29), ("pop", 4.74, -29), ("pop", 5.94, -28),
    # GOLD SAVINGS
    ("shimmer", 6.92, -27),
    ("popb", 8.00, -30), ("popb", 8.78, -30), ("popb", 9.60, -30),
    ("popb", 10.40, -30), ("popb", 11.12, -30), ("popb", 11.88, -30),
    # TRANSITION TO KAABAH
    ("whoosh_long", 12.95, -25), ("airy", 13.15, -32),
    # CLOSING
    ("sparkle", 22.12, -26), ("swoosh", 27.30, -27),
]


def build(total):
    tr = np.zeros(int(total * SR) + SR)
    bar_i = 0
    for kind, t, g in CUES:
        if kind == "whoosh":
            c = whoosh(0.85)
        elif kind == "whoosh_long":
            c = whoosh(1.15, 200, 2200, 0.5)
        elif kind == "pop":
            c = pop()
        elif kind == "popb":  # gold-bar drop: light pop, rising slightly each bar
            c = pop(760 + 45 * bar_i, 420 + 25 * bar_i, 0.11)
            b = bell(2400 + 120 * bar_i, 0.4, 9)
            c[: len(b)] += 0.08 * b[: len(c)]
            bar_i += 1
        elif kind == "shimmer":
            c = shimmer()
        elif kind == "sparkle":
            c = sparkle()
        elif kind == "airy":
            c = airy()
        elif kind == "swoosh":
            c = whoosh(0.7, 400, 3400, 0.45)
        place(tr, c, t, g)
    return tr[: int(total * SR)]


def main():
    voice_path, out_mix = sys.argv[1], sys.argv[2]
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", voice_path, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    v = np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).astype(np.float64)
    total = len(v) / SR
    fx = build(total)
    # gentle stereo spread for the effects
    fx_st = np.stack([fx, np.roll(fx, int(0.006 * SR))], axis=1) * 0.92
    mix = v + fx_st
    # smooth fade-out at the very end (voice ends ~31.1 s; fade starts after)
    fade = int(0.7 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)[:, None] ** 2
    peak = np.max(np.abs(mix))
    if peak > 0.98:  # safety only; should not trigger
        mix *= 0.98 / peak
    mix.astype(np.float32).tofile(out_mix + ".f32")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", out_mix + ".f32",
                    "-c:a", "pcm_s24le", out_mix], check=True)
    if len(sys.argv) > 3:
        fx_st.astype(np.float32).tofile(sys.argv[3] + ".f32")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", sys.argv[3] + ".f32",
                        "-c:a", "pcm_s24le", sys.argv[3]], check=True)
    print(f"duration {total:.3f}s, fx peak {20*np.log10(np.max(np.abs(fx))+1e-9):.1f} dBFS, mix peak {20*np.log10(peak):.1f} dBFS")


if __name__ == "__main__":
    main()
