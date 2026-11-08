"""Synthesize a soft UI sound pack with numpy and the standard-library wave module. No sound files are downloaded.

Usage: python3 sfx.py [out_dir]          (default: hf/assets/sfx)
gen.py calls this for you when the pack is missing, then mixes the cues into one track.

The pack:
  whoosh       airy band-passed noise swell (scene changes, cards rising in)
  slam         sub drop plus a low thock (the big accent word on each line)
  tick1..3     tiny clicks (words appearing, list ticks, gauge steps)
  land1..3     soft low thocks (cards landing, rows settling)
  click        UI button press (cursor clicks)
  pop          quick upward blip (tags and badges popping on)
  chime        glassy bell (a win: the counter landing, a CTA)
  roll         rapid ticks that slow down (odometer counting)
  rattle       scatter of small clicks (debris bursts)
Change a recipe below, re-run, and every video made afterwards picks it up.
"""
import sys
import wave
from pathlib import Path

import numpy as np

SR = 44100
rng = np.random.default_rng(7)  # seeded, so the pack is identical on every machine


def env(n, attack, decay):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(attack, 1e-4)) * np.exp(-t / decay)


def lp(x, cut):
    """One-pole low-pass filter."""
    a = np.exp(-2 * np.pi * cut / SR)
    y = np.empty_like(x)
    s = 0.0
    for i, v in enumerate(x):
        s = (1 - a) * v + a * s
        y[i] = s
    return y


def hp(x, cut):
    return x - lp(x, cut)


def sweep(f):
    """Phase of a sine whose frequency follows the array f."""
    return 2 * np.pi * np.cumsum(f) / SR


def write_wav(path, x, peak=0.5):
    x = x / (np.max(np.abs(x)) + 1e-9) * peak
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def thock(f0, f1, dur, click=0.25):
    n = int(SR * dur)
    t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t / 0.03)
    body = np.sin(sweep(f)) * env(n, 0.002, dur / 4)
    noise = lp(rng.standard_normal(n), 2500) * env(n, 0.0005, 0.012) * click
    return body + noise


def bell(freqs, dur=0.9):
    n = int(SR * dur)
    t = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * f * t) * np.exp(-t / (dur / (1 + k))) / (1 + k) for k, f in enumerate(freqs))
    return x * env(n, 0.002, dur)


def build(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)

    # whoosh: band-passed noise with a sine-squared swell
    n = int(SR * 0.34)
    t = np.arange(n) / SR
    x = lp(hp(rng.standard_normal(n), 400), 3000)
    write_wav(out / "whoosh.wav", x * np.sin(np.pi * np.clip(t / 0.34, 0, 1)) ** 2, 0.45)

    # slam: sub drop under a low thock
    n = int(SR * 0.7)
    t = np.arange(n) / SR
    sub = np.sin(sweep(42 + 80 * np.exp(-t / 0.07))) * env(n, 0.003, 0.22)
    x = sub + np.pad(thock(180, 60, 0.3, 0.5), (0, n - int(SR * 0.3))) * 0.6
    x += lp(rng.standard_normal(n), 900) * env(n, 0.001, 0.04) * 0.4
    write_wav(out / "slam.wav", x, 0.75)

    # ticks: tiny high clicks
    for i, c in enumerate([3500, 5000, 2600]):
        n = int(SR * 0.03)
        x = hp(rng.standard_normal(n), c * 0.5) * env(n, 0.0003, 0.004)
        x += np.sin(2 * np.pi * c * np.arange(n) / SR) * env(n, 0.0003, 0.003) * 0.4
        write_wav(out / f"tick{i + 1}.wav", x, 0.35)

    # lands: soft low thocks at three pitches
    for i, (a, b) in enumerate([(220, 70), (260, 85), (190, 60)]):
        write_wav(out / f"land{i + 1}.wav", thock(a, b, 0.22), 0.6)

    # click: a short, bright button press
    n = int(SR * 0.06)
    x = thock(900, 400, 0.06, 0.6) + hp(rng.standard_normal(n), 2500) * env(n, 0.0002, 0.003) * 0.5
    write_wav(out / "click.wav", x, 0.45)

    # pop: fast upward sine blip
    n = int(SR * 0.09)
    t = np.arange(n) / SR
    write_wav(out / "pop.wav", np.sin(sweep(300 + 900 * (t / 0.09))) * env(n, 0.001, 0.025), 0.45)

    # chime: glassy three-partial bell
    write_wav(out / "chime.wav", bell([1568, 2349, 3136]), 0.4)

    # roll: rapid soft ticks that slow down, for odometer counting
    n = int(SR * 1.2)
    x = np.zeros(n)
    tt, gap = 0.0, 0.035
    while tt < 1.15:
        p, m = int(SR * tt), int(SR * 0.008)
        x[p:p + m] += hp(rng.standard_normal(m), 3000) * env(m, 0.0002, 0.002)
        tt += gap
        gap *= 1.04
    write_wav(out / "roll.wav", x, 0.25)

    # rattle: a scatter of small clicks that thins out (debris)
    n = int(SR * 0.6)
    x = np.zeros(n)
    for k in range(22):
        p = int(SR * (0.6 * (k / 22) ** 1.6)) + int(rng.integers(0, 400))
        m = min(n - p, int(SR * 0.012))
        if m > 0:
            x[p:p + m] += hp(rng.standard_normal(m), 1800) * env(m, 0.0002, 0.003) * (1 - k / 26)
    write_wav(out / "rattle.wav", x, 0.35)
    return sorted(p.name for p in out.glob("*.wav"))


if __name__ == "__main__":
    dest = sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent / "hf" / "assets" / "sfx"
    print("wrote", build(dest))
