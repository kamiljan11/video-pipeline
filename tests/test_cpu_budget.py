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
        files = ["chunked_whisper.py", "verify_cut.py", "spot_check.py", "transcribe.py", "run_whisper.sh"]
        for name in files:
            text = (ROOT / name).read_text()
            for bad in ('"-t", "30"', '"-t", "16"', "-t 30 ", "-t 16 ", "cpu_threads=30"):
                self.assertNotIn(bad, text, f"{name} hardcodes {bad}")

    def test_low_priority_puts_child_on_sched_idle(self):
        code = (f"import os, sys; sys.path.insert(0, {str(ROOT)!r}); import cpu_budget; cpu_budget.low_priority(); "
                "print(os.sched_getscheduler(0) == os.SCHED_IDLE, os.nice(0))")
        out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
        self.assertEqual(out.stdout.split(), ["True", str(cpu_budget.NICE)])

    def test_preexec_fn_is_inherited_by_grandchild(self):
        # ffmpeg/whisper are started by our scripts; the policy must reach them.
        out = subprocess.run(["sh", "-c", "chrt -p $$"], capture_output=True, text=True, check=True,
                             preexec_fn=cpu_budget.low_priority)
        self.assertIn("SCHED_IDLE", out.stdout)

    def test_shell_launchers_start_heavy_jobs_idle(self):
        for name, needle in (("run_v4.sh", "chrt -i 0 nice -n 15 python3 $VP/assemble.py"),
                             ("run_v4.sh", "chrt -i 0 nice python3 $VP/critic.py"),
                             ("run_whisper.sh", 'chrt -i 0 nice -n 10 "$W/whisper.cpp/build/bin/whisper-cli"')):
            self.assertIn(needle, (ROOT / name).read_text(), f"{name}: heavy job not on SCHED_IDLE")


if __name__ == "__main__":
    unittest.main()
