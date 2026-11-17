#!/bin/bash
# install/check.sh -> is this machine ready to run the pipeline? One line per requirement of README "Quick start":
# "ok", or "MISSING" with the command that fixes it. Installs nothing. Exit 1 when a required item is missing.
set -uo pipefail
VP="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
miss=0
case "$VP" in *[[:space:]]*) echo "MISSING a checkout path without spaces ($VP) -> clone it elsewhere (run_v4.sh refuses this path)"; miss=1;; esac
ok() { echo "ok      $1"; }
no() { echo "MISSING $1 -> $2"; miss=1; }
opt() { echo "option  $1 -> $2"; }

v=$(ffmpeg -version 2>/dev/null | sed -nE '1s/^ffmpeg version n?([0-9]+).*/\1/p')
if [ -n "$v" ] && [ "$v" -ge 8 ]; then ok "ffmpeg $v"; else no "ffmpeg 8 or newer (found: ${v:-none})" "README Quick start: a static 8.x build, Ubuntu 24.04 apt has 6.1"; fi
v=$(node -v 2>/dev/null | sed -nE 's/^v([0-9]+).*/\1/p')
if [ -n "$v" ] && [ "$v" -ge 24 ]; then ok "node $v"; else no "Node 24 (found: ${v:-none})" "https://nodejs.org (LTS 24)"; fi
if [ -x /usr/bin/google-chrome ]; then ok "google-chrome"; else no "Google Chrome at /usr/bin/google-chrome" "Google's .deb from https://www.google.com/chrome/"; fi
for t in pdftoppm:poppler-utils tesseract:tesseract-ocr; do
  if command -v "${t%%:*}" >/dev/null; then ok "${t%%:*}"; else no "${t%%:*}" "sudo apt install ${t##*:}"; fi
done
langs=$(tesseract --list-langs 2>/dev/null); fonts=$(fc-list : family 2>/dev/null)  # captured: grep -q in a pipe + pipefail = SIGPIPE
if grep -qx pol <<< "$langs"; then ok "tesseract pol"; else no "tesseract Polish data" "sudo apt install tesseract-ocr-pol"; fi
if grep -q 'Montserrat' <<< "$fonts"; then ok "font Montserrat (captions)"; else no "font Montserrat for captions" "mkdir -p ~/.local/share/fonts && cp '$VP/fonts/Montserrat-VF.ttf' ~/.local/share/fonts/ && fc-cache -f"; fi
if [ -f "$VP/node_modules/playwright-core/package.json" ]; then ok "node_modules"; else no "node_modules" "cd '$VP' && npm ci"; fi
if "$VP/.venv/bin/python" -c 'import cv2, numpy' 2>/dev/null; then ok ".venv ($("$VP/.venv/bin/python" -V))"
elif command -v python3.12 >/dev/null; then no ".venv with requirements.txt" "cd '$VP' && python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt"
else no "python3.12 for .venv" "sudo apt install python3.12-venv (CI tests on 3.12)"; fi
if [ -x "$VP/whisper.cpp/build/bin/whisper-cli" ]; then ok "whisper.cpp"; else no "whisper.cpp/build/bin/whisper-cli" "README: Postawienie od zera, step 4"; fi
while read -r sum name; do
  f="$VP/models/$name"
  if [ -f "$f" ] && echo "$sum  $f" | sha256sum -c --status -; then ok "models/$name"; else no "models/$name (or wrong sha256)" "bash '$VP/install/fetch_models.sh'"; fi
done < "$VP/install/models.sha256"
[ -n "${PEXELS_API_KEY:-}${Pexels:-}" ] && ok "PEXELS_API_KEY (b-roll)" || opt "PEXELS_API_KEY not set" "b-roll only; a free key from https://www.pexels.com/api/"
[ -x "$VP/matte/.venv/bin/python" ] && ok "matte/.venv (text behind the speaker)" || opt "matte/.venv not set up" "only for \"behind\" cards: README step 9"
echo; [ $miss = 0 ] && echo "ready" || echo "not ready: fix the MISSING lines above"
exit $miss
