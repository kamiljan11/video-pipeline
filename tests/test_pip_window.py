"""16:9 picture-in-picture: the window is cut around each piece's head from the recording (gfx_types.pip_window, assemble.py).

  python3 -m unittest tests.test_pip_window   (the render test needs ffmpeg; about 5 s)
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import gfx_types  # after the path insert: the scripts are not a package

SW, SH = 2560, 1440


def run(*args: str) -> None:
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


class PipWindowTest(unittest.TestCase):
    def test_the_head_is_in_the_middle(self):
        head = (0.33, 0.30, 0.43, 0.55)  # off to the left, face mode box (hair 0.12)
        x, y, side = gfx_types.pip_window(head, SW, SH, 0.12)
        self.assertAlmostEqual(x + side / 2, 0.38 * SW, delta=2)
        fh = 0.25 * SH / 1.37
        top = 0.30 * SH - 0.33 * fh  # the hair line above the brow-only box
        self.assertLess(y, top)  # the hair is inside, with room above it
        self.assertGreater(y + side, 0.55 * SH)  # the chin too
        self.assertAlmostEqual((0.55 * SH - top) / side, 0.62, delta=0.01)

    def test_hair_mode_box_gives_the_same_window(self):
        fh = 0.2 * SH  # one face, two boxes: grown 0.12 or 0.45 face heights above the face
        face_top, chin = 0.35 * SH, 0.35 * SH + 1.25 * fh
        brow = (0.4, (face_top - 0.12 * fh) / SH, 0.5, chin / SH)
        hair = (0.4, (face_top - 0.45 * fh) / SH, 0.5, chin / SH)
        self.assertEqual(gfx_types.pip_window(brow, SW, SH, 0.12), gfx_types.pip_window(hair, SW, SH, 0.45))

    def test_a_close_head_takes_the_full_height_and_stays_in_frame(self):
        for head in ((0.30, 0.14, 0.57, 0.71), (0.0, 0.0, 0.2, 0.9), (0.85, 0.2, 1.0, 0.8)):
            x, y, side = gfx_types.pip_window(head, SW, SH, 0.12)
            self.assertLessEqual(side, SH)
            self.assertTrue(0 <= x <= SW - side and 0 <= y <= SH - side, (head, x, y, side))
            self.assertEqual((x % 2, y % 2, side % 2), (0, 0, 0))


class PipRenderTest(unittest.TestCase):
    """a red head left of the middle: the window shows it, the old film-wide face point (0.52) would show the wall"""
    W, H = 640, 360

    def test_window_follows_the_piece_head(self):
        tmp = Path(tempfile.mkdtemp(prefix="pip-"))
        src, card = tmp / "src.mp4", tmp / "card.mov"
        run("-f", "lavfi", "-i", f"color=c=0x202020:s={self.W}x{self.H}:r=30:d=2", "-f", "lavfi", "-i", "sine=f=220:d=2",
            "-vf", f"drawbox=x={int(0.10 * self.W)}:y={int(0.25 * self.H)}:w={int(0.12 * self.W)}:h={int(0.45 * self.H)}:color=red:t=fill",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(src))
        run("-f", "lavfi", "-i", f"color=c=blue:s={self.W}x{self.H}:r=30:d=1.5,format=yuva444p10le", "-c:v", "prores_ks",
            "-profile:v", "4444", "-pix_fmt", "yuva444p10le", str(card))
        head = [0.10, 0.25, 0.22, 0.70]
        edl = {"sources": {"A": str(src)}, "w": self.W, "h": self.H, "src_w": self.W, "src_h": self.H, "seg_exact": True, "head_track": True,
               "face": [0.52, 0.42], "pip_size": 120, "out_name": "final.mp4",
               "segments": [{"src": "A", "in": 0.0, "out": 2.0, "zoom": 1.0, "face": [0.5, 0.42], "head": head}],
               "overlays": [{"file": str(card), "at": 0.2, "dur": 1.5, "id": "c", "pip": True}]}
        (tmp / "edl.json").write_text(json.dumps(edl))
        r = subprocess.run([sys.executable, str(ROOT / "assemble.py"), str(tmp / "edl.json"), str(tmp)],
                           capture_output=True, text=True, check=False)
        self.assertEqual(r.returncode, 0, r.stderr[-2000:])
        px, py = self.W - 120 - 72 + 60, self.H - 120 - 72 - 20 + 60  # the middle of the window (assemble.py pip_x, pip_y)
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", "1.0", "-i", str(tmp / "final.mp4"), "-frames:v", "1", "-vf",
                              f"format=rgb24,crop=1:1:{px}:{py}", "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
        self.assertGreater(raw[0], 150, list(raw))  # red head, not the grey wall
        self.assertLess(raw[2], 90, list(raw))  # and not the blue card under the window
        del edl["head_track"]  # an old EDL: the window as before, at the film face point (the wall), panel compat test
        (tmp / "edl.json").write_text(json.dumps(edl))
        r = subprocess.run([sys.executable, str(ROOT / "assemble.py"), str(tmp / "edl.json"), str(tmp)],
                           capture_output=True, text=True, check=False)
        self.assertEqual(r.returncode, 0, r.stderr[-2000:])
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", "1.0", "-i", str(tmp / "final.mp4"), "-frames:v", "1", "-vf",
                              f"format=rgb24,crop=1:1:{px}:{py}", "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
        self.assertLess(raw[0], 90, list(raw))

    def test_b_roll_still_reads_its_own_file_next_to_a_window(self):
        """pip.mkv is one more stage-2 input: the b-roll input numbers must step over it (review 2026-11-05 code-1)"""
        tmp = Path(tempfile.mkdtemp(prefix="pip-broll-"))
        src, card, broll = tmp / "src.mp4", tmp / "card.mov", tmp / "broll.mp4"
        run("-f", "lavfi", "-i", f"color=c=0x202020:s={self.W}x{self.H}:r=30:d=3", "-f", "lavfi", "-i", "sine=f=220:d=3",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(src))
        run("-f", "lavfi", "-i", f"color=c=blue:s={self.W}x{self.H}:r=30:d=0.8,format=yuva444p10le", "-c:v", "prores_ks",
            "-profile:v", "4444", "-pix_fmt", "yuva444p10le", str(card))
        run("-f", "lavfi", "-i", f"color=c=0x00ff00:s={self.W}x{self.H}:r=30:d=2", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(broll))
        edl = {"sources": {"A": str(src)}, "w": self.W, "h": self.H, "src_w": self.W, "src_h": self.H, "seg_exact": True, "head_track": True,
               "face": [0.5, 0.42], "pip_size": 120, "out_name": "final.mp4",
               "segments": [{"src": "A", "in": 0.0, "out": 3.0, "zoom": 1.0, "face": [0.5, 0.42], "head": [0.4, 0.25, 0.6, 0.7]}],
               "overlays": [{"file": str(card), "at": 0.1, "dur": 0.8, "id": "c", "pip": True}],
               "broll": [{"file": str(broll), "at": 1.5, "dur": 1.0}]}
        (tmp / "edl.json").write_text(json.dumps(edl))
        r = subprocess.run([sys.executable, str(ROOT / "assemble.py"), str(tmp / "edl.json"), str(tmp)],
                           capture_output=True, text=True, check=False)
        self.assertEqual(r.returncode, 0, r.stderr[-2000:])
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", "2.0", "-i", str(tmp / "final.mp4"), "-frames:v", "1", "-vf",
                              f"format=rgb24,crop=1:1:{self.W // 4}:{self.H // 4}", "-f", "rawvideo", "-"],
                             capture_output=True, check=True).stdout
        self.assertGreater(raw[1], 150, list(raw))  # the green b-roll, not the window's track



class CornerRenderTest(unittest.TestCase):
    """9:16 corner circle: cut from the recording around the head, head and shoulders (Kamil 2026-11-05: "oddal mnie…
    nie ultra zoomed twarz"); the old crop of the zoomed vertical picture sat on the frame's middle"""

    def render(self, *flags):
        tmp = Path(tempfile.mkdtemp(prefix="corner-"))
        src, card = tmp / "src.mp4", tmp / "card.mov"
        sw, sh, W, H = 640, 360, 1080, 1920
        run("-f", "lavfi", "-i", f"color=c=0x202020:s={sw}x{sh}:r=30:d=2", "-f", "lavfi", "-i", "sine=f=220:d=2",
            "-vf", f"drawbox=x={int(0.30 * sw)}:y={int(0.25 * sh)}:w={int(0.12 * sw)}:h={int(0.45 * sh)}:color=red:t=fill",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(src))
        run("-f", "lavfi", "-i", f"color=c=blue:s={W}x{H}:r=30:d=1.5,format=yuva444p10le", "-c:v", "prores_ks",
            "-profile:v", "4444", "-pix_fmt", "yuva444p10le", str(card))
        edl = {"sources": {"A": str(src)}, "w": W, "h": H, "src_w": sw, "src_h": sh, "vertical": True, "seg_exact": True, "head_track": True,
               "face": [0.5, 0.42], "out_name": "final.mp4",
               "segments": [{"src": "A", "in": 0.0, "out": 2.0, "zoom": 1.0, "face": [0.5, 0.42], "head": [0.30, 0.25, 0.42, 0.70]}],
               "overlays": [{"file": str(card), "at": 0.2, "dur": 1.5, "id": "c", "corner": True}]}
        (tmp / "edl.json").write_text(json.dumps(edl))
        r = subprocess.run([sys.executable, str(ROOT / "assemble.py"), str(tmp / "edl.json"), str(tmp), *flags],
                           capture_output=True, text=True, check=False)
        self.assertEqual(r.returncode, 0, r.stderr[-2000:])
        return tmp, src

    def again(self, tmp, *flags):
        return subprocess.run([sys.executable, str(ROOT / "assemble.py"), str(tmp / "edl.json"), str(tmp), *flags],
                              capture_output=True, text=True, check=False)

    def test_circle_follows_the_head_and_leaves_room_below_it(self):
        tmp, _ = self.render()
        CN = gfx_types.CORNER

        def px(fy):  # the circle's middle column, fy of its height down
            x, y = CN["x"] + CN["size"] // 2, CN["y"] + int(CN["size"] * fy)
            return subprocess.run(["ffmpeg", "-v", "error", "-ss", "1.0", "-i", str(tmp / "final.mp4"), "-frames:v", "1", "-vf",
                                   f"format=rgb24,crop=1:1:{x}:{y}", "-f", "rawvideo", "-"], capture_output=True, check=True).stdout

        mid = px(0.5)
        self.assertGreater(mid[0], 150, list(mid))  # the red head (left of the frame's middle, x 0.30-0.42), not the wall at 0.5
        self.assertLess(mid[2], 90, list(mid))  # and not the blue card under the circle
        low = px(0.85)
        self.assertLess(low[0], 90, list(low))  # below the chin: the circle holds more than the face

    def test_a_missing_recording_stops_a_render_and_a_preview_uses_rough(self):
        """film 1's recording went to the cloud and the panel previews broke (2026-11-05): a preview (--proxy) cuts the
        circle from the cached rough.mkv and says so; a real render still needs the recording"""
        tmp, src = self.render()
        src.unlink()
        r = self.again(tmp)
        self.assertNotEqual(r.returncode, 0); self.assertIn("missing", r.stderr)
        r = self.again(tmp, "--proxy")
        self.assertEqual(r.returncode, 0, r.stderr[-2000:]); self.assertIn("preview from rough.mkv", r.stderr)

if __name__ == "__main__":
    unittest.main()
