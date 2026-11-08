"""Lay frames from a video (or a folder of images) out on one sheet, so you can review a piece at a glance.

Usage:
  python3 contact_sheet.py <video.mp4> <out.jpg> [frames=12] [cols=6]
  python3 contact_sheet.py <folder-of-pngs> <out.jpg> [max=12] [cols=5]
Check the sheet for text near the top and bottom edges (safe zone) and animations cut off early.
Requires Pillow and ffmpeg.
"""
import pathlib, subprocess, sys, tempfile
from PIL import Image

src, out = pathlib.Path(sys.argv[1]), sys.argv[2]
n = int(sys.argv[3]) if len(sys.argv) > 3 else 12
cols = int(sys.argv[4]) if len(sys.argv) > 4 else (5 if src.is_dir() else 6)
if src.is_dir():
    files = sorted(p for p in src.iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg"))[:n]
else:
    d = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                       "-of", "csv=p=0", str(src)]).decode())
    tmp = pathlib.Path(tempfile.mkdtemp())
    files = []
    for i in range(n):
        t = d * (0.03 + 0.94 * i / max(1, n - 1))
        f = tmp / f"f{i:02d}.png"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", str(src), "-frames:v", "1", str(f)], check=True)
        files.append(f)
ims = [Image.open(f).convert("RGB") for f in files]
w = 270
h = round(ims[0].height * w / ims[0].width)
rows = -(-len(ims) // cols)
sheet = Image.new("RGB", (cols * w, rows * h), "black")
for i, im in enumerate(ims):
    sheet.paste(im.resize((w, h)), ((i % cols) * w, (i // cols) * h))
sheet.save(out, quality=85)
print(out)
