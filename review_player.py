#!/usr/bin/env python3
"""review_player.py: Kamil watches the edited film before the full render and leaves notes at the pause.

    python3 review_player.py <work> <film> [--video <mp4>] [--port 8791] [--no-browser]

Kamil 2026-11-15: "jak jest zedytowany do konca ze wszystkimi zoomami ... wyskakuje filmik przed renderem i moge go sobie
obejrzec i skomentowac i dopiero sobie renderujesz". The dry render (run_v4.sh DRY=1, assemble.py --dry) is that film: the
same cut, zooms, cards, PiP, captions, music and master, in a small picture. This serves it on 127.0.0.1 with a page:
play, pause (Space) -> a box at that second -> Enter saves the note. Each note keeps the film second, the recording second
and the words said there (EDL segments + transcript), so the fix lands on the right words even after the cut moves.

Notes: <work>/review_notes_<film>.json {"film", "video", "notes": [{"t", "src", "words", "text"}], "done": bool}.
"Gotowe" sets done: the editor fixes every note, then the full render. Nothing here renders or edits a plan.
"""
from __future__ import annotations

import json
import re
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from retime_cards import film_to_source

PAGE = """<!doctype html><meta charset="utf-8"><title>Podgląd: {film}</title>
<style>body{{background:#111;color:#eee;font:16px system-ui;margin:0;display:flex;gap:16px;padding:16px}}
video{{width:960px;max-width:65vw;background:#000}}#side{{flex:1;min-width:300px}}
#box{{display:none;margin:8px 0}}#box textarea{{width:100%;height:70px;font:16px system-ui}}
li{{margin:6px 0;cursor:pointer}}li span{{color:#8cf}}button{{font:16px system-ui;padding:6px 12px}}</style>
<div><video id="v" src="/video" controls preload="auto"></video>
<p>Spacja = pauza i notatka w tym miejscu. Enter zapisuje, Esc anuluje. Klik notatki = skok.</p></div>
<div id="side"><div id="box"><b id="at"></b><textarea id="tx" placeholder="co poprawić w tym miejscu"></textarea></div>
<ol id="list"></ol><button id="done">Gotowe: obejrzane, popraw i renderuj</button> <span id="st"></span></div>
<script>
const v=document.getElementById('v'),box=document.getElementById('box'),tx=document.getElementById('tx'),
 at=document.getElementById('at'),list=document.getElementById('list'),st=document.getElementById('st');
let notes=[];const mmss=t=>Math.floor(t/60)+':'+String(Math.floor(t%60)).padStart(2,'0');
async function load(){{notes=(await (await fetch('/notes')).json()).notes;draw()}}
function draw(){{list.innerHTML='';notes.forEach((n,i)=>{{const li=document.createElement('li');
 li.innerHTML='<span>'+mmss(n.t)+'</span> '+n.text.replace(/</g,'&lt;')+' <a href="#" data-i="'+i+'">usuń</a>';
 li.onclick=e=>{{if(e.target.dataset.i!==undefined){{e.preventDefault();del(+e.target.dataset.i)}}else{{v.currentTime=n.t}}}};
 list.appendChild(li)}})}}
async function post(u,b){{const r=await fetch(u,{{method:'POST',body:JSON.stringify(b)}});notes=(await r.json()).notes;draw()}}
function del(i){{post('/delete',{{i}})}}
function open_(){{v.pause();box.style.display='block';at.textContent='notatka w '+mmss(v.currentTime);tx.value='';tx.focus()}}
document.addEventListener('keydown',e=>{{if(document.activeElement===tx){{
  if(e.key==='Enter'&&!e.shiftKey){{e.preventDefault();if(tx.value.trim())post('/note',{{t:v.currentTime,text:tx.value.trim()}});
   box.style.display='none';tx.blur()}}
  if(e.key==='Escape'){{box.style.display='none';tx.blur()}}return}}
 if(e.code==='Space'){{e.preventDefault();if(v.paused&&box.style.display==='block'){{box.style.display='none';v.play()}}
  else if(v.paused)v.play();else open_()}}}});
document.getElementById('done').onclick=async()=>{{await post('/done',{{}});st.textContent='zapisane: '+notes.length+' notatek'}};
load();
</script>"""


def words_at(words: list[dict], src: float, around: float = 2.0) -> str:
    """the words said within `around` s of recording second src (transcript offsets in ms)"""
    got = [w["text"].strip() for w in words if abs(w["offsets"]["from"] / 1000 - src) <= around]
    return " ".join(x for x in got if x)


def note(edl: dict, words: list[dict], t: float, text: str) -> dict:
    """a note at film second t: where it is in the recording and what is said there"""
    src = round(film_to_source(edl.get("segments", []), t), 2)
    return {"t": round(t, 2), "src": src, "words": words_at(words, src), "text": text}


def byte_range(header: str | None, size: int) -> tuple[int, int] | None:
    """(first, last) of an HTTP Range "bytes=a-b" (a video element seeks with it), None = the whole file"""
    m = re.fullmatch(r"bytes=(\d*)-(\d*)", (header or "").strip())
    if not m or (m.group(1) == "" and m.group(2) == ""): return None
    if m.group(1) == "": a, b = max(size - int(m.group(2)), 0), size - 1
    else: a, b = int(m.group(1)), int(m.group(2)) if m.group(2) else size - 1
    return (a, min(b, size - 1)) if a < size else None


class Review:
    def __init__(self, work: Path, film: str, video: Path):
        self.film, self.video = film, video
        self.notes_file = work / f"review_notes_{film}.json"
        self.edl = json.loads((work / f"edl_{film}.json").read_text())
        plan = json.loads((work / f"plan_{film}.json").read_text())
        w = json.loads((work / plan["words"]).read_text())
        self.words = w["transcription"] if isinstance(w, dict) else w
        self.lock = threading.Lock()
        self.state = json.loads(self.notes_file.read_text()) if self.notes_file.exists() else \
            {"film": film, "video": str(video), "notes": [], "done": False}

    def save(self) -> dict:
        self.state["notes"].sort(key=lambda n: n["t"])
        tmp = self.notes_file.with_suffix(".json.part")
        tmp.write_text(json.dumps(self.state, ensure_ascii=False, indent=1)); tmp.replace(self.notes_file)
        return self.state

    def add(self, t: float, text: str) -> dict:
        with self.lock:
            self.state["notes"].append(note(self.edl, self.words, t, text)); self.state["done"] = False
            return self.save()

    def delete(self, i: int) -> dict:
        with self.lock:
            if 0 <= i < len(self.state["notes"]): self.state["notes"].pop(i)
            return self.save()

    def done(self) -> dict:
        with self.lock:
            self.state["done"] = True
            return self.save()


def handler(rv: Review):
    class H(BaseHTTPRequestHandler):
        def log_message(self, format, *args): pass  # quiet: notes and seeks are not news

        def send(self, code: int, body: bytes, ctype: str):
            self.send_response(code); self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

        def do_GET(self):
            if self.path == "/": return self.send(200, PAGE.format(film=rv.film).encode(), "text/html; charset=utf-8")
            if self.path == "/notes": return self.send(200, json.dumps(rv.state).encode(), "application/json")
            if self.path != "/video": return self.send(404, b"", "text/plain")
            size = rv.video.stat().st_size
            r = byte_range(self.headers.get("Range"), size)
            a, b = r or (0, size - 1)
            self.send_response(206 if r else 200); self.send_header("Content-Type", "video/mp4")
            self.send_header("Accept-Ranges", "bytes"); self.send_header("Content-Length", str(b - a + 1))
            if r: self.send_header("Content-Range", f"bytes {a}-{b}/{size}")
            self.end_headers()
            with rv.video.open("rb") as f:
                f.seek(a); left = b - a + 1
                try:
                    while left > 0:
                        chunk = f.read(min(1 << 20, left))
                        if not chunk: break
                        self.wfile.write(chunk); left -= len(chunk)
                except (BrokenPipeError, ConnectionResetError): pass  # the player seeks and drops the old request

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
            if self.path == "/note": st = rv.add(float(body["t"]), str(body["text"])[:2000])
            elif self.path == "/delete": st = rv.delete(int(body["i"]))
            elif self.path == "/done": st = rv.done()
            else: return self.send(404, b"", "text/plain")
            self.send(200, json.dumps(st).encode(), "application/json")
    return H


def main(argv: list[str]) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="watch the dry film, leave notes at the pause")
    ap.add_argument("work"); ap.add_argument("film")
    ap.add_argument("--video"); ap.add_argument("--port", type=int, default=8791); ap.add_argument("--no-browser", action="store_true")
    o = ap.parse_args(argv)
    work, film = Path(o.work).resolve(), o.film
    video = Path(o.video) if o.video else Path(__file__).resolve().parent / "render" / film / f"{film}.mp4"
    if not video.exists(): print(f"review_player: no video {video} (run_v4.sh DRY=1 {film} makes it)", file=sys.stderr); return 2
    rv = Review(work, film, video)
    port = o.port
    srv = ThreadingHTTPServer(("127.0.0.1", port), handler(rv))
    url = f"http://127.0.0.1:{port}/"
    print(f"review_player: {url} -> notes in {rv.notes_file}", flush=True)
    if not o.no_browser: webbrowser.open(url)
    try: srv.serve_forever()
    except KeyboardInterrupt: pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
