"""sound_seen.py: the sound checks carry over only to the same sound, cut, words and code (2026-11-15 long: 78 of 123 min in checks)."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import sound_seen


class SoundSeenTest(unittest.TestCase):
    def setUp(self):
        self.w = Path(tempfile.mkdtemp(prefix="sound-seen-"))
        self.edl = {"segments": [{"in": 1.0, "out": 5.0}], "overlays": [{"id": "a", "at": 1.0}], "music_db": -9, "music": "beds/m.wav"}
        (self.w / "plan_f.json").write_text(json.dumps({"retakes_ok": {}}))
        (self.w / "edl_f.txt").write_text("a b c")
        (self.w / "args.json").write_text("[]")
        self.sound = {"rough.mkv": "r1", "f.mp4": "f1"}

    def key(self, commit="c1"):
        (self.w / "edl_f.json").write_text(json.dumps(self.edl))
        return sound_seen.key(self.w, "f", Path("rough.mkv"), Path("f.mp4"), self.w / "args.json", commit, md5=lambda p: self.sound[p.name])

    def test_a_moved_card_keeps_the_key(self):
        k = self.key()
        self.edl["overlays"] = [{"id": "a", "at": 2.5}]; self.edl["music"] = "other/m.wav"
        self.assertEqual(self.key(), k)

    def test_another_sound_cut_words_setting_or_commit_is_another_key(self):
        k = self.key()
        self.sound["f.mp4"] = "f2"; self.assertNotEqual(self.key(), k); self.sound["f.mp4"] = "f1"
        self.sound["rough.mkv"] = "r2"; self.assertNotEqual(self.key(), k); self.sound["rough.mkv"] = "r1"
        self.edl["segments"][0]["out"] = 5.2; self.assertNotEqual(self.key(), k); self.edl["segments"][0]["out"] = 5.0
        self.edl["music_db"] = -13; self.assertNotEqual(self.key(), k); self.edl["music_db"] = -9
        (self.w / "edl_f.txt").write_text("a b"); self.assertNotEqual(self.key(), k); (self.w / "edl_f.txt").write_text("a b c")
        (self.w / "plan_f.json").write_text(json.dumps({"retakes_ok": {"a b c d": "said twice on purpose"}})); self.assertNotEqual(self.key(), k)
        (self.w / "plan_f.json").write_text(json.dumps({"retakes_ok": {}}))
        self.assertNotEqual(self.key("c2"), k)
        self.assertEqual(self.key(), k)

    def test_unknown_code_gets_no_key(self):
        with self.assertRaises(ValueError): self.key("")

    def test_only_a_recorded_pass_of_this_key_carries_over(self):
        k = self.key()
        self.assertEqual(sound_seen.same(self.w, "f", k), "")
        self.assertEqual(sound_seen.main(["pass", str(self.w), "f", k]), 0)
        self.assertNotEqual(sound_seen.same(self.w, "f", k), "")
        self.assertEqual(sound_seen.same(self.w, "f", "other"), ""); self.assertEqual(sound_seen.same(self.w, "f", ""), "")
        self.assertEqual(sound_seen.main(["same", str(self.w), "f", "other"]), 1)
        self.assertEqual(sound_seen.main(["pass", str(self.w), "f", ""]), 1)

    def test_the_samples_and_not_the_file_are_hashed(self):
        import shutil
        import subprocess
        if not shutil.which("ffmpeg"): self.skipTest("no ffmpeg")
        a, b, c = self.w / "a.wav", self.w / "b.mkv", self.w / "c.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "sine=440:d=1", "-c:a", "pcm_s16le", str(a)], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-i", str(a), "-c", "copy", str(b)], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "sine=441:d=1", "-c:a", "pcm_s16le", str(c)], check=True)
        self.assertEqual(sound_seen.samples_md5(a), sound_seen.samples_md5(b))
        self.assertNotEqual(sound_seen.samples_md5(a), sound_seen.samples_md5(c))


if __name__ == "__main__":
    unittest.main()
