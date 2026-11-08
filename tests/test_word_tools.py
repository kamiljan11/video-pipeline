"""words_check (lost words) and word_times (word starts on the voice): the pure parts, no whisper run.
Film 2026-11-04: "Przez" and "I" lost in the long; whisper word starts up to 1.07 s off the voice."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import word_times as T
import words_check as C


def w(text: str, s: int, e: int) -> dict:
    return {"offsets": {"from": s, "to": e}, "text": f" {text}"}


class WordsCheckTest(unittest.TestCase):
    EXP = C.norm("Dzisiaj muszę się przyznać. Przez długi czas wstydziłem się. I wtedy zmieniłem pytanie, już nie czy wypada")

    def test_sound_mode_fails_on_any_lost_word_inside_the_film(self):
        heard = [x for x in self.EXP if x not in ("przez", "i")]
        bad, _ = C.judge("sound", self.EXP, heard)
        self.assertEqual(len(bad), 2, bad)
        self.assertTrue(any("[[przez]]" in b for b in bad) and any("[[i]]" in b for b in bad), bad)

    def test_sound_mode_only_warns_at_the_film_edges(self):
        bad, warn = C.judge("sound", self.EXP, self.EXP[1:])
        self.assertEqual(bad, [])
        self.assertTrue(warn and "film edge" in warn[0])

    def test_cut_mode_tolerates_short_single_mishearings(self):
        heard = [x for x in self.EXP if x != "i"]
        self.assertEqual(C.judge("cut", self.EXP, heard)[0], [])  # "i" alone: WARN, whisper drops it by itself
        heard = [x for x in self.EXP if x != "przez"]
        self.assertTrue(C.judge("cut", self.EXP, heard)[0])  # a 5-letter word gone: FAIL
        heard = [x for x in self.EXP if x not in ("już", "nie")]
        self.assertTrue(C.judge("cut", self.EXP, heard)[0])  # 2 in a row: FAIL

    def test_identical_text_passes(self):
        self.assertEqual(C.judge("sound", self.EXP, list(self.EXP)), ([], []))

    def test_the_same_letters_split_another_way_is_not_lost(self):  # 2026-11-08 s04: "nie sprawdzone" heard "niesprawdzone"
        exp = C.norm("to jest kod nie sprawdzone i jest też napisane dalej")
        heard = C.norm("to jest kod niesprawdzone i jest też napisane dalej")
        self.assertEqual(C.judge("cut", exp, heard), ([], []))
        self.assertEqual(C.judge("cut", heard, exp), ([], []))  # and joined in the plan, split by whisper
        lost = C.norm("to jest kod sprawdzone i jest też napisane dalej")  # a real loss still fails
        self.assertTrue(C.judge("sound", exp, lost)[0])  # "nie" really gone inside the film: still a FAIL


class WordTimesTest(unittest.TestCase):
    def test_dtw_start_reads_the_first_real_token(self):
        item = {"tokens": [{"text": "[_BEG_]", "t_dtw": 0}, {"text": " Pr", "t_dtw": 932}, {"text": "ze", "t_dtw": 940}]}
        self.assertEqual(T.dtw_start_ms(item), 9320)
        self.assertIsNone(T.dtw_start_ms({"tokens": [{"text": " Pr", "t_dtw": -1}]}))

    def test_transfer_keeps_hand_fixed_text_and_takes_matching_starts(self):
        words = [w("Dzisiaj", 1000, 1400), w("Halloweenowo", 1600, 6480), w("muszę", 6500, 6800)]
        dtw = [w("dzisiaj", 1050, 1400), w("Halloween", 1700, 2300), w("owo", 2300, 2700), w("muszę", 2900, 3200)]
        moved = T.transfer(words, dtw)
        self.assertEqual([x["text"] for x in words], [" Dzisiaj", " Halloweenowo", " muszę"])  # text untouched
        self.assertEqual(words[0]["offsets"]["from"], 1050)
        self.assertEqual(words[1]["offsets"]["from"], 1600)  # no match: kept
        self.assertEqual(words[2]["offsets"]["from"], 6500)  # matched but 3.6 s away: another occurrence, kept
        self.assertEqual(moved, 1)

    def test_snap_moves_a_start_after_a_pause_onto_the_onset_only(self):
        words = [w("a", 1000, 1500), w("b", 2200, 2600), w("c", 2620, 2900)]
        n = T.snap(words, np.array([1.98, 2.64]))
        self.assertEqual(words[1]["offsets"]["from"], 1980)  # after a 0.7 s pause, onset 0.22 s earlier: snapped
        self.assertEqual(words[2]["offsets"]["from"], 2620)  # inside the phrase: left alone
        self.assertEqual(n, 1)

    def test_onsets_and_error_on_a_synthetic_voice(self):
        sr = 16000
        a = np.zeros(sr * 3, np.int16)
        for t0 in (0.5, 1.6):
            a[int(t0 * sr):int((t0 + 0.4) * sr)] = (8000 * np.sin(np.arange(int(0.4 * sr)) * 2 * np.pi * 200 / sr)).astype(np.int16)
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "v.wav"
            with wave.open(str(f), "wb") as wf:
                wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes(a.tobytes())
            on = T.onsets(str(f))
            self.assertEqual([round(x, 2) for x in on], [0.5, 1.6])
            e = T.error([w("x", 700, 900), w("y", 1600, 1900)], on)
            self.assertEqual((e["n"], e["over_150ms_pct"]), (2, 50.0))




SEGS = ({"in": 10.0, "out": 12.0}, {"in": 20.0, "out": 22.0}, {"in": 30.0, "out": 31.0})  # film 0-2, 2-4, 4-5 s


class ConfirmKeptTest(unittest.TestCase):
    """cut mode confirms a word whisper did not hear against rough.mkv: speech at its film time = kept (WARN), silence or
    a source time outside every piece = still a problem (2026-11-08 long: 8 misheard names and fillers)"""

    def test_film_time_through_the_pieces(self):
        self.assertEqual(C.film_time(list(SEGS), 10.5), 0.5)
        self.assertEqual(C.film_time(list(SEGS), 21.0), 3.0)
        self.assertIsNone(C.film_time(list(SEGS), 15.0))  # cut out

    def test_token_times_follow_norm(self):
        words = [{"text": " Ala", "offsets": {"from": 10000, "to": 10300}}, {"text": " kamiljan.com", "offsets": {"from": 10400, "to": 11000}}]
        self.assertEqual(C.token_times({"keeps": [[0, 1]]}, words), [(10.0, 10.3), (10.4, 11.0), (10.4, 11.0)])

    @unittest.skipUnless(shutil.which("ffmpeg"), "no ffmpeg")
    def test_speech_kept_silence_and_cut_out_stay(self):
        d = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, d)
        rough = f"{d}/rough.wav"  # film 0-2 s a loud tone (speech), 2-5 s silence
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "sine=f=300:d=2", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
                        "-filter_complex", "[1:a]atrim=0:3[s];[0:a][s]concat=n=2:v=0:a=1", rough], check=True)
        exp = ["aa", "bb", "cc", "dd"]
        times = [(10.2, 10.4), (10.8, 11.0), (20.5, 20.7), (15.0, 15.2)]  # bb in the tone, cc in the silence, dd cut out
        real = C.transcribe
        try:
            for gone, want in (("bb", "kept in the cut"), ("cc", "silence"), ("dd", "cut out")):
                C.transcribe = lambda m, g=gone: [w for w in exp if w != g]
                bad = [f"missing: {C.context(exp, exp.index(gone), 1)} | heard: -"]
                still, kept = C.confirm_kept(bad, exp, times, list(SEGS), rough)
                self.assertIn(want, (kept if gone == "bb" else still)[0], (gone, still, kept))
                self.assertEqual(len(still) + len(kept), 1)
        finally:
            C.transcribe = real

    @unittest.skipUnless(shutil.which("ffmpeg"), "no ffmpeg")
    def test_no_measurement_is_a_problem_not_a_fake_level(self):  # ffmpeg failed: never "silence at -99 dB"
        self.assertIsNone(C.mean_db("/nonexistent/rough.mkv", 1.0, 0.5))
        exp = ["aa", "bb"]
        real = C.transcribe
        try:
            C.transcribe = lambda m: ["aa"]
            still, kept = C.confirm_kept([f"missing: {C.context(exp, 1, 1)} | heard: -"], exp, [(10.2, 10.4), (10.8, 11.0)],
                                         list(SEGS), "/nonexistent/rough.mkv")
        finally:
            C.transcribe = real
        self.assertEqual(kept, [])
        self.assertIn("not measured", still[0])


class ConfirmAudibleTest(unittest.TestCase):
    """sound mode confirms a word whisper heard in the cut but not in the film against assemble's own audio graph
    rendered as voice and bed stems (2026-11-08 s02 "no" 20 dB over the music, s04 English words 24 dB: mishearings)"""

    def test_locate_spans_the_shared_words_around_the_gap(self):
        plan = ["coś", "jest", "nie", "tak", "no", "to", "zatrzymuje"]
        times = [(10.0 + 0.3 * k, 10.2 + 0.3 * k) for k in range(len(plan))]  # all inside piece 1 (film 0-2 s)
        heard_cut = ["coś", "jest", "nie", "tak", "mhm", "to", "zatrzymuje"]  # whisper's words of the cut, misheard
        span = C.locate(heard_cut, 4, 1, plan, times, list(SEGS))
        assert span is not None
        self.assertAlmostEqual(span[0], 0.9); self.assertAlmostEqual(span[1], 1.5 + 0.3)  # "tak" start .. "to" start
        self.assertIsNone(C.locate(heard_cut, 0, 1, plan, times, list(SEGS)))  # nothing shared before it
        self.assertIsNone(C.locate(heard_cut, 4, 1, plan, times[:-1], list(SEGS)))  # tokens do not line up

    def test_voice_over_bed_reads_speech_windows_only(self):
        sr = C.SR; t = np.arange(3 * sr) / sr
        voice = np.where((t > 1) & (t < 2), 0.3 * np.sin(2 * np.pi * 200 * t), 0.0).astype(np.float32)
        quiet, loud = (0.003 * np.sin(2 * np.pi * 900 * t)).astype(np.float32), (0.3 * np.sin(2 * np.pi * 900 * t)).astype(np.float32)
        clear, masked = C.voice_over_bed(voice, quiet, 1.0, 2.0), C.voice_over_bed(voice, loud, 1.0, 2.0)
        assert clear is not None and masked is not None
        self.assertGreater(clear, C.MASK_DB); self.assertLess(masked, C.MASK_DB)
        self.assertIsNone(C.voice_over_bed(voice, quiet, 2.2, 2.9))  # no speech there

    @unittest.skipUnless(shutil.which("ffmpeg"), "no ffmpeg")
    def test_a_word_under_loud_music_stays_a_problem(self):
        d = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, d)
        mk = lambda name, src: subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", src, str(d / name)], check=True)
        mk("rough.wav", "sine=f=200:d=5"); mk("sfx.wav", "anullsrc=r=44100:cl=mono:d=5")
        exp = ["aa", "bb", "cc", "dd", "ee", "ff", "gg"]
        plan_toks, times = exp, [(10.0 + 0.25 * k, 10.2 + 0.25 * k) for k in range(len(exp))]
        loc = {"toks": plan_toks, "times": times, "segments": list(SEGS)}
        bad = [f"missing: {C.context(exp, 3, 1)} | heard: -"]
        heard = [x for x in exp if x != "dd"]
        for music_db, want in (("-30dB", "whisper did not hear it"), ("0dB", "music within")):
            mk(f"music{music_db}.wav", "sine=f=900:d=5")
            graph = (f"[0:a]asplit=2[vm][vsc];[1:a]volume={music_db}[mu];[mu][vsc]sidechaincompress=threshold=0.5:ratio=1.1[mud];"
                     "[2:a]anull[sx];[vm][mud][sx]amix=inputs=3:normalize=0:duration=first,alimiter=limit=0.89[a]")
            args = d / "assemble.audio.args.json"
            args.write_text(json.dumps({"audio": ["ffmpeg", "-v", "error", "-y", "-i", str(d / "rough.wav"), "-i",
                                                  str(d / f"music{music_db}.wav"), "-i", str(d / "sfx.wav"),
                                                  "-filter_complex", graph, "-map", "[a]", str(d / "out.m4a")]}))
            still, kept = C.confirm_audible(bad, exp, heard, loc, args)
            self.assertIn(want, (kept or still)[0], (music_db, still, kept))
            self.assertEqual(len(still) + len(kept), 1)

    def test_reheard_compares_the_same_short_window(self):
        real = C._whisper_window
        try:
            C._whisper_window = lambda m, t0, d: ["a", "b"]
            self.assertTrue(C.reheard(["x"], "rough.mkv", "film.mp4", 10.0, 12.0))  # the same: whisper misheard the whole film
            C._whisper_window = lambda m, t0, d: ["a", "x", "b"] if "rough" in m else ["a", "b"]
            self.assertFalse(C.reheard(["x"], "rough.mkv", "film.mp4", 10.0, 12.0))  # gone in the film's window too
            C._whisper_window = lambda m, t0, d: ["a", "x", "b"] if "rough" in m else ["a", "x", "c"]
            self.assertTrue(C.reheard(["x"], "rough.mkv", "film.mp4", 10.0, 12.0))  # the word is heard in the film
            C._whisper_window = lambda m, t0, d: None
            self.assertFalse(C.reheard(["x"], "rough.mkv", "film.mp4", 10.0, 12.0))  # no whisper: stays a problem
        finally:
            C._whisper_window = real

    def test_no_stems_keeps_the_problem(self):
        bad = ["missing: a b c [[dd]] e f g | heard: -"]
        self.assertEqual(C.confirm_audible(bad, [], [], {}, Path("/nonexistent/assemble.audio.args.json")), (bad, []))


if __name__ == "__main__":
    unittest.main()
