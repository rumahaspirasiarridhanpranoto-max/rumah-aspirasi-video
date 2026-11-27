"""Ubah slide 9:16 (1080x1920) jadi 4:5 (1080x1350) untuk carousel Instagram/Facebook.

Pemakaian: python3 -I tools/ig_format.py carousel/YYYY-MM-DD-slug
Hasil: carousel/.../ig/slide_N.jpg (+ ig/preview.jpg).
Slide diperkecil utuh (tidak ada teks terpotong) dan diletakkan di tengah
di atas latar versi blur dari slide itu sendiri, dengan sedikit bayangan.
"""
import glob, os, re, sys
from PIL import Image, ImageFilter, ImageDraw

W, H = 1080, 1350

def convert(src, dst):
    im = Image.open(src).convert("RGB")
    bg = im.resize((W, int(im.height * W / im.width))).crop((0, (int(im.height * W / im.width) - H) // 2, W, (int(im.height * W / im.width) - H) // 2 + H))
    bg = bg.filter(ImageFilter.GaussianBlur(40))
    bg = Image.blend(bg, Image.new("RGB", (W, H), (10, 16, 40)), 0.35)
    h = H - 40; w = int(im.width * h / im.height)
    fg = im.resize((w, h), Image.LANCZOS)
    x, y = (W - w) // 2, 20
    sh = Image.new("L", (W, H), 0); ImageDraw.Draw(sh).rounded_rectangle((x + 6, y + 10, x + w + 6, y + h + 10), 24, fill=150)
    bg.paste((0, 0, 0), (0, 0), sh.filter(ImageFilter.GaussianBlur(14)))
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w, h), 24, fill=255)
    bg.paste(fg, (x, y), m)
    bg.save(dst, quality=92)

def main(folder):
    out = os.path.join(folder, "ig"); os.makedirs(out, exist_ok=True)
    files = sorted(glob.glob(os.path.join(folder, "slide_*.jpg")), key=lambda p: int(re.findall(r"(\d+)", os.path.basename(p))[0]))
    files = [f for f in files if re.fullmatch(r"slide_\d+\.jpg", os.path.basename(f))]
    for f in files: convert(f, os.path.join(out, os.path.basename(f)))
    th = [Image.open(os.path.join(out, os.path.basename(f))).resize((270, 338)) for f in files]
    cols = 4; rows = (len(th) + cols - 1) // cols
    pv = Image.new("RGB", (cols * 280 + 10, rows * 348 + 10), (30, 30, 30))
    for i, t in enumerate(th): pv.paste(t, (10 + (i % cols) * 280, 10 + (i // cols) * 348))
    pv.save(os.path.join(out, "preview.jpg"), quality=85)
    print(len(files), "slide ->", out)

if __name__ == "__main__":
    main(sys.argv[1])
