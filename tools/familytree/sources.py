"""The source registry and the search log.

Two levels throughout, because they answer different questions. A SITE is a base
venue — Geneanet, AGATHA, FamilySearch, Open Archives. A PAGE is something specific
inside it: a member tree, a collection, a single act. "Have we tried Geneanet for this
person?" and "which pages have ever yielded anything?" are different questions, and a
flat list answers neither well.

Every search records whether it succeeded, what it found, and — when it found nothing
— why. The why is the part a strategist needs: "not indexed here" and "wrong region"
and "hit the paywall" point at completely different next moves.
"""

from __future__ import annotations

import json

from .people import ROOT

SOURCES = ROOT / "research" / "sources.json"
LOG = ROOT / "research" / "searches.jsonl"

# Success and failure, and the two states in between that a strategist must not
# confuse. `ambiguous` is a real find that is not proof — do not graft it, but do not
# search for it again either. `blocked` never reached the material at all, so it is
# the one result that means "try this again".
RESULTS = {
    "hit": "found what was wanted",
    "miss": "searched properly, nothing there",
    "ambiguous": "found something, not enough to prove it",
    "blocked": "never reached the material — login, paywall, cap",
}

# HOW the material was consulted, which is a different question from whether it was
# found. It is the field that stops a miss from being permanent. "AGATHA is exhausted
# for Édouard's parentage" was true of AGATHA's NAME INDEX — his 1901 act is not
# indexed there — and says nothing about reading the register page by page, or about
# a full-text search of the images that did not exist when the search was run. A miss
# without a basis cannot be re-opened when a venue gains a capability, so it silently
# becomes a permanent wall.
BASIS = {
    "name-index": "queried a name index — only finds what somebody indexed",
    "full-text": "searched the text of the images themselves",
    "image-read": "actually read the act images, page by page",
    "tree": "read someone else's compiled tree",
    "api": "structured query against an open-data API",
    "testimony": "a person told us",
}

# What a miss actually covered. Required, because "miss" without an extent tells the
# next pass nothing: "191 hits, none born 1876" and "the whole 1901 marriage index for
# one commune" and "province-wide, both spellings" are three different claims, and
# only the third closes anything.
SCOPE_REQUIRED_FOR = {"miss", "ambiguous"}

ACCESS_COST = {"open": 1, "mixed": 2, "login": 3, "paywall": 5, "offline": 8}

MARK = {"hit": "✓", "miss": "✗", "ambiguous": "~", "blocked": "⊘"}


def succeeded(result: str) -> bool:
    return result == "hit"


def load_sources() -> tuple[list[dict], list[dict]]:
    raw = json.loads(SOURCES.read_text(encoding="utf-8"))
    return raw.get("sites", []), raw.get("pages", [])


def load_log() -> list[dict]:
    if not LOG.exists():
        return []
    out = []
    for i, line in enumerate(LOG.read_text(encoding="utf-8").split("\n"), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError as e:
            raise ValueError(f"research/searches.jsonl line {i} is not valid JSON: {e}") from e
    return out


def append_log(entry: dict) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def site_by_id(sites: list[dict], site_id: str) -> dict | None:
    return next((s for s in sites if s["id"] == site_id), None)


def page_by_id(pages: list[dict], page_id: str) -> dict | None:
    return next((p for p in pages if p["id"] == page_id), None)


def entry_problems(entry: dict, at: str, sites: list[dict], pages: list[dict], people: dict) -> list[str]:
    """Everything wrong with one log line. Shared by `log` and `check` so the rule
    that refuses a bad entry at write time is the same rule that catches an old one."""
    problems = []
    for field in ("date", "person", "goal", "site", "result", "basis"):
        if not entry.get(field):
            problems.append(f'{at}: missing "{field}"')
    result = entry.get("result")
    if result and result not in RESULTS:
        problems.append(f"{at}: result \"{result}\" is not one of {', '.join(RESULTS)}")
    if entry.get("basis") and entry["basis"] not in BASIS:
        problems.append(f"{at}: basis \"{entry['basis']}\" is not one of {', '.join(BASIS)}")
    if entry.get("site") and not site_by_id(sites, entry["site"]):
        problems.append(f"{at}: unknown site \"{entry['site']}\"")
    if entry.get("page"):
        page = page_by_id(pages, entry["page"])
        if not page:
            problems.append(f"{at}: unknown page \"{entry['page']}\"")
        elif page["site"] != entry.get("site"):
            problems.append(f"{at}: page \"{entry['page']}\" belongs to site \"{page['site']}\", not \"{entry.get('site')}\"")
    if entry.get("person") and entry["person"] not in people:
        problems.append(f"{at}: unknown person \"{entry['person']}\"")
    # The outcome has to be legible, or the entry tells the next pass nothing.
    if result and succeeded(result) and not entry.get("found"):
        problems.append(f'{at}: a hit with no "found" — say what it gave')
    if result and not succeeded(result) and not entry.get("why"):
        problems.append(f'{at}: a {result} with no "why" — say whether it is worth retrying')
    if result in SCOPE_REQUIRED_FOR and not entry.get("scope"):
        problems.append(f'{at}: a {result} with no "scope" — say what was actually covered, or it reads as "everywhere"')
    return problems


def registry_problems(sites, pages, log, people, artifacts) -> list[str]:
    """Everything wrong with the registry and the log together.

    Shared by the validator and `research.py check`, so the rule that refuses a bad
    entry at write time is exactly the rule that catches an old one.
    """
    problems: list[str] = []
    site_ids: set[str] = set()
    for s in sites:
        if not s.get("id"):
            problems.append("a site has no id")
        elif s["id"] in site_ids:
            problems.append(f"duplicate site id \"{s['id']}\"")
        site_ids.add(s.get("id"))
        if not s.get("title"):
            problems.append(f"site \"{s.get('id')}\" has no title")
        for cap in s.get("capabilities") or []:
            if cap not in BASIS:
                problems.append(f"site \"{s['id']}\": capability \"{cap}\" is not one of {', '.join(BASIS)}")

    page_ids: set[str] = set()
    for p in pages:
        if not p.get("id"):
            problems.append("a page has no id")
        elif p["id"] in page_ids or p["id"] in site_ids:
            problems.append(f"duplicate id \"{p['id']}\"")
        page_ids.add(p.get("id"))
        if not p.get("title"):
            problems.append(f"page \"{p.get('id')}\" has no title")
        if not p.get("site"):
            problems.append(f"page \"{p.get('id')}\" names no site")
        elif p["site"] not in site_ids:
            problems.append(f"page \"{p['id']}\" belongs to site \"{p['site']}\", which is not registered")
        if p.get("artifact") and p["artifact"] not in artifacts:
            problems.append(f"page \"{p['id']}\" cites artifact \"{p['artifact']}\", which has no record in data/artifacts/")

    for i, e in enumerate(log, start=1):
        at = f"searches.jsonl line {i}"
        problems += entry_problems(e, at, sites, pages, people)
        if e.get("artifact") and e["artifact"] not in artifacts:
            problems.append(f"{at}: cites artifact \"{e['artifact']}\", which has no record in data/artifacts/")
    return problems


def stale_misses(log: list[dict], sites: list[dict]) -> list[dict]:
    """Misses a venue may have outgrown.

    A source is not a fixed thing. FamilySearch is adding handwriting recognition for
    Dutch and French and expanding its Belgian collections; a commune's registers get
    indexed by volunteers years after somebody looked and found nothing. Every one of
    those makes a `name-index` miss re-checkable, and nothing else in this repository
    would ever notice.
    """
    out = []
    for e in log:
        if succeeded(e.get("result", "")):
            continue
        site = site_by_id(sites, e.get("site", ""))
        if not site:
            continue
        caps = site.get("capabilities") or []
        reasons = []
        stronger = [c for c in caps if c != e.get("basis")]
        changed = site.get("capabilitiesChanged")
        if changed and e.get("date", "") < changed:
            reasons.append(f"the venue gained a capability on {changed}, after this search")
        if e.get("basis") == "name-index" and "full-text" in caps:
            reasons.append("full-text search now reads the images this name index never covered")
        if e.get("result") == "blocked":
            reasons.append("nothing was ever read — blocked is not a finding")
        if reasons:
            out.append({**e, "reasons": reasons, "nowOffers": stronger})
    return out
