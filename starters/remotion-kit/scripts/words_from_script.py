"""Estimate word timings from a script, so you can lay out beats before you record.

Usage: python3 scripts/words_from_script.py "Your script here. | Pause marks a long silence." out.json

Writes [{"w", "s", "e"}, ...] in the same shape as tools/transcribe.py. The times are guesses
(about 150 words a minute). Once you have a real take or voiceover, transcribe it and replace the
file: every beat is keyed to words with at(), so nothing else needs to change.
A "|" in the script inserts a 0.9 s pause, like the dead air tools/cuts.py removes from a real take.
"""
import json, re, sys


def estimate(script: str, start: float = 0.15):
    out, t = [], start
    for tok in script.split():
        if tok == "|":
            t += 0.9
            continue
        letters = len(re.sub(r"[^A-Za-z0-9]", "", tok)) or 1
        dur = min(0.62, max(0.18, 0.14 + 0.06 * letters))
        out.append({"w": tok, "s": round(t, 2), "e": round(t + dur, 2)})
        t += dur + 0.04
        if re.search(r"[,:;]$", tok):
            t += 0.18
        elif re.search(r"[.?!]$", tok):
            t += 0.32
    return out


if __name__ == "__main__":
    words = estimate(sys.argv[1])
    json.dump(words, open(sys.argv[2], "w"), indent=1)
    print(f"{len(words)} words, {words[-1]['e']:.2f} s -> {sys.argv[2]}")
