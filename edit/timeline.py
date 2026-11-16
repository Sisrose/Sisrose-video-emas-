"""Timeline bersama untuk video & audio. Masa dalam saat (masa video asal = 'src')."""
FPS = 30
# Bahagian video asal yang dikekalkan (jeda panjang dibuang = dynamic cuts)
SEGMENTS = [(0.0, 8.9), (9.15, 31.3), (31.85, 41.75), (42.25, 44.40)]   # potong "Jangan tunggu" - tamat pada "Sis Rose."
END_HOLD = 1.80                      # end card Sis Rose dipanjangkan selepas dialog tamat
OUT_DUR = sum(b - a for a, b in SEGMENTS) + END_HOLD   # ~44.93s (< 45s)


def src_to_out(ts):
    acc = 0.0
    for a, b in SEGMENTS:
        if a <= ts <= b:
            return acc + ts - a
        acc += b - a
    return acc + (ts - SEGMENTS[-1][1])


def out_to_src(to):
    acc = 0.0
    for a, b in SEGMENTS:
        if to < acc + (b - a):
            return a + (to - acc)
        acc += b - a
    return SEGMENTS[-1][1] + (to - acc)   # selepas tamat: masa 'src' maya untuk end card


# Titik pertukaran babak (src) -> flash + whoosh
SECTION_SRC = [11.4, 14.05, 21.4, 27.8, 31.85, 36.3, 42.25]
CUT_OUT = [src_to_out(SEGMENTS[i][0]) for i in range(1, len(SEGMENTS))]
TRANSITIONS_OUT = sorted(set(round(src_to_out(s), 3) for s in SECTION_SRC) | set(round(c, 3) for c in CUT_OUT))
# Masa visual hadiah 'pop' (src) -> bunyi sparkle
POPS_SRC = [5.45, 7.8, 19.7, 25.6, 26.45, 26.95, 32.35, 32.7, 38.6]
POPS_OUT = [src_to_out(s) for s in POPS_SRC]
END_CARD_SRC = 42.25
END_CARD_OUT = src_to_out(END_CARD_SRC)
