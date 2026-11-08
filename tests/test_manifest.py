"""manifest.py: a film or material made by older or uncommitted pipeline code is not done (Kamil 2026-11-08 "wszystko po
starych poszlo??")."""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import manifest


def sh(repo: Path, *a: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True, check=True).stdout.strip()


class ManifestTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="manifest-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.repo = self.tmp / "vp"; self.repo.mkdir()
        sh(self.repo, "init", "-q")
        sh(self.repo, "config", "user.email", "t@t"); sh(self.repo, "config", "user.name", "t")
        (self.tmp / "hooks").mkdir()  # a fixture repo: the laptop's global commit gates are for real code, not for these files
        sh(self.repo, "config", "core.hooksPath", str(self.tmp / "hooks"))
        (self.repo / "a.py").write_text("x = 1\n"); (self.repo / "docs").mkdir(); (self.repo / "docs" / "n.md").write_text("n\n")
        sh(self.repo, "add", "."); sh(self.repo, "commit", "-qm", "one")
        p = mock.patch.object(manifest, "ROOT", self.repo); p.start(); self.addCleanup(p.stop)
        self.out = self.tmp / "out"
        for d in ("long", "shorts", "thumbnails"): (self.out / d).mkdir(parents=True)
        (self.out / "long" / "l.mp4").write_text("v"); (self.out / "shorts" / "s1.mp4").write_text("v")
        (self.out / "RAPORT.md").write_text("r")

    def stamp_all(self):
        manifest.stamp(self.out / "long", ["l.mp4"]); manifest.stamp(self.out / "shorts", ["s1.mp4"])
        manifest.stamp(self.out, ["thumbnails"])

    def commit(self, rel: str, text: str):
        f = self.repo / rel; f.parent.mkdir(parents=True, exist_ok=True); f.write_text(text)
        sh(self.repo, "add", "."); sh(self.repo, "commit", "-qm", rel)

    def test_everything_stamped_by_head_passes(self):
        self.stamp_all()
        self.assertEqual(manifest.check(self.out), [])

    def test_a_part_without_a_stamp_fails(self):
        manifest.stamp(self.out / "long", ["l.mp4"])
        bad = manifest.check(self.out)
        self.assertEqual(sorted(b.split(":")[0] for b in bad), ["shorts/s1.mp4", "thumbnails"])

    def test_code_changed_after_the_stamp_fails(self):
        self.stamp_all()
        self.commit("a.py", "x = 2\n")
        bad = manifest.check(self.out)
        self.assertEqual(len(bad), 3)
        self.assertIn("code changed since", bad[0]); self.assertIn("a.py", bad[0])

    def test_docs_and_tests_after_the_stamp_do_not_count(self):
        self.stamp_all()
        self.commit("docs/n.md", "m\n"); self.commit("tests/test_a.py", "pass\n"); self.commit("README.md", "r\n")
        self.assertEqual(manifest.check(self.out), [])

    def test_a_stamp_from_uncommitted_code_fails(self):
        (self.repo / "a.py").write_text("x = 3\n")
        self.stamp_all()
        self.assertIn("uncommitted code", manifest.check(self.out)[0])

    def test_unknown_commit_fails(self):
        (self.out / "manifest.json").write_text(json.dumps({"thumbnails": {"commit": "f" * 40, "dirty": False}}))
        manifest.stamp(self.out / "long", ["l.mp4"]); manifest.stamp(self.out / "shorts", ["s1.mp4"])
        self.assertEqual(manifest.check(self.out), [f"thumbnails: unknown commit {'f' * 12}"])

    def test_cli(self):
        self.assertEqual(manifest.main(["stamp", str(self.out), "thumbnails"]), 0)
        self.assertEqual(manifest.main(["check", str(self.out)]), 1)  # the films are not stamped
        self.stamp_all()
        self.assertEqual(manifest.main(["check", str(self.out)]), 0)
        self.assertEqual(manifest.main(["nope"]), 2)


if __name__ == "__main__":
    unittest.main()
