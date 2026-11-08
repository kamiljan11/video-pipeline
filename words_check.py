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

import timeline
from cpu_budget import heavy_threads, low_priority

W = "/home/kamil-jan/video-pipeline"
SPEECH_DB = -40.0  # mean level of a said word in rough.mkv (speech measured -15..-25 dB, the cut-out pauses -51..-61 dB)
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


def token_times(plan: dict, words: list[dict]) -> list[tuple[float, float]]:
    """source (start, end) of every token of the plan text, in the order norm() reads edl_<n>.txt (build_edl joins the
    kept words' text); [] when the tokens do not line up one to one (then nothing is confirmed, the check stays as strict)"""
    out = []
    for a, b in plan["keeps"]:
        for i in range(a, b + 1):
            w = words[i]; out += [(w["offsets"]["from"] / 1000, w["offsets"]["to"] / 1000)] * len(norm(w["text"]))
    return out


def film_time(segments: list[dict], t: float) -> float | None:
    """film time of source time t: the piece that holds it (seg_exact lengths), None when t was cut out"""
    for s, start in zip(segments, timeline.starts(segments, True), strict=True):
        if s["in"] <= t <= s["out"]:
            return start + (t - s["in"])
    return None


def mean_db(media: str, t0: float, d: float) -> float:
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-ss", f"{t0:.3f}", "-t", f"{d:.3f}", "-i", media, "-vn",
                        "-af", "volumedetect", "-f", "null", "-"], capture_output=True, text=True, check=False, timeout=120)
    m = re.search(r"mean_volume: (-?[\d.]+) dB", r.stderr)
    return float(m.group(1)) if m else -99.0


def confirm_kept(bad: list[str], expected: list[str], times: list[tuple[float, float]], segments: list[dict], rough: str
                 ) -> tuple[list[str], list[str]]:
    """cut mode: a word whisper did not hear in rough.mkv is kept when its source time lies in a piece of the cut and
    rough.mkv has speech there (2026-11-08 long: 8 FAILs, all names and fillers whisper misheard; the pauses cut out
    around them were silence). Problems that stay: a word outside every piece, or silence where it should be."""
    if len(times) != len(expected):
        return bad, []
    still, kept = [], []
    for i, gone, _ in missing(expected, transcribe(rough)):
        line = next((x for x in bad if x.startswith(f"missing: {context(expected, i, len(gone))} ")), None)
        if line is None:
            continue
        # word starts only: the transcript's end times run late (2026-11-08 "Claude." ended 0.1 s after its piece, the
        # cut-out pause after it was silence, -60 dB)
        f0, f1 = film_time(segments, times[i][0]), film_time(segments, times[i + len(gone) - 1][0])
        db = mean_db(rough, f0, max(f1 - f0, 0.0) + 0.3) if f0 is not None and f1 is not None else None
        if db is not None and db > SPEECH_DB:
            kept.append(f"{line} (whisper did not hear it; kept in the cut at {f0:.2f} s, speech {db:.1f} dB)")
        else:
            still.append(line + (" (cut out)" if db is None else f" (silence at {f0:.2f} s: {db:.1f} dB)"))
    return still, kept


def main(argv: list[str]) -> int:
    out = None
    if "--json" in argv: i = argv.index("--json"); out = argv[i + 1]; argv = argv[:i] + argv[i + 2:]
    if len(argv) != 3 or argv[0] not in ("cut", "sound"):
        print("usage: words_check.py cut <edl.txt> <rough.mkv> | sound <rough.mkv> <final.mp4> [--json out.json]", file=sys.stderr); return 2
    mode, a, b = argv
    expected = norm(Path(a).read_text(encoding="utf-8")) if mode == "cut" else transcribe(a)
    heard = transcribe(b)
    bad, warn = judge(mode, expected, heard)
    edl_json = Path(a).with_suffix(".json")
    if mode == "cut" and bad and edl_json.exists():  # confirm against the sound: the plan says which source words are kept
        edl = json.loads(edl_json.read_text(encoding="utf-8"))
        plan_p = edl_json.with_name(edl_json.name.replace("edl_", "plan_", 1))
        if plan_p.exists():
            plan = json.loads(plan_p.read_text(encoding="utf-8"))
            words = json.loads((plan_p.parent / plan["words"]).read_text(encoding="utf-8"))["transcription"]
            bad, kept = confirm_kept(bad, expected, token_times(plan, words), edl["segments"], b)
            warn += kept
    if out: Path(out).write_text(json.dumps({"mode": mode, "expected": len(expected), "heard": len(heard), "problems": bad, "warnings": warn}, ensure_ascii=False, indent=1), encoding="utf-8")
    for x in bad: print(x)
    for x in warn: print("WARN", x)
    print(f"words {mode}: expected {len(expected)}, heard {len(heard)}, {len(bad)} problems, {len(warn)} warnings" + ("" if bad else " OK"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
