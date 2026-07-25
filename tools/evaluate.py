#!/usr/bin/env python3
"""The gold standard: what the verifier decided, kept as data the scorer is measured on.

Every other part of this project treats a verifier ruling as a one-off — the candidate
is grafted or dropped, and the reasoning goes into the log as prose. That throws away
the only labelled data this project will ever have. A ruling is a *labelled pair*: two
records, and a human-or-adversarial judgement that they are or are not the same person.
Kept, they turn every threshold in match.py from a guess into a measurement.

This matters more the larger the tree gets. `graftable` currently requires two
independent classes and six distinguishing bits. Those numbers were chosen by reading
output, which is the only thing anyone could have done without labels — but it means
nobody can say what they cost. With a few hundred labels you can say: at this threshold
the scorer misses one true link in nine, and one in forty it proposes is wrong. That is
the difference between a tool you trust and a tool you audit by hand forever.

A label is never evidence. It records that a judgement was made, by whom, and why — and
a wrong label is corrected the same way a wrong graft is, by writing a new one.

    uv run tools/evaluate.py label anna_vc abt:c59c… --match --why "act names both parents"
    uv run tools/evaluate.py label anna_vc gnt:d4f1… --nonmatch --why "wrong province"
    uv run tools/evaluate.py report            precision, recall and where they disagree
    uv run tools/evaluate.py sweep             what the thresholds would cost if moved
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from familytree.corpus import corpus_exists, corpus_mentions  # noqa: E402
from familytree.corpus import frequencies  # noqa: E402
from familytree.frontier import children_index  # noqa: E402
from familytree.match import compare, from_mention, from_person  # noqa: E402
from familytree.people import ROOT, load_config, load_people  # noqa: E402

LABELS = ROOT / "research" / "labels.jsonl"

# Who decided, and how much that is worth. Kept explicit because a label from a read act
# and a label from a plausible-looking index page are not the same evidence, and a gold
# standard that mixes them silently measures the wrong thing.
BASES = ("act", "index", "tree", "reasoning")


@dataclass
class Label:
    person: str
    ref: str
    match: bool
    basis: str
    why: str
    date: str


def read_labels() -> list[Label]:
    if not LABELS.exists():
        return []
    out = []
    for line in LABELS.read_text(encoding="utf-8").split("\n"):
        if line.strip():
            r = json.loads(line)
            out.append(Label(r["person"], r["ref"], r["match"], r.get("basis", "reasoning"),
                             r.get("why", ""), r.get("date", "")))
    # Later labels supersede earlier ones for the same pair — corrections are first-class
    # here exactly as they are in the tree.
    latest: dict[tuple[str, str], Label] = {}
    for lab in out:
        latest[(lab.person, lab.ref)] = lab
    return list(latest.values())


def cmd_label(args) -> int:
    people = load_people(load_config()["roster"])
    if args.person not in people:
        raise SystemExit(f'error unknown person "{args.person}"')
    if not args.why:
        raise SystemExit("error a label without a reason is not a label — pass --why")
    row = {
        "person": args.person,
        "ref": args.ref,
        "match": bool(args.match),
        "basis": args.basis,
        "why": args.why,
        "date": dt.date.today().isoformat(),
    }
    LABELS.parent.mkdir(parents=True, exist_ok=True)
    with LABELS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    verdict = "MATCH" if args.match else "NOT a match"
    print(f"recorded: {args.person} × {args.ref} — {verdict} ({args.basis}) — {args.why}")
    return 0


def _scored(labels: list[Label]):
    """Each label, re-scored by the scorer as it stands today.

    Re-scored rather than stored: the whole point is to see what a change to match.py
    does to judgements that were already made, so the score has to come from the current
    code and never from what it was when the label was written.
    """
    people = load_people(load_config()["roster"])
    children = children_index(people)
    freq = frequencies()
    by_ref = {f"{m.act.id}#{m.pid}" if m.act else m.pid: m for m in corpus_mentions()}
    # Labels are written against act ids, which is what link.py prints; a mention ref
    # carries the participant too.
    for lab in labels:
        if lab.person not in people:
            continue
        mention = by_ref.get(lab.ref) or next(
            (m for r, m in by_ref.items() if r.split("#")[0] == lab.ref), None)
        if mention is None:
            yield lab, None
            continue
        a = from_person(people[lab.person], people, children)
        yield lab, compare(a, from_mention(mention), freq)


def cmd_report(args) -> int:
    labels = read_labels()
    if not labels:
        print("No labels yet. Every verifier ruling is one — record them as they happen:")
        print('  uv run tools/evaluate.py label <person> <act-id> --match --why "…"')
        print("\nUntil then every threshold in match.py is a reasonable guess that")
        print("nobody can price. Around fifty labels is enough to start pricing them.")
        return 0
    if not corpus_exists():
        raise SystemExit("error nothing harvested yet — the labels cannot be re-scored")

    tp = fp = tn = fn = 0
    missing = 0
    disagreements = []
    for lab, m in _scored(labels):
        if m is None:
            missing += 1
            continue
        proposed = m.graftable
        if lab.match and proposed:
            tp += 1
        elif lab.match and not proposed:
            fn += 1
            disagreements.append(("MISSED", lab, m))
        elif not lab.match and proposed:
            fp += 1
            disagreements.append(("WRONGLY PROPOSED", lab, m))
        else:
            tn += 1

    print(f"{len(labels)} labels · {tp + fp + tn + fn} re-scored"
          + (f" · {missing} no longer in the corpus" if missing else ""))
    print(f"\n  confirmed matches the scorer would graft   {tp}")
    print(f"  confirmed matches it would MISS            {fn}")
    print(f"  refuted pairs it would wrongly graft       {fp}")
    print(f"  refuted pairs it correctly rejects         {tn}")

    if tp + fp:
        print(f"\n  precision  {tp / (tp + fp):.1%}   of what it proposes, this much is right")
    if tp + fn:
        print(f"  recall     {tp / (tp + fn):.1%}   of what is true, this much it finds")
    # Precision is the one that matters here, and the asymmetry is deliberate: a missed
    # link is found again next pass, a wrong graft is invisible forever.
    if fp:
        print("\n  A false graft is the failure this project is built to avoid. Every")
        print("  entry below is one the current thresholds would have let through.")

    for kind, lab, m in disagreements[: args.limit]:
        print(f"\n  [{kind}] {lab.person} × {lab.ref}")
        print(f"      labelled {'match' if lab.match else 'not a match'} ({lab.basis}): {lab.why}")
        print(f"      scorer: {m.explain()}")
    return 0


def cmd_sweep(args) -> int:
    """What the two thresholds cost, at every setting the labels can speak to.

    This is the number `graftable` was missing. It does not choose the threshold — the
    asymmetry between a missed link and a false graft is a judgement about this project's
    purpose, not something a table decides.
    """
    labels = read_labels()
    if not labels:
        return cmd_report(args)
    scored = [(lab, m) for lab, m in _scored(labels) if m is not None]
    print(f"{len(scored)} labelled pairs re-scored.\n")
    print(f"  {'bits':>5} {'classes':>8} {'graft':>6} {'right':>6} {'wrong':>6} {'missed':>7}")
    for bits in (4, 6, 8, 10, 12, 16):
        for classes in (2, 3):
            graft = [(lab, m) for lab, m in scored
                     if not m.conflict and m.independent >= classes and m.distinguishing >= bits]
            right = sum(1 for lab, _ in graft if lab.match)
            wrong = len(graft) - right
            missed = sum(1 for lab, m in scored
                         if lab.match and not (not m.conflict and m.independent >= classes
                                               and m.distinguishing >= bits))
            print(f"  {bits:>5} {classes:>8} {len(graft):>6} {right:>6} {wrong:>6} {missed:>7}")
    print("\n  Current setting: 6 bits, 2 classes. Raising either trades recall for")
    print("  precision, and this project has always chosen precision.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("label", help="record a verifier ruling as a labelled pair")
    p.add_argument("person", help="a person id from data/people/")
    p.add_argument("ref", help="an act id, or act-id#participant, as link.py prints it")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--match", action="store_true", help="the verifier accepted it")
    g.add_argument("--nonmatch", dest="match", action="store_false", help="the verifier refuted it")
    p.add_argument("--basis", choices=BASES, default="reasoning",
                   help="how it was judged: the act image, an index page, a member tree, or reasoning")
    p.add_argument("--why", required=True, help="the reasoning — a label without one is not a label")
    p.set_defaults(fn=cmd_label)

    p = sub.add_parser("report", help="precision, recall, and every pair the scorer gets wrong")
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(fn=cmd_report)

    p = sub.add_parser("sweep", help="what moving the thresholds would cost")
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(fn=cmd_sweep)

    args = parser.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
