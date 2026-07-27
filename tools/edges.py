#!/usr/bin/env python3
"""Write every link in the records out in full: explicit confidence, and siblings as edges.

    uv run tools/edges.py sync     rewrite data/people so every edge is stated
    uv run tools/edges.py check    say what is out of step, change nothing

A person file may write `father: lucien_vincke` and leave the rest implied. That is compact
and it is also half a model: the confidence of a link lives nowhere, and a sibship is a
thing you have to compute before you can read it. `sync` makes every edge say what it is,
in the file, so a record can be read on its own.

WHY THIS IS GENERATED AND NOT HAND-KEPT. Materialising a derived relation is the thing the
data model spends its whole design avoiding — a second copy that drifts from the first. It
is safe here for exactly one reason: it is regenerated from the parent links and the
validator FAILS when a record disagrees with what this tool would write. So the sibling
edges are not a second source of truth. They are a projection of the first, checked on
every build, in the same way `dist/bundle.js` is.

WHAT IT NEVER TOUCHES. Anything stated by hand wins: a `confidence` already on a link, a
`source`, a `note`, and any sibling entry naming somebody the parent links cannot reach.
Those are findings. This tool only fills in what it can derive, so running it can never
overwrite research with arithmetic.
"""

from __future__ import annotations

import argparse
import sys

from familytree.edges import planned, rewrite
from familytree.people import PEOPLE_DIR, load_config, load_people


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=("sync", "check"))
    args = parser.parse_args()

    people = load_people(load_config()["roster"])
    plan = planned(people)
    changes = {pid: text for pid in plan if (text := rewrite(pid, plan[pid])) is not None}

    if not changes:
        print(f"OK — every edge in {len(people)} records is already written out in full.")
        return 0
    if args.command == "check":
        for pid in sorted(changes):
            print(f"stale {pid}.md", file=sys.stderr)
        print(f"\n{len(changes)} record(s) have edges that are not written out. "
              "Run: uv run tools/edges.py sync", file=sys.stderr)
        return 1
    for pid, text in changes.items():
        (PEOPLE_DIR / f"{pid}.md").write_text(text, encoding="utf-8")
    print(f"{len(changes)} record(s) rewritten. Now run: uv run tools/build.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
