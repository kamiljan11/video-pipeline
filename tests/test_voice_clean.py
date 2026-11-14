"""voice_clean.py: the voice through DeepFilterNet before the chain; a missing binary stops the render, named."""
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import edl_guard
import voice_clean

# stands in for deep-filter: writes <out>/<name> at half the level and records its arguments
STUB = """#!/bin/sh
echo "$@" > "$(dirname "$0")/args.txt"
[ "$1" = "-D" ] && [ "$2" = "-o" ] || exit 9
mkdir -p "$3" && ffmpeg -v error -y -i "$4" -af volume=0.5 "$3/$(basename "$4")"
"""


class VoiceCleanTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="voice-clean-test-"))
        self.media = self.tmp / "rough.mkv"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=f=220:d=1", "-c:a", "aac", str(self.media)], check=True)
        self.exe = self.tmp / "deep-filter"
        self.exe.write_text(STUB); self.exe.chmod(self.exe.stat().st_mode | stat.S_IXUSR)

    def level(self, f: Path) -> float:
        r = subprocess.run(["ffmpeg", "-v", "info", "-nostats", "-i", str(f), "-af", "astats=measure_overall=RMS_level:measure_perchannel=none",
                            "-f", "null", "-"], capture_output=True, text=True, check=True)
        return float(r.stderr.rsplit("RMS level dB:", 1)[1].split()[0])

    def test_the_cleaned_voice_is_what_the_binary_wrote(self):
        with mock.patch.dict(os.environ, {"VP_DEEP_FILTER": str(self.exe)}):
            dst = voice_clean.clean(str(self.media), str(self.tmp / "rough.voice.wav"))
        self.assertAlmostEqual(self.level(Path(dst)), self.level(self.media) - 6.0, delta=1.0)  # the stub's volume=0.5
        self.assertTrue((self.tmp / "args.txt").read_text().startswith("-D -o "))  # -D: the model's delay taken back

    def test_a_missing_binary_stops_with_its_path(self):
        with mock.patch.dict(os.environ, {"VP_DEEP_FILTER": str(self.tmp / "nope")}), self.assertRaises(SystemExit) as e:
            voice_clean.clean(str(self.media), str(self.tmp / "v.wav"))
        self.assertIn(str(self.tmp / "nope"), str(e.exception))
        self.assertFalse((self.tmp / "v.wav").exists())

    def test_a_failing_binary_stops_and_writes_nothing(self):
        self.exe.write_text("#!/bin/sh\necho broken model >&2\nexit 3\n")
        with mock.patch.dict(os.environ, {"VP_DEEP_FILTER": str(self.exe)}), self.assertRaises(SystemExit) as e:
            voice_clean.clean(str(self.media), str(self.tmp / "v.wav"))
        self.assertIn("broken model", str(e.exception))
        self.assertFalse((self.tmp / "v.wav").exists())

    def test_the_guard_knows_the_key_and_the_default_chain(self):
        base = {"sources": {"A": "a.mp4"}, "segments": [{"src": "A", "in": 0.0, "out": 1.0}]}
        self.assertEqual(edl_guard.problems({**base, "voice_clean": "dfn", "audio": voice_clean.CHAIN}), [])
        for bad in ("resemble", True, 1, ""):
            self.assertTrue(any("voice_clean" in p for p in edl_guard.problems({**base, "voice_clean": bad})), bad)
        self.assertNotIn("afftdn", voice_clean.CHAIN); self.assertNotIn("acompressor", voice_clean.CHAIN)


if __name__ == "__main__":
    unittest.main()
