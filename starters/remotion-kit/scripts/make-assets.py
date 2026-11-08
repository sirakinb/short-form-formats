"""Generate every placeholder asset the sample compositions use, from scratch:
sample word lists, a placeholder talking-head take, a sample UI screenshot, placeholder logos
and synthesized sound effects. Nothing here is copied from a third party.

Usage: python3 scripts/make-assets.py      (run from starters/remotion-kit)
Needs Python 3 with Pillow, and ffmpeg on your PATH. Safe to re-run; it overwrites the samples.
"""
import json, math, random, shutil, struct, subprocess, sys, tempfile, wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
from words_from_script import estimate  # noqa: E402

KIT = Path(__file__).resolve().parent.parent
REPO = KIT.parent.parent
PUB = KIT / "public"
BRAND = json.loads((REPO / "brand/brand.json").read_text())
COL = BRAND["colors"]
SR = 44100
random.seed(7)

SCRIPTS = {
    # "|" marks dead air in the raw take; tools/cuts.py removes it.
    "talking-head.raw": "Most short videos lose people in two seconds. | Here is the fix. | Change the picture every one to two seconds. | "
                        "Show the real screen, not a drawing. | Keep your text inside the safe zone. | "
                        "Three rules: move fast, show the real thing, stay in the zone. | Follow for more.",
    "listicle": "Five edits that keep people watching. One: cut every pause. Two: change the picture every two seconds. "
                "Three: show the real screen. Four: one accent word per caption. Five: keep it in the safe zone. Save this for your next video.",
    "counter": "How many apps does one post take? Let's count. Editor. Captions. Thumbnails. Scheduler. Analytics. Inbox. "
               "Six apps. Now put them in one place. Six apps. One place. Zero tab switching. Follow for the setup.",
    "game-parody": "Me versus my inbox. Round one: two hundred unread. Archive. Filter. Reply. Final round: the newsletter pile. "
                   "Unsubscribe. K.O. Inbox zero. Follow for more fights.",
}


def font(size, bold=False):
    names = ["Arial Bold.ttf" if bold else "Arial.ttf", "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"]
    dirs = ["/System/Library/Fonts/Supplemental", "/Library/Fonts", "/usr/share/fonts/truetype/dejavu", "C:/Windows/Fonts"]
    for d in dirs:
        for n in names:
            p = Path(d) / n
            if p.exists():
                return ImageFont.truetype(str(p), size)
    return ImageFont.load_default(size=size)


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, k):
    a, b = hexrgb(a), hexrgb(b)
    return tuple(round(a[i] + (b[i] - a[i]) * k) for i in range(3))


# ---------- word lists ----------

def make_words():
    out = PUB / "words"
    out.mkdir(parents=True, exist_ok=True)
    for name, text in SCRIPTS.items():
        words = estimate(text)
        (out / f"{name}.json").write_text(json.dumps(words, indent=1))
        print(f"words/{name}.json  {len(words)} words, {words[-1]['e']:.1f} s")
    # The talking-head take goes through the same silence cutter you use on real footage.
    subprocess.run([sys.executable, str(REPO / "tools/cuts.py"), str(out / "talking-head.raw.json"), str(out / "talking-head.edit.json")], check=True)


# ---------- audio ----------

def write_wav(path, samples):
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, x)) * 32000)) for x in samples))


def tick(freq):
    n = int(SR * 0.05)
    return [0.7 * math.exp(-i / SR * 160) * (math.sin(2 * math.pi * freq * i / SR) + 0.25 * random.uniform(-1, 1)) for i in range(n)]


def whoosh():
    n, lp, out = int(SR * 0.45), 0.0, []
    for i in range(n):
        k = i / n
        a = 0.02 + 0.25 * math.sin(math.pi * k)  # cutoff sweeps up and back down
        lp += a * (random.uniform(-1, 1) - lp)
        out.append(2.2 * lp * math.sin(math.pi * k) ** 1.5)
    return out


def slam():
    n, ph, out = int(SR * 0.6), 0.0, []
    for i in range(n):
        t = i / SR
        ph += 2 * math.pi * (38 + 50 * math.exp(-t * 18)) / SR
        body = math.sin(ph) * math.exp(-t * 6)
        crack = random.uniform(-1, 1) * math.exp(-t * 60) * 0.6
        out.append(0.9 * math.tanh(1.6 * (body + crack)))
    return out


def hit():
    n, lp, out = int(SR * 0.3), 0.0, []
    for i in range(n):
        t = i / SR
        lp += 0.25 * (random.uniform(-1, 1) - lp)
        out.append(0.9 * math.tanh(2 * (lp * 2.5 * math.exp(-t * 25) + math.sin(2 * math.pi * 110 * t) * math.exp(-t * 14))))
    return out


def pop():
    n, ph, out = int(SR * 0.12), 0.0, []
    for i in range(n):
        t = i / SR
        ph += 2 * math.pi * (420 + 4000 * t) / SR
        out.append(0.6 * math.sin(ph) * math.exp(-t * 30))
    return out


def make_sfx():
    d = PUB / "sfx"
    for name, s in {"tick1": tick(2200), "tick2": tick(2750), "tick3": tick(3300), "whoosh": whoosh(), "slam": slam(), "hit": hit(), "pop": pop()}.items():
        write_wav(d / f"{name}.wav", s)
    print("sfx/  tick1-3, whoosh, slam, hit, pop")


def voice_track(words, dur):
    """A soft hum while each word is 'spoken' and silence in the pauses, so cuts are audible."""
    n = int(SR * dur)
    out = [0.0] * n
    for k, w in enumerate(words):
        a, b = int(w["s"] * SR), min(n, int(w["e"] * SR))
        f = 150 + 30 * (k % 4)
        for i in range(a, b):
            x = (i - a) / max(1, b - a)
            out[i] = 0.12 * math.sin(math.pi * x) * (math.sin(2 * math.pi * f * i / SR) + 0.4 * math.sin(4 * math.pi * f * i / SR))
    return out


# ---------- images and video ----------

def make_take():
    raw = json.loads((PUB / "words/talking-head.raw.json").read_text())
    dur = round(raw[-1]["e"] + 0.6, 2)
    W, H = 1080, 1920
    img = Image.new("RGB", (W, H))
    px = img.load()
    top, bot = mix(COL["card"], COL["line"], 0.6), mix(COL["bg"], COL["card"], 0.5)
    for y in range(H):
        c = tuple(round(top[i] + (bot[i] - top[i]) * y / H) for i in range(3))
        for x in range(W):
            px[x, y] = c
    d = ImageDraw.Draw(img)
    body = mix(COL["line"], COL["muted"], 0.35)
    d.ellipse([340, 520, 740, 960], fill=body)          # head
    d.rounded_rectangle([170, 1000, 910, 1920], radius=320, fill=body)  # shoulders
    d.text((W / 2, 1560), "PLACEHOLDER TAKE", font=font(64, True), fill=hexrgb(COL["ink"]), anchor="mm")
    d.text((W / 2, 1630), "replace public/video/take.mp4 with your own", font=font(36), fill=hexrgb(COL["muted"]), anchor="mm")
    tmp = Path(tempfile.mkdtemp())
    img.save(tmp / "plate.png")
    write_wav(tmp / "voice.wav", voice_track(raw, dur))
    out = PUB / "video/take.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    # Burn in the source timecode so you can see the silence cuts in the edit.
    tc = "drawtext=text='SOURCE %{pts\\:hms}':x=(w-tw)/2:y=1280:fontsize=64:fontcolor=white@0.85:box=1:boxcolor=black@0.5:boxborderw=18"
    base = ["ffmpeg", "-v", "error", "-y", "-loop", "1", "-framerate", "30", "-i", str(tmp / "plate.png"), "-i", str(tmp / "voice.wav"), "-t", str(dur)]
    enc = ["-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "128k", "-shortest", str(out)]
    if subprocess.run(base + ["-vf", tc] + enc).returncode != 0:
        print("drawtext unavailable; making the take without a timecode")
        subprocess.run(base + enc, check=True)
    # A still for the cover.
    shutil.copy(tmp / "plate.png", PUB / "video/take-cover.png")
    print(f"video/take.mp4  {dur:.1f} s placeholder take")


# Rectangles of interest on the sample screenshot, in its own pixels. Compositions use these for camera moves and marks.
SHOT_W, SHOT_H = 2160, 1350


def make_shot():
    img = Image.new("RGB", (SHOT_W, SHOT_H), hexrgb(COL["card"]))
    d = ImageDraw.Draw(img)
    ink, muted, line, acc, ok = (hexrgb(COL[k]) for k in ("ink", "muted", "line", "accent", "success"))
    panel = mix(COL["card"], COL["line"], 0.35)
    d.rectangle([0, 0, 360, SHOT_H], fill=mix(COL["bg"], COL["card"], 0.5))
    d.text((48, 44), "Your App", font=font(44, True), fill=ink)
    for i, item in enumerate(["Overview", "Videos", "Captions", "Schedule", "Settings"]):
        y = 190 + i * 90
        if i == 0:
            d.rounded_rectangle([28, y - 18, 332, y + 50], radius=14, fill=panel)
        d.text((56, y), item, font=font(34), fill=ink if i == 0 else muted)
    d.line([360, 120, SHOT_W, 120], fill=line, width=2)
    d.text((420, 40), "Overview", font=font(48, True), fill=ink)
    d.text((SHOT_W - 60, 52), "Sample screenshot - replace with your real UI", font=font(28), fill=muted, anchor="ra")
    cards = [((420, 180, 980, 420), "Views", "48.2K"), ((1020, 180, 1580, 420), "Watched past 2 s", "71%"), ((1620, 180, 2120, 420), "New follows", "+1,204")]
    for (x0, y0, x1, y1), label, value in cards:
        d.rounded_rectangle([x0, y0, x1, y1], radius=24, fill=panel, outline=line, width=2)
        d.text((x0 + 36, y0 + 36), label, font=font(32), fill=muted)
        d.text((x0 + 36, y0 + 100), value, font=font(96, True), fill=acc if label.startswith("Watched") else ink)
    d.rounded_rectangle([420, 470, 1580, 1000], radius=24, fill=panel, outline=line, width=2)
    d.text((456, 500), "Retention", font=font(32), fill=muted)
    pts = [(470 + i * 55, 600 + 330 * (1 - math.exp(-i / 4)) + 18 * math.sin(i)) for i in range(20)]
    d.line(pts, fill=acc, width=8, joint="curve")
    d.rounded_rectangle([1620, 470, 2120, 1000], radius=24, fill=panel, outline=line, width=2)
    d.text((1656, 500), "Recent videos", font=font(32), fill=muted)
    for i in range(5):
        y = 580 + i * 80
        d.rounded_rectangle([1656, y, 1736, y + 56], radius=10, fill=line)
        d.text((1760, y + 8), f"Video {i + 1}", font=font(32), fill=ink)
        d.text((2090, y + 8), f"{[92, 81, 77, 64, 58][i]}%", font=font(32), fill=ok, anchor="ra")
    d.rounded_rectangle([420, 1050, 2120, 1290], radius=24, fill=panel, outline=line, width=2)
    d.text((456, 1080), "Tip", font=font(32), fill=muted)
    d.text((456, 1140), "Change the picture every 1-2 seconds.", font=font(64, True), fill=ink)
    out = PUB / "shots/sample-ui.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    print("shots/sample-ui.png  2160x1350")


LOGOS = [("editor", "E", "#3b82f6"), ("captions", "C", "#f59e0b"), ("thumbnails", "T", "#ef4444"),
         ("scheduler", "S", "#10b981"), ("analytics", "A", "#06b6d4"), ("inbox", "I", "#ec4899")]


def make_logos():
    d = PUB / "logos"
    d.mkdir(parents=True, exist_ok=True)
    for name, letter, color in LOGOS:
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120"><rect width="120" height="120" rx="28" fill="{color}"/>'
               f'<text x="60" y="80" text-anchor="middle" font-family="Helvetica, Arial, sans-serif" font-weight="700" font-size="60" fill="#ffffff">{letter}</text></svg>')
        (d / f"{name}.svg").write_text(svg)
    print("logos/  " + ", ".join(n for n, _, _ in LOGOS) + " (placeholders: use real logos)")


if __name__ == "__main__":
    make_words()
    make_sfx()
    make_take()
    make_shot()
    make_logos()
