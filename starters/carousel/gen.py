"""Carousel slides for TikTok and Instagram: a JSON data file in, 1080x1350 PNG slides out.

    python3 gen.py data/example-evergreen.json            # writes out/example-evergreen/slide-01.png ...
    python3 gen.py data/a.json data/b.json --brand path/to/brand.json

Each run writes slide-NN.png, contact.jpg (a contact sheet for review) and caption.txt (if the data
file has a caption) to out/<data file name>/.

Slide types: hook, features, diagram, step, list, cta. Themes: brand (built from brand.json) and the
lab themes in THEMES. See README.md for the data file schema.

Requirements: Python 3 with Pillow, and Google Chrome (set CHROME to point at another binary).
"""
import argparse, html, json, os, re, shutil, subprocess, sys
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
DEFAULT_BRAND = HERE.parent.parent / "brand" / "brand.json"
MAC_CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
W, H = 1080, 1350

# Lab themes borrow the launching lab's palette and type, so a news carousel looks like the launch it covers.
# Keys: bg, card, ink, mut (muted text), acc (accent), hl / hlink (title highlight and its text),
# head / body (CSS font stacks), line (borders), dark (prompt box and CTA card).
THEMES = {
    "anthropic": dict(bg="#f3eee6", card="#fbf8f3", ink="#1f1e1d", mut="#5f5a52", acc="#d97757", hl="#d97757", hlink="#1f1e1d",
                      head="'Source Serif 4', Georgia, serif", body="'Inter', system-ui, sans-serif", line="#e3dccf", dark="#1f1e1d"),
    "openai": dict(bg="#ffffff", card="#f7f7f8", ink="#0d0d0d", mut="#5d5d5d", acc="#0d0d0d", hl="#0d0d0d", hlink="#ffffff",
                   head="'Inter', system-ui, sans-serif", body="'Inter', system-ui, sans-serif", line="#e5e5e5", dark="#0d0d0d"),
    "google": dict(bg="#ffffff", card="#f6f8fc", ink="#1f1f1f", mut="#5e5e5e", acc="#1a73e8", hl="#d3e3fd", hlink="#0b57d0",
                   head="'Inter', system-ui, sans-serif", body="'Inter', system-ui, sans-serif", line="#e3e3e3", dark="#1f1f1f"),
    "meta": dict(bg="#f1f4fa", card="#ffffff", ink="#1c2b33", mut="#5d6c7b", acc="#0866ff", hl="#0866ff", hlink="#ffffff",
                 head="'Inter', system-ui, sans-serif", body="'Inter', system-ui, sans-serif", line="#dde3ec", dark="#1c2b33"),
    "xai": dict(bg="#000000", card="#0f0f0f", ink="#ffffff", mut="#9a9a9a", acc="#ffffff", hl="#ffffff", hlink="#000000",
                head="'Inter', system-ui, sans-serif", body="'JetBrains Mono', ui-monospace, monospace", line="#262626", dark="#141414"),
    "opensource": dict(bg="#0d1117", card="#161b22", ink="#e6edf3", mut="#8b949e", acc="#3fb950", hl="#3fb950", hlink="#0d1117",
                       head="'Inter', system-ui, sans-serif", body="'JetBrains Mono', ui-monospace, monospace", line="#30363d", dark="#010409"),
}
FONTS = ("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Source+Serif+4:ital,wght@0,600;0,700;1,600"
         "&family=JetBrains+Mono:wght@500;700&display=swap")


def brand_theme(b):
    """The brand theme: your colors and fonts from brand.json."""
    c, f = b.get("colors", {}), b.get("fonts", {})
    stack = lambda name, fallback: f"'{name}', {fallback}" if name else fallback
    return dict(bg=c.get("bg", "#000000"), card=c.get("card", "#0a0a0a"), ink=c.get("ink", "#fafafa"), mut=c.get("muted", "#999999"),
                acc=c.get("accent", "#a855f7"), hl=c.get("accent", "#a855f7"), hlink=c.get("bg", "#000000"),
                head=stack(f.get("head"), "'Inter', system-ui, sans-serif"), body=stack(f.get("body"), "'Inter', system-ui, sans-serif"),
                line=c.get("line", "#262626"), dark=c.get("card", "#0a0a0a"), fonts_url=f.get("googleFontsUrl", ""))


# ---------- helpers ----------

class Ctx:
    """Everything one render needs: data, theme, brand, paths."""

    def __init__(self, data, data_path, brand, brand_path, outdir):
        self.d, self.data_dir, self.b, self.brand_path, self.out = data, data_path.parent, brand, brand_path, outdir
        name = data.get("theme", "brand")
        if name == "brand":
            self.t = brand_theme(brand)
        elif name in THEMES:
            self.t = THEMES[name]
        else:
            raise SystemExit(f"unknown theme '{name}'. Use 'brand' or one of: {', '.join(THEMES)}")
        self.platforms = data.get("platforms") or []

    def fill(self, s):
        """Swap {name}, {handle}, {url}, {cta}, {cta_sub} for brand.json values."""
        b = self.b
        vals = {"name": b.get("name", ""), "handle": b.get("handle", ""), "url": b.get("url", ""),
                "cta": b.get("cta", {}).get("default", ""), "cta_sub": b.get("cta", {}).get("sub", "")}
        return re.sub(r"\{(name|handle|url|cta|cta_sub)\}", lambda m: vals[m.group(1)], str(s))

    def e(self, s):
        return html.escape(self.fill(s))

    def find(self, name):
        """Look for a file as given, next to the data file, in this folder, then in assets/."""
        if not name:
            return None
        for p in (Path(name), self.data_dir / name, HERE / name, HERE / "assets" / name):
            if p.exists():
                return p.resolve()
        print(f"  warning: file not found: {name}", file=sys.stderr)
        return None

    def img(self, name):
        """URI for an image. SVGs drawn in currentColor get recolored to the theme ink so they show on dark themes."""
        p = self.find(name)
        if not p:
            return ""
        if p.suffix.lower() == ".svg":
            src = p.read_text()
            if "currentColor" in src:
                tinted = self.out / f"tint-{p.name}"
                tinted.write_text(src.replace("currentColor", self.t["ink"]))
                return tinted.as_uri()
        return p.as_uri()

    def brand_logo(self):
        logo = self.b.get("logo", "")
        if not logo:
            return ""
        for base in (self.brand_path.parent.parent, self.brand_path.parent, Path.cwd()):
            p = base / logo
            if p.exists():
                return p.resolve().as_uri()
        print(f"  warning: brand logo not found: {logo}", file=sys.stderr)
        return ""


def crop_shot(src, frac, out):
    """Crop a real screenshot by fractions [x, y, w, h] so the slide shows only the part that proves the step."""
    im = Image.open(src)
    if frac:
        x, y, w, h = frac
        im = im.crop((int(x * im.width), int(y * im.height), int((x + w) * im.width), int((y + h) * im.height)))
    im.convert("RGB").save(out, quality=92)
    return out.as_uri()


def icons_grid(c, size, cols=4):
    if not c.platforms:
        return ""
    cells = "".join(f'<img src="{c.img(p + ".png")}" style="width:{size}px;height:{size}px;border-radius:{size*.22}px">' for p in c.platforms)
    cols = min(cols, len(c.platforms))
    return f'<div class="grid" style="display:grid;grid-template-columns:repeat({cols},{size}px);gap:{size*.14}px">{cells}</div>'


def frame(c, i, n, inner, foot=""):
    lab = c.d.get("lab_logo", "")
    logo = c.brand_logo()
    parts = []
    if lab:
        parts.append(f'<img class="lab" src="{c.img(lab)}">')
    if lab and logo:
        parts.append("<span>×</span>")
    if logo:
        parts.append(f'<img class="ps" src="{logo}">')
    if not lab:
        parts.append(f'<b class="bname">{c.e(c.b.get("name", ""))}</b>')
    return f'''<div class="slide">
<header><div class="pair">{"".join(parts)}</div><div class="count">{i} / {n}</div></header>
<section>{inner}</section>
<footer><span>{c.e(foot)}</span><span class="arrow">{"→" if i < n else ""}</span></footer></div>'''


def label(c, text):
    return f'<div class="kicker">{c.e(text)}</div>' if text else ""


def title(c, text):
    return f'<h2><span class="hl">{c.e(text)}</span></h2>'


def sub(c, s):
    return f'<p class="sub">{c.e(s["sub"])}</p>' if s.get("sub") else '<div class="gap"></div>'


def slide_html(c, s, i, n):
    k = s.get("type")
    d, url = c.d, c.b.get("url", "")
    if k == "hook":
        prod = f' <em>{c.e(s["product"])}</em>' if s.get("product") else ""
        chip = (f'<div class="chip">{"<b>NEW</b> " if s.get("new") else ""}{c.e(s.get("chip", ""))}</div>') if s.get("chip") or s.get("new") else ""
        icon = f'<div class="halo"><img src="{c.img(s["icon"])}"></div>' if s.get("icon") else ""
        grid = ""
        if c.platforms:
            tiny = f'<div class="tiny">{c.e(d["platforms_label"])}</div>' if d.get("platforms_label") else ""
            grid = f'<div class="plat">{tiny}{icons_grid(c, 78)}</div>'
        solo = "" if s.get("icon") else " solo"
        row = f'<div class="hookrow{solo}">{icon}{grid}</div>' if s.get("icon") or grid else ""
        sub_ = f'<p class="sub">{c.e(s["sub"])}</p>' if s.get("sub") else ""
        return frame(c, i, n, f'{chip}<h1>{c.e(s["lead"])}{prod}</h1>{sub_}{row}', s.get("foot", "Swipe"))
    if k == "features":
        rows = "".join(f'<div class="row"><b>{c.e(a)}</b><span>{c.e(b)}</span></div>' for a, b in s["items"])
        return frame(c, i, n, f'{label(c, s.get("kicker"))}{title(c, s["title"])}{sub(c, s)}<div class="card list">{rows}</div>', s.get("foot", ""))
    if k == "diagram":
        left = s.get("icon", d.get("product_icon", ""))
        logo = c.brand_logo()
        pair = []
        if left:
            pair.append(f'<img src="{c.img(left)}">')
        if left and logo:
            pair.append("<i></i>")
        if logo:
            pair.append(f'<img class="ps" src="{logo}">')
        below = ""
        if s.get("nodes"):
            below = '<div class="nodes">' + "".join(f'<span>{c.e(x)}</span>' for x in s["nodes"]) + "</div>"
        elif c.platforms:
            below = icons_grid(c, 118)
        drop = '<div class="drop"></div>' if below else ""
        inner = f'''{label(c, s.get("kicker"))}{title(c, s["title"])}{sub(c, s)}
<div class="card diagram"><div class="pairbig">{"".join(pair)}</div>{drop}{below}</div>'''
        return frame(c, i, n, inner, s.get("foot", url))
    if k == "step":
        img = ""
        if s.get("shot"):
            src = c.find(s["shot"])
            if src:
                img = f'<div class="shot"><img src="{crop_shot(src, s.get("crop"), c.out / f"shot-{i:02d}.jpg")}"></div>'
        prompt = f'<div class="prompt">{c.e(s["prompt"])}</div>' if s.get("prompt") else ""
        return frame(c, i, n, f'{label(c, s.get("kicker"))}{title(c, s["title"])}{sub(c, s)}{prompt}{img}', s.get("foot", ""))
    if k == "list":
        rows = "".join(f'<div class="card item"><b>{c.e(a)}</b><span>{c.e(b)}</span></div>' for a, b in s["items"])
        return frame(c, i, n, f'{label(c, s.get("kicker"))}{title(c, s["title"])}{sub(c, s)}<div class="items">{rows}</div>', s.get("foot", ""))
    if k == "cta":
        cta = c.b.get("cta", {})
        icon = s.get("icon", d.get("product_icon", ""))
        logo = c.brand_logo()
        pair = []
        if icon:
            pair.append(f'<img src="{c.img(icon)}">')
        if icon and logo:
            pair.append("<span>×</span>")
        if logo:
            pair.append(f'<img class="ps" src="{logo}">')
        ask_sub = s.get("ask_sub", cta.get("sub", ""))
        inner = f'''{label(c, s.get("kicker"))}{title(c, s["title"])}{sub(c, s)}
<div class="ctacard"><div class="pairbig small">{"".join(pair)}</div>
<div class="big">{c.e(s.get("ask", cta.get("default", "Link in bio")))}</div>{f'<div class="small2">{c.e(ask_sub)}</div>' if ask_sub else ""}</div>
<div class="ctafoot">{icons_grid(c, 46, 8) or "<span></span>"}<span>{c.e(url)}</span></div>'''
        return frame(c, i, n, inner, "")
    raise SystemExit(f"slide {i}: unknown slide type '{k}'. Use hook, features, diagram, step, list or cta.")


def css(t):
    extra = f'@import url("{t["fonts_url"]}");' if t.get("fonts_url") else ""
    return f'''@import url("{FONTS}");{extra}
*{{box-sizing:border-box;margin:0}} body{{width:{W}px;height:{H}px;overflow:hidden;background:{t["bg"]}}}
.slide{{width:{W}px;height:{H}px;background:{t["bg"]};color:{t["ink"]};font-family:{t["body"]};padding:64px 72px;display:flex;flex-direction:column}}
header{{display:flex;justify-content:space-between;align-items:center}} .pair{{display:flex;align-items:center;gap:14px;color:{t["mut"]};font-size:26px}}
.pair img{{height:54px;width:auto;max-width:220px;border-radius:14px;object-fit:contain}}
.pair .lab{{width:54px;background:{t["card"]};padding:8px;border:1px solid {t["line"]}}}
.bname{{color:{t["ink"]};font-family:{t["head"]};font-size:28px;font-weight:700;margin-left:4px}}
.count{{color:{t["mut"]};font-size:24px;letter-spacing:2px}}
section{{flex:1;display:flex;flex-direction:column;justify-content:flex-start;padding-top:80px;min-height:0}}
footer{{display:flex;justify-content:space-between;align-items:flex-end;color:{t["mut"]};font-size:20px;letter-spacing:3px;text-transform:uppercase}} .arrow{{font-size:44px;line-height:1;color:{t["ink"]}}}
.chip{{align-self:flex-start;font-size:24px;color:{t["mut"]};margin-bottom:30px}} .chip b{{background:{t["ink"]};color:{t["bg"]};border-radius:999px;padding:6px 16px;margin-right:12px;font-size:20px;letter-spacing:2px}}
h1{{font-family:{t["head"]};font-weight:700;font-size:112px;line-height:1.0;letter-spacing:-3px}} h1 em{{color:{t["acc"]};font-style:italic;font-weight:600}}
h2{{font-family:{t["head"]};font-weight:700;font-size:76px;line-height:1.14;letter-spacing:-1.5px}}
.hl{{background:{t["hl"]};color:{t["hlink"]};padding:2px 18px;box-decoration-break:clone;-webkit-box-decoration-break:clone}}
.kicker{{color:{t["acc"]};font-size:24px;font-weight:700;letter-spacing:4px;text-transform:uppercase;margin-bottom:20px}}
.sub{{font-size:38px;line-height:1.3;color:{t["ink"]};margin:28px 0 40px;font-weight:500;max-width:900px}} .gap{{height:40px}}
.hookrow{{display:flex;align-items:center;justify-content:space-between;margin-top:auto;margin-bottom:56px}}
.hookrow.solo{{justify-content:flex-start}} .hookrow.solo .tiny{{text-align:left}}
.halo{{width:330px;height:330px;border-radius:50%;background:{t["line"]};display:flex;align-items:center;justify-content:center}} .halo img{{width:250px;height:250px;border-radius:52px}}
.plat .tiny{{font-size:20px;letter-spacing:3px;text-transform:uppercase;color:{t["mut"]};margin-bottom:16px;text-align:right}}
.card{{background:{t["card"]};border:1px solid {t["line"]};border-radius:24px}}
.list{{padding:24px 40px}} .row{{display:flex;flex-direction:column;padding:22px 0;border-bottom:1px solid {t["line"]}}} .row:last-child{{border:0}}
.row b{{font-family:{t["head"]};font-size:42px}} .row span,.item span{{color:{t["mut"]};font-size:28px;margin-top:6px}}
.diagram{{padding:44px;display:flex;flex-direction:column;align-items:center}} .pairbig{{display:flex;align-items:center;gap:30px}}
.pairbig img{{height:150px;width:auto;min-width:150px;max-width:340px;border-radius:34px;object-fit:contain;background:{t["card"]}}} .pairbig i{{width:110px;height:3px;background:{t["mut"]}}}
.pairbig.small img{{height:110px;min-width:110px;border-radius:26px}} .pairbig span{{color:#fff;font-size:40px}}
.drop{{width:3px;height:50px;background:{t["mut"]};margin:18px 0}}
.nodes{{display:flex;flex-wrap:wrap;justify-content:center;gap:16px}} .nodes span{{border:1px solid {t["line"]};background:{t["bg"]};border-radius:999px;padding:16px 28px;font-size:30px;font-weight:600}}
.prompt{{background:{t["dark"]};color:#fff;border:1px solid {t["line"]};border-radius:20px;padding:28px 34px;font-size:32px;line-height:1.35;margin-bottom:36px;white-space:pre-line}}
.shot{{border-radius:22px;overflow:hidden;border:1px solid {t["line"]};background:#0b0b0f;min-height:0;flex-shrink:1}} .shot img{{width:100%;height:100%;object-fit:cover;object-position:top;display:block}}
.items{{display:flex;flex-direction:column;gap:22px}} .item{{padding:30px 38px;display:flex;flex-direction:column}} .item b{{font-family:{t["head"]};font-size:44px}}
.ctacard{{background:{t["dark"]};color:#fff;border:1px solid {t["line"]};border-radius:28px;padding:56px;display:flex;flex-direction:column;align-items:center;gap:22px;text-align:center}}
.ctacard .big{{font-family:{t["head"]};font-size:84px;line-height:1.05;font-weight:700}} .small2{{font-size:30px;opacity:.8}}
.ctafoot{{display:flex;justify-content:space-between;align-items:center;margin-top:46px;color:{t["mut"]};font-size:24px;letter-spacing:3px;text-transform:uppercase}}'''


def check_banned(c):
    """Warn about phrases brand.json says never to use."""
    text = json.dumps(c.d, ensure_ascii=False).lower()
    for phrase in c.b.get("banned", []):
        if phrase.lower() in text:
            print(f"  warning: banned phrase in data file: '{phrase}'", file=sys.stderr)


def chrome_path():
    env = os.environ.get("CHROME")
    if env:
        if not Path(env).exists():
            raise SystemExit(f"CHROME is set but not found: {env}")
        return env
    for p in (MAC_CHROME, shutil.which("google-chrome"), shutil.which("chromium"), shutil.which("chromium-browser")):
        if p and Path(p).exists():
            return p
    raise SystemExit("Chrome not found. Set CHROME=/path/to/chrome")


def render(data_path, brand_path):
    data_path = Path(data_path).resolve()
    brand = json.loads(brand_path.read_text())
    d = json.loads(data_path.read_text())
    slug = data_path.stem
    out = HERE / "out" / slug
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("slide-*.png"):
        old.unlink()
    c = Ctx(d, data_path, brand, brand_path, out)
    check_banned(c)
    chrome = chrome_path()
    n = len(d["slides"])
    pngs = []
    for i, s in enumerate(d["slides"], 1):
        page = out / f"slide-{i:02d}.html"
        page.write_text(f'<!doctype html><html><head><meta charset="utf-8"><style>{css(c.t)}</style></head><body>{slide_html(c, s, i, n)}</body></html>')
        png = out / f"slide-{i:02d}.png"
        subprocess.run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
                        "--virtual-time-budget=4000", f"--window-size={W},{H}", f"--screenshot={png}", page.as_uri()],
                       capture_output=True, check=True)
        pngs.append(png)
    # contact sheet for review
    tw, th, cols = 270, 337, 5
    ims = [Image.open(p).convert("RGB").resize((tw, th)) for p in pngs]
    sheet = Image.new("RGB", (cols * tw + (cols + 1) * 8, ((len(ims) + cols - 1) // cols) * (th + 8) + 8), "#808080")
    for j, im in enumerate(ims):
        sheet.paste(im, (8 + (j % cols) * (tw + 8), 8 + (j // cols) * (th + 8)))
    sheet.save(out / "contact.jpg", quality=85)
    if d.get("caption"):
        (out / "caption.txt").write_text(c.fill(d["caption"]).strip() + "\n")
    for p in list(out.glob("*.html")) + list(out.glob("tint-*")):
        p.unlink()
    print(f"{slug}: {n} slides -> {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Render carousel slides from JSON data files.")
    ap.add_argument("data", nargs="+", help="data/<name>.json")
    ap.add_argument("--brand", default=str(DEFAULT_BRAND), help="path to brand.json (default: ../../brand/brand.json)")
    a = ap.parse_args()
    bp = Path(a.brand).resolve()
    if not bp.exists():
        raise SystemExit(f"brand file not found: {bp}")
    for p in a.data:
        render(p, bp)
