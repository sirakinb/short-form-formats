"""Generate a faceless 9:16 explainer as a HyperFrames project, keyed to the voiceover's word times.

    python3 gen.py                      # reads script.json, words.json and the repo's brand/brand.json
    python3 gen.py --look paper         # same video in the cream-paper look (see looks.md)
    python3 gen.py --script my.json --brand path/to/brand.json --out hf

Writes hf/index.html, hf/compositions/*.html, hf/assets/ (fonts, logo, voiceover, sound pack) and
hf/assets/sfx-mix.wav: one sound track whose cues are placed by the same code that places the motion.

How a video is built: the script plays word by word at the top, one slam word per line lands huge in the
accent colour, and under each line sits an animated card (see CARDS at the bottom). Every visible change is
keyed to a spoken word, so re-run this file after any change to the script, the voiceover or the timings.
Needs Python 3.9+ and numpy.
"""
import argparse
import difflib
import json
import math
import re
import shutil
import wave
from pathlib import Path

import numpy as np

import sfx as sfxpack

HERE = Path(__file__).resolve().parent
W, H = 1080, 1920
GSAP = "https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"
HF_VERSION = "0.9.13"
# Families HyperFrames resolves by name without a font file (references/format.md in the hyperframes skill).
BUNDLED = {"Inter", "Montserrat", "Outfit", "Nunito", "Oswald", "League Gothic", "Archivo Black", "Space Mono",
           "IBM Plex Mono", "JetBrains Mono", "EB Garamond", "Playfair Display", "Source Code Pro", "Noto Sans JP",
           "Roboto", "Open Sans", "Lato", "Poppins"}
SFX = []  # (absolute seconds, sound name, gain): every motion event appends its cue here


def r(x):
    return round(x, 3)


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def seeded(n, seed):
    """Deterministic pseudo-random numbers in [0, 1). Renders must never use Math.random()."""
    out, x = [], seed
    for _ in range(n):
        x = (x * 9301 + 49297) % 233280
        out.append(x / 233280)
    return out


# ---------------------------------------------------------------- colour helpers
def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgba(h, a):
    return "rgba({},{},{},{})".format(*hex_rgb(h), a)


def mix(h1, h2, t):
    a, b = hex_rgb(h1), hex_rgb(h2)
    return "#" + "".join(f"{round(a[i] + (b[i] - a[i]) * t):02x}" for i in range(3))


def lum(h):
    def ch(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    rr, gg, bb = (ch(c) for c in hex_rgb(h))
    return 0.2126 * rr + 0.7152 * gg + 0.0722 * bb


def on(h):
    """Black or white, whichever reads better on colour h."""
    L = lum(h)
    return "#000000" if (L + 0.05) / 0.05 >= 1.05 / (L + 0.05) else "#ffffff"


# ---------------------------------------------------------------- looks
def ground(bg, card, line, ink, muted, accent, success, danger, sub):
    return dict(bg=bg, card=card, line=line, ink=ink, muted=muted, accent=accent, on=on(accent),
                soft=rgba(accent, 0.14), success=success, danger=danger, sub=sub, track=sub)


def make_look(name, brand):
    """A look is everything visual that is not the script: fonts, grounds, motion style, backdrop.
    'dark' comes from brand.json. 'paper' shows how to match a reference: change the look, keep the code."""
    c, f = brand["colors"], brand["fonts"]
    if name == "dark":
        dark = ground(c["bg"], c["card"], c["line"], c["ink"], c["muted"], c["accent"], c["success"], c["danger"],
                      rgba(c["ink"], 0.05))
        light = ground(c["ink"], "#ffffff", rgba(c["bg"], 0.10), c["card"], rgba(c["card"], 0.6), c["accentStrong"],
                       c["success"], c["danger"], rgba(c["bg"], 0.04))
        return dict(name="dark", head=f["head"], body=f["body"], mono=f["mono"], grounds=[dark, light],
                    entrance="rise", slam="big", backdrop="pixels", transition="dissolve", clay=False,
                    headline_weight=600, slam_weight=800, radius=28, accent_soft=c["accentSoft"])
    if name == "paper":
        # Cream paper with a faint grid and drifting window light, clay-coloured accent with a soft 3D "clay" fill,
        # serif captions with highlight boxes wiped behind the key words, cards that fly in and land.
        p = ground("#ede8df", "#fbfaf7", "#ddd6ca", "#141416", "rgba(20,20,22,.55)", "#c2552d", "#4f8a5b", "#b83a2e",
                   "#f1ece3")
        p["track"] = "#ece6db"
        p["on"] = "#ffffff"  # the reference sets white type on its clay boxes
        return dict(name="paper", head="EB Garamond", body="Inter", mono="JetBrains Mono", grounds=[p],
                    entrance="land", slam="box", backdrop="paper", transition="drift", clay=True,
                    headline_weight=600, slam_weight=700, radius=28, accent_soft="#f0c3a6")
    raise SystemExit(f"Unknown look '{name}'. Use dark or paper (see looks.md).")


def fill(g, look, strong=True):
    """CSS for an accent surface (buttons, bars, tick boxes): flat in the dark look, clay in the paper look."""
    a = g["accent"] if strong else mix(g["accent"], "#ffffff", 0.45)
    if not look["clay"]:
        return f"background:{a};"
    return (f"background:linear-gradient(180deg,{mix(a, '#ffffff', 0.3)} 0%,{a} 45%,{mix(a, '#000000', 0.12)} 100%);"
            f"box-shadow:0 8px 0 {mix(a, '#000000', 0.38)}, 0 20px 34px rgba(60,30,10,.22), inset 0 3px 0 rgba(255,255,255,.45), "
            f"inset 0 -8px 14px rgba(0,0,0,.14);")


# ---------------------------------------------------------------- fonts
def font_css(look, brand_dir, fonts_out):
    """@font-face for each family that has a file; bundled families resolve by name; anything else falls back."""
    dirs = [brand_dir / "fonts", HERE / "fonts"]
    css, used = [], {}
    for role in ("head", "body", "mono"):
        fam = look[role]
        if fam in used:
            continue
        key = norm(fam)
        hit = next((p for d in dirs if d.is_dir() for p in sorted(d.iterdir())
                    if p.suffix.lower() in (".woff2", ".woff", ".ttf", ".otf") and norm(p.stem) == key), None)
        if hit:
            fonts_out.mkdir(parents=True, exist_ok=True)
            shutil.copy(hit, fonts_out / hit.name)
            fmt = {".woff2": "woff2", ".woff": "woff", ".ttf": "truetype", ".otf": "opentype"}[hit.suffix.lower()]
            css.append(f"@font-face {{ font-family:'{fam}'; src:url('assets/fonts/{hit.name}') format('{fmt}'); font-weight:100 900; }}")
            used[fam] = fam
        elif fam in BUNDLED:
            used[fam] = fam
        else:
            fb = "JetBrains Mono" if role == "mono" else "Inter"
            print(f"note: no font file for '{fam}' (put {fam.replace(' ', '')}.woff2 in brand/fonts/); using {fb}")
            used[fam] = fb
            look[role] = fb
    return "\n".join(css)


# ---------------------------------------------------------------- words
def load_words(path):
    """Whisper word times, with its usual splits glued back so they match the script's own tokens."""
    out = []
    for w in json.load(open(path)):
        m = re.match(r"^\s*(\d+)(am|pm)(\W*)$", w["w"], re.I)
        if m:  # "7pm" is one whisper word; a script that says "7 PM" has two tokens
            out.append({"w": m.group(1), "s": w["s"], "e": w["s"]})
            out.append({"w": m.group(2) + m.group(3), "s": w["s"], "e": w["e"]})
            continue
        if out and w["w"].startswith("-"):  # "step-by-step" arrives as "step" "-by" "-step"
            out[-1]["w"] += w["w"]
            out[-1]["e"] = w["e"]
        else:
            out.append(dict(w))
    return out


def align(lines, heard):
    """Attach whisper times to the script's tokens with a diff, so a misheard, merged ("Hookpoint") or split
    ("Chat" "GPT") word still lands: equal runs map 1:1, changed runs share their time span in order."""
    mine = [w for ln in lines for w in ln["text"].split()]
    heard = [w for w in heard if norm(w["w"])]
    times = [None] * len(mine)
    sm = difflib.SequenceMatcher(a=[norm(x) for x in mine], b=[norm(x["w"]) for x in heard], autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            for k in range(i2 - i1):
                times[i1 + k] = (heard[j1 + k]["s"], heard[j1 + k]["e"])
        elif op == "replace":
            a, b, n = heard[j1]["s"], heard[j2 - 1]["e"], i2 - i1
            for k in range(n):
                times[i1 + k] = (a + (b - a) * k / n, a + (b - a) * (k + 1) / n)
    for k in range(len(times)):  # words the speaker skipped borrow the previous word's end
        if times[k] is None:
            p = times[k - 1][1] if k else 0.0
            times[k] = (p, p)
    out, k = [], 0
    for ln in lines:
        row = []
        for w in ln["text"].split():
            row.append({"w": w, "s": r(times[k][0]), "e": r(times[k][1])})
            k += 1
        out.append(row)
    return out


# ---------------------------------------------------------------- icons
ICONS = {
    "check": '<path d="M5 12.5l4.5 4.5L19 7"/>',
    "doc": '<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4M9 12h6M9 16h6"/>',
    "play": '<path d="M7 4l13 8-13 8z"/>',
}
CURSOR = ('<svg width="60" height="60" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 2l15 9-6.5 1.6L9 19z" '
          'fill="#ffffff" stroke="#000000" stroke-width="1.4" stroke-linejoin="round"/></svg>')


def icon(name, size, color, sw=2.0):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{sw}" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>')


ODO_JS = """function odo(id, v, n){ v = Math.round(v * 1000) / 1000;
  for(let k=0;k<n;k++){ const el=document.getElementById(id+'-c'+k); if(!el) continue;
    const p=Math.pow(10,k); let pos; if(k===0){ pos=v%10; } else { const base=Math.floor(v/p)%10; const rem=(v%p)/p; pos=base+Math.max(0,(rem-0.9)/0.1); }
    el.style.transform='translateY('+(-pos*1.2)+'em)'; el.parentNode.style.width=(k===0||v>=p)?'.62em':'0'; } }"""


def odo_html(oid, n):
    cols = [f'<span class="oc"><span class="os" data-layout-ignore id="{oid}-c{k}">' + "<br>".join(str(d % 10) for d in range(11)) + "</span></span>"
            for k in range(n - 1, -1, -1)]
    return f'<span class="odo" id="{oid}">{"".join(cols)}</span>'


# ---------------------------------------------------------------- scene
class Scene:
    def __init__(self, ctx, idx, lines, s0, s1):
        self.ctx, self.idx, self.lines = ctx, idx, lines
        self.id = f"s{idx + 1}"
        self.first, self.last = lines[0], lines[-1]
        self.s0, self.s1, self.dur = s0, s1, r(s1 - s0)
        look = ctx["look"]
        self.look = look
        self.g = look["grounds"][idx % len(look["grounds"])]
        self.html, self.js, self.init, self.css = [], [], [], []
        self.nb = 0
        self.uses_odo = False

    # --- time
    def t(self, line, i):
        return r(self.ctx["LW"][line][i]["s"] - self.s0)

    def find(self, line, word, nth=1):
        """Scene-relative time of a spoken word in a line (punctuation and case ignored)."""
        n = 0
        for i, w in enumerate(self.ctx["LW"][line]):
            if norm(w["w"]) == norm(word):
                n += 1
                if n == nth:
                    return self.t(line, i)
        words = " ".join(w["w"] for w in self.ctx["LW"][line])
        raise SystemExit(f'line {line + 1}: "{word}" is not in "{words}". Use a word from the line\'s text.')

    def window(self, line):
        """[start, end) of a line inside this scene: from just before its first word to just before the next line."""
        LW = self.ctx["LW"]
        a = 0.0 if line == self.first else r(LW[line][0]["s"] - self.s0 - 0.12)
        b = self.dur if line == self.last else r(LW[line + 1][0]["s"] - self.s0 - 0.12)
        return a, b

    def at(self, line, word, default):
        return self.find(line, word) if word else r(default)

    def cue(self, t, name, gain=1.0):
        SFX.append((r(self.s0 + t), name, gain))

    def tw(self, s):
        self.js.append(s)

    # --- backdrop for the dark look: its own ground, a soft glow and a drifting pixel field
    def backdrop(self):
        g, sid = self.g, self.id
        self.css.append(f"#root {{ background:{g['bg']}; }}" if self.look["backdrop"] == "pixels" else "#root { background:transparent; }")
        if self.look["backdrop"] != "pixels":
            return
        dark = lum(g["bg"]) < 0.3
        if dark:
            self.html.append(f'<div style="position:absolute;inset:0;background:radial-gradient(ellipse 90% 55% at 50% 100%, '
                             f'{rgba(g["accent"], .30)}, {rgba(g["accent"], 0)} 70%)"></div>')
        rnd = seeded(240, self.idx * 131 + 7)
        pix = []
        for i in range(60):
            x, y, s, o = rnd[i * 4:i * 4 + 4]
            size = 6 + int(s * 12)
            top = int(900 + y * 1100) if dark else int(y * H)
            op = (0.12 + o * 0.5) if dark else (0.05 + o * 0.12)
            pix.append(f'<i style="position:absolute;left:{int(x * W)}px;top:{top}px;width:{size}px;height:{size}px;'
                       f'background:{g["accent"]};opacity:{op:.2f}"></i>')
        self.html.append(f'<div id="{sid}-pix" data-layout-ignore style="position:absolute;inset:-80px 0 0 0">{"".join(pix)}</div>')
        self.tw(f'tl.fromTo("#{sid}-pix", {{y:0}}, {{y:-70, duration:{self.dur}, ease:"none"}}, 0);')

    def transition_in(self, prev):
        if self.idx == 0:
            return
        self.cue(0.0, "whoosh", 0.3)
        if self.look["transition"] == "dissolve":  # pixel dissolve from the previous scene's ground
            sid, col, cs = self.id, prev.g["bg"], 90
            rnd = seeded(12 * 22, self.idx * 71 + 3)
            cells = "".join(f'<i style="position:absolute;left:{c * cs}px;top:{row * cs}px;width:{cs}px;height:{cs}px;background:{col}"></i>'
                            for row in range(22) for c in range(12))
            self.html.append(f'<div id="{sid}-dz" data-layout-ignore style="position:absolute;inset:0;z-index:50">{cells}</div>')
            self.tw(f'const {sid}D=[{",".join(f"{v * 0.42:.3f}" for v in rnd)}]; '
                    f'document.querySelectorAll("#{sid}-dz i").forEach((el,i)=>tl.fromTo(el,{{opacity:1}},{{opacity:0,duration:0.06,ease:"none"}},{sid}D[i]));')

    def drift_out(self, is_last):
        """Paper look: the whole stage drifts slowly, then blurs up and away at the cut."""
        if self.look["transition"] != "drift":
            return
        self.tw(f'tl.fromTo("#{self.id}-stage", {{scale:1, y:16}}, {{scale:1.03, y:-16, duration:{self.dur}, ease:"none"}}, 0);')
        if not is_last:
            self.tw(f'tl.to("#{self.id}-stage", {{opacity:0, y:-80, filter:"blur(12px)", duration:0.12, ease:"power2.in"}}, {r(self.dur - 0.13)});')

    # --- headline: the line word by word, the slam word huge
    def headline(self, line):
        sid, g, look = self.id, self.g, self.look
        a, b = self.window(line)
        ws = self.ctx["LW"][line]
        slam = [norm(x) for x in str(self.ctx["lines"][line].get("slam", "")).split()]
        run = []
        for i in range(len(ws)):
            if slam and [norm(w["w"]) for w in ws[i:i + len(slam)]] == slam:
                run = list(range(i, i + len(slam)))
                break
        if slam and not run:
            raise SystemExit(f'line {line + 1}: slam "{self.ctx["lines"][line]["slam"]}" is not in its text.')
        n_chars = sum(len(ws[i]["w"]) for i in run) + len(run) - 1 if run else 1
        size = min(150, int(900 / (0.56 * max(n_chars, 1))))
        hid = f"{sid}-h{line}"
        spans = []
        for i, w in enumerate(ws):
            if run and i == run[0]:
                spans.append(f'<span class="slam" style="font-size:{size}px;letter-spacing:{-size * 0.03:.1f}px">'
                             + (f'<span class="slam-wrap"><i class="slam-box" id="{hid}-box"></i><span id="{hid}-st" class="slam-t">' if look["slam"] == "box" else ""))
            spans.append(f'<span class="w" id="{hid}-w{i}">{esc(w["w"])}</span>')
            if run and i == run[-1]:
                spans.append(("</span></span>" if look["slam"] == "box" else "") + "</span>")
        self.html.append(f'<div id="{hid}" class="clip hl" data-start="{a}" data-duration="{r(b - a)}" data-track-index="3">'
                         f'<div class="hl-in" id="{hid}-in">{" ".join(spans)}</div></div>')
        hold_first = line == 0 and self.idx == 0  # frame 0 is the thumbnail: the hook is already on screen
        for i, w in enumerate(ws):
            t = max(a, r(w["s"] - self.s0 - 0.03))
            if i in run:
                if not hold_first:
                    self.tw(f'tl.fromTo("#{hid}-w{i}", {{opacity:0, scale:1.7, filter:"blur(10px)"}}, '
                            f'{{opacity:1, scale:1, filter:"blur(0px)", duration:0.32, ease:"expo.out"}}, {t});')
                if i == run[0] and not (hold_first and look["slam"] != "box"):
                    self.cue(t + 0.05, "slam", 0.5)
                    if look["slam"] == "box":
                        self.tw(f'tl.fromTo("#{hid}-box", {{scaleX:0}}, {{scaleX:1, duration:0.3, ease:"expo.out"}}, {r(t + 0.12)});')
                        self.tw(f'tl.to("#{hid}-st", {{color:"{g["on"]}", duration:0.12}}, {r(t + 0.18)});')
            elif not hold_first:
                self.tw(f'tl.fromTo("#{hid}-w{i}", {{opacity:0, filter:"blur(6px)"}}, '
                        f'{{opacity:1, filter:"blur(0px)", duration:0.13, ease:"power2.out"}}, {t});')
                self.cue(t, f"tick{i % 3 + 1}", 0.05)
        if line != self.last:
            self.tw(f'tl.to("#{hid}-in", {{opacity:0, filter:"blur(8px)", duration:0.12, ease:"power2.in"}}, {r(b - 0.13)});')

    # --- card frame: every card type renders inside one of these
    def card(self, line, inner, top=720, height=560, width=900):
        cid = f"{self.id}-c{line}"
        a, b = self.window(line)
        self.html.append(f'<div id="{cid}" class="clip" data-start="{a}" data-duration="{r(b - a)}" data-track-index="2" '
                         f'style="position:absolute;left:{(W - width) // 2}px;top:{top}px;width:{width}px;height:{height}px">'
                         f'<div id="{cid}-in" style="position:absolute;inset:0">{inner}</div></div>')
        if not (line == 0 and self.idx == 0):
            if self.look["entrance"] == "land":  # fly in from the camera and land with a little overshoot
                self.tw(f'tl.fromTo("#{cid}-in", {{opacity:0, scale:1.5, y:-140, rotationX:38, transformPerspective:1600, filter:"blur(10px)"}}, '
                        f'{{opacity:1, scale:1, y:0, rotationX:0, filter:"blur(0px)", duration:0.45, ease:"back.out(1.5)"}}, {r(a + 0.02)});')
                self.cue(a + 0.28, f"land{line % 3 + 1}", 0.6)
            else:  # rise out of a blur
                self.tw(f'tl.fromTo("#{cid}-in", {{opacity:0, y:50, scale:0.95, filter:"blur(10px)"}}, '
                        f'{{opacity:1, y:0, scale:1, filter:"blur(0px)", duration:0.5, ease:"expo.out"}}, {r(a + 0.02)});')
                if line != self.first:
                    self.cue(a, "whoosh", 0.22)
        if line != self.last:
            self.tw(f'tl.to("#{cid}-in", {{opacity:0, y:-30, filter:"blur(8px)", duration:0.16, ease:"power3.in"}}, {r(b - 0.17)});')
        return cid

    def panel(self, inner, pad=40, extra=""):
        g = self.g
        shadow = ("inset 0 2px 0 #fff, 0 2px 0 #d9d2c5, 0 14px 24px rgba(70,50,20,.10), 0 44px 80px rgba(70,50,20,.18)"
                  if self.look["clay"] else f"0 30px 80px rgba(0,0,0,{0.5 if lum(g['bg']) < 0.3 else 0.10})")
        return (f'<div style="position:absolute;inset:0;background:{g["card"]};border:1px solid {g["line"]};'
                f'border-radius:{self.look["radius"]}px;padding:{pad}px;box-shadow:{shadow};{extra}">{inner}</div>')

    def label(self, text, color=None):
        return f'<div class="mono" style="font-size:28px;color:{color or self.g["muted"]};margin-bottom:28px">{esc(text)}</div>'

    def burst(self, x, y, t, n=20, spread=280):
        """Deterministic debris burst at stage point (x, y): pieces fly out, arc and fall."""
        self.nb += 1
        g = self.g
        cols = (g["accent"], g["ink"], self.look["accent_soft"], g["card"])
        rnd = seeded(n * 5, self.idx * 977 + self.nb * 131)
        pcs = []
        for i in range(n):
            a, s, sz, rt, c = rnd[i * 5:i * 5 + 5]
            pid = f"{self.id}-b{self.nb}-{i}"
            w, h = int(8 + sz * 16), int(6 + (1 - sz) * 12)
            pcs.append(f'<i id="{pid}" style="position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;border-radius:3px;'
                       f'background:{cols[int(c * len(cols)) % len(cols)]};opacity:0"></i>')
            ang = -math.pi * (0.1 + 0.8 * a)
            dx, up, dd = math.cos(ang) * spread * (0.4 + s), math.sin(ang) * spread * (0.5 + s * 0.6), 0.85 + s * 0.35
            self.tw(f'tl.fromTo("#{pid}", {{opacity:0}}, {{opacity:1, duration:0.01}}, {r(t)});')
            self.tw(f'tl.fromTo("#{pid}", {{x:0, y:0, rotation:0}}, {{keyframes:{{x:[0,{dx * 0.7:.0f},{dx:.0f}], y:[0,{up:.0f},{up + 300 + s * 200:.0f}], '
                    f'rotation:[0,{int(rt * 360)},{int(rt * 720)}], easeEach:"power1.out"}}, duration:{dd:.2f}, ease:"none"}}, {r(t)});')
            self.tw(f'tl.to("#{pid}", {{opacity:0, duration:0.3}}, {r(t + dd - 0.3)});')
        self.html.append(f'<div data-layout-ignore style="position:absolute;inset:0;pointer-events:none;z-index:6">{"".join(pcs)}</div>')
        self.cue(t, "rattle", 0.5)

    def write(self, out_dir, fonts):
        g, look = self.g, self.look
        style = "\n".join([
            fonts,
            f"#root {{ position:absolute; inset:0; overflow:hidden; font-family:'{look['body']}',sans-serif; color:{g['ink']}; }}",
            f".hl {{ position:absolute; left:70px; right:70px; top:{self.ctx['safe_top'] - 20}px; text-align:center; z-index:5; }}",
            f".hl-in {{ font-family:'{look['head']}',serif; font-weight:{look['headline_weight']}; font-size:{66 if look['slam'] == 'box' else 62}px; "
            f"line-height:1.1; letter-spacing:{-1 if look['slam'] == 'box' else -2}px; color:{g['ink']}; }}",
            ".hl .w { display:inline-block; }",
            f".hl .slam {{ display:block; font-weight:{look['slam_weight']}; line-height:1.0; margin:10px 0 14px; "
            f"color:{g['ink'] if look['slam'] == 'box' else g['accent']}; }}",
            ".slam-wrap { position:relative; display:inline-block; padding:4px 26px 12px; }",
            f".slam-box {{ position:absolute; inset:0; border-radius:18px; transform-origin:left center; display:block; {fill(g, look)} }}",
            ".slam-t { position:relative; }",
            f".mono {{ font-family:'{look['mono']}',monospace; letter-spacing:3px; text-transform:uppercase; }}",
            ".odo { display:inline-flex; font-variant-numeric:tabular-nums; line-height:1; vertical-align:top; }",
            ".oc { display:inline-block; height:1.2em; overflow:hidden; width:.62em; text-align:center; }",
            ".os { display:block; line-height:1.2em; }",
            *self.css,
        ])
        stage_attrs = 'data-layout-allow-overflow data-layout-allow-overlap'
        out = f"""<template>
<style>
{style}
</style>
<div id="root" data-composition-id="{self.id}" data-width="{W}" data-height="{H}">
<div id="{self.id}-stage" style="position:absolute;inset:0" {stage_attrs}>
{chr(10).join(self.html)}
</div>
</div>
<script>
{ODO_JS if self.uses_odo else ""}
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(self.init)}
{chr(10).join(self.js)}
window.__timelines["{self.id}"] = tl;
</script>
</template>
"""
        (out_dir / "compositions" / f"{self.id}.html").write_text(out)


# ---------------------------------------------------------------- card types
# Each card is a function (scene, line index, options) that writes markup with sc.card(...), tweens with sc.tw(...)
# and a sound for each motion event with sc.cue(...). Times come from sc.find(line, "word"), never by hand.

def card_list_ticks(sc, ln, o):
    g, look = sc.g, sc.look
    items = [i if isinstance(i, dict) else {"label": i} for i in o.get("items", [])]
    a, b = sc.window(ln)
    n = max(len(items), 1)
    rows = []
    for k, it in enumerate(items):
        rid = f"{sc.id}-c{ln}-r{k}"
        rows.append(f'<div id="{rid}" style="display:flex;align-items:center;gap:26px;padding:22px 26px;border:1px solid {g["line"]};'
                    f'border-radius:20px;margin-bottom:18px;background:{g["sub"]}">'
                    f'<div class="mono" style="font-size:30px;color:{g["muted"]};width:56px">{k + 1:02d}</div>'
                    f'<div style="font-weight:600;font-size:46px;color:{g["ink"]}">{esc(it["label"])}</div>'
                    f'<div id="{rid}-tk" style="margin-left:auto;width:56px;height:56px;border-radius:15px;{fill(g, look)}'
                    f'display:flex;align-items:center;justify-content:center">{icon("check", 34, g["on"], 3)}</div></div>')
    title = sc.label(o["title"]) if o.get("title") else ""
    height = (110 if title else 60) + n * 112
    sc.card(ln, sc.panel(title + "".join(rows), pad=36), top=740, height=height)
    span = max(0.6, (b - a) - 0.8)
    for k, it in enumerate(items):
        rid = f"{sc.id}-c{ln}-r{k}"
        t = sc.at(ln, it.get("at"), a + 0.35 + k * span / n)
        sc.tw(f'tl.fromTo("#{rid}", {{opacity:0.25, x:-30}}, {{opacity:1, x:0, duration:0.3, ease:"expo.out"}}, {t});')
        sc.tw(f'tl.fromTo("#{rid}-tk", {{scale:0}}, {{scale:1, duration:0.3, ease:"back.out(2)"}}, {r(t + 0.12)});')
        sc.cue(t + 0.12, f"tick{k % 3 + 1}", 0.5)
    if o.get("allAt"):
        t = sc.find(ln, o["allAt"])
        for k in range(len(items)):
            sc.tw(f'tl.to("#{sc.id}-c{ln}-r{k}", {{borderColor:"{g["accent"]}", backgroundColor:"{g["soft"]}", duration:0.25}}, {r(t + k * 0.05)});')
        sc.cue(t, "chime", 0.25)


def card_bar_grow(sc, ln, o):
    g, look = sc.g, sc.look
    bars = o.get("bars", [])
    a, _ = sc.window(ln)
    tag = o.get("tag") or {}
    final = [x.get("to", x["value"]) for x in bars]
    win = tag.get("bar", max(range(len(bars)), key=lambda i: final[i]) if bars else 0)
    row_h = 132
    rows = []
    for i, x in enumerate(bars):
        bid = f"{sc.id}-c{ln}-b{i}"
        strong = i == win
        bar_css = fill(g, look, True) if strong else f"background:{mix(g['muted'] if g['muted'].startswith('#') else '#9a9389', g['card'], 0.35)};"
        tag_html = (f'<div id="{bid}-tag" class="mono" style="margin-left:auto;font-size:30px;padding:8px 16px;border-radius:10px;'
                    f'background:{g["ink"]};color:{g["card"]}">{esc(tag["text"])}</div>') if tag and i == tag.get("bar") else ""
        rows.append(f'<div id="{bid}-row" style="position:absolute;left:0;right:0;top:{i * row_h}px;height:{row_h}px">'
                    f'<div style="display:flex;align-items:center;gap:18px;margin-bottom:14px">'
                    f'<div style="font-weight:600;font-size:42px;color:{g["ink"]}">{esc(x["label"])}</div>{tag_html}</div>'
                    f'<div style="height:30px;border-radius:15px;background:{g["track"]};position:relative">'
                    f'<div id="{bid}" style="position:absolute;left:0;top:0;height:30px;width:100%;border-radius:15px;transform-origin:left center;{bar_css}"></div></div></div>')
    title = sc.label(o["title"]) if o.get("title") else ""
    inner = title + f'<div style="position:relative;height:{len(bars) * row_h}px">{"".join(rows)}</div>'
    sc.card(ln, sc.panel(inner, pad=50), top=760, height=(130 if title else 90) + len(bars) * row_h)
    for i, x in enumerate(bars):
        t = r(a + 0.25 + i * 0.12)
        sc.tw(f'tl.fromTo("#{sc.id}-c{ln}-b{i}", {{scaleX:0}}, {{scaleX:{x["value"]}, duration:0.6, ease:"expo.out"}}, {t});')
        sc.cue(t, f"tick{i % 3 + 1}", 0.4)
    if o.get("raceAt"):  # bar race: values move to "to" and the rows swap into rank order
        t = sc.find(ln, o["raceAt"])
        order = sorted(range(len(bars)), key=lambda i: -final[i])
        for i, x in enumerate(bars):
            sc.tw(f'tl.to("#{sc.id}-c{ln}-b{i}", {{scaleX:{final[i]}, duration:0.6, ease:"power3.inOut"}}, {t});')
            dy = (order.index(i) - i) * row_h
            if dy:
                sc.tw(f'tl.to("#{sc.id}-c{ln}-b{i}-row", {{y:{dy}, duration:0.45, ease:"power3.inOut"}}, {r(t + 0.1)});')
        sc.cue(t, "whoosh", 0.3)
        sc.cue(t + 0.5, "land3", 0.6)
    if tag:
        t = sc.at(ln, tag.get("at"), a + 1.0)
        sc.tw(f'tl.fromTo("#{sc.id}-c{ln}-b{tag["bar"]}-tag", {{scale:0, rotation:-12}}, {{scale:1, rotation:-4, duration:0.35, ease:"back.out(2.2)"}}, {t});')
        sc.cue(t, "pop", 0.5)


def card_counter(sc, ln, o):
    g = sc.g
    sc.uses_odo = True
    a, b = sc.window(ln)
    v0, v1 = int(o.get("from", 0)), int(o["to"])
    nd = len(str(max(abs(v0), abs(v1))))
    oid = f"{sc.id}-c{ln}-o"
    size = 300 if nd <= 2 else 220
    num = (f'<div id="{oid}-wrap" style="font-weight:800;font-size:{size}px;letter-spacing:-6px;color:{g["accent"]};line-height:1">'
           f'{esc(o.get("prefix", ""))}{odo_html(oid, nd)}{esc(o.get("suffix", ""))}</div>')
    lab = f'<div style="font-weight:600;font-size:52px;color:{g["ink"]};margin-top:22px">{esc(o.get("label", ""))}</div>'
    note = f'<div class="mono" style="font-size:28px;color:{g["muted"]};margin-top:26px">{esc(o["note"])}</div>' if o.get("note") else ""
    inner = sc.panel(f'<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%">{num}{lab}{note}</div>', pad=40)
    sc.card(ln, inner, top=760, height=520)
    t1 = sc.at(ln, o.get("at"), b - 0.4)
    t0 = r(a + 0.25)
    if t1 - t0 < 0.5:
        t0 = r(max(0.0, t1 - 0.5))
    sc.init.append(f'odo("{oid}", {v0}, {nd});')
    sc.tw(f'(()=>{{const o={{v:{v0}}}; tl.fromTo(o,{{v:{v0}}},{{v:{v1},duration:{r(t1 - t0)},ease:"power1.inOut",'
          f'onUpdate:()=>odo("{oid}",o.v,{nd})}},{t0});}})();')
    sc.cue(t0, "roll", 0.45)
    sc.tw(f'tl.fromTo("#{oid}-wrap", {{scale:1}}, {{scale:1.12, duration:0.1, ease:"power2.out"}}, {t1}); '
          f'tl.to("#{oid}-wrap", {{scale:1, duration:0.3, ease:"back.out(2.5)"}}, {r(t1 + 0.1)});')
    sc.cue(t1, "land1", 0.7)
    sc.cue(t1 + 0.05, "chime", 0.25)
    sc.burst(W // 2, 1000, r(t1 + 0.02))


def card_cursor_click(sc, ln, o):
    g, look = sc.g, sc.look
    a, b = sc.window(ln)
    cid = f"{sc.id}-c{ln}"
    skel = "".join(f'<div style="height:{h}px;border-radius:12px;background:{g["sub"]};border:1px solid {g["line"]};margin-bottom:16px;width:{w}%"></div>'
                   for h, w in [(40, 62), (40, 84)])
    head = (f'<div style="display:flex;align-items:center;gap:16px;margin-bottom:30px">{icon("doc", 44, g["ink"])}'
            f'<div style="font-weight:700;font-size:42px;color:{g["ink"]}">{esc(o.get("title", ""))}</div></div>')
    btn = (f'<div id="{cid}-btn" style="position:absolute;left:150px;top:290px;width:600px;height:140px;border-radius:30px;{fill(g, look)}'
           f'display:flex;align-items:center;justify-content:center;font-weight:700;font-size:56px;color:{g["on"]};letter-spacing:-1px">'
           f'<span id="{cid}-l0">{esc(o.get("button", "Start"))}</span>'
           f'<span id="{cid}-l1" style="position:absolute;opacity:0">{esc(o.get("done", o.get("button", "Start")))}</span></div>'
           f'<div id="{cid}-cur" style="position:absolute;left:0;top:0;z-index:3">{CURSOR}</div>')
    sc.card(ln, sc.panel(head + skel + btn, pad=40), top=760, height=500)
    t = sc.at(ln, o.get("at"), b - 0.5)
    sc.tw(f'tl.fromTo("#{cid}-cur", {{x:820, y:470}}, {{x:560, y:380, duration:0.55, ease:"power3.inOut"}}, {r(max(a + 0.1, t - 0.55))});')
    sc.tw(f'tl.to("#{cid}-btn", {{scale:0.94, duration:0.08, ease:"power2.in"}}, {t});')
    sc.tw(f'tl.to("#{cid}-btn", {{scale:1, duration:0.3, ease:"back.out(2)"}}, {r(t + 0.08)});')
    sc.tw(f'tl.to("#{cid}-l0", {{opacity:0, duration:0.08}}, {r(t + 0.05)}); tl.fromTo("#{cid}-l1", {{opacity:0}}, {{opacity:1, duration:0.12}}, {r(t + 0.1)});')
    sc.cue(t, "click", 0.6)
    sc.cue(t + 0.1, "pop", 0.35)


def card_gauge(sc, ln, o):
    g = sc.g
    a, b = sc.window(ln)
    cid = f"{sc.id}-c{ln}"
    v0, v1 = float(o.get("from", 0.1)), float(o.get("to", 0.9))
    col = g.get(o.get("color", "accent"), g["accent"])
    start_col = g["danger"] if o.get("color") == "success" else g["track"]
    L = 440  # length of the arc path below (half circle, radius 140)
    svg = (f'<svg width="460" height="270" viewBox="0 0 340 200"><path d="M30 180 A140 140 0 0 1 310 180" fill="none" stroke="{g["track"]}" stroke-width="26" stroke-linecap="round"/>'
           f'<path id="{cid}-arc" d="M30 180 A140 140 0 0 1 310 180" fill="none" stroke="{start_col}" stroke-width="26" stroke-linecap="round" stroke-dasharray="{L}" stroke-dashoffset="{L * (1 - v0):.0f}"/>'
           f'<line id="{cid}-nd" x1="170" y1="180" x2="170" y2="62" stroke="{g["ink"]}" stroke-width="8" stroke-linecap="round"/><circle cx="170" cy="180" r="14" fill="{g["ink"]}"/></svg>')
    ends = (f'<div style="display:flex;justify-content:space-between;width:460px;margin-top:6px" class="mono">'
            f'<span style="font-size:28px;color:{g["muted"]}">{esc(o.get("low", ""))}</span><span style="font-size:28px;color:{g["muted"]}">{esc(o.get("high", ""))}</span></div>') if o.get("low") or o.get("high") else ""
    inner = (f'<div style="display:flex;flex-direction:column;align-items:center">{sc.label(o.get("label", ""))}{svg}{ends}'
             f'<div id="{cid}-v" style="font-weight:800;font-size:96px;letter-spacing:-3px;color:{col};margin-top:8px;opacity:0">{esc(o.get("value", ""))}</div></div>')
    sc.card(ln, sc.panel(inner, pad=44), top=740, height=600)
    t = sc.at(ln, o.get("at"), a + 1.0)
    ang = lambda v: -90 + 180 * v
    sc.tw(f'tl.set("#{cid}-nd", {{rotation:{ang(v0):.1f}, svgOrigin:"170 180"}}, 0);')
    sc.tw(f'tl.to("#{cid}-nd", {{rotation:{ang(v1):.1f}, svgOrigin:"170 180", duration:0.6, ease:"back.out(1.4)"}}, {r(t - 0.15)});')
    sc.tw(f'tl.to("#{cid}-arc", {{attr:{{"stroke-dashoffset":{L * (1 - v1):.0f}}}, stroke:"{col}", duration:0.6, ease:"power2.out"}}, {r(t - 0.15)});')
    sc.tw(f'tl.fromTo("#{cid}-v", {{scale:1.4, opacity:0}}, {{scale:1, opacity:1, duration:0.3, ease:"expo.out"}}, {r(t + 0.3)});')
    for k in range(3):
        sc.cue(t - 0.15 + k * 0.1, f"tick{k + 1}", 0.45)
    sc.cue(t + 0.3, "land2", 0.6)


def card_quote(sc, ln, o):
    g, look = sc.g, sc.look
    a, _ = sc.window(ln)
    cid = f"{sc.id}-c{ln}"
    hi = [norm(x) for x in o.get("highlight", [])]
    words = o["text"].split()
    parts, i, runs = [], 0, []
    while i < len(words):
        if norm(words[i]) in hi:
            j = i
            while j < len(words) and norm(words[j]) in hi:
                j += 1
            k = len(runs)
            runs.append(k)
            parts.append(f'<span style="position:relative;display:inline-block;padding:0 14px;margin:0 -4px">'
                         f'<i id="{cid}-hb{k}" style="position:absolute;left:0;right:0;top:8px;bottom:-4px;border-radius:12px;transform-origin:left center;display:block;{fill(g, look)}"></i>'
                         f'<span id="{cid}-ht{k}" style="position:relative">{esc(" ".join(words[i:j]))}</span></span>')
            i = j
        else:
            parts.append(esc(words[i]))
            i += 1
    serif = look["head"]
    inner = (f'<div style="font-family:\'{serif}\',serif;font-weight:800;font-size:150px;line-height:.8;color:{g["accent"]};height:90px">&ldquo;</div>'
             f'<div style="font-family:\'{serif}\',serif;font-weight:700;font-size:76px;line-height:1.12;letter-spacing:-1.5px;color:{g["ink"]}">{" ".join(parts)}</div>'
             + (f'<div class="mono" style="font-size:28px;color:{g["muted"]};margin-top:36px">{esc(o["by"])}</div>' if o.get("by") else ""))
    sc.card(ln, sc.panel(inner, pad=56), top=760, height=500)
    t = sc.at(ln, o.get("at"), a + 0.8)
    for k in runs:
        tk = r(t + k * 0.2)
        sc.tw(f'tl.fromTo("#{cid}-hb{k}", {{scaleX:0}}, {{scaleX:1, duration:0.3, ease:"expo.out"}}, {tk});')
        sc.tw(f'tl.to("#{cid}-ht{k}", {{color:"{g["on"]}", duration:0.1}}, {r(tk + 0.08)});')
        sc.cue(tk, "tick2", 0.5)
        sc.cue(tk + 0.05, "whoosh", 0.15)


def card_cta_profile(sc, ln, o):
    g, look, brand = sc.g, sc.look, sc.ctx["brand"]
    a, b = sc.window(ln)
    cid = f"{sc.id}-c{ln}"
    logo = (f'<img src="{sc.ctx["logo"]}" alt="" style="width:150px;height:150px;border-radius:36px;display:block">' if sc.ctx["logo"]
            else f'<div style="width:150px;height:150px;border-radius:36px;{fill(g, look)}"></div>')
    cta = brand.get("cta", {})
    inner = (f'<div style="display:flex;align-items:center;gap:30px;margin-bottom:34px">{logo}'
             f'<div><div style="font-weight:800;font-size:58px;letter-spacing:-1.5px;color:{g["ink"]};line-height:1.05">{esc(brand.get("name", ""))}</div>'
             f'<div style="font-size:38px;color:{g["muted"]};margin-top:8px">{esc(brand.get("handle", ""))}</div></div></div>'
             f'<div class="mono" style="font-size:28px;color:{g["muted"]};margin-bottom:30px">{esc(o.get("sub", cta.get("default", "")))}'
             f' &middot; {esc(brand.get("url", ""))}</div>'
             f'<div id="{cid}-btn" style="position:relative;height:130px;border-radius:30px;{fill(g, look)}display:flex;align-items:center;justify-content:center;'
             f'font-weight:800;font-size:56px;color:{g["on"]};letter-spacing:-1px">'
             f'<i id="{cid}-ok" style="position:absolute;inset:0;border-radius:30px;background:{g["success"]};opacity:0;display:block"></i>'
             f'<span id="{cid}-l0" style="position:relative">{esc(o.get("button", "Follow"))}</span>'
             f'<span id="{cid}-l1" style="position:absolute;opacity:0;color:{on(g["success"])}">{esc(o.get("done", "Following"))}</span></div>'
             f'<div id="{cid}-cur" style="position:absolute;left:0;top:0;z-index:3">{CURSOR}</div>')
    sc.card(ln, sc.panel(inner, pad=48), top=760, height=520)
    t = sc.at(ln, o.get("at"), a + 0.8)
    sc.tw(f'tl.fromTo("#{cid}-cur", {{x:820, y:520}}, {{x:520, y:410, duration:0.55, ease:"power3.inOut"}}, {r(max(a + 0.1, t - 0.45))});')
    sc.tw(f'tl.to("#{cid}-btn", {{scale:0.95, duration:0.08}}, {r(t + 0.1)}); tl.to("#{cid}-btn", {{scale:1, duration:0.3, ease:"back.out(2)"}}, {r(t + 0.18)}); '
          f'tl.fromTo("#{cid}-ok", {{opacity:0}}, {{opacity:1, duration:0.2}}, {r(t + 0.15)});')
    sc.tw(f'tl.to("#{cid}-l0", {{opacity:0, duration:0.08}}, {r(t + 0.15)}); tl.fromTo("#{cid}-l1", {{opacity:0}}, {{opacity:1, duration:0.12}}, {r(t + 0.2)});')
    sc.cue(t + 0.1, "click", 0.6)
    sc.cue(t + 0.2, "chime", 0.35)


CARDS = {
    "list-ticks": card_list_ticks,
    "bar-grow": card_bar_grow,
    "counter": card_counter,
    "odometer": card_counter,
    "cursor-click": card_cursor_click,
    "gauge": card_gauge,
    "quote": card_quote,
    "highlight": card_quote,
    "cta-profile": card_cta_profile,
}


# ---------------------------------------------------------------- paper backdrop (one composition under every scene)
def write_paper(out_dir, look, end, fonts):
    g = look["grounds"][0]
    bands = "".join(f'<div style="position:absolute;left:{x}px;top:0;width:{w}px;height:2800px;background:linear-gradient(90deg,rgba(255,255,255,0),'
                    f'rgba(255,255,255,{o}),rgba(255,255,255,0));transform:rotate(24deg)"></div>'
                    for x, w, o in [(300, 260, .55), (700, 140, .4), (1150, 320, .5), (1700, 180, .35)])
    shade = "".join(f'<div style="position:absolute;left:{x}px;top:0;width:{w}px;height:2800px;background:linear-gradient(90deg,rgba(120,90,50,0),'
                    f'rgba(120,90,50,.07),rgba(120,90,50,0));transform:rotate(24deg)"></div>' for x, w in [(520, 160), (950, 200), (1480, 220)])
    html = f"""<template>
<style>
{fonts}
#root {{ position:absolute; inset:0; overflow:hidden; background:{g['bg']}; }}
</style>
<div id="root" data-composition-id="paper" data-width="{W}" data-height="{H}">
<div style="position:absolute;inset:0;background-image:linear-gradient(rgba(0,0,0,.045) 1px,transparent 1px),linear-gradient(90deg,rgba(0,0,0,.045) 1px,transparent 1px);background-size:54px 54px"></div>
<div id="lt" data-layout-ignore style="position:absolute;left:-600px;top:-400px;width:2400px;height:2800px">{bands}{shade}</div>
<div style="position:absolute;inset:0;background:radial-gradient(ellipse 110% 70% at 50% 40%, rgba(0,0,0,0) 55%, rgba(80,60,30,.12))"></div>
</div>
<script>
const tl = gsap.timeline({{ paused: true }});
tl.fromTo("#lt", {{x:0}}, {{x:220, duration:{end}, ease:"none"}}, 0);
window.__timelines["paper"] = tl;
</script>
</template>
"""
    (out_dir / "compositions" / "paper.html").write_text(html)


# ---------------------------------------------------------------- sound
def read_wav(path):
    with wave.open(str(path)) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768
        if w.getnchannels() > 1:
            x = x.reshape(-1, w.getnchannels()).mean(1)
    return x


def mix_sfx(out_dir, end, sr=44100):
    """Place every cue on one track. Gains are relative; the <audio> tag's data-volume sets the overall level."""
    pack = out_dir / "assets" / "sfx"
    names = {n for _, n, _ in SFX}
    if not all((pack / f"{n}.wav").exists() for n in names):
        sfxpack.build(pack)
    bus = np.zeros(int(sr * end), dtype=np.float32)
    cache = {}
    for t, name, gain in SFX:
        if name not in cache:
            cache[name] = read_wav(pack / f"{name}.wav")
        x, p = cache[name], int(t * sr)
        m = min(len(x), len(bus) - p)
        if m > 0 and p >= 0:
            bus[p:p + m] += x[:m] * gain
    peak = float(np.max(np.abs(bus))) if len(bus) else 0.0
    if peak > 0.95:
        bus *= 0.95 / peak
    with wave.open(str(out_dir / "assets" / "sfx-mix.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(bus, -1, 1) * 32767).astype("<i2").tobytes())
    return len(SFX), round(peak, 2)


def audio_seconds(path):
    import subprocess
    try:
        return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)]).decode())
    except Exception:
        return None


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--script", default=str(HERE / "script.json"))
    ap.add_argument("--brand", default=str(HERE.parent.parent / "brand" / "brand.json"))
    ap.add_argument("--look", default=None, help="dark (default, from brand.json) or paper")
    ap.add_argument("--out", default=str(HERE / "hf"))
    args = ap.parse_args()

    script_path = Path(args.script).resolve()
    sdir = script_path.parent
    script = json.load(open(script_path))
    brand_path = Path(args.brand).resolve()
    brand = json.load(open(brand_path))
    look = make_look(args.look or script.get("look", "dark"), brand)
    out = Path(args.out).resolve()
    (out / "compositions").mkdir(parents=True, exist_ok=True)
    (out / "assets").mkdir(parents=True, exist_ok=True)
    for f in (out / "compositions").glob("*.html"):
        f.unlink()

    lines = script["lines"]
    for k, ln in enumerate(lines):
        typ = ln.get("card", {}).get("type")
        if typ not in CARDS:
            raise SystemExit(f'line {k + 1}: card type "{typ}" is unknown. Known: {", ".join(sorted(CARDS))}')
    LW = align(lines, load_words(sdir / script.get("words", "words.json")))

    # Scenes: groups of lines. Each scene is one sub-composition; the ground can change between scenes.
    groups = script.get("scenes") or [list(range(i, min(i + 2, len(lines)))) for i in range(0, len(lines), 2)]
    flat = [i for grp in groups for i in grp]
    if flat != list(range(len(lines))):
        raise SystemExit('"scenes" must list every line once, in order, e.g. [[0, 1], [2, 3], [4]].')
    end = r(max(w["e"] for row in LW for w in row) + float(script.get("hold", 2.0)))
    starts = [0.0] + [r(LW[grp[0]][0]["s"] - 0.25) for grp in groups[1:]]
    bounds = list(zip(starts, starts[1:] + [end]))

    # Assets: fonts, logo, voiceover.
    fonts = font_css(look, brand_path.parent, out / "assets" / "fonts")
    logo_rel = None
    lp = brand.get("logo")
    if lp:
        for base in (brand_path.parent, brand_path.parent.parent):
            if (base / lp).exists():
                dst = out / "assets" / ("logo" + (base / lp).suffix)
                shutil.copy(base / lp, dst)
                logo_rel = f"assets/{dst.name}"
                break
    audio = sdir / script.get("audio", "vo.mp3")
    vo_tag = ""
    if audio.exists():
        shutil.copy(audio, out / "assets" / f"vo{audio.suffix}")
        vo_len = audio_seconds(audio) or end
        vo_tag = (f'      <audio id="vo" src="assets/vo{audio.suffix}" data-start="0" data-duration="{r(min(vo_len, end))}" '
                  f'data-track-index="10" data-volume="1"></audio>')
    else:
        print(f"note: no voiceover at {audio}; building silent")

    ctx = dict(look=look, brand=brand, lines=lines, LW=LW, logo=logo_rel,
               safe_top=int(brand.get("safeZone", {}).get("top", 240)))
    SFX.clear()
    scenes = [Scene(ctx, k, grp, a, b) for k, (grp, (a, b)) in enumerate(zip(groups, bounds))]
    for k, sc in enumerate(scenes):
        sc.backdrop()
        for ln in sc.lines:
            CARDS[lines[ln]["card"]["type"]](sc, ln, lines[ln]["card"])
            sc.headline(ln)
        sc.transition_in(scenes[k - 1] if k else None)
        sc.drift_out(k == len(scenes) - 1)
        sc.write(out, fonts)

    hosts = []
    if look["backdrop"] == "paper":
        write_paper(out, look, end, fonts)
        hosts.append(f'      <div id="paper" data-composition-id="paper" data-composition-src="compositions/paper.html" data-start="0" '
                     f'data-duration="{end}" data-track-index="0" data-track-kind="graphics" data-width="{W}" data-height="{H}" style="z-index:0"></div>')
    for sc in scenes:
        hosts.append(f'      <div id="{sc.id}" data-composition-id="{sc.id}" data-composition-src="compositions/{sc.id}.html" data-start="{r(sc.s0)}" '
                     f'data-duration="{sc.dur}" data-track-index="1" data-track-kind="graphics" data-width="{W}" data-height="{H}" style="z-index:1"></div>')
    n_cues, peak = mix_sfx(out, end)
    page_bg = look["grounds"][0]["bg"]
    index = f"""<!doctype html>
<html lang="en" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <title>{esc(script.get("title", "Explainer"))}</title>
    <script src="{GSAP}"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ margin: 0; width: {W}px; height: {H}px; overflow: hidden; background: {page_bg}; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{end}" data-width="{W}" data-height="{H}">
{chr(10).join(hosts)}
{vo_tag}
      <audio id="sfx" src="assets/sfx-mix.wav" data-start="0" data-duration="{end}" data-track-index="11" data-volume="0.6"></audio>
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""
    (out / "index.html").write_text(index)

    # Project files, written once so your own edits to them survive a re-run.
    files = {
        "hyperframes.json": json.dumps({"$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
                                        "paths": {"blocks": "compositions", "assets": "assets"}}, indent=2) + "\n",
        "package.json": json.dumps({"name": "explainer", "private": True, "type": "module", "scripts": {
            "dev": f"npx --yes hyperframes@{HF_VERSION} preview", "check": f"npx --yes hyperframes@{HF_VERSION} check",
            "render": f"npx --yes hyperframes@{HF_VERSION} render"}}, indent=2) + "\n",
        "meta.json": json.dumps({"id": "explainer", "name": "explainer"}, indent=2) + "\n",
    }
    for name, body in files.items():
        if not (out / name).exists():
            (out / name).write_text(body)

    print(f"look: {look['name']}  length: {end}s  scenes: {[(s.id, r(s.s0), s.dur) for s in scenes]}")
    print(f"sfx: {n_cues} cues, peak {peak}  ->  {out}")


if __name__ == "__main__":
    main()
