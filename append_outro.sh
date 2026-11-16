#!/usr/bin/env bash
# Append the saved SIS ROSE outro, unchanged, to the end of a main video.
# Usage: ./append_outro.sh input.mp4 [output.mp4]
# The main video's picture, voice and narration are kept as they are. They are only
# re-encoded at high quality so they can be joined to the 1080x1920 / 30 fps / 48 kHz outro.
set -euo pipefail
IN="${1:?Usage: $0 input.mp4 [output.mp4]}"
OUT="${2:-${IN%.*}_WITH_OUTRO.mp4}"
DIR="$(cd "$(dirname "$0")" && pwd)"
OUTRO="$DIR/outro/SIS_ROSE_PINK_LUXURY_OUTRO.mp4"
[ -f "$OUTRO" ] || { echo "Missing $OUTRO"; exit 1; }

if ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 "$IN" | grep -q .; then
  AIN=(-i "$IN"); AMAP="[0:a:0]"
else   # main video has no sound: give it silence so the outro sound still plays
  DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$IN")
  AIN=(-f lavfi -t "$DUR" -i anullsrc=r=48000:cl=stereo); AMAP="[2:a]"
fi

ffmpeg -y -i "$IN" -i "$OUTRO" "${AIN[@]}" -filter_complex "
 [0:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,fps=30,format=yuv420p[v0];
 ${AMAP}aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[a0];
 [1:v]setsar=1,format=yuv420p[v1];[1:a]aformat=sample_fmts=fltp:channel_layouts=stereo[a1];
 [v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]" \
 -map "[v]" -map "[a]" -c:v libx264 -preset slow -crf 17 -c:a aac -b:a 192k -movflags +faststart "$OUT"
echo "Saved: $OUT"
