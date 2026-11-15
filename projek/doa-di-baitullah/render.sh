#!/usr/bin/env bash
# Render preview DOA DI BAITULLAH (9:16, tanpa muzik — muzik ditambah pengguna di TikTok).
# Guna: bash render.sh <folder_upload> <folder_kerja> <fail_output.mp4>
set -euo pipefail
UP=$1; WK=$2; OUTF=$3
HERE=$(cd "$(dirname "$0")" && pwd)
L=$WK/layers; SEG=$WK/seg; mkdir -p "$L" "$SEG"
python3 "$HERE/build_layers.py" "$UP" "$L" >/dev/null

C1=$UP/22198455-v1c044g50000dbstb9nog65ouvpjlr00.mp4   # Madinah, berniqab
C2=$UP/a214ae4c-87B6256F-FCF1-497E-8A0C-AFF2DC4A154A.mov # Kaabah malam
C3=$UP/d9d793f8-IMG_3891.mov                            # jemaah putih
C4=$UP/f5591c76-v14044g50000db3o4snog65osvlu7q9g.mov    # kebun kurma, wajah

GRADE="eq=contrast=1.04:saturation=0.93:gamma=0.98,colorbalance=rh=0.035:gh=0.015:bh=-0.035:rm=0.02:bm=-0.02,vignette=PI/5"
ENC="-an -c:v libx264 -preset medium -crf 17 -pix_fmt yuv420p -r 30"

zoom() { # $1=zoom amount $2=duration
  echo "scale=w='trunc(1080*(1+$1*t/$2)/2)*2':h='trunc(1920*(1+$1*t/$2)/2)*2':eval=frame:flags=bicubic,crop=1080:1920:(iw-1080)/2:(ih-1920)/2"
}
txt() { # $1=label in $2=start $3=end(fade-out start) $4=label out
  echo "[$1]format=rgba,fade=t=in:st=$2:d=0.9:alpha=1,fade=t=out:st=$3:d=0.7:alpha=1[$4]"
}

# seg <out> <src> <ss> <speed> <D> <prefilter> <zoom> <text-filtergraph-tail> [png...]
seg() {
  local out=$1 src=$2 ss=$3 sp=$4 D=$5 pre=$6 z=$7 tail=$8; shift 8
  local ins=() i=1
  for p in "$@"; do ins+=(-loop 1 -framerate 30 -t "$D" -i "$p"); done
  local srcdur; srcdur=$(python3 -c "print(round($D*$sp+0.2,3))")
  ffmpeg -v error -y -ss "$ss" -t "$srcdur" -i "$src" "${ins[@]}" -filter_complex \
    "[0:v]setpts=(PTS-STARTPTS)/$sp,fps=30,${pre}$(zoom "$z" "$D"),$GRADE,trim=duration=$D,setpts=PTS-STARTPTS[v0];$tail" \
    -map "[vout]" -t "$D" $ENC "$SEG/$out"
}

FIT="scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,"

# 1 — "Kalau selama ini…" (Madinah)
seg s1.mp4 "$C1" 0 0.92 7.0 "$FIT" 0.06 \
  "$(txt 1:v 0.9 6.0 a);[v0][a]overlay=0:'18*max(0,1-(t-0.9)/1.2)',fade=t=in:st=0:d=0.6[vout]" "$L/t1.png"
# 2 — "…di hadapan Kaabah?" (Kaabah malam)
seg s2.mp4 "$C2" 0 0.85 7.0 "$FIT" 0.12 \
  "$(txt 1:v 1.0 6.0 a);[v0][a]overlay=0:'18*max(0,1-(t-1.0)/1.2)'[vout]" "$L/t2.png"
# 3 — "Bawa segala…" ×3 (jemaah putih)
seg s3.mp4 "$C3" 0 0.92 7.5 "$FIT" 0.05 \
  "$(txt 1:v 0.9 6.5 a);$(txt 2:v 2.2 6.5 b);$(txt 3:v 3.5 6.5 c);[v0][a]overlay=0:'14*max(0,1-(t-0.9)/1.2)'[x1];[x1][b]overlay=0:'14*max(0,1-(t-2.2)/1.2)'[x2];[x2][c]overlay=0:'14*max(0,1-(t-3.5)/1.2)'[vout]" \
  "$L/t3_0.png" "$L/t3_1.png" "$L/t3_2.png"
# 4 — "…tetamu Allah." (kebun kurma → wajah)
seg s4.mp4 "$C4" 7.3 0.95 7.0 "$FIT unsharp=5:5:0.5," 0.04 \
  "$(txt 1:v 1.0 6.0 a);[v0][a]overlay=0:'18*max(0,1-(t-1.0)/1.2)'[vout]" "$L/t4.png"
# 5 — "JOM PERGI UMRAH ❤️" (Kaabah dizoom)
seg s5.mp4 "$C2" 4.2 0.85 4.5 "crop=675:1200:188:350,scale=1080:1920:flags=lanczos," 0.05 \
  "[1:v]format=rgba,fade=t=in:st=0.7:d=0.9:alpha=1[a];[v0][a]overlay=0:'16*max(0,1-(t-0.7)/1.2)'[vout]" "$L/t5.png"

# 6 — Branding 4 saat terakhir
D=4.8
el() { echo "[$1]format=rgba,fade=t=in:st=$2:d=0.7:alpha=1[$3]"; }
ffmpeg -v error -y -loop 1 -framerate 30 -t $D -i "$L/brand_bg.jpg" \
  -loop 1 -framerate 30 -t $D -i "$L/brand_portrait.png" \
  -loop 1 -framerate 30 -t $D -i "$L/brand_sis.png" \
  -loop 1 -framerate 30 -t $D -i "$L/brand_rose.png" \
  -loop 1 -framerate 30 -t $D -i "$L/brand_th.png" \
  -loop 1 -framerate 30 -t $D -i "$L/brand_line.png" \
  -loop 1 -framerate 30 -t $D -i "$L/brand_tag.png" \
  -loop 1 -framerate 30 -t $D -i "$L/brand_logo.png" -filter_complex "
[0:v]fps=30,$(zoom 0.05 $D),format=yuv420p[bg];
$(el 1:v 0.9 p);$(el 2:v 1.2 s);$(el 3:v 1.35 r);$(el 4:v 1.65 th);$(el 5:v 1.8 ln);$(el 6:v 2.0 tg);$(el 7:v 2.25 lg);
[bg][p]overlay=x='540+50*max(0,1-(t-0.9)/1.1)':y=470[b1];
[b1][s]overlay=x=28:y='600+14*max(0,1-(t-1.2)/1.0)'[b2];
[b2][r]overlay=x=28:y='725+14*max(0,1-(t-1.35)/1.0)'[b3];
[b3][th]overlay=x=30:y=890[b4];
[b4][ln]overlay=x=60:y=1000[b5];
[b5][tg]overlay=x=28:y=1010[b6];
[b6][lg]overlay=x=30:y=1170[vout]" -map "[vout]" -t $D $ENC "$SEG/s6.mp4"

# Cantum dengan crossfade lembut 0.8s
X=0.8
ffmpeg -v error -y -i "$SEG/s1.mp4" -i "$SEG/s2.mp4" -i "$SEG/s3.mp4" -i "$SEG/s4.mp4" -i "$SEG/s5.mp4" -i "$SEG/s6.mp4" \
  -f lavfi -t 40 -i anullsrc=r=48000:cl=stereo -filter_complex "
[0:v][1:v]xfade=transition=fade:duration=$X:offset=6.2[a];
[a][2:v]xfade=transition=fade:duration=$X:offset=12.4[b];
[b][3:v]xfade=transition=fade:duration=$X:offset=19.1[c];
[c][4:v]xfade=transition=fade:duration=$X:offset=25.3[d];
[d][5:v]xfade=transition=fade:duration=$X:offset=29.0,format=yuv420p[v]" \
  -map "[v]" -map 6:a -shortest -c:v libx264 -preset slow -crf 18 -profile:v high -pix_fmt yuv420p -r 30 \
  -c:a aac -b:a 128k -movflags +faststart "$OUTF"
echo "Siap: $OUTF"
