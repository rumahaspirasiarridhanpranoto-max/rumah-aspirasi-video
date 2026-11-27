"""Gaya "Photo Story" untuk posting kerja nyata dengan BANYAK foto lapangan.

Pemakaian: python3 -I tools/photostory.py konten.json carousel/YYYY-MM-DD-slug
Hasil: slide_N.jpg (1080x1920) + preview.jpg

konten.json:
{
  "seed": 3,
  "slides": [
    {"type": "hero", "src": "foto/.../01.jpg", "focus": 0.45, "date": "JUMAT, 27 NOVEMBER 2026",
     "loc": "Pojok Gobali, Berngam", "kicker": "...", "title": "Baris 1|Baris 2 kuning", "body": "..."},
    {"type": "full", "src": "...", "focus": 0.4, "tag": "SUARA WARGA", "title": "...", "body": "..."},
    {"type": "collage", "srcs": ["a.jpg", "b.jpg", "c.jpg"], "tag": "...", "title": "...", "body": "..."},
    {"type": "glass", "src": "...", "tag": "KENAL DULU", "big": "6 Hari", "title": "...", "body": "...", "source": "Dasar: ..."},
    {"type": "closing", "srcs": ["a.jpg", "b.jpg", "c.jpg"], "title": "...", "items": ["..."], "cta": "..."}
  ]
}
Judul: pakai "|" untuk pindah baris; bagian setelah "|" terakhir berwarna kuning.
"focus" (0..1) = posisi vertikal fokus saat foto dipotong (0 atas, 1 bawah).
"""
import json, math, os, random, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance, ImageOps

W, H = 1080, 1920
FD = "/usr/share/fonts/truetype/google-fonts/"
BLUE, LB, YEL, NAVY, WHITE = (52, 78, 184), (83, 166, 245), (245, 238, 27), (12, 20, 52), (255, 255, 255)

def font(s, w="b"):
    n = {"x": "Poppins-ExtraBold.ttf", "b": "Poppins-Bold.ttf", "m": "Poppins-Medium.ttf", "s": "Poppins-SemiBold.ttf", "i": "Poppins-BoldItalic.ttf"}[w]
    p = FD + n
    return ImageFont.truetype(p if os.path.exists(p) else FD + "Poppins-Bold.ttf", s)

def wrap(d, text, f, maxw):
    out, cur = [], ""
    for w in str(text).split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= maxw: cur = t
        else:
            if cur: out.append(cur)
            cur = w
    return out + ([cur] if cur else [])

def enhance(ph):
    ph = ImageOps.autocontrast(ph, cutoff=1)
    ph = ImageEnhance.Color(ph).enhance(1.12)
    ph = ImageEnhance.Contrast(ph).enhance(1.06)
    r, g, b = ph.split()
    r = r.point(lambda v: min(255, int(v * 1.03)))
    ph = Image.merge("RGB", (r, g, b))
    return ph.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=3))

def cover_crop(ph, w, h, focus=0.5):
    s = max(w / ph.width, h / ph.height)
    ph = ph.resize((int(ph.width * s + .5), int(ph.height * s + .5)), Image.LANCZOS)
    x = (ph.width - w) // 2
    y = int((ph.height - h) * focus)
    return ph.crop((x, y, x + w, y + h))

def load(src):
    return enhance(Image.open(src).convert("RGB"))

def grad(im, y0, y1, color=NAVY, a0=0, a1=235):
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    for y in range(y0, y1):
        t = (y - y0) / max(1, y1 - y0)
        d.line([(0, y), (W, y)], fill=color + (int(a0 + (a1 - a0) * (t ** 1.3)),))
    if y1 < H: d.rectangle((0, y1, W, H), fill=color + (a1,))
    im.paste(ov, (0, 0), ov)

def top_shade(im, h=360, a=150):
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    for y in range(h): d.line([(0, y), (W, y)], fill=(0, 0, 0, int(a * (1 - y / h))))
    im.paste(ov, (0, 0), ov)

def grain(im, rnd, k=10):
    n = Image.effect_noise((W // 2, H // 2), 40).resize((W, H)).convert("RGB")
    return Image.blend(im, n, k / 255)

def shadow_paste(base, img, xy, angle=0, border=18, radius=10, blur=20):
    fr = Image.new("RGB", (img.width + border * 2, img.height + border * 2), WHITE)
    fr.paste(img, (border, border))
    fr = fr.convert("RGBA")
    if angle: fr = fr.rotate(angle, expand=True, resample=Image.BICUBIC)
    sh = Image.new("RGBA", (fr.width + 80, fr.height + 80), (0, 0, 0, 0))
    a = fr.split()[3]
    sh.paste((0, 0, 0, 140), (40, 52), a)
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    base.paste(sh, (xy[0] - 40, xy[1] - 40), sh)
    base.paste(fr, xy, fr)

def badge(d):
    f = font(34); s = "Rumah Aspirasi · Arridhan Pranoto"
    w = d.textlength(s, font=f); x = (W - w) / 2 - 30
    d.rounded_rectangle((x, 96, x + w + 60, 168), radius=36, fill=BLUE, outline=LB, width=3)
    d.text((x + 30, 107), s, font=f, fill=WHITE)

def footer(d, i, n, col=(215, 222, 240)):
    f = font(30, "m"); s = f"{i}/{n}"
    d.text((W - 90 - d.textlength(s, font=f), H - 140), s, font=f, fill=col)
    if i < n: d.text((90, H - 140), "Geser  >>", font=f, fill=col)
    # progress bar
    bw = (W - 180) / n
    for k in range(n):
        d.rounded_rectangle((90 + k * bw + 4, H - 80, 90 + (k + 1) * bw - 4, H - 72), radius=4, fill=YEL if k < i else (255, 255, 255, 90) if False else (90, 100, 140))

def chip(d, x, y, text, bg=YEL, fg=NAVY, size=38, pin=False):
    f = font(size, "x"); w = d.textlength(text, font=f); pad = 26; ph = size + 30
    extra = 46 if pin else 0
    d.rounded_rectangle((x, y, x + w + pad * 2 + extra, y + ph), radius=ph // 2, fill=bg)
    if pin:
        cx, cy = x + pad + 14, y + ph / 2 - 4
        d.ellipse((cx - 14, cy - 16, cx + 14, cy + 12), fill=fg)
        d.polygon([(cx - 12, cy + 2), (cx + 12, cy + 2), (cx, cy + 24)], fill=fg)
        d.ellipse((cx - 6, cy - 8, cx + 6, cy + 4), fill=bg)
    d.text((x + pad + extra, y + 12), text, font=f, fill=fg)
    return x + w + pad * 2 + extra

def title_block(d, x, y, title, maxw=900, start=118, minsize=70, maxlines=4):
    parts = title.split("|")
    s = start
    while s >= minsize:
        f = font(s, "x")
        lines = []
        for k, p in enumerate(parts):
            for ln in wrap(d, p, f, maxw): lines.append((ln, k == len(parts) - 1 and len(parts) > 1))
        if len(lines) <= maxlines: break
        s -= 6
    for ln, hl in lines:
        d.text((x, y), ln, font=f, fill=YEL if hl else WHITE)
        y += int(f.size * 1.04)
    return y

def body_block(d, x, y, text, size=42, col=(225, 230, 245), maxw=900, w="m"):
    f = font(size, w)
    for ln in wrap(d, text, f, maxw):
        d.text((x, y), ln, font=f, fill=col); y += int(size * 1.35)
    return y

def measure_title(d, title, maxw=900, start=118, minsize=70, maxlines=4):
    parts = title.split("|"); s = start
    while s >= minsize:
        f = font(s, "x"); n = sum(len(wrap(d, p, f, maxw)) for p in parts)
        if n <= maxlines: return n * int(s * 1.04)
        s -= 6
    return 4 * int(minsize * 1.04)

def measure_body(d, text, size=42, maxw=900):
    return len(wrap(d, text, font(size, "m"), maxw)) * int(size * 1.35) if text else 0

# ---------------- slides ----------------
def s_hero(sl, rnd):
    im = cover_crop(load(sl["src"]), W, H, sl.get("focus", .45))
    top_shade(im); grad(im, 700, 1500, a1=245)
    im = grain(im, rnd, 8); d = ImageDraw.Draw(im, "RGBA")
    fdate = font(36, "x"); date_w = d.textlength(sl["date"], font=fdate) + 52
    loc_inline = False
    if sl.get("loc"):
        lw = d.textlength(sl["loc"], font=font(32, "x")) + 98
        if 90 + date_w + 16 + lw <= W - 60: loc_inline = True
        else: sl = dict(sl, body=(sl.get("body", "").rstrip(".") + " · " + sl["loc"]).strip(" ·"))
    th = measure_title(d, sl["title"], start=124); bh = measure_body(d, sl.get("body", ""), 44)
    y = H - 250 - bh - th - 100 - (60 if sl.get("kicker") else 0) - 40
    x2 = chip(d, 90, y, sl["date"], size=36)
    if loc_inline: chip(d, x2 + 16, y + 3, sl["loc"], bg=(255, 255, 255), fg=NAVY, size=32, pin=True)
    y += 100
    if sl.get("kicker"):
        d.text((90, y), sl["kicker"].upper(), font=font(36, "b"), fill=LB); y += 60
    y = title_block(d, 90, y, sl["title"], start=124) + 40
    body_block(d, 90, y, sl.get("body", ""), 44)
    return im

def s_full(sl, rnd):
    im = cover_crop(load(sl["src"]), W, H, sl.get("focus", .4))
    top_shade(im); grad(im, 1000, 1720, a1=235)
    im = grain(im, rnd, 6); d = ImageDraw.Draw(im, "RGBA")
    th = measure_title(d, sl["title"], start=104, maxlines=3); bh = measure_body(d, sl.get("body", ""), 42)
    y = H - 220 - bh - th - 110
    chip(d, 90, y, sl.get("tag", ""), size=32); y += 96
    y = title_block(d, 90, y, sl["title"], start=104, maxlines=3) + 22
    body_block(d, 90, y, sl.get("body", ""), 42)
    return im

def s_collage(sl, rnd):
    bg = cover_crop(load(sl["srcs"][0]), W, H, .5).filter(ImageFilter.GaussianBlur(38))
    bg = Image.blend(bg, Image.new("RGB", (W, H), NAVY), .72)
    im = grain(bg, rnd, 10).convert("RGBA")
    srcs = sl["srcs"]
    if len(srcs) == 3:
        spots = [((70, 250), (560, 700), -4), ((470, 420), (540, 720), 5), ((150, 900), (640, 420), -2)]
    elif len(srcs) == 2:
        spots = [((60, 260), (600, 760), -4), ((420, 640), (600, 560), 4)]
    else:
        spots = [((60, 250), (470, 600), -4), ((540, 270), (470, 600), 3), ((70, 760), (470, 430), 2), ((530, 790), (480, 430), -3)]
    for (xy, wh, ang), src in zip(spots, srcs):
        ph = cover_crop(load(src), wh[0], wh[1], .4)
        shadow_paste(im, ph, xy, angle=ang + rnd.uniform(-1, 1))
    im = im.convert("RGB"); d = ImageDraw.Draw(im, "RGBA")
    y = 1290
    chip(d, 90, y, sl.get("tag", ""), size=32); y += 96
    y = title_block(d, 90, y, sl["title"], start=96, maxlines=2) + 20
    body_block(d, 90, y, sl.get("body", ""), 40)
    return im

def s_glass(sl, rnd):
    bg = cover_crop(load(sl["src"]), W, H, sl.get("focus", .45))
    sharp = bg.copy()
    bg = bg.filter(ImageFilter.GaussianBlur(26))
    bg = Image.blend(bg, Image.new("RGB", (W, H), NAVY), .55)
    im = grain(bg, rnd, 8).convert("RGBA")
    # strip foto tajam di atas
    strip = cover_crop(sharp, W - 180, 520, sl.get("focus", .45))
    shadow_paste(im, strip, (72, 230), angle=0, border=12)
    x0, y0, x1, y1 = 60, 850, W - 60, 1680
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(ov).rounded_rectangle((x0, y0, x1, y1), radius=40, fill=(255, 255, 255, 30), outline=(255, 255, 255, 110), width=3)
    im = Image.alpha_composite(im, ov).convert("RGB"); d = ImageDraw.Draw(im, "RGBA")
    y = y0 + 50
    chip(d, 110, y, sl.get("tag", ""), size=30); y += 100
    if sl.get("big"):
        f = font(200, "x"); d.text((104, y - 30), sl["big"], font=f, fill=YEL); y += 210
    y = title_block(d, 110, y, sl["title"], maxw=860, start=84, maxlines=3) + 16
    y = body_block(d, 110, y, sl.get("body", ""), 38, maxw=860)
    if sl.get("source"):
        body_block(d, 110, y1 - 80, sl["source"], 26, col=(190, 200, 230), maxw=860, w="m")
    return im

def s_closing(sl, rnd):
    im = Image.new("RGB", (W, H), YEL)
    d = ImageDraw.Draw(im)
    for k in range(-4, 16): d.line([(k * 110, H), (k * 110 + 900, H - 900)], fill=(250, 232, 0), width=26)
    im = im.convert("RGBA")
    xs = [(60, 230, -6), (380, 210, 3), (700, 240, -2)]
    for (x, y, a), src in zip(xs, sl["srcs"][:3]):
        shadow_paste(im, cover_crop(load(src), 300, 380, .35), (x, y), angle=a, border=12)
    im = im.convert("RGB"); d = ImageDraw.Draw(im)
    y = 760
    for ln in wrap(d, sl["title"], font(84, "x"), 900):
        d.text((90, y), ln, font=font(84, "x"), fill=NAVY); y += 92
    y += 30
    f = font(44, "b")
    for it in sl["items"]:
        d.rounded_rectangle((90, y, W - 90, y + 96), radius=48, fill=NAVY)
        d.ellipse((112, y + 18, 172, y + 78), fill=YEL)
        d.line([(127, y + 49), (139, y + 61), (158, y + 36)], fill=NAVY, width=8)
        d.text((196, y + 20), it, font=f, fill=WHITE); y += 118
    y += 20
    d.rounded_rectangle((90, y, W - 90, y + 110), radius=24, fill=BLUE)
    fc = font(40, "b"); tw = d.textlength(sl["cta"], font=fc)
    if tw > W - 240:
        fc = font(34, "b"); tw = d.textlength(sl["cta"], font=fc)
    d.text(((W - tw) / 2, y + 30), sl["cta"], font=fc, fill=WHITE)
    f2 = font(46, "x"); s1, s2 = "DARI WARGA ", "KE KEBIJAKAN"
    w1 = d.textlength(s1, font=f2); w2 = d.textlength(s2, font=f2)
    xx = (W - w1 - w2) / 2
    d.text((xx, H - 250), s1, font=f2, fill=NAVY); d.text((xx + w1, H - 250), s2, font=f2, fill=BLUE)
    return im

LAY = {"hero": s_hero, "full": s_full, "collage": s_collage, "glass": s_glass, "closing": s_closing}

def render(spec, out):
    os.makedirs(out, exist_ok=True)
    rnd = random.Random(spec.get("seed", 1)); n = len(spec["slides"]); files = []
    for i, sl in enumerate(spec["slides"], 1):
        im = LAY[sl["type"]](sl, rnd).convert("RGB")
        d = ImageDraw.Draw(im, "RGBA"); badge(d)
        footer(d, i, n, col=NAVY if sl["type"] == "closing" else (215, 222, 240))
        fn = os.path.join(out, f"slide_{i}.jpg"); im.save(fn, quality=92); files.append(fn)
    th = [Image.open(f).resize((270, 480)) for f in files]
    cols = min(4, n); rows = (n + cols - 1) // cols
    pv = Image.new("RGB", (cols * 280 + 10, rows * 490 + 10), (30, 30, 30))
    for k, t in enumerate(th): pv.paste(t, (10 + (k % cols) * 280, 10 + (k // cols) * 490))
    pv.save(os.path.join(out, "preview.jpg"), quality=85)

if __name__ == "__main__":
    render(json.load(open(sys.argv[1])), sys.argv[2])
