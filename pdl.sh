#!/bin/bash
# parallel range download: pdl.sh URL OUT PARTS
URL="$1"; OUT="$2"; N="${3:-12}"
SIZE=$(curl -sIL "$URL" | grep -i '^content-length' | tail -1 | tr -dc '0-9')
CH=$(( (SIZE + N - 1) / N ))
mkdir -p "$OUT.parts"
for i in $(seq 0 $((N-1))); do
  S=$((i*CH)); E=$((S+CH-1)); [ $E -ge $SIZE ] && E=$((SIZE-1))
  ( until [ -f "$OUT.parts/$i.done" ]; do
      curl -sfL --retry 5 -r $S-$E -o "$OUT.parts/$i" "$URL" && [ $(stat -c%s "$OUT.parts/$i") -eq $((E-S+1)) ] && touch "$OUT.parts/$i.done"
    done ) &
done
wait
cat $(for i in $(seq 0 $((N-1))); do echo "$OUT.parts/$i"; done) > "$OUT"
[ $(stat -c%s "$OUT") -eq $SIZE ] && rm -rf "$OUT.parts" && echo "DONE $SIZE"
