#!/usr/bin/env bash
# Usage: phone_copy.sh <in.mp4> [out.mp4]
# Makes a small 720p copy for reviewing on your phone.
set -euo pipefail
out="${2:-${1%.*}-phone.mp4}"
ffmpeg -y -i "$1" -vf "scale=720:-2" -c:v libx264 -crf 26 -preset veryfast -c:a aac -b:a 128k "$out"
