#!/usr/bin/env python3
"""words_check: no word of the speaker lost on the way to the finished film.

    python3 words_check.py cut <edl.txt> <rough.mkv>       the plan's kept words vs what whisper hears in the cut
    python3 words_check.py sound <rough.mkv> <final.mp4>   the cut vs the finished film (voice chain, mix, mux)
    [--json out.json]

Kamil, many times (latest 2026-11-08 "0:04 uciales moje gadanie ... juz ktorys raz ci zglaszam"): words cut at the
edges or eaten later. Film 2026-11-04 long lost "Przez" (0.65 s dropped in stage 2) and "I" of "I wtedy" (the noise
gate); verify_cut.py flagged only runs of 2+ words and ran by hand. Here:
  cut   (plan text vs whisper of rough.mkv): whisper also mishears, so FAIL = a run of >= 2 missing words or one
        missing word of >= 4 letters; shorter single words = WARN
  sound (whisper of rough vs whisper of final, the same model on nearly the same sound): FAIL = any missing word
        that whisper heard in the cut, except the 3 words at either end of the film
"""
import difflib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from cpu_budget import heavy_threads, low_priority

W = "/home/kamil-jan/video-pipeline"
WORD = re.compile(r"[a-ząćęłńóśźż0-9%]+")


def norm(text: str) -> list[str]:
    return WORD.findall(text.lower())


def transcribe(media: str) -> list[str]:
    """whisper's words of a film; cached next to it as <media>.heard.txt keyed by size and mtime (cut + sound read the same rough)"""
    st = os.stat(media); key = f"{st.st_size}:{int(st.st_mtime)}"
    cache = Path(media + ".heard.txt")
    if cache.exists():
        head, _, body = cache.read_text(encoding="utf-8").partition("\n")
        if head == key: return body.split()
    words = _whisper(media)
    try: cache.write_text(key + "\n" + " ".join(words), encoding="utf-8")
    except OSError as e: print(f"words_check: no cache for {media}: {e}", file=sys.stderr)
    return words


def _whisper(media: str) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, "a.wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", media, "-vn", "-ac", "1", "-ar", "16000", wav], check=True, timeout=1800)
        subprocess.run([f"{W}/whisper.cpp/build/bin/whisper-cli", "-m", f"{W}/models/ggml-large-v3-q5_0.bin", "-l", "pl",
                        "-t", str(heavy_threads()), "-otxt", "-of", os.path.join(tmp, "a"), wav],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, preexec_fn=low_priority, timeout=7200)
        return norm(Path(tmp, "a.txt").read_text(encoding="utf-8"))


def missing(expected: list[str], heard: list[str]) -> list[tuple[int, list[str], list[str]]]:
    """(index in expected, missing words, what was heard there instead) for every gap"""
    out = []
    for op, a1, a2, b1, b2 in difflib.SequenceMatcher(None, expected, heard, autojunk=False).get_opcodes():
        # the same letters split another way ("nie sprawdzone" / "niesprawdzone", 2026-11-08 s04) is not a lost word
        if op == "replace" and "".join(expected[a1:a2]) == "".join(heard[b1:b2]):
            continue
        if op == "delete" or (op == "replace" and a2 - a1 > b2 - b1):
            out.append((a1, expected[a1:a2], heard[b1:b2]))
    return out


def context(words: list[str], i: int, n: int) -> str:
    return f"{' '.join(words[max(0, i - 4):i])} [[{' '.join(words[i:i + n])}]] {' '.join(words[i + n:i + n + 4])}"


def judge(mode: str, expected: list[str], heard: list[str]) -> tuple[list[str], list[str]]:
    bad, warn = [], []
    for i, gone, instead in missing(expected, heard):
        line = f"missing: {context(expected, i, len(gone))} | heard: {' '.join(instead) or '-'}"
        if mode == "sound":
            if i < 3 or i + len(gone) > len(expected) - 3: warn.append(line + " (film edge)")
            else: bad.append(line)
        elif len(gone) >= 2 or any(len(w) >= 4 for w in gone): bad.append(line)
        else: warn.append(line)
    return bad, warn


def main(argv: list[str]) -> int:
    out = None
    if "--json" in argv: i = argv.index("--json"); out = argv[i + 1]; argv = argv[:i] + argv[i + 2:]
    if len(argv) != 3 or argv[0] not in ("cut", "sound"):
        print("usage: words_check.py cut <edl.txt> <rough.mkv> | sound <rough.mkv> <final.mp4> [--json out.json]", file=sys.stderr); return 2
    mode, a, b = argv
    expected = norm(Path(a).read_text(encoding="utf-8")) if mode == "cut" else transcribe(a)
    heard = transcribe(b)
    bad, warn = judge(mode, expected, heard)
    if out: Path(out).write_text(json.dumps({"mode": mode, "expected": len(expected), "heard": len(heard), "problems": bad, "warnings": warn}, ensure_ascii=False, indent=1), encoding="utf-8")
    for x in bad: print(x)
    for x in warn: print("WARN", x)
    print(f"words {mode}: expected {len(expected)}, heard {len(heard)}, {len(bad)} problems, {len(warn)} warnings" + ("" if bad else " OK"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
