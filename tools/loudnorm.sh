#!/usr/bin/env bash
# Usage: loudnorm.sh <in.mp4> <out.mp4>
# Normalises audio to -14 LUFS (the TikTok, Reels and Shorts target) without re-encoding video.
set -euo pipefail
ffmpeg -y -i "$1" -c:v copy -af "loudnorm=I=-14:TP=-1.5:LRA=11" -c:a aac -b:a 192k "$2"
