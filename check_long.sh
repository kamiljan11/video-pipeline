#!/bin/bash
cd /home/kamil-jan/Videos/Montaz/2026-10-20/work
R=/home/kamil-jan/video-pipeline/render; F=../out/95procent_long.mp4
TIMES=$(python3 -c "
import json
e=json.load(open('edl_long.json'));ts=[]
for o in e['overlays']:
    if o['id'] in ('g03_rules','g15_panel','g20_cta','g06_z1'): ts.append(o['at']+2.0)
acc=0
for s in e['segments']:
    z=s['zoom']
    if isinstance(z,dict) and z['t0']>0.01: ts.append(acc+z['t1']+0.3)
    acc+=s['out']-s['in']
print(' '.join(f'{t:.2f}' for t in sorted(ts)[:12]))
")
echo "$TIMES"
i=0; rm -f $R/lc_*.jpg
for t in $TIMES; do ffmpeg -v error -y -ss $t -i $F -frames:v 1 -vf scale=480:-1 $R/lc_$(printf %02d $i).jpg; i=$((i+1)); done
ffmpeg -v error -y -pattern_type glob -i "$R/lc_*.jpg" -vf tile=4x3 $R/longcheck3.jpg
ffprobe -v error -show_entries format=duration -of csv=p=0 $F
ffmpeg -i $F -af ebur128=peak=true:framelog=quiet -f null - 2>&1 | grep -E " I:| Peak:" | tail -2
ffmpeg -v error -y -ss 826 -t 6 -i $F -af ebur128=framelog=quiet -f null - 2>&1 | grep " I:" | tail -1
echo CHECK_DONE
