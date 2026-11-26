"""Build a watermark badge from the official Rumah Aspirasi logo, unaltered (crop + uniform scale only)."""
import sys
from PIL import Image, ImageDraw, ImageFilter

logo_path, W, H, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
logo = Image.open(logo_path).convert("RGB")
# Crop the lockup (icon + "Rumah Aspirasi / Oleh Arridhan Pranoto") with its own blue background
lock = logo.crop((130, 290, 960, 530))
s = W / 768
target_w = int(300 * s)
lock = lock.resize((target_w, int(lock.height * target_w / lock.width)), Image.LANCZOS)
bw, bh = lock.size
r = int(16 * s)
mask = Image.new("L", lock.size, 0)
ImageDraw.Draw(mask).rounded_rectangle([0, 0, bw - 1, bh - 1], r, fill=255)

img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
x0, y0 = int(26 * s), int(112 * s)
sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(sh).rounded_rectangle([x0 + 3, y0 + 5, x0 + bw + 3, y0 + bh + 5], r, fill=(0, 0, 0, 120))
img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(7)))
img.paste(lock, (x0, y0), mask)
img.save(out)
