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

from familytree import store  # noqa: E402
from familytree.corpus import corpus_exists  # noqa: E402
from familytree.frontier import children_index  # noqa: E402
from familytree.match import compare, from_mention, from_person  # noqa: E402
from familytree.people import ROOT, family_key, load_config, load_people  # noqa: E402

# The reader lives in familytree/labels.py, not here. It was private to this file, which is
# why nothing else could read the gold standard and the queues went on re-proposing what a
# verifier had already refuted — see that module's opening note.
from familytree.labels import BASES, LABELS, Label, read_labels, reset_cache  # noqa: E402,F401


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
    reset_cache()
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
    store.ensure(verbose=True)
    freq = store.frequencies()
    # Only the acts the labels actually name. See store.acts_by_id — resolving 48 refs by
    # indexing every mention in the corpus cost three minutes once the corpus passed a
    # million acts.
    acts = store.acts_by_id(lab.ref.split("#", 1)[0] for lab in labels)
    by_ref: dict[str, object] = {}
    in_act: dict[str, list] = {}
    for act in acts.values():
        for m in act.people:
            by_ref[f"{act.id}#{m.pid}"] = m
            in_act.setdefault(act.id, []).append(m)

    for lab in labels:
        if lab.person not in people:
            # Yielded as unresolved rather than skipped. Skipping dropped it out of every
            # total — 48 labels, 33 re-scored, 14 unresolved, and one that simply evaporated —
            # which is the same silent-subtraction failure as a truncated list that does not
            # say it truncated. A ruling about a retracted record is still a ruling.
            yield lab, None
            continue
        a = from_person(people[lab.person], people, children)
        mention = by_ref.get(lab.ref)
        if mention is None:
            # An ACT-level ref, which is what `link.py` prints and what 45 of the first 48
            # labels were written with. An act names six people, so the ref alone does not
            # say which of them the ruling was about — and taking the first participant, as
            # this did, silently scored the wrong person: Maria Thérèsia Pardon against
            # Joseph Reniers, her own husband, and Hendrik Vandenbemden against a witness.
            # Every one of those came out REJECTED on a sex or birth-date conflict and was
            # counted as the scorer MISSING a confirmed match, which made recall a
            # measurement of this bug rather than of the scorer.
            #
            # Disambiguated on the surname alone — the cheapest identifier there is, and
            # the one the label's author was implicitly using. Deliberately not "the
            # best-matching participant": choosing the mention that scores highest would be
            # grading the scorer against a pair the scorer picked. The name class is
            # therefore guaranteed to agree in a resolved pair, which is why `graftable`
            # and `distinguishing` — both of which exclude the name — remain honest.
            candidates = [m for m in in_act.get(lab.ref, [])
                          if family_key(m.surname) and family_key(m.surname) == family_key(a.surname)]
            if len(candidates) != 1:
                # AN ACT-LEVEL REJECTION IS A RULING, not a malformed pairwise one, and it
                # can be scored without inventing a participant for it.
                #
                # Every remaining one says the same shape of thing: "the act's principal is a
                # different person of the same surname; ours is X." There is no single pair to
                # name — that is the point of the ruling — and the ten labels of this kind name
                # no participant resembling our person at all. Asking a human to choose one
                # would be asking them to invent the thing the label denies, and forcing the
                # choice mechanically is exactly the bug this whole block exists because of.
                #
                # But "no participant of this act is this person" quantifies over the act, and
                # a quantified claim is testable: the scorer satisfies it when it would graft
                # NONE of them, and violates it when it would graft any. That is a stricter
                # test than a single pair, not a weaker one. Reported as the worst offender, so
                # a violation names the mention that caused it.
                #
                # An ACCEPT cannot be handled this way. It asserts our person IS in the act,
                # which is existential and needs a specific someone; those stay unresolved.
                if lab.match or not in_act.get(lab.ref):
                    yield lab, None
                    continue
                scored = [compare(a, from_mention(m), freq) for m in in_act[lab.ref]]
                yield lab, max(scored, key=lambda m: (m.graftable, m.bits))
                continue
            mention = candidates[0]
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

    people = load_people(load_config()["roster"])
    tp = fp = tn = fn = 0
    missing = 0
    disagreements = []
    unresolved = []
    for lab, m in _scored(labels):
        if m is None:
            missing += 1
            unresolved.append((lab, m))
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
          + (f" · {missing} unresolved" if missing else ""))
    if missing:
        # Said loudly, because an unresolved label is a hole in the gold standard and the
        # figures below are computed without it — but broken down, because most of the hole
        # is not waiting on anybody. Reporting all of them as "re-record these" made the
        # backlog look like human work when the large majority resolves on the next harvest.
        # Counted directly, each from its own condition. Deriving one of them by subtracting
        # the others printed "-1" the moment act-level rejections started scoring, because a
        # category that is no longer part of `missing` cannot be recovered from it.
        held = store.acts_by_id(lab.ref.split("#", 1)[0] for lab in labels)
        absent = gone = needs_a_person = 0
        for lab, m in unresolved:
            if lab.person not in people:
                gone += 1
            elif lab.ref.split("#", 1)[0] not in held:
                absent += 1
            else:
                needs_a_person += 1
        print(f"  {missing} label(s) are not counted above:")
        if needs_a_person:
            print(f"    {needs_a_person:>3} name a held act but not which of its people. An act names six,\n"
                  "        so the ref alone does not say which. `evaluate.py refs` prints the\n"
                  "        command for each participant — this is the only part needing a person.")
        if absent:
            print(f"    {absent:>3} name an act the corpus does not hold, so there are no participants\n"
                  "        to choose between yet. These resolve themselves once it is harvested.")
        if gone:
            print(f"    {gone:>3} name a person no longer in the tree — a record retracted after the\n"
                  "        act was re-read, leaving the ruling that justified it pointing at nobody.")
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


def cmd_refs(args) -> int:
    """Every label that cannot be tied to one participant, and the command to fix it.

    An act names six people. A label written against the act id says "the ruling was about
    somebody in here", and for 45 of the first 48 labels that was all it said — so the
    scorer was handed whichever participant came first, which was usually the groom. The
    resulting figures measured the ambiguity, not the scorer.

    The fix per label is a human choosing the pid, and this prints the evidence for that
    choice: who in the act carries the surname, what role the act gives them, and the
    command to re-record it. It chooses nothing itself. Where the act names a bride AND her
    father of the same surname, both are listed and the role is what tells them apart.
    """
    labels = read_labels()
    if not labels:
        return cmd_report(args)
    if not corpus_exists():
        raise SystemExit("error nothing harvested yet — the labels cannot be resolved")

    people = load_people(load_config()["roster"])
    store.ensure(verbose=True)
    in_act = {aid: act.people for aid, act in
              store.acts_by_id(lab.ref.split("#", 1)[0] for lab in labels).items()}

    unheld, ambiguous, gone = [], [], []
    for lab in labels:
        if "#" in lab.ref:
            continue
        if lab.person not in people:
            gone.append(lab)
            continue
        parts = in_act.get(lab.ref)
        if not parts:
            unheld.append(lab)
            continue
        key = family_key(people[lab.person].get("surname"))
        same = [m for m in parts if family_key(m.surname) and family_key(m.surname) == key]
        if len(same) != 1:
            ambiguous.append((lab, parts, same))

    print(f"{len(labels)} labels · {len(ambiguous)} need a participant · "
          f"{len(unheld)} name an act not held · {len(gone)} name a person no longer in the tree\n")

    for lab, parts, same in ambiguous[: args.limit]:
        verdict = "--match" if lab.match else "--nonmatch"
        print(f"── {lab.person}  ×  {lab.ref}   ({'match' if lab.match else 'NOT a match'})")
        print(f"   {lab.why[:110]}")
        listed = same or parts
        print(f"   {len(same)} participant(s) share the surname; the act names {len(parts)}:")
        for m in listed:
            when = m.birth or (str(m.birth_year) if m.birth_year else "—")
            print(f"     {m.pid:<28} {m.role:<22} {m.name[:32]:<34} b. {when}")
            print(f'       uv run tools/evaluate.py label {lab.person} {lab.ref}#{m.pid} '
                  f'{verdict} --basis {lab.basis} --why "…"')
        print()

    if unheld:
        print(f"{len(unheld)} label(s) name an act the corpus does not hold. Not an error — the")
        print("  act was read in a browser, or the harvest has not reached it. They will")
        print("  resolve on their own once it is held:")
        for lab in unheld[:8]:
            print(f"    {lab.person:<22} {lab.ref}")
    return 0


def cmd_floor(args) -> int:
    """Where the verifier need never look — measured, not guessed.

    `sweep` asks what it would cost to move the GRAFT threshold up. This asks the opposite
    and cheaper question: how far DOWN the scale can a candidate be discarded without ever
    having discarded a true match. Everything below that line is work the verifier is
    currently doing for nothing — and verifier time is the expensive resource in this
    project, because it is the one that is not a computer.

    The floor is set by the weakest confirmed match in the labels, and nothing else. Not
    by a percentile, not by a ratio of true to false: by the single true pair that scored
    lowest, because the cost of being wrong here is a missed link, and this project's
    standing choice is that a missed link is the only acceptable error.

    That makes the floor honest about small evidence, too. With a few dozen labels the
    weakest true match is a weak estimate, so the margin below it matters, and the
    recommendation stays conservative until there are enough labels to move it.
    """
    labels = read_labels()
    if not labels:
        return cmd_report(args)
    if not corpus_exists():
        raise SystemExit("error nothing harvested yet — the labels cannot be re-scored")

    scored = [(lab, m) for lab, m in _scored(labels) if m is not None]
    matches = [m for lab, m in scored if lab.match]
    refuted = [m for lab, m in scored if not lab.match]
    if not matches:
        print("No confirmed matches among the labels yet, so nothing sets a floor.")
        print("A floor drawn from rejections alone would be a guess with arithmetic on top.")
        return 0

    weakest = min(m.distinguishing for m in matches)
    print(f"{len(scored)} labelled pairs · {len(matches)} confirmed · {len(refuted)} refuted\n")
    print(f"  The weakest CONFIRMED match scores {weakest:.1f} distinguishing bits.")
    print(f"  ({', '.join(f'{m.distinguishing:.1f}' for m in sorted(matches, key=lambda m: m.distinguishing)[:8])}"
          f"{' …' if len(matches) > 8 else ''})")

    # A margin below the weakest true pair, because the weakest true pair is an estimate
    # from a few dozen labels and not a law. Half of it, floored at nothing — with a
    # weakest match this low there may be no safe floor at all, and saying so is the
    # answer.
    safe = weakest / 2
    below = [m for m in refuted if m.distinguishing < safe]
    lost = [m for m in matches if m.distinguishing < safe]
    print(f"\n  Proposed auto-reject floor: {safe:.1f} bits — half the weakest true match, as a margin.")
    print(f"    refuted pairs it would discard unseen   {len(below)} of {len(refuted)}")
    print(f"    confirmed matches it would lose         {len(lost)}   ← must be 0")
    if lost:
        print("\n  It is not 0, so there is no safe floor at this label count. Keep showing")
        print("  everything, and label more rulings — especially rejections.")
        return 0

    print("\n  What that suppresses in the live candidate stream, not just in the labels:")
    people = load_people(load_config()["roster"])
    children = children_index(people)
    freq = store.frequencies()
    seen = suppressed = 0
    for pid in sorted(people)[: args.people]:
        c = from_person(people[pid], people, children)
        for other in store.candidates_for(c):
            m = compare(c, other, freq)
            if m.conflict:
                continue
            seen += 1
            if m.distinguishing < safe:
                suppressed += 1
    if seen:
        print(f"    {suppressed} of {seen} unvetoed candidates across {min(args.people, len(people))} people"
              f" — {suppressed / seen:.0%} the verifier would never have to read.")
    print("\n  This is a measurement, not a change. Nothing is suppressed until the floor is")
    print("  written into the tools, and that is a judgement about this project's purpose.")
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

    p = sub.add_parser("refs", help="labels that name an act but not which of its six people")
    p.add_argument("--limit", type=int, default=25)
    p.set_defaults(fn=cmd_refs)

    p = sub.add_parser("floor", help="below which bits no true match has ever been seen")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--people", type=int, default=60, help="how many people to sample for the live figure")
    p.set_defaults(fn=cmd_floor)

    args = parser.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
