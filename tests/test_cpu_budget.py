"""cpu_budget.py: heavy jobs leave cores for the desktop.

Run: cd ~/video-pipeline && python3 -m pytest -q tests/test_cpu_budget.py
"""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import cpu_budget  # after the repo root is on the path


class CpuBudgetTest(unittest.TestCase):
    def test_reserves_cores_on_big_machine(self):
        self.assertEqual(cpu_budget.heavy_threads(32), 24)

    def test_never_below_minimum(self):
        self.assertEqual(cpu_budget.heavy_threads(4), cpu_budget.MIN_THREADS)
        self.assertEqual(cpu_budget.heavy_threads(1), cpu_budget.MIN_THREADS)

    def test_cli_prints_same_number_as_function(self):
        out = subprocess.run([sys.executable, str(ROOT / "cpu_budget.py")], capture_output=True, text=True, check=True)
        self.assertEqual(int(out.stdout), cpu_budget.heavy_threads())

    def test_no_call_site_hardcodes_whisper_threads(self):
        files = ["chunked_whisper.py", "verify_cut.py", "spot_check.py", "transcribe.py", "run_whisper.sh", "final_check.sh"]
        for name in files:
            text = (ROOT / name).read_text()
            for bad in ('"-t", "30"', '"-t", "16"', "-t 30 ", "-t 16 ", "cpu_threads=30"):
                self.assertNotIn(bad, text, f"{name} hardcodes {bad}")


if __name__ == "__main__":
    unittest.main()
