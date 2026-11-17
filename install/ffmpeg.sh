#!/bin/bash
# install/ffmpeg.sh [BIN_DIR]  -> ffmpeg and ffprobe 8.x (a static GPL build of FFmpeg-Builds) into BIN_DIR, default ~/.local/bin.
# Ubuntu 24.04 apt has ffmpeg 6.1, too old for the filters the render uses. The one place the version is pinned: CI runs this
# script too. The archive is kept only when its sha256 equals FFMPEG_SHA256 (from the release's checksums.sha256).
# Month-end autobuilds stay published; daily ones are pruned after ~2 weeks (2026-10-24 was, CI went 404).
set -euo pipefail
FFMPEG_RELEASE=autobuild-2026-10-31-12-59
FFMPEG_TAR=ffmpeg-n8.1.3-27-g8dca1586f4-linux64-gpl-8.1.tar.xz
FFMPEG_SHA256=41e9c565594c390622cf968d82fa4135d9e9a11d06c1515644288cbc844e3380
BIN=${1:-$HOME/.local/bin}
VERSION=${FFMPEG_TAR#ffmpeg-}; VERSION=${VERSION%%-linux64*}  # n8.1.3-27-g8dca1586f4, as "ffmpeg -version" prints it
if [ -x "$BIN/ffmpeg" ] && "$BIN/ffmpeg" -version 2>/dev/null | head -1 | grep -qF "version $VERSION "; then
  echo "ok   ffmpeg $VERSION already in $BIN"; exit 0
fi
[ "$(uname -m)" = x86_64 ] || { echo "FAILED: this build is for x86_64 Linux (found $(uname -m))" >&2; exit 1; }
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
URL="https://github.com/FFmpeg-Builds/FFmpeg-Builds/releases/download/$FFMPEG_RELEASE/$FFMPEG_TAR"
curl -fsSL --retry 3 --retry-all-errors --connect-timeout 20 --max-time 900 --proto '=https' -o "$tmp/$FFMPEG_TAR" "$URL" ||
  { echo "FAILED: download of $URL (a 404 = the build was taken down: pin a newer month-end build in install/ffmpeg.sh)" >&2; exit 1; }
echo "$FFMPEG_SHA256  $tmp/$FFMPEG_TAR" | sha256sum -c --quiet - ||
  { echo "FAILED: $FFMPEG_TAR does not match FFMPEG_SHA256 (corrupt or changed upstream; nothing installed)" >&2; exit 1; }
tar -xJf "$tmp/$FFMPEG_TAR" -C "$tmp"
mkdir -p "$BIN"
for b in ffmpeg ffprobe; do  # copy beside, then rename: a running render keeps its binary, an interrupted copy leaves none half-written
  cp "$tmp/${FFMPEG_TAR%.tar.xz}/bin/$b" "$BIN/.$b.new" && mv -f "$BIN/.$b.new" "$BIN/$b"
done
"$BIN/ffmpeg" -version | head -1
case ":$PATH:" in *":$BIN:"*) ;; *) echo "note: $BIN is not on PATH; add it before /usr/bin (export PATH=\"$BIN:\$PATH\")";; esac
