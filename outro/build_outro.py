#!/usr/bin/env python3
"""
SIS ROSE – PINK LUXURY SIGNATURE OUTRO (editable master template)

Renders outro/SIS_ROSE_PINK_LUXURY_OUTRO.mp4 (1080x1920, 30 fps, 4.0 s, AAC 48 kHz)
from the original photograph in outro/assets/. Output is deterministic: running it
again produces the same outro. Edit the constants below to tweak; do not change the
portrait source – the face is only cropped to a circle and uniformly scaled.

Usage:  python3 outro/build_outro.py
Needs:  Python 3, Pillow, NumPy, ffmpeg
"""
import math, os, subprocess, tempfile, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
OUT = os.path.join(HERE, "SIS_ROSE_PINK_LUXURY_OUTRO.mp4")

W, H, FPS, DUR = 1080, 1920, 30, 4.0
N = int(FPS * DUR)
SR = 48000

# ---- Official brand colours ----
LUX_PINK = (0xF4, 0x8F, 0xB1)
BLUSH = (0xFA, 0xDA, 0xDD)
PEARL = (0xFF, 0xF9, 0xFC)
PURPLE = (0xC8, 0xA2, 0xD8)
GOLD = (0xD8, 0xB5, 0x6A)
PLUM = (0x76, 0x2A, 0x63)
DEEP_PINK = (0xD9, 0x3A, 0x78)
BTN_PINK = (0xF0, 0x5A, 0x96)

# ---- Fonts (OFL, Google Fonts via Fontsource) ----
F_CINZEL = os.path.join(ASSETS, "fonts", "Cinzel-Bold.woff")
F_POPPINS = os.path.join(ASSETS, "fonts", "Poppins-SemiBold.woff")
F_MONT = os.path.join(ASSETS, "fonts", "Montserrat-ExtraBold.woff")

# ---- Layout (inside TikTok safe area) ----
PORTRAIT_C = (540, 610)
PORTRAIT_R = 265
NAME_Y = 1010
BTN_C = (540, 1240)
BTN_W, BTN_H = 640, 112
TAG_Y = 1395

# Portrait crop in the original 1254x1254 photo (centre, radius) – face, glasses,
# hijab and headphones kept intact.
CROP_C = (622, 545)
CROP_R = 430


# ------------------------------------------------------------------ helpers
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))

def prog(t, a, b):
    return clamp((t - a) / (b - a))

def ease_out_cubic(x):
    return 1 - (1 - x) ** 3

def ease_in_out(x):
    return 0.5 - 0.5 * math.cos(math.pi * x)

def ease_out_back(x, s=1.7):
    x -= 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2

def with_alpha(img, a):
    if a >= 1:
        return img
    r, g, b, al = img.split()
    al = al.point(lambda v: int(v * a))
    return Image.merge("RGBA", (r, g, b, al))

def paste_center(base, img, cx, cy):
    base.alpha_composite(img, (int(round(cx - img.width / 2)), int(round(cy - img.height / 2))))

def scaled(img, s):
    if abs(s - 1) < 1e-3:
        return img
    w, h = max(1, int(img.width * s)), max(1, int(img.height * s))
    return img.resize((w, h), Image.LANCZOS)


# ------------------------------------------------------------------ static layers
def make_portrait():
    src = Image.open(os.path.join(ASSETS, "sis_rose_portrait_original.jpg")).convert("RGB")
    cx, cy = CROP_C
    box = (cx - CROP_R, cy - CROP_R, cx + CROP_R, cy + CROP_R)
    crop = src.crop(box).resize((PORTRAIT_R * 2, PORTRAIT_R * 2), Image.LANCZOS)
    ss = 4
    mask = Image.new("L", (PORTRAIT_R * 2 * ss,) * 2, 0)
    ImageDraw.Draw(mask).ellipse((0, 0, mask.width - 1, mask.height - 1), fill=255)
    mask = mask.resize(crop.size, Image.LANCZOS)
    out = crop.convert("RGBA")
    out.putalpha(mask)
    return out

def make_ring():
    """Champagne-gold ring with angular sheen + ornaments (rotated per frame)."""
    ss = 2
    R_out, R_in = PORTRAIT_R + 34, PORTRAIT_R + 6
    size = (R_out + 30) * 2 * ss
    c = size / 2
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    dx, dy = xx - c, yy - c
    r = np.sqrt(dx * dx + dy * dy) / ss
    ang = np.arctan2(dy, dx)
    sheen = 0.72 + 0.28 * np.cos(2 * ang) + 0.12 * np.cos(5 * ang + 1)
    # bevel: brighter at centre line of band
    mid = (R_out + R_in) / 2
    bevel = 1 - 0.35 * ((r - mid) / ((R_out - R_in) / 2)) ** 2
    lum = np.clip(sheen * bevel, 0.35, 1.25)
    gold = np.array(GOLD, np.float32)
    hi = np.array((255, 244, 214), np.float32)
    t = np.clip(lum - 0.75, 0, 0.5)[..., None] * 2
    rgb = gold * np.clip(lum, 0, 1)[..., None] * (1 - t) + hi * t
    band = ((r >= R_in) & (r <= R_out)).astype(np.float32)
    # fine inner/outer pinstripes
    stripe = (((r >= R_in + 4) & (r <= R_in + 6)) | ((r >= R_out - 6) & (r <= R_out - 4))).astype(np.float32)
    rgb = rgb * (1 - 0.25 * stripe[..., None])
    a = band * 255
    img = Image.fromarray(np.dstack([np.clip(rgb, 0, 255), a]).astype(np.uint8), "RGBA")
    d = ImageDraw.Draw(img)
    # ornaments: 8 pearls + 4 diamonds on outer edge
    for k in range(12):
        th = k * math.pi * 2 / 12
        rr = (R_out + 8) * ss
        px, py = c + rr * math.cos(th), c + rr * math.sin(th)
        if k % 3 == 0:
            s = 13 * ss
            pts = [(px + s * math.cos(th), py + s * math.sin(th)),
                   (px + s * 0.55 * math.cos(th + math.pi / 2), py + s * 0.55 * math.sin(th + math.pi / 2)),
                   (px - s * math.cos(th), py - s * math.sin(th)),
                   (px + s * 0.55 * math.cos(th - math.pi / 2), py + s * 0.55 * math.sin(th - math.pi / 2))]
            d.polygon(pts, fill=(255, 238, 200, 255), outline=GOLD + (255,))
        else:
            s = 6 * ss
            d.ellipse((px - s, py - s, px + s, py + s), fill=PEARL + (255,), outline=GOLD + (255,), width=ss)
    return img.resize((img.width // ss, img.height // ss), Image.LANCZOS)

def make_glow(radius, color, blur):
    size = int((radius + blur * 3) * 2)
    g = Image.new("RGBA", (size, size), color + (0,))
    ImageDraw.Draw(g).ellipse((size / 2 - radius, size / 2 - radius, size / 2 + radius, size / 2 + radius), fill=color + (200,))
    return g.filter(ImageFilter.GaussianBlur(blur))

def make_star(size, color=(255, 236, 190)):
    """4-point sparkle."""
    ss = 4
    s = size * ss
    img = Image.new("RGBA", (s, s), color + (0,))
    d = ImageDraw.Draw(img)
    c = s / 2
    w = s * 0.11
    d.polygon([(c, 0), (c + w, c - w), (s, c), (c + w, c + w), (c, s), (c - w, c + w), (0, c), (c - w, c - w)], fill=color + (255,))
    img = img.resize((size, size), Image.LANCZOS)
    glow = img.filter(ImageFilter.GaussianBlur(size / 6))
    return Image.alpha_composite(glow, img)

STAR_CACHE = {}
def star(size, color=(255, 236, 190)):
    key = (size, color)
    if key not in STAR_CACHE:
        STAR_CACHE[key] = make_star(size, color)
    return STAR_CACHE[key]


def background(t):
    """Pink-to-pearl gradient with soft purple silk ribbons (computed at 1/4 res)."""
    w, h = W // 4, H // 4
    y = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    x = np.linspace(0, 1, w, dtype=np.float32)[None, :]
    top, mid, bot = np.array(LUX_PINK, np.float32), np.array(BLUSH, np.float32), np.array(PEARL, np.float32)
    k = np.clip(y * 1.6, 0, 1)
    k2 = np.clip((y - 0.45) * 2.2, 0, 1)
    base = top * (1 - k)[..., None] + mid * k[..., None]
    base = base * (1 - k2)[..., None] + bot * k2[..., None]
    base = np.broadcast_to(base, (h, w, 3)).copy()
    # soft diagonal light
    light = np.exp(-((x - 0.25) ** 2 + (y - 0.15) ** 2) / 0.08)
    base += (np.array(PEARL, np.float32) - base) * (0.35 * light)[..., None]
    # purple silk ribbons
    ph = t * 0.9
    ribbons = [
        (0.30, 0.060, 0.050, 2.2, 0.0, 0.40),
        (0.78, 0.075, 0.055, 1.8, 1.7, 0.35),
        (0.90, 0.050, 0.040, 2.6, 3.1, 0.30),
    ]
    purple = np.array(PURPLE, np.float32)
    for cy, amp, thick, freq, off, strength in ribbons:
        centre = cy + amp * np.sin(2 * math.pi * freq * x * 0.5 + off + ph) + 0.06 * (x - 0.5)
        dist = (y - centre) / thick
        a = np.exp(-dist ** 2) * strength
        sheen = 0.5 + 0.5 * np.sin(2 * math.pi * (x * 1.3 + 0.2 * np.sin(ph + off)) + dist * 1.5)
        pearl = np.array(PEARL, np.float32)
        mixk = (0.15 + 0.45 * sheen)[..., None]
        col = purple * (1 - mixk) + pearl * mixk
        base = base * (1 - a)[..., None] + col * a[..., None]
    img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.BICUBIC)
    return img.convert("RGBA")


# ------------------------------------------------------------------ text layers
def letter_sprites():
    font = ImageFont.truetype(F_CINZEL, 132)
    text = "SIS ROSE"
    full_w = font.getlength(text)
    x0 = W / 2 - full_w / 2
    sprites = []
    for i, ch in enumerate(text):
        if ch == " ":
            continue
        cx = x0 + font.getlength(text[:i]) + font.getlength(ch) / 2
        pad = 30
        bb = font.getbbox(ch, stroke_width=4)
        cw, chh = bb[2] - bb[0] + pad * 2, bb[3] - bb[1] + pad * 2
        img = Image.new("RGBA", (int(cw), int(chh)), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        ox, oy = pad - bb[0], pad - bb[1]
        # 3D depth: stacked plum shadow
        for k in range(6, 0, -1):
            d.text((ox + k * 0.6, oy + k), ch, font=font, fill=PLUM + (90,))
        d.text((ox, oy), ch, font=font, fill=DEEP_PINK + (255,), stroke_width=4, stroke_fill=GOLD + (255,))
        # top highlight on the face of the letter
        hl = Image.new("L", img.size, 0)
        ImageDraw.Draw(hl).text((ox, oy), ch, font=font, fill=255)
        grad = Image.linear_gradient("L").resize(img.size).point(lambda v: int(max(0, 110 - v * 1.2)))
        hl = ImageChops.multiply(hl, grad)
        img.alpha_composite(Image.merge("RGBA", (Image.new("L", img.size, 255),) * 3 + (hl,)))
        # centre of this sprite in the frame when its text origin sits at (x0+advance, NAME_Y)
        ccx = x0 + font.getlength(text[:i]) - ox + img.width / 2
        ccy = NAME_Y - oy + img.height / 2
        sprites.append((img, ccx, ccy))
    return sprites

def shimmer(img, pos):
    """Gold shimmer band sweeping across a sprite; pos in [0,1] relative to name width."""
    w, h = img.size
    band = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(band)
    bx = pos
    d.polygon([(bx - 30, h), (bx + 10, h), (bx + 70, 0), (bx + 30, 0)], fill=200)
    band = band.filter(ImageFilter.GaussianBlur(10))
    band = ImageChops.multiply(band, img.split()[3])
    layer = Image.new("RGBA", (w, h), (255, 240, 200, 0))
    layer.putalpha(band)
    out = img.copy()
    out.alpha_composite(layer)
    return out

def make_button(pressed=0.0):
    ss = 2
    w, h = BTN_W * ss, BTN_H * ss
    pad = 40 * ss
    img = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    # shadow
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((pad, pad + 14 * ss, pad + w, pad + h + 14 * ss), radius=h // 2, fill=PLUM + (110,))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12 * ss)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((pad, pad, pad + w, pad + h), radius=h // 2, fill=GOLD + (255,))
    b = 6 * ss
    col = tuple(int(c * (1 - 0.12 * pressed)) for c in BTN_PINK)
    d.rounded_rectangle((pad + b, pad + b, pad + w - b, pad + h - b), radius=h // 2 - b, fill=col + (255,))
    # glossy top
    gloss = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(gloss).rounded_rectangle((pad + b * 3, pad + b * 2, pad + w - b * 3, pad + h // 2), radius=h // 4, fill=(255, 255, 255, 55))
    img.alpha_composite(gloss)
    # follow icon (person +) in a white circle
    icx, icy, ir = pad + 70 * ss, pad + h // 2, 34 * ss
    d.ellipse((icx - ir, icy - ir, icx + ir, icy + ir), fill=(255, 255, 255, 255))
    d.ellipse((icx - 13 * ss, icy - 20 * ss, icx + 5 * ss, icy - 2 * ss), fill=BTN_PINK + (255,))
    d.pieslice((icx - 22 * ss, icy + 0 * ss, icx + 14 * ss, icy + 34 * ss), 180, 360, fill=BTN_PINK + (255,))
    d.rectangle((icx + 12 * ss, icy - 4 * ss, icx + 26 * ss, icy), fill=BTN_PINK + (255,))
    d.rectangle((icx + 17 * ss, icy - 9 * ss, icx + 21 * ss, icy + 5 * ss), fill=BTN_PINK + (255,))
    font = ImageFont.truetype(F_MONT, 46 * ss)
    txt = "FOLLOW SIS ROSE"
    tw = font.getlength(txt)
    tb = font.getbbox(txt)
    tx = pad + 120 * ss + (w - 140 * ss - tw) / 2
    ty = pad + h / 2 - (tb[1] + tb[3]) / 2
    d.text((tx, ty + 2 * ss), txt, font=font, fill=PLUM + (90,))
    d.text((tx, ty), txt, font=font, fill=(255, 255, 255, 255))
    return img.resize((img.width // ss, img.height // ss), Image.LANCZOS)

def make_hand():
    """Simple white pointing-hand cursor with plum outline."""
    ss = 4
    s = 120 * ss
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    u = ss
    def shape(dd, fill, grow):
        g = grow
        dd.rounded_rectangle((40 * u - g, 6 * u - g, 58 * u + g, 70 * u + g), radius=9 * u + g, fill=fill)      # index finger
        dd.rounded_rectangle((56 * u - g, 44 * u - g, 72 * u + g, 76 * u + g), radius=8 * u + g, fill=fill)     # middle
        dd.rounded_rectangle((70 * u - g, 50 * u - g, 85 * u + g, 80 * u + g), radius=7 * u + g, fill=fill)     # ring
        dd.rounded_rectangle((83 * u - g, 56 * u - g, 97 * u + g, 84 * u + g), radius=7 * u + g, fill=fill)     # pinky
        dd.rounded_rectangle((22 * u - g, 58 * u - g, 46 * u + g, 74 * u + g), radius=8 * u + g, fill=fill)     # thumb
        dd.rounded_rectangle((36 * u - g, 62 * u - g, 96 * u + g, 112 * u + g), radius=18 * u + g, fill=fill)   # palm
    shadow = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    shape(ImageDraw.Draw(shadow), PLUM + (90,), 0)
    shadow = shadow.transform(shadow.size, Image.AFFINE, (1, 0, -4 * u, 0, 1, -6 * u)).filter(ImageFilter.GaussianBlur(5 * u))
    img.alpha_composite(shadow)
    shape(d, PLUM + (255,), 3 * u)
    shape(d, (255, 255, 255, 255), 0)
    return img.resize((s // ss, s // ss), Image.LANCZOS)

def make_tagline():
    font = ImageFont.truetype(F_POPPINS, 54)
    lines = ["BERKONGSI ILMU,", "MENYEBAR INSPIRASI"]
    lh = 74
    img = Image.new("RGBA", (W, lh * 2 + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i, ln in enumerate(lines):
        tw = font.getlength(ln)
        d.text(((W - tw) / 2, 10 + i * lh), ln, font=font, fill=PLUM + (255,))
    # thin gold flourish lines
    y = 10 + lh * 2 + 12
    d.line((W / 2 - 210, y, W / 2 - 30, y), fill=GOLD + (255,), width=3)
    d.line((W / 2 + 30, y, W / 2 + 210, y), fill=GOLD + (255,), width=3)
    d.polygon([(W / 2, y - 9), (W / 2 + 9, y), (W / 2, y + 9), (W / 2 - 9, y)], fill=GOLD + (255,))
    return img


# ------------------------------------------------------------------ frame render
def build_frames(tmpdir):
    portrait = make_portrait()
    ring = make_ring()
    glow = make_glow(PORTRAIT_R + 40, LUX_PINK, 40)
    letters = letter_sprites()
    btn_normal = make_button(0.0)
    btn_pressed = make_button(1.0)
    hand = make_hand()
    tagline = make_tagline()

    rng = np.random.default_rng(20261116)
    # ambient gold sparkles
    amb = [(rng.uniform(80, W - 80), rng.uniform(180, H - 380), rng.uniform(14, 30), rng.uniform(0, 2 * math.pi), rng.uniform(1.2, 2.4)) for _ in range(26)]
    # portrait sparkles (burst 0.3–1.4s)
    ps = [(rng.uniform(0, 2 * math.pi), rng.uniform(PORTRAIT_R + 30, PORTRAIT_R + 120), rng.uniform(0.25, 0.9), rng.uniform(18, 34)) for _ in range(14)]
    # tagline sparkles
    ts = [(rng.uniform(220, 860), rng.uniform(TAG_Y - 20, TAG_Y + 170), rng.uniform(3.05, 3.55), rng.uniform(16, 30)) for _ in range(12)]

    name_letters = [l for l in letters]
    nl = len(name_letters)
    name_left = min(l[1] - l[0].width / 2 for l in name_letters)
    name_right = max(l[1] + l[0].width / 2 for l in name_letters)

    for f in range(N):
        t = f / FPS
        frame = background(t)

        # ambient sparkles (twinkle)
        for x, y, s, ph, sp in amb:
            a = 0.5 + 0.5 * math.sin(t * sp * 2 * math.pi / 2 + ph)
            a = a ** 3 * clamp(t / 0.6)
            if a > 0.03:
                paste_center(frame, with_alpha(star(int(s)), a * 0.85), x, y)

        # 1) portrait zoom-in (0.0–1.0) with glow and rotating gold ring
        p = prog(t, 0.0, 0.85)
        sc = 0.35 + 0.65 * ease_out_back(p, 1.3) if p < 1 else 1.0
        alpha = ease_out_cubic(prog(t, 0.0, 0.45))
        cx, cy = PORTRAIT_C
        g_pulse = 0.85 + 0.15 * math.sin(t * 2 * math.pi * 0.6)
        paste_center(frame, with_alpha(scaled(glow, sc), alpha * g_pulse), cx, cy)
        paste_center(frame, with_alpha(scaled(portrait, sc), alpha), cx, cy)   # portrait never rotates
        ring_rot = ring.rotate(-t * 40, resample=Image.BICUBIC)               # only the ring rotates
        paste_center(frame, with_alpha(scaled(ring_rot, sc), alpha), cx, cy)

        for th, rr, t0, s in ps:
            lt = prog(t, t0, t0 + 0.7)
            if 0 < lt < 1:
                a = math.sin(math.pi * lt)
                r2 = rr + 30 * lt
                paste_center(frame, with_alpha(star(int(s)), a), cx + r2 * math.cos(th + t * 0.4), cy + r2 * math.sin(th + t * 0.4))

        # 2) SIS ROSE letter pop (1.0–2.0) + gold shimmer
        for i, (img, lx, ly) in enumerate(name_letters):
            t0 = 1.0 + i * 0.07
            lp = prog(t, t0, t0 + 0.35)
            if lp <= 0:
                continue
            s = 0.3 + 0.7 * ease_out_back(lp, 2.4)
            spr = img
            sh_t = prog(t, 1.55, 2.05)
            if 0 < sh_t < 1:
                bandx = name_left + (name_right - name_left + 200) * sh_t - 100
                spr = shimmer(img, bandx - (lx - img.width / 2))
            spr = with_alpha(scaled(spr, s), ease_out_cubic(clamp(lp * 2)))
            yoff = (1 - ease_out_cubic(lp)) * 30
            paste_center(frame, spr, lx, ly + yoff)

        # 3) Follow button (2.0–3.0) with hand tap at 2.6s
        bp = prog(t, 2.0, 2.3)
        if bp > 0:
            tap = 2.6
            dt = t - tap
            press = 0.0
            bs = 0.5 + 0.5 * ease_out_back(bp, 2.0)
            if 0 <= dt < 0.08:
                press = dt / 0.08
            elif 0.08 <= dt < 0.4:
                k = (dt - 0.08) / 0.32
                press = math.exp(-5 * k) * math.cos(3 * math.pi * k)
            bs *= 1 - 0.07 * press
            b_img = btn_pressed if press > 0.5 else btn_normal
            paste_center(frame, with_alpha(scaled(b_img, bs), ease_out_cubic(bp)), *BTN_C)
            # ripple
            if 0 <= dt < 0.5:
                k = dt / 0.5
                rip = Image.new("RGBA", (W, 400), (0, 0, 0, 0))
                rr = 20 + 260 * ease_out_cubic(k)
                tx, ty = BTN_C[0] + 150, 200
                ImageDraw.Draw(rip).ellipse((tx - rr, ty - rr * 0.45, tx + rr, ty + rr * 0.45), outline=(255, 255, 255, int(200 * (1 - k))), width=5)
                frame.alpha_composite(rip, (0, BTN_C[1] - 200))
                for j in range(6):
                    th = j * math.pi / 3 + 0.3
                    paste_center(frame, with_alpha(star(22), 1 - k), tx + (40 + 120 * k) * math.cos(th), BTN_C[1] + (30 + 70 * k) * math.sin(th))
            # hand: glides in 2.25–2.55, taps 2.6, leaves 2.85–3.1
            hx_end, hy_end = BTN_C[0] + 150, BTN_C[1] + 6
            if 2.25 <= t < 3.1:
                hp = ease_in_out(prog(t, 2.25, 2.55))
                hx = hx_end + 220 * (1 - hp)
                hy = hy_end + 260 * (1 - hp)
                if 0 <= dt < 0.25:
                    hy += 10 * math.sin(math.pi * clamp(dt / 0.25))
                    hs = 1 - 0.08 * math.sin(math.pi * clamp(dt / 0.25))
                else:
                    hs = 1.0
                ha = 1.0
                if t >= 2.85:
                    lv = ease_in_out(prog(t, 2.85, 3.1))
                    hx += 160 * lv
                    hy += 200 * lv
                    ha = 1 - lv
                hand_s = scaled(hand, hs)
                # fingertip ~ (49,8) in the 120px sprite
                frame.alpha_composite(with_alpha(hand_s, ha), (int(hx - 49 * hs), int(hy - 8 * hs)))

        # 4) Tagline fade-in (3.0–3.45) + gold sparkles
        tp = prog(t, 3.0, 3.45)
        if tp > 0:
            yoff = (1 - ease_out_cubic(tp)) * 24
            frame.alpha_composite(with_alpha(tagline, ease_in_out(tp)), (0, int(TAG_Y + yoff)))
            for x, y, t0, s in ts:
                lt = prog(t, t0, t0 + 0.45)
                if 0 < lt < 1:
                    paste_center(frame, with_alpha(star(int(s)), math.sin(math.pi * lt)), x, y)

        # final elegant fade-out to pearl white (3.7–4.0)
        fo = ease_in_out(prog(t, 3.7, 4.0 - 1 / FPS))
        if fo > 0:
            frame = Image.blend(frame, Image.new("RGBA", (W, H), PEARL + (255,)), fo)
        # gentle fade-in from pearl at the very start
        fi = 1 - ease_out_cubic(prog(t, 0.0, 0.2))
        if fi > 0:
            frame = Image.blend(frame, Image.new("RGBA", (W, H), PEARL + (255,)), fi * 0.6)

        frame.convert("RGB").save(os.path.join(tmpdir, f"f{f:04d}.png"), compress_level=1)
        if f % 15 == 0:
            print(f"frame {f}/{N}", flush=True)


# ------------------------------------------------------------------ audio
def build_audio(path):
    rng = np.random.default_rng(7)
    n = int(SR * DUR)
    L = np.zeros(n, np.float64)
    Rr = np.zeros(n, np.float64)

    def add(sig, start, pan=0.0):
        i = int(start * SR)
        j = min(n, i + len(sig))
        L[i:j] += sig[: j - i] * math.sqrt((1 - pan) / 2) * math.sqrt(2)
        Rr[i:j] += sig[: j - i] * math.sqrt((1 + pan) / 2) * math.sqrt(2)

    # WHOOSH 0.0–0.85: noise through a sweeping resonant band-pass
    d = 0.85
    m = int(SR * d)
    noise = rng.standard_normal(m)
    tt = np.arange(m) / SR
    fc = 300 + 2600 * np.sin(np.pi * np.clip(tt / d, 0, 1)) ** 2
    out = np.zeros(m)
    low = band = 0.0
    q = 0.35
    for k in range(m):  # state-variable filter
        f = 2 * math.sin(math.pi * fc[k] / SR)
        low += f * band
        high = noise[k] - low - q * band
        band += f * high
        out[k] = band
    env = np.sin(np.pi * np.clip(tt / d, 0, 1)) ** 1.6
    whoosh = out * env * 0.20
    # stereo motion: pan from left to centre
    i = 0
    for k in range(0, m, 480):
        pan = -0.6 + 0.6 * (k / m)
        add(whoosh[k:k + 480], k / SR, pan)

    # POP at 1.0: pitch-dropping sine blip + soft body
    d = 0.12
    tt = np.arange(int(SR * d)) / SR
    freq = 180 + 520 * np.exp(-tt * 45)
    ph = 2 * np.pi * np.cumsum(freq) / SR
    pop = np.sin(ph) * np.exp(-tt * 38) * 0.55
    pop[: int(0.002 * SR)] *= np.linspace(0, 1, int(0.002 * SR))
    add(pop, 1.0)

    # CLICK at 2.6 (hand tap): crisp transient + gentle bounce
    d = 0.03
    tt = np.arange(int(SR * d)) / SR
    tick = (np.sin(2 * np.pi * 3200 * tt) * 0.5 + rng.standard_normal(len(tt)) * 0.25) * np.exp(-tt * 260)
    body = np.sin(2 * np.pi * 1100 * tt) * np.exp(-tt * 120) * 0.35
    add((tick + body) * 0.6, 2.6, 0.15)
    d = 0.18
    tt = np.arange(int(SR * d)) / SR
    freq = 520 + 380 * (1 - np.exp(-tt * 30))
    ph = 2 * np.pi * np.cumsum(freq) / SR
    bounce = np.sin(ph) * np.exp(-tt * 22) * np.sin(np.pi * np.clip(tt / 0.01, 0, 0.5)) * 0.22
    add(bounce, 2.68, 0.15)

    # crystal DING at 3.0: inharmonic bell partials, slight stereo detune
    d = 1.0
    tt = np.arange(int(SR * d)) / SR
    f0 = 1567.98  # G6
    partials = [(1.0, 1.0, 2.2), (2.76, 0.42, 4.0), (5.40, 0.20, 6.5), (8.93, 0.10, 9.0), (0.5, 0.18, 2.8)]
    for side, det in ((-0.5, 1.0), (0.5, 1.0015)):
        s = np.zeros_like(tt)
        for ratio, amp, dec in partials:
            s += amp * np.sin(2 * np.pi * f0 * ratio * det * tt) * np.exp(-tt * dec)
        s[: int(0.003 * SR)] *= np.linspace(0, 1, int(0.003 * SR))
        tail = np.clip((d - tt) / 0.15, 0, 1)  # land cleanly at 4.0 s
        add(s * tail * 0.20, 3.0, side)

    st = np.stack([L, Rr], 1)
    st /= np.max(np.abs(st)) / 10 ** (-4 / 20)   # peak -4 dBFS: clear but not loud
    pcm = (st * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def main():
    with tempfile.TemporaryDirectory() as tmp:
        build_frames(tmp)
        wav = os.path.join(tmp, "signature.wav")
        build_audio(wav)
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error",
            "-framerate", str(FPS), "-i", os.path.join(tmp, "f%04d.png"), "-i", wav,
            "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
            "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", str(SR),
            "-movflags", "+faststart", "-t", str(DUR), OUT,
        ], check=True)
    print("saved", OUT)


if __name__ == "__main__":
    main()
