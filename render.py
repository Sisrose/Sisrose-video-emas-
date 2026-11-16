"""Render "DARI GRAM KE BAITULLAH" (1080x1920, 30 fps) as raw frames to stdout.

Usage: python3 render.py <assets_dir> | ffmpeg -f rawvideo -pix_fmt rgb24 -s 1080x1920 -r 30 -i - ...
assets_dir must contain: madinah.mp4, goldcard.jpg, kaabah.jpg, sisrose.jpg
"""
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
DUR = 32.19
A = sys.argv[1]

SERIF_B = "/usr/share/fonts/truetype/crosextra/Caladea-Bold.ttf"
SERIF_I = "/usr/share/fonts/truetype/crosextra/Caladea-Italic.ttf"
SERIF_BI = "/usr/share/fonts/truetype/crosextra/Caladea-BoldItalic.ttf"
SANS_B = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
SANS_SB = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
SANS_XB = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"

GOLD = [(255, 243, 196), (240, 205, 120), (196, 145, 52)]
GOLD_HI = (246, 210, 120)

# ----------------------------------------------------------------- easing ----
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out_cubic(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in_out(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out_back(x, s=1.9):
    x = clamp(x)
    return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2


# -------------------------------------------------------------- text art ----
_font_cache = {}


def font(path, size):
    k = (path, size)
    if k not in _font_cache:
        _font_cache[k] = ImageFont.truetype(path, size)
    return _font_cache[k]


def gradient_fill(size, stops):
    w, h = size
    ys = np.linspace(0, 1, h)[:, None]
    n = len(stops) - 1
    out = np.zeros((h, 1, 3))
    for i in range(n):
        lo, hi = i / n, (i + 1) / n
        m = (ys >= lo) & (ys <= hi)
        f = (ys - lo) / (hi - lo)
        c = np.array(stops[i]) * (1 - f) + np.array(stops[i + 1]) * f
        out = np.where(m[..., None], c[..., None, :] if c.ndim == 2 else c, out)
    out = np.repeat(out, w, axis=1)
    return Image.fromarray(out.astype(np.uint8), "RGB")


def text_img(lines, fpath, size, fill="gold", align="center", spacing=1.08, shadow=0.75,
             stroke=0, stroke_fill=(40, 10, 10), tracking=0, glow=False):
    """Multi-line text rendered to a tight RGBA image with soft shadow."""
    if isinstance(lines, str):
        lines = [lines]
    f = font(fpath, size)
    pad = int(size * 0.6)
    asc, desc = f.getmetrics()
    lh = int((asc + desc) * spacing)

    def line_w(s):
        if tracking == 0:
            return f.getlength(s)
        return sum(f.getlength(ch) for ch in s) + tracking * (len(s) - 1)

    widths = [line_w(l) for l in lines]
    tw = int(max(widths)) + 2 * pad
    th = lh * len(lines) + 2 * pad
    mask = Image.new("L", (tw, th), 0)
    d = ImageDraw.Draw(mask)
    for i, l in enumerate(lines):
        x = pad + (tw - 2 * pad - widths[i]) / 2 if align == "center" else pad
        y = pad + i * lh
        if tracking == 0:
            d.text((x, y), l, font=f, fill=255, stroke_width=stroke, stroke_fill=255)
        else:
            for ch in l:
                d.text((x, y), ch, font=f, fill=255, stroke_width=stroke, stroke_fill=255)
                x += f.getlength(ch) + tracking
    if fill == "gold":
        col = gradient_fill((tw, th), [GOLD[0], GOLD[1], GOLD[2]])
    else:
        col = Image.new("RGB", (tw, th), fill)
    out = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    if shadow:
        sh = mask.filter(ImageFilter.GaussianBlur(size * 0.12))
        sh = sh.point(lambda v: int(v * shadow))
        shadow_layer = Image.new("RGBA", (tw, th), (10, 2, 4, 0))
        shadow_layer.putalpha(sh)
        out = Image.alpha_composite(out, ImageChops_offset(shadow_layer, int(size * 0.04), int(size * 0.06)))
    if glow:
        gl = mask.filter(ImageFilter.GaussianBlur(size * 0.35)).point(lambda v: int(v * 0.55))
        gll = Image.new("RGBA", (tw, th), (255, 200, 110, 0))
        gll.putalpha(gl)
        out = Image.alpha_composite(out, gll)
    txt = col.convert("RGBA")
    txt.putalpha(mask)
    out = Image.alpha_composite(out, txt)
    return out


def ImageChops_offset(img, dx, dy):
    o = Image.new("RGBA", img.size, (0, 0, 0, 0))
    o.paste(img, (dx, dy))
    return o


def place(canvas, img, cx, cy, scale=1.0, alpha=1.0, dy=0):
    """Composite RGBA `img` centred at (cx, cy) with scale/alpha."""
    if alpha <= 0.002 or scale <= 0.01:
        return
    if abs(scale - 1) > 0.003:
        img = img.resize((max(1, int(img.width * scale)), max(1, int(img.height * scale))), Image.BICUBIC)
    if alpha < 0.999:
        a = img.getchannel("A").point(lambda v: int(v * alpha))
        img = img.copy()
        img.putalpha(a)
    x = int(cx - img.width / 2)
    y = int(cy - img.height / 2 + dy)
    canvas.alpha_composite(img, (max(0, x), max(0, y)), (max(0, -x), max(0, -y)))


def pop_anim(t, t0, t1, dur_in=0.38, dur_out=0.3, style="pop"):
    """Return (scale, alpha, dy) for an element visible on [t0, t1]."""
    if t < t0 or t > t1 + dur_out:
        return 0, 0, 0
    p = (t - t0) / dur_in
    if style == "pop":
        sc = 0.55 + 0.45 * ease_out_back(p)
        dy = 0
    elif style == "rise":
        sc = 1.0
        dy = 40 * (1 - ease_out_cubic(p))
    else:  # fade
        sc = 1.0 + 0.04 * (1 - ease_out_cubic(p))
        dy = 0
    al = ease_out_cubic(p * 2.2 if style == "pop" else p)
    if t > t1:
        q = (t - t1) / dur_out
        al *= 1 - ease_in_out(q)
        sc *= 1 + 0.05 * q
    return sc, al, dy


def rounded_rect(size, r, fill):
    im = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), r, fill=fill)
    return im


def chip(text, fpath, size, fg=(255, 255, 255), bg=(20, 6, 8, 170), border=GOLD_HI, padx=34, pady=18):
    f = font(fpath, size)
    tw = int(f.getlength(text))
    asc, desc = f.getmetrics()
    w, h = tw + 2 * padx, asc + desc + 2 * pady
    im = rounded_rect((w, h), h // 2, bg)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((1, 1, w - 2, h - 2), h // 2, outline=border + (230,), width=3)
    d.text((padx, pady - 2), text, font=f, fill=fg)
    return im


# --------------------------------------------------------- backgrounds ------
def cover(img, w, h):
    s = max(w / img.width, h / img.height)
    img = img.resize((math.ceil(img.width * s), math.ceil(img.height * s)), Image.LANCZOS)
    x = (img.width - w) // 2
    y = (img.height - h) // 2
    return img.crop((x, y, x + w, y + h))


def kenburns(big, t_frac, z0, z1, cx0=0.5, cy0=0.5, cx1=0.5, cy1=0.5):
    """`big` is the image pre-scaled to cover WxH at zoom z_max. Crop+resize per frame."""
    z = z0 + (z1 - z0) * ease_in_out(t_frac)
    zmax = big.width / W
    cw, ch = W * zmax / z, H * zmax / z
    cx = (cx0 + (cx1 - cx0) * ease_in_out(t_frac)) * big.width
    cy = (cy0 + (cy1 - cy0) * ease_in_out(t_frac)) * big.height
    x0 = clamp(cx - cw / 2, 0, big.width - cw)
    y0 = clamp(cy - ch / 2, 0, big.height - ch)
    return big.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))


def vgrad_overlay(top_a=0.55, top_h=700, bot_a=0.7, bot_h=900, col=(8, 2, 4)):
    a = np.zeros((H, 1), np.float32)
    y = np.arange(H)[:, None]
    a = np.maximum(a, top_a * np.clip(1 - y / top_h, 0, 1) ** 1.6)
    a = np.maximum(a, bot_a * np.clip((y - (H - bot_h)) / bot_h, 0, 1) ** 1.4)
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., :3] = col
    arr[..., 3] = (np.repeat(a, W, axis=1) * 255).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def maroon_bg():
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((x - W / 2) / W) ** 2 + ((y - H * 0.38) / H) ** 2)
    f = np.clip(r / 0.75, 0, 1)[..., None]
    c0 = np.array([92, 18, 26], np.float32)
    c1 = np.array([22, 4, 8], np.float32)
    arr = c0 * (1 - f) + c1 * f
    # songket-like diamond dot pattern
    pat = (((x.astype(int) + y.astype(int)) % 46 < 3) | ((x.astype(int) - y.astype(int)) % 46 < 3)).astype(np.float32)
    arr += pat[..., None] * np.array([28, 10, 8]) * (1 - f * 0.6)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


# ------------------------------------------------------------ gold bars -----
def gold_bar(w=250, h=118):
    S = 3
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    top_h = int(h * S * 0.34)
    inset = int(w * S * 0.12)
    # front face
    front = gradient_fill((w * S, h * S - top_h), [(255, 226, 140), (214, 160, 60), (150, 100, 30)]).convert("RGBA")
    m = Image.new("L", front.size, 0)
    ImageDraw.Draw(m).polygon([(0, 0), (w * S, 0), (w * S - inset // 2, front.height), (inset // 2, front.height)], fill=255)
    im.paste(front, (0, top_h), m)
    # top face
    top = gradient_fill((w * S, top_h), [(255, 250, 215), (245, 210, 120)]).convert("RGBA")
    mt = Image.new("L", top.size, 0)
    ImageDraw.Draw(mt).polygon([(inset, 0), (w * S - inset, 0), (w * S, top_h), (0, top_h)], fill=255)
    im.paste(top, (0, 0), mt)
    f = font(SANS_XB, int(h * S * 0.24))
    label = "999.9"
    tw = f.getlength(label)
    d.text(((w * S - tw) / 2, top_h + (h * S - top_h) * 0.2), label, font=f, fill=(120, 76, 18, 200))
    d.line([(0, top_h), (w * S, top_h)], fill=(255, 255, 230, 220), width=S * 2)
    return im.resize((w, h), Image.LANCZOS)


def drop_shadow(img, blur=22, alpha=0.6, dy=18):
    pad = blur * 3
    sh = Image.new("RGBA", (img.width + 2 * pad, img.height + 2 * pad), (0, 0, 0, 0))
    a = img.getchannel("A").point(lambda v: int(v * alpha))
    blk = Image.new("RGBA", img.size, (0, 0, 0, 255))
    blk.putalpha(a)
    sh.paste(blk, (pad, pad + dy), blk)
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    sh.alpha_composite(img, (pad, pad))
    return sh


def sweep_shine(img, p, width=0.18, strength=0.75):
    """Diagonal light band crossing an RGBA image; p in [0,1]."""
    if p <= 0 or p >= 1:
        return img
    w, h = img.size
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    u = (x / w + y / h * 0.45) / 1.45
    c = -0.2 + 1.4 * p
    band = np.exp(-0.5 * ((u - c) / (width / 2.5)) ** 2) * strength
    arr = np.array(img).astype(np.float32)
    arr[..., :3] = arr[..., :3] + (255 - arr[..., :3]) * band[..., None] * (arr[..., 3:4] / 255)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")


# --------------------------------------------------------------- assets -----
print("loading assets", file=sys.stderr)
card_src = Image.open(os.path.join(A, "goldcard.jpg")).convert("RGB").crop((252, 347, 1030, 840))
cm = Image.new("L", card_src.size, 0)
ImageDraw.Draw(cm).rounded_rectangle((2, 2, card_src.width - 3, card_src.height - 3), 34, fill=255)
card = card_src.convert("RGBA")
card.putalpha(cm)
card = card.resize((900, int(900 * card.height / card.width)), Image.LANCZOS)
card_sh = drop_shadow(card, 26, 0.7, 22)

kaabah_big = cover(Image.open(os.path.join(A, "kaabah.jpg")).convert("RGB"), int(W * 1.3), int(H * 1.3)).convert("RGBA")
rose_big = cover(Image.open(os.path.join(A, "sisrose.jpg")).convert("RGB"), int(W * 1.08), int(H * 1.08)).convert("RGBA")
MAROON = maroon_bg()
OVL = vgrad_overlay()
OVL_SOFT = vgrad_overlay(0.45, 650, 0.35, 700)
OVL_K = vgrad_overlay(0.82, 1000, 0.6, 800)
BAR = drop_shadow(gold_bar(), 10, 0.55, 8)

# --------------------------------------------------------- text elements ----
T = {}
T["hook1"] = text_img(["IMPIAN KE"], SERIF_B, 92, "white", tracking=6)
T["hook2"] = text_img(["BAITULLAH"], SERIF_B, 150, "gold", tracking=4, glow=True, shadow=1.0)
T["hook3"] = text_img(["jangan sekadar disimpan dalam hati"], SERIF_I, 58, (255, 240, 220))
T["cuba"] = text_img(["CUBA MULA DENGAN"], SANS_B, 58, "white", tracking=4)
T["1gram"] = text_img(["1 GRAM EMAS"], SERIF_B, 132, "gold", glow=True, shadow=1.0)
T["sebulan"] = text_img(["sebulan"], SERIF_BI, 76, (255, 240, 220))
T["simpan"] = text_img(["SIMPAN 1 GRAM", "SETIAP BULAN"], SERIF_B, 84, "gold", glow=True, shadow=1.0)
T["counter"] = [text_img([f"{i} GRAM"], SERIF_B, 96, "gold", glow=True, shadow=1.0) for i in range(0, 7)]
T["bulan"] = [text_img([f"BULAN KE-{i}"], SANS_SB, 40, (255, 228, 190), tracking=5) for i in range(0, 7)]
T["chip_mampu"] = chip("Ikut kemampuan", SANS_SB, 44)
T["chip_tunai"] = chip("Jangan lupa simpanan tunai juga", SANS_SB, 40)
T["sikit"] = text_img(["SIKIT DEMI SIKIT"], SERIF_B, 100, "gold", glow=True, shadow=1.0)
T["bekal"] = text_img(["jadi bekal ke", "Tanah Suci"], SERIF_BI, 82, (255, 245, 230), spacing=1.0)
T["target"] = text_img(["TARGET + ISTIQOMAH"], SERIF_B, 86, "gold", glow=True, shadow=1.0)
T["jom"] = text_img(["JOM MULAKAN LANGKAH PERTAMA"], SANS_B, 46, "white", tracking=4)
T["dari"] = text_img(["DARI GRAM"], SERIF_B, 128, "gold", glow=True, tracking=4)
T["ke"] = text_img(["KE BAITULLAH"], SERIF_B, 128, "gold", glow=True, tracking=4)
T["cta1"] = text_img(["Semoga satu hari nanti usaha kecil kita", "menjadi asbab sampai ke Baitullah."], SERIF_I, 54,
                     (255, 245, 230), spacing=1.15, shadow=1.0)
T["brand"] = text_img(["SIS ROSE  ·  UMAR JEWELLERIES"], SANS_SB, 30, (255, 230, 180), tracking=4, shadow=0.9)

# --------------------------------------------------------------- subtitles ---
# Word timings from the original voice (spoken words, not the typed script).
WORDS = [
    ("Siapa", 1.54), ("kata", 2.14), ("nak", 2.50), ("pergi", 2.68), ("umrah", 2.86), ("|", 0),
    ("kena", 3.22), ("tunggu", 3.50), ("duit", 3.72), ("banyak?", 3.88), ("#", 4.6),
    ("Cuba", 4.76), ("mula", 5.04), ("dengan", 5.32), ("|", 0), ("1", 5.62), ("gram", 5.96), ("emas", 6.12),
    ("sebulan.", 6.42), ("#", 7.2),
    ("Bayangkan", 7.98), ("setiap", 8.48), ("bulan", 8.78), ("|", 0), ("kita", 9.10), ("simpan", 9.32), ("1", 9.62),
    ("gram", 9.88), ("emas,", 10.06), ("#", 10.6),
    ("kalau", 10.72), ("tak", 10.90), ("mampu,", 11.08), ("|", 0), ("simpanlah", 11.50), ("ikut", 12.08),
    ("kemampuan.", 12.32), ("#", 13.2),
    ("Sikit", 13.46), ("demi", 13.64), ("sikit.", 13.88), ("#", 14.6),
    ("Lama-lama", 14.76), ("jadi", 15.18), ("bekal", 15.46), ("|", 0), ("untuk", 15.78), ("ke", 16.04), ("tanah", 16.18),
    ("suci.", 16.38), ("#", 17.0),
    ("Yang", 17.08), ("penting", 17.28), ("kita", 17.70), ("ada", 17.92), ("target", 18.12), ("|", 0), ("dan", 18.46),
    ("istiqomah", 18.70), ("menyimpan.", 19.24), ("#", 20.25),
    ("Jom", 20.42), ("mulakan", 20.54), ("langkah", 20.92), ("|", 0), ("pertama", 21.18), ("hari", 21.58), ("ini", 21.80),
    ("#", 22.15),
    ("@dari", 22.20), ("gram", 22.50), ("ke", 22.74), ("Baitullah.", 22.92), ("#", 23.7),  # @ = hidden (headline)
    ("InsyaAllah,", 23.78), ("semoga", 24.26), ("Allah", 24.60), ("|", 0), ("jemput", 24.84), ("kita", 25.12),
    ("menjadi", 25.42), ("tetamu-Nya.", 25.74), ("#", 26.75),
    ("Amin.", 26.86), ("#", 27.4),
    ("Kalau", 27.46), ("nak", 28.04), ("tahu", 28.18), ("|", 0), ("macam", 28.48), ("mana", 28.70), ("menyimpan", 28.86),
    ("emas,", 29.26), ("#", 30.0),
    ("boleh", 30.10), ("contact", 30.24), ("Kak", 30.48), ("Rose.", 30.66), ("#", 31.6),
]


def parse_groups():
    groups, cur, line, hidden = [], [], [], False
    for w, t in WORDS:
        if w == "|":
            cur.append(line)
            line = []
        elif w == "#":
            cur.append(line)
            start = cur[0][0][1]
            groups.append({"lines": cur, "start": start, "end": t, "hidden": hidden})
            cur, line, hidden = [], [], False
        else:
            if w.startswith("@"):
                hidden, w = True, w[1:]
            line.append((w, t))
    return groups


GROUPS = parse_groups()
SUB_F = font(SANS_B, 54)
_sub_cache = {}


def sub_img(gi, active):
    k = (gi, active)
    if k in _sub_cache:
        return _sub_cache[k]
    g = GROUPS[gi]
    space = SUB_F.getlength(" ")
    asc, desc = SUB_F.getmetrics()
    lh = int((asc + desc) * 1.18)
    widths = [sum(SUB_F.getlength(w) for w, _ in l) + space * (len(l) - 1) for l in g["lines"]]
    padx, pady = 40, 22
    bw = int(max(widths)) + 2 * padx
    bh = lh * len(g["lines"]) + 2 * pady - int(lh * 0.18)
    im = rounded_rect((bw, bh), 30, (12, 4, 6, 150))
    d = ImageDraw.Draw(im)
    idx = 0
    for li, l in enumerate(g["lines"]):
        x = padx + (bw - 2 * padx - widths[li]) / 2
        y = pady + li * lh - 4
        for w, _ in l:
            col = GOLD_HI if idx == active else (255, 255, 255)
            d.text((x, y), w, font=SUB_F, fill=col, stroke_width=2 if idx == active else 0, stroke_fill=(90, 50, 10))
            x += SUB_F.getlength(w) + space
            idx += 1
    _sub_cache[k] = im
    return im


def draw_subs(canvas, t, cy):
    for gi, g in enumerate(GROUPS):
        if g["hidden"] or not (g["start"] - 0.05 <= t <= g["end"] + 0.15):
            continue
        times = [wt for l in g["lines"] for _, wt in l]
        active = max([i for i, wt in enumerate(times) if wt <= t + 0.03], default=0)
        sc, al, dy = pop_anim(t, g["start"] - 0.05, g["end"], 0.22, 0.15, "rise")
        place(canvas, sub_img(gi, active), W / 2, cy, 1.0, al, dy * 0.5)


# ------------------------------------------------------------- scenes -------
def scene_hook(t, frame):
    c = Image.fromarray(frame, "RGB").convert("RGBA")
    # slow push-in on the Madinah clip
    z = 1.0 + 0.06 * (t / 6.9)
    if z > 1.001:
        cw, ch = W / z, H / z
        c = c.resize((W, H), Image.BICUBIC, box=((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2))
    c.alpha_composite(OVL)
    # headline block 1 (typed hook)
    s, a, dy = pop_anim(t, 0.15, 4.45, 0.45, 0.3, "fade")
    place(c, T["hook1"], W / 2, 330, s, a, dy)
    s, a, dy = pop_anim(t, 0.58, 4.45, 0.42, 0.3, "pop")
    place(c, T["hook2"], W / 2, 455, s, a, dy)
    s, a, dy = pop_anim(t, 1.15, 4.45, 0.5, 0.3, "rise")
    place(c, T["hook3"], W / 2, 580, s, a, dy)
    # block 2
    s, a, dy = pop_anim(t, 4.74, 7.0, 0.35, 0.25, "pop")
    place(c, T["cuba"], W / 2, 330, s, a, dy)
    s, a, dy = pop_anim(t, 5.94, 7.0, 0.4, 0.25, "pop")
    place(c, T["1gram"], W / 2, 460, s, a, dy)
    s, a, dy = pop_anim(t, 6.42, 7.0, 0.35, 0.25, "rise")
    place(c, T["sebulan"], W / 2, 580, s, a, dy)
    return c


BAR_T = [8.00, 8.78, 9.60, 10.40, 11.12, 11.88]
BAR_POS = [(-260, 0), (0, 0), (260, 0), (-130, -112), (130, -112), (0, -224)]  # pyramid


def scene_gold(t):
    lt = t - 6.9
    c = MAROON.copy()
    # card floats in
    p = ease_out_cubic(lt / 0.7)
    cy = 520 + 60 * (1 - p) + 8 * math.sin(lt * 1.6)
    img = card_sh
    if 0.0 < lt < 1.1:
        img = sweep_shine(card_sh, lt / 1.1)
    place(c, img, W / 2, cy, 0.8 * (0.92 + 0.08 * p), p)
    s, a, dy = pop_anim(t, 7.0, 10.45, 0.5, 0.3, "rise")
    place(c, T["simpan"], W / 2, 200, 1, a, dy)
    # bars
    base_y = 1330
    n = sum(1 for bt in BAR_T if t >= bt)
    for i, bt in enumerate(BAR_T):
        if t < bt - 0.12:
            continue
        q = clamp((t - bt + 0.12) / 0.32)
        y = base_y + BAR_POS[i][1] - 260 * (1 - ease_out_back(q, 1.2))
        place(c, BAR, W / 2 + BAR_POS[i][0], y, 1, clamp(q * 3))
    # counter
    if t >= BAR_T[0] - 0.05:
        k = max(1, n)
        bump = 1 + 0.12 * math.exp(-max(0, t - BAR_T[k - 1]) * 9)
        place(c, T["counter"][k], W / 2, 1515, bump, 1)
        place(c, T["bulan"][k], W / 2, 1435, 1, 0.9)
    # chips (soft, no sound)
    s, a, dy = pop_anim(t, 10.72, 13.6, 0.4, 0.3, "rise")
    place(c, T["chip_mampu"], W / 2, 150, 1, a, dy)
    s, a, dy = pop_anim(t, 12.15, 13.6, 0.4, 0.3, "rise")
    place(c, T["chip_tunai"], W / 2, 245, 1, a, dy)
    return c


def scene_kaabah(t):
    lt = (t - 13.1) / (27.6 - 13.1)
    c = kenburns(kaabah_big, lt, 1.0, 1.22, 0.5, 0.55, 0.55, 0.5)
    c.alpha_composite(OVL_K)
    s, a, dy = pop_anim(t, 13.46, 14.55, 0.4, 0.25, "fade")
    place(c, T["sikit"], W / 2, 360, s, a, dy)
    s, a, dy = pop_anim(t, 14.76, 16.85, 0.45, 0.25, "rise")
    place(c, T["bekal"], W / 2, 380, s, a, dy)
    s, a, dy = pop_anim(t, 17.10, 20.1, 0.45, 0.25, "fade")
    place(c, T["target"], W / 2, 360, s, a, dy)
    s, a, dy = pop_anim(t, 20.42, 22.0, 0.4, 0.2, "rise")
    place(c, T["jom"], W / 2, 360, s, a, dy)
    # DARI GRAM KE BAITULLAH (sparkle at 22.15)
    s, a, dy = pop_anim(t, 22.18, 27.3, 0.5, 0.35, "pop")
    place(c, T["dari"], W / 2, 330, s, a, dy)
    s, a, dy = pop_anim(t, 22.62, 27.3, 0.5, 0.35, "pop")
    place(c, T["ke"], W / 2, 470, s, a, dy)
    if 22.15 <= t <= 23.6:
        draw_sparkles(c, t - 22.15)
    s, a, dy = pop_anim(t, 23.78, 27.3, 0.6, 0.35, "rise")
    place(c, T["cta1"], W / 2, 620, s, a, dy)
    return c


SPARK = None


def sparkle_sprite(r=34):
    S = r * 2
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(r, 0), (r + 5, r - 5), (S, r), (r + 5, r + 5), (r, S), (r - 5, r + 5), (0, r), (r - 5, r - 5)],
              fill=(255, 245, 210, 255))
    g = im.filter(ImageFilter.GaussianBlur(5))
    g.alpha_composite(im)
    return g


_rs = np.random.default_rng(3)
SPARKS = [(_rs.uniform(170, 910), _rs.uniform(250, 560), _rs.uniform(0, 0.9), _rs.uniform(0.5, 1.1)) for _ in range(16)]


def draw_sparkles(c, lt):
    global SPARK
    if SPARK is None:
        SPARK = sparkle_sprite()
    for x, y, t0, sz in SPARKS:
        q = (lt - t0) / 0.5
        if 0 < q < 1:
            place(c, SPARK, x, y, sz * math.sin(math.pi * q), math.sin(math.pi * q))


def scene_rose(t):
    lt = (t - 27.3) / (DUR - 27.3)
    c = kenburns(rose_big, lt, 1.0, 1.06, 0.5, 0.45, 0.5, 0.42)
    c.alpha_composite(OVL_SOFT)
    # gold shine sweep across the baked-in "FOLLOW SIS ROSE" card (swoosh at 27.3)
    p = (t - 27.45) / 0.9
    if 0 < p < 1:
        box = (40, 1270, 1040, 1600)
        reg = c.crop(box)
        reg = sweep_shine(reg, p, 0.22, 0.45)
        c.paste(reg, box[:2])
    return c


def flash(c, amt, col=(255, 236, 200)):
    if amt <= 0:
        return c
    ov = Image.new("RGBA", c.size, col + (int(255 * amt),))
    c.alpha_composite(ov)
    return c


def blend(a, b, f):
    return Image.blend(a, b, ease_in_out(f))


# --------------------------------------------------------------- main -------
def main():
    nframes = int(round(DUR * FPS))
    vid = subprocess.Popen(["ffmpeg", "-v", "error", "-i", os.path.join(A, "madinah.mp4"), "-vf",
                            f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS}",
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    last = None
    out = sys.stdout.buffer
    for i in range(nframes):
        t = i / FPS
        if t < 7.3:
            buf = vid.stdout.read(W * H * 3)
            if len(buf) == W * H * 3:
                last = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        if t < 6.75:
            c = scene_hook(t, last)
        elif t < 7.15:  # hook -> gold crossfade with warm flash
            f = (t - 6.75) / 0.4
            c = blend(scene_hook(t, last), scene_gold(t), f)
            c = flash(c, 0.28 * math.sin(math.pi * f))
        elif t < 12.95:
            c = scene_gold(t)
        elif t < 13.75:  # cinematic transition to Kaabah: zoom-blur + light bloom
            f = (t - 12.95) / 0.8
            g = scene_gold(t)
            z = 1 + 0.25 * ease_in_out(f)
            g = g.resize((W, H), Image.BICUBIC, box=((W - W / z) / 2, (H - H / z) / 2, (W + W / z) / 2, (H + H / z) / 2))
            k = scene_kaabah(t)
            c = blend(g, k, f)
            c = flash(c, 0.45 * math.sin(math.pi * f) ** 2)
        elif t < 27.3:
            c = scene_kaabah(t)
        elif t < 27.7:
            f = (t - 27.3) / 0.4
            c = blend(scene_kaabah(t), scene_rose(t), f)
            c = flash(c, 0.18 * math.sin(math.pi * f))
        else:
            c = scene_rose(t)
        # subtitles (spoken words) — placed above TikTok's bottom UI zone
        sub_y = 930  # captions centred on screen (clear of TikTok UI)
        draw_subs(c, t, sub_y)
        # smooth fade-out at the end
        if t > DUR - 0.7:
            c = flash(c, ease_in_out((t - (DUR - 0.7)) / 0.7), (0, 0, 0))
        out.write(c.convert("RGB").tobytes())
        if i % 60 == 0:
            print(f"frame {i}/{nframes}", file=sys.stderr)
    vid.stdout.close()
    vid.wait()


if __name__ == "__main__":
    main()
