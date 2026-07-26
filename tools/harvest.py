#!/usr/bin/env python3
"""Harvesting Open Archives — the shift from searching to holding.

Every other route into these records is a person-at-a-time browser session behind a
login: slow, unreproducible for anyone else, and it throws away five of the six people
a marriage act names. Open Archives publishes the same material as open data over an
unauthenticated JSON API — around thirty million Belgian person-mentions, including the
Familiekunde Vlaanderen and Doodsprentjes.be memorial cards and the Rijksarchief civil
acts transcribed by the Demogen volunteers — so the act can be pulled once, kept, and
joined against every open frontier at once. That is what family reconstitution has
always done, and what a person-indexed search log cannot do.

Two phases, because the API has two levels. A SEARCH returns person-MENTIONS: one row
per person per act. An ACT — fetched by (archive, identifier) — returns the whole
record: every participant, their role, their age, their birthplace, the act number, and
a link to the scan. The mentions say which acts exist; the acts are the evidence.

Harvesting stops there and makes no claim about who any of them is. Linking them to the
tree is tools/link.py, and grafting is still a decision made under the rules in
CLAUDE.md.

A SEARCH is still one request per act, and that is the wall a province runs into: at the
four requests a second the venue permits, Belgium's ~30 million person-mentions are about
a month of continuous fetching. The same records are published whole — a gzipped export
per archive, and an OAI-PMH feed serving 150 full records a request — so `bulk` and `oai`
below fetch an entire archive for the price of a few searches, and produce acts that
normalise identically to the ones fetched one at a time. Reach for those first; the
per-act route is for the archives that publish neither, which unfortunately includes the
Rijksarchief and Familiekunde sets this tree mostly rests on.

    uv run tools/harvest.py bulk gnt                a whole archive in ONE request
    uv run tools/harvest.py oai den                 a whole archive, 150 acts a request
    uv run tools/harvest.py surname Bundervoet
    uv run tools/harvest.py surname "Van Craenenbroeck" --place Zaventem
    uv run tools/harvest.py place Oostende
    uv run tools/harvest.py frontiers --limit 5      harvest what the queue asks for
    uv run tools/harvest.py status                  what is held, and what is missing

The cache is authoritative: nothing already held is re-fetched. `--refresh` overrides
that for one run. The store is gitignored because it is re-fetchable open data that
grows without limit; research/harvest/manifest.json is committed instead, so the exact
queries — and therefore the corpus — are reproducible from the repository alone.
"""

from __future__ import annotations

import argparse
import datetime as dt
import gzip
import io
import json
import re
import sys
import threading
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))

from familytree import store  # noqa: E402
from familytree.a2a import read_acts  # noqa: E402
from familytree.corpus import (  # noqa: E402
    ACTS_DIR, HARVEST, MANIFEST, MENTIONS_DIR, load_manifest, reset_manifest_cache,
)
from familytree.frontier import frontier_rows  # noqa: E402
from familytree.people import family_key, load_config, load_people  # noqa: E402

API = "https://api.openarch.nl/1.1"
# Open Archives asks for a descriptive user-agent so they can get in touch, and
# throttles to four requests a second per IP. Going under that deliberately: losing
# access to the one open venue in the registry would cost far more than the wait.
UA = "family-tree/0.1 (genealogy research; contact via repository)"
RATE = 3.0        # requests a second, aggregate across every worker
WORKERS = 4       # concurrent act fetches
PAGE = 100

# Where the same records can be had without paying a request per act. See familytree/a2a.py
# for why these are equivalent to `records/show` and how that was checked.
BULK = "https://oa-export.s3.nl-ams.scw.cloud/xml/{archive}.xml.gz"
BULK_INDEX = "https://www.openarchieven.nl/exports/xml/"
OAI = "http://api.openarch.nl/oai-pmh/"


class Throttle:
    """The four-a-second limit, enforced across threads instead of between them.

    The old form was a single `_last_call` timestamp and a sleep to the next slot, which
    is correct for one thread and also means the gap starts when the previous request
    RETURNS. With a 300 ms round trip that is 0.3 s of waiting plus 0.3 s of flight per
    act — about 1.6 requests a second against a budget of four, and the difference is
    pure latency rather than politeness.

    A token bucket separates the two: the rate is what the venue asked for, and the
    workers only decide how much of it is left idle. Four workers against a 3/s bucket
    stays under the published limit whatever the network does.
    """

    def __init__(self, rate: float):
        self.gap = 1.0 / rate
        self.lock = threading.Lock()
        self.next_at = 0.0

    def wait(self) -> None:
        with self.lock:
            now = time.monotonic()
            at = max(now, self.next_at)
            self.next_at = at + self.gap
        if at > now:
            time.sleep(at - now)


_throttle = Throttle(RATE)


class Blocked(RuntimeError):
    """Never reached the material. The same distinction the search log draws between
    `blocked` and `miss`: nothing was read, so nothing is exhausted."""


def api(endpoint: str, params: dict) -> dict:
    url = f"{API}/{endpoint}.json?" + urllib.parse.urlencode(params)
    for attempt in range(1, 5):
        _throttle.wait()
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=60) as res:
                body = json.loads(res.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            # 429 and 5xx are "come back later", not "nothing there".
            if e.code == 429 or e.code >= 500:
                if attempt == 4:
                    raise Blocked(f"{endpoint}: HTTP {e.code} after {attempt} attempts") from e
                time.sleep(2 * attempt)
                continue
            raise Blocked(f"{endpoint}: HTTP {e.code}") from e
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt == 4:
                raise Blocked(f"{endpoint}: {e}") from e
            time.sleep(attempt)
            continue
        if body.get("error_code"):
            raise Blocked(f"{endpoint}: {body.get('error_description')}")
        return body
    raise Blocked(f"{endpoint}: gave up")


def slug(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower())
    return re.sub(r"^-|-$", "", re.sub(r"[^a-z0-9]+", "-", s))


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").split("\n") if line.strip()]


def save_manifest(entry: dict | None = None, population: dict | None = None) -> None:
    """Read, merge, write — never write back a copy read minutes ago.

    A surname harvest is thousands of sequential requests and can run for a quarter of
    an hour. Holding the manifest in memory for that long and saving it at the end
    silently erased every harvest that finished in between: the acts survived on disk,
    but the record of which query produced them — and the `found` count that every
    rarity weight is measured against — did not.

    `load_manifest` is cached now, which would reintroduce that bug in a subtler form —
    the copy read here would be however old this process is — so the cache is dropped on
    both sides of the write: before, so the merge is against what is on disk now, and
    after, so the next reader sees what was just merged.
    """
    HARVEST.mkdir(parents=True, exist_ok=True)
    reset_manifest_cache()
    manifest = load_manifest()
    if population:
        manifest.setdefault("population", population)
    if entry:
        manifest["harvests"] = [h for h in manifest["harvests"] if h["id"] != entry["id"]] + [entry]
    manifest["harvests"].sort(key=lambda h: h["id"])
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    reset_manifest_cache()


def held_act_ids() -> set[str]:
    """Acts are shared between harvests — one Zaventem marriage answers a surname query
    and a commune query both — so they are stored once, by archive, and never twice."""
    held: set[str] = set()
    if ACTS_DIR.is_dir():
        for f in ACTS_DIR.glob("*.jsonl"):
            held |= {a["id"] for a in read_jsonl(f)}
    return held


def fetch_mentions(params: dict, cap: int) -> tuple[list[dict], int | None]:
    """Every mention matching the query, paged to exhaustion.

    The API caps a page at 100 and reports the true total, so a partial harvest is
    recorded as partial rather than looking complete.
    """
    docs: list[dict] = []
    total: int | None = None
    start = 0
    while total is None or start < min(total, cap):
        body = api("records/search", {**params, "number_show": PAGE, "start": start})
        if total is None:
            total = body["response"]["number_found"]
            print(f"  {total} mentions" + (f" (capping at {cap})" if total > cap else ""))
        page = body["response"].get("docs") or []
        if not page:
            break
        docs += page
        print(f"\r  fetched {len(docs)}…", end="", flush=True)
        start += PAGE
    if docs:
        print()
    return docs, total


def fetch_acts(mentions: list[dict], refresh: bool) -> tuple[int, int]:
    """The acts behind those mentions.

    Several mentions share one act — the child, the father and the mother of a birth are
    three rows against one record — so this is where the person-indexed view collapses
    into the event-indexed one.
    """
    held = set() if refresh else held_act_ids()
    wanted: dict[str, dict] = {}
    for m in mentions:
        key = f"{m['archive_code']}:{m['identifier']}"
        if key not in held:
            wanted[key] = m
    if not wanted:
        print("  all acts already held")
        return 0, len(mentions)

    print(f"  {len(wanted)} acts to fetch ({len(mentions) - len(wanted)} already held)")
    ACTS_DIR.mkdir(parents=True, exist_ok=True)

    # Dropping the stale copies up front, so a refresh replaces them rather than leaving
    # two versions of the same act in the store. Everything after this only appends.
    if refresh:
        for stale in ACTS_DIR.glob("*.jsonl"):
            keep = [a for a in read_jsonl(stale) if a["id"] not in wanted]
            stale.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in keep), encoding="utf-8")

    # Written as they arrive rather than held until the end. A common surname is
    # thousands of requests over several minutes; writing only on success meant a
    # Ctrl-C, a dropped connection or a closed laptop threw all of it away and the next
    # run started from nothing.
    # Concurrent, because the limit that matters is the venue's four-a-second and a
    # single thread never reaches it — it spends most of each slot waiting for the
    # previous response to come back. The rate itself is unchanged and enforced centrally
    # by `Throttle`, so this is the same politeness at closer to the permitted speed.
    handles: dict[str, object] = {}
    write_lock = threading.Lock()
    done = 0
    today = dt.date.today().isoformat()

    def fetch(item):
        key, m = item
        try:
            record = api("records/show", {"archive": m["archive_code"], "identifier": m["identifier"]})
        except Blocked as e:
            return key, e, None
        return key, None, {
            "id": key,
            "archive": m["archive_code"],
            "archive_org": m.get("archive_org"),
            "fetched": today,
            "record": record,
        }

    try:
        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            for key, error, row in pool.map(fetch, wanted.items()):
                if error is not None:
                    print(f"\n  skipped {key}: {error}")
                    continue
                # One writer at a time. The workers only fetch; the file handles are
                # shared, and a half-written line is a corrupt act that survives every
                # future run of the harvester.
                with write_lock:
                    archive = row["archive"]
                    if archive not in handles:
                        handles[archive] = (ACTS_DIR / f"{archive}.jsonl").open("a", encoding="utf-8")
                    handles[archive].write(json.dumps(row, ensure_ascii=False) + "\n")
                    # Flushed per act: the point of streaming is that an interrupted
                    # harvest keeps what it already paid for, and a buffered line is a
                    # lost one.
                    handles[archive].flush()
                    done += 1
                    print(f"\r  fetched {done}/{len(wanted)} acts…", end="", flush=True)
    finally:
        for h in handles.values():
            h.close()
    print()
    return done, len(mentions) - len(wanted)


def record_population() -> None:
    """How many Belgian person-mentions the venue holds in total.

    One query, once, and it is the denominator every rarity weight depends on: a
    surname is only rare relative to a population, and the harvest cannot supply that
    figure about itself because it is filtered to the surname it was run for.
    """
    if load_manifest().get("population", {}).get("be"):
        return
    body = api("records/search", {"name": "*", "country_code": "be", "number_show": 1})
    save_manifest(population={"be": body["response"]["number_found"], "counted": dt.date.today().isoformat()})


def harvest(harvest_id: str, label: str, params: dict, cap: int, refresh: bool) -> dict:
    manifest = load_manifest()
    previous = next((h for h in manifest["harvests"] if h["id"] == harvest_id), None)
    if previous and not refresh:
        print(f"{label}\n  already harvested {previous['date']} — {previous['mentions']} mentions, "
              f"{previous['acts']} acts. Use --refresh to redo.\n")
        return previous

    print(label)
    record_population()
    docs, total = fetch_mentions(params, cap)
    MENTIONS_DIR.mkdir(parents=True, exist_ok=True)
    (MENTIONS_DIR / f"{harvest_id}.jsonl").write_text(
        "\n".join(json.dumps(d, ensure_ascii=False) for d in docs) + "\n", encoding="utf-8"
    )
    fetched, already = fetch_acts(docs, refresh)

    entry = {
        "id": harvest_id,
        "query": params,
        "date": dt.date.today().isoformat(),
        "found": total,
        "mentions": len(docs),
        # The honest bit: say when the harvest is a sample rather than the whole thing,
        # because a capped harvest that looks complete is the corpus equivalent of an
        # unlogged miss.
        "complete": total is not None and len(docs) >= total,
        "acts": fetched + already,
    }
    save_manifest(entry)
    print(f"  → {entry['mentions']}/{entry['found']} mentions, {entry['acts']} acts"
          + ("" if entry["complete"] else " — PARTIAL") + "\n")
    return entry


# ---------- whole archives, without a request per act ----------


def _open(url: str, accept: str = "*/*"):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    try:
        return urllib.request.urlopen(req, timeout=300)
    except urllib.error.HTTPError as e:
        # The export bucket answers 403, not 404, for an archive it does not carry, so
        # "no bulk export" and "refused" look identical from here and both mean the same
        # thing to the caller: this route is not available, try another.
        raise Blocked(f"{url}: HTTP {e.code}") from e
    except (urllib.error.URLError, TimeoutError) as e:
        raise Blocked(f"{url}: {e}") from e


def archive_countries() -> dict[str, str]:
    """Which country each archive belongs to, according to the venue's own register.

    Read from the ISIL code `stats/archives` publishes — `NL-HtBHIC`, `NL-MdbZA` — whose
    prefix is the ISO country. Derived in one request rather than kept as a list here,
    because the register grows and a stale copy would silently mis-classify.

    An absent ISIL means UNREGISTERED, not Belgian. 133 of the 207 archives have none, and
    every Belgian one in this corpus is among them — but that is a correlation, and turning
    it into "no ISIL therefore Belgium" is exactly the inference this project refuses to
    make. So the caller gets "" and treats it as unknown.
    """
    try:
        with _open(f"{API}/stats/archives.json?number_show=500", "application/json") as res:
            rows = json.loads(res.read().decode("utf-8"))
    except (Blocked, json.JSONDecodeError):
        return {}
    return {r["archive_code"]: (r.get("isilcode") or "").split("-")[0]
            for r in rows if r.get("archive_code")}


def out_of_scope(archive: str) -> str | None:
    """Why a whole-archive pull would be the wrong thing, or None.

    The trap this exists for: the corpus holds Oostende and Bredene acts from Zeeuws
    Archief and Historisch Centrum Limburg, which look like Belgian archives and are not.
    They are only in the corpus because every API harvest was filtered `country_code=be`.
    Their EXPORTS are the whole archive — Zeeuws Archief alone is millions of Dutch
    records — so pulling one floods the corpus with material no objective in CLAUDE.md
    asks for, and skews the fallback rarity weights in `frequencies()` toward Dutch name
    distributions while `population()` still measures against 30 million Belgian mentions.

    A country filter at parse time would be the general answer, and it needs the
    historical gazetteer that docs/method/scaling.md lists as future work. Until then this
    refuses the known-wrong case and says why.
    """
    country = archive_countries().get(archive, "")
    if country and country != "BE":
        return (f'"{archive}" is registered in {country}, not Belgium. Its export is the '
                f"whole archive, and only the sliver about Belgian events is in scope.")
    return None


def bulk_archives() -> set[str]:
    """Which archives publish a whole-archive export. Read from the index, not hardcoded —
    the list grows as archives join, and a stale copy here would quietly send the harvester
    back to fetching one act at a time."""
    try:
        with _open(BULK_INDEX, "text/html") as res:
            html = res.read().decode("utf-8", "replace")
    except Blocked:
        return set()
    return set(re.findall(r"/xml/\./([a-z0-9]+)\.xml\.gz", html))


def _held_in(archive: str) -> int:
    """How many acts are actually on disk for one archive — the figure the manifest owes."""
    path = ACTS_DIR / f"{archive}.jsonl"
    if not path.exists():
        return 0
    with path.open("rb") as f:
        return sum(1 for line in f if line.strip())


def write_acts(rows, archive: str, refresh: bool) -> tuple[int, int, Exception | None]:
    """Stream acts into the store, skipping the ones already held.

    Shared by both bulk routes. The dedup is on the act id, which `a2a.act_id` mints to
    match the JSON API's exactly — so pulling an archive in bulk after months of per-act
    harvesting adds only what is genuinely new, and the acts already cited by records in
    the tree keep the ids those citations use.
    """
    held = set() if refresh else held_act_ids()
    ACTS_DIR.mkdir(parents=True, exist_ok=True)
    today = dt.date.today().isoformat()
    added = skipped = 0
    error: Exception | None = None
    with (ACTS_DIR / f"{archive}.jsonl").open("a", encoding="utf-8") as f:
        # The iterator is a live network stream, so it can fail part-way through — and the
        # acts written before it failed are on disk and held. Catching here rather than in
        # the caller is what lets the count survive the failure: returning only on success
        # meant a dropped connection recorded "0 acts" for an archive whose file had just
        # grown by three and a half thousand, which is the same lie as a capped harvest
        # reported as complete.
        try:
            for row in rows:
                if row["id"] in held:
                    skipped += 1
                    continue
                held.add(row["id"])
                f.write(json.dumps({**row, "fetched": today}, ensure_ascii=False) + "\n")
                added += 1
                if added % 2000 == 0:
                    f.flush()
                    print(f"\r  {added} new acts, {skipped} already held…", end="", flush=True)
        except (OSError, EOFError, ET.ParseError) as e:
            # A dropped stream, a truncated gzip member, and XML ending mid-element are the
            # same event seen at three layers.
            error = e
    print(f"\r  {added} new acts, {skipped} already held.        ")
    return added, skipped, error


def cmd_bulk(args):
    """Whole archives, one request each.

    This is the route that changes the arithmetic. Kortrijk holds 140,543 acts; fetching
    them one at a time at the permitted rate is thirteen hours, and the export is a 19 MB
    download. Where an archive publishes one, nothing else should be used.

    Takes several archives because the index is rebuilt once per invocation: pulling nine
    of them one command at a time means nine rebuilds over a corpus that is growing each
    time, and the last one is the only rebuild that was ever needed.
    """
    failed = []
    for archive in args.archive:
        # One archive failing must not take the rest of the run with it. A batch of nine is
        # half an hour of downloading, and losing the eight that would have worked because
        # the first connection dropped is the difference between a tool and a demonstration.
        try:
            if not _bulk_one(archive.lower(), args):
                failed.append(archive.lower())
        except Blocked as e:
            print(f"  {archive}: {e}", file=sys.stderr)
            failed.append(archive.lower())
    if failed:
        print(f"\n{len(failed)} archive(s) did not complete: {', '.join(failed)}")
        print("  Nothing is lost — what arrived is held, and a re-run skips it by act id:")
        print(f"    uv run tools/harvest.py bulk {' '.join(failed)}")


def _bulk_one(archive: str, args) -> bool:
    """One whole archive. True if it completed, False if it did not.

    A partial pull is recorded as partial, for the same reason a capped surname search is:
    a harvest that looks complete and is not is the corpus equivalent of an unlogged miss,
    and every later report would read the gap as evidence of absence.
    """
    if (why := out_of_scope(archive)) and not args.anyway:
        print(f"refusing to bulk-harvest {archive}\n  {why}\n\n"
              "  Keep using the country-filtered API for this one — it returns only the\n"
              f'  Belgian records:  uv run tools/harvest.py surname "<name>"\n\n'
              "  Pass --anyway if you really do want the whole archive.", file=sys.stderr)
        return True
    url = BULK.format(archive=archive)
    print(f"Bulk export — {archive}\n  {url}")

    added = skipped = 0
    complete = False
    # Retried, because a multi-megabyte stream from a CDN drops sometimes and a gzip
    # stream cannot be resumed mid-way. Restarting is cheap in the only sense that
    # matters: `write_acts` skips by act id, so a second attempt re-reads the export but
    # writes only what the first one did not reach.
    for attempt in range(1, 4):
        try:
            res = _open(url, "application/gzip")
        except Blocked as e:
            available = sorted(bulk_archives())
            print(f"  no bulk export for \"{archive}\" ({e})", file=sys.stderr)
            if available:
                print(f"\n  {len(available)} archives do publish one: {', '.join(available)}", file=sys.stderr)
            print(f"\n  For this one, try OAI-PMH instead — still 150 acts a request:\n"
                  f"    uv run tools/harvest.py oai {archive}", file=sys.stderr)
            return True   # not a failure to retry: this archive has no export
        with res:
            size = res.headers.get("Content-Length")
            if size and attempt == 1:
                print(f"  {int(size) / 1048576:.0f} MB compressed — streamed, never held whole")
            got, seen, error = write_acts(read_acts(gzip.GzipFile(fileobj=res), archive), archive, args.refresh)
        # Counted whether or not the stream finished: those acts are on disk and held.
        added += got
        skipped = seen
        if error is None:
            complete = True
            break
        print(f"  attempt {attempt}: stream failed after {added} new acts — "
              f"{type(error).__name__}: {error}", file=sys.stderr)
        if attempt < 3:
            time.sleep(3 * attempt)

    # Counted off the file rather than from this run's tallies. A run that dies part-way
    # has seen fewer acts than are held — `ell` reported 1,859 while its file held 3,584
    # from an earlier attempt — and a count that is lower than the truth is still a count
    # that is not the truth.
    held = _held_in(archive)
    save_manifest({
        "id": f"archive-{archive}",
        "query": {"archive": archive, "via": "bulk"},
        "date": dt.date.today().isoformat(),
        "found": held,
        "mentions": held,
        # A whole-archive export IS the archive, so a completed pull has nothing left
        # behind to be honest about — and an interrupted one has, so it says so.
        "complete": complete,
        "acts": held,
    })
    print(f"  → {held} acts held for {archive}" + ("" if complete else " — PARTIAL") + "\n")
    return complete


def cmd_oai(args):
    """A whole archive at 150 acts a request, for the archives with no bulk export.

    The Rijksarchief and Familiekunde Vlaanderen sets — the backbone of Belgian civil
    registration, and most of what this tree already rests on — publish neither an export
    nor an OAI set, so for those the per-act endpoint is still the only route and this
    will report that rather than appear to work.
    """
    archive = args.archive.lower()
    if (why := out_of_scope(archive)) and not args.anyway:
        print(f"refusing to harvest all of {archive}\n  {why}\n"
              "  Pass --anyway to override.", file=sys.stderr)
        return
    print(f"OAI-PMH — {archive}")
    params = {"verb": "ListRecords", "metadataPrefix": "oai_a2a", "set": archive}
    total_added = total_skipped = 0
    pages = 0

    def pages_of_acts():
        nonlocal pages
        nonlocal params
        while True:
            _throttle.wait()
            with _open(OAI + "?" + urllib.parse.urlencode(params), "text/xml") as res:
                body = res.read()
            pages += 1
            found = list(read_acts(io.BytesIO(body), archive))
            yield from found
            token = re.search(rb"<resumptionToken[^>]*>([^<]+)</resumptionToken>", body)
            if not token or not found:
                return
            params = {"verb": "ListRecords", "resumptionToken": token.group(1).decode()}

    total_added, total_skipped, error = write_acts(pages_of_acts(), archive, args.refresh)
    if not (total_added + total_skipped):
        print(f"  the OAI endpoint has no records for \"{archive}\" — it is not one of its sets.\n"
              f"  Fall back to the per-act route: uv run tools/harvest.py surname <name>", file=sys.stderr)
        return
    if error is not None:
        print(f"  the feed failed after {total_added} new acts — {type(error).__name__}: {error}\n"
              "  What arrived is held; re-running resumes by skipping it.", file=sys.stderr)
    save_manifest({
        "id": f"archive-{archive}",
        "query": {"archive": archive, "via": "oai"},
        "date": dt.date.today().isoformat(),
        "found": total_added + total_skipped,
        "mentions": total_added + total_skipped,
        # Only a feed read to exhaustion is the whole archive.
        "complete": error is None,
        "acts": total_added + total_skipped,
    })
    print(f"  → {total_added + total_skipped} acts held for {archive}, over {pages} request(s)"
          + ("" if error is None else " — PARTIAL") + "\n")


# ---------- commands ----------


def surname_harvest_id(surname: str, place: str | None = None) -> str:
    """One id per surname, minted in one place.

    It was minted in two: `surname` slugged the name and `frontiers` used the project's
    family key, so "De Keyser" was filed once as `de-keyser` and once as `dekeyser` —
    two rows, two full harvests of the same eleven thousand records, and every lookup
    finding whichever one it happened to ask for. The family key wins because it is
    already the project's answer to "are these the same family name".
    """
    return family_key(surname) + (f"-{slug(place)}" if place else "")


def cmd_surname(args):
    params = {"name": args.surname, "country_code": "be"}
    if args.place:
        params["eventplace"] = args.place
    harvest(
        surname_harvest_id(args.surname, args.place),
        f'Surname "{args.surname}"' + (f" at {args.place}" if args.place else "") + ", Belgium",
        params, args.max, args.refresh,
    )


def cmd_place(args):
    # The API has no year filter, so a commune harvest is a whole-commune harvest and
    # the years are applied when the corpus is read. Saying so rather than silently
    # pulling 262,000 Oostende records under a --from that does nothing.
    harvest(
        f"place-{slug(args.place)}",
        f'Commune "{args.place}", Belgium',
        {"name": "*", "eventplace": args.place, "country_code": "be"},
        args.max, args.refresh,
    )


def cmd_frontiers(args):
    """Harvest what the queue is actually asking for, rather than what someone thought
    of. A frontier's surname is exactly the axis the API filters on."""
    rows = [r for r in frontier_rows()][: args.limit]
    print(f"Harvesting for the top {len(rows)} frontiers.\n")
    for r in rows:
        if not r.surname:
            print(f"{r.name}\n  no surname recorded — nothing to query on.\n")
            continue
        harvest(surname_harvest_id(r.surname), f'{r.name} → surname "{r.surname}", Belgium',
                {"name": r.surname, "country_code": "be"}, args.max, args.refresh)


def cmd_status(args):
    manifest = load_manifest()
    if not manifest["harvests"]:
        return print("Nothing harvested yet. Start with: uv run tools/harvest.py frontiers")
    print(f"{len(manifest['harvests'])} harvests · {len(held_act_ids())} acts held\n")
    print(f"  {'harvest':<30} {'date':<11} {'mentions':>9} {'of':>8} {'acts':>6}")
    for h in manifest["harvests"]:
        print(f"  {h['id']:<30} {h['date']:<11} {h['mentions']:>9} {h['found']:>8} {h['acts']:>6}"
              + ("" if h["complete"] else "   PARTIAL"))

    partial = [h for h in manifest["harvests"] if not h["complete"]]
    if partial:
        short = sum((h["found"] or 0) - (h["mentions"] or 0) for h in partial)
        print(f"\n  {len(partial)} partial, {short} mentions short — raise --max and re-run with --refresh:")
        for h in partial[:12]:
            print(f"    {h['id']:<28} --max {h['found']} --refresh")
        if len(partial) > 12:
            print(f"    …and {len(partial) - 12} more")

    # Which of the archives already represented here can be had whole, in one request,
    # instead of one act at a time. This is the difference between a surname and a
    # province: the per-act route is about three acts a second, so Kortrijk's 140,543
    # acts are thirteen hours of fetching or a 19 MB download.
    if not args.offline:
        exports = bulk_archives()
        by_archive: dict[str, int] = {}
        for f in ACTS_DIR.glob("*.jsonl") if ACTS_DIR.is_dir() else []:
            by_archive[f.stem] = sum(1 for line in f.open(encoding="utf-8") if line.strip())
        whole = {h["query"]["archive"] for h in manifest["harvests"]
                 if (h.get("query") or {}).get("archive")}
        cheap = sorted((set(by_archive) & exports) - whole, key=lambda a: -by_archive[a])
        # Split, because recommending them together is how a Dutch archive gets pulled
        # whole by reflex. See out_of_scope().
        in_scope = [a for a in cheap if not out_of_scope(a)]
        elsewhere = [a for a in cheap if out_of_scope(a)]
        if in_scope:
            print(f"\n  {len(in_scope)} archive(s) you already hold acts from publish a WHOLE-ARCHIVE export.")
            print("  One request each, and it supersedes every future surname query there:\n")
            for a in in_scope[:12]:
                print(f"    {a:<6} {by_archive[a]:>6} acts held    uv run tools/harvest.py bulk {a}")
        if elsewhere:
            print(f"\n  {len(elsewhere)} more publish one, but are registered OUTSIDE Belgium — the acts")
            print("  held from them are Belgian only because the API queries were filtered that way.")
            print("  Pulling their exports would be mostly out-of-scope records:")
            where = archive_countries()
            print("    " + ", ".join(f"{a} ({where.get(a) or '?'})" for a in elsewhere))

    # Which surnames in the tree have never been harvested. This is objective 3's to-do
    # list, and it is derived rather than kept by hand.
    people = load_people(load_config()["roster"])
    held = {h["id"] for h in manifest["harvests"]}
    counts: dict[str, tuple[int, str]] = {}
    for p in people.values():
        if p.get("surname"):
            key = family_key(p["surname"])
            n, name = counts.get(key, (0, p["surname"]))
            counts[key] = (n + 1, name)
    missing = {k: v for k, v in counts.items() if k not in held}
    if missing:
        print(f"\n  {len(missing)} of {len(counts)} surnames in the tree never harvested — largest families first:")
        for key, (n, name) in sorted(missing.items(), key=lambda kv: -kv[1][0])[:12]:
            print(f"    {name:<28} {n} in the tree    uv run tools/harvest.py surname \"{name}\"")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    def common(p):
        p.add_argument("--max", type=int, default=4000, help="stop after this many mentions")
        p.add_argument("--refresh", action="store_true", help="re-fetch what is already held")
        return p

    p = common(sub.add_parser("surname", help="every Belgian record for one surname"))
    p.add_argument("surname")
    p.add_argument("--place", help="narrow to one commune")
    p.set_defaults(fn=cmd_surname)

    p = common(sub.add_parser("place", help="every Belgian record for one commune"))
    p.add_argument("place")
    p.set_defaults(fn=cmd_place)

    p = sub.add_parser("bulk", help="whole archives, ONE request each — always try this first")
    p.add_argument("archive", nargs="+", help="archive codes, e.g. gnt kor aal den")
    p.add_argument("--refresh", action="store_true", help="re-read what is already held")
    p.add_argument("--anyway", action="store_true",
                   help="pull an archive registered outside Belgium — see out_of_scope()")
    p.set_defaults(fn=cmd_bulk)

    p = sub.add_parser("oai", help="a whole archive at 150 acts a request, where there is no export")
    p.add_argument("archive", help="an archive code, e.g. den, ell, sla")
    p.add_argument("--refresh", action="store_true", help="re-read what is already held")
    p.add_argument("--anyway", action="store_true",
                   help="pull an archive registered outside Belgium — see out_of_scope()")
    p.set_defaults(fn=cmd_oai)

    p = common(sub.add_parser("frontiers", help="harvest the surnames the queue is asking for"))
    p.add_argument("--limit", type=int, default=5)
    p.set_defaults(fn=cmd_frontiers)

    p = sub.add_parser("status", help="what is held, and what is missing")
    p.add_argument("--offline", action="store_true", help="skip the check for whole-archive exports")
    p.set_defaults(fn=cmd_status)

    args = parser.parse_args()
    try:
        args.fn(args)
    except Blocked as e:
        # Deliberately loud and deliberately not recorded as an empty result.
        print(f"blocked {e}\n  Nothing was read, so nothing is exhausted. Try again later.", file=sys.stderr)
        return 2
    # The harvest is the only thing that changes the corpus, so it is the right place to
    # bring the index back into step. Doing it here rather than lazily in whatever report
    # runs next means the cost lands on the command that caused it, and no later command
    # quietly answers "no candidates" out of an index that predates the acts.
    if args.command != "status":
        store.ensure(verbose=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
