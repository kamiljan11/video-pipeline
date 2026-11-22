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
if [ -n "$v" ] && [ "$v" -ge 8 ]; then ok "ffmpeg $v"; else no "ffmpeg 8 or newer on PATH (found: ${v:-none})" "bash '$VP/install/ffmpeg.sh' && export PATH=\"\$HOME/.local/bin:\$PATH\""; fi
v=$(node -v 2>/dev/null | sed -nE 's/^v([0-9]+).*/\1/p')
if [ -n "$v" ] && [ "$v" -ge 24 ]; then ok "node $v"; else no "Node 24 (found: ${v:-none})" "https://nodejs.org (LTS 24)"; fi
if [ -x /usr/bin/google-chrome ]; then
  ok "google-chrome"
  # the renders launch Chrome with its sandbox on (gfx/webshot.mjs loads pages from the internet): it must start here
  prof=$(mktemp -d)  # a throwaway profile: the user's own Chrome profile is not touched
  chrome_err=$(timeout 60 /usr/bin/google-chrome --headless=new --disable-gpu --user-data-dir="$prof" --dump-dom about:blank 2>&1 >/dev/null); rc=$?
  find "$prof" -delete 2>/dev/null
  if [ $rc = 0 ]; then ok "google-chrome starts with its sandbox"
  elif [ "$(id -u)" = 0 ]; then no "a user that is not root (Chrome's sandbox refuses root)" "run the pipeline as a normal user"
  elif [ $rc = 124 ]; then no "Chrome to start (no answer in 60 s)" "run: google-chrome --headless=new --dump-dom about:blank, and read its error"
  elif grep -q -i -e "namespace" -e "setuid sandbox" <<<"$chrome_err"; then no "Chrome's sandbox (it cannot create namespaces)" "in Docker: docker run --security-opt seccomp=unconfined ...; on a host: allow unprivileged user namespaces (AppArmor)"
  else no "Chrome to start ($(tail -1 <<<"$chrome_err"))" "reinstall Google's .deb"; fi
else no "Google Chrome at /usr/bin/google-chrome" "Google's .deb from https://www.google.com/chrome/"; fi
# Chrome keeps its frame buffers in /dev/shm; Docker's default 64 MB makes parallel card screenshots fail now and then
shm=$(df -Pm /dev/shm 2>/dev/null | awk 'NR == 2 {print $2}')
if [ -n "$shm" ] && [ "$shm" -lt 512 ]; then opt "/dev/shm is ${shm} MB (renders can fail to capture)" "in Docker: docker run --shm-size=2g ..."; fi
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
