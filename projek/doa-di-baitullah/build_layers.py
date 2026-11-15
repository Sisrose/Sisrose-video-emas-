"""Jana lapisan PNG (teks babak + elemen branding) untuk video DOA DI BAITULLAH.
Wording teks dikunci mengikut brief pengguna — jangan ubah tanpa kelulusan.
Guna: python3 build_layers.py <folder_upload> <folder_output>
"""
import sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

UP, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")
W, H = 1080, 1920
GOLD = (226, 196, 128)
GOLD_LIGHT = (246, 226, 176)
WHITE = (255, 252, 245)
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"


def font(name, size, weight=None):
    f = ImageFont.truetype(os.path.join(FONTS, name), size)
    if weight:
        try:
            f.set_variation_by_axes([weight])
        except Exception:
            pass
    return f


def gold_text(text, fnt, tracking=0):
    """Teks bergradien emas sebagai RGBA."""
    tmp = Image.new("L", (10, 10))
    d = ImageDraw.Draw(tmp)
    widths = [d.textlength(c, font=fnt) for c in text]
    tw = int(sum(widths) + tracking * (len(text) - 1)) + 8
    asc, desc = fnt.getmetrics()
    th = asc + desc + 8
    mask = Image.new("L", (tw, th), 0)
    md = ImageDraw.Draw(mask)
    x = 4
    for c, w in zip(text, widths):
        md.text((x, 4), c, font=fnt, fill=255)
        x += w + tracking
    grad = Image.new("RGB", (tw, th))
    gd = ImageDraw.Draw(grad)
    for y in range(th):
        t = y / max(1, th - 1)
        c1, c2, c3 = (250, 232, 185), (222, 186, 110), (176, 136, 68)
        if t < 0.5:
            a, b, k = c1, c2, t / 0.5
        else:
            a, b, k = c2, c3, (t - 0.5) / 0.5
        gd.line([(0, y), (tw, y)], fill=tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3)))
    img = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    img.paste(grad, (0, 0), mask)
    return img


def plain_text(text, fnt, fill, tracking=0):
    tmp = ImageDraw.Draw(Image.new("L", (10, 10)))
    widths = [tmp.textlength(c, font=fnt) for c in text]
    tw = int(sum(widths) + tracking * (len(text) - 1)) + 8
    asc, desc = fnt.getmetrics()
    img = Image.new("RGBA", (tw, asc + desc + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x = 4
    for c, w in zip(text, widths):
        d.text((x, 4), c, font=fnt, fill=fill)
        x += w + tracking
    return img


def with_shadow(img, radius=10, opacity=170, grow=0):
    pad = radius * 3
    base = Image.new("RGBA", (img.width + 2 * pad, img.height + 2 * pad), (0, 0, 0, 0))
    a = img.split()[3]
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sh.putalpha(a.point(lambda v: v * opacity // 255))
    base.paste(sh, (pad, pad + 3), sh)
    base = base.filter(ImageFilter.GaussianBlur(radius))
    base.alpha_composite(img, (pad, pad))
    return base, pad


def ornament(width=260):
    """Garis emas halus dengan berlian kecil di tengah."""
    h = 24
    img = Image.new("RGBA", (width, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cy, cx = h // 2, width // 2
    for x in range(width):
        dist = abs(x - cx) / cx
        a = int(230 * max(0, 1 - dist) ** 0.8)
        if abs(x - cx) > 16:
            d.point((x, cy), fill=GOLD + (a,))
    d.polygon([(cx, cy - 7), (cx + 7, cy), (cx, cy + 7), (cx - 7, cy)], fill=GOLD_LIGHT + (240,))
    return img


def scene_layer(lines, name, center_y=1180, size=70, gold_idx=(), emoji_line=None):
    """Satu lapisan penuh 1080x1920: teks tengah + gradien gelap lembut di belakang."""
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # Gradien gelap lembut (bukan kotak) supaya teks mudah dibaca
    band = Image.new("L", (W, H), 0)
    bd = ImageDraw.Draw(band)
    for y in range(H):
        dist = abs(y - center_y) / 420
        bd.line([(0, y), (W, y)], fill=int(120 * max(0, 1 - dist ** 2)))
    canvas.paste(Image.new("RGBA", (W, H), (10, 8, 5, 255)), (0, 0), band)

    fnt = font("Cormorant.ttf", size, 600)
    rendered = []
    for i, ln in enumerate(lines):
        t = gold_text(ln, fnt) if i in gold_idx else plain_text(ln, fnt, WHITE)
        rendered.append(t)
    lh = int(size * 1.22)
    total = lh * len(rendered)
    y = center_y - total // 2
    orn = ornament()
    canvas.alpha_composite(orn, ((W - orn.width) // 2, y - 56))
    for t in rendered:
        s, pad = with_shadow(t, 12, 200)
        canvas.alpha_composite(s, ((W - t.width) // 2 - pad, y - pad))
        y += lh
    canvas.save(os.path.join(OUT, name))


# ---------- Babak 1–4 (wording asal pengguna) ----------
scene_layer(["Kalau selama ini", "kita tak pernah", "berhenti berdoa…"], "t1.png", gold_idx=(2,))
scene_layer(["Apa kata kali ini", "kita berdoa", "di hadapan Kaabah?"], "t2.png", gold_idx=(2,))
# Babak 3: tiga baris muncul satu demi satu → tiga lapisan berasingan
for i, ln in enumerate(["Bawa segala hajat.", "Bawa segala impian.", "Bawa segala pengharapan."]):
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if i == 0:
        band = Image.new("L", (W, H), 0)
        bd = ImageDraw.Draw(band)
        for y in range(H):
            dist = abs(y - 1180) / 460
            bd.line([(0, y), (W, y)], fill=int(125 * max(0, 1 - dist ** 2)))
        canvas.paste(Image.new("RGBA", (W, H), (10, 8, 5, 255)), (0, 0), band)
        orn = ornament()
        canvas.alpha_composite(orn, ((W - orn.width) // 2, 1180 - 125 - 56))
    fnt = font("Cormorant.ttf", 68, 600)
    t = gold_text(ln, fnt) if i == 2 else plain_text(ln, fnt, WHITE)
    s, pad = with_shadow(t, 12, 200)
    y = 1180 - 125 + i * 88
    canvas.alpha_composite(s, ((W - t.width) // 2 - pad, y - pad))
    canvas.save(os.path.join(OUT, f"t3_{i}.png"))
scene_layer(["Mungkin sudah tiba masanya", "kita menjadi", "tetamu Allah."], "t4.png", size=66, gold_idx=(2,))

# ---------- Babak akhir: JOM PERGI UMRAH ❤️ ----------
canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
band = Image.new("L", (W, H), 0)
bd = ImageDraw.Draw(band)
for y in range(H):
    dist = abs(y - 1250) / 420
    bd.line([(0, y), (W, y)], fill=int(130 * max(0, 1 - dist ** 2)))
canvas.paste(Image.new("RGBA", (W, H), (10, 8, 5, 255)), (0, 0), band)
jom = gold_text("JOM PERGI", font("Cinzel.ttf", 92, 600), tracking=6)
umrah = gold_text("UMRAH", font("Cinzel.ttf", 128, 700), tracking=10)
ef = ImageFont.truetype(EMOJI, 109)
heart = Image.new("RGBA", (140, 140), (0, 0, 0, 0))
ImageDraw.Draw(heart).text((0, 0), "❤️", font=ef, embedded_color=True)
heart = heart.crop(heart.getbbox()).resize((80, 74), Image.LANCZOS)
for img, yy in ((jom, 1120), (umrah, 1230)):
    s, pad = with_shadow(img, 14, 210)
    x = (W - img.width) // 2 - (48 if img is umrah else 0)
    canvas.alpha_composite(s, (x - pad, yy - pad))
    if img is umrah:
        canvas.alpha_composite(heart, (x + img.width + 14, yy + 52))
orn = ornament(320)
canvas.alpha_composite(orn, ((W - orn.width) // 2, 1080))
canvas.alpha_composite(orn, ((W - orn.width) // 2, 1400))
canvas.save(os.path.join(OUT, "t5.png"))

# ---------- Branding (4 saat terakhir) ----------
# Latar: gambar Kaabah (Pinterest, diluluskan pengguna) — dikaburkan & digelapkan
bg = Image.open(os.path.join(UP, "6d8f2484-image.jpg")).convert("RGB")
s = max(W / bg.width, H / bg.height) * 1.12
bg = bg.resize((int(bg.width * s), int(bg.height * s)), Image.LANCZOS)
bg = bg.crop(((bg.width - W) // 2, (bg.height - H) // 2, (bg.width - W) // 2 + W, (bg.height - H) // 2 + H))
bg = bg.filter(ImageFilter.GaussianBlur(6))
bg = ImageEnhance.Brightness(bg).enhance(0.62)
shade = Image.new("L", (W, H))
sd = ImageDraw.Draw(shade)
for x in range(W):  # gelap di kiri untuk teks
    sd.line([(x, 0), (x, H)], fill=int(150 * max(0, 1 - x / 760)))
bg = Image.composite(Image.new("RGB", (W, H), (8, 6, 4)), bg, shade)
bg.save(os.path.join(OUT, "brand_bg.jpg"), quality=95)

# Potret dalam bingkai gerbang emas (foto asal tidak diubah; hanya dipotong/diskala)
AW, AH = 440, 800
por = Image.open(os.path.join(UP, "e16053f0-image.jpg")).convert("RGB")
cw = 560
ch = int(cw * AH / AW)
cx0 = 330 - cw // 2
por = por.crop((cx0, 20, cx0 + cw, 20 + ch)).resize((AW, AH), Image.LANCZOS)
mask = Image.new("L", (AW, AH), 0)
md = ImageDraw.Draw(mask)
md.rectangle([0, AW // 2, AW, AH], fill=255)
md.ellipse([0, 0, AW, AW], fill=255)
B = 14
arch = Image.new("RGBA", (AW + 2 * B + 60, AH + 2 * B + 60), (0, 0, 0, 0))
ox = oy = 30
glow = Image.new("L", arch.size, 0)
gd = ImageDraw.Draw(glow)
gd.rectangle([ox, oy + AW // 2 + B, ox + AW + 2 * B, oy + AH + 2 * B], fill=200)
gd.ellipse([ox, oy, ox + AW + 2 * B, oy + AW + 2 * B], fill=200)
glow = glow.filter(ImageFilter.GaussianBlur(18))
arch.paste(Image.new("RGBA", arch.size, (240, 200, 120, 255)), (0, 0), glow.point(lambda v: v * 0.55))
frame = Image.new("L", (AW + 2 * B, AH + 2 * B), 0)
fd = ImageDraw.Draw(frame)
fd.rectangle([0, AW // 2 + B, AW + 2 * B, AH + 2 * B], fill=255)
fd.ellipse([0, 0, AW + 2 * B, AW + 2 * B], fill=255)
goldfill = gold_text("█", font("Cormorant.ttf", 40)).resize(frame.size)
gl = Image.new("RGBA", frame.size, (0, 0, 0, 0))
gl.paste(goldfill.convert("RGB"), (0, 0), frame)
arch.alpha_composite(gl, (ox, oy))
pi = Image.new("RGBA", (AW, AH), (0, 0, 0, 0))
pi.paste(por, (0, 0), mask)
arch.alpha_composite(pi, (ox + B, oy + B))
arch.save(os.path.join(OUT, "brand_portrait.png"))

# Teks branding (kiri)
def save_text(img, name, shadow=True):
    if shadow:
        img, _ = with_shadow(img, 12, 200)
    img.save(os.path.join(OUT, name))

save_text(gold_text("SIS", font("Cinzel.ttf", 116, 700), tracking=8), "brand_sis.png")
save_text(gold_text("ROSE", font("Cinzel.ttf", 116, 700), tracking=8), "brand_rose.png")
save_text(plain_text("TH TRAVEL", font("Cinzel.ttf", 52, 500), WHITE, tracking=7), "brand_th.png")
o = ornament(380)
o.save(os.path.join(OUT, "brand_line.png"))
tag = Image.new("RGBA", (500, 140), (0, 0, 0, 0))
tf = font("Cormorant-Italic.ttf", 42, 500)
td = ImageDraw.Draw(tag)
td.text((4, 4), "“Membantu Anda Melangkah", font=tf, fill=WHITE)
td.text((4, 58), "Ke Baitullah”", font=tf, fill=GOLD_LIGHT)
save_text(tag, "brand_tag.png")

# Logo TH Travel atas kad krim membulat (logo asal tidak diubah)
logo = Image.open(os.path.join(UP, "316468c9-image.jpg")).convert("RGB")
bb = Image.eval(logo.convert("L"), lambda v: 255 if v < 235 else 0).getbbox()
logo = logo.crop((bb[0] - 30, bb[1] - 30, bb[2] + 30, bb[3] + 30))
LW = 300
logo = logo.resize((LW, int(logo.height * LW / logo.width)), Image.LANCZOS)
card = Image.new("RGBA", (LW + 8, logo.height + 8), (0, 0, 0, 0))
cm = Image.new("L", card.size, 0)
ImageDraw.Draw(cm).rounded_rectangle([0, 0, card.width - 1, card.height - 1], radius=22, fill=255)
card.paste(Image.new("RGBA", card.size, GOLD + (255,)), (0, 0), cm)
inner = Image.new("L", logo.size, 0)
ImageDraw.Draw(inner).rounded_rectangle([0, 0, logo.width - 1, logo.height - 1], radius=19, fill=255)
card.paste(logo, (4, 4), inner)
save_text(card, "brand_logo.png")
print("ok")
