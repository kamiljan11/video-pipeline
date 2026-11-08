"""render_audit.py on a tiny film with planted defects: a flash, a picture change the EDL does not explain, a doubled word, a short card"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import render_audit as RA


def word(text: str, a: float, b: float) -> dict:
    return {"text": f" {text}", "offsets": {"from": int(a * 1000), "to": int(b * 1000)}}


def film(path: Path, parts: list[tuple[str, float]]) -> None:
    """colour blocks one after another: a hard picture change at every join"""
    args, chain = [], ""
    for i, (c, d) in enumerate(parts):
        args += ["-f", "lavfi", "-i", f"color=c={c}:s=160x90:r=30:d={d}"]
        chain += f"[{i}:v]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args, "-filter_complex", f"{chain}concat=n={len(parts)}:v=1[v]", "-map", "[v]",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path)], check=True)


class AuditTest(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory(); self.d = Path(self.t.name)

    def tearDown(self):
        self.t.cleanup()

    def project(self, parts, overlays, words) -> list[str]:
        film(self.d / "f.mp4", parts)
        (self.d / "edl.json").write_text(json.dumps({"segments": [{"in": 0.0, "out": 3.0}, {"in": 10.0, "out": 13.0}], "overlays": overlays}))
        (self.d / "w.json").write_text(json.dumps({"transcription": words}))
        (self.d / "plan.json").write_text(json.dumps({"edl_out": "edl.json", "words": "w.json"}))
        return [str(self.d / "plan.json"), str(self.d / "f.mp4")]

    def run_cli(self, args):
        return subprocess.run([sys.executable, str(ROOT / "render_audit.py"), *args], capture_output=True, text=True, check=False)

    def test_planted_defects_are_each_named(self):
        args = self.project([("blue", 2.0), ("red", 0.2), ("blue", 0.8), ("green", 1.5), ("yellow", 1.5)],
                            [{"id": "g1", "at": 5.0, "dur": 1.0}],
                            [word("agent", 0.5, 0.9), word("agent", 1.0, 1.4), word("tak", 10.5, 10.7), word("tak", 10.8, 11.0)])
        r = self.run_cli(args)
        self.assertEqual(r.returncode, 1, r.stderr)
        kinds = {f["kind"]: f for f in json.loads((self.d / "f.audit.json").read_text())["defects"]}
        self.assertEqual(set(kinds), {"flash", "jump", "repeat", "short"}, r.stdout)
        self.assertIn("0:02.0-0:02.2", kinds["flash"]["detail"])
        self.assertIn("'agent'", kinds["repeat"]["detail"])  # "tak tak" is on the allowed list
        self.assertIn("g1", kinds["short"]["detail"])
        jumps = [f["t"] for f in json.loads((self.d / "f.audit.json").read_text())["defects"] if f["kind"] == "jump"]
        self.assertTrue(any(abs(t - 4.5) < 0.05 for t in jumps), jumps)  # the cut at 3.0 is in the EDL, 4.5 is not
        self.assertFalse(any(abs(t - 3.0) < 0.05 for t in jumps), jumps)

    def test_a_clean_film_passes(self):
        args = self.project([("blue", 3.0), ("green", 3.0)], [], [word("raz", 0.5, 0.9), word("dwa", 1.0, 1.4)])
        r = self.run_cli(args)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("OK render_audit", r.stdout)

    def test_a_film_from_another_edl_says_so(self):
        args = self.project([("blue", 3.0), ("green", 1.0)], [], [])
        r = self.run_cli(args)
        self.assertEqual(r.returncode, 1)
        self.assertIn("not the EDL this film was rendered from", r.stdout)

    def test_marks_and_word_compare(self):
        edl = {"segments": [{"in": 0, "out": 2}, {"in": 5, "out": 6}], "overlays": [{"at": 0.5, "dur": 1}], "broll": [{"at": 2.5, "dur": 0.4}]}
        self.assertEqual(RA.marks(edl), [0.0, 0.5, 1.5, 2.0, 2.5, 2.9, 3.0])
        self.assertEqual(RA.norm("Żółw,"), "żółw")

    def test_a_card_fading_in_and_a_question_answered_are_not_defects(self):
        edl = {"segments": [{"in": 0, "out": 10}], "overlays": [{"id": "g", "at": 3.0, "dur": 4.0}]}
        said = [(1.0, "mamy?"), (1.5, "Mamy"), (5.0, "na"), (5.3, "na")]
        got = RA.audit([3.3, 6.75], edl, said)  # 0.3 s into the fade in, 0.25 s before the end: the card, not a jump
        self.assertEqual([(f["kind"], f["detail"]) for f in got], [("repeat", "0:05.0: 'na' 'na'")])
        self.assertEqual([f["kind"] for f in RA.audit([4.0], edl, [])], ["jump"])  # mid card: unexplained

    def test_a_card_over_the_mouth_fails_a_side_column_passes(self):
        specs = {"mouth": {"id": "mouth", "type": "kw"}, "side": {"id": "side", "type": "kw"},
                 "full": {"id": "full", "type": "chap"}, "pip": {"id": "pip", "type": "slide"}}
        edl = {"overlays": [{"id": "mouth", "at": 2.0, "dur": 2.0}, {"id": "side", "at": 6.0, "dur": 2.0},
                            {"id": "full", "at": 10.0, "dur": 2.0}, {"id": "pip", "at": 14.0, "dur": 2.0}]}
        hidden = [(2.0, 4.0), (10.0, 12.0), (14.0, 16.0)]  # the face is gone under "mouth" and under the full screens
        got = RA.face_covered(edl, specs, lambda t: not any(a <= t < b for a, b in hidden))
        self.assertEqual([f["detail"].split(": ")[1].split(" ")[0] for f in got], ["mouth"])
        self.assertEqual(got[0]["kind"], "face")

    def test_usage_and_a_broken_plan(self):
        self.assertEqual(self.run_cli([]).returncode, 2)
        (self.d / "plan.json").write_text("{}")
        r = self.run_cli([str(self.d / "plan.json"), str(self.d / "nope.mp4")])
        self.assertEqual(r.returncode, 1)
        self.assertIn("FAILED render_audit", r.stderr)


if __name__ == "__main__":
    unittest.main()
