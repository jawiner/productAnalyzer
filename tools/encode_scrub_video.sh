#!/usr/bin/env bash
# Encode a generated clip for scroll-scrubbing (frame-accurate seeking) and
# extract exact first-frame posters. Adapted from Higgsfield's scroll-scrub helper.
#   bash tools/encode_scrub_video.sh desktop <in.mp4> <out.mp4>   # native res, GOP 8
#   bash tools/encode_scrub_video.sh mobile  <in.mp4> <out.mp4>   # <=720p, GOP 4
#   bash tools/encode_scrub_video.sh poster  <in.mp4> <out.jpg>   # exact first frame
#   bash tools/encode_scrub_video.sh last    <in.mp4> <out.jpg>   # exact last frame
set -euo pipefail
[ "$#" -eq 3 ] || { echo "usage: $0 desktop|mobile|poster|last <in> <out>" >&2; exit 2; }
action=$1; input=$2; output=$3
[ -f "$input" ] || { echo "missing input $input" >&2; exit 2; }
mkdir -p "$(dirname "$output")"
case "$action" in
  desktop)
    ffmpeg -v error -y -i "$input" -an -vf "unsharp=5:5:0.6:5:5:0.0" \
      -c:v libx264 -preset slow -crf 20 -pix_fmt yuv420p \
      -g 8 -keyint_min 8 -sc_threshold 0 -movflags +faststart "$output" ;;
  mobile)
    ffmpeg -v error -y -i "$input" -an -vf "scale=-2:'min(720,ih)',unsharp=5:5:0.5:5:5:0.0" \
      -c:v libx264 -preset slow -crf 23 -pix_fmt yuv420p \
      -g 4 -keyint_min 4 -sc_threshold 0 -movflags +faststart "$output" ;;
  poster)
    ffmpeg -v error -y -ss 0 -i "$input" -frames:v 1 -q:v 2 "$output" ;;
  last)
    ffmpeg -v error -y -i "$input" -vf reverse -frames:v 1 -q:v 2 "$output" ;;
  *) echo "unknown action $action" >&2; exit 2 ;;
esac
echo "wrote $output ($(du -k "$output" | cut -f1) KB)"
