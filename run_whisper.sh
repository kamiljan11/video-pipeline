#!/bin/bash
# run_whisper.sh WORKDIR  -> word-level JSON per wav (whisper.cpp, CPU)
W=/home/kamil-jan/video-pipeline
cd "$1"
for f in $(ls -S -r *.wav); do
  b="${f%.wav}"
  [ -f "$b.words.json" ] && continue
  T=$(date +%s)
  $W/whisper.cpp/build/bin/whisper-cli -m $W/models/ggml-large-v3-q5_0.bin -l pl -t 30 \
    -ml 1 -sow -oj -of "$b.words" --prompt "Yyy, eee, no więc, tak jakby. Nagranie na YouTube." "$f" > "$b.whisper.log" 2>&1
  echo "$b $(( $(date +%s) - T ))s" >> whisper_times.log
done
echo ALL_DONE >> whisper_times.log
