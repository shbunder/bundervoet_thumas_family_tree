#!/usr/bin/env python3
"""Is this person already in the tree? Ask before writing a new record.

The rule that every person referenced anywhere gets their own file means records get
added constantly, and the failure it invites is the quiet one: the same person entered
twice under two spellings. That does not look broken. It looks like two people, and it
splits a branch in half — the children hang off one copy and the parents off the other,
and no validator complains because both records are internally fine.

This runs the same blocking index and the same rarity-weighted comparison used against
the corpus, but against the tree itself. Run it before adding anyone; the validator
runs a stricter version of it on every build, so a duplicate that slips through is
caught at the next commit rather than in a year.

    uv run tools/identify.py "Amandus Van Craenenbroeck" --birth 1902 --place Zaventem
    uv run tools/identify.py --person anna_vc      who else could already be them
    uv run tools/identify.py --suggest-id "Amandus Franciscus Van Craenenbroeck"
"""

from __future__ import annotations

import argparse
import re
import unicodedata

from familytree.match import (
    Candidate, build_index, candidates_for, compare, from_person, phonetic,
)
from familytree.people import (
    PEOPLE_DIR, children_index, family_key, load_config, load_people,
)


def candidate_from_args(args) -> Candidate:
    """A person who does not have a record yet, in the shape everything else compares."""
    surname = args.surname
    if not surname:
        # Only a guess, and only for the query — a real record states its surname,
        # because a quarter of these names carry a particle the last word misses.
        surname = args.name.split()[-1] if args.name else ""
    given = args.name
    if surname and surname in args.name:
        at = args.name.rfind(surname)
        given = (args.name[:at] + args.name[at + len(surname):]).strip()
    year = None
    if args.birth:
        m = re.search(r"(\d{4})", args.birth)
        year = int(m.group(1)) if m else None
    return Candidate(
        ref="<new>",
        name=args.name,
        surname=surname,
        given=given,
        sex=args.sex,
        birth_year=year,
        birth_date=args.birth if args.birth and re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.birth) else None,
        birth_place=args.place,
        places=[p for p in [args.place] if p],
        stated_birth_year=bool(year),
    )


def suggest_id(name: str, taken: set[str]) -> str:
    """A stable, readable id that is not already used.

    Ids are stable and renaming one breaks every reference, so the only safe moment to
    choose well is before the file exists.
    """
    parts = [re.sub(r"[^a-z]", "", unicodedata.normalize("NFD", w.lower())) for w in name.split()]
    parts = [p for p in parts if p]
    if not parts:
        return "unnamed"
    first, last = parts[0], parts[-1]
    for base in (first, f"{first}_{last[0]}", f"{first}_{last[:3]}", f"{first}_{last}", last):
        if base and base not in taken:
            return base
    n = 2
    while f"{first}_{last}{n}" in taken:
        n += 1
    return f"{first}_{last}{n}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("name", nargs="?", help="the name as the source writes it")
    parser.add_argument("--person", help="an existing person id, to check against the rest of the tree")
    parser.add_argument("--surname", help="which part of the name is the family name")
    parser.add_argument("--birth", help="1902 or 1902-11-11")
    parser.add_argument("--place")
    parser.add_argument("--sex", choices=["f", "m"])
    parser.add_argument("--suggest-id", action="store_true", help="also propose an unused record id")
    args = parser.parse_args()
    if not args.name and not args.person:
        parser.error("give a name, or --person <id>")

    people = load_people(load_config()["roster"])
    children = children_index(people)
    index = build_index(from_person(p, people, children) for p in people.values())

    if args.person:
        if args.person not in people:
            raise SystemExit(f'error unknown person "{args.person}"')
        subject = from_person(people[args.person], people, children)
        label = people[args.person]["name"]
    else:
        subject = candidate_from_args(args)
        label = args.name

    matches = sorted((compare(subject, o) for o in candidates_for(subject, index)), key=lambda m: -m.bits)
    real = [m for m in matches if m.band in ("strong", "read the act")]

    print(f"{label}")
    print(f"  blocking on phonetic surname \"{phonetic(subject.surname)}\"" if subject.surname else "  no surname given")
    if not real:
        vetoed = sum(1 for m in matches if m.conflict)
        print(f"  no likely duplicate — {len(matches)} compared"
              + (f", {vetoed} vetoed on a stated conflict" if vetoed else ""))
    else:
        print(f"  {len(real)} record(s) that may already be this person:\n")
        for m in real:
            print(f"    {m.b.ref:<26} {people[m.b.ref]['name']}")
            print(f"      {m.explain()}")
            print(f"      data/people/{m.b.ref}.md")
        print("\n  If one of these IS them, edit that record rather than adding a new one.")
        print("  Two records for one person split a branch, and nothing else will notice.")

    if args.suggest_id and args.name:
        taken = set(people) | {f.stem for f in PEOPLE_DIR.glob("*.md")}
        print(f"\n  unused id: {suggest_id(args.name, taken)}")
        family = family_key(subject.surname)
        kin = [pid for pid, p in people.items() if family_key(p.get("surname")) == family]
        if kin:
            print(f"  {len(kin)} record(s) already share this family key ({family}): {', '.join(sorted(kin)[:8])}")
    return 0 if not real else 0


if __name__ == "__main__":
    raise SystemExit(main())
