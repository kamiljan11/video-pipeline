"""where a long step writes its progress for the render widget: ~/.cache/vp-progress, never next to a delivered film.

Standard library only: render_status (the widget) imports it every 5 s and must not pull in numpy or whisper.
"""
import hashlib
import os
from pathlib import Path

PROGRESS_DIR = Path.home() / ".cache/vp-progress"


def progress_file(media: str, pid: int) -> Path:
    """the progress file of whisper hearing media in process pid (words_check writes it, render_status reads it)"""
    return PROGRESS_DIR / f"{progress_key(media)}.{pid}.progress"


def progress_key(media: str) -> str:
    return hashlib.sha1(os.path.abspath(media).encode()).hexdigest()[:16]
