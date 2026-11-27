"""Renderer carousel Rumah Aspirasi.

Pemakaian:  python3 tools/render.py konten.json  folder_keluaran
konten.json:
{
  "theme": "tips" | "viral" | "dunia" | "tekno" | "aspirasi",
  "seed": 7,                      # ganti tiap posting -> variasi tata letak/hiasan
  "slides": [
    {"type": "cover", "kicker": "...", "title": "...", "sub": "...", "icon": "bulb"},
    {"type": "point", "num": "1", "kicker": "...", "title": "...", "body": "...",
     "bad": "...", "good": "...", "icon": "target"},
    {"type": "fact", "big": "42%", "label": "...", "body": "...", "source": "Sumber: ..."},
    {"type": "text", "kicker": "...", "title": "...", "body": "..."},
    {"type": "closing", "title": "...", "items": ["..."], "cta": "..."},
    {"type": "photo", "src": "foto/2026-12-01-reses/a.jpg", "label": "SEBELUM", "kicker": "...", "title": "...", "body": "...", "layout": "full|frame"}
  ]
}
Ikon: target, pin, camera, people, bulb, phone, shield, globe, chip, news, check, warn
Badge "Rumah Aspirasi · Arridhan Pranoto" selalu ada (anti re-upload).
"""
import json, math, os, random, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
FD = "/usr/share/fonts/truetype/google-fonts/"
def font(size, w="b"):
    names = {"x": "Poppins-ExtraBold.ttf", "b": "Poppins-Bold.ttf", "m": "Poppins-Medium.ttf", "s": "Poppins-SemiBold.ttf"}
    p = FD + names[w]
    if not os.path.exists(p): p = FD + "Poppins-Bold.ttf"
    return ImageFont.truetype(p, size)

BRAND_BLUE, BRAND_LB, BRAND_Y, NAVY, WHITE = (52, 78, 184), (83, 166, 245), (245, 238, 27), (14, 24, 62), (255, 255, 255)
RED, GREEN = (232, 72, 85), (46, 184, 114)

# ---------- palet per tema: daftar "suasana" yang dirotasi antar slide ----------
THEMES = {
    "aspirasi": [  # bg, teks utama, aksen, teks halus, kartu
        dict(bg=("flat", BRAND_Y), fg=NAVY, ac=BRAND_BLUE, mu=(90, 80, 20), card=WHITE, ink=NAVY),
        dict(bg=("flat", (244, 246, 251)), fg=NAVY, ac=BRAND_BLUE, mu=(120, 132, 165), card=WHITE, ink=NAVY),
        dict(bg=("grad", (40, 66, 170), (18, 30, 90)), fg=WHITE, ac=BRAND_Y, mu=(200, 215, 250), card=(28, 42, 96), ink=WHITE),
        dict(bg=("grad", (14, 24, 62), (8, 14, 36)), fg=WHITE, ac=BRAND_LB, mu=(170, 190, 240), card=(28, 42, 96), ink=WHITE),
    ],
    "tips": [
        dict(bg=("flat", (255, 214, 64)), fg=(30, 30, 40), ac=(232, 72, 85), mu=(90, 70, 20), card=WHITE, ink=(30, 30, 40)),
        dict(bg=("flat", (255, 246, 230)), fg=(30, 30, 40), ac=(255, 120, 60), mu=(130, 110, 90), card=WHITE, ink=(30, 30, 40)),
        dict(bg=("flat", (46, 184, 114)), fg=WHITE, ac=(255, 230, 80), mu=(220, 250, 230), card=WHITE, ink=(20, 60, 40)),
        dict(bg=("flat", (255, 120, 60)), fg=WHITE, ac=(255, 236, 120), mu=(255, 225, 205), card=WHITE, ink=(60, 30, 20)),
    ],
    "viral": [  # gaya cek fakta / berita
        dict(bg=("flat", (16, 16, 20)), fg=WHITE, ac=(232, 52, 60), mu=(180, 180, 190), card=(36, 36, 44), ink=WHITE),
        dict(bg=("flat", (245, 245, 245)), fg=(16, 16, 20), ac=(220, 40, 50), mu=(110, 110, 120), card=WHITE, ink=(16, 16, 20)),
        dict(bg=("flat", (220, 40, 50)), fg=WHITE, ac=(255, 230, 80), mu=(255, 210, 210), card=(255, 255, 255), ink=(20, 20, 24)),
    ],
    "dunia": [
        dict(bg=("grad", (8, 40, 60), (4, 18, 30)), fg=WHITE, ac=(60, 220, 200), mu=(170, 210, 215), card=(20, 60, 80), ink=WHITE),
        dict(bg=("flat", (236, 244, 240)), fg=(10, 40, 50), ac=(0, 150, 140), mu=(100, 130, 130), card=WHITE, ink=(10, 40, 50)),
        dict(bg=("grad", (0, 120, 120), (0, 60, 80)), fg=WHITE, ac=(255, 210, 90), mu=(200, 235, 230), card=(0, 90, 100), ink=WHITE),
    ],
    "tekno": [
        dict(bg=("grad", (20, 8, 48), (6, 4, 20)), fg=WHITE, ac=(0, 240, 255), mu=(180, 170, 230), card=(40, 24, 90), ink=WHITE),
        dict(bg=("grad", (60, 20, 140), (20, 8, 60)), fg=WHITE, ac=(255, 60, 200), mu=(210, 190, 250), card=(70, 40, 150), ink=WHITE),
        dict(bg=("flat", (240, 240, 250)), fg=(20, 10, 50), ac=(110, 60, 255), mu=(120, 110, 160), card=WHITE, ink=(20, 10, 50)),
    ],
}
THEME_LABEL = {"aspirasi": "ASPIRASI", "tips": "TIPS & TRIK", "viral": "CEK FAKTA", "dunia": "DUNIA HARI INI", "tekno": "TEKNOLOGI"}

def lighten(c, k): return tuple(int(v + (255 - v) * k) for v in c)
def darken(c, k): return tuple(int(v * (1 - k)) for v in c)

def make_bg(p, rnd):
    kind = p["bg"][0]
    if kind == "flat":
        im = Image.new("RGB", (W, H), p["bg"][1])
    else:
        c1, c2 = p["bg"][1], p["bg"][2]
        yy = np.linspace(0, 1, H)[:, None]
        a = np.zeros((H, W, 3))
        for i in range(3): a[..., i] = c1[i] + (c2[i] - c1[i]) * yy
        im = Image.fromarray(a.astype(np.uint8))
        g = Image.new("RGB", (W, H), 0)
        x, y = rnd.randint(100, 980), rnd.randint(300, 1500)
        ImageDraw.Draw(g).ellipse((x - 420, y - 420, x + 420, y + 420), fill=p["ac"])
        g = g.filter(ImageFilter.GaussianBlur(190))
        im = Image.fromarray(np.clip(np.asarray(im, float) + np.asarray(g, float) * .35, 0, 255).astype(np.uint8))
    return im

def decorate(im, p, theme, rnd, kind=""):
    d = ImageDraw.Draw(im)
    base = p["bg"][1]
    dim = lighten(base, .12) if sum(base) < 380 else darken(base, .07)
    m = rnd.choice(["dots", "rings", "stripes", "grid", "blob"])
    if theme == "tekno": m = rnd.choice(["grid", "circuit"])
    if theme == "dunia": m = rnd.choice(["lat", "rings"])
    if theme == "viral": m = rnd.choice(["stripes", "ticker"]) if kind != "closing" else "stripes"
    if m == "dots":
        x0, y0 = rnd.choice([(80, 230), (760, 230), (760, 1500)])
        for i in range(7):
            for j in range(5): d.ellipse((x0 + i * 34 - 5, y0 + j * 34 - 5, x0 + i * 34 + 5, y0 + j * 34 + 5), fill=dim)
    elif m == "rings":
        cx, cy = rnd.choice([(W, 300), (0, 1650), (W, 1500)])
        for r in range(120, 700, 70): d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=dim, width=6)
    elif m == "stripes":
        for k in range(-4, 14): d.line([(k * 120, H), (k * 120 + 700, H - 700)], fill=dim, width=22)
    elif m == "grid" :
        for x in range(0, W, 90): d.line([(x, 0), (x, H)], fill=dim, width=2)
        for y in range(0, H, 90): d.line([(0, y), (W, y)], fill=dim, width=2)
    elif m == "circuit":
        for _ in range(14):
            x, y = rnd.randrange(0, W, 60), rnd.randrange(200, H, 60)
            pts = [(x, y)]
            for __ in range(4):
                x += rnd.choice([0, 120, -120]); y += rnd.choice([0, 120])
                pts.append((x, y))
            d.line(pts, fill=dim, width=5)
            d.ellipse((x - 10, y - 10, x + 10, y + 10), fill=p["ac"])
    elif m == "lat":
        for k in range(8):
            d.arc((-400, 200 + k * 180, W + 400, 900 + k * 180), 200, 340, fill=dim, width=4)
    elif m == "blob":
        cx, cy = rnd.randint(700, 1000), rnd.randint(250, 600)
        d.ellipse((cx - 260, cy - 260, cx + 260, cy + 260), fill=dim)
    elif m == "ticker":
        d.rectangle((0, H - 300, W, H - 230), fill=p["ac"])
        f = font(30, "b"); x = 20
        while x < W:
            d.text((x, H - 290), "CEK DULU SEBELUM SHARE  •", font=f, fill=WHITE); x += 520

# ---------- ikon ----------
def icon(d, name, cx, cy, s, p):
    ac, fg, card = p["ac"], p["fg"], p["card"]
    if name == "target":
        for i, rr in enumerate([s, s * .68, s * .36]): d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=ac if i % 2 == 0 else card)
        d.line([(cx + s * 1.1, cy - s * 1.1), (cx + 6, cy - 6)], fill=fg, width=16)
    elif name == "pin":
        d.ellipse((cx - s * .7, cy - s * 1.4, cx + s * .7, cy), fill=ac)
        d.polygon([(cx - s * .6, cy - s * .45), (cx + s * .6, cy - s * .45), (cx, cy + s * .6)], fill=ac)
        d.ellipse((cx - s * .28, cy - s * .98, cx + s * .28, cy - s * .42), fill=card)
    elif name == "camera":
        d.rounded_rectangle((cx - s * 1.2, cy - s * .75, cx + s * 1.2, cy + s * .85), radius=30, fill=fg)
        d.ellipse((cx - s * .6, cy - s * .5, cx + s * .6, cy + s * .7), fill=ac)
        d.ellipse((cx - s * .32, cy - s * .22, cx + s * .32, cy + s * .42), fill=card)
    elif name == "people":
        for i, dx in enumerate([-1.2, 0, 1.2]):
            r = s * (.38 if i != 1 else .46); x = cx + dx * s; yo = 0 if i == 1 else s * .2
            col = ac if i == 1 else fg
            d.ellipse((x - r, cy - s + yo - r, x + r, cy - s + yo + r), fill=col)
            d.rounded_rectangle((x - r * 1.5, cy - s * .45 + yo, x + r * 1.5, cy + s * .7 + yo), radius=int(r), fill=col)
    elif name == "bulb":
        for a in range(20, 170, 30):
            r1, r2 = s * 1.2, s * 1.55
            d.line([(cx + r1 * math.cos(math.radians(a)), cy - .2 * s - r1 * math.sin(math.radians(a))),
                    (cx + r2 * math.cos(math.radians(a)), cy - .2 * s - r2 * math.sin(math.radians(a)))], fill=ac, width=14)
        d.ellipse((cx - s * .9, cy - s * 1.1, cx + s * .9, cy + s * .7), fill=ac)
        d.rounded_rectangle((cx - s * .45, cy + s * .5, cx + s * .45, cy + s * 1.1), radius=10, fill=fg)
    elif name == "phone":
        d.rounded_rectangle((cx - s * .7, cy - s * 1.3, cx + s * .7, cy + s * 1.3), radius=36, fill=fg)
        d.rounded_rectangle((cx - s * .58, cy - s * 1.12, cx + s * .58, cy + s * 1.05), radius=20, fill=ac)
        for k in range(3): d.rounded_rectangle((cx - s * .45, cy - s * .8 + k * s * .5, cx + s * .3, cy - s * .55 + k * s * .5), radius=10, fill=card)
    elif name == "shield":
        d.polygon([(cx, cy - s * 1.2), (cx + s, cy - s * .7), (cx + s * .8, cy + s * .5), (cx, cy + s * 1.2), (cx - s * .8, cy + s * .5), (cx - s, cy - s * .7)], fill=ac)
        d.line([(cx - s * .4, cy), (cx - s * .05, cy + s * .35), (cx + s * .45, cy - s * .3)], fill=card, width=int(s * .2), joint="curve")
    elif name == "globe":
        d.ellipse((cx - s, cy - s, cx + s, cy + s), fill=ac)
        d.ellipse((cx - s * .45, cy - s, cx + s * .45, cy + s), outline=card, width=8)
        d.line([(cx - s, cy), (cx + s, cy)], fill=card, width=8); d.line([(cx, cy - s), (cx, cy + s)], fill=card, width=8)
        d.arc((cx - s * .95, cy - s * 1.4, cx + s * .95, cy - s * .2), 20, 160, fill=card, width=6)
        d.arc((cx - s * .95, cy + s * .2, cx + s * .95, cy + s * 1.4), 200, 340, fill=card, width=6)
    elif name == "chip":
        d.rounded_rectangle((cx - s * .8, cy - s * .8, cx + s * .8, cy + s * .8), radius=24, fill=ac)
        d.rounded_rectangle((cx - s * .4, cy - s * .4, cx + s * .4, cy + s * .4), radius=12, fill=card)
        for k in range(-2, 3):
            o = k * s * .3
            for a, b in [((cx + o, cy - s * .8), (cx + o, cy - s * 1.15)), ((cx + o, cy + s * .8), (cx + o, cy + s * 1.15)),
                         ((cx - s * .8, cy + o), (cx - s * 1.15, cy + o)), ((cx + s * .8, cy + o), (cx + s * 1.15, cy + o))]:
                d.line([a, b], fill=ac, width=10)
    elif name == "news":
        d.rounded_rectangle((cx - s * 1.1, cy - s * .9, cx + s * 1.1, cy + s * .9), radius=20, fill=card)
        d.rectangle((cx - s * .9, cy - s * .7, cx + s * .9, cy - s * .35), fill=ac)
        for k in range(4): d.rectangle((cx - s * .9, cy - s * .15 + k * s * .25, cx + s * (.9 if k % 2 == 0 else .4), cy - s * .03 + k * s * .25), fill=p["mu"])
    elif name == "check":
        d.ellipse((cx - s, cy - s, cx + s, cy + s), fill=GREEN)
        d.line([(cx - s * .45, cy), (cx - s * .1, cy + s * .38), (cx + s * .5, cy - s * .35)], fill=WHITE, width=int(s * .22), joint="curve")
    elif name == "warn":
        d.polygon([(cx, cy - s), (cx + s * 1.1, cy + s * .85), (cx - s * 1.1, cy + s * .85)], fill=ac)
        f = font(int(s * 1.2), "x"); d.text((cx - d.textlength("!", font=f) / 2, cy - s * .65), "!", font=f, fill=card)

# ---------- utilitas teks ----------
def wrap(d, text, f, maxw):
    out, cur = [], ""
    for w in str(text).split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= maxw: cur = t
        else:
            if cur: out.append(cur)
            cur = w
    return out + [cur]

def block(d, x, y, text, f, fill, maxw, gap=1.22, align="left"):
    for ln in wrap(d, text, f, maxw):
        w = d.textlength(ln, font=f)
        d.text((x if align == "left" else x + (maxw - w) / 2, y), ln, font=f, fill=fill)
        y += f.size * gap
    return y

def fit(d, text, maxw, maxlines, start, minsize=60, w="x"):
    s = start
    while s > minsize:
        f = font(s, w)
        ls = wrap(d, text, f, maxw)
        if len(ls) <= maxlines and all(d.textlength(l, font=f) <= maxw for l in ls): return f
        s -= 6
    return font(minsize, w)

def card(im, box, fill, radius=34, off=10):
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((box[0] + off, box[1] + off, box[2] + off, box[3] + off), radius=radius, fill=(0, 0, 0, 60))
    sh = sh.filter(ImageFilter.GaussianBlur(12)); im.paste(sh, (0, 0), sh)
    ImageDraw.Draw(im).rounded_rectangle(box, radius=radius, fill=fill)

def mark(d, x, y, ok, s=44):
    d.ellipse((x, y, x + s, y + s), fill=GREEN if ok else RED); w = max(5, s // 8)
    if ok: d.line([(x + s * .25, y + s * .52), (x + s * .43, y + s * .7), (x + s * .76, y + s * .32)], fill=WHITE, width=w, joint="curve")
    else:
        d.line([(x + s * .3, y + s * .3), (x + s * .7, y + s * .7)], fill=WHITE, width=w)
        d.line([(x + s * .7, y + s * .3), (x + s * .3, y + s * .7)], fill=WHITE, width=w)

def badge(d, p):
    f = font(34); s = "Rumah Aspirasi · Arridhan Pranoto"
    w = d.textlength(s, font=f); x = (W - w) / 2 - 30
    d.rounded_rectangle((x, 96, x + w + 60, 168), radius=36, fill=BRAND_BLUE, outline=BRAND_LB, width=3)
    d.text((x + 30, 107), s, font=f, fill=WHITE)

def tag(d, theme, p, x=90, y=210):
    f = font(32, "b"); s = THEME_LABEL[theme]
    w = d.textlength(s, font=f)
    d.rounded_rectangle((x, y, x + w + 44, y + 62), radius=12, fill=p["ac"])
    d.text((x + 22, y + 10), s, font=f, fill=p["card"] if p["ac"] != p["card"] else p["fg"])

def footer(d, i, n, p):
    f = font(30, "m"); s = f"{i}/{n}"
    d.text((W - 90 - d.textlength(s, font=f), H - 150), s, font=f, fill=p["mu"])
    if i < n: d.text((90, H - 150), "Geser  >>", font=f, fill=p["mu"])

# ---------- tata letak ----------
def s_cover(im, d, sl, p, theme, rnd):
    lay = rnd.choice(["top", "center", "split"])
    ic = sl.get("icon", "bulb")
    if lay == "split":
        d.polygon([(0, 1150), (W, 980), (W, H), (0, H)], fill=p["ac"] if p["bg"][0] == "flat" else darken(p["bg"][1], .3))
        icon(d, ic, W / 2, 1420, 170, dict(p, ac=p["fg"] if p["bg"][0] == "flat" else p["ac"], fg=p["card"]))
        y0 = 300
    elif lay == "top":
        icon(d, ic, W - 260, 430, 130, p); y0 = 620
    else:
        icon(d, ic, W / 2, 470, 150, p); y0 = 760
    tag(d, theme, p, 90, y0 - 100 if lay != "split" else 220)
    if sl.get("kicker"): d.text((90, y0), sl["kicker"].upper(), font=font(64, "b"), fill=p["ac"] if lay != "split" else p["ac"]); y0 += 90
    f = fit(d, sl["title"], 900, 4, 150)
    y = block(d, 90, y0, sl["title"], f, p["fg"], 900, 1.05)
    if sl.get("sub"):
        fs = font(54, "b"); tw = min(900, d.textlength(sl["sub"], font=fs) + 60)
        lines = wrap(d, sl["sub"], fs, 840)
        hh = len(lines) * fs.size * 1.25 + 40
        d.rounded_rectangle((90, y + 30, 90 + tw, y + 30 + hh), radius=20, fill=p["fg"])
        block(d, 120, y + 46, sl["sub"], fs, p["bg"][1] if p["bg"][0] == "flat" else p["bg"][2], 840, 1.25)

def s_point(im, d, sl, p, theme, rnd):
    lay = rnd.choice(["iconL", "iconR", "band"])
    num = sl.get("num", "")
    nf = font(400, "x"); numcol = lighten(p["bg"][1], .1) if sum(p["bg"][1]) < 380 else darken(p["bg"][1], .08)
    if lay == "band":
        d.rectangle((0, 0, W, 720), fill=p["ac"])
        if num: d.text((90, 170), num, font=nf, fill=darken(p["ac"], .15))
        icon(d, sl.get("icon", "check"), 700, 470, 120, dict(p, ac=p["card"], card=p["ac"], fg=p["fg"] if p["bg"][0] == "flat" else NAVY))
        badge(d, p); y = 800
    else:
        x_num, x_ic = (640, 300) if lay == "iconL" else (80, 760)
        if num: d.text((x_num, 160), num, font=nf, fill=numcol)
        icon(d, sl.get("icon", "check"), x_ic, 480, 130, p); y = 760
    if sl.get("kicker"): d.text((90, y), sl["kicker"].upper(), font=font(58, "b"), fill=p["ac"] if lay != "band" else p["fg"]); y += 76
    f = fit(d, sl["title"], 900, 2, 160)
    y = block(d, 90, y, sl["title"], f, p["fg"], 900, 1.05) + 45
    if sl.get("body"): y = block(d, 90, y, sl["body"], font(42, "m"), p["mu"], 900, 1.35) + 20
    if sl.get("bad") or sl.get("good"):
        for lab, txt, ok in [("KURANG", sl.get("bad"), False), ("LEBIH KUAT", sl.get("good"), True)]:
            if not txt: continue
            ft = font(40, "m"); ls = wrap(d, txt, ft, W - 260)
            hh = 120 + len(ls) * 52
            card(im, (90, y, W - 90, y + hh), p["card"]); d = ImageDraw.Draw(im)
            mark(d, 130, y + 36, ok); d.text((192, y + 38), lab, font=font(32), fill=GREEN if ok else RED)
            block(d, 130, y + 98, txt, ft, p["ink"], W - 260, 1.3)
            y += hh + 36
    return d

def s_fact(im, d, sl, p, theme, rnd):
    tag(d, theme, p)
    if sl.get("label"): block(d, 90, 420, sl["label"].upper(), font(56, "b"), p["ac"], 900)
    f = fit(d, sl["big"], 920, 1, 300, 120)
    d.text((90, 520), sl["big"], font=f, fill=p["fg"])
    y = 540 + f.size * 1.1
    d.rectangle((90, y, 290, y + 14), fill=p["ac"])
    y = block(d, 90, y + 60, sl.get("body", ""), font(50, "s"), p["fg"], 900, 1.35)
    if sl.get("source"):
        block(d, 90, H - 300, sl["source"], font(30, "m"), p["mu"], 900, 1.3)

def s_text(im, d, sl, p, theme, rnd):
    tag(d, theme, p)
    y = 420
    if sl.get("kicker"): d.text((90, y), sl["kicker"].upper(), font=font(58, "b"), fill=p["ac"]); y += 90
    f = fit(d, sl["title"], 900, 3, 130)
    y = block(d, 90, y, sl["title"], f, p["fg"], 900, 1.08) + 40
    body = sl.get("body", "")
    fb = font(46, "m"); ls = wrap(d, body, fb, W - 260)
    hh = len(ls) * fb.size * 1.4 + 90
    card(im, (90, y, W - 90, y + hh), p["card"]); d = ImageDraw.Draw(im)
    d.rectangle((90, y + 30, 104, y + hh - 30), fill=p["ac"])
    block(d, 140, y + 45, body, fb, p["ink"], W - 260, 1.4)
    if sl.get("source"): block(d, 90, H - 300, sl["source"], font(30, "m"), p["mu"], 900, 1.3)
    return d

def s_closing(im, d, sl, p, theme, rnd):
    from math import cos
    # logo
    cx, cy, sc = W / 2, 330, .9
    for col, pts in [(BRAND_BLUE, [(-137, -2), (0, 95), (137, -2)]), (BRAND_BLUE, [(-109, -22), (0, 56), (109, -22)]),
                     (BRAND_Y, [(-82, -32), (0, -94), (82, -32)]), (BRAND_Y, [(-56, -13), (0, -58), (56, -13)])]:
        d.line([(cx + x * sc, cy + y * sc) for x, y in pts], fill=col, width=int(17 * sc), joint="curve")
    d.polygon([(cx, cy - 16 * sc), (cx - 19 * sc, cy), (cx, cy + 16 * sc), (cx + 19 * sc, cy)], fill=BRAND_LB)
    f = fit(d, sl.get("title", ""), 900, 2, 96)
    y = block(d, 90, 430, sl.get("title", ""), f, p["fg"], 900, 1.1, "center") + 30
    for it in sl.get("items", []):
        ft = font(44, "b"); ls = wrap(d, it, ft, W - 400); hh = max(104, 40 + len(ls) * 56)
        card(im, (130, y, W - 130, y + hh), p["card"], radius=46, off=8); d = ImageDraw.Draw(im)
        mark(d, 160, y + (hh - 56) / 2, True, 56)
        block(d, 240, y + (hh - len(ls) * 56) / 2 - 4, it, ft, p["ink"], W - 400, 1.25)
        y += hh + 24
    if sl.get("cta"):
        fc = font(42, "b"); ls = wrap(d, sl["cta"], fc, W - 320); hh = len(ls) * 54 + 50
        d.rounded_rectangle((130, y + 20, W - 130, y + 20 + hh), radius=30, fill=BRAND_Y)
        block(d, 160, y + 42, sl["cta"], fc, NAVY, W - 320, 1.28, "center")
    fa = font(66, "x"); a, b = "DARI WARGA ", "KE KEBIJAKAN"
    w = d.textlength(a, font=fa) + d.textlength(b, font=fa); x = (W - w) / 2
    tcol = p["fg"]
    d.text((x, H - 300), a, font=fa, fill=tcol)
    d.text((x + d.textlength(a, font=fa), H - 300), b, font=fa, fill=BRAND_BLUE if sum(p["bg"][1]) > 500 else BRAND_Y)
    return d

def s_photo(im, d, sl, p, theme, rnd):
    """Slide foto lapangan: {"type":"photo","src":"foto/.../a.jpg","kicker":"...","title":"...","body":"...","label":"SEBELUM"}"""
    ph = Image.open(sl["src"]).convert("RGB")
    if sl.get("enhance", True):  # edit otomatis: kontras, warna, sedikit hangat, tajam
        from PIL import ImageOps, ImageEnhance
        ph = ImageOps.autocontrast(ph, cutoff=1)
        ph = ImageEnhance.Color(ph).enhance(1.15); ph = ImageEnhance.Contrast(ph).enhance(1.06)
        a_ = np.asarray(ph).astype(float); a_[..., 0] *= 1.03; a_[..., 2] *= .97
        ph = Image.fromarray(np.clip(a_, 0, 255).astype(np.uint8)).filter(ImageFilter.UnsharpMask(2, 70, 2))
    lay = sl.get("layout") or ("wide" if ph.width / ph.height > 1.2 else rnd.choice(["full", "frame"]))
    if lay == "wide":  # foto lanskap (foto bersama): tampil utuh, tidak terpotong
        # latar: foto yang sama diperbesar + blur + lapisan navy -> kesan sinematik
        r = max(W / ph.width, H / ph.height)
        bg = ph.resize((int(ph.width * r + 1), int(ph.height * r + 1)))
        bg = bg.crop(((bg.width - W) // 2, (bg.height - H) // 2, (bg.width - W) // 2 + W, (bg.height - H) // 2 + H)).filter(ImageFilter.GaussianBlur(28))
        ov = np.asarray(bg, float) * .35 + np.array(NAVY, float) * .65
        grad = np.linspace(0, 1, H)[:, None, None]
        ov = ov * (1 - .35 * grad) + np.array((6, 10, 30), float) * .35 * grad
        im.paste(Image.fromarray(np.clip(ov, 0, 255).astype(np.uint8)), (0, 0))
        bw = 960; bh = int(bw * ph.height / ph.width)
        ph = ph.resize((bw, bh), Image.LANCZOS); top = 400
        # bingkai putih tipis + bayangan, sedikit miring agar dinamis
        fr = Image.new("RGBA", (bw + 24, bh + 24), (255, 255, 255, 255)); fr.paste(ph, (12, 12))
        fr = fr.rotate(rnd.choice([-2, -1.5, 1.5, 2]), expand=True, resample=Image.BICUBIC)
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); a_ = fr.split()[3]
        sh.paste((0, 0, 0, 140), (int((W - fr.width) / 2) + 14, top + 22), a_); sh = sh.filter(ImageFilter.GaussianBlur(18))
        im.paste(sh, (0, 0), sh); im.paste(fr, (int((W - fr.width) / 2), top), fr)
        d = ImageDraw.Draw(im)
        # aksen garis brand
        d.rectangle((90, top + bh + 120, 250, top + bh + 132), fill=BRAND_Y)
        y = top + bh + 170; fg, mu = WHITE, (205, 215, 240)
        p = dict(p, ac=BRAND_Y)
        if sl.get("label"):
            f = font(40, "x"); w = d.textlength(sl["label"], font=f)
            d.rounded_rectangle((90, top - 40, 90 + w + 48, top + 32), radius=14, fill=BRAND_Y)
            d.text((114, top - 32), sl["label"], font=f, fill=NAVY)
        if sl.get("kicker"): d.text((90, y), sl["kicker"].upper(), font=font(52, "b"), fill=p["ac"]); y += 80
        if sl.get("title"): y = block(d, 90, y, sl["title"], fit(d, sl["title"], 900, 3, 112), fg, 900, 1.08) + 40
        if sl.get("body"): block(d, 90, y, sl["body"], font(42, "m"), mu, 900, 1.35)
        return d
    if lay == "full":
        r = max(W / ph.width, H / ph.height)
        ph = ph.resize((int(ph.width * r + 1), int(ph.height * r + 1)))
        ph = ph.crop(((ph.width - W) // 2, (ph.height - H) // 2, (ph.width - W) // 2 + W, (ph.height - H) // 2 + H))
        im.paste(ph, (0, 0))
        ov = np.zeros((H, W, 4), np.uint8); ov[..., :3] = NAVY
        a = np.clip((np.linspace(0, 1, H) - .45) / .4, 0, 1) * 235
        top = np.clip((.16 - np.linspace(0, 1, H)) / .16, 0, 1) * 150
        ov[..., 3] = np.maximum(a, top)[:, None].astype(np.uint8)
        im.paste(Image.fromarray(ov, "RGBA"), (0, 0), Image.fromarray(ov, "RGBA"))
        d = ImageDraw.Draw(im); y = 1180; fg, mu = WHITE, (210, 220, 245)
    else:
        bw, bh = 900, 900
        r = max(bw / ph.width, bh / ph.height)
        ph = ph.resize((int(ph.width * r + 1), int(ph.height * r + 1)))
        ph = ph.crop(((ph.width - bw) // 2, (ph.height - bh) // 2, (ph.width - bw) // 2 + bw, (ph.height - bh) // 2 + bh))
        card(im, (80, 230, 80 + bw + 20, 230 + bh + 20), WHITE, radius=20)
        im.paste(ph, (90, 240)); d = ImageDraw.Draw(im); y = 1220; fg, mu = p["fg"], p["mu"]
    if sl.get("label"):
        f = font(40, "x"); w = d.textlength(sl["label"], font=f)
        d.rounded_rectangle((90, 260 if lay == "full" else 270, 90 + w + 48, (260 if lay == "full" else 270) + 72), radius=14, fill=BRAND_Y)
        d.text((114, (268 if lay == "full" else 278)), sl["label"], font=f, fill=NAVY)
    if sl.get("kicker"): d.text((90, y), sl["kicker"].upper(), font=font(48, "b"), fill=BRAND_Y if lay == "full" else p["ac"]); y += 70
    if sl.get("title"): y = block(d, 90, y, sl["title"], fit(d, sl["title"], 900, 2, 96), fg, 900, 1.08) + 40
    if sl.get("body"): block(d, 90, y, sl["body"], font(40, "m"), mu, 900, 1.35)
    return d

LAYOUT = {"photo": s_photo, "cover": s_cover, "point": s_point, "fact": s_fact, "text": s_text, "closing": s_closing}

def render(spec, out):
    os.makedirs(out, exist_ok=True)
    theme = spec.get("theme", "aspirasi"); rnd = random.Random(spec.get("seed", 1))
    pals = THEMES[theme][:]; rnd.shuffle(pals)
    n = len(spec["slides"]); files = []; prev = None
    for i, sl in enumerate(spec["slides"], 1):
        choices = [q for q in pals if q is not prev] or pals
        p = choices[(i + rnd.randint(0, 5)) % len(choices)]; prev = p
        im = make_bg(p, rnd); decorate(im, p, theme, rnd, sl["type"])
        d = ImageDraw.Draw(im)
        d = LAYOUT[sl["type"]](im, d, sl, p, theme, rnd) or ImageDraw.Draw(im)
        d = ImageDraw.Draw(im); badge(d, p); footer(d, i, n, dict(p, mu=(200, 210, 235)) if sl["type"] == "photo" else p)
        fn = os.path.join(out, f"slide_{i}.jpg"); im.save(fn, quality=92); files.append(fn)
    th = [Image.open(f).resize((270, 480)) for f in files]
    cols = min(4, n); rows = (n + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 280 + 10, rows * 490 + 10), (20, 20, 20))
    for i, t in enumerate(th): sheet.paste(t, (10 + (i % cols) * 280, 10 + (i // cols) * 490))
    sheet.save(os.path.join(out, "preview.jpg"), quality=88)
    return files

if __name__ == "__main__":
    render(json.load(open(sys.argv[1])), sys.argv[2])
