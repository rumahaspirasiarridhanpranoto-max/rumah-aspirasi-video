"""Video vertikal "Membalas komentar" (1080x1920, 30fps, H.264/AAC) dengan musik sintesis bebas hak cipta.

Pemakaian: python3 -I tools/balas_video.py konten.json keluaran.mp4
konten.json:
{
  "comment": "Jalan banyak yg rusak. Tolonglah",
  "user": "",                                  # opsional, mis. "@namaakun"
  "bg": ["foto/.../06.jpg", "foto/.../08.jpg"],  # foto latar (dari kiriman pemilik)
  "headline": "Kami dengar.|Biar bisa dikawal:",
  "intro": "Kirim lewat DM:",
  "items": ["Lokasi persis", "Foto/video", "..."],
  "outro": "Laporan lengkap|lebih cepat ditindaklanjuti",
  "cta": "Kirim DM sekarang",
  "mood": "tahunbaru",                         # suasana musik dari tools/ucapan_video.py
  "basis": {"tag": "DASARNYA", "title": "...", "cards": [{"text": "...", "src": "UU .../Pasal ..."}]}  # opsional
}
Adegan: (1) komentar muncul sebagai gelembung, (2) judul, (3) daftar muncul satu per satu,
(4) penutup + ajakan. Latar foto buram bergerak pelan (Ken Burns).
"""
import importlib.util, json, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
def _mod(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, name + ".py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
PS = _mod("photostory"); UV = _mod("ucapan_video")
W, H, FPS = 1080, 1920, 30
font, wrap, YEL, NAVY, BLUE, LB, WHITE = PS.font, PS.wrap, PS.YEL, PS.NAVY, PS.BLUE, PS.LB, PS.WHITE

def ease(t): t = max(0, min(1, t)); return 1 - (1 - t) ** 3

def bg_frames(srcs):
    out = []
    for s in srcs:
        ph = PS.cover_crop(PS.load(s), int(W * 1.12), int(H * 1.12), .4)
        sharp = ph
        blur = Image.blend(ph.filter(ImageFilter.GaussianBlur(6)), Image.new("RGB", ph.size, NAVY), .55)
        out.append(blur)
    return out

def ken(img, t):
    z = 1 + .08 * t; w, h = int(W * 1.12 / z), int(H * 1.12 / z)
    x = (img.width - w) // 2; y = int((img.height - h) * (.3 + .4 * t))
    return img.crop((x, y, x + w, y + h)).resize((W, H))

def bubble(d, y, text, user, a):
    f = font(54, "b"); lines = wrap(d, text, f, 780)
    h = 120 + len(lines) * 72
    x0 = 90; yy = y + int((1 - a) * 60)
    d.rounded_rectangle((x0, yy, W - 90, yy + h), radius=40, fill=(255, 255, 255, int(245 * a)))
    d.ellipse((x0 + 34, yy + 30, x0 + 94, yy + 90), fill=(200, 205, 220, int(255 * a)))
    d.text((x0 + 116, yy + 38), (user or "Komentar warga"), font=font(34, "s"), fill=(110, 118, 140, int(255 * a)))
    ty = yy + 100
    for ln in lines:
        d.text((x0 + 40, ty), ln, font=f, fill=(20, 24, 40, int(255 * a))); ty += 72
    return yy + h

def label(d, x, y, s, a, bg=YEL, fg=NAVY, size=34):
    f = font(size, "x"); w = d.textlength(s, font=f)
    d.rounded_rectangle((x, y, x + w + 52, y + size + 30), radius=(size + 30) // 2, fill=bg + (int(255 * a),))
    d.text((x + 26, y + 12), s, font=f, fill=fg + (int(255 * a),))

def title(d, y, s, a, size=92):
    parts = s.split("|")
    for k, p in enumerate(parts):
        for ln in wrap(d, p, font(size, "x"), 900):
            d.text((90 + int((1 - a) * -40), y), ln, font=font(size, "x"), fill=(YEL if k == len(parts) - 1 and len(parts) > 1 else WHITE) + (int(255 * a),))
            y += int(size * 1.08)
    return y

def frame(spec, bgs, t, T):
    # timeline (detik)
    s1, s2, s3 = 0.0, 3.2, 5.0
    s4 = s3 + 1.1 * len(spec["items"]) + 1.6
    nb = 5.8 if spec.get("basis") else 0
    s5 = s4 + nb
    which = 0 if t < s4 else 1
    im = ken(bgs[min(which, len(bgs) - 1)], t / T).convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    PS.badge(d)
    if t < s4:
        label(d, 90, 330, "MEMBALAS KOMENTAR", ease(t / .4), bg=BLUE, fg=WHITE, size=32)
        yb = bubble(d, 430, spec["comment"], spec.get("user", ""), ease((t - .2) / .6))
        if t >= s2:
            y = title(d, yb + 90, spec["headline"], ease((t - s2) / .6))
            if t >= s3:
                a = ease((t - s3) / .5)
                d.text((90, y + 40), spec["intro"], font=font(50, "b"), fill=(LB) + (int(255 * a),)); y += 140
                for i, it in enumerate(spec["items"]):
                    ai = ease((t - s3 - .5 - 1.1 * i) / .45)
                    if ai <= 0: break
                    x = 90 + int((1 - ai) * 80)
                    d.rounded_rectangle((x, y, W - 90, y + 116), radius=30, fill=(255, 255, 255, int(40 * ai)), outline=(255, 255, 255, int(110 * ai)), width=2)
                    d.ellipse((x + 24, y + 26, x + 88, y + 90), fill=YEL + (int(255 * ai),))
                    n = str(i + 1); fn = font(38, "x"); d.text((x + 56 - d.textlength(n, font=fn) / 2, y + 30), n, font=fn, fill=NAVY + (int(255 * ai),))
                    f = font(42, "b") if d.textlength(it, font=font(42, "b")) < 740 else font(36, "b")
                    d.text((x + 110, y + 32), it, font=f, fill=WHITE + (int(255 * ai),)); y += 136
    elif t < s5:
        B = spec["basis"]; a = ease((t - s4) / .5)
        label(d, 90, 300, B.get("tag", "DASARNYA"), a, size=34)
        y = title(d, 400, B["title"], a, size=78) + 40
        for i, c in enumerate(B["cards"]):
            ai = ease((t - s4 - .7 - 1.0 * i) / .5)
            if ai <= 0: break
            ft = font(40, "b"); lines = wrap(d, c["text"], ft, 820); h = 70 + len(lines) * 56 + 60
            x = 90 + int((1 - ai) * 80)
            d.rounded_rectangle((x, y, W - 90, y + h), radius=32, fill=(255, 255, 255, int(235 * ai)))
            d.rectangle((x, y + 30, x + 12, y + h - 30), fill=YEL + (int(255 * ai),))
            ty = y + 36
            for ln in lines: d.text((x + 50, ty), ln, font=ft, fill=NAVY + (int(255 * ai),)); ty += 56
            d.text((x + 50, ty + 10), c["src"], font=font(30, "s"), fill=BLUE + (int(255 * ai),))
            y += h + 34
    else:
        s4 = s5
        a = ease((t - s4) / .6)
        y = title(d, 700, spec["outro"], a, size=104)
        if t > s4 + .8:
            a2 = ease((t - s4 - .8) / .5); f = font(52, "x"); w = d.textlength(spec["cta"], font=f)
            d.rounded_rectangle(((W - w) / 2 - 50, y + 80, (W + w) / 2 + 50, y + 200), radius=60, fill=YEL + (int(255 * a2),))
            d.text(((W - w) / 2, y + 108), spec["cta"], font=f, fill=NAVY + (int(255 * a2),))
        f2 = font(46, "x"); s1_, s2_ = "DARI WARGA ", "KE KEBIJAKAN"
        w1 = d.textlength(s1_, font=f2); w2 = d.textlength(s2_, font=f2); xx = (W - w1 - w2) / 2
        d.text((xx, H - 260), s1_, font=f2, fill=WHITE + (int(255 * a),)); d.text((xx + w1, H - 260), s2_, font=f2, fill=YEL + (int(255 * a),))
    im = Image.alpha_composite(im, ov).convert("RGB")
    fade = min(1, t / .3, (T - t) / .4)
    if fade < 1: im = Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), im, max(0, fade))
    return im

def main(cfg, out):
    spec = json.load(open(cfg))
    T = 5.0 + 1.1 * len(spec["items"]) + 1.6 + 4.0 + (5.8 if spec.get("basis") else 0)
    bgs = bg_frames(spec["bg"])
    tmpv = out + ".v.mp4"; tmpa = out + ".wav"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium", tmpv], stdin=subprocess.PIPE)
    for k in range(int(T * FPS)):
        p.stdin.write(frame(spec, bgs, k / FPS, T).tobytes())
    p.stdin.close(); p.wait()
    audio = UV.compose(spec.get("mood", "tahunbaru"), T)
    audio = np.clip(audio * .8, -1, 1)
    with wave.open(tmpa, "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(UV.SR); w.writeframes((audio * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmpv, "-i", tmpa, "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", out], check=True)
    os.remove(tmpv); os.remove(tmpa)
    print("OK", out, round(T, 1), "detik")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
