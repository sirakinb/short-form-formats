#!/usr/bin/env bash
# Usage: proxy.sh <take.mov> <out.mp4>
# iPhone HEVC footage can crash Remotion. This makes an H.264 proxy at 30 fps and lifts dark footage a little.
# Drop the eq filter if your footage is already bright.
set -euo pipefail
ffmpeg -y -i "$1" -vf "eq=gamma=1.35:contrast=1.08,format=yuv420p" -c:v libx264 -crf 18 -r 30 -c:a aac "$2"
