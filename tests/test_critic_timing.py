"""critic.py film times = build_edl's: frame-exact pieces (seg_exact) and pieces out of source order (2026-11-09 v5 long:
a false C2 "zoom 1.12 pod ramką k_przestac" because critic added raw piece lengths)."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import timeline


class CriticTimingTest(unittest.TestCase):
    def run_critic(self, exact: bool, card_at: float | None = None) -> str:
        d = Path(tempfile.mkdtemp(prefix="critic-")); self.addCleanup(shutil.rmtree, d, True)
        a_out = 10.0 + 0.4 / timeline.FPS  # raw 10.013 s; whole frames 10.0 s
        end = timeline.piece_len({"in": 0.0, "out": a_out}, exact)
        words = {"transcription": [{"text": " słowo", "offsets": {"from": i * 500, "to": i * 500 + 400}} for i in range(60)]}
        (d / "w.json").write_text(json.dumps(words))
        (d / "edl.json").write_text(json.dumps({"seg_exact": exact, "segments": [
            {"in": 0.0, "out": a_out, "zoom": 1.12}, {"in": 12.0, "out": 25.0, "zoom": 1.0}],
            "overlays": [{"id": "k", "at": end if card_at is None else card_at, "dur": 3.0}]}))
        (d / "specs.json").write_text(json.dumps([{"id": "k", "type": "kw", "text": "Przestań dokładać blokady"}]))
        (d / "plan.json").write_text(json.dumps({"edl_out": "edl.json", "words": "w.json", "gfx_specs": "specs.json", "seg_exact": exact}))
        r = subprocess.run([sys.executable, str(HERE / "critic.py"), "plan.json"], cwd=d, capture_output=True, text=True, timeout=60, check=False)
        return r.stdout + r.stderr

    def test_a_card_right_after_a_zoomed_frame_exact_piece_is_not_under_the_zoom(self):
        self.assertNotIn("C2", self.run_critic(True))

    def test_a_card_inside_the_zoomed_piece_is_still_an_error(self):
        self.assertIn("C2", self.run_critic(True, card_at=8.0))
        self.assertIn("C2", self.run_critic(False, card_at=8.0))


if __name__ == "__main__":
    unittest.main()
