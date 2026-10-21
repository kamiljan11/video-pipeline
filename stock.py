"""stock.py — free stock video behind one interface (b-roll for broll.py): search() -> [Clip], fetch() -> local file.

The provider name comes from style/grammar.json broll.provider; adding one = one search function in PROVIDERS plus
its file host in HOSTS. Pexels (https://www.pexels.com/api/documentation/): free key, 200 requests/h and 20k/month;
the licence needs no attribution, but the API guidelines ask for a link to Pexels and its authors: credits are kept per clip for the description.
The key is read from the environment only (Infisical: `infisical_bridge.py run --secrets Pexels -- ...`), never from
files and never printed. Downloads: https from the provider's own file host only (also after redirects), size-capped,
written atomically into a cache named by provider + clip id + rendition, so a clip is fetched once for every project."""
import glob
import http.client
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass

MAX_BYTES = 150 * 1024 * 1024
TIMEOUT = 30  # per socket operation
DEADLINE = 300  # whole download: a trickling stream must not hold the job until its own limit
UA = {"User-Agent": "video-pipeline-broll/1.0"}
HOSTS = {"pexels": {"videos.pexels.com"}}


class StockError(RuntimeError):
    """Search or download failed; the message is shown to the editor (Polish)."""


class ProviderDown(StockError):
    """The search itself failed (no network, bad key, rate limit): every next query would fail the same way."""


@dataclass(frozen=True)
class Clip:
    provider: str
    id: int
    url: str  # the chosen rendition (smallest that still fills the frame)
    width: int
    height: int
    duration: float
    author: str
    page: str  # the clip's page on the provider (credits)
    size: int  # bytes, 0 = unknown

    def as_dict(self) -> dict:
        return asdict(self)


def _host_ok(provider: str, url) -> bool:
    if not isinstance(url, str):
        return False
    u = urllib.parse.urlsplit(url)
    return u.scheme == "https" and u.hostname in HOSTS.get(provider, set())


class _SameHost(urllib.request.HTTPRedirectHandler):
    """Follow a redirect only to an allowed https host: the check runs before the request, not after it."""

    def __init__(self, allowed) -> None:
        self.allowed = allowed

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        u = urllib.parse.urlsplit(newurl)
        if u.scheme != "https" or u.hostname not in self.allowed:
            raise StockError(f"przekierowanie poza dozwolony serwer: {newurl[:80]}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _open(req: urllib.request.Request, allowed):
    return urllib.request.build_opener(_SameHost(allowed)).open(req, timeout=TIMEOUT)


def _pexels_key() -> str:
    key = os.environ.get("PEXELS_API_KEY") or os.environ.get("Pexels")
    if not key:
        raise ProviderDown("brak klucza Pexels: uruchom przez ~/infisical/infisical_bridge.py run --secrets Pexels -- ...")
    return key


def _pexels(query: str, orientation: str, min_w: int, min_h: int, min_dur: float) -> list[Clip]:
    q = urllib.parse.urlencode({"query": query[:100], "orientation": orientation, "size": "medium", "per_page": 15})
    req = urllib.request.Request("https://api.pexels.com/videos/search?" + q, headers=UA)
    req.add_unredirected_header("Authorization", _pexels_key())  # urllib copies plain headers to a redirect's host
    try:
        with _open(req, {"api.pexels.com"}) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        why = {401: "zły klucz API", 403: "zły klucz API", 429: "limit zapytań (200/h): spróbuj za godzinę"}.get(e.code, f"HTTP {e.code}")
        raise ProviderDown(f"Pexels: {why}") from e
    except (OSError, ValueError, http.client.HTTPException) as e:  # URLError/timeout: OSError; bad JSON: ValueError; cut body: IncompleteRead
        raise ProviderDown(f"Pexels: brak połączenia albo zła odpowiedź ({type(e).__name__}): sprawdź internet") from e
    out = []
    for v in data.get("videos", []) if isinstance(data, dict) else []:
        if not isinstance(v, dict) or not isinstance(v.get("id"), int) or not isinstance(v.get("duration"), (int, float)):
            continue
        if v["duration"] < min_dur:
            continue
        files = [f for f in v.get("video_files", []) if isinstance(f, dict) and f.get("file_type") == "video/mp4"
                 and isinstance(f.get("width"), int) and isinstance(f.get("height"), int)
                 and f["width"] >= min_w and f["height"] >= min_h and _host_ok("pexels", f.get("link"))]
        if not files:
            continue
        f = min(files, key=lambda f: f["width"] * f["height"])
        user = v.get("user")
        user = user if isinstance(user, dict) else {}
        out.append(Clip("pexels", v["id"], f["link"], f["width"], f["height"], float(v["duration"]),
                        str(user.get("name", ""))[:100], str(v.get("url", ""))[:300], int(f.get("size") or 0)))
    return out


PROVIDERS = {"pexels": _pexels}


def search(provider: str, query: str, orientation: str, min_w: int, min_h: int, min_dur: float) -> list[Clip]:
    """Clips for query, provider's relevance order; each at least min_w x min_h and min_dur s long."""
    if provider not in PROVIDERS:
        raise ProviderDown(f"nieznany dostawca b-rollu: {provider} (są: {', '.join(PROVIDERS)})")
    return PROVIDERS[provider](query, orientation, min_w, min_h, min_dur)


def cache_name(clip: Clip) -> str:
    return f"{clip.provider}_{int(clip.id)}_{int(clip.width)}x{int(clip.height)}.mp4"


def fetch(clip: Clip, cache_dir: str) -> str:
    """Local path of the clip (downloaded once into cache_dir)."""
    dst = os.path.join(cache_dir, cache_name(clip))
    if os.path.exists(dst):
        return dst
    if not _host_ok(clip.provider, clip.url):
        raise StockError(f"plik spoza serwera {clip.provider}: {clip.url[:80]}")
    if clip.size > MAX_BYTES:
        raise StockError(f"klip {clip.id} za duży ({clip.size // 2**20} MB)")
    os.makedirs(cache_dir, exist_ok=True)
    for old in glob.glob(os.path.join(cache_dir, "*.part")):  # left by a killed job (SIGKILL skips finally)
        if time.time() - os.path.getmtime(old) > 3600:
            os.remove(old)
    tmp = f"{dst}.{os.getpid()}.part"
    end = time.monotonic() + DEADLINE
    try:
        with _open(urllib.request.Request(clip.url, headers=UA), HOSTS.get(clip.provider, set())) as r, open(tmp, "wb") as f:
            if not _host_ok(clip.provider, r.geturl()):
                raise StockError(f"przekierowanie poza serwer {clip.provider}")
            cl = str(r.headers.get("Content-Length") or "")
            want = int(cl) if cl.isdigit() else 0
            n = 0
            while chunk := r.read1(1 << 16):  # read1: one socket read at most, so the deadline is checked every <= TIMEOUT s
                n += len(chunk)
                if n > MAX_BYTES:
                    raise StockError(f"klip {clip.id} przekracza {MAX_BYTES // 2**20} MB")
                if time.monotonic() > end:
                    raise StockError(f"klip {clip.id}: pobieranie dłuższe niż {DEADLINE} s")
                f.write(chunk)
            if n == 0 or (want and n != want):  # a cut connection ends like EOF: never cache a clip without its moov
                raise StockError(f"klip {clip.id} pobrany niecały ({n} z {want or '?'} B)")
        os.replace(tmp, dst)
    except (OSError, http.client.HTTPException) as e:
        raise StockError(f"pobieranie klipu {clip.id} nie powiodło się ({e})") from e
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    return dst
