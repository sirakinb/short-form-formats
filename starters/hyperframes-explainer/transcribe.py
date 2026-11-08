"""Transcribe a voiceover with word timestamps (faster-whisper), for gen.py.

Usage: python3 transcribe.py <audio-or-video> <out.json> [model]
Writes [{"w": word, "s": start, "e": end}, ...] and prints each segment with its times.
gen.py keys every visible change to these word times, so never time anything by hand.

Requires faster-whisper and numpy (pip install faster-whisper numpy, or
`uv run --with faster-whisper --with numpy python transcribe.py ...`) and ffmpeg on your PATH.
The first run downloads the model (about 500 MB for "small").
"""
import json
import subprocess
import sys

import numpy as np
from faster_whisper import WhisperModel

if len(sys.argv) < 3:
    sys.exit(__doc__)
src, out = sys.argv[1], sys.argv[2]
model = sys.argv[3] if len(sys.argv) > 3 else "small"

# Decode to 16 kHz mono float32 with ffmpeg, so any audio or video file works.
raw = subprocess.run(
    ["ffmpeg", "-loglevel", "error", "-i", src, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
    check=True, capture_output=True,
).stdout
segs, _ = WhisperModel(model, device="cpu", compute_type="int8").transcribe(
    np.frombuffer(raw, np.float32), word_timestamps=True)

words, lines = [], []
for s in segs:
    lines.append(f"[{s.start:6.2f}-{s.end:6.2f}] {s.text.strip()}")
    words += [{"w": w.word.strip(), "s": round(w.start, 2), "e": round(w.end, 2)} for w in s.words]
with open(out, "w") as f:
    json.dump(words, f, indent=0)
print("\n".join(lines))
print(f"{len(words)} words -> {out}")
