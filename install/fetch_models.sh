#!/bin/bash
# install/fetch_models.sh -> models/ of this checkout: the whisper.cpp model, the YuNet face detector and the MediaPipe face
# landmarker. Each file is downloaded to <name>.part and kept only when its sha256 equals install/models.sha256
# (the hashes the publishers list: Hugging Face LFS, opencv_zoo LFS, frame_pick.LANDMARK_SHA). A file already in place with the
# right hash is not downloaded again. No sudo, nothing outside the checkout.
set -euo pipefail
VP="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SUMS="$VP/install/models.sha256"
mkdir -p "$VP/models"

get() {  # name url
  local name=$1 url=$2 f="$VP/models/$1" want
  want=$(awk -v n="$name" '$2 == n {print $1}' "$SUMS")
  [ -n "$want" ] || { echo "FAILED $name: no sha256 in $SUMS" >&2; exit 1; }
  if [ -f "$f" ] && echo "$want  $f" | sha256sum -c --status -; then echo "ok   $name (already there)"; return; fi
  echo "get  $name <- $url"
  curl -fL --retry 3 --proto '=https' -o "$f.part" "$url"
  if ! echo "$want  $f.part" | sha256sum -c --status -; then
    rm -f "$f.part"
    echo "FAILED $name: sha256 differs from $SUMS (file removed)" >&2; exit 1
  fi
  mv "$f.part" "$f"; echo "ok   $name"
}

get ggml-large-v3-q5_0.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-q5_0.bin
get face_detection_yunet_2023mar.onnx https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx
get face_landmarker.task https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task
