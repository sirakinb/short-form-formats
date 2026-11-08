#!/usr/bin/env bash
# Usage: make_strip.sh <video> <out.jpg> [frames=5]
# Pulls evenly spaced frames (skipping the first and last 8%) and lays them side by side, 216 px wide each.
set -euo pipefail
v="$1"; out="$2"; n="${3:-5}"
d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$v")
tmp=$(mktemp -d)
inputs=()
for i in $(seq 0 $((n-1))); do
  t=$(python3 -c "print(round($d*(0.08+0.84*$i/($n-1)),2))")
  ffmpeg -v error -y -ss "$t" -i "$v" -frames:v 1 -vf "scale=216:384:force_original_aspect_ratio=decrease,pad=216:384:(ow-iw)/2:(oh-ih)/2:black" "$tmp/f$i.png"
  inputs+=(-i "$tmp/f$i.png")
done
ffmpeg -v error -y "${inputs[@]}" -filter_complex "hstack=inputs=$n" -q:v 4 "$out"
rm -rf "$tmp"
