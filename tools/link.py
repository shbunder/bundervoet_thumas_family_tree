#!/usr/bin/env python3
"""What the held corpus says about a frontier — candidates, never conclusions.

This is the join that makes harvesting worth doing. It takes a person in the tree,
finds every mention in the corpus that could be them, scores each one by how much rare
evidence agrees, and prints what the act would give if the identification held: the
parents it names, the spouse, the act number, and a link to the scan so the claim can
be checked against the image rather than against an index.

It writes nothing, and it decides nothing. Every candidate it prints defaults to NOT
PROVEN — the two-independent-identifiers rule is applied as a floor, a stated conflict
is a veto, and everything that survives is still a lead for the verifier to try to
refute. The point is to put the evidence in front of that judgement quickly, not to
make it.

    uv run tools/link.py anna_vc                  one person
    uv run tools/link.py --frontiers --limit 8    the top of the queue
    uv run tools/link.py anna_vc --all            include the weak matches too
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from familytree.corpus import (  # noqa: E402
    Mention, corpus_exists, corpus_mentions, frequencies, normalise_key,
)
from familytree.frontier import children_index, frontier_rows  # noqa: E402
from familytree.match import (  # noqa: E402
    build_index, candidates_for, compare, from_mention, from_person, surname_weight,
)
from familytree.people import load_config, load_people  # noqa: E402

BANDS = {"strong": "STRONG", "read the act": "READ THE ACT", "noise": "weak", "rejected": "rejected"}


def relatives_in_act(m: Mention) -> list[str]:
    """What the act says about this person, as relationships rather than roles.

    A father named in an act is the whole reason the act is worth fetching; printing
    "Vader: Antonius Josephus" is what turns a search result into a decision a person
    can make.
    """
    act = m.act
    if not act:
        return []
    by_pid = {p.pid: p for p in act.people}
    out = []
    for e in act.edges:
        if e["type"] in ("father", "mother") and e["child"] == m.pid:
            parent = by_pid.get(e["parent"])
            if parent:
                extra = []
                if parent.age is not None:
                    extra.append(f"age {parent.age}")
                if parent.birth_place:
                    extra.append(f"b. {parent.birth_place}")
                if parent.occupation:
                    extra.append(parent.occupation)
                label = "father" if e["type"] == "father" else "mother"
                out.append(f"{label}: {parent.name}" + (f" ({', '.join(extra)})" if extra else ""))
        elif e["type"] == "couple" and m.pid in (e["a"], e["b"]):
            other = by_pid.get(e["b"] if e["a"] == m.pid else e["a"])
            if other:
                out.append(f"spouse: {other.name}")
    return out


def report(person, index, freq, show_all: bool, people=None, children=None) -> int:
    # With the tree passed in, the person brings their relatives to the comparison, and
    # a father's name in an act becomes the second identifier the rule asks for.
    c = from_person(person, people, children)
    weight = surname_weight(c.surname, freq)
    held = sum(1 for m in corpus_mentions() if normalise_key(m.surname) == normalise_key(c.surname))
    rarity = f"{weight.bits:.1f} bits"
    rarity += f" ({weight.count} in Belgium)" if weight.count is not None else " (estimated)"
    print(f"\n{person['name']}  ({person['id']})")
    print(f"  surname evidence: {rarity} · {held} mentions held")
    if held == 0:
        print("  nothing harvested under this surname yet — "
              f"uv run tools/harvest.py surname \"{c.surname}\"")
        return 0

    matches = sorted(
        (compare(c, other, freq) for other in candidates_for(c, index)),
        key=lambda m: -m.bits,
    )
    shown = [m for m in matches if show_all or m.band in ("strong", "read the act")]
    if not shown:
        blocked_by = sum(1 for m in matches if m.conflict)
        print(f"  {len(matches)} candidates compared, none above the noise floor"
              + (f" ({blocked_by} vetoed on a stated conflict)" if blocked_by else ""))
        return 0

    print(f"  {len(shown)} candidate(s) worth reading, of {len(matches)} compared:\n")
    for m in shown:
        mention = m.b.mention
        act = mention.act
        print(f"    [{BANDS[m.band]}] {mention.name}  — {mention.role} in {act.label}")
        print(f"      {m.explain()}")
        for line in relatives_in_act(mention):
            print(f"      · {line}")
        if not m.graftable:
            reason = ("a stated conflict vetoes it" if m.conflict
                      else f"only {m.independent} independent identifier(s) — the rule needs two")
            print(f"      NOT GRAFTABLE — {reason}")
        print(f"      {act.url}")
        if act.original:
            print(f"      act:  {act.original}")
        if act.scan:
            print(f"      scan: {act.scan}")
        print()
    return len(shown)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("person", nargs="?", help="a person id from data/people/")
    parser.add_argument("--frontiers", action="store_true", help="run over the top of the frontier queue")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--all", action="store_true", help="show the weak matches too")
    args = parser.parse_args()

    if not corpus_exists():
        raise SystemExit("error nothing harvested yet — run: uv run tools/harvest.py frontiers")
    people = load_people(load_config()["roster"])

    if args.person:
        targets = [args.person]
    elif args.frontiers:
        targets = [r.id for r in frontier_rows(people)][: args.limit]
    else:
        parser.error("give a person id, or --frontiers")
    for pid in targets:
        if pid not in people:
            raise SystemExit(f'error unknown person "{pid}"')

    freq = frequencies()
    index = build_index(from_mention(m) for m in corpus_mentions())
    children = children_index(people)
    total = sum(report(people[pid], index, freq, args.all, people, children) for pid in targets)
    print(f"\n{total} candidate(s) across {len(targets)} person(s). None of them is a fact yet:")
    print("  every one still has to survive an attempt to refute it before it is grafted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
