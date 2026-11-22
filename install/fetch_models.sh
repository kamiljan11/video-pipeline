#!/bin/bash
# install/fetch_models.sh -> models/ of this checkout: the whisper.cpp model, the YuNet face detector and the MediaPipe face
# landmarker. Each file is downloaded to <name>.part and kept only when its sha256 equals install/models.sha256
# (the hashes the publishers list: Hugging Face LFS, opencv_zoo LFS, frame_pick.LANDMARK_SHA). A file already in place with the
# right hash is not downloaded again. No sudo, nothing outside the checkout.
# --check-urls: only ask each URL whether it is still there (CI: an upstream move shows up before a stranger meets it).
set -euo pipefail
CHECK=0; [ "${1:-}" = --check-urls ] && CHECK=1
VP="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SUMS="$VP/install/models.sha256"
mkdir -p "$VP/models"

get() {  # name url
  local name=$1 url=$2 f="$VP/models/$1" want
  want=$(awk -v n="$name" '$2 == n {print $1}' "$SUMS")
  [ -n "$want" ] || { echo "FAILED $name: no sha256 in $SUMS" >&2; exit 1; }
  if [ $CHECK = 1 ]; then
    curl -fsSIL --retry 3 --retry-all-errors --connect-timeout 20 --max-time 120 --proto '=https' -o /dev/null "$url" ||
      { echo "FAILED $name: $url does not answer (moved upstream? update the URL in install/fetch_models.sh)" >&2; exit 1; }
    echo "ok   $name url"; return
  fi
  if [ -f "$f" ] && echo "$want  $f" | sha256sum -c --status -; then echo "ok   $name (already there)"; return; fi
  echo "get  $name <- $url"
  # -C -: an interrupted download resumes; the sha256 below decides, never the size
  dl() { curl -fL --retry 3 --retry-all-errors --connect-timeout 20 --max-time 7200 --proto '=https' "$@" -o "$f.part" "$url"; }
  good() { echo "$want  $f.part" | sha256sum -c --status -; }
  fail() { echo "FAILED $name: $1" >&2; exit 1; }
  local nodl="download of $url (network, disk space, or moved upstream: bash install/fetch_models.sh --check-urls)"
  if [ -f "$f.part" ]; then  # resume an interrupted download; one that does not end with the right hash starts over once
    if dl -C - && good; then mv "$f.part" "$f"; echo "ok   $name"; return; fi
    rm -f "$f.part"; echo "     $name: the partial download did not resume cleanly, starting over"
  fi
  dl || fail "$nodl"
  good || { rm -f "$f.part"; fail "sha256 differs from $SUMS (corrupt or changed upstream; the download was removed)"; }
  mv "$f.part" "$f"; echo "ok   $name"
}

get ggml-large-v3-q5_0.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-q5_0.bin
get face_detection_yunet_2023mar.onnx https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx
get face_landmarker.task https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task
