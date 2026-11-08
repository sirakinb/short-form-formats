"""Transcribe a media file with word timestamps (faster-whisper).

Usage: python3 transcribe.py <audio-or-video> <out.json> [model]
Writes [{"w": word, "s": start, "e": end}, ...] and prints the lines with times.
Every format keys its visuals to these word times. Don't time anything by hand.
Requires: pip install faster-whisper numpy, and ffmpeg on your PATH.
"""
import json, subprocess, sys
import numpy as np
from faster_whisper import WhisperModel

src, out = sys.argv[1], sys.argv[2]
model = sys.argv[3] if len(sys.argv) > 3 else "small"
raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", src, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
                     check=True, capture_output=True).stdout
segs, _ = WhisperModel(model, device="cpu", compute_type="int8").transcribe(
    np.frombuffer(raw, np.float32), word_timestamps=True)
words, lines = [], []
for s in segs:
    lines.append(f"[{s.start:6.2f}-{s.end:6.2f}] {s.text.strip()}")
    words += [{"w": w.word.strip(), "s": round(w.start, 2), "e": round(w.end, 2)} for w in s.words]
json.dump(words, open(out, "w"), indent=0)
print("\n".join(lines))
