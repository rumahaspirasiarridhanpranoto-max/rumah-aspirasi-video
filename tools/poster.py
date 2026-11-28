"""Gaya POSTER / MAJALAH: kertas krem, judul Anton tinggal-ramping, isi serif (Lora), ilustrasi gambar tangan
sederhana (pohon, sungai, rambutan, peta, pin). Cocok untuk seri cerita/sejarah/fakta lokal tanpa foto.

Pemakaian: python3 -I tools/poster.py konten.json carousel/YYYY-MM-DD-slug
konten.json:
{
  "seed": 1, "series": "BINJAI PUNYA CERITA #1", "accent": "red|green|blue",
  "slides": [
    {"type": "cover", "kicker": "...", "big": "BINJAI", "title": "Kenapa namanya", "sub": "...", "art": "tree"},
    {"type": "story", "num": "01", "title": "...", "body": "...", "source": "Sumber: ...", "art": "river"},
    {"type": "number", "big": "22 KM", "title": "...", "body": "...", "source": "...", "art": "pin"},
    {"type": "list", "title": "...", "items": ["..."], "body": "...", "source": "..."},
    {"type": "closing", "title": "...", "items": ["..."], "cta": "..."}
  ]
}
art: tree, river, rambutan, pin, map, monument, none.
"""
import json, math, os, random, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
GF = "/usr/share/fonts/truetype/google-fonts/"
ANTON = GF + "ofl/anton/Anton-Regular.ttf"
ARCH = GF + "ofl/archivoblack/ArchivoBlack-Regular.ttf"
LORA = GF + "Lora-Variable.ttf"
POP = GF + "Poppins-Bold.ttf"
PAPER, INK, NAVY = (246, 239, 224), (28, 26, 30), (12, 20, 52)
ACC = {"red": (190, 32, 52), "green": (26, 110, 70), "blue": (52, 78, 184)}
BLUE, LB, YEL, WHITE = (52, 78, 184), (83, 166, 245), (245, 238, 27), (255, 255, 255)

def F(path, size, var=None):
    f = ImageFont.truetype(path, size)
    if var:
        try: f.set_variation_by_name(var)
        except Exception: pass
    return f

def wrap(d, text, f, maxw):
    out, cur = [], ""
    for w in str(text).split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= maxw: cur = t
        else:
            if cur: out.append(cur)
            cur = w
    return out + ([cur] if cur else [])

def paper(rnd, tint=PAPER):
    im = Image.new("RGB", (W, H), tint)
    n = Image.effect_noise((W, H), 22).convert("RGB")
    im = Image.blend(im, n, .06)
    d = ImageDraw.Draw(im)
    for _ in range(40):  # serat kertas
        x, y = rnd.randint(0, W), rnd.randint(0, H)
        d.line([(x, y), (x + rnd.randint(-40, 40), y + rnd.randint(-6, 6))], fill=tuple(max(0, c - 14) for c in tint), width=1)
    return im

def badge(d):
    f = F(POP, 34); s = "Rumah Aspirasi · Arridhan Pranoto"
    w = d.textlength(s, font=f); x = (W - w) / 2 - 30
    d.rounded_rectangle((x, 96, x + w + 60, 168), radius=36, fill=BLUE, outline=LB, width=3)
    d.text((x + 30, 107), s, font=f, fill=WHITE)

def masthead(d, series, acc, i, n):
    d.line([(70, 210), (W - 70, 210)], fill=INK, width=4)
    d.line([(70, 218), (W - 70, 218)], fill=INK, width=1)
    f = F(ARCH, 30); d.text((70, 232), series, font=f, fill=acc)
    s = f"{i:02d} / {n:02d}"; d.text((W - 70 - d.textlength(s, font=f), 232), s, font=f, fill=INK)

def footer(d, i, n, acc):
    d.line([(70, H - 170), (W - 70, H - 170)], fill=INK, width=2)
    f = F(POP, 30)
    if i < n: d.text((70, H - 150), "Geser  >>", font=f, fill=INK)
    s = "DARI WARGA KE KEBIJAKAN"; d.text((W - 70 - d.textlength(s, font=f), H - 150), s, font=f, fill=acc)

# ---------- ilustrasi ----------
def art_tree(d, cx, cy, s, acc, rnd):
    green = (36, 104, 64); dark = (24, 72, 44)
    d.polygon([(cx - s * .09, cy + s * .9), (cx + s * .09, cy + s * .9), (cx + s * .05, cy + s * .1), (cx - s * .05, cy + s * .1)], fill=(92, 60, 40))
    for k in range(-3, 4):
        d.line([(cx, cy + s * .35), (cx + k * s * .12, cy + s * .05)], fill=(92, 60, 40), width=int(s * .03))
    for _ in range(26):
        a = rnd.uniform(0, math.pi); r = rnd.uniform(.15, .55) * s
        x = cx + math.cos(a) * r * 1.3; y = cy - math.sin(a) * r * .8 + s * .05; rr = rnd.uniform(.14, .24) * s
        d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=rnd.choice([green, dark, (48, 124, 76)]))
    d.line([(cx - s * 1.1, cy + s * .9), (cx + s * 1.1, cy + s * .9)], fill=INK, width=4)

def art_river(d, cx, cy, s, acc, rnd):
    for k in range(5):
        pts = [(cx - s + t * 2 * s / 60, cy + k * s * .14 + math.sin(t / 4 + k) * s * .05) for t in range(61)]
        d.line(pts, fill=(52, 120, 190) if k % 2 == 0 else (110, 170, 220), width=int(s * .035))
    art_tree(d, cx + s * .55, cy - s * .55, s * .45, acc, rnd)
    # rumah kecil
    for j, x in enumerate([cx - s * .7, cx - s * .35]):
        y = cy - s * .25
        d.rectangle((x - s * .12, y - s * .1, x + s * .12, y + s * .12), fill=(180, 120, 80))
        d.polygon([(x - s * .16, y - s * .1), (x + s * .16, y - s * .1), (x, y - s * .28)], fill=acc)

def art_rambutan(d, cx, cy, s, acc, rnd):
    for (ox, oy, r) in [(-.35, .1, .42), (.3, .15, .38), (0, -.25, .4)]:
        x, y, rr = cx + ox * s, cy + oy * s, r * s
        for k in range(70):
            a = k / 70 * 2 * math.pi + rnd.uniform(-.05, .05); L = rr * rnd.uniform(1.15, 1.35)
            x1, y1 = x + math.cos(a) * rr * .9, y + math.sin(a) * rr * .9
            x2, y2 = x + math.cos(a + .25) * L, y + math.sin(a + .25) * L
            d.line([(x1, y1), (x2, y2)], fill=(rnd.choice([(196, 40, 50), (220, 70, 60), (120, 150, 60)])), width=5)
        d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=acc)
        d.ellipse((x - rr * .55, y - rr * .6, x - rr * .15, y - rr * .25), fill=(236, 110, 110))

def art_pin(d, cx, cy, s, acc, rnd):
    # jalan Medan -> Binjai
    d.line([(cx - s, cy + s * .5), (cx + s, cy + s * .5)], fill=INK, width=6)
    for x in range(int(cx - s), int(cx + s), 50): d.line([(x, cy + s * .5), (x + 24, cy + s * .5)], fill=PAPER, width=2)
    for x, lab, c in [(cx - s * .8, "MEDAN", INK), (cx + s * .8, "BINJAI", acc)]:
        d.ellipse((x - s * .2, cy - s * .35, x + s * .2, cy + s * .05), fill=c)
        d.polygon([(x - s * .17, cy - s * .08), (x + s * .17, cy - s * .08), (x, cy + s * .4)], fill=c)
        d.ellipse((x - s * .08, cy - s * .23, x + s * .08, cy - s * .07), fill=PAPER)
        f = F(ARCH, int(s * .14)); d.text((x - d.textlength(lab, font=f) / 2, cy + s * .62), lab, font=f, fill=c)

def art_map(d, cx, cy, s, acc, rnd):
    names = ["Binjai Utara", "Binjai Barat", "Binjai Kota", "Binjai Timur", "Binjai Selatan"]
    pos = [(0, -.75), (-.75, 0), (0, 0), (.75, 0), (0, .75)]
    for (ox, oy), nm in zip(pos, names):
        x, y = cx + ox * s, cy + oy * s; r = s * .36
        pts = [(x + math.cos(a) * r * rnd.uniform(.85, 1.05), y + math.sin(a) * r * rnd.uniform(.85, 1.05)) for a in [k * math.pi / 3 + math.pi / 6 for k in range(6)]]
        d.polygon(pts, fill=acc if nm == "Binjai Kota" else (226, 214, 190), outline=INK)
        f = F(ARCH, int(s * .075)); t = nm.replace("Binjai ", "")
        d.text((x - d.textlength(t, font=f) / 2, y - s * .05), t, font=f, fill=WHITE if nm == "Binjai Kota" else INK)

def art_monument(d, cx, cy, s, acc, rnd):
    d.rectangle((cx - s * .5, cy + s * .6, cx + s * .5, cy + s * .75), fill=INK)
    d.rectangle((cx - s * .32, cy + s * .45, cx + s * .32, cy + s * .6), fill=(90, 90, 96))
    d.polygon([(cx - s * .12, cy + s * .45), (cx + s * .12, cy + s * .45), (cx + s * .05, cy - s * .7), (cx - s * .05, cy - s * .7)], fill=(120, 120, 128))
    d.polygon([(cx - s * .05, cy - s * .7), (cx + s * .05, cy - s * .7), (cx, cy - s * .9)], fill=acc)

ART = {"tree": art_tree, "river": art_river, "rambutan": art_rambutan, "pin": art_pin, "map": art_map, "monument": art_monument}

def text_block(d, x, y, text, f, fill, maxw, gap=1.32):
    for ln in wrap(d, text, f, maxw):
        d.text((x, y), ln, font=f, fill=fill); y += int(f.size * gap)
    return y

def anton_fit(d, text, maxw, start, minsize=80, maxlines=3):
    s = start
    while s > minsize:
        f = F(ANTON, s)
        if len(wrap(d, text, f, maxw)) <= maxlines: return f
        s -= 8
    return F(ANTON, minsize)

def source(d, y, s, acc):
    if not s: return
    f = F(LORA, 28, "Italic") if False else F(GF + "Lora-Italic-Variable.ttf", 28)
    text_block(d, 70, y, s, f, (90, 84, 80), 940, 1.3)

# ---------- slide ----------
def s_cover(sl, rnd, acc, meta):
    im = paper(rnd); d = ImageDraw.Draw(im)
    art = sl.get("art", "tree")
    if art in ART: ART[art](d, W * .5, 560, 300, acc, rnd)
    y = 960
    f = F(ARCH, 40); d.text((70, y), sl.get("kicker", "").upper(), font=f, fill=acc); y += 70
    ft = F(LORA, 76, "Bold"); y = text_block(d, 70, y, sl["title"], ft, INK, 940, 1.15)
    fb = anton_fit(d, sl["big"], 940, 300, maxlines=1)
    d.text((62, y - 20), sl["big"], font=fb, fill=acc); y = d.textbbox((62, y - 20), sl["big"], font=fb)[3] + 30
    d.rectangle((70, y, 330, y + 12), fill=INK); y += 40
    text_block(d, 70, y, sl.get("sub", ""), F(LORA, 42), INK, 940)
    return im

def s_story(sl, rnd, acc, meta):
    im = paper(rnd); d = ImageDraw.Draw(im)
    if sl.get("num"):
        fn = F(ANTON, 300); d.text((60, 250), sl["num"], font=fn, fill=tuple(int(c * .25 + 246 * .75) for c in acc))
    art = sl.get("art", "none")
    if art in ART: ART[art](d, W * .62, 520, 250, acc, rnd)
    y = 880
    ft = anton_fit(d, sl["title"].upper(), 940, 120, maxlines=3)
    for ln in wrap(d, sl["title"].upper(), ft, 940): d.text((70, y), ln, font=ft, fill=INK); y += int(ft.size * 1.22)
    d.rectangle((70, y + 34, 200, y + 44), fill=acc); y += 84
    fb = F(LORA, 46)
    # huruf awal besar (drop cap)
    body = sl.get("body", "")
    y = text_block(d, 70, y, body, fb, INK, 940, 1.38)
    source(d, max(y + 30, H - 300), sl.get("source", ""), acc)
    return im

def s_number(sl, rnd, acc, meta):
    im = Image.new("RGB", (W, H), acc); im = Image.blend(im, Image.effect_noise((W, H), 30).convert("RGB"), .05)
    d = ImageDraw.Draw(im)
    for k in range(-6, 20): d.line([(k * 90, 0), (k * 90 - 600, H)], fill=tuple(min(255, c + 10) for c in acc), width=3)
    fb = anton_fit(d, sl["big"], 940, 360, maxlines=1)
    d.text((60, 300), sl["big"], font=fb, fill=PAPER)
    y = 300 + int(fb.size * 1.15)
    art = sl.get("art", "none")
    if art in ART:
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        ART[art](od, W * .5, y + 170, 260, (120, 14, 30) if art == "rambutan" else PAPER, rnd)
        im.paste(ov, (0, 0), ov); d = ImageDraw.Draw(im); y += 480
    ft = anton_fit(d, sl["title"].upper(), 940, 100, maxlines=2)
    for ln in wrap(d, sl["title"].upper(), ft, 940): d.text((70, y), ln, font=ft, fill=PAPER); y += int(ft.size * 1.22)
    y += 30; y = text_block(d, 70, y, sl.get("body", ""), F(LORA, 44), PAPER, 940, 1.38)
    if sl.get("source"): text_block(d, 70, max(y + 30, H - 300), sl["source"], F(GF + "Lora-Italic-Variable.ttf", 28), (250, 225, 225), 940)
    return im

def s_list(sl, rnd, acc, meta):
    im = paper(rnd); d = ImageDraw.Draw(im)
    art = sl.get("art", "none")
    y = 290
    ft = anton_fit(d, sl["title"].upper(), 940, 130, maxlines=2)
    for ln in wrap(d, sl["title"].upper(), ft, 940): d.text((70, y), ln, font=ft, fill=INK); y += int(ft.size * 1.22)
    if art in ART: ART[art](d, W * .5, y + 280, 280, acc, rnd); y += 620
    y += 20
    for k, it in enumerate(sl.get("items", [])):
        d.text((70, y), f"{k + 1:02d}", font=F(ANTON, 54), fill=acc)
        d.text((170, y + 6), it, font=F(LORA, 44, "Bold"), fill=INK); y += 70
    y += 10; y = text_block(d, 70, y, sl.get("body", ""), F(LORA, 40), INK, 940)
    source(d, max(y + 30, H - 300), sl.get("source", ""), acc)
    return im

def s_closing(sl, rnd, acc, meta):
    im = Image.new("RGB", (W, H), NAVY); im = Image.blend(im, Image.effect_noise((W, H), 30).convert("RGB"), .04)
    d = ImageDraw.Draw(im)
    art = sl.get("art", "rambutan")
    if art in ART: ART[art](d, W * .5, 470, 200, acc, rnd)
    y = 800
    ft = anton_fit(d, sl["title"].upper(), 940, 120, maxlines=3)
    for ln in wrap(d, sl["title"].upper(), ft, 940): d.text((70, y), ln, font=ft, fill=YEL); y += int(ft.size * 1.22)
    y += 30
    for it in sl.get("items", []):
        d.rounded_rectangle((70, y, W - 70, y + 92), radius=46, fill=PAPER)
        d.text((110, y + 16), it, font=F(LORA, 44, "Bold"), fill=NAVY); y += 112
    y += 20
    fc = F(POP, 38); tw = d.textlength(sl["cta"], font=fc)
    if tw > W - 200: fc = F(POP, 32); tw = d.textlength(sl["cta"], font=fc)
    d.rounded_rectangle((70, y, W - 70, y + 104), radius=24, fill=YEL)
    d.text(((W - tw) / 2, y + 28), sl["cta"], font=fc, fill=NAVY)
    return im

LAY = {"cover": s_cover, "story": s_story, "number": s_number, "list": s_list, "closing": s_closing}

def render(spec, out):
    os.makedirs(out, exist_ok=True)
    rnd = random.Random(spec.get("seed", 1)); acc = ACC.get(spec.get("accent", "red"), ACC["red"])
    n = len(spec["slides"]); files = []
    for i, sl in enumerate(spec["slides"], 1):
        im = LAY[sl["type"]](sl, rnd, acc, spec)
        d = ImageDraw.Draw(im)
        dark = sl["type"] in ("number", "closing")
        badge(d)
        if not dark:
            masthead(d, spec.get("series", ""), acc, i, n); footer(d, i, n, acc)
        else:
            f = F(POP, 30); s = f"{i}/{n}"
            d.text((W - 70 - d.textlength(s, font=f), H - 150), s, font=f, fill=PAPER)
            if i < n: d.text((70, H - 150), "Geser  >>", font=f, fill=PAPER)
        fn = os.path.join(out, f"slide_{i}.jpg"); im.save(fn, quality=92); files.append(fn)
    th = [Image.open(f).resize((270, 480)) for f in files]
    cols = min(4, n); rows = (n + cols - 1) // cols
    pv = Image.new("RGB", (cols * 280 + 10, rows * 490 + 10), (30, 30, 30))
    for k, t in enumerate(th): pv.paste(t, (10 + (k % cols) * 280, 10 + (k // cols) * 490))
    pv.save(os.path.join(out, "preview.jpg"), quality=85)

if __name__ == "__main__":
    render(json.load(open(sys.argv[1])), sys.argv[2])
