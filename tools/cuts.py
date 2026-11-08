"""Cut the dead air out of a talking-head take.

Usage: python3 cuts.py <words.json> <edit.json> [max_gap_seconds=0.5]
Reads word times from transcribe.py and writes the segments to keep (source seconds)
plus the words retimed to the edited video. Pauses longer than max_gap are removed.
"""
import json, sys

src_path, out_path = sys.argv[1], sys.argv[2]
MAX_GAP = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
PAD_IN, PAD_OUT = 0.08, 0.15
words = json.load(open(src_path))
groups = [[words[0]]]
for w in words[1:]:
    (groups[-1].append(w) if w["s"] - groups[-1][-1]["e"] <= MAX_GAP else groups.append([w]))
segments, out_words, t = [], [], 0.0
for g in groups:
    a, b = max(0, g[0]["s"] - PAD_IN), g[-1]["e"] + PAD_OUT
    if segments and a < segments[-1]["to"]:
        a = segments[-1]["to"]
    segments.append({"from": round(a, 3), "to": round(b, 3), "at": round(t, 3)})
    for w in g:
        # Whisper splits "5.5" into "5" + ".5": glue such pieces back onto the previous word.
        if out_words and w["w"][:1] in ".-" and len(w["w"]) > 1:
            out_words[-1]["w"] += w["w"]; out_words[-1]["e"] = round(w["e"] - a + t, 3)
        else:
            out_words.append({"w": w["w"], "s": round(w["s"] - a + t, 3), "e": round(w["e"] - a + t, 3)})
    t += b - a
json.dump({"duration": round(t, 3), "segments": segments, "words": out_words}, open(out_path, "w"), indent=1)
print(f"{len(segments)} segments, {words[-1]['e']:.1f}s -> {t:.1f}s (cut {words[-1]['e'] - t:.1f}s)")
