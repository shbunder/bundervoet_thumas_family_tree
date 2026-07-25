#!/usr/bin/env python3
"""Every person in the tree, scored against every act held — in one pass.

`tools/link.py` answers "what does the corpus say about this person", and running it
person-by-person over three hundred records reloads and re-indexes the whole corpus each
time. This asks the same question of the whole tree at once, so a verification sweep is
one pass over the acts rather than three hundred, and prints a table of who is
corroborated, who is contradicted, and who the corpus simply cannot reach.

It writes nothing and grafts nothing. Its output is a worklist: STRONG means two or more
independent identifiers agree and nothing conflicts, which is the floor CLAUDE.md sets
before a claim may even be considered — not a decision that it is true.

    uv run tools/verify_all.py                    the whole tree
    uv run tools/verify_all.py --line bundervoet  one line
    uv run tools/verify_all.py --strong-only      just what is corroborated
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from familytree.corpus import (  # noqa: E402
    corpus_exists, corpus_mentions, frequencies, normalise_key,
)
from familytree.match import (  # noqa: E402
    build_index, candidates_for, compare, from_mention, from_person,
)
from familytree.frontier import children_index  # noqa: E402
from familytree.people import load_config, load_people  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--line", help="only people on this line")
    ap.add_argument("--strong-only", action="store_true", help="only people with a graftable match")
    ap.add_argument("--min-bits", type=float, default=0.0, help="ignore matches below this")
    args = ap.parse_args()

    if not corpus_exists():
        print("Nothing harvested yet — uv run tools/harvest.py surname <name>")
        return 1

    people = load_people(load_config()["roster"])
    mentions = corpus_mentions()
    freq = frequencies()

    # Index the corpus once. Everything after this is a lookup inside a block rather
    # than a scan, which is the only reason a full sweep is affordable at all.
    index = build_index([from_mention(m) for m in mentions])

    # How many mentions the corpus holds under each surname. Without this, a person
    # whose family has never been harvested still matches somebody — on a shared
    # forename and a shared birth year, across two unrelated families. That is exactly
    # the coincidence the two-identifier rule exists to reject, and it read as
    # "corroborated" until this guard was added.
    held_by_surname: dict[str, int] = {}
    for m in mentions:
        held_by_surname[normalise_key(m.surname)] = held_by_surname.get(normalise_key(m.surname), 0) + 1

    children = children_index(people)
    rows = []
    for pid, p in sorted(people.items()):
        if args.line and p.get("line") != args.line:
            continue
        me = from_person(p, people, children)
        if not held_by_surname.get(normalise_key(me.surname)):
            rows.append((pid, p, None, "unharvested"))
            continue
        best = None
        for other in candidates_for(me, index):
            m = compare(me, other, freq)
            if m.conflict or m.bits < args.min_bits:
                continue
            # The tool's own noise floor, not a threshold invented here.
            if m.band not in ("strong", "read the act"):
                continue
            if best is None or m.bits > best.bits:
                best = m
        rows.append((pid, p, best, "compared"))

    # A match that agrees on nothing but a surname and a relative's forename is not
    # corroboration, however many bits it scores. Gustaaf Dekeyser's best candidate was a
    # man in Aalst in 1809; Simonne Vandewalle's was a woman bearing Dekeyser children a
    # decade before Simonne was born. Both scored "strong" on surname + kin alone, because
    # for the commonest Flemish surnames that combination is close to no information. So a
    # date or a place has to agree too before this reports the word "corroborated".
    def anchored(m):
        return bool({"date", "place"} & set(m.classes))

    ok = lambda m: m.band == "strong" and m.graftable
    strong = [r for r in rows if r[2] and ok(r[2]) and anchored(r[2])]
    unanchored = [r for r in rows if r[2] and ok(r[2]) and not anchored(r[2])]
    weak = [r for r in rows if r[2] and not ok(r[2])]
    none = [r for r in rows if not r[2]]

    def show(label, group):
        if not group:
            return
        print(f"\n{label} ({len(group)})")
        for pid, p, m, _why in sorted(group, key=lambda r: -(r[2].bits if r[2] else 0)):
            line = f"  {pid:<28} {(p.get('name') or '')[:34]:<36}"
            if m:
                line += f"{m.bits:6.1f} bits  {m.independent} indep ({'+'.join(m.classes)})"
            print(line)
            if m:
                print(f"      {', '.join(lbl for _, lbl, _ in m.agree)}")
                if getattr(m.b, "url", None):
                    print(f"      {m.b.url}")

    print(f"{len(rows)} people compared against {len(mentions)} mentions held.")
    show("CORROBORATED — a date or place agrees as well as the names, and nothing conflicts", strong)
    show("NAME AND KIN ONLY — no date, no place: treat as a lead, not corroboration", unanchored)
    if not args.strong_only:
        show("PARTIAL — something agrees, but not two independent identifiers", weak)
        show("NOT REACHED — surname never harvested, or nothing above the noise floor", none)

    print(f"\n{len(strong)} corroborated · {len(unanchored)} name-and-kin only · "
          f"{len(weak)} partial · {len(none)} not reached")
    print("None of these is a fact: every one still has to survive an attempt to refute it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
