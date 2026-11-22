#!/bin/bash
# run_whisper.sh WORKDIR  -> word-level JSON per wav (whisper.cpp, CPU)
W="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"  # whisper.cpp/ and models/ live in the checkout
case "$W" in *[[:space:]]*) echo "FAILED: the checkout path has a space ($W); clone it to a path without spaces" >&2; exit 2;; esac
cd "$1" || { echo "FAILED: no work dir $1" >&2; exit 2; }
shopt -s nullglob; wavs=(*.wav)
[ ${#wavs[@]} -gt 0 ] || { echo "FAILED: no .wav in $1" >&2; exit 2; }
mapfile -t wavs < <(ls -S -r -- "${wavs[@]}")  # smallest first, as before
for f in "${wavs[@]}"; do
  b="${f%.wav}"
  [ -f "$b.words.json" ] && continue
  T=$(date +%s)
  nice -n 10 "$W/whisper.cpp/build/bin/whisper-cli" -m "$W/models/ggml-large-v3-q5_0.bin" -l pl -t "$(python3 "$W/cpu_budget.py")" \
    -ml 1 -sow -oj -of "$b.words" --prompt "Yyy, eee, no więc, tak jakby. Nagranie na YouTube." "$f" > "$b.whisper.log" 2>&1
  echo "$b $(( $(date +%s) - T ))s" >> whisper_times.log
done
echo ALL_DONE >> whisper_times.log
