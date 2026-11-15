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
        that whisper heard in the cut, except the 3 words at either end of the film, unless assemble's audio graph
        rendered as two stems shows the voice MASK_DB over music+sfx at that word (then WARN: whisper misheard)
"""
import difflib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

import timeline
from cpu_budget import heavy_threads, low_priority
from progress import progress_file

W = str(Path(__file__).resolve().parent)  # whisper.cpp and the models live in the pipeline repo
SPEECH_DB = -40.0  # mean level of a said word in rough.mkv (speech measured -15..-25 dB, the cut-out pauses -51..-61 dB)
MASK_DB = 10.0  # voice over music+sfx at a said word; the misheard words of 2026-11-08 s02/s04 sat 25-38 dB above the bed
SR = 16000
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


REHEAR_MAX = 24  # short-window re-hearings a check (2-4 whisper passes each, ~10 s a pass: the 2026-11-14 long had 12 flags, 24 passes in 3:47); a run with more flags fails, it does not stall


def _whisper(media: str, timeout: int = 7200) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, "a.wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", media, "-vn", "-ac", "1", "-ar", "16000", wav], check=True, timeout=1800)
        # render_status reads the % for the widget; one file a run (cut and sound may hear the same media at once), and a
        # folder we cannot write only loses the %, never the check
        prog = progress_file(media, os.getpid())
        try:
            prog.parent.mkdir(parents=True, exist_ok=True)
            pf = prog.open("w")
        except OSError as e:
            print(f"words_check: no progress file {prog}: {e}", file=sys.stderr)
            pf = None
        try:
            subprocess.run([f"{W}/whisper.cpp/build/bin/whisper-cli", "-m", f"{W}/models/ggml-large-v3-q5_0.bin", "-l", "pl",
                            "-t", str(heavy_threads()), "-pp", "-otxt", "-of", os.path.join(tmp, "a"), wav],
                           stdout=subprocess.DEVNULL, stderr=pf or subprocess.DEVNULL, check=True, preexec_fn=low_priority, timeout=timeout)
        finally:
            if pf is not None:
                pf.close(); prog.unlink(missing_ok=True)
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
    for k in plan["keeps"]:  # [w0, w1] or [w0, w1, {"t0", "t1"}] (build_edl.py plan format)
        for i in range(k[0], k[1] + 1):
            w = words[i]; out += [(w["offsets"]["from"] / 1000, w["offsets"]["to"] / 1000)] * len(norm(w["text"]))
    return out


# a word start this far before a piece's in-point counts from the in-point: transcript starts run early (v5 s04 2026-11-10:
# "Claude" stamped 279.786 s, before "W" at 279.890 s, speech from 279.87 s, the piece from 279.814 s in silence)
WORD_LEAD = 0.15


def film_time(segments: list[dict], t: float, lead: float = 0.0) -> float | None:
    """film time of source time t: the piece that holds it (seg_exact lengths); a piece starting at most `lead` s after t
    gives its own start; None when t was cut out"""
    starts = timeline.starts(segments, True)
    for s, start in zip(segments, starts, strict=True):
        if s["in"] <= t <= s["out"]:
            return start + (t - s["in"])
    for s, start in zip(segments, starts, strict=True):
        if 0 < s["in"] - t <= lead:
            return start
    return None


def mean_db(media: str, t0: float, d: float) -> float | None:
    """mean level of media over [t0, t0+d]; None when ffmpeg gave no measurement (the caller keeps the word a problem)"""
    try:
        r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-ss", f"{t0:.3f}", "-t", f"{d:.3f}", "-i", media, "-vn",
                            "-af", "volumedetect", "-f", "null", "-"], capture_output=True, text=True, check=False, timeout=120)
    except (subprocess.TimeoutExpired, OSError) as e:  # hung or missing ffmpeg: no measurement, never a fake level
        print(f"words_check: volumedetect on {media} at {t0:.2f} s failed: {e}", file=sys.stderr)
        return None
    m = re.search(r"mean_volume: (-?[\d.]+) dB", r.stderr)
    if not m:
        print(f"words_check: no volumedetect on {media} at {t0:.2f} s: {r.stderr.strip().splitlines()[-1:]}", file=sys.stderr)
    return float(m.group(1)) if m else None


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
        f0, f1 = film_time(segments, times[i][0], WORD_LEAD), film_time(segments, times[i + len(gone) - 1][0], WORD_LEAD)
        if f0 is not None and f1 is not None and f1 < f0:  # word starts out of order in the transcript
            f0, f1 = f1, f0
        if f0 is None or f1 is None:
            still.append(line + " (cut out)")
            continue
        db = mean_db(rough, f0, max(f1 - f0, 0.0) + 0.3)
        if db is None:
            still.append(line + f" (level at {f0:.2f} s not measured, see the ffmpeg line above)")
        elif db > SPEECH_DB:
            kept.append(f"{line} (whisper did not hear it; kept in the cut at {f0:.2f} s, speech {db:.1f} dB)")
        else:
            still.append(line + f" (silence at {f0:.2f} s: {db:.1f} dB)")
    return still, kept


def stems(args_json: Path) -> tuple[np.ndarray, np.ndarray] | None:
    """the voice and the bed (ducked music + sfx) of the finished film, rendered apart by assemble's own audio graph
    (assemble.audio.args.json): the mix is exactly voice + bed, so their ratio says if a word is still audible.
    None when the graph is not the known shape or ffmpeg fails (then nothing is confirmed)."""
    try:
        cmd = json.loads(args_json.read_text(encoding="utf-8"))["audio"]
        i = cmd.index("-filter_complex")
    except (OSError, ValueError, KeyError) as e:
        print(f"words_check: no audio graph in {args_json}: {e}", file=sys.stderr); return None
    head, _, tail = cmd[i + 1].rpartition(";")
    if not tail.startswith("[vm][mud][sx]amix"):
        print(f"words_check: unknown mix in {args_json}: {tail[:60]}", file=sys.stderr); return None
    graph = head + ";[mud][sx]amix=inputs=2:normalize=0:duration=first[bg]"
    with tempfile.TemporaryDirectory() as tmp:
        v, bg = os.path.join(tmp, "v.raw"), os.path.join(tmp, "b.raw")
        out = ["-ac", "1", "-ar", str(SR), "-f", "f32le"]
        try:
            subprocess.run([*cmd[:i], "-filter_complex", graph, "-map", "[vm]", *out, v, "-map", "[bg]", *out, bg],
                           capture_output=True, check=True, preexec_fn=low_priority, timeout=1800)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as e:
            print(f"words_check: stems of {args_json} failed: {e}", file=sys.stderr); return None
        a, b = np.fromfile(v, np.float32), np.fromfile(bg, np.float32)
    n = min(len(a), len(b))
    return a[:n], b[:n]


def _db(x: np.ndarray) -> float:
    return float(10 * np.log10(np.mean(x.astype(np.float64) ** 2) + 1e-12))


def voice_over_bed(voice: np.ndarray, bed: np.ndarray, t0: float, t1: float) -> float | None:
    """lowest voice-minus-bed level (dB) over the 0.3 s windows of [t0, t1] that hold speech; None when none do"""
    w, h, lows = int(0.3 * SR), int(0.05 * SR), []
    for s in range(int(t0 * SR), max(int(t1 * SR) - w, int(t0 * SR)) + 1, h):
        vv, bb = voice[s:s + w], bed[s:s + w]
        if len(vv) == w and _db(vv) > -35:
            lows.append(_db(vv) - _db(bb))
    return min(lows) if lows else None


def locate(expected: list[str], i: int, n: int, plan_toks: list[str], times: list[tuple[float, float]],
           segments: list[dict], max_span: float = 6.0) -> tuple[float, float] | None:
    """film time span of expected[i:i+n] (whisper's words of the cut, no times): from the start of the nearest word
    before it that the plan text shares to the start of the nearest shared word after it; None when unsure"""
    if len(times) != len(plan_toks):
        return None
    pairs = [(a + k, b + k) for a, b, size in difflib.SequenceMatcher(None, expected, plan_toks, autojunk=False).get_matching_blocks()
             for k in range(size)]
    before = [p for e, p in pairs if e < i]
    after = [p for e, p in pairs if e >= i + n]
    if not before or not after:
        return None
    # the nearest shared word may start in what the cut took out (a piece's edge moved past it): the next one out is taken
    # (2026-11-14 long, 640 s: "no place on the timeline" for a gap whose neighbour sat 0.1 s outside its piece)
    t0 = next((t for p in reversed(before[-NEAR:]) if (t := film_time(segments, times[p][0])) is not None), None)
    t1 = next((t for p in after[:NEAR] if (t := film_time(segments, times[p][0])) is not None), None)
    if t0 is None or t1 is None or not 0 < t1 - t0 <= max_span:
        return None
    return t0, t1 + 0.3


def _whisper_window(media: str, t0: float, d: float) -> list[str] | None:
    """whisper's words of media over [t0, t0+d] alone; None when it could not run"""
    with tempfile.TemporaryDirectory() as tmp:
        clip = os.path.join(tmp, "w.wav")
        try:
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t0:.3f}", "-t", f"{d:.3f}", "-i", media, "-vn", "-ac", "1",
                            "-ar", "16000", clip], check=True, timeout=300)
            return _whisper(clip, timeout=600)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as e:
            print(f"words_check: no short-window whisper of {media} at {t0:.2f} s: {e}", file=sys.stderr)
            return None


NEAR = 4  # shared words each side of a gap that may place it on the timeline
LEADS = (1.0, 2.5, 1.5)  # s of film before the gap in each short window; whisper drops a weak word in one window and hears it in the next


def reheard(gone: list[str], around: list[str], rough: str, final: str, t0: float, t1: float) -> str | None:
    """the last word on a flag: whisper the same short window of the cut and of the film. The words around the gap
    (around) must be heard in the film's window, so the window sits on the right place; then the same words in both,
    or the missing words heard in the film = whisper misheard the whole film (2026-11-08 long: "to jest to co się
    dzieje" at 443 s was not in the cut's own window either; the outro read the same word for word in both).
    Whole long 2026-11-14 (1078 s, 12 flags): whisper over the whole film dropped 57 words; the film's short window
    heard as many of them as the cut's in 10 places ("haczyk co ja lubię..." 27 of 28 against 26 of 28: one window is
    never word for word the other), and lost one filler in two ("no" at 230 s, "mam" at 640 s) that a window starting
    1.5 s earlier heard; with the music 5 dB lower "mam" stayed lost, without any music "no" was lost. So a word counts
    as heard when any of the film's windows (LEADS) has it, and the film must hear as many of the missing words as the
    cut's own window does (whisper rewords a long gap: "co ja lubię" / "który lubię"); the words the film's windows do
    not have are named for Kamil's ear (ADR-0021).
    Returns which evidence held, for the WARN line; None = no proof."""
    a = _whisper_window(rough, max(t0 - LEADS[0], 0.0), t1 - t0 + LEADS[0] + 1.0)
    if a is None or not around: return None
    heard: set[str] = set(); placed = False
    for lead in LEADS:
        b = _whisper_window(final, max(t0 - lead, 0.0), t1 - t0 + lead + 1.0)
        if b is None: return None
        placed = placed or all(w in b for w in around)
        if lead == LEADS[0] and a == b: return "missing in both short windows of the cut and the film: listen" if placed else None
        heard |= set(b)
        if placed and all(w in heard for w in gone): return "heard in the film's short window"
    in_cut, in_film = sum(w in a for w in gone), sum(w in heard for w in gone)
    # a long gap: one word in ten may be misheard, not lost ("z AI" read "za jaj" in every window of the film at 569 s, the
    # 28-word gap of the 2026-11-14 long: 26 in the film's windows against 27 in the cut's); under ten words: none
    if not placed or in_film < in_cut - len(gone) // 10: return None
    weak = [w for w in gone if w not in heard]
    return f"the film's short windows hear {in_film} of the {len(gone)} words, the cut's own {in_cut}; not in the film's: {' '.join(weak)}: listen"


def confirm_audible(bad: list[str], expected: list[str], heard: list[str], loc: dict, args_json: Path,
                    rough: str = "", final: str = "") -> tuple[list[str], list[str]]:
    """sound mode: a word whisper heard in the cut but not in the film is kept when the voice there is MASK_DB over the
    music and sfx (2026-11-08 s02 "no" 28 dB over the bed, s04 English words 25 dB: mishearings, not losses).
    Problems that stay: no place on the timeline, no stems, or a bed within MASK_DB of the voice."""
    st = stems(args_json)
    if st is None:
        return bad, []
    still, kept, reheard_n = [], [], 0
    for i, gone, _ in missing(expected, heard):
        line = next((x for x in bad if x.startswith(f"missing: {context(expected, i, len(gone))} ")), None)
        if line is None:
            continue
        span = (locate(expected, i, len(gone), loc["toks"], loc["times"], loc["segments"])
                or locate(expected, i, len(gone), loc["toks"], loc["times"], loc["segments"], max_span=30.0))
        snr = voice_over_bed(*st, *span) if span else None
        if span is None:
            still.append(line + " (no place on the timeline to measure)")
        elif snr is not None and snr >= MASK_DB:
            kept.append(f"{line} (whisper did not hear it; voice {snr:.1f} dB over the music at {span[0]:.2f} s)")
        elif snr is not None and rough and final and reheard_n >= REHEAR_MAX:
            still.append(line + f" (music within {snr:.1f} dB at {span[0]:.2f} s; not re-heard: over {REHEAR_MAX} flags)")
        elif snr is not None and rough and final:
            reheard_n += 1  # counts every attempt, a heard one too: the budget is whisper time
            why = reheard(gone, expected[max(0, i - 2):i] + expected[i + len(gone):i + len(gone) + 2], rough, final, *span)
            if why:
                kept.append(f"{line} ({why} at {span[0]:.2f} s; music within {snr:.1f} dB)")
            else:
                still.append(line + f" (music within {snr:.1f} dB of the voice at {span[0]:.2f} s)")
        else:
            still.append(line + (f" (music within {snr:.1f} dB of the voice at {span[0]:.2f} s)" if snr is not None
                                 else f" (no speech to measure at {span[0]:.2f} s)"))
    return still, kept


def plan_times(edl_txt: Path) -> dict | None:
    """plan tokens, their source times and the EDL pieces next to edl_<n>.txt; None when a file is missing"""
    edl_json = edl_txt.with_suffix(".json")
    plan_p = edl_json.with_name(edl_json.name.replace("edl_", "plan_", 1))
    if not (edl_txt.exists() and edl_json.exists() and plan_p.exists()):
        return None
    plan = json.loads(plan_p.read_text(encoding="utf-8"))
    words = json.loads((plan_p.parent / plan["words"]).read_text(encoding="utf-8"))["transcription"]
    return {"toks": norm(edl_txt.read_text(encoding="utf-8")), "times": token_times(plan, words),
            "segments": json.loads(edl_json.read_text(encoding="utf-8"))["segments"]}


def preflight(edl_txt: Path) -> int:
    """read the plan the way cut and sound do when they confirm a flag (plan_times), so a plan they cannot read fails
    before the render, not after it: 1 when a file is missing or the plan's tokens do not line up with edl_<n>.txt"""
    loc = plan_times(edl_txt)
    if loc is None:
        print(f"words plan: FAIL no plan, EDL or words next to {edl_txt}"); return 1
    if len(loc["times"]) != len(loc["toks"]):
        print(f"words plan: FAIL {len(loc['toks'])} tokens in {edl_txt}, {len(loc['times'])} timed from the plan"); return 1
    print(f"words plan: {len(loc['toks'])} tokens timed, {len(loc['segments'])} pieces OK"); return 0


def main(argv: list[str]) -> int:
    out = None
    edl = None
    if "--json" in argv: i = argv.index("--json"); out = argv[i + 1]; argv = argv[:i] + argv[i + 2:]
    if "--edl" in argv: i = argv.index("--edl"); edl = argv[i + 1]; argv = argv[:i] + argv[i + 2:]
    if len(argv) == 2 and argv[0] == "plan":  # run_v4 before assemble: the code the checks run after the render, on this
        return preflight(Path(argv[1]))       # film's plan, in a second (2026-11-10: a 3-field keep crashed it after 50 min)
    if len(argv) != 3 or argv[0] not in ("cut", "sound"):
        print("usage: words_check.py cut <edl.txt> <rough.mkv> | sound <rough.mkv> <final.mp4> [--edl edl_<n>.txt] [--json out.json]",
              file=sys.stderr); return 2
    mode, a, b = argv
    expected = norm(Path(a).read_text(encoding="utf-8")) if mode == "cut" else transcribe(a)
    heard = transcribe(b)
    bad, warn = judge(mode, expected, heard)
    if mode == "cut" and bad:  # confirm against the sound: the plan says which source words are kept
        loc = plan_times(Path(a))
        if loc:
            bad, kept = confirm_kept(bad, expected, loc["times"], loc["segments"], b)
            warn += kept
    if mode == "sound" and bad:  # confirm against the mix: run_v4 runs in the work dir next to edl_<n>.txt
        loc = plan_times(Path(edl or f"edl_{Path(a).parent.name}.txt"))
        if loc:
            bad, kept = confirm_audible(bad, expected, heard, loc, Path(b).parent / "assemble.audio.args.json", a, b)
            warn += kept
    if out: Path(out).write_text(json.dumps({"mode": mode, "expected": len(expected), "heard": len(heard), "problems": bad, "warnings": warn}, ensure_ascii=False, indent=1), encoding="utf-8")
    for x in bad: print(x)
    for x in warn: print("WARN", x)
    print(f"words {mode}: expected {len(expected)}, heard {len(heard)}, {len(bad)} problems, {len(warn)} warnings" + ("" if bad else " OK"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
