#!/usr/bin/env python3
# stop_render.py — stop pipeline processes (run_v4/render_all, assemble.py, its ffmpeg) without matching itself
import os
import signal
from pathlib import Path

me = os.getpid(); killed = []
for pid in os.listdir('/proc'):
    if not pid.isdigit() or int(pid) in (me, os.getppid()): continue
    try: cmd = Path(f'/proc/{pid}/cmdline').read_bytes().replace(b'\0', b' ').decode(errors='ignore')
    except OSError: continue  # process gone or not ours
    if any(k in cmd for k in ('run_v4.sh', 'render_all.sh', 'render_v3.sh', 'assemble.py edl_')) or (cmd.startswith('ffmpeg') and ('/video-pipeline/render/' in cmd or 'Nagrania/2026-10-20_11-38-18.mp4' in cmd)):
        try: os.kill(int(pid), signal.SIGTERM); killed.append(cmd[:70])
        except OSError: pass  # already exited
print(len(killed), 'stopped'); [print(' ', k) for k in killed]
