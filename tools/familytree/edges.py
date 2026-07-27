"""How every link in a record is written out in full — the rule, in one place.

`tools/edges.py` is the command; this is what it and the validator both read, so "what the
records should say" cannot be answered two different ways by the thing that writes them and
the thing that checks them.

WHY A DERIVED RELATION IS MATERIALISED AT ALL. Writing siblings into the records is the
duplication the data model spends its whole design avoiding — until it is GENERATED and
CHECKED, at which point it stops being a second source of truth and becomes a projection of
the first, exactly like `dist/bundle.js`. The validator fails when a record disagrees with
what `planned` would write, so a triangle cannot drift: correct a parent link and the
sibling edges that rested on it go stale loudly, on the next build.

WHAT IS NEVER TOUCHED. Anything stated by hand wins — a `confidence` already on a link, a
`source`, a `note`, and any sibling entry naming somebody the parent links cannot reach.
Those are findings; this only fills in what it can derive, so running it can never overwrite
research with arithmetic.
"""

from __future__ import annotations

from . import frontmatter
from .people import FIELDS, PEOPLE_DIR, children_index, parent_id

# Weakest wins, and this is the order of "weak". It is the GEDCOM QUAY order the exporter
# already uses, so the two cannot disagree about which of two codes is the lesser.
RANK = {"asm": 0, "fam": 1, "sup": 2, "doc": 3}


def weaker(*codes: str | None) -> str | None:
    """An edge is no better evidenced than its weaker end.

    The one rule this tool applies, and it is conservative on purpose. A link between a
    documented person and one known only from family testimony is not documented — the
    weaker end is what a reader would have to accept to accept the join. Symmetric, so a
    marriage written on two records gets the same answer from both, which is what the
    one-marriage-one-set-of-facts invariant requires.
    """
    known = [c for c in codes if c in RANK]
    return min(known, key=lambda c: RANK[c]) if known else None


def parent_edge(people: dict, pid: str, role: str) -> str | None:
    other = parent_id(people[pid], role)
    return weaker(people[pid].get("confidence"), (people.get(other) or {}).get("confidence"))


def sibship_confidence(people: dict, a: str, b: str, edges: dict) -> str | None:
    """How well it is known that these two are siblings.

    NOT the weaker of the two people — that would grade the wrong thing. They are siblings
    *because* each has a link to the same parent, so the sibship is only as good as the
    weaker of those two links. Where they share both parents there are two routes to the
    same conclusion and the better one is taken, which is the point of having two.
    """
    best = None
    for role_a in ("father", "mother"):
        pa = parent_id(people[a], role_a)
        if not pa:
            continue
        for role_b in ("father", "mother"):
            if parent_id(people[b], role_b) != pa:
                continue
            route = weaker(edges[a][role_a], edges[b][role_b])
            if route and (best is None or RANK[route] > RANK[best]):
                best = route
    return best


def planned(people: dict) -> dict[str, dict]:
    """What every record's links should say. Pure — it writes nothing."""
    children = children_index(people)
    edges = {
        pid: {role: (p[role].get("confidence") or parent_edge(people, pid, role))
              for role in ("father", "mother") if parent_id(p, role)}
        for pid, p in people.items()
    }

    out: dict[str, dict] = {}
    for pid, p in sorted(people.items()):
        fields: dict = {}
        for role in ("father", "mother"):
            if parent_id(p, role):
                fields[role] = {**p[role], "confidence": edges[pid][role]}

        # Derived first, in birth order so the list reads like the sibship does on the page.
        stated = {s["id"]: s for s in (p.get("siblings") or []) if isinstance(s, dict) and s.get("id")}
        derived: list[dict] = []
        seen = {pid}
        for role in ("father", "mother"):
            for kid in children.get(parent_id(p, role) or "", []):
                if kid in seen:
                    continue
                seen.add(kid)
                # A hand-written entry for the same person keeps everything it says; only a
                # confidence it never stated is filled in.
                held = stated.get(kid, {})
                derived.append({**held, "id": kid,
                                "confidence": held.get("confidence")
                                or sibship_confidence(people, pid, kid, edges)})
        # Then the ones no parent link can reach — findings, left exactly as written.
        derived += [s for sid, s in stated.items() if sid not in seen]
        if derived:
            fields["siblings"] = derived

        spouses = []
        for s in p.get("spouses") or []:
            other = (people.get(s.get("id")) or {}).get("confidence") if s.get("id") else None
            spouses.append({**s, "confidence": s.get("confidence")
                            or weaker(p.get("confidence"), other)})
        if spouses:
            fields["spouses"] = spouses
        out[pid] = fields
    return out


def rewrite(pid: str, fields: dict) -> str | None:
    """The record with its link fields replaced. None when nothing would change.

    Read and written through the same parser the whole project uses, so field order, the
    prose body and the quoting rules are whatever `frontmatter` says they are rather than
    something this tool invents. The round-trip is checked before anything is written: a
    normaliser that silently drops a field would be the worst possible bug here, because it
    would look like a tidy-up.
    """
    path = PEOPLE_DIR / f"{pid}.md"
    original = path.read_text(encoding="utf-8")
    data, body = frontmatter.parse(original, f"{pid}.md")
    for key in ("father", "mother", "siblings", "spouses"):
        data.pop(key, None)
    data.update(fields)
    text = frontmatter.stringify(data, body, FIELDS)

    back, back_body = frontmatter.parse(text, f"{pid}.md")
    if back != data or back_body.strip() != body.strip():
        raise SystemExit(f"error {pid}.md would not survive the round trip — refusing to write")
    return None if text == original else text
