#!/usr/bin/env python3
"""Checks the data files hang together. Run with: uv run tools/check_data.py"""

from __future__ import annotations

import re
import sys
from hashlib import sha256
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from familytree import sources as reg  # noqa: E402
from familytree.bundle import build_bundle  # noqa: E402
from familytree.frontmatter import FrontmatterError  # noqa: E402
from familytree.landing import stale_reason  # noqa: E402
from familytree.match import build_index, candidates_for, compare, from_person  # noqa: E402
from familytree.people import (  # noqa: E402
    ARTIFACT_FIELDS, ARTIFACTS_DIR, EVENT_FIELDS, FIELDS, ROOT, SPOUSE_FIELDS, SPOUSE_KINDS,
    given_names, is_approximate, is_valid_date, load_artifacts, load_config, load_person,
    point_year, sort_key,
)

# A marriage detail may no longer carry a date or say which marriage in a sequence it
# was. Both are fields or derived now, and a second handwritten copy is what these
# strings had become — "1st — mother of Segerius" was asserting a parent link that
# nothing checked against the child's own record.
DATE_IN_PROSE = re.compile(
    r"\b\d{4}\b|\b\d{1,2}(st|nd|rd|th)\b|\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d",
    re.I,
)

# The build runs this validator first, so it passes --skip-generated to avoid being
# told the files it is about to write are out of date.
SKIP_GENERATED = "--skip-generated" in sys.argv

errors: list[str] = []
warnings: list[str] = []


def fail(m):
    errors.append(m)


def main() -> int:
    config = load_config()
    ids, meta, root = config["roster"], config["meta"], config["root"]
    branches, lineages, groups = config["branches"], config["lineages"], config["groups"]
    group_keys = {g["key"] for g in groups}
    sites, pages = reg.load_sources()
    source_ids = {s["id"] for s in [*sites, *pages]}
    confidence = set(meta["confidence"])

    people: dict[str, dict] = {}
    for pid in ids:
        try:
            p = load_person(pid)
        except FrontmatterError as e:
            fail(str(e))
            continue
        people[pid] = p

        if p.get("id") != pid:
            fail(f"{pid}.md: \"id\" field says \"{p.get('id')}\"")
        if not p.get("name"):
            fail(f'{pid}.md: missing "name"')
        # The surname is stated because it cannot be computed, so the one thing worth
        # checking is that it is really part of the name — a typo here would split a
        # family in two without anything else noticing.
        if p.get("surname") and p["surname"] not in p.get("name", ""):
            fail(f"{pid}.md: surname \"{p['surname']}\" does not appear in name \"{p.get('name')}\"")
        if p.get("confidence") not in confidence:
            fail(f"{pid}.md: confidence \"{p.get('confidence')}\" is not one of {', '.join(sorted(confidence))}")
        if p.get("branch") and p["branch"] not in branches:
            fail(f"{pid}.md: branch \"{p['branch']}\" is not in data/branches.json")
        if p.get("line") and p["line"] not in group_keys:
            fail(f"{pid}.md: line \"{p['line']}\" is not a group key in site/labels.json")
        if "sex" in p and p["sex"] not in ("f", "m"):
            fail(f"{pid}.md: sex \"{p['sex']}\" must be \"f\" or \"m\"")

        # A date is either in the grammar or explicitly marked raw. There is no third
        # option, because a half-parsed date is one that later gets read as a fact.
        for ev in ("birth", "death"):
            e = p.get(ev)
            if not e:
                continue
            if not isinstance(e, dict):
                fail(f'{pid}.md: "{ev}" must be a block with date/place')
                continue
            for k in e:
                if k not in EVENT_FIELDS and k != "raw":
                    warnings.append(f'{pid}.md: {ev} has unknown field "{k}"')
            if e.get("date") and not is_valid_date(e["date"]):
                fail(f"{pid}.md: {ev}.date \"{e['date']}\" is not a valid date — "
                     "use 1876-11-12, 1876-11, 1876, ~1682, <1727, >1900 or 1575..1587")
            if not e.get("date") and not e.get("raw"):
                fail(f'{pid}.md: "{ev}" has neither a date nor a raw value')

        # A citation is a link into research/sources.json, so a typo is caught here
        # rather than becoming a claim backed by a source that does not exist.
        if "sources" in p:
            raw = p["sources"]
            listed = raw if isinstance(raw, list) else [raw]
            for sid in (x if isinstance(x, str) else x.get("id") for x in listed):
                if sid not in source_ids:
                    fail(f'{pid}.md: cites source "{sid}", which is not in research/sources.json')
        if "spouses" in p:
            if not isinstance(p["spouses"], list):
                fail(f'{pid}.md: "spouses" must be a list')
            else:
                for i, s in enumerate(p["spouses"]):
                    if not s.get("name"):
                        fail(f'{pid}.md: spouses[{i}] has no "name"')
                    for k in s:
                        if k not in SPOUSE_FIELDS:
                            warnings.append(f'{pid}.md: spouses[{i}] unknown field "{k}"')
                    # A marriage is an event, so its dates go through the same grammar
                    # as a birth. Nothing here may be prose that later has to be parsed.
                    for field in ("married", "divorced"):
                        if s.get(field) and not is_valid_date(s[field]):
                            fail(f'{pid}.md: spouses[{i}].{field} "{s[field]}" is not a valid date — '
                                 "use 1876-11-12, 1876-11, 1876, ~1682, <1727, >1900 or 1575..1587")
                    if s.get("kind") and s["kind"] not in SPOUSE_KINDS:
                        fail(f'{pid}.md: spouses[{i}].kind "{s["kind"]}" must be one of '
                             f"{', '.join(SPOUSE_KINDS)}")
                    if s.get("divorced") and not s.get("married"):
                        fail(f"{pid}.md: spouses[{i}] records a divorce but no marriage date")
                    if s.get("married") and s.get("divorced") and sort_key(s["divorced"]) < sort_key(s["married"]):
                        fail(f"{pid}.md: spouses[{i}] divorced ({s['divorced']}) before "
                             f"married ({s['married']})")
                    if s.get("detail") and DATE_IN_PROSE.search(s["detail"]):
                        fail(f'{pid}.md: spouses[{i}].detail "{s["detail"]}" carries a date or a '
                             'position in a sequence — use "married"/"divorced"/"place", or the '
                             "list order, which is what states the sequence")
                # Oldest first, so the order carries the sequence and nothing has to
                # write "his 2nd marriage" into a field that cannot be checked.
                dated = [(i, sort_key(s["married"])) for i, s in enumerate(p["spouses"]) if s.get("married")]
                for (i, a), (j, b) in zip(dated, dated[1:]):
                    if b < a:
                        fail(f"{pid}.md: spouses are out of order — [{j}] ({p['spouses'][j]['married']}) "
                             f"is earlier than [{i}] ({p['spouses'][i]['married']}); oldest first")
        for k in p:
            if k not in FIELDS and k != "note":
                warnings.append(f'{pid}.md: unknown field "{k}"')

    # Parent links point at people who exist, and nobody is their own ancestor.
    for pid, p in people.items():
        for rel in ("father", "mother"):
            if p.get(rel) and p[rel] not in people:
                fail(f"{pid}.md: {rel} \"{p[rel]}\" does not exist")

    # Spouse links point at people who exist, and marriage is mutual: if A records B, B
    # records A. Without that, building the tree downwards silently loses branches — a
    # child hangs off the parent who happened to be written up first.
    for pid, p in people.items():
        for s in p.get("spouses") or []:
            if not s.get("id"):
                continue
            if s["id"] not in people:
                fail(f"{pid}.md: spouse id \"{s['id']}\" does not exist")
                continue
            if s["id"] == pid:
                fail(f"{pid}.md: is listed as their own spouse")
            back = next((t for t in people[s["id"]].get("spouses") or [] if t.get("id") == pid), None)
            if back is None:
                fail(f"{pid}.md: lists spouse \"{s['id']}\", but {s['id']}.md does not list \"{pid}\" back")
                continue
            # One marriage, one set of facts. The link was already required to be
            # mutual; the facts were not, so the two records could — and did — give
            # different places and dates for the same act, with nothing to say which
            # was right. Whichever record is read first would have won.
            for field in ("kind", "married", "place", "divorced"):
                mine, theirs = s.get(field), back.get(field)
                if field == "kind":
                    mine, theirs = mine or "marriage", theirs or "marriage"
                if mine != theirs:
                    fail(f'{pid}.md and {s["id"]}.md disagree about their marriage: '
                         f'{field} is "{mine}" here and "{theirs}" there')

    # A shared child is proof of a couple, so both parents must record the marriage.
    # This is what keeps the upward tree and the downward tree describing one family.
    for pid, p in people.items():
        if not (p.get("father") and p.get("mother")):
            continue
        if p["father"] not in people or p["mother"] not in people:
            continue
        for a, b in ((p["father"], p["mother"]), (p["mother"], p["father"])):
            if not any(s.get("id") == b for s in people[a].get("spouses") or []):
                fail(f'{a}.md: has a child ({pid}) with "{b}" but does not list them as a spouse')

    # Which children came from which marriage is already in the data — every child names
    # its own father and mother — so writing "mother of Segerius" into the marriage is a
    # second copy of the tree that nothing keeps in step. The index and the tree derive
    # that grouping; a note asserting it can only ever go stale or contradict.
    kids_of_couple: dict[frozenset, list[str]] = {}
    for pid, p in people.items():
        if p.get("father") and p.get("mother"):
            kids_of_couple.setdefault(frozenset((p["father"], p["mother"])), []).append(pid)
    for pid, p in people.items():
        for i, s in enumerate(p.get("spouses") or []):
            if not (s.get("id") and s.get("detail")):
                continue
            words = {w.lower() for w in re.findall(r"\w{3,}", s["detail"])}
            for kid in kids_of_couple.get(frozenset((pid, s["id"])), []):
                named = [w for w in re.findall(r"\w{3,}", given_names(people[kid])) if w.lower() in words]
                if named:
                    fail(f'{pid}.md: spouses[{i}].detail names their own child ({kid}, "{named[0]}") — '
                         f"{kid}.md already records both parents, so this is a second copy of it; "
                         "put anything the fields cannot hold in the prose body instead")

    for start in people:
        seen: set[str] = set()

        def walk(pid, start=start, seen=seen):
            if not pid or pid in seen or pid not in people:
                return
            if pid == start and seen:
                fail(f"{start}.md: parent chain loops back to itself")
                return
            seen.add(pid)
            walk(people[pid].get("father"))
            walk(people[pid].get("mother"))

        walk(people[start].get("father"))
        walk(people[start].get("mother"))

    # Config files only reference people who exist.
    if root not in people:
        fail(f'meta.json: roots[0] "{root}" does not exist')

    def lineage_chain(lineage):
        if lineage.get("chain"):
            return lineage["chain"]
        out, seen, pid = [], set(), lineage.get("head")
        while pid and pid in people and pid not in seen:
            seen.add(pid)
            out.append(pid)
            pid = people[pid].get("father")
        return list(reversed(out))

    for lineage in lineages:
        if lineage.get("head") and lineage["head"] not in people:
            fail(f"lineages.json ({lineage['key']}): head \"{lineage['head']}\" does not exist")
        for pid in lineage_chain(lineage):
            if pid not in people:
                fail(f"lineages.json ({lineage['key']}): \"{pid}\" does not exist")
    for g in groups:
        if not g.get("key") or not g.get("title"):
            fail("site/labels.json: every group needs a key and a title")

    roots = [r for r in meta["roots"] if r in people]
    for r in meta["roots"]:
        if r not in people:
            fail(f'meta.json: roots entry "{r}" does not exist')
    for b, sid in branches.items():
        if sid not in source_ids:
            fail(f'branches.json: "{b}" cites source "{sid}", which is not registered')

    # Not fatal, but usually a mistake: a record connected to nothing. Marriage counts
    # as a connection, which is how a spouse with no children still belongs.
    children_of: dict[str, list[str]] = {}
    for pid, p in people.items():
        for rel in ("father", "mother"):
            if p.get(rel) in people:
                children_of.setdefault(p[rel], []).append(pid)

    def neighbours(pid):
        p = people[pid]
        out = [p.get("father"), p.get("mother")]
        out += [s["id"] for s in p.get("spouses") or [] if s.get("id")]
        out += children_of.get(pid, [])
        return [x for x in out if x and x in people]

    reachable, queue = set(roots), list(roots)
    while queue:
        for n in neighbours(queue.pop()):
            if n not in reachable:
                reachable.add(n)
                queue.append(n)
    for pid in ids:
        if pid in reachable or pid not in people:
            continue
        warnings.append(
            f"{pid}.md: connected to nobody — no parents, children or spouse"
            if not neighbours(pid)
            else f"{pid}.md: not connected to any root in meta.json (add a root, or link them in)"
        )

    _check_duplicates(people, children_of)
    _check_plausibility(people, children_of)
    _check_search_log(people, sites, pages)
    _check_artifacts(people, source_ids)

    # The page loads dist/bundle.js, not the individual files, so a stale bundle is a
    # site silently showing old data. Catching it here means it cannot be committed:
    # the rule is that this validator is green before every commit.
    if not SKIP_GENERATED:
        bundle_path = ROOT / "dist" / "bundle.js"
        if not bundle_path.exists():
            fail("dist/bundle.js is missing — run: uv run tools/build.py")
        elif bundle_path.read_text(encoding="utf-8") != build_bundle():
            fail("dist/bundle.js is out of date with data/people/ — run: uv run tools/build.py")

        # index.html states the size of the tree in prose, because it loads no
        # JavaScript and cannot count. That is the one number on the site that can go
        # wrong in silence — the tree grows and the paragraph does not — so it is
        # checked here too.
        landing = ROOT / "index.html"
        if landing.exists():
            stale = stale_reason(landing.read_text(encoding="utf-8"), people, config)
            if stale:
                fail(stale)

    for w in warnings:
        print("warn  " + w, file=sys.stderr)
    for e in errors:
        print("error " + e, file=sys.stderr)
    print(f"\n{len(errors)} error(s) in {len(ids)} people." if errors else
          f"OK — {len(ids)} people, {len(branches)} branches, {len(lineages)} lineages, {len(groups)} index groups.")
    return 1 if errors else 0


def _check_plausibility(people, children_of):
    """Arithmetic on the links, which is how a wrong graft announces itself.

    A false parent link almost never looks wrong in the record — the names agree, that
    is why it was made. It looks wrong in the dates: a mother of nine, a father dead six
    years before the birth, a man married at eleven. Historical demography has leaned on
    exactly these bounds since Louis Henry, because they are the cheapest possible test
    and they catch the error the name comparison could not.

    Bounds are deliberately loose. The aim is to catch the graft that is off by a
    generation — the recurring failure in this material, where a forename returns every
    second generation — and never to adjudicate an unusual but real life. Everything
    here is a warning: a record can be right and strange, and the validator does not get
    to overrule a document.
    """
    def dated(p, event):
        """Only dates that assert a year, and how much slack they carry. A `<1673` bounds
        a birth without stating one, and doing arithmetic on the bound is how this check
        first reported a mother aged -6 for a record that was perfectly consistent."""
        raw = (p.get(event) or {}).get("date")
        return point_year(raw), (3 if is_approximate(raw) else 0)

    for pid, p in sorted(people.items()):
        (born, born_slack), (died, died_slack) = dated(p, "birth"), dated(p, "death")
        slack = born_slack + died_slack
        if born and died and died < born - slack:
            warnings.append(f"{pid}.md: dies {died} but is born {born}")
        if born and died and died - born > 110 + slack:
            warnings.append(f"{pid}.md: lifespan {died - born} years — check the pair is one person")

        for cid in children_of.get(pid, []):
            child_born, child_slack = dated(people[cid], "birth")
            if not (born and child_born):
                continue
            age = child_born - born
            give = born_slack + child_slack
            is_mother = people[cid].get("mother") == pid
            # A father can father a child until he dies; a mother cannot. Split, because
            # a single bound wide enough for both catches neither.
            upper = 50 if is_mother else 75
            if age < 13 - give or age > upper + give:
                role = "mother" if is_mother else "father"
                warnings.append(
                    f"{pid}.md: is {role} of {cid} at age {age} — a generation may be missing")
            # A father's child may be born after he dies; a mother's may not.
            if died and child_born > died + died_slack + child_slack + (0 if is_mother else 1):
                warnings.append(
                    f"{pid}.md: {cid} is born {child_born}, after this parent dies {died}")


def _check_duplicates(people, children_of):
    """Two records for one person.

    At 302 people you can see it; at ten thousand, with Bostyn/Bostin and De Keyser/
    Dekeyser already in the tree, you cannot — and a person entered twice does not look
    broken, it looks like two people, which quietly splits a branch in half. So the
    blocking index that finds candidates in the corpus is also run against the tree
    itself, every build.

    Only pairs that agree on a DATE are reported. A father and son sharing a name and a
    commune agree on two classes without being the same person, and a check that cries
    wolf gets switched off.
    """
    related: set[frozenset] = set()
    for pid, p in people.items():
        for rel in ("father", "mother"):
            if p.get(rel) in people:
                related.add(frozenset((pid, p[rel])))
        for s in p.get("spouses") or []:
            if s.get("id") in people:
                related.add(frozenset((pid, s["id"])))
    for _, kids in children_of.items():
        for i, a in enumerate(kids):
            for b in kids[i + 1:]:
                related.add(frozenset((a, b)))  # siblings

    candidates = [from_person(p, people, children_of) for p in people.values()]
    index = build_index(candidates)
    seen: set[frozenset] = set()
    for c in candidates:
        for other in candidates_for(c, index):
            pair = frozenset((c.ref, other.ref))
            if pair in seen or pair in related:
                continue
            seen.add(pair)
            m = compare(c, other)
            if m.band == "strong" and "date" in m.classes:
                warnings.append(
                    f"{c.ref}.md and {other.ref}.md may be the same person — {m.explain()}. "
                    f"Check with: uv run tools/identify.py --person {c.ref}"
                )


def _check_search_log(people, sites, pages):
    try:
        log = reg.load_log()
    except ValueError as e:
        fail(str(e))
        return
    for problem in reg.registry_problems(sites, pages, log, people, load_artifacts()):
        fail(problem)


def _check_artifacts(people, source_ids):
    """Artifacts are the evidence itself. A record pointing at a file that is missing is
    a citation to nothing; a file whose bytes no longer match the recorded digest is
    worse, because the claim still looks sourced while the proof has changed under it."""
    artifacts = load_artifacts()
    for aid, a in artifacts.items():
        if a.get("id") != aid:
            fail(f"artifacts/{aid}.md: \"id\" says \"{a.get('id')}\"")
        if not a.get("title"):
            fail(f'artifacts/{aid}.md: missing "title"')
        for k in a:
            if k not in ARTIFACT_FIELDS and k != "note":
                warnings.append(f'artifacts/{aid}.md: unknown field "{k}"')
        if a.get("date") and not is_valid_date(a["date"]):
            fail(f"artifacts/{aid}.md: date \"{a['date']}\" is not a valid date")
        if a.get("source") and a["source"] not in source_ids:
            fail(f"artifacts/{aid}.md: source \"{a['source']}\" is not registered")
        for pid in a.get("evidences") or []:
            if pid not in people:
                fail(f"artifacts/{aid}.md: evidences \"{pid}\", who does not exist")

        if not a.get("file"):
            fail(f'artifacts/{aid}.md: missing "file"')
            continue
        f = ARTIFACTS_DIR / a["file"]
        if not f.exists():
            fail(f"artifacts/{aid}.md: file \"{a['file']}\" is missing")
            continue
        data = f.read_bytes()
        if a.get("bytes") and int(a["bytes"]) != len(data):
            fail(f"artifacts/{aid}.md: file is {len(data)} bytes, the record says {a['bytes']}")
        if a.get("sha256") and sha256(data).hexdigest() != a["sha256"]:
            fail(f"artifacts/{aid}.md: sha256 does not match the file — the evidence has changed")
    if ARTIFACTS_DIR.is_dir():
        for f in sorted(ARTIFACTS_DIR.iterdir()):
            if f.suffix != ".md" and not any(a.get("file") == f.name for a in artifacts.values()):
                warnings.append(f"artifacts/{f.name}: no record describes this file")


if __name__ == "__main__":
    raise SystemExit(main())
