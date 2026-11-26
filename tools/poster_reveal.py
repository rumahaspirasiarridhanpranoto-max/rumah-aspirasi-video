"""Poster shown whole (never cropped): sections slide/fade in one by one over a blurred backdrop,
then the full poster holds for reading. Official Rumah Aspirasi logo badge top-right.
usage: poster_reveal.py poster.jpg logo.jpg out.mp4"""
import sys, math, subprocess
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

poster_p, logo_p, out = sys.argv[1], sys.argv[2], sys.argv[3]
W, H, FPS = 768, 1344, 30
P = Image.open(poster_p).convert("RGB").resize((W, H), Image.LANCZOS)
sy = H / 1600
bg = ImageEnhance.Brightness(P.filter(ImageFilter.GaussianBlur(28))).enhance(0.45)

# sections (y ranges in 1600-high poster coords), direction of entry
SECTIONS = [(0, 640, "down"), (640, 860, "left"), (860, 1080, "right"), (1080, 1385, "up"), (1385, 1600, "left")]
STAGGER, DUR = 1.0, 0.7

logo = Image.open(logo_p).convert("RGB").crop((130, 290, 960, 530))
bw = 230
logo = logo.resize((bw, int(logo.height * bw / logo.width)), Image.LANCZOS)
bh = logo.height
mask = Image.new("L", logo.size, 0)
ImageDraw.Draw(mask).rounded_rectangle([0, 0, bw - 1, bh - 1], 14, fill=255)
badge = Image.new("RGBA", (W, H), (0, 0, 0, 0))
bx, by = W - bw - 20, 112
sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(sh).rounded_rectangle([bx + 3, by + 5, bx + bw + 3, by + bh + 5], 14, fill=(0, 0, 0, 140))
badge = Image.alpha_composite(badge, sh.filter(ImageFilter.GaussianBlur(7)))
badge.paste(logo, (bx, by), mask)

def ease_out(t):
    t = max(0, min(1, t)); return 1 - (1 - t) ** 3

parts = []
for y0, y1, d in SECTIONS:
    a, b = int(y0 * sy), int(y1 * sy)
    parts.append((P.crop((0, a, W, b)).convert("RGBA"), a, d))

last_in = STAGGER * (len(SECTIONS) - 1) + DUR
T = last_in + 8.0  # hold to read
proc = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                         "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                         "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
for i in range(int(T * FPS)):
    t = i / FPS
    fr = bg.convert("RGBA")
    for k, (img, top, d) in enumerate(parts):
        u = ease_out((t - 0.3 - k * STAGGER) / DUR)
        if u <= 0:
            continue
        off = int((1 - u) * 120)
        dx, dy = {"left": (-off, 0), "right": (off, 0), "up": (0, off), "down": (0, -off)}[d]
        layer = img.copy()
        layer.putalpha(int(255 * u))
        fr.alpha_composite(layer, (dx, top + dy))
    # gentle light sweep across the finished poster
    ts = t - (last_in + 0.6)
    if 0 <= ts <= 1.4:
        sweep = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        cx = int(-300 + (W + 600) * ts / 1.4)
        ImageDraw.Draw(sweep).polygon([(cx, 0), (cx + 90, 0), (cx - 210, H), (cx - 300, H)], fill=(255, 255, 255, 45))
        fr.alpha_composite(sweep.filter(ImageFilter.GaussianBlur(25)))
    bu = ease_out((t - 0.2) / 0.6)
    if bu > 0:
        b = badge.copy(); b.putalpha(b.getchannel("A").point(lambda v: int(v * bu)))
        fr.alpha_composite(b)
    proc.stdin.write(fr.convert("RGB").tobytes())
proc.stdin.close(); proc.wait()
