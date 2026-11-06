#!/usr/bin/env bash
# Rebuild the cinematic dakwah video from the original recording.
# usage: ./build.sh path/to/VID_20261106_100640_100.mp4 [out_dir]
set -euo pipefail
SRC="$1"; OUT="${2:-out}"; HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$OUT"
python3 "$HERE/render.py" "$SRC" "$OUT/video_only.mp4"
python3 "$HERE/audio.py" "$SRC" "$OUT/sfx_cues.txt" "$OUT/mix.wav"
python3 "$HERE/audio.py" "$SRC" "$OUT/sfx_cues.txt" "$OUT/mix_nomusic.wav" --no-music
# two-pass delivery encode (~5.8 Mbps: upload-ready, keeps file < 100 MB)
ffmpeg -v error -y -i "$OUT/video_only.mp4" -c:v libx264 -preset slow -b:v 5800k -pass 1 \
  -passlogfile "$OUT/x264" -pix_fmt yuv420p -an -f mp4 /dev/null
ffmpeg -v error -y -i "$OUT/video_only.mp4" -c:v libx264 -preset slow -b:v 5800k -maxrate 9000k \
  -bufsize 13000k -pass 2 -passlogfile "$OUT/x264" -pix_fmt yuv420p -profile:v high -level 4.1 \
  -an "$OUT/video_delivery.mp4"
for v in "" _tanpa_muzik; do
  A="$OUT/mix.wav"; [ -n "$v" ] && A="$OUT/mix_nomusic.wav"
  ffmpeg -v error -y -i "$OUT/video_delivery.mp4" -i "$A" -map 0:v -map 1:a -c:v copy \
    -af "loudnorm=I=-14:TP=-1.5:LRA=9" -c:a aac -b:a 192k -ar 48000 -shortest \
    -movflags +faststart "$OUT/dakwah_zawiyah_an_nur_9x16${v}.mp4"
done
echo "done -> $OUT"
