#!/usr/bin/env python3
"""Checks the data files hang together. Run with: uv run tools/check_data.py"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from dataclasses import dataclass, field
from hashlib import sha256

from familytree import sources as reg
from familytree import store
from familytree.bundle import build_bundle
from familytree.corpus import NOT_A_FORENAME, normalise_key
from familytree.docsite import stale_reason as docs_stale_reason
from familytree.edges import planned, rewrite
from familytree.frontmatter import FrontmatterError
from familytree.landing import stale_reason
from familytree.match import build_index, candidates_for, compare, from_person
from familytree.people import (
    ARTIFACT_FIELDS, ARTIFACTS_DIR, EDGE_CONFIDENCE, EVENT_FIELDS, FIELDS, LINK_FIELDS,
    MAX_FATHER_AGE, MAX_LIFESPAN, MAX_MOTHER_AGE, MIN_PARENT_AGE, NOT_EVIDENCE, ROOT,
    SIBLING_FIELDS, SPOUSE_FIELDS, SPOUSE_KINDS, WEAK_EDGE_BLAST_RADIUS, children_index,
    given_names,
    is_approximate, is_valid_date, link_of, load_artifacts, load_config, load_forenames,
    load_person, parent_id, point_year, sort_key, weak_edges,
)

# A marriage detail may no longer carry a date or say which marriage in a sequence it
# was. Both are fields or derived now, and a second handwritten copy is what these
# strings had become — "1st — mother of Segerius" was asserting a parent link that
# nothing checked against the child's own record.
DATE_IN_PROSE = re.compile(
    r"\b\d{4}\b|\b\d{1,2}(st|nd|rd|th)\b|\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d",
    re.I,
)


@dataclass
class Report:
    """What the checks found, threaded through them rather than accumulated in a global.

    It was two module-level lists and a bare `fail()`. That reads fine in a script, and it
    quietly made the checks untestable: with nowhere to put a second run's findings, a test
    could assert that a check passes but never that it FAILS. So the test written to pin the
    cross-partition forename check reimplemented the check in its own body and asserted on
    that — it would have passed with `_check_forenames` deleted. A check handed a fresh
    Report can be asked what it says about a deliberately bad file.
    """

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def fail(self, m: str) -> None:
        self.errors.append(m)

    def warn(self, m: str) -> None:
        self.warnings.append(m)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    # The build runs this validator first, so it passes --skip-generated to avoid being
    # told the files it is about to write are out of date.
    parser.add_argument("--skip-generated", action="store_true",
                        help="do not check that dist/ and index.html are up to date")
    args = parser.parse_args(argv)
    report = Report()
    config = load_config()
    ids, meta, root = config["roster"], config["meta"], config["root"]
    lineages, groups = config["lineages"], config["groups"]
    group_keys = {g["key"] for g in groups}
    sites, pages = reg.load_sources()
    source_ids = {s["id"] for s in [*sites, *pages]}
    confidence = set(meta["confidence"])

    people: dict[str, dict] = {}
    for pid in ids:
        try:
            p = load_person(pid)
        except FrontmatterError as e:
            report.fail(str(e))
            continue
        people[pid] = p

        if p.get("id") != pid:
            report.fail(f"{pid}.md: \"id\" field says \"{p.get('id')}\"")
        if not p.get("name"):
            report.fail(f'{pid}.md: missing "name"')
        # The surname is stated because it cannot be computed, so the one thing worth
        # checking is that it is really part of the name — a typo here would split a
        # family in two without anything else noticing.
        if p.get("surname") and p["surname"] not in p.get("name", ""):
            report.fail(f"{pid}.md: surname \"{p['surname']}\" does not appear in name \"{p.get('name')}\"")
        if p.get("confidence") not in confidence:
            report.fail(f"{pid}.md: confidence \"{p.get('confidence')}\" is not one of {', '.join(sorted(confidence))}")
        if p.get("line") and p["line"] not in group_keys:
            report.fail(f"{pid}.md: line \"{p['line']}\" is not a group key in site/labels.json")
        if "sex" in p and p["sex"] not in ("f", "m"):
            report.fail(f"{pid}.md: sex \"{p['sex']}\" must be \"f\" or \"m\"")

        # A date is either in the grammar or explicitly marked raw. There is no third
        # option, because a half-parsed date is one that later gets read as a fact.
        for ev in ("birth", "death"):
            e = p.get(ev)
            if not e:
                continue
            if not isinstance(e, dict):
                report.fail(f'{pid}.md: "{ev}" must be a block with date/place')
                continue
            for k in e:
                if k not in EVENT_FIELDS and k != "raw":
                    report.warn(f'{pid}.md: {ev} has unknown field "{k}"')
            if e.get("date") and not is_valid_date(e["date"]):
                report.fail(f"{pid}.md: {ev}.date \"{e['date']}\" is not a valid date — "
                     "use 1876-11-12, 1876-11, 1876, ~1682, <1727, >1900 or 1575..1587")
            if not e.get("date") and not e.get("raw"):
                report.fail(f'{pid}.md: "{ev}" has neither a date nor a raw value')

        # A citation is a link into research/sources.json, so a typo is caught here
        # rather than becoming a claim backed by a source that does not exist.
        if "sources" in p:
            raw = p["sources"]
            listed = raw if isinstance(raw, list) else [raw]
            for sid in (x if isinstance(x, str) else x.get("id") for x in listed):
                if sid not in source_ids:
                    report.fail(f'{pid}.md: cites source "{sid}", which is not in research/sources.json')
        if "spouses" in p:
            if not isinstance(p["spouses"], list):
                report.fail(f'{pid}.md: "spouses" must be a list')
            else:
                for i, s in enumerate(p["spouses"]):
                    if not s.get("name"):
                        report.fail(f'{pid}.md: spouses[{i}] has no "name"')
                    for k in s:
                        if k not in SPOUSE_FIELDS:
                            report.warn(f'{pid}.md: spouses[{i}] unknown field "{k}"')
                    # A marriage is an event, so its dates go through the same grammar
                    # as a birth. Nothing here may be prose that later has to be parsed.
                    for field in ("married", "divorced"):
                        if s.get(field) and not is_valid_date(s[field]):
                            report.fail(f'{pid}.md: spouses[{i}].{field} "{s[field]}" is not a valid date — '
                                 "use 1876-11-12, 1876-11, 1876, ~1682, <1727, >1900 or 1575..1587")
                    if s.get("kind") and s["kind"] not in SPOUSE_KINDS:
                        report.fail(f'{pid}.md: spouses[{i}].kind "{s["kind"]}" must be one of '
                             f"{', '.join(SPOUSE_KINDS)}")
                    if s.get("divorced") and not s.get("married"):
                        report.fail(f"{pid}.md: spouses[{i}] records a divorce but no marriage date")
                    if s.get("married") and s.get("divorced") and sort_key(s["divorced"]) < sort_key(s["married"]):
                        report.fail(f"{pid}.md: spouses[{i}] divorced ({s['divorced']}) before "
                             f"married ({s['married']})")
                    if s.get("detail") and DATE_IN_PROSE.search(s["detail"]):
                        report.fail(f'{pid}.md: spouses[{i}].detail "{s["detail"]}" carries a date or a '
                             'position in a sequence — use "married"/"divorced"/"place", or the '
                             "list order, which is what states the sequence")
                # Oldest first, so the order carries the sequence and nothing has to
                # write "his 2nd marriage" into a field that cannot be checked.
                dated = [(i, sort_key(s["married"])) for i, s in enumerate(p["spouses"]) if s.get("married")]
                for (i, a), (j, b) in zip(dated, dated[1:]):
                    if b < a:
                        report.fail(f"{pid}.md: spouses are out of order — [{j}] ({p['spouses'][j]['married']}) "
                             f"is earlier than [{i}] ({p['spouses'][i]['married']}); oldest first")
        for k in p:
            if k not in FIELDS and k != "note":
                report.warn(f'{pid}.md: unknown field "{k}"')

    # Parent links point at people who exist, and nobody is their own ancestor.
    for pid, p in people.items():
        for rel in ("father", "mother"):
            target = parent_id(p, rel)
            if target and target not in people:
                report.fail(f'{pid}.md: {rel} "{target}" does not exist')

    # Spouse links point at people who exist, and marriage is mutual: if A records B, B
    # records A. Without that, building the tree downwards silently loses branches — a
    # child hangs off the parent who happened to be written up first.
    for pid, p in people.items():
        for s in p.get("spouses") or []:
            if not s.get("id"):
                continue
            if s["id"] not in people:
                report.fail(f"{pid}.md: spouse id \"{s['id']}\" does not exist")
                continue
            if s["id"] == pid:
                report.fail(f"{pid}.md: is listed as their own spouse")
            back = next((t for t in people[s["id"]].get("spouses") or [] if t.get("id") == pid), None)
            if back is None:
                report.fail(f"{pid}.md: lists spouse \"{s['id']}\", but {s['id']}.md does not list \"{pid}\" back")
                continue
            # One marriage, one set of facts. The link was already required to be
            # mutual; the facts were not, so the two records could — and did — give
            # different places and dates for the same act, with nothing to say which
            # was right. Whichever record is read first would have won.
            # `confidence` and `source` join the list because a marriage is a link and
            # the two records describe ONE link. Without them, the same act could be `doc`
            # on his record and `asm` on hers, and whichever the reader opened first would
            # decide whether the page drew it red.
            for field in ("kind", "confidence", "source", "married", "place", "divorced"):
                mine, theirs = s.get(field), back.get(field)
                if field == "kind":
                    mine, theirs = mine or "marriage", theirs or "marriage"
                if mine != theirs:
                    report.fail(f'{pid}.md and {s["id"]}.md disagree about their marriage: '
                         f'{field} is "{mine}" here and "{theirs}" there')

    # A shared child is proof of a couple, so both parents must record the marriage.
    # This is what keeps the upward tree and the downward tree describing one family.
    for pid, p in people.items():
        father, mother = parent_id(p, "father"), parent_id(p, "mother")
        if father not in people or mother not in people:
            continue
        for a, b in ((father, mother), (mother, father)):
            if not any(s.get("id") == b for s in people[a].get("spouses") or []):
                report.fail(f'{a}.md: has a child ({pid}) with "{b}" but does not list them as a spouse')

    # Which children came from which marriage is already in the data — every child names
    # its own father and mother — so writing "mother of Segerius" into the marriage is a
    # second copy of the tree that nothing keeps in step. The index and the tree derive
    # that grouping; a note asserting it can only ever go stale or contradict.
    kids_of_couple: dict[frozenset, list[str]] = {}
    for pid, p in people.items():
        father, mother = parent_id(p, "father"), parent_id(p, "mother")
        if father and mother:
            kids_of_couple.setdefault(frozenset((father, mother)), []).append(pid)
    for pid, p in people.items():
        for i, s in enumerate(p.get("spouses") or []):
            if not (s.get("id") and s.get("detail")):
                continue
            words = {w.lower() for w in re.findall(r"\w{3,}", s["detail"])}
            for kid in kids_of_couple.get(frozenset((pid, s["id"])), []):
                named = [w for w in re.findall(r"\w{3,}", given_names(people[kid])) if w.lower() in words]
                if named:
                    report.fail(f'{pid}.md: spouses[{i}].detail names their own child ({kid}, "{named[0]}") — '
                         f"{kid}.md already records both parents, so this is a second copy of it; "
                         "put anything the fields cannot hold in the prose body instead")

    for start in people:
        seen: set[str] = set()

        def walk(pid, start=start, seen=seen):
            if not pid or pid in seen or pid not in people:
                return
            if pid == start and seen:
                report.fail(f"{start}.md: parent chain loops back to itself")
                return
            seen.add(pid)
            walk(parent_id(people[pid], "father"))
            walk(parent_id(people[pid], "mother"))

        walk(parent_id(people[start], "father"))
        walk(parent_id(people[start], "mother"))

    # Config files only reference people who exist.
    if root not in people:
        report.fail(f'meta.json: roots[0] "{root}" does not exist')

    def lineage_chain(lineage):
        """Walked up from `head`, never written down. A `chain:` field used to be allowed
        as an override and no lineage ever used one — a hand-kept copy of something the
        father-links already say, which is the duplication the data model forbids."""
        out, seen, pid = [], set(), lineage.get("head")
        while pid and pid in people and pid not in seen:
            seen.add(pid)
            out.append(pid)
            pid = parent_id(people[pid], "father")
        return list(reversed(out))

    for lineage in lineages:
        if lineage.get("head") and lineage["head"] not in people:
            report.fail(f"lineages.json ({lineage['key']}): head \"{lineage['head']}\" does not exist")
        for pid in lineage_chain(lineage):
            if pid not in people:
                report.fail(f"lineages.json ({lineage['key']}): \"{pid}\" does not exist")
    for g in groups:
        if not g.get("key") or not g.get("title"):
            report.fail("site/labels.json: every group needs a key and a title")
    _check_wording(report, config["site"])

    roots = [r for r in meta["roots"] if r in people]
    for r in meta["roots"]:
        if r not in people:
            report.fail(f'meta.json: roots entry "{r}" does not exist')

    # `named` is whose tree the page says it is, and it is deliberately not `roots`:
    # objective 3 gives every disconnected Bundervoet family a root, and the title is
    # not theirs. Empty is a failure rather than a fallback — the page would silently
    # go back to naming itself after all the roots.
    named = meta.get("named") or []
    if not named:
        report.fail("meta.json: named is empty — nobody for the page to say the tree is of")
    for r in named:
        if r not in people:
            report.fail(f'meta.json: named entry "{r}" does not exist')
    if meta["defaultSource"] not in source_ids:
        report.fail(f'meta.json: defaultSource "{meta["defaultSource"]}" is not registered')

    # Not fatal, but usually a mistake: a record connected to nothing. Marriage counts
    # as a connection, which is how a spouse with no children still belongs.
    children_of = children_index(people)

    def neighbours(pid):
        p = people[pid]
        out = [parent_id(p, "father"), parent_id(p, "mother")]
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
        report.warn(
            f"{pid}.md: connected to nobody — no parents, children or spouse"
            if not neighbours(pid)
            else f"{pid}.md: not connected to any root in meta.json (add a root, or link them in)"
        )

    _check_duplicates(report, people, children_of)
    _check_plausibility(report, people, children_of)
    _check_links(report, people, meta, source_ids)
    _check_edges_written(report, people)
    _check_search_log(report, sites, pages, people)
    _check_forenames(report)
    _check_labels(report, people)
    _check_artifacts(report, people, source_ids)

    # The page loads dist/bundle.js, not the individual files, so a stale bundle is a
    # site silently showing old data. Catching it here means it cannot be committed:
    # the rule is that this validator is green before every commit.
    if not args.skip_generated:
        bundle_path = ROOT / "dist" / "bundle.js"
        if not bundle_path.exists():
            report.fail("dist/bundle.js is missing — run: uv run tools/build.py")
        elif bundle_path.read_text(encoding="utf-8") != build_bundle():
            report.fail("dist/bundle.js is out of date with data/people/ — run: uv run tools/build.py")

        # index.html states the size of the tree in prose, because it loads no
        # JavaScript and cannot count. That is the one number on the site that can go
        # wrong in silence — the tree grows and the paragraph does not — so it is
        # checked here too.
        landing = ROOT / "index.html"
        if landing.exists():
            stale = stale_reason(landing.read_text(encoding="utf-8"), people, config)
            if stale:
                report.fail(stale)

        # The rendered docs are committed like the bundle and, until now, were the one
        # generated artefact nothing checked — because this validator cannot import
        # MkDocs to regenerate them. It compares a signature over the inputs instead;
        # see familytree/docsite.py for what that does and does not catch.
        docs_stale = docs_stale_reason()
        if docs_stale:
            report.fail(docs_stale)

    for w in report.warnings:
        print("warn  " + w, file=sys.stderr)
    for e in report.errors:
        print("error " + e, file=sys.stderr)
    print(f"\n{len(report.errors)} error(s) in {len(ids)} people." if report.errors else
          f"OK — {len(ids)} people, {len(lineages)} lineages, {len(groups)} index groups.")
    return 1 if report.errors else 0


def _check_wording(report, site):
    """Every word the page shows, in every language it offers.

    A missing translation does not break anything — the i18n layer falls back to the
    first language — which is exactly why it has to be caught here. Falling back is
    invisible: the page stays readable, and the untranslated string sits in the
    middle of it until somebody happens to be reading in that language and notices.
    A build is the only place that can see the whole table at once.
    """
    langs = [lang["code"] for lang in site.get("languages", [])]
    if not langs:
        report.fail("site/labels.json: no languages declared")
        return

    def every_language(entry, where):
        if not isinstance(entry, dict):
            report.fail(f"site/labels.json: {where} is not a per-language object")
            return
        for code in langs:
            if not str(entry.get(code) or "").strip():
                report.fail(f"site/labels.json: {where} has no {code} translation")

    every_language(site.get("footer"), "footer")
    for code, label in site.get("confidenceLabels", {}).items():
        every_language(label, f"confidenceLabels.{code}")
    for g in site.get("groups", []):
        every_language(g.get("title"), f"groups.{g.get('key')}.title")
    for key, value in site.get("ui", {}).items():
        if not key.startswith("_"):
            every_language(value, f"ui.{key}")

    # The relation vocabulary is keyed by language at the top, because its *shape*
    # differs: English stacks one prefix where Dutch has a word per step. So it is
    # checked for the same set of keys in each language rather than field by field.
    kinship = {k: v for k, v in site.get("kinship", {}).items() if not k.startswith("_")}
    for code in langs:
        if code not in kinship:
            report.fail(f"site/labels.json: kinship has no {code} vocabulary")
    shapes = {code: set(v) for code, v in kinship.items()}
    if shapes:
        expected = set.union(*shapes.values())
        for code, keys in shapes.items():
            for missing in sorted(expected - keys):
                report.fail(f"site/labels.json: kinship.{code} is missing \"{missing}\"")


def _check_plausibility(report, people, children_of):
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
            report.warn(f"{pid}.md: dies {died} but is born {born}")
        if born and died and died - born > MAX_LIFESPAN + slack:
            report.warn(f"{pid}.md: lifespan {died - born} years — check the pair is one person")

        for cid in children_of.get(pid, []):
            child_born, child_slack = dated(people[cid], "birth")
            if not (born and child_born):
                continue
            age = child_born - born
            give = born_slack + child_slack
            is_mother = parent_id(people[cid], "mother") == pid
            upper = MAX_MOTHER_AGE if is_mother else MAX_FATHER_AGE
            if age < MIN_PARENT_AGE - give or age > upper + give:
                role = "mother" if is_mother else "father"
                report.warn(
                    f"{pid}.md: is {role} of {cid} at age {age} — a generation may be missing")
            # A father's child may be born after he dies; a mother's may not.
            if died and child_born > died + died_slack + child_slack + (0 if is_mother else 1):
                report.warn(
                    f"{pid}.md: {cid} is born {child_born}, after this parent dies {died}")


def _check_duplicates(report, people, children_of):
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
            if parent_id(p, rel) in people:
                related.add(frozenset((pid, parent_id(p, rel))))
        for s in p.get("spouses") or []:
            if s.get("id") in people:
                related.add(frozenset((pid, s["id"])))
    for _, kids in children_of.items():
        for i, a in enumerate(kids):
            for b in kids[i + 1:]:
                related.add(frozenset((a, b)))  # siblings

    # The duplicate check compares tree people with each other, but `compare` reaches for
    # the corpus frequencies to weigh a surname — and when the index is stale that falls
    # back to counting every held act. The validator runs before every commit, so it is the
    # last place that should silently pay for a 1.7-million-act scan: bringing the index
    # up to date once is cheaper than scanning on every run, and it is announced rather
    # than appearing as an unexplained pause.
    store.ensure(verbose=True)
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
                report.warn(
                    f"{c.ref}.md and {other.ref}.md may be the same person — {m.explain()}. "
                    f"Check with: uv run tools/identify.py --person {c.ref}"
                )


def _check_search_log(report, sites, pages, people):
    try:
        log = reg.load_log()
    except ValueError as e:
        report.fail(str(e))
        return
    for problem in reg.registry_problems(sites, pages, log, people, load_artifacts()):
        report.fail(problem)


def _check_forenames(report):
    """`data/forenames.json` — the names that are one name in another language.

    Errors, not warnings, unlike the label checks: a bad entry here silently changes what the
    scorer believes agrees, across the whole corpus at once, and there is no judgement to be
    made about a duplicate. The cross-block check earned its place immediately — it catches
    `corneille`, the French masculine Cornelius, which the first draft of the table also put
    into the feminine `cornelia` group.
    """
    try:
        blocks = load_forenames()
    except FileNotFoundError:
        return report.fail("data/forenames.json is missing")
    if set(blocks) != {"m", "f"}:
        report.fail(f'data/forenames.json: blocks must be exactly "m" and "f", not {sorted(blocks)}')
    where: dict[str, str] = {}
    for sex, groups in blocks.items():
        for group in groups:
            if len(group) < 2:
                report.fail(f"data/forenames.json: {sex} group {group} has nothing to fold to")
            for token in group:
                if normalise_key(token) != token:
                    report.fail(f'data/forenames.json: "{token}" is not normalised — '
                         f'write it as "{normalise_key(token)}"')
                if token in NOT_A_FORENAME:
                    report.fail(f'data/forenames.json: "{token}" is a particle, not a forename')
                if token in where:
                    report.fail(f'data/forenames.json: "{token}" appears in {where[token]} and in '
                         f"{sex} {group[0]} — a name folds one way or it folds ambiguously, "
                         "and across the sexes it merges a brother with his sister")
                where[token] = f"{sex} {group[0]}"


def _check_links(report, people, meta, source_ids):
    """A link is a fact, so it is checked like one.

    The SHAPE is an error. A link block with no `id`, a confidence outside the vocabulary,
    or a citation to a source that is not registered — all mechanical, all unambiguous, and
    every one of them makes the page assert something nobody can trace. `unk` is refused
    here specifically: on a person it means "not researched yet", and on a link there is no
    such state, so allowing it would put a drawn edge and an absent one in the same bucket.

    The COST is a warning: how many people an assumed link is carrying, and whether it rests
    on another assumption. Both are repaired by research nobody can do on demand, and the
    project's rule is that the validator is green before a commit. Failing on them would
    make the cheapest way back a deletion of the record of the guess — the tree would get
    LESS honest under pressure, which is exactly backwards.
    """
    for pid, p in sorted(people.items()):
        for role in ("father", "mother"):
            link = link_of(p, role)
            if not link:
                continue
            for k in link:
                if k not in LINK_FIELDS:
                    report.warn(f'{pid}.md: {role} link has unknown field "{k}"')
            if not link.get("id"):
                report.fail(f'{pid}.md: "{role}" is a block with no "id"')
            _check_edge(report, f"{pid}.md: {role}", link, source_ids)
        for i, s_ in enumerate(p.get("spouses") or []):
            if isinstance(s_, dict):
                _check_edge(report, f"{pid}.md: spouses[{i}]", s_, source_ids)
        _check_siblings(report, pid, p, people, source_ids)

    edges = weak_edges(people, meta.get("roots") or [])
    if not edges:
        return
    for e in edges:
        where = f"{e['person']}.md ({e['link']} → {e['parent']})"
        # The compounding the scorer is protected from, surfacing in the shape of the tree
        # instead. Two assumptions in a chain multiply: the upper one was reasoned about as
        # if the lower were settled, because on the page it looks exactly like a settled one.
        if e["stacked"]:
            report.warn(f"{where}: rests on another assumed link — {e['parent']}.md is itself "
                        "only assumed to be where it is, so this is a guess on a guess")
        if len(e["at_stake"]) >= WEAK_EDGE_BLAST_RADIUS:
            report.warn(f"{where}: {len(e['at_stake'])} people are in the tree only through "
                        "this assumed link and would leave with it — worth a document")
    print(f"note  {len(edges)} assumed link(s) drawn — uv run tools/research.py weak",
          file=sys.stderr)


def _check_edges_written(report, people):
    """Every edge is written out in full, and still says what the links imply.

    This is the check that makes materialising a derived relation safe rather than reckless.
    Sibling edges duplicate what the parent links already state — 994 of them — and a copy
    that nothing verifies is precisely the failure the data model is built to avoid. So it
    is verified: `familytree.edges.planned` says what each record should say, and a record
    that disagrees fails the build. Correct a parent link and the sibling edges resting on it
    go stale loudly, on the next build, instead of quietly describing a family that changed.

    Same pattern as the bundle and the rendered docs, pointed at `data/` instead of `dist/`:
    generated by a command, checked by the validator, never kept in step by hand.
    """
    try:
        stale = sorted(pid for pid, fields in planned(people).items()
                       if rewrite(pid, fields) is not None)
    except SystemExit as e:            # a record that would not survive the round trip
        return report.fail(str(e))
    if stale:
        shown = ", ".join(stale[:5]) + (f" and {len(stale) - 5} more" if len(stale) > 5 else "")
        report.fail(f"{len(stale)} record(s) have edges that are not written out or no longer "
                    f"match the links they derive from ({shown}) — run: uv run tools/edges.py sync")


def _check_siblings(report, pid, p, people, source_ids):
    """The one relationship this project stores, and the fence that keeps it honest.

    `siblings` exists for a case the parent links cannot express: an act naming two people
    as brother and sister without naming a parent either can be grafted to. `antoine_vanald`
    describes exactly that and had to give the fact up — "she cannot be linked as a sibling
    while the parents themselves are only a frontier".

    THE INVARIANT: a stated sibling link between two people who already share a recorded
    parent is an ERROR, not a duplicate to tolerate. That is what stops this field becoming
    the second, uncheckable copy of the tree that the data model forbids — the exception is
    scoped to precisely the case where there is nothing to be a second copy OF. Get it wrong
    and the two copies drift, which is how "Ronny's sister" written into prose survives a
    correction to the links that made it false.
    """
    for i, s in enumerate(p.get("siblings") or []):
        where = f"{pid}.md: siblings[{i}]"
        if not isinstance(s, dict):
            report.fail(f"{where}: must be a block with id/confidence/source/note")
            continue
        for k in s:
            if k not in SIBLING_FIELDS:
                report.warn(f'{where}: unknown field "{k}"')
        other = s.get("id")
        # No `name`-only form, unlike spouses. A spouse with no record still belongs on the
        # card as a name; a sibling with no record connects nothing in the graph, which is
        # the only reason to state one — and prose already holds an unlinked name better.
        if not other:
            report.fail(f'{where}: has no "id" — a sibling with no record connects nothing; '
                        "put an unlinked name in the prose body instead")
            continue
        if other == pid:
            report.fail(f"{where}: is listed as their own sibling")
            continue
        if other not in people:
            report.fail(f'{where}: "{other}" does not exist')
            continue
        _check_edge(report, where, s, source_ids)

        # Redundancy with the parent links is expected and fine — `edges.py` writes exactly
        # those entries, and the sync check below is what stops them drifting. What is NOT
        # fine is a stated sibship the parent links CONTRADICT: two people whose parents are
        # both fully recorded and share nobody are not siblings, whatever an entry says, and
        # one of the two facts is wrong. Only fully-known pairs are judged, because a missing
        # parent is the ordinary case this field exists to serve.
        mine = [parent_id(p, r) for r in ("father", "mother")]
        theirs = [parent_id(people[other], r) for r in ("father", "mother")]
        if all(mine) and all(theirs) and not set(mine) & set(theirs):
            report.fail(
                f"{where}: {pid} and {other} are stated siblings, but both have two recorded "
                f"parents and share none of them ({'+'.join(mine)} against {'+'.join(theirs)}) "
                "— the parent links and this entry cannot both be right")
        # Mutual, exactly like marriage, and for the same reason: siblinghood is symmetric,
        # so a one-sided entry means the tree answers differently depending on whose record
        # is read. One relationship, one set of facts.
        back = next((t for t in people[other].get("siblings") or []
                     if isinstance(t, dict) and t.get("id") == pid), None)
        if back is None:
            report.fail(f'{where}: lists "{other}", but {other}.md does not list "{pid}" back')
            continue
        for field in ("confidence", "source", "note"):
            if s.get(field) != back.get(field):
                report.fail(f'{pid}.md and {other}.md disagree about being siblings: '
                            f'{field} is "{s.get(field)}" here and "{back.get(field)}" there')


def _check_edge(report, where, link, source_ids):
    """The fields every link carries, wherever it appears. Shared so a parent link and a
    marriage cannot end up held to different standards — a marriage grafted on one
    identifier is the same claim on the same evidence as a parent grafted on one, and the
    first draft of this checked the note on parents only."""
    conf = link.get("confidence")
    if conf is not None and conf not in EDGE_CONFIDENCE:
        report.fail(f"{where}: confidence \"{conf}\" is not one of "
                    f"{', '.join(EDGE_CONFIDENCE)}"
                    + (' — "unk" is a state a person can be in, not a link'
                       if conf == "unk" else ""))
    # This is rule 2 finally made checkable. While `sources` was a person-level list, "every
    # new parent link cites a source" could not be verified by anything: the citation and
    # the claim sat in the same file without being attached to each other.
    if link.get("source") and link["source"] not in source_ids:
        report.fail(f'{where}: cites source "{link["source"]}", '
                    "which is not in research/sources.json")
    # An assumption nobody explained cannot be checked by anyone later, including whoever
    # made it. The note IS the finding; the link is only its consequence, and it is what the
    # page shows beside the red mark.
    if conf in NOT_EVIDENCE and not (link.get("note") or "").strip():
        report.fail(f"{where}: is assumed but says nothing about why — name the one "
                    "identifier it rests on and the one still missing")


def _check_labels(report, people):
    """The gold standard, checked for the two ways it goes quietly useless.

    `research/searches.jsonl` has been validated here since it existed;
    `research/labels.jsonl` never has, and it is the more valuable file — every verifier
    ruling this project will ever produce, and the only thing that turns the thresholds in
    match.py from reasoned guesses into measurements.

    WARNINGS, NOT ERRORS, both of them. Each one is repaired by a judgement nobody but a
    person can make — which participant of a six-person act the ruling was about, or whether
    a ruling about a retracted record should be re-pointed or dropped — and failing the build
    over it would make the choice urgent instead of considered. The rule is that the
    validator is green before a commit; that must not become a reason to delete evidence.
    """
    path = ROOT / "research" / "labels.jsonl"
    if not path.exists():
        return
    act_level: list[str] = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            label = json.loads(line)
        except json.JSONDecodeError as e:
            report.fail(f"research/labels.jsonl:{n}: not valid JSON — {e}")
            continue
        for required in ("person", "ref"):
            if not label.get(required):
                report.fail(f'research/labels.jsonl:{n}: no "{required}"')
        person, ref = label.get("person"), label.get("ref") or ""
        # A ruling about a person who is no longer in the tree cannot be re-scored, so it
        # silently stops counting. The known case is a record retracted after the act was
        # re-read: correct to retract, and the ruling that justified it was left pointing at
        # nothing. It is still evidence — re-point it at whoever remains the frontier.
        if person and person not in people:
            report.warn(
                f'research/labels.jsonl:{n}: labels "{person}", who has no record — '
                "the ruling cannot be re-scored until it names someone in the tree")
        if ref and "#" not in ref:
            act_level.append(ref)
    if not act_level:
        return
    # The bug that made this project report 33% recall for a scorer with no known errors. An
    # act names six people; the ref alone does not say which, so the scorer is handed
    # whichever comes first — usually the groom.
    #
    # Split by whether anyone can actually act on it. A label naming an act the corpus does
    # not hold has no participants to choose between yet and resolves itself on the next
    # harvest; reporting those together with the rest turned a backlog of four into one of
    # twenty-two, and a number nobody can reduce is a number that gets ignored.
    held = store.acts_by_id(act_level) if store.ensure() else {}
    actionable = [r for r in act_level if r in held] if held else act_level
    if actionable:
        # Deliberately not claimed as "uncounted": `evaluate.py` resolves an act-level ref
        # where exactly one participant shares the surname, so some of these do score. How
        # many is its question to answer, and duplicating that disambiguation here would put
        # a second copy of it in a file whose job is to have no opinions about scoring.
        report.warn(
            f"research/labels.jsonl: {len(actionable)} label(s) name a held act rather than one "
            "of its people. `uv run tools/evaluate.py refs` prints the command for each "
            "participant; `report` says how many are going uncounted because of it")
    waiting = len(act_level) - len(actionable)
    if waiting:
        report.warn(
            f"research/labels.jsonl: {waiting} label(s) name an act not yet harvested — "
            "nothing to do, they resolve when it is held")


def _check_artifacts(report, people, source_ids):
    """Artifacts are the evidence itself. A record pointing at a file that is missing is
    a citation to nothing; a file whose bytes no longer match the recorded digest is
    worse, because the claim still looks sourced while the proof has changed under it."""
    artifacts = load_artifacts()
    for aid, a in artifacts.items():
        if a.get("id") != aid:
            report.fail(f"artifacts/{aid}.md: \"id\" says \"{a.get('id')}\"")
        if not a.get("title"):
            report.fail(f'artifacts/{aid}.md: missing "title"')
        for k in a:
            if k not in ARTIFACT_FIELDS and k != "note":
                report.warn(f'artifacts/{aid}.md: unknown field "{k}"')
        if a.get("date") and not is_valid_date(a["date"]):
            report.fail(f"artifacts/{aid}.md: date \"{a['date']}\" is not a valid date")
        if a.get("source") and a["source"] not in source_ids:
            report.fail(f"artifacts/{aid}.md: source \"{a['source']}\" is not registered")
        for pid in a.get("evidences") or []:
            if pid not in people:
                report.fail(f"artifacts/{aid}.md: evidences \"{pid}\", who does not exist")

        if not a.get("file"):
            report.fail(f'artifacts/{aid}.md: missing "file"')
            continue
        f = ARTIFACTS_DIR / a["file"]
        if not f.exists():
            report.fail(f"artifacts/{aid}.md: file \"{a['file']}\" is missing")
            continue
        data = f.read_bytes()
        if a.get("bytes") and int(a["bytes"]) != len(data):
            report.fail(f"artifacts/{aid}.md: file is {len(data)} bytes, the record says {a['bytes']}")
        if a.get("sha256") and sha256(data).hexdigest() != a["sha256"]:
            report.fail(f"artifacts/{aid}.md: sha256 does not match the file — the evidence has changed")
    if ARTIFACTS_DIR.is_dir():
        for f in sorted(ARTIFACTS_DIR.iterdir()):
            if f.suffix != ".md" and not any(a.get("file") == f.name for a in artifacts.values()):
                report.warn(f"artifacts/{f.name}: no record describes this file")


if __name__ == "__main__":
    raise SystemExit(main())
