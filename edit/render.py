"""Render video TikTok 9:16 (1080x1920) – Kempen Mega Rezeki Umar Jewelleries.
Guna: python3 render.py <video_asal.mov> <audio_mix.wav> <output.mp4>"""
import json, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from timeline import FPS, SEGMENTS, OUT_DUR, out_to_src, src_to_out, TRANSITIONS_OUT, END_CARD_SRC

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1920
SRC_VIDEO, AUDIO, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
PREVIEW = os.environ.get("PREVIEW")  # cth "5.6,12.5" -> simpan frame PNG sahaja

# ---------- warna branding ----------
PURPLE_D = (38, 10, 58); PURPLE = (92, 36, 140); PURPLE_L = (150, 90, 200)
GOLD = (231, 184, 74); GOLD_L = (255, 241, 184); GOLD_D = (160, 108, 24); WHITE = (255, 255, 255)

F = lambda n: os.path.join(HERE, "fonts", n)
MONT9, MONT8, PLAY9 = F("montserrat-latin-900-normal.woff"), F("montserrat-latin-800-normal.woff"), F("playfair-display-latin-900-normal.woff")
_fc = {}
def font(p, s):
    if (p, s) not in _fc: _fc[(p, s)] = ImageFont.truetype(p, s)
    return _fc[(p, s)]

# ---------- easing ----------
clamp = lambda x, a=0.0, b=1.0: max(a, min(b, x))
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_in_out(x): x = clamp(x); return 3 * x * x - 2 * x * x * x
def back_out(x, s=1.9):
    x = clamp(x); x -= 1; return x * x * ((s + 1) * x + s) + 1

# ---------- helper grafik ----------
def gold_gradient(w, h):
    y = np.linspace(0, 1, h)[:, None]
    stops = [(0, GOLD_L), (0.45, GOLD), (0.55, (214, 160, 50)), (1, GOLD_D)]
    out = np.zeros((h, 3))
    for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
        m = ((y >= p0) & (y <= p1))[:, 0]
        k = ((y[m] - p0) / (p1 - p0))
        out[m] = np.array(c0) * (1 - k) + np.array(c1) * k
    return Image.fromarray(np.repeat(out[:, None, :], w, 1).astype(np.uint8))

def text_img(txt, fpath, size, fill=WHITE, stroke=0, stroke_fill=(0, 0, 0), shadow=True, track=0):
    f = font(fpath, size)
    bb = f.getbbox(txt, stroke_width=stroke)
    pad = stroke + 14
    w, h = bb[2] - bb[0] + 2 * pad + track * len(txt), bb[3] - bb[1] + 2 * pad
    img = Image.new("RGBA", (w, h))
    org = (pad - bb[0], pad - bb[1])
    def draw_txt(d, fill_, sw=0, sf=None):
        if track:
            x = org[0]
            for ch in txt:
                d.text((x, org[1]), ch, font=f, fill=fill_, stroke_width=sw, stroke_fill=sf)
                x += f.getlength(ch) + track
        else:
            d.text(org, txt, font=f, fill=fill_, stroke_width=sw, stroke_fill=sf)
    if shadow:
        sh = Image.new("RGBA", (w, h)); draw_txt(ImageDraw.Draw(sh), (0, 0, 0, 170), stroke, (0, 0, 0, 170))
        sh = sh.filter(ImageFilter.GaussianBlur(6))
        img.alpha_composite(sh, (0, 0))
        img = img.transform(img.size, Image.AFFINE, (1, 0, -4, 0, 1, -6))
    if stroke:
        st = Image.new("RGBA", (w, h)); draw_txt(ImageDraw.Draw(st), stroke_fill, stroke, stroke_fill)
        img.alpha_composite(st)
    if fill == "gold":
        m = Image.new("L", (w, h)); draw_txt(ImageDraw.Draw(m), 255)
        g = gold_gradient(w, h).convert("RGBA"); g.putalpha(m)
        img.alpha_composite(g)
    else:
        t = Image.new("RGBA", (w, h)); draw_txt(ImageDraw.Draw(t), fill)
        img.alpha_composite(t)
    return img

def rounded(w, h, r, fill, border=0, border_fill="gold", grad=None):
    img = Image.new("RGBA", (w, h))
    if border:
        m = Image.new("L", (w, h)); ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255)
        b = gold_gradient(w, h).convert("RGBA") if border_fill == "gold" else Image.new("RGBA", (w, h), border_fill)
        b.putalpha(m); img.alpha_composite(b)
    m = Image.new("L", (w, h)); ImageDraw.Draw(m).rounded_rectangle((border, border, w - 1 - border, h - 1 - border), max(1, r - border), fill=255)
    if grad:
        y = np.linspace(0, 1, h)[:, None, None]
        arr = np.array(grad[0]) * (1 - y) + np.array(grad[1]) * y
        inner = Image.fromarray(np.repeat(arr, w, 1).astype(np.uint8)).convert("RGBA")
        a = Image.new("L", (w, h), fill[3] if len(fill) == 4 else 255)
        inner.putalpha(Image.fromarray(np.minimum(np.array(a), np.array(m))))
    else:
        inner = Image.new("RGBA", (w, h), fill); inner.putalpha(Image.fromarray(np.minimum(np.array(m), fill[3] if len(fill) == 4 else 255).astype(np.uint8)))
    img.alpha_composite(inner)
    return img

def round_img(im, r):
    im = im.convert("RGBA"); m = Image.new("L", im.size)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), r, fill=255)
    im.putalpha(m); return im

def fit(im, w, h):
    s = min(w / im.width, h / im.height)
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)

def glow(w, h, color=GOLD, strength=200):
    y, x = np.mgrid[0:h, 0:w]
    d = np.sqrt(((x - w / 2) / (w / 2)) ** 2 + ((y - h / 2) / (h / 2)) ** 2)
    a = (np.clip(1 - d, 0, 1) ** 1.6 * strength).astype(np.uint8)
    im = Image.new("RGBA", (w, h), color + (0,)); im.putalpha(Image.fromarray(a)); return im

def stack(items, gap=0):
    w = max(i.width for i in items); h = sum(i.height for i in items) + gap * (len(items) - 1)
    out = Image.new("RGBA", (w, h)); y = 0
    for i in items: out.alpha_composite(i, ((w - i.width) // 2, y)); y += i.height + gap
    return out

def paste_anim(frame, img, cx, cy, scale=1.0, alpha=1.0, rot=0):
    """letak img (RGBA) berpusat di (cx,cy) dengan skala & alpha."""
    if alpha <= 0.01 or scale <= 0.01: return
    if abs(scale - 1) > 1e-3:
        img = img.resize((max(1, int(img.width * scale)), max(1, int(img.height * scale))), Image.BILINEAR)
    if rot: img = img.rotate(rot, Image.BILINEAR, expand=True)
    if alpha < 0.999:
        a = img.getchannel("A").point(lambda v: int(v * alpha)); img = img.copy(); img.putalpha(a)
    frame.alpha_composite(img, (int(cx - img.width / 2), int(cy - img.height / 2)))

def pop(t, t0, dur=0.38, out_t=None, out_dur=0.25):
    """skala & alpha untuk animasi pop-in (+ optional pop-out)."""
    if t < t0: return 0, 0
    s = back_out((t - t0) / dur); a = clamp((t - t0) / 0.12)
    if out_t is not None and t > out_t:
        k = clamp((t - out_t) / out_dur); s *= 1 - 0.3 * k; a *= 1 - k
    return 0.3 + 0.7 * s, a

def shine(img, phase):
    """jalur cahaya diagonal melintas imej (highlight)."""
    if not (0 <= phase <= 1): return img
    w, h = img.size
    y, x = np.mgrid[0:h, 0:w]
    c = -0.3 * w + phase * 1.6 * w
    band = np.clip(1 - np.abs((x + y * 0.5) - c - 0.25 * h) / (0.09 * w), 0, 1) ** 2
    arr = np.array(img).astype(np.float32)
    arr[..., :3] = np.minimum(255, arr[..., :3] + band[..., None] * 140)
    return Image.fromarray(arr.astype(np.uint8))

# ---------- aset ----------
poster = Image.open(os.path.join(HERE, "assets", "poster.jpg")).convert("RGB")
crop = lambda b: poster.crop(b)
A_MYVI = round_img(crop((468, 418, 1012, 700)), 26)
A_MOTO = crop((262, 765, 510, 848)); A_RINGS = crop((283, 888, 505, 972))
A_GOLD5 = crop((765, 750, 970, 855)); A_GOLD1 = crop((730, 895, 985, 990))
SIS_ROSE = Image.open(os.path.join(HERE, "assets", "sis_rose.jpg")).convert("RGB")
SIS_ROSE_W = SIS_ROSE.resize((W, int(SIS_ROSE.height * W / SIS_ROSE.width)), Image.LANCZOS)

def bg_purple():
    y, x = np.mgrid[0:H, 0:W]
    d = np.sqrt(((x - W / 2) / W) ** 2 + ((y - H * 0.4) / H) ** 2)
    k = np.clip(d * 1.6, 0, 1)[..., None]
    arr = np.array(PURPLE) * (1 - k) + np.array(PURPLE_D) * k
    im = Image.fromarray(arr.astype(np.uint8)).convert("RGBA")
    rng = np.random.default_rng(3); d = ImageDraw.Draw(im)
    for _ in range(140):
        px, py, r = rng.integers(0, W), rng.integers(0, H), rng.uniform(1, 4)
        d.ellipse((px - r, py - r, px + r, py + r), fill=GOLD + (int(rng.uniform(60, 200)),))
    return im
BG = bg_purple()

# --- overlay statik ---
BRAND = (lambda: (lambda t: (lambda p: (p.alpha_composite(t, ((p.width - t.width) // 2, (p.height - t.height) // 2)), p)[1])(
    rounded(t.width + 30, 74, 37, PURPLE_D + (225,), border=4)))(
    text_img("MEGA REZEKI 2026  •  UMAR JEWELLERIES", MONT8, 30, "gold", shadow=False)))()

def ribbon(txt, size, fill_txt=WHITE, grad=(PURPLE_L, PURPLE), pad=(50, 22)):
    t = text_img(txt, MONT9, size, fill_txt, stroke=0, shadow=False)
    r = rounded(t.width + pad[0] * 2, t.height + pad[1] * 2 - 20, 24, (0, 0, 0, 255), border=6, grad=grad)
    r.alpha_composite(t, ((r.width - t.width) // 2, (r.height - t.height) // 2)); return r

# Myvi #1 (Bulan terakhir)
MYVI_BIG = fit(A_MYVI, 900, 520)
MYVI_GLOW = glow(1080, 760, GOLD, 210)
RIB_TERAKHIR = ribbon("BULAN TERAKHIR!", 64, "gold", grad=((120, 20, 40), (200, 30, 50)))
RIB_MENANG = ribbon("PELUANG MENANG MYVI", 50)
# Myvi #2 (Hadiah utama)
MYVI_MED = round_img(fit(A_MYVI, 760, 440), 22)
RIB_UTAMA = ribbon("HADIAH UTAMA: MYVI 1.5X", 52, "gold", grad=(PURPLE, PURPLE_D))

# Headline wall
WALL = [(11.45, text_img("KEMPEN TAMAT", MONT9, 118, WHITE, stroke=6, stroke_fill=PURPLE_D)),
        (12.05, text_img("30", PLAY9, 380, "gold", stroke=8, stroke_fill=PURPLE_D)),
        (12.45, text_img("NOVEMBER", MONT9, 168, WHITE, stroke=6, stroke_fill=PURPLE_D)),
        (13.05, text_img("2026", PLAY9, 230, "gold", stroke=8, stroke_fill=PURPLE_D))]

# Pullback hadiah
def prize_row(img, label, sub):
    r = rounded(1000, 156, 30, (0, 0, 0, 255), border=5, grad=((70, 25, 105), (30, 8, 48)))
    im = round_img(fit(img, 380, 124), 14)
    r.alpha_composite(im, (22 + (380 - im.width) // 2, (156 - im.height) // 2))
    t1 = text_img(label, MONT9, 58, "gold", shadow=False); t2 = text_img(sub, MONT8, 34, WHITE, shadow=False)
    r.alpha_composite(t1, (430, 16)); r.alpha_composite(t2, (434, 88)); return r
PRIZES = [(25.6, prize_row(A_MOTO, "MOTOSIKAL", "Hadiah Kedua • 3 Unit")),
          (26.45, prize_row(A_RINGS, "CINCIN EMAS", "Emas 916 • 15 Pcs")),
          (26.95, prize_row(A_GOLD5, "GOLD BAR", "999.9 Fine Gold • 5g & 1g"))]
HDR_HADIAH = text_img("BANYAK LAGI HADIAH MENARIK!", MONT9, 56, "gold", stroke=4, stroke_fill=PURPLE_D)

# Khas dealer
def dealer_badge():
    a = text_img("KHAS UNTUK", MONT8, 46, WHITE, shadow=False)
    b = text_img("DEALER UMAR JEWELLERIES", MONT9, 56, "gold", shadow=False)
    c = text_img("SAHAJA", MONT9, 46, WHITE, shadow=False)
    s = stack([a, b, c], -14)
    r = rounded(s.width + 70, s.height + 30, 34, PURPLE_D + (235,), border=6)
    r.alpha_composite(s, (35, 15)); return r
DEALER = dealer_badge()

# Emas 916 / 999.9
def karat_card(img, big, small):
    r = rounded(486, 380, 34, (0, 0, 0, 255), border=6, grad=((80, 30, 120), (28, 8, 45)))
    im = round_img(fit(img, 430, 170), 16); r.alpha_composite(im, ((486 - im.width) // 2, 28))
    t = text_img(big, PLAY9, 104, "gold", shadow=False); r.alpha_composite(t, ((486 - t.width) // 2, 192))
    s = text_img(small, MONT8, 30, WHITE, shadow=False); r.alpha_composite(s, ((486 - s.width) // 2, 316))
    return r
CARD916 = karat_card(A_RINGS, "916", "EMAS 22K • BARANG KEMAS")
CARD999 = karat_card(A_GOLD1, "999.9", "EMAS 24K • GOLD BAR")
RIB_JIMAT = ribbon("HARGA EMAS LEBIH JIMAT!", 58, "gold", grad=((120, 20, 40), (200, 30, 50)))

# Frame break CTA
RIB_DAFTAR = (lambda: (lambda t1, t2: (lambda r: (r.alpha_composite(t1, ((r.width - t1.width) // 2, 30)),
                                                     r.alpha_composite(t2, ((r.width - t2.width) // 2, 30 + t1.height - 26)), r)[2])(
    rounded(1040, t1.height + t2.height + 30, 40, (0, 0, 0, 255), border=7, grad=((200, 30, 50), (120, 15, 35)))))(
    text_img("JOM DAFTAR DEALER", MONT9, 84, "gold", shadow=False), text_img("SEKARANG!", MONT9, 70, WHITE, shadow=False)))()
def frame_border(w, h, r=40, t=10):
    g = gold_gradient(w, h).convert("RGBA"); m = Image.new("L", (w, h)); d = ImageDraw.Draw(m)
    d.rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255); d.rounded_rectangle((t, t, w - 1 - t, h - 1 - t), r - t, fill=0)
    g.putalpha(m); return g

# End card
def end_cta():
    a = text_img("JOM DAFTAR DEALER", MONT9, 64, "gold", stroke=0, shadow=False)
    b = text_img("UMAR JEWELLERIES", PLAY9, 58, WHITE, shadow=False)
    c = text_img("Hubungi Sis Rose untuk maklumat lanjut.", MONT8, 33, GOLD_L, shadow=False)
    s = stack([a, b, c], -16)
    r = rounded(1020, s.height + 26, 36, PURPLE_D + (240,), border=6)
    r.alpha_composite(s, ((r.width - s.width) // 2, 13)); return r
END_CTA = end_cta()


# Label besar "SIS ROSE" gaya kaca putih (frosted glass) untuk end card
TAG_TEXT = text_img("SIS ROSE", PLAY9, 116, WHITE, shadow=True)
TAG_W, TAG_H = TAG_TEXT.width + 70, 170
TAG_MASK = Image.new("L", (TAG_W, TAG_H)); ImageDraw.Draw(TAG_MASK).rounded_rectangle((0, 0, TAG_W - 1, TAG_H - 1), 50, fill=255)
TAG_TINT = Image.new("RGBA", (TAG_W, TAG_H), (25, 10, 40, 110))
TAG_EDGE = Image.new("RGBA", (TAG_W, TAG_H))
ImageDraw.Draw(TAG_EDGE).rounded_rectangle((0, 0, TAG_W - 1, TAG_H - 1), 50, outline=(255, 255, 255, 170), width=3)
def glass_tag(frame, cx, cy, scale, alpha):
    if alpha <= 0.01: return
    x, y = int(cx - TAG_W / 2), int(cy - TAG_H / 2)
    g = frame.crop((x, y, x + TAG_W, y + TAG_H)).filter(ImageFilter.GaussianBlur(18))
    g.alpha_composite(TAG_TINT); g.alpha_composite(TAG_EDGE)
    g.alpha_composite(TAG_TEXT, ((TAG_W - TAG_TEXT.width) // 2, (TAG_H - TAG_TEXT.height) // 2 - 4))
    g.putalpha(TAG_MASK)
    paste_anim(frame, g, cx, cy, scale, alpha)

# Watermark / trademark "Sis Rose" – teks putih atas pil kaca (frosted glass), sepanjang video
WM_TEXT = text_img("Sis Rose", PLAY9, 42, WHITE, shadow=False)
WM_W, WM_H = WM_TEXT.width + 24, 62
def _wm_mask():
    m = Image.new("L", (WM_W, WM_H)); ImageDraw.Draw(m).rounded_rectangle((0, 0, WM_W - 1, WM_H - 1), WM_H // 2, fill=255); return m
WM_MASK = _wm_mask()
WM_TINT = Image.new("RGBA", (WM_W, WM_H), (25, 10, 40, 95))
WM_EDGE = (lambda: (lambda e: (ImageDraw.Draw(e).rounded_rectangle((0, 0, WM_W - 1, WM_H - 1), WM_H // 2, outline=(255, 255, 255, 120), width=2), e)[1])(Image.new("RGBA", (WM_W, WM_H))))()
def put_watermark(frame, end_card=False, scale=1.0, alpha=1.0):
    # bawah kanan; pada end card ke atas kanan supaya tak bertindih dengan CTA
    x = W - WM_W - 24
    y = 24 if end_card else H - WM_H - 18
    glass = frame.crop((x, y, x + WM_W, y + WM_H)).filter(ImageFilter.GaussianBlur(14))
    glass.alpha_composite(WM_TINT)
    glass.alpha_composite(WM_EDGE)
    glass.alpha_composite(WM_TEXT, ((WM_W - WM_TEXT.width) // 2, (WM_H - WM_TEXT.height) // 2 - 2))
    if scale >= 0.999 and alpha >= 0.999:
        frame.paste(glass, (x, y), WM_MASK); return
    glass.putalpha(WM_MASK)
    paste_anim(frame, glass, x + WM_W / 2, y + WM_H / 2, scale, alpha)

# ---------- sari kata ----------
def build_words():
    tr = json.load(open(os.path.join(HERE, "transcript.json")))
    ws = []
    for seg in tr:
        for a, b, w in seg["w"]:
            ws.append([a, b, w.strip()])
    fixed = []
    for a, b, w in ws:
        if w == "Manatahu":
            m = (a + b) / 2; fixed += [[a, m, "Mana"], [m, b, "tahu"]]; continue
        if w.startswith("-") and fixed:
            fixed[-1][2] += w; fixed[-1][1] = b; continue
        fixed.append([a, b, w])
    for x in fixed:
        x[2] = x[2].upper()
    return fixed

def chunk_words(ws, maxw=3, maxc=16):
    chunks, cur = [], []
    for w in ws:
        cur.append(w)
        txt = " ".join(x[2] for x in cur)
        if len(cur) >= maxw or len(txt) >= maxc or w[2][-1] in ",.?!":
            chunks.append(cur); cur = []
    if cur: chunks.append(cur)
    out = []
    for i, c in enumerate(chunks):
        start = c[0][0]
        nxt = chunks[i + 1][0][0] if i + 1 < len(chunks) else c[-1][1] + 0.6
        end = min(nxt, c[-1][1] + 0.6)
        out.append((start, end, c))
    return out

CHUNKS = chunk_words(build_words())
_sub_cache = {}
def sub_img(ci, wi):
    key = (ci, wi)
    if key in _sub_cache: return _sub_cache[key]
    words = CHUNKS[ci][2]
    size = 84
    imgs = [text_img(w[2], MONT9, size, "gold" if k == wi else WHITE, stroke=9, stroke_fill=(20, 4, 32)) for k, w in enumerate(words)]
    total = sum(i.width for i in imgs) - 30 * (len(imgs) - 1)
    if total > 1020:
        s = 1020 / total; imgs = [i.resize((int(i.width * s), int(i.height * s)), Image.LANCZOS) for i in imgs]
        total = sum(i.width for i in imgs) - int(30 * s) * (len(imgs) - 1)
    h = max(i.height for i in imgs)
    out = Image.new("RGBA", (total + 10, h)); x = 0
    for i in imgs:
        out.alpha_composite(i, (x, (h - i.height) // 2)); x += i.width - 30
    _sub_cache[key] = out; return out

def draw_subs(frame, ts, cy):
    for ci, (a, b, words) in enumerate(CHUNKS):
        if a <= ts < b:
            wi = 0
            for k, w in enumerate(words):
                if ts >= w[0]: wi = k
            img = sub_img(ci, wi)
            s, al = pop(ts, a, 0.18)
            paste_anim(frame, img, W / 2, cy, 0.85 + 0.15 * (s - 0.3) / 0.7 if s else 0, al)
            return

# ---------- kamera (digital zoom) ----------
ZOOM_KEYS = [  # (src_t, zoom, anchor_y)
    (0.0, 1.00, .36), (4.0, 1.08, .36), (4.05, 1.24, .34), (5.3, 1.24, .34), (5.35, 1.04, .40), (8.9, 1.10, .40),
    (9.15, 1.12, .36), (11.4, 1.18, .36), (14.05, 1.30, .33), (16.3, 1.30, .33), (16.35, 1.06, .38), (19.6, 1.10, .40),
    (21.3, 1.10, .40), (27.8, 1.18, .35), (31.3, 1.24, .35), (31.85, 1.03, .40), (36.3, 1.06, .38), (41.75, 1.12, .38)]
JUMPS = {4.05, 5.35, 14.05, 16.35, 27.8, 31.85}
def zoom_at(ts):
    for (t0, z0, y0), (t1, z1, y1) in zip(ZOOM_KEYS, ZOOM_KEYS[1:]):
        if t0 <= ts < t1:
            k = (ts - t0) / (t1 - t0)
            if t1 - t0 < 0.1: k = 1.0
            return z0 + (z1 - z0) * k, y0 + (y1 - y0) * k
    return ZOOM_KEYS[-1][1], ZOOM_KEYS[-1][2]

def camera(src_frame, z, ay):
    cw, ch = W / z, H / z
    cx = W / 2; cy = clamp(ay * H, ch / 2, H - ch / 2)
    box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
    return src_frame.resize((W, H), Image.BILINEAR, box=box)

# ---------- komposisi setiap frame ----------
def compose(fr, to):
    ts = out_to_src(to)
    z, ay = zoom_at(ts)
    # bump zoom selepas setiap transisi
    for tt in TRANSITIONS_OUT:
        if 0 <= to - tt < 0.3: z *= 1 + 0.06 * (1 - ease_out((to - tt) / 0.3))
    show_brand, sub_y = True, 1560

    if ts >= END_CARD_SRC:  # ===== END CARD: Sis Rose =====
        k = ts - END_CARD_SRC
        img = SIS_ROSE_W
        zz = 1.0 + 0.05 * ease_in_out(k / 4.3)
        intro = ease_out(k / 0.45)
        zz *= 1.12 - 0.12 * intro
        frame = img.resize((W, H), Image.BILINEAR, box=((W - W / zz) / 2, (img.height - H / zz) * 0.9, (W + W / zz) / 2, (img.height - H / zz) * 0.9 + H / zz)).convert("RGBA")
        s, a = pop(ts, END_CARD_SRC + 0.35, 0.45)
        paste_anim(frame, END_CTA, W / 2, 1800, s, a)
        s, a = pop(ts, 43.98, 0.45)   # label nama muncul tepat bila Kak Ros sebut "Sis Rose"
        glass_tag(frame, W / 2, 1140, s, a)   # tengah, atas badan, sedikit atas kotak "Follow Sis Rose"
        put_watermark(frame, end_card=True)
        return frame

    cam = camera(fr, z, ay).convert("RGBA")

    if 21.3 <= ts < 27.8:  # ===== PULLBACK: hadiah =====
        k = ease_in_out((ts - 21.4) / 0.45)
        sc = 1 - 0.45 * k
        frame = BG.copy()
        vw, vh = int(W * sc), int(H * sc)
        vy = int(60 * k + (H - vh) / 2 * (1 - k))
        v = round_img(cam.resize((vw, vh), Image.BILINEAR), int(36 * k))
        if k > 0.02:
            frame.alpha_composite(frame_border(vw + 16, vh + 16, 44, 8), ((W - vw) // 2 - 8, vy - 8))
        frame.alpha_composite(v, ((W - vw) // 2, vy))
        s, a = pop(ts, 23.2, 0.35)
        paste_anim(frame, HDR_HADIAH, W / 2, 1170, s, a)
        for i, (t0, row) in enumerate(PRIZES):
            s, a = pop(ts, t0, 0.4)
            paste_anim(frame, row, W / 2, 1300 + i * 166, s, a)
        show_brand = False; sub_y = 1785
    elif 36.3 <= ts < 41.75:  # ===== FRAME BREAK: daftar dealer =====
        k = ease_out((ts - 36.3) / 0.4)
        sc = 1 - 0.12 * k
        frame = BG.copy()
        vw, vh = int(W * sc), int(H * sc)
        vy = int((H - vh) / 2 + 40 * k)
        frame.alpha_composite(frame_border(vw + 20, vh + 20, 46, 10), ((W - vw) // 2 - 10, vy - 10))
        frame.alpha_composite(round_img(cam.resize((vw, vh), Image.BILINEAR), 36), ((W - vw) // 2, vy))
        s, a = pop(ts, 38.55, 0.42)
        paste_anim(frame, RIB_DAFTAR, W / 2, 1330, s, a, rot=-2 * a)
        sub_y = 1590
    else:
        frame = cam

    # ===== Myvi: bulan terakhir =====
    if 5.4 <= ts < 8.9:
        s, a = pop(ts, 5.45, 0.5)
        zoomc = 1 + 0.08 * clamp((ts - 5.45) / 3.4)
        paste_anim(frame, MYVI_GLOW, W / 2, 1210, s * 1.05, a * (0.75 + 0.25 * math.sin(ts * 6)))
        car = shine(MYVI_BIG, (ts - 7.75) / 0.6)
        paste_anim(frame, car, W / 2, 1220, s * zoomc, a)
        s2, a2 = pop(ts, 5.6, 0.35)
        paste_anim(frame, RIB_TERAKHIR, W / 2, 935, s2, a2, rot=3)
        s3, a3 = pop(ts, 7.6, 0.35)
        paste_anim(frame, RIB_MENANG, W / 2, 1500, s3, a3)
        sub_y = 1665
    # ===== Myvi: hadiah utama =====
    if 19.6 <= ts < 21.4:
        s, a = pop(ts, 19.7, 0.45, out_t=21.15)
        paste_anim(frame, MYVI_GLOW, W / 2, 1180, s * 0.85, a)
        paste_anim(frame, shine(MYVI_MED, (ts - 20.6) / 0.6), W / 2, 1190, s, a)
        s2, a2 = pop(ts, 19.85, 0.35, out_t=21.15)
        paste_anim(frame, RIB_UTAMA, W / 2, 920, s2, a2, rot=-2)
        sub_y = 1580
    # ===== Headline wall: tarikh =====
    if 11.4 <= ts < 14.05:
        k = clamp((ts - 11.4) / 0.2) * (1 - clamp((ts - 13.85) / 0.2))
        arr = np.array(frame).astype(np.float32)
        tint = np.array(PURPLE_D + (255,), np.float32)
        arr = arr * (1 - 0.82 * k) + tint * 0.82 * k
        frame = Image.fromarray(arr.astype(np.uint8))
        ys = [560, 820, 1110, 1330]
        for (t0, img), y in zip(WALL, ys):
            if ts >= t0:
                p = ease_out((ts - t0) / 0.22)
                paste_anim(frame, img, W / 2, y, 1.7 - 0.7 * p, clamp(p * 1.5) * k)
        bar = Image.new("RGBA", (int(760 * ease_out((ts - 13.2) / 0.4)) or 1, 10), GOLD + (int(255 * k),))
        if ts > 13.2: frame.alpha_composite(bar, ((W - bar.width) // 2, 1480))
        show_brand, sub_y = False, None
    # ===== Khas dealer =====
    if 28.5 <= ts < 31.3:
        s, a = pop(ts, 28.55, 0.4)
        paste_anim(frame, DEALER, W / 2, 1180, s, a)
        sub_y = 1560
    # ===== Emas 916 / 999.9 =====
    if 31.85 <= ts < 36.3:
        s, a = pop(ts, 32.35, 0.42, out_t=36.05)
        paste_anim(frame, CARD916, 287, 1235, s, a, rot=3 * a)
        s, a = pop(ts, 32.7, 0.42, out_t=36.05)
        paste_anim(frame, CARD999, 793, 1235, s, a, rot=-3 * a)
        s, a = pop(ts, 33.45, 0.38, out_t=36.05)
        paste_anim(frame, RIB_JIMAT, W / 2, 1000, s, a)
        sub_y = 1610

    if show_brand:
        paste_anim(frame, BRAND, W / 2, 92)
    if sub_y:
        draw_subs(frame, ts, sub_y)
    put_watermark(frame)
    # flash putih pada transisi
    for tt in TRANSITIONS_OUT:
        d = to - tt
        if 0 <= d < 0.18:
            a = 0.75 * (1 - d / 0.18)
            fl = Image.new("RGBA", (W, H), (255, 250, 235, int(255 * a)))
            frame.alpha_composite(fl)
    return frame

# ---------- pembaca frame sumber ----------
class Reader:
    def __init__(self, path):
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-vf", f"fps={FPS},scale={W}:{H}:flags=lanczos",
                                   "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        self.idx, self.last = -1, None
    def get(self, i):
        while self.idx < i:
            b = self.p.stdout.read(W * H * 3)
            if len(b) < W * H * 3: break
            self.last = Image.frombuffer("RGB", (W, H), b); self.idx += 1
        return self.last

def main():
    n = int(round(OUT_DUR * FPS))
    if PREVIEW:
        times = [float(x) for x in PREVIEW.split(",")]
        for to in times:
            r = Reader(SRC_VIDEO); ts = out_to_src(to)
            fr = r.get(int(min(ts, SEGMENTS[-1][1] - 0.05) * FPS)); r.p.kill()
            compose(fr, to).convert("RGB").save(os.path.join(os.environ.get("PREVIEW_DIR", "."), f"prev_{to:05.2f}.jpg"), quality=85)
        return
    r = Reader(SRC_VIDEO)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                            "-i", "-", "-i", AUDIO, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                            "-pix_fmt", "yuv420p", "-profile:v", "high", "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
                            "-movflags", "+faststart", "-shortest", OUT], stdin=subprocess.PIPE)
    for i in range(n):
        to = i / FPS; ts = out_to_src(to)
        fr = r.get(int(min(ts, SEGMENTS[-1][1] - 0.04) * FPS))
        enc.stdin.write(compose(fr, to).convert("RGB").tobytes())
        if i % 150 == 0: print(f"frame {i}/{n}", flush=True)
    enc.stdin.close(); enc.wait(); r.p.kill()
    print("siap:", OUT)

if __name__ == "__main__":
    main()
