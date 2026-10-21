#!/bin/bash
cd /home/kamil-jan/Videos/Montaz/2026-10-20/work
R=/home/kamil-jan/video-pipeline/render
F=../out/95procent_long.mp4
T=$(python3 -c "
import json
e=json.load(open('edl_long.json'));acc=0
for s in e['segments']:
    if s['in']<=465.0<=s['out']: print(round(acc+465.0-s['in'],2)); break
    acc+=s['out']-s['in']
")
echo "t=$T"
ffprobe -v error -show_entries format=duration -of csv=p=0 $F
ffmpeg -v error -y -ss $T -t 6 -i $F -ac 1 -ar 16000 $R/chk.wav
/home/kamil-jan/video-pipeline/whisper.cpp/build/bin/whisper-cli -m /home/kamil-jan/video-pipeline/models/ggml-large-v3-q5_0.bin -l pl -t 16 -nt $R/chk.wav 2>/dev/null
ffmpeg -i $F -af ebur128=peak=true:framelog=quiet -f null - 2>&1 | grep -E " I:| Peak:" | tail -2
for n in short1_95procent short2_cichy_bol short3_jedno_zlecenie short4_drugi_tydzien; do
  echo "$n $(ffmpeg -i ../out/$n.mp4 -af ebur128=framelog=quiet -f null - 2>&1 | grep ' I:' | tail -1)"
done
echo "== short4"; python3 /home/kamil-jan/video-pipeline/verify_cut.py edl_short4_drugi_tydzien.txt ../out/short4_drugi_tydzien.mp4
echo CHECK_DONE
