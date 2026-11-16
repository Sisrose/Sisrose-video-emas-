"""Render video motivasi 'Jangan Terlalu Fikir Apa Orang Kata' (9:16, 1080x1920, 30fps).

Kegunaan:  python3 src/render.py <foto_sumber.png> <output.mp4> [--preview t1,t2,...]
"""
import math
import os
import subprocess
import sys
from functools import lru_cache
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

W, H, FPS, DUR = 1080, 1920, 30, 45.0
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, 'assets', 'fonts')

CREAM = (251, 243, 232)
PLUM = (74, 36, 102)
GOLD_L = (250, 226, 160)
GOLD_D = (184, 136, 58)

A = {}  # aset dikongsi (diisi oleh init)


# ---------------------------------------------------------------- utils
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_io(x):
    x = clamp(x)
    return 0.5 - 0.5 * math.cos(math.pi * x)


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_back(x):
    x = clamp(x)
    c1, c3 = 1.4, 2.4
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def lerp(a, b, t):
    return a + (b - a) * t


def with_alpha(img, k):
    if k >= 0.999:
        return img
    im = img.copy()
    a = im.getchannel('A').point(lambda v: int(v * k))
    im.putalpha(a)
    return im


def comp(base, spr, x, y, alpha=1.0):
    """Tampal sprite RGBA ke base pada (x,y) dengan klip sempadan."""
    if alpha <= 0.003:
        return
    x, y = int(round(x)), int(round(y))
    sw, sh = spr.size
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(base.width, x + sw), min(base.height, y + sh)
    if x1 <= x0 or y1 <= y0:
        return
    if (x0, y0, x1, y1) != (x, y, x + sw, y + sh):
        spr = spr.crop((x0 - x, y0 - y, x1 - x, y1 - y))
    base.alpha_composite(with_alpha(spr, alpha), (x0, y0))


def comp_c(base, spr, cx, cy, alpha=1.0, scale=1.0):
    if scale != 1.0:
        nw, nh = max(1, int(spr.width * scale)), max(1, int(spr.height * scale))
        spr = spr.resize((nw, nh), Image.BILINEAR)
    comp(base, spr, cx - spr.width / 2, cy - spr.height / 2, alpha)


def font(name, size, wght=None):
    f = ImageFont.truetype(os.path.join(FONTS, name), size)
    if wght is not None:
        try:
            f.set_variation_by_axes([wght])
        except Exception:
            pass
    return f


def gradient_v(w, h, c1, c2):
    t = np.linspace(0, 1, h)[:, None, None]
    arr = np.array(c1)[None, None] * (1 - t) + np.array(c2)[None, None] * t
    arr = np.broadcast_to(arr, (h, w, 3))
    return Image.fromarray(arr.astype(np.uint8), 'RGB')


def gradient_d(w, h, c1, c2):
    yy, xx = np.mgrid[0:h, 0:w]
    t = ((xx / max(1, w) + yy / max(1, h)) / 2)[..., None]
    arr = np.array(c1) * (1 - t) + np.array(c2) * t
    return Image.fromarray(arr.astype(np.uint8), 'RGB')


def soft_dot(r, color, hard=0.35):
    s = int(r * 2 + 4)
    yy, xx = np.mgrid[0:s, 0:s]
    d = np.hypot(xx - s / 2, yy - s / 2) / r
    a = np.clip(1 - d, 0, 1)
    a = np.where(d < hard, 1.0, a ** 1.6)
    arr = np.zeros((s, s, 4), np.uint8)
    arr[..., :3] = color
    arr[..., 3] = (np.clip(a, 0, 1) * 255).astype(np.uint8)
    return Image.fromarray(arr, 'RGBA')


def sparkle(size, color=(255, 240, 200)):
    s = size * 4
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = s / 2
    L, w = s * 0.48, s * 0.07
    d.polygon([(c, c - L), (c + w, c - w), (c + L, c), (c + w, c + w), (c, c + L), (c - w, c + w), (c - L, c), (c - w, c - w)],
              fill=color + (255,))
    glow = im.filter(ImageFilter.GaussianBlur(s * 0.08))
    out = Image.alpha_composite(glow, im)
    return out.resize((size, size), Image.LANCZOS)


def circle_mask(d, ss=4):
    m = Image.new('L', (d * ss, d * ss), 0)
    ImageDraw.Draw(m).ellipse((0, 0, d * ss - 1, d * ss - 1), fill=255)
    return m.resize((d, d), Image.LANCZOS)


def rrect_mask(w, h, r, ss=3):
    m = Image.new('L', (w * ss, h * ss), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w * ss - 1, h * ss - 1), r * ss, fill=255)
    return m.resize((w, h), Image.LANCZOS)


def perspective_coeffs(dst, src):
    """Pekali Image.PERSPECTIVE: titik output dst -> titik input src."""
    M, B = [], []
    for (x, y), (u, v) in zip(dst, src):
        M.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        M.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return np.linalg.solve(np.array(M, float), np.array(B, float)).tolist()


def rotate_y(img, theta, bg, cam=2600, scale=1.0):
    """Putaran 3D paksi-Y (kesan orbit)."""
    w, h = img.size
    if abs(math.cos(theta)) < 0.03:
        return bg.copy()
    pts = []
    for x, y in [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]:
        xr, z = x * math.cos(theta), x * math.sin(theta)
        k = cam / (cam + z) * scale
        pts.append((xr * k + w / 2, y * k + h / 2))
    co = perspective_coeffs(pts, [(0, 0), (w, 0), (w, h), (0, h)])
    out = img.transform((w, h), Image.PERSPECTIVE, co, Image.BILINEAR, fillcolor=(0, 0, 0, 0))
    res = bg.copy()
    res.alpha_composite(out)
    return res


# ---------------------------------------------------------------- assets
def init(photo_path):
    if A:
        return
    src = Image.open(photo_path).convert('RGB')
    s = src.width / 924.0  # skala skrin asal
    cx, cy, r = 462 * s, 700 * s, 207 * s  # bulatan foto dalam bingkai emas
    sq = src.crop((int(cx - r), int(cy - r), int(cx + r), int(cy + r)))
    sq = sq.resize((1000, 1000), Image.LANCZOS).filter(ImageFilter.UnsharpMask(2, 55, 2))
    A['photo'] = sq

    # latar belakang: foto dikabur + grade warm-cinematic + vinyet
    big = sq.resize((260, 260), Image.BILINEAR).filter(ImageFilter.GaussianBlur(22))
    bw, bh = int(W * 1.18), int(H * 1.18)
    big = big.resize((bh, bh), Image.BICUBIC).crop(((bh - bw) // 2, 0, (bh - bw) // 2 + bw, bh))
    arr = np.asarray(big).astype(np.float32)
    arr = arr * 0.40 * np.array([1.12, 0.90, 0.92]) + np.array([30, 12, 26])
    yy, xx = np.mgrid[0:bh, 0:bw]
    v = np.hypot((xx - bw / 2) / (bw * 0.62), (yy - bh * 0.45) / (bh * 0.62))
    arr *= np.clip(1.15 - v ** 2 * 0.75, 0.35, 1.1)[..., None]
    A['bg'] = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert('RGBA')

    # latar Follow (lavender cerah seperti jenama Sis Rose)
    g = gradient_v(W, H, (214, 198, 236), (250, 244, 248))
    gl = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(gl)
    for i, (yc, col) in enumerate([(1500, (230, 210, 240, 120)), (1650, (245, 225, 240, 140)), (1350, (255, 255, 255, 90))]):
        pts = [(x, yc + 90 * math.sin(x / 260 + i * 1.7)) for x in range(-20, W + 40, 20)]
        d.polygon(pts + [(W + 40, H), (-20, H)], fill=col)
    gl = gl.filter(ImageFilter.GaussianBlur(40))
    A['bg_follow'] = Image.alpha_composite(g.convert('RGBA'), gl)

    # light leaks
    A['leak_gold'] = soft_dot(520, (255, 196, 120), hard=0).point(lambda v: v)  # RGBA
    A['leak_rose'] = soft_dot(460, (255, 150, 190), hard=0)
    for k in ('leak_gold', 'leak_rose'):
        im = A[k]
        im.putalpha(im.getchannel('A').point(lambda v: int(v * 0.33)))

    A['dots'] = [soft_dot(r, (255, 236, 200), hard=0.25) for r in (3, 5, 7, 10, 14)]
    A['bokeh'] = [soft_dot(r, c, hard=0.6) for r, c in [(18, (255, 220, 180)), (26, (255, 200, 210)), (34, (255, 230, 190))]]
    for b in A['bokeh']:
        b.putalpha(b.getchannel('A').point(lambda v: int(v * 0.28)))
    A['spark'] = [sparkle(s) for s in (22, 34, 50, 70)]

    rng = np.random.default_rng(3)
    A['particles'] = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(12, 45), rng.uniform(0, 6.28),
                       int(rng.integers(0, 5)), rng.uniform(0.3, 1.0)) for _ in range(46)]
    A['bokehs'] = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(6, 18), int(rng.integers(0, 3))) for _ in range(12)]

    # bingkai cincin emas
    D = 720
    A['ring'] = make_ring(D)
    A['ring_follow'] = make_ring(D, follow=True)
    A['mask_D'] = circle_mask(D)
    A['paper'] = [make_paper(c, i) for i, c in enumerate([(78, 40, 84), (216, 164, 170), (244, 232, 216)])]
    A['strip'] = make_strip(820, 150)
    A['texts'] = {}


def make_ring(D, follow=False):
    pad = 70
    S = D + pad * 2
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    th = 16
    outer = circle_mask(D + th * 2)
    inner = circle_mask(D)
    ring = Image.new('L', (S, S), 0)
    ring.paste(outer, (pad - th, pad - th))
    hole = Image.new('L', (S, S), 0)
    hole.paste(inner, (pad, pad))
    ring = ImageChops.subtract(ring, hole)
    gold = gradient_d(S, S, (255, 236, 180), (150, 104, 40)).convert('RGBA')
    # kilau logam
    sheen = gradient_v(S, S, (255, 250, 230), (120, 80, 30)).convert('RGBA')
    gold = Image.blend(gold, sheen, 0.35)
    glow = Image.new('RGBA', (S, S), (255, 214, 150, 0))
    glow.putalpha(ring.filter(ImageFilter.GaussianBlur(18)).point(lambda v: int(v * (0.5 if not follow else 0.35))))
    shadow = Image.new('RGBA', (S, S), (20, 5, 25, 0))
    shadow.putalpha(ring.filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * 0.6)))
    im = Image.alpha_composite(im, glow)
    im.alpha_composite(shadow, (0, 6))
    gold.putalpha(ring)
    im = Image.alpha_composite(im, gold)
    # mutiara kecil di sekeliling cincin
    d = ImageDraw.Draw(im)
    for k in range(10):
        a = k / 10 * 2 * math.pi + 0.3
        rr = D / 2 + th + 24
        x, y = S / 2 + rr * math.cos(a), S / 2 + rr * math.sin(a)
        d.ellipse((x - 5, y - 5, x + 5, y + 5), fill=(255, 238, 200, 230))
    return im


def make_paper(color, seed):
    """Jalur kertas koyak (paper cut) dengan tepi serat & bayang."""
    rng = np.random.default_rng(seed + 11)
    bh = int(H * 1.25)
    m = 140
    S = (W, bh + 2 * m)

    def edge(y0, sign):
        pts = []
        ph = rng.uniform(0, 6)
        for x in range(-30, W + 60, 16):
            pts.append((x, y0 + sign * (rng.uniform(-13, 13) + 26 * math.sin(x / 140 + ph) + 12 * math.sin(x / 47 + ph * 2))))
        return pts

    top, bot = edge(m, 1), edge(m + bh, -1)
    poly = top + bot[::-1]
    im = Image.new('RGBA', S, (0, 0, 0, 0))
    sh = Image.new('L', S, 0)
    ImageDraw.Draw(sh).polygon([(x, y + 14) for x, y in poly], fill=150)
    sh = sh.filter(ImageFilter.GaussianBlur(16))
    shadow = Image.new('RGBA', S, (15, 5, 20, 0))
    shadow.putalpha(sh)
    im = Image.alpha_composite(im, shadow)
    d = ImageDraw.Draw(im)
    rim = [(x, y - 7) for x, y in top] + [(x, y + 7) for x, y in bot[::-1]]
    d.polygon(rim, fill=(255, 252, 245, 255))
    d.polygon(poly, fill=tuple(color) + (255,))
    # tekstur kertas
    arr = np.asarray(im).astype(np.int16)
    noise = rng.normal(0, 7, (S[1], S[0], 1)).astype(np.int16)
    arr[..., :3] = np.clip(arr[..., :3] + noise, 0, 255)
    return Image.fromarray(arr.astype(np.uint8), 'RGBA'), m, bh


def make_strip(w, h):
    rng = np.random.default_rng(5)
    S = (w + 60, h + 60)
    pts = []
    for x in range(0, w + 1, 14):
        pts.append((30 + x, 30 + rng.uniform(-5, 5)))
    for y in range(0, h + 1, 12):
        pts.append((30 + w + rng.uniform(-6, 6), 30 + y))
    for x in range(w, -1, -14):
        pts.append((30 + x, 30 + h + rng.uniform(-5, 5)))
    for y in range(h, -1, -12):
        pts.append((30 + rng.uniform(-6, 6), 30 + y))
    im = Image.new('RGBA', S, (0, 0, 0, 0))
    sh = Image.new('L', S, 0)
    ImageDraw.Draw(sh).polygon([(x + 4, y + 8) for x, y in pts], fill=140)
    shadow = Image.new('RGBA', S, (10, 0, 15, 0))
    shadow.putalpha(sh.filter(ImageFilter.GaussianBlur(9)))
    im = Image.alpha_composite(im, shadow)
    ImageDraw.Draw(im).polygon(pts, fill=(246, 236, 222, 255))
    arr = np.asarray(im).astype(np.int16)
    arr[..., :3] = np.clip(arr[..., :3] + rng.normal(0, 6, (S[1], S[0], 1)), 0, 255)
    return Image.fromarray(arr.astype(np.uint8), 'RGBA')


# ---------------------------------------------------------------- text
def word_sprite(word, size, style):
    key = (word, size, style)
    if key in A['texts']:
        return A['texts'][key]
    if style == 'hl':
        f = font('Montserrat.ttf', int(size), 800)
    elif style == 'paper':
        f = font('Montserrat.ttf', int(size), 800)
    elif style == 'sans':
        f = font('Montserrat.ttf', int(size), 500)
    else:
        f = font('Montserrat.ttf', int(size), 600)
    bb = f.getbbox(word, anchor='ls')
    pad = 40
    w, h = bb[2] - bb[0] + pad * 2, bb[3] - bb[1] + pad * 2
    mask = Image.new('L', (w, h), 0)
    ImageDraw.Draw(mask).text((pad - bb[0], pad - bb[1]), word, font=f, fill=255, anchor='ls')
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    if style == 'paper':
        fill = Image.new('RGBA', (w, h), (110, 32, 72, 255))
        fill.putalpha(mask)
        out = fill
    else:
        sh = Image.new('RGBA', (w, h), (25, 8, 25, 0))
        sh.putalpha(mask.filter(ImageFilter.GaussianBlur(7)).point(lambda v: int(v * 0.85)))
        out.alpha_composite(sh, (0, 3))
        if style == 'hl':
            glow = Image.new('RGBA', (w, h), (255, 205, 120, 0))
            glow.putalpha(mask.filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.6)))
            out = Image.alpha_composite(out, glow)
            fill = gradient_v(w, h, (255, 240, 190), (214, 160, 70)).convert('RGBA')
        else:
            fill = Image.new('RGBA', (w, h), CREAM + (255,))
        fill.putalpha(mask)
        out = Image.alpha_composite(out, fill)
    res = (out, pad, f.getlength(' '), bb)
    A['texts'][key] = res
    return res


class Block:
    """Blok teks animasi: senarai baris (teks, saiz, masa_mula, gaya).
    Perkataan berbalut *...* diserlahkan (emas)."""

    def __init__(self, lines, cy, t_out, line_gap=1.32):
        self.items = []
        self.strips = []
        self.t_out = t_out
        lines = [(tx, sz * 1.1, t0, st) for tx, sz, t0, st in lines]
        heights = [s * line_gap for _, s, _, _ in lines]
        y = cy - sum(heights) / 2
        for (text, size, t0, style), lh in zip(lines, heights):
            words = text.split(' ')
            sprs = []
            for wd in words:
                hl = wd.startswith('*')
                wd2 = wd.strip('*')
                st = ('paper' if style == 'paper' else 'hl') if hl else style
                sz = size * (1.08 if hl and style != 'paper' else 1.0)
                sprs.append((word_sprite(wd2, sz, st), hl))
            space = sprs[0][0][2] * 0.95
            widths = [sp[3][2] - sp[3][0] for sp, _ in sprs]
            total = sum(widths) + space * (len(widths) - 1)
            x = W / 2 - total / 2
            base = y + lh * 0.72
            if style == 'paper':
                self.strips.append((W / 2, base - size * 0.33, total + 120, t0))
            for i, ((sp, hl), wdt) in enumerate(zip(sprs, widths)):
                img, pad, _, bb = sp
                self.items.append(dict(img=img, x=x - pad, y=base - pad + bb[1],
                                       t0=t0 + i * 0.09, hl=hl, cx=x + wdt / 2, cy=base - size * 0.35))
                x += wdt + space
            y += lh

    def draw(self, frame, t):
        out = clamp((self.t_out - t) / 0.45)
        if out <= 0:
            return
        for sx, sy, sw, t0 in self.strips:
            p = ease_out((t - t0 + 0.25) / 0.55)
            if p <= 0:
                continue
            st = A['strip'].resize((int(sw + 60), A['strip'].height), Image.BILINEAR)
            cw = int(st.width * p)
            if cw < 2:
                continue
            st = st.crop((0, 0, cw, st.height)).rotate(-1.5, Image.BILINEAR, expand=True)
            comp(frame, st, sx - (sw + 60) / 2, sy - st.height / 2, out)
        for it in self.items:
            p = (t - it['t0']) / 0.6
            if p <= 0:
                continue
            a = ease_out(p) * out
            dy = (1 - ease_out(p)) * 30 - (1 - out) * 18
            img = it['img']
            if it['hl']:
                s = 1.22 - 0.22 * ease_back(p)
                if abs(s - 1) > 0.003:
                    comp_c(frame, img, it['cx'], it['cy'] + dy, a, s)
                else:
                    comp(frame, img, it['x'], it['y'] + dy, a)
                # kilauan kecil di sekitar perkataan
                q = t - it['t0']
                if 0 < q < 1.6:
                    for k in range(3):
                        ang = k * 2.1 + it['cx'] * 0.01
                        sx = it['cx'] + math.cos(ang) * (60 + 30 * k)
                        sy = it['cy'] - 40 + math.sin(ang) * 40
                        tw = math.sin(clamp((q - k * 0.15) / 1.2) * math.pi)
                        comp_c(frame, A['spark'][1], sx, sy, tw * out, 0.6 + 0.6 * tw)
            else:
                comp(frame, img, it['x'], it['y'] + dy, a)


# ---------------------------------------------------------------- layers
def background(t, follow=False):
    if follow:
        return A['bg_follow'].copy()
    bg = A['bg']
    z = 1.0 + 0.06 * (t / DUR)
    bw, bh = W * 1.18 / z / 1.18 * 1.0, H / z
    cw, ch = W / (1.0 + 0.0) / z * 1.0, H / z
    ox = (bg.width - cw) / 2 + 40 * math.sin(t / 9)
    oy = (bg.height - ch) / 2 + 50 * math.cos(t / 11)
    fr = bg.resize((W, H), Image.BILINEAR, box=(ox, oy, ox + cw, oy + ch))
    comp_c(fr, A['leak_gold'], 200 + 160 * math.sin(t / 5), 260 + 80 * math.cos(t / 7))
    comp_c(fr, A['leak_rose'], 900 + 120 * math.cos(t / 6), 1500 + 140 * math.sin(t / 8))
    return fr


def particles(fr, t, dim=1.0, color_bright=False):
    for x0, y0, sp, ph, ri, al in A['particles']:
        y = (y0 - sp * t) % (H + 40) - 20
        x = x0 + 18 * math.sin(t * 0.6 + ph)
        tw = 0.55 + 0.45 * math.sin(t * 2.2 + ph * 3)
        comp_c(fr, A['dots'][ri], x, y, al * tw * dim)
    for x0, y0, sp, bi in A['bokehs']:
        y = (y0 - sp * t) % (H + 120) - 60
        comp_c(fr, A['bokeh'][bi], x0 + 30 * math.sin(t / 3 + x0), y, dim)


def portrait(zoom=1.0, fx=0.5, fy=0.5, follow=False):
    """Sprite potret bulat + cincin emas (wajah asal, tanpa ubahsuai)."""
    D = 720
    ph = A['photo']
    zoom = max(1.0, zoom)
    cs = ph.width / zoom
    cx = clamp(fx * ph.width, cs / 2, ph.width - cs / 2)
    cy = clamp(fy * ph.height, cs / 2, ph.height - cs / 2)
    crop = ph.resize((D, D), Image.LANCZOS if zoom > 1.01 else Image.BILINEAR,
                     box=(cx - cs / 2, cy - cs / 2, cx + cs / 2, cy + cs / 2)).convert('RGBA')
    crop.putalpha(A['mask_D'])
    ring = A['ring_follow' if follow else 'ring'].copy()
    pad = (ring.width - D) // 2
    base = Image.new('RGBA', ring.size, (0, 0, 0, 0))
    base.alpha_composite(crop, (pad, pad))
    return Image.alpha_composite(base, ring)


def draw_portrait(fr, cx, cy, diam, zoom=1.0, fx=0.5, fy=0.5, alpha=1.0, ytheta=0.0, follow=False):
    spr = portrait(zoom, fx, fy, follow)
    s = diam / 720
    nw, nh = int(spr.width * s), int(spr.height * s)
    spr = spr.resize((nw, nh), Image.BILINEAR)
    if abs(ytheta) > 0.01:
        cw = max(2, int(nw * abs(math.cos(ytheta))))
        spr = spr.resize((cw, nh), Image.BILINEAR)
    comp_c(fr, spr, cx, cy, alpha)


def orbit(fr, t, cx, cy, R, front, alpha=1.0, tilt=-0.35, squash=0.28):
    """Kesan ORBIT: komet cahaya mengelilingi potret (lapisan belakang/depan)."""
    ct, st = math.cos(tilt), math.sin(tilt)
    for c in range(3):
        head = t * 1.25 + c * 2.094
        for k in range(26):
            th = head - k * 0.05
            dep = math.sin(th)
            if (dep >= 0) != front:
                continue
            x, y = R * math.cos(th), R * squash * math.sin(th)
            X, Y = cx + x * ct - y * st, cy + x * st + y * ct
            fade = (1 - k / 26) ** 1.5
            depth = 0.65 + 0.35 * dep
            ri = 3 if k == 0 else (2 if k < 4 else 1)
            comp_c(fr, A['dots'][ri], X, Y, alpha * fade * depth)
            if k == 0:
                comp_c(fr, A['spark'][2], X, Y, alpha * depth, 0.7 + 0.3 * depth)


# ---------------------------------------------------------------- scenes
def block_cache(key, fn):
    if key not in A:
        A[key] = fn()
    return A[key]


def scene1(t, gt):  # Hook — orbit cahaya mengelilingi teks
    fr = background(gt)
    particles(fr, gt)
    cx, cy = 540, 930
    a = ease_io(t / 1.2)
    orbit(fr, gt, cx, cy, 470, False, a)
    b = block_cache('b1', lambda: Block([
        ('Sampai bila kita', 64, 0.8, 'normal'),
        ('nak hidup ikut apa', 64, 1.25, 'normal'),
        ('orang fikir', 64, 1.7, 'normal'),
        ('tentang kita?', 64, 2.1, 'normal')], cy, 5.9))
    b.draw(fr, t)
    orbit(fr, gt, cx, cy, 470, True, a)
    return fr


def scene2(t, gt):  # Paper cut
    fr = background(gt)
    particles(fr, gt)
    b = block_cache('b2', lambda: Block([
        ('Kalau kita buat,', 66, 0.4, 'normal'),
        ('*ORANG* *BERCAKAP.*', 74, 1.5, 'paper')], 930, 4.9, 1.7))
    b.draw(fr, t)
    return fr


def scene3(t, gt):  # zoom
    fr = background(gt)
    particles(fr, gt)
    b = block_cache('b3', lambda: Block([
        ('Kalau kita', 64, 0.4, 'normal'),
        ('tak buat pun,', 64, 0.8, 'normal'),
        ('orang tetap', 64, 1.4, 'normal'),
        ('ada cerita.', 64, 1.8, 'normal')], 930, 5.4))
    b.draw(fr, t)
    return fr


def glass_panel(fr, x0, y0, x1, y1, alpha, t_sweep):
    w, h = int(x1 - x0), int(y1 - y0)
    region = fr.crop((int(x0), int(y0), int(x0) + w, int(y0) + h)).convert('RGB')
    small = region.resize((max(1, w // 4), max(1, h // 4)), Image.BILINEAR).filter(ImageFilter.GaussianBlur(6))
    blur = small.resize((w, h), Image.BILINEAR).convert('RGBA')
    tint = Image.new('RGBA', (w, h), (255, 245, 240, 38))
    blur = Image.alpha_composite(blur, tint)
    # kilauan atas
    hl = gradient_v(w, h, (255, 255, 255), (255, 255, 255)).convert('RGBA')
    ga = np.linspace(60, 0, h)[:, None].repeat(w, 1).astype(np.uint8)
    hl.putalpha(Image.fromarray(ga))
    blur = Image.alpha_composite(blur, hl)
    # sapuan cahaya
    if 0 <= t_sweep <= 1:
        sw = Image.new('L', (w, h), 0)
        sx = -300 + (w + 600) * t_sweep
        ImageDraw.Draw(sw).polygon([(sx, 0), (sx + 120, 0), (sx - 80, h), (sx - 200, h)], fill=90)
        sw = sw.filter(ImageFilter.GaussianBlur(20))
        swl = Image.new('RGBA', (w, h), (255, 255, 255, 0))
        swl.putalpha(sw)
        blur = Image.alpha_composite(blur, swl)
    mask = rrect_mask(w, h, 46)
    border = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(border).rounded_rectangle((1, 1, w - 2, h - 2), 46, outline=(255, 240, 220, 140), width=3)
    blur.putalpha(mask)
    blur = Image.alpha_composite(blur, border)
    # bayang lembut
    sh = Image.new('RGBA', (w + 80, h + 80), (10, 0, 15, 0))
    sm = Image.new('L', (w + 80, h + 80), 0)
    sm.paste(mask, (40, 52))
    sh.putalpha(sm.filter(ImageFilter.GaussianBlur(22)).point(lambda v: int(v * 0.45)))
    comp(fr, sh, x0 - 40, y0 - 40, alpha)
    comp(fr, blur, x0, y0, alpha)


def scene4(t, gt):  # Glass
    fr = background(gt)
    particles(fr, gt)
    p = ease_out((t - 0.2) / 0.9)
    out = clamp((6.3 - t) / 0.45)
    if p > 0:
        dy = (1 - p) * 60
        glass_panel(fr, 70, 640 + dy, 1010, 1240 + dy, p * out, (t - 0.4) / 1.4)
    b = block_cache('b4', lambda: Block([
        ('Jadi sampai bila', 58, 0.8, 'normal'),
        ('kita nak habiskan', 58, 1.3, 'normal'),
        ('tenaga memikirkan', 58, 1.8, 'normal'),
        ('pandangan orang?', 58, 2.3, 'normal')], 940, 6.3))
    b.draw(fr, t)
    return fr


def scene5(t, gt):  # Teruskan — orbit
    fr = background(gt)
    particles(fr, gt, 1.0 + 0.4 * clamp((t - 4) / 1))
    cx, cy = 540, 930
    orbit(fr, gt * 1.1, cx, cy, 480, False)
    b = block_cache('b5', lambda: Block([
        ('Selagi apa yang', 58, 0.5, 'normal'),
        ('kita buat itu baik', 58, 1.0, 'normal'),
        ('dan tidak menyusahkan', 58, 1.5, 'normal'),
        ('sesiapa,', 58, 2.0, 'normal'),
        ('*TERUSKAN.*', 96, 4.2, 'normal')], cy, 6.85, 1.45))
    b.draw(fr, t)
    orbit(fr, gt * 1.1, cx, cy, 480, True)
    return fr


def scene6(t, gt):  # Ending
    fr = background(gt)
    particles(fr, gt)
    b = block_cache('b6', lambda: Block([
        ('Kita yang menjalani', 58, 0.4, 'normal'),
        ('kehidupan ini,', 58, 0.9, 'normal'),
        ('bukan orang yang', 58, 1.5, 'normal'),
        ('sibuk mengulas', 58, 2.0, 'normal'),
        ('*KEHIDUPAN* *KITA.*', 74, 3.6, 'normal')], 930, 6.2, 1.45))
    b.draw(fr, t)
    return fr


def comment_icon(size):
    s = size * 3
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((s * 0.06, s * 0.1, s * 0.94, s * 0.72), s * 0.2, fill=GOLD_L + (255,))
    d.polygon([(s * 0.26, s * 0.66), (s * 0.24, s * 0.92), (s * 0.48, s * 0.68)], fill=GOLD_L + (255,))
    for i in range(3):
        x = s * (0.32 + 0.18 * i)
        d.ellipse((x - s * 0.05, s * 0.36, x + s * 0.05, s * 0.46), fill=PLUM + (255,))
    return im.resize((size, size), Image.LANCZOS)


def scene_cta(t, gt):
    fr = background(gt)
    particles(fr, gt)
    p = ease_out(t / 0.9)
    glass_panel(fr, 80, 640 + (1 - p) * 60, 1000, 1260 + (1 - p) * 60, p, (t - 0.3) / 1.4)
    ic = block_cache('icon', lambda: comment_icon(120))
    comp_c(fr, ic, 540, 760 + (1 - p) * 60, ease_out((t - 0.3) / 0.6), 0.8 + 0.2 * ease_back((t - 0.3) / 0.6))
    b = block_cache('b7', lambda: Block([
        ('Pernah alami', 60, 0.4, 'normal'),
        ('perkara macam ni?', 60, 0.8, 'normal'),
        ('Kongsikan pengalaman awak', 42, 1.5, 'sans'),
        ('di ruangan komen.', 42, 1.8, 'sans')], 1010, 99))
    b.draw(fr, t)
    return fr


def follow_assets():
    name_f = font('Playfair.ttf', 160, 900)
    txt = 'SIS ROSE'
    bb = name_f.getbbox(txt)
    w, h = bb[2] - bb[0] + 80, bb[3] - bb[1] + 80
    m = Image.new('L', (w, h), 0)
    ImageDraw.Draw(m).text((40 - bb[0], 40 - bb[1]), txt, font=name_f, fill=255)
    outline = m.filter(ImageFilter.MaxFilter(9))
    name = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    glow = Image.new('RGBA', (w, h), (255, 120, 190, 0))
    glow.putalpha(outline.filter(ImageFilter.GaussianBlur(22)).point(lambda v: int(v * 0.9)))
    name = Image.alpha_composite(name, glow)
    sh = Image.new('RGBA', (w, h), (50, 10, 60, 0))
    sh.putalpha(outline.filter(ImageFilter.GaussianBlur(6)).point(lambda v: int(v * 0.55)))
    name.alpha_composite(sh, (0, 6))
    g = gradient_v(w, h, (246, 220, 150), (176, 128, 52)).convert('RGBA')
    g.putalpha(outline)
    name = Image.alpha_composite(name, g)
    f = gradient_v(w, h, (255, 255, 255), (255, 214, 232)).convert('RGBA')
    f.putalpha(m)
    A['name_mask'] = m
    name = Image.alpha_composite(name, f)

    bw, bh = 660, 124
    S = (bw + 60, bh + 70)
    btn = Image.new('RGBA', S, (0, 0, 0, 0))
    shm = Image.new('L', S, 0)
    ImageDraw.Draw(shm).rounded_rectangle((30, 42, 30 + bw, 42 + bh), bh // 2, fill=120)
    sh = Image.new('RGBA', S, (150, 60, 110, 0))
    sh.putalpha(shm.filter(ImageFilter.GaussianBlur(14)))
    btn = Image.alpha_composite(btn, sh)
    gold = gradient_v(bw + 10, bh + 10, (250, 228, 170), (190, 140, 60)).convert('RGBA')
    gold.putalpha(rrect_mask(bw + 10, bh + 10, (bh + 10) // 2))
    btn.alpha_composite(gold, (25, 25))
    pink = gradient_v(bw - 4, bh - 4, (246, 150, 184), (232, 104, 146)).convert('RGBA')
    gl = Image.new('RGBA', (bw - 4, bh - 4), (255, 255, 255, 0))
    ImageDraw.Draw(gl).rounded_rectangle((14, 6, bw - 18, bh // 2 - 4), bh // 4, fill=(255, 255, 255, 70))
    pink = Image.alpha_composite(pink, gl.filter(ImageFilter.GaussianBlur(4)))
    pink.putalpha(rrect_mask(bw - 4, bh - 4, (bh - 4) // 2))
    btn.alpha_composite(pink, (32, 32))
    d = ImageDraw.Draw(btn)
    icx, icy, r = 32 + 70, 30 + bh // 2 + 2, 38
    d.ellipse((icx - r, icy - r, icx + r, icy + r), fill=(255, 255, 255, 255))
    pc = (232, 104, 146, 255)
    d.ellipse((icx - 14, icy - 22, icx + 6, icy - 2), fill=pc)
    d.pieslice((icx - 24, icy + 2, icx + 16, icy + 40), 180, 360, fill=pc)
    d.rectangle((icx + 14, icy - 4, icx + 26, icy - 1), fill=pc)
    d.rectangle((icx + 18, icy - 9, icx + 21, icy + 4), fill=pc)
    bf = font('Montserrat.ttf', 46, 800)
    txt = 'FOLLOW SIS ROSE'
    tb = bf.getbbox(txt)
    tx = 32 + 140 + (bw - 160 - (tb[2] - tb[0])) / 2 - tb[0]
    ty = 30 + bh / 2 + 2 - (tb[1] + tb[3]) / 2
    d.text((tx + 1, ty + 2), txt, font=bf, fill=(170, 60, 100, 120))
    d.text((tx, ty), txt, font=bf, fill=(255, 255, 255, 255))

    # kursor tangan ringkas
    hs = 150
    hand = Image.new('RGBA', (hs * 3, hs * 3), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hand)
    k = 3
    poly = [(46, 10), (60, 10), (64, 18), (64, 62), (72, 56), (84, 58), (88, 66), (98, 62), (110, 66), (112, 74),
            (122, 72), (132, 78), (134, 92), (130, 120), (120, 140), (64, 140), (40, 104), (26, 84), (28, 74),
            (38, 72), (46, 82), (42, 18)]
    poly = [(x * k, y * k) for x, y in poly]
    hd.polygon(poly, fill=(255, 255, 255, 255), outline=(60, 30, 70, 255), width=12)
    for x in (88, 110):
        hd.line([(x * k, 70 * k), (x * k, 96 * k)], fill=(60, 30, 70, 255), width=8)
    hand = hand.resize((hs, hs), Image.LANCZOS)
    hsh = Image.new('RGBA', hand.size, (60, 20, 60, 0))
    hsh.putalpha(hand.getchannel('A').filter(ImageFilter.GaussianBlur(6)).point(lambda v: v // 3))
    handf = Image.new('RGBA', (hs + 20, hs + 20), (0, 0, 0, 0))
    handf.alpha_composite(hsh, (8, 12))
    handf.alpha_composite(hand, (0, 0))
    return name, btn, handf


def follow_extra():
    """Aset tambahan penutup: latar warna-warni, sinar cahaya, hati."""
    R = 1700
    yy, xx = np.mgrid[0:R, 0:R]
    ang = np.arctan2(yy - R / 2, xx - R / 2)
    dist = np.hypot(yy - R / 2, xx - R / 2) / (R / 2)
    rays = (0.5 + 0.5 * np.cos(ang * 14)) ** 6 * np.clip(1 - dist, 0, 1) ** 1.3
    arr = np.zeros((R, R, 4), np.uint8)
    arr[..., :3] = (255, 236, 200)
    arr[..., 3] = (rays * 120).astype(np.uint8)
    rays_im = Image.fromarray(arr, 'RGBA').filter(ImageFilter.GaussianBlur(4))

    def grad(c1, c2, c3):
        t = np.linspace(0, 1, H)[:, None]
        top = np.array(c1) * (1 - np.clip(t * 2, 0, 1)) + np.array(c2) * np.clip(t * 2, 0, 1)
        bot = np.array(c2) * (1 - np.clip(t * 2 - 1, 0, 1)) + np.array(c3) * np.clip(t * 2 - 1, 0, 1)
        g = np.where(t < 0.5, top, bot)[:, None, :].repeat(W, 1)
        return Image.fromarray(g.astype(np.uint8), 'RGB').convert('RGBA')
    g1 = grad((255, 150, 196), (196, 96, 200), (84, 36, 128))
    g2 = grad((255, 186, 150), (226, 104, 176), (104, 40, 140))

    hs = 90
    hm = Image.new('L', (hs * 4, hs * 4), 0)
    d = ImageDraw.Draw(hm)
    S = hs * 4
    d.ellipse((S * 0.08, S * 0.12, S * 0.52, S * 0.56), fill=255)
    d.ellipse((S * 0.48, S * 0.12, S * 0.92, S * 0.56), fill=255)
    d.polygon([(S * 0.12, S * 0.44), (S * 0.88, S * 0.44), (S * 0.5, S * 0.9)], fill=255)
    hm = hm.resize((hs, hs), Image.LANCZOS)
    hearts = []
    for col in [(255, 92, 150), (255, 160, 200), (255, 214, 120)]:
        hcol = gradient_v(hs, hs, tuple(min(255, c + 50) for c in col), col).convert('RGBA')
        hcol.putalpha(hm)
        big = Image.new('RGBA', (hs + 40, hs + 40), (0, 0, 0, 0))
        gl = Image.new('RGBA', (hs + 40, hs + 40), col + (0,))
        gm = Image.new('L', (hs + 40, hs + 40), 0)
        gm.paste(hm, (20, 20))
        gl.putalpha(gm.filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * 0.7)))
        big = Image.alpha_composite(big, gl)
        big.alpha_composite(hcol, (20, 20))
        hearts.append(big)
    halo = soft_dot(470, (255, 190, 225), hard=0)
    rng = np.random.default_rng(9)
    hp = [(rng.uniform(60, W - 60), rng.uniform(0, 1), rng.uniform(0.35, 0.8), int(rng.integers(0, 3)),
           rng.uniform(0, 6.28), rng.uniform(0.3, 0.7)) for _ in range(16)]
    return dict(rays=rays_im, g1=g1, g2=g2, hearts=hearts, halo=halo, hp=hp)


def scene_follow(t, gt):
    """Penutup berwarna: latar pink-ungu beranimasi, sinar cahaya, halo, orbit,
    hati terapung, nama berkilau & butang FOLLOW yang ditekan."""
    name, btn, hand = block_cache('follow', follow_assets)
    X = block_cache('follow_x', follow_extra)
    tt = max(0.0, t)
    fr = Image.blend(X['g1'], X['g2'], 0.5 + 0.5 * math.sin(gt * 1.3))
    pcx, pcy = 540, 720
    # sinar cahaya berputar di belakang potret
    ra = ease_out(tt / 1.0)
    rays = X['rays'].rotate(gt * 14 % 360, Image.BILINEAR)
    comp_c(fr, rays, pcx, pcy, ra * 0.9)
    # halo bernadi
    comp_c(fr, X['halo'], pcx, pcy, 0.55 * ra, 1.0 + 0.05 * math.sin(gt * 4))
    particles(fr, gt, 1.0)
    # hati terapung ke atas
    for x0, ph0, sp, hi, ph, sc in X['hp']:
        y = H + 80 - ((ph0 + tt * sp * 0.45) % 1.0) * (H + 200)
        comp_c(fr, X['hearts'][hi], x0 + 30 * math.sin(gt * 1.5 + ph), y, 0.75 * ra, sc)
    p = ease_back(tt / 0.9)
    D = 600 * (0.65 + 0.35 * p)
    orbit(fr, gt * 1.2, pcx, pcy, 420, False, ra)
    draw_portrait(fr, pcx, pcy, D, zoom=1.0 + 0.03 * tt / 4.5, fy=0.5, alpha=ease_out(tt / 0.4), follow=True)
    orbit(fr, gt * 1.2, pcx, pcy, 420, True, ra)
    # nama dengan kilauan menyapu
    pn = ease_out((tt - 0.4) / 0.7)
    if pn > 0:
        nm = name.copy()
        q = (tt - 1.1) / 0.9
        if 0 < q < 1:
            w, h = nm.size
            band = Image.new('L', (w, h), 0)
            sx = -200 + (w + 400) * ease_io(q)
            ImageDraw.Draw(band).polygon([(sx, 0), (sx + 70, 0), (sx - 30, h), (sx - 100, h)], fill=255)
            band = ImageChops.multiply(band.filter(ImageFilter.GaussianBlur(10)), A['name_mask'])
            sh = Image.new('RGBA', (w, h), (255, 236, 170, 0))
            sh.putalpha(band)
            nm = Image.alpha_composite(nm, sh)
        comp_c(fr, nm, 540, 1170 + (1 - pn) * 50, pn, 0.9 + 0.1 * pn)
    # butang
    pb = ease_back((tt - 0.85) / 0.7)
    tap = 2.05
    press = 1.0 - 0.07 * math.sin(math.pi * clamp((t - tap) / 0.25))
    pulse = 1.0 + 0.03 * math.sin(gt * 6) * (t > tap + 0.3)
    bx, by = 540, 1360
    if pb > 0:
        if t > tap:  # glow selepas ditekan
            comp_c(fr, X['halo'], bx, by, 0.5 * clamp((t - tap) / 0.3), 0.75)
        comp_c(fr, btn, bx, by, clamp(pb), (0.6 + 0.4 * pb) * press * pulse)
    ph = ease_io((t - 1.3) / 0.75)
    if t > 1.3:
        hx, hy = lerp(840, 660, ph), lerp(1660, 1400, ph)
        hs = 1.0 - 0.12 * math.sin(math.pi * clamp((t - tap) / 0.25))
        comp_c(fr, hand, hx + 40, hy + 50, ease_out((t - 1.3) / 0.3), hs)
    q = (t - tap) / 1.0
    if 0 < q < 1:
        rip = Image.new('RGBA', (460, 460), (0, 0, 0, 0))
        r = 30 + 180 * ease_out(q)
        ImageDraw.Draw(rip).ellipse((230 - r, 230 - r, 230 + r, 230 + r), outline=(255, 255, 255, int(230 * (1 - q))), width=7)
        comp_c(fr, rip, 660, by)
        for k in range(12):
            a = k / 12 * 2 * math.pi
            rr = 60 + 300 * ease_out(q)
            img = X['hearts'][k % 3] if k % 2 else A['spark'][2]
            comp_c(fr, img, 660 + rr * math.cos(a), by + rr * 0.7 * math.sin(a) - 80 * q, 1 - q, 0.55 - 0.2 * q)
    return fr


SCENES = [(0.0, 6.0, scene1), (6.0, 11.0, scene2), (11.0, 16.5, scene3), (16.5, 23.0, scene4),
          (23.0, 30.0, scene5), (30.0, 36.5, scene6), (36.5, 40.5, scene_cta), (40.5, DUR, scene_follow)]
TRANS = {6.0: ('paper', 0.6), 11.0: ('zoom', 0.45), 16.5: ('glass', 0.45), 23.0: ('orbit', 0.5),
         30.0: ('paper', 0.6), 36.5: ('glass', 0.45), 40.5: ('flash', 0.5)}


def scene_at(i, gt):
    s, e, fn = SCENES[i]
    return fn(gt - s, gt)


def paper_trans(a, b, p):
    fr = a.copy()
    layers = A['paper']
    ys = []
    for i, (img, m, bh) in enumerate(layers):
        pi = clamp((p - i * 0.12) / 0.76)
        pi = ease_io(pi)
        ytop = H + 100 - pi * (H + bh + 260)
        ys.append((img, ytop - m))
    # kawasan di bawah lapisan terakhir = adegan B
    last_bot = ys[-1][1] + layers[-1][1] + layers[-1][2] - 40
    if last_bot < H:
        yb = int(max(0, last_bot))
        fr.paste(b.crop((0, yb, W, H)), (0, yb))
    for img, y in ys:
        comp(fr, img, 0, y)
    return fr


def blur_frame(img, r):
    if r < 0.5:
        return img
    sm = img.resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(r / 4))
    return sm.resize((W, H), Image.BILINEAR)


def transition(kind, a, b, p):
    if kind == 'paper':
        return paper_trans(a, b, p)
    if kind == 'zoom':
        e = ease_io(p)
        sa, sb = 1 + 0.12 * e, 1.12 - 0.12 * e
        A1 = a.resize((int(W * sa), int(H * sa)), Image.BILINEAR).crop((int(W * (sa - 1) / 2), int(H * (sa - 1) / 2), int(W * (sa - 1) / 2) + W, int(H * (sa - 1) / 2) + H))
        B1 = b.resize((int(W * sb), int(H * sb)), Image.BILINEAR).crop((int(W * (sb - 1) / 2), int(H * (sb - 1) / 2), int(W * (sb - 1) / 2) + W, int(H * (sb - 1) / 2) + H))
        r = 14 * math.sin(math.pi * p)
        return Image.blend(blur_frame(A1, r), blur_frame(B1, r), e)
    if kind == 'glass':
        r = 34 * math.sin(math.pi * p)
        m = Image.blend(a, b, ease_io((p - 0.3) / 0.4))
        m = blur_frame(m, r)
        k = math.sin(math.pi * p)
        m = Image.alpha_composite(m, Image.new('RGBA', (W, H), (255, 246, 240, int(48 * k))))
        sw = Image.new('L', (W // 4, H // 4), 0)
        sx = (-300 + (W + 600) * p) / 4
        ImageDraw.Draw(sw).polygon([(sx, 0), (sx + 50, 0), (sx - 60, H // 4), (sx - 110, H // 4)], fill=int(110 * k))
        sw = sw.filter(ImageFilter.GaussianBlur(6)).resize((W, H), Image.BILINEAR)
        lay = Image.new('RGBA', (W, H), (255, 255, 255, 0))
        lay.putalpha(sw)
        return Image.alpha_composite(m, lay)
    if kind == 'orbit':
        bgc = Image.new('RGBA', (W, H), (28, 12, 30, 255))
        if p < 0.5:
            th = ease_io(p * 2) * (math.pi / 2)
            return rotate_y(a, th, bgc, scale=1 - 0.12 * math.sin(th))
        th = (1 - ease_io((p - 0.5) * 2)) * (-math.pi / 2)
        return rotate_y(b, th, bgc, scale=1 - 0.12 * math.sin(-th))
    if kind == 'flash':
        e = ease_io(p)
        m = Image.blend(a, b, e)
        k = math.sin(math.pi * p)
        return Image.alpha_composite(m, Image.new('RGBA', (W, H), (255, 248, 245, int(200 * k))))
    return b


def frame(gt):
    for T, (kind, d) in TRANS.items():
        if T - d <= gt < T + d:
            i = next(k for k, s in enumerate(SCENES) if abs(s[0] - T) < 1e-6)
            a = scene_at(i - 1, gt)
            b = scene_at(i, gt)
            fr = transition(kind, a, b, (gt - (T - d)) / (2 * d))
            break
    else:
        i = max(k for k, s in enumerate(SCENES) if s[0] <= gt)
        fr = scene_at(i, gt)
    if gt < 0.7:  # fade masuk
        fr = Image.blend(Image.new('RGBA', (W, H), (0, 0, 0, 255)), fr, ease_io(gt / 0.7))
    return fr.convert('RGB')


# ---------------------------------------------------------------- render
def render_chunk(args):
    photo, idx, f0, f1, out = args
    init(photo)
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
           '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', out]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(f0, f1):
        pr.stdin.write(frame(f / FPS).tobytes())
    pr.stdin.close()
    pr.wait()
    return out


def main():
    photo, out = sys.argv[1], sys.argv[2]
    tmp = os.path.join(os.path.dirname(os.path.abspath(out)), 'chunks')
    os.makedirs(tmp, exist_ok=True)
    if '--preview' in sys.argv:
        init(photo)
        ts = [float(x) for x in sys.argv[sys.argv.index('--preview') + 1].split(',')]
        for t in ts:
            frame(t).resize((W // 2, H // 2), Image.LANCZOS).save(os.path.join(tmp, f'prev_{t:05.2f}.jpg'), quality=88)
        return
    nf = int(DUR * FPS)
    n = os.cpu_count() or 4
    cuts = [round(nf * k / n) for k in range(n + 1)]
    jobs = [(photo, k, cuts[k], cuts[k + 1], os.path.join(tmp, f'c{k}.mp4')) for k in range(n)]
    with Pool(n) as pool:
        parts = pool.map(render_chunk, jobs)
    lst = os.path.join(tmp, 'list.txt')
    with open(lst, 'w') as f:
        f.writelines(f"file '{p}'\n" for p in parts)
    audio = os.path.join(os.path.dirname(os.path.abspath(out)), 'audio.wav')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-i', audio,
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], check=True)
    print('wrote', out)


if __name__ == '__main__':
    main()
