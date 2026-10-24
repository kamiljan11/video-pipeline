#!/usr/bin/env python3
"""CPU budget for heavy jobs (whisper): leave cores for the desktop and run at low priority.

Whisper on 30 of 32 threads at nice 0 starved the compositor (load ~40-100, CPU PSI ~60%) and the
screen stuttered while rendering. One place decides how many threads heavy jobs get.

    python3 cpu_budget.py          -> prints the thread count (for shell scripts)
    from cpu_budget import heavy_threads, low_priority
"""
import os

RESERVED_CORES = 8  # kept free for gnome-shell, browser, editor
MIN_THREADS = 4
NICE = 10


def heavy_threads(cpus: int | None = None) -> int:
    """Threads a heavy job may use: all cores minus the reserve, never below MIN_THREADS."""
    total = cpus if cpus is not None else (os.cpu_count() or MIN_THREADS)
    return max(MIN_THREADS, total - RESERVED_CORES)


def low_priority() -> None:
    """subprocess preexec_fn / in-process call: lower CPU priority of the current process."""
    os.nice(NICE)


if __name__ == "__main__":
    print(heavy_threads())
