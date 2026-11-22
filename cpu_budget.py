#!/usr/bin/env python3
"""CPU budget for heavy jobs (whisper): leave cores for the desktop and run at low priority.

Whisper on 30 of 32 threads at nice 0 starved the compositor (load ~40-100, CPU PSI ~60%) and the
screen stuttered while rendering. One place decides how many threads heavy jobs get.

    python3 cpu_budget.py          -> prints the thread count (for shell scripts)
    from cpu_budget import heavy_threads, low_priority
"""
import os
import sys

RESERVED_CORES = 8  # kept free for gnome-shell, browser, editor
MIN_THREADS = 4
NICE = 10


def heavy_threads(cpus: int | None = None) -> int:
    """Threads a heavy job may use: all cores minus the reserve, never below MIN_THREADS."""
    total = cpus if cpus is not None else (os.cpu_count() or MIN_THREADS)
    return max(MIN_THREADS, total - RESERVED_CORES)


def low_priority() -> None:
    """subprocess preexec_fn / in-process call: lower CPU priority of the current process.

    nice alone is not enough: 6 x ffmpeg (~83 threads each) at nice 15 still pushed CPU PSI to 42 %
    and the whole desktop stuttered (2026-11-22). SCHED_IDLE runs the job only on CPU time nobody
    else wants; children inherit it (ffmpeg spawned by assemble.py, whisper-cli). Measured after
    `chrt -i`: gnome-shell answered within 8 ms while the render kept going.
    """
    os.nice(NICE)
    try:
        os.sched_setscheduler(0, os.SCHED_IDLE, os.sched_param(0))
    except (OSError, AttributeError) as e:  # non-Linux or blocked by a sandbox: nice still applies
        print(f"cpu_budget: SCHED_IDLE unavailable ({e}); running at nice {NICE} only", file=sys.stderr)


if __name__ == "__main__":
    print(heavy_threads())
