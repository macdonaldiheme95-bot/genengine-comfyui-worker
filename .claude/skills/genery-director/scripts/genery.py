#!/usr/bin/env python3
"""Read cinematography references from genery.io's public pages.

Genery is a reference library of short scenes from films, TV, music videos and
commercials, each tagged with shot size and camera angle, plus a technique
library (speed ramp, whip pan, dolly zoom, ...). This script reads the same
public pages a visitor's browser loads and turns them into compact text.

Etiquette, enforced here rather than left to the caller:
  * only paths robots.txt allows (never /api/), checked on every request
  * at most one request per second, across invocations
  * pages cached on disk (6h; sitemaps 7d) so repeat lookups cost nothing
  * a per-run request budget (default 25) so a run cannot turn into a crawl

Commands:
  search WORDS...         find titles (films, shows, music videos, ads) by name
  effects                 list the technique library
  effect SLUG             frames tagged with one technique
  title SLUG              frames from one title
  director NAME|SLUG      titles by one director
  stills URL...           cache stills locally so they can be looked at

Run any command with -h for its options. Python 3.8+, standard library only.
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from pathlib import Path

try:
    import fcntl
except ImportError:  # Windows: runs still throttle, just not across parallel processes
    fcntl = None

SITE = "https://genery.io"
USER_AGENT = "genery-director-skill/0.1 (reference lookup for a Claude Code skill; low rate)"
MIN_INTERVAL_S = 1.0
PAGE_TTL_S = 6 * 3600          # signed clip links on a page stay valid ~24h
SITEMAP_TTL_S = 7 * 24 * 3600
ROBOTS_TTL_S = 24 * 3600

CACHE = Path(os.environ.get("GENERY_CACHE") or Path.home() / ".cache" / "genery-director")

_budget = {"left": 25}
_stats = {"requests": 0, "cached": 0}
_robots = None


class BudgetExceeded(RuntimeError):
    pass


# ── network ─────────────────────────────────────────────────────────────────

def _throttle():
    """Space requests MIN_INTERVAL_S apart, even across parallel runs."""
    CACHE.mkdir(parents=True, exist_ok=True)
    stamp = CACHE / "last_request"
    with open(CACHE / "lock", "w") as lock:
        if fcntl:
            fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            wait = MIN_INTERVAL_S - (time.time() - stamp.stat().st_mtime)
            if wait > 0:
                time.sleep(wait)
        except FileNotFoundError:
            pass
        stamp.touch()


def _download(url):
    if _budget["left"] <= 0:
        raise BudgetExceeded(
            "request budget for this run is spent; narrow the search or pass --max-requests")
    _budget["left"] -= 1
    _stats["requests"] += 1
    _throttle()
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def _allowed(url):
    global _robots
    if _robots is None:
        _robots = urllib.robotparser.RobotFileParser()
        _robots.parse(fetch_text(SITE + "/robots.txt", ROBOTS_TTL_S, check_robots=False).splitlines())
    return _robots.can_fetch(USER_AGENT, url)


def fetch_bytes(url, ttl, check_robots=True, subdir="pages", suffix=".html"):
    path = CACHE / subdir / (hashlib.sha1(url.encode()).hexdigest() + suffix)
    if path.exists() and time.time() - path.stat().st_mtime < ttl:
        _stats["cached"] += 1
        return path.read_bytes()
    if check_robots and url.startswith(SITE) and not _allowed(url):
        raise PermissionError(f"robots.txt disallows {url}")
    data = _download(url)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return data


def fetch_text(url, ttl=PAGE_TTL_S, check_robots=True):
    return fetch_bytes(url, ttl, check_robots).decode("utf-8", "replace")


# ── parsing ─────────────────────────────────────────────────────────────────
# Pages are server-rendered and embed their data as a JS object stream
# ($R[n]={...}). Each frame record looks like:
#   {350:"<still>",650:"<still>",id:"<uuid>",...,scene:$R[n]={url:"<hls>",
#    sceneTimestamp:..,sceneTimestampStart:..,sceneTimestampEnd:..},
#    aspectRatio:1.78,nsfw:"neutral",aestheticScore:6.07,alt:"Movie still from
#    “Ford Kuga - Levels” (2021) – Extreme Wide shot, High angle"}

JS_STR = r'"((?:[^"\\]|\\.)*)"'
FRAME_RE = re.compile(
    r'\{350:"(?P<s350>[^"]+)",650:"(?P<s650>[^"]+)",id:"(?P<id>[0-9a-f-]{36})",'
    r'(?P<body>(?:(?!\{350:").)*?)alt:' + JS_STR + r'(?=[,}])', re.S)
ALT_RE = re.compile(
    r'^.*?from “(?P<title>.+?)” \((?P<year>\d{4})\)(?:, directed by (?P<director>.+?))?'
    r'\s*–\s*(?P<rest>.*)$', re.S)
SHOT_RE = re.compile(r'(?:^|;\s*)(?P<shot>[A-Za-z][A-Za-z \-]*?) shot(?:, (?P<angle>[A-Za-z][A-Za-z \-]*?) angle)?\s*$')
TITLE_ITEM_RE = re.compile(
    r'slug:' + JS_STR + r',type:' + JS_STR + r',title:' + JS_STR + r',year:(\d+)')


def js_unescape(s):
    try:
        return json.loads('"' + s + '"')
    except ValueError:
        return s


def num(body, key):
    m = re.search(r'\b' + key + r':(-?[\d.]+(?:e-?\d+)?)', body)
    return float(m.group(1)) if m else None


def slug_words(name):
    s = unicodedata.normalize("NFKD", name.replace("ß", "ss")).encode("ascii", "ignore").decode()
    s = re.sub(r"['’]", "", s.lower())
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def slugify(name, year):
    return f"{slug_words(name)}-{year}"


def parse_frames(page):
    frames, seen = [], set()
    for m in FRAME_RE.finditer(page):
        if m["id"] in seen:
            continue
        seen.add(m["id"])
        body, alt = m["body"], js_unescape(m[5])
        f = {
            "id": m["id"],
            "still": m["s650"],
            "still_small": m["s350"],
            "aesthetic": num(body, "aestheticScore"),
            "aspect": num(body, "aspectRatio"),
            "at_s": num(body, "timestamp") or num(body, "sceneTimestamp"),
            "clip_start_s": num(body, "sceneTimestampStart"),
            "clip_end_s": num(body, "sceneTimestampEnd"),
            "alt": alt,
        }
        clip = re.search(r'scene:\$R\[\d+\]=\{url:"([^"]+)"', body)
        f["clip_hls_expiring"] = clip.group(1) if clip else None
        a = ALT_RE.match(alt)
        if a:
            f["title"], f["year"] = a["title"], int(a["year"])
            f["director"] = a["director"]
            f["title_slug"] = slugify(a["title"], a["year"])
            rest = a["rest"].strip()
            s = SHOT_RE.search(rest)
            f["shot"] = s["shot"] if s else None
            f["angle"] = s["angle"] if s else None
            f["description"] = (rest[:s.start()] if s else rest).strip(" ;") or None
        frames.append(f)
    return frames


def ld_json(page):
    m = re.search(r'<script type="application/ld\+json">(.*?)</script>', page, re.S)
    if not m:
        return {}
    try:
        data = json.loads(m.group(1))
    except ValueError:
        return {}
    for node in data.get("@graph", [data]):
        if node.get("@type") != "BreadcrumbList":
            return node
    return {}


# ── title index (from the public sitemap) ───────────────────────────────────

def title_index():
    xml = fetch_text(SITE + "/sitemaps/sitemap-scenes.xml", SITEMAP_TTL_S)
    return re.findall(r"<loc>https://genery\.io/title/([^<]+)</loc>", xml)


# ── filtering and output ────────────────────────────────────────────────────

def apply_filters(frames, a):
    def has(value, wanted):
        return wanted is None or (value or "").lower().find(wanted.lower()) >= 0
    if a.contains and frames and not any(f.get("description") for f in frames):
        print("note: this page has no frame captions (ads and technique pages usually don't);"
              " --contains is matching title names only", file=sys.stderr)
    out = [f for f in frames
           if has(f.get("shot"), a.shot) and has(f.get("angle"), a.angle)
           and (has(f.get("description"), a.contains) or has(f.get("title"), a.contains))
           and (a.min_score is None or (f["aesthetic"] or 0) >= a.min_score)]
    out.sort(key=lambda f: -(f["aesthetic"] or 0))
    return out[: a.top] if a.top else out


def fmt_s(x):
    """Seconds as m:ss or h:mm:ss, the way an editor or player shows them."""
    if x is None:
        return "?"
    h, rem = divmod(int(x), 3600)
    m, sec = divmod(rem, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m}:{sec:02d}"


def when(f):
    if f.get("clip_start_s") is not None:
        return f"clip {fmt_s(f['clip_start_s'])}–{fmt_s(f['clip_end_s'])}"
    return f"at {fmt_s(f['at_s'])}" if f.get("at_s") is not None else ""


def print_frames(frames, show_title):
    for i, f in enumerate(frames, 1):
        head = f"{i:>2}. [{f['aesthetic'] or 0:.2f}] {f.get('shot') or '?'} shot, {f.get('angle') or '?'} angle"
        if f.get("aspect"):
            head += f", {f['aspect']:.2f}:1"
        print(head)
        if show_title and f.get("title"):
            by = f" — dir. {f['director']}" if f.get("director") else ""
            print(f"    {f['title']} ({f['year']}){by}  {SITE}/title/{f['title_slug']}")
        if f.get("description"):
            print(f"    {f['description']}")
        if when(f):
            print(f"    {when(f)}")
        print(f"    still {f['still']}")


def print_compact(frames, show_title):
    for i, f in enumerate(frames, 1):
        cells = [f"{i:>3}", f"{f['aesthetic'] or 0:.2f}", f"{f.get('shot') or '?'}/{f.get('angle') or '?'}"]
        if show_title:
            cells.append(f.get("title_slug") or "?")
        cells += [when(f), (f.get("description") or "")[:60], f["still"]]
        print(" | ".join(c for c in cells if c))


def print_by_title(frames):
    groups = {}
    for f in frames:
        groups.setdefault(f.get("title_slug") or "?", []).append(f)
    rows = sorted(groups.items(), key=lambda kv: -max(f["aesthetic"] or 0 for f in kv[1]))
    print(f"titles: {len(rows)} (best score, frame count, shot sizes)\n")
    for slug, fs in rows:
        f0 = fs[0]
        sizes = ", ".join(sorted({f.get("shot") or "?" for f in fs}))
        by = f" — dir. {f0['director']}" if f0.get("director") else ""
        print(f"[{max(f['aesthetic'] or 0 for f in fs):.2f}] x{len(fs):<3} {f0.get('title', '?')} ({f0.get('year', '?')}){by}")
        print(f"    {SITE}/title/{slug}   {sizes}")


def emit(obj, frames, a, show_title):
    if a.json:
        obj["frames"] = frames
        json.dump(obj, sys.stdout, indent=1, ensure_ascii=False)
        print()
        return
    for k, v in obj.items():
        if v:
            print(f"{k}: {', '.join(v) if isinstance(v, list) else v}")
    if getattr(a, "by_title", False):
        print_by_title(frames)
        return
    print(f"frames: {len(frames)} shown (sorted by genery aesthetic score)\n")
    (print_compact if a.compact else print_frames)(frames, show_title)


# ── commands ────────────────────────────────────────────────────────────────

def cmd_search(a):
    words = [w for w in slug_words(" ".join(a.words)).split("-") if w]
    def matches(slug):
        parts = slug.split("-")
        return all(any(p.startswith(w) for p in parts) for w in words)
    hits = [s for s in title_index() if matches(s)]
    if a.year:
        hits = [s for s in hits if s.endswith(str(a.year))]
    for s in hits[: a.limit]:
        print(s)
    if len(hits) > a.limit:
        print(f"... {len(hits) - a.limit} more; add words to narrow")
    if not hits:
        print("no titles match; try fewer or different words, or a technique instead"
              " (genery's catalog is broad but not every brand is in it)")


def cmd_effects(a):
    page = fetch_text(SITE + "/effects", SITEMAP_TTL_S)
    items = dict.fromkeys(re.findall(r'href="/effects/([a-z0-9-]+)"', page))
    for slug in items:
        print(slug)


def cmd_effect(a):
    page = fetch_text(f"{SITE}/effects/{a.slug}")
    m = re.search(r'metadata:\$R\[\d+\]=\{id:"eff_[^"]*",slug:"[^"]*",title:' + JS_STR, page)
    d = re.search(r'metadata:\$R\[\d+\]=\{id:"eff_.*?description:' + JS_STR, page, re.S)
    obj = {
        "technique": js_unescape(m.group(1)) if m else a.slug,
        "definition": js_unescape(d.group(1)) if d else None,
        "page": f"{SITE}/effects/{a.slug}",
    }
    emit(obj, apply_filters(parse_frames(page), a), a, show_title=True)


def cmd_title(a):
    page = fetch_text(f"{SITE}/title/{a.slug}")
    meta = ld_json(page)
    directors = [d.get("name") for d in meta.get("director", []) if isinstance(d, dict)]
    obj = {
        "title": meta.get("name"),
        "year": meta.get("datePublished"),
        "type": meta.get("@type"),
        "directors": directors,
        "director_pages": [d.get("url") for d in meta.get("director", []) if isinstance(d, dict)],
        "genres": meta.get("genre"),
        "page": f"{SITE}/title/{a.slug}",
    }
    if not a.json and meta.get("description"):
        obj["synopsis"] = meta["description"][:300]
    emit(obj, apply_filters(parse_frames(page), a), a, show_title=False)


def cmd_director(a):
    slug = slug_words(a.name)
    page = fetch_text(f"{SITE}/people/{slug}")
    titles = {}
    for s, typ, t, y in TITLE_ITEM_RE.findall(page):
        titles.setdefault(s, (js_unescape(t), y, typ))
    if a.json:
        json.dump({"director": slug, "page": f"{SITE}/people/{slug}",
                   "titles": [{"slug": s, "title": t, "year": int(y), "type": typ}
                              for s, (t, y, typ) in titles.items()]}, sys.stdout, indent=1)
        print()
        return
    print(f"director: {slug}  {SITE}/people/{slug}")
    for s, (t, y, typ) in titles.items():
        print(f"  {s}  — {t} ({y}) [{typ}]")
    if not titles:
        print("  no titles found; check the slug (try `search` on a known film and read its director_pages)")


def cmd_stills(a):
    """Cache stills so Claude can look at them with its image-reading tool."""
    for u in a.refs:
        if not re.match(r"https://cdn\.genery\.online/\S+\.(jpg|jpeg|webp|png)$", u):
            raise SystemExit(f"not a genery still URL: {u}")
        name = hashlib.sha1(u.encode()).hexdigest()[:16] + ".jpg"
        path = CACHE / "stills" / name
        if path.exists():
            _stats["cached"] += 1
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(_download(u))
        print(path)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--max-requests", type=int, default=25,
                   help="network requests allowed this run (cache hits are free); default 25")
    sub = p.add_subparsers(dest="cmd", required=True)

    def frame_opts(sp):
        sp.add_argument("--shot", help="shot size contains, e.g. 'close up', 'extreme wide', 'medium'")
        sp.add_argument("--angle", help="angle contains, e.g. 'low', 'high', 'over the shoulder'")
        sp.add_argument("--contains", help="caption or title contains this text, e.g. 'car', 'nike'"
                        " (captions exist on film/TV pages, rarely on ads or technique pages)")
        sp.add_argument("--min-score", type=float, help="minimum genery aesthetic score (most fall 5-6.5)")
        sp.add_argument("--top", type=int, default=12, help="how many frames to show (0 = all); default 12")
        sp.add_argument("--compact", action="store_true", help="one line per frame, for scanning long lists")
        sp.add_argument("--json", action="store_true", help="machine-readable output")

    sp = sub.add_parser("search", help="find title slugs by name words")
    sp.add_argument("words", nargs="+")
    sp.add_argument("--year", type=int)
    sp.add_argument("--limit", type=int, default=30)
    sp.set_defaults(fn=cmd_search)

    sp = sub.add_parser("effects", help="list technique slugs")
    sp.set_defaults(fn=cmd_effects)

    sp = sub.add_parser("effect", help="frames for one technique, e.g. speed-ramp")
    sp.add_argument("slug")
    frame_opts(sp)
    sp.add_argument("--by-title", action="store_true",
                    help="summarise which titles show this technique (applies filters, ignores --top)")
    sp.set_defaults(fn=cmd_effect)

    sp = sub.add_parser("title", help="frames from one title, e.g. ford-kuga-levels-2021")
    sp.add_argument("slug")
    frame_opts(sp)
    sp.set_defaults(fn=cmd_title)

    sp = sub.add_parser("director", help="titles by a director, e.g. 'Sidney Lumet' or sidney-lumet")
    sp.add_argument("name")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(fn=cmd_director)

    sp = sub.add_parser("stills", help="cache still images locally and print their paths")
    sp.add_argument("refs", nargs="+", help="still URLs from effect/title output")
    sp.set_defaults(fn=cmd_stills)

    a = p.parse_args(argv)
    _budget["left"] = a.max_requests
    if getattr(a, "by_title", False):
        a.top = 0
    try:
        a.fn(a)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"genery returned HTTP {e.code} for {e.url}"
                         + (" (check the slug with `search`)" if e.code == 404 else ""))
    except (BudgetExceeded, PermissionError) as e:
        raise SystemExit(str(e))
    except BrokenPipeError:  # output piped into head etc.
        sys.stdout = open(os.devnull, "w")
    finally:
        print(f"[genery: {_stats['requests']} network requests, {_stats['cached']} from cache;"
              f" cache {CACHE}]", file=sys.stderr)


if __name__ == "__main__":
    main()
