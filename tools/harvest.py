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
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

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
GAP = 0.3
PAGE = 100

_last_call = 0.0


class Blocked(RuntimeError):
    """Never reached the material. The same distinction the search log draws between
    `blocked` and `miss`: nothing was read, so nothing is exhausted."""


def api(endpoint: str, params: dict) -> dict:
    global _last_call
    url = f"{API}/{endpoint}.json?" + urllib.parse.urlencode(params)
    for attempt in range(1, 5):
        wait = GAP - (time.monotonic() - _last_call)
        if wait > 0:
            time.sleep(wait)
        _last_call = time.monotonic()
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
    handles: dict[str, object] = {}
    done = 0
    today = dt.date.today().isoformat()
    try:
        for key, m in wanted.items():
            try:
                record = api("records/show", {"archive": m["archive_code"], "identifier": m["identifier"]})
            except Blocked as e:
                print(f"\n  skipped {key}: {e}")
                continue
            archive = m["archive_code"]
            if archive not in handles:
                handles[archive] = (ACTS_DIR / f"{archive}.jsonl").open("a", encoding="utf-8")
            handles[archive].write(json.dumps({
                "id": key,
                "archive": archive,
                "archive_org": m.get("archive_org"),
                "fetched": today,
                "record": record,
            }, ensure_ascii=False) + "\n")
            # Flushed per act: the point of streaming is that an interrupted harvest
            # keeps what it already paid for, and a buffered line is a lost one.
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
        print(f"\n  {len(partial)} partial — raise --max and re-run with --refresh to complete:")
        for h in partial:
            print(f"    {h['id']:<28} --max {h['found']} --refresh")

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

    p = common(sub.add_parser("frontiers", help="harvest the surnames the queue is asking for"))
    p.add_argument("--limit", type=int, default=5)
    p.set_defaults(fn=cmd_frontiers)

    p = sub.add_parser("status", help="what is held, and what is missing")
    p.set_defaults(fn=cmd_status)

    args = parser.parse_args()
    try:
        args.fn(args)
    except Blocked as e:
        # Deliberately loud and deliberately not recorded as an empty result.
        print(f"blocked {e}\n  Nothing was read, so nothing is exhausted. Try again later.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
