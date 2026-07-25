"""Three questions the tree can answer about itself once it is treated as a graph.

WHICH ACT TO FETCH. An act is not a fact about one person, it is a hyperedge over six:
a marriage names both spouses and all four parents. So "which frontier is most
valuable" is the wrong question — the right one is "which ACT touches the most open
frontiers", which is a maximum-coverage problem and is solved greedily. Picking the
shallowest frontier and fetching whatever answers it leaves the other five people in
the same document unread.

WHICH FAMILIES ARE NOT YET CONNECTED. Objective 3 — connect all Bundervoets — is a
connected-components problem plus link prediction between the components. The tree
knows its own components; the corpus holds the clusters that are not in it yet. What
has never existed is a queue ranking the PAIRS by how joinable they look.

WHERE THE TREE FOLDS BACK ON ITSELF. In a coastal Flemish commune the same families
recur, so an ancestor reached by two different paths is expected rather than alarming —
but it has to be visible, because it means the ancestor count does not double every
generation, and the architecture is sized against an assumption that it does.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field

from .corpus import Act, corpus_exists, load_corpus, normalise_key
from .match import build_index, candidates_for, compare, from_mention, from_person
from .people import family_key
from .frontier import children_index, generations

# ---------- which act to fetch ----------


@dataclass
class ActCoverage:
    act: Act
    resolves: list[tuple[str, str]] = field(default_factory=list)   # (person id, how)
    mentions: list[tuple[str, str]] = field(default_factory=list)   # (person id, explanation)

    @property
    def weight(self) -> int:
        return len(self.resolves) * 3 + len(self.mentions)


def act_coverage(people: dict, frontier_ids: set[str]) -> list[ActCoverage]:
    """Every held act that touches an open frontier, and what it would give.

    "Resolves" means the act names that person AND names a parent of them — the act
    would answer the frontier, not merely mention it. Everything else is a mention:
    still worth reading, worth much less.
    """
    if not corpus_exists():
        return []
    children = children_index(people)
    targets = [from_person(people[pid], people, children) for pid in frontier_ids if pid in people]
    if not targets:
        return []
    index = build_index(targets)

    out: list[ActCoverage] = []
    for act in load_corpus():
        cov = ActCoverage(act=act)
        # A parent edge exists for this mention, so the act states their parentage.
        has_parent = {e["child"] for e in act.edges if e["type"] in ("father", "mother")}
        for m in act.people:
            c = from_mention(m)
            for target in candidates_for(c, index):
                match = compare(target, c)
                # "rejected" is not a weak match, it is a vetoed one — a stated
                # conflict. Letting it through here listed contradicted people as
                # though the act would resolve them.
                if match.band in ("noise", "rejected"):
                    continue
                if m.pid in has_parent:
                    cov.resolves.append((target.ref, match.explain()))
                else:
                    cov.mentions.append((target.ref, match.explain()))
        if cov.resolves or cov.mentions:
            out.append(cov)
    return out


def greedy_cover(coverages: list[ActCoverage]) -> list[tuple[ActCoverage, list[str]]]:
    """Order the acts so each one is chosen for what it adds, not what it repeats.

    Straight maximum coverage: take the act touching the most still-uncovered
    frontiers, mark them covered, repeat. Reading the list top to bottom is the
    shortest route to touching every frontier the corpus can reach.
    """
    remaining = {a for cov in coverages for a, _ in cov.resolves + cov.mentions}
    pool = list(coverages)
    ordered: list[tuple[ActCoverage, list[str]]] = []
    while pool and remaining:
        def gain(cov):
            return len({a for a, _ in cov.resolves if a in remaining}) * 3 + \
                   len({a for a, _ in cov.mentions if a in remaining})

        best = max(pool, key=gain)
        if gain(best) == 0:
            break
        new = sorted({a for a, _ in best.resolves + best.mentions} & remaining)
        ordered.append((best, new))
        remaining -= set(new)
        pool.remove(best)
    return ordered


# ---------- which families are not yet connected ----------


def tree_components(people: dict) -> list[list[str]]:
    """Connected components over parents, spouses and children together.

    Marriage counts as a connection, which is how a spouse with no children still
    belongs to the family they married into.
    """
    children = children_index(people)
    adjacency: dict[str, set[str]] = defaultdict(set)
    for pid, p in people.items():
        adjacency[pid]
        for parent in (p.get("father"), p.get("mother")):
            if parent in people:
                adjacency[pid].add(parent)
                adjacency[parent].add(pid)
        for s in p.get("spouses") or []:
            if s.get("id") in people:
                adjacency[pid].add(s["id"])
                adjacency[s["id"]].add(pid)
        for c in children.get(pid, []):
            adjacency[pid].add(c)

    seen: set[str] = set()
    out: list[list[str]] = []
    for pid in people:
        if pid in seen:
            continue
        stack, group = [pid], []
        seen.add(pid)
        while stack:
            cur = stack.pop()
            group.append(cur)
            for n in adjacency[cur]:
                if n not in seen:
                    seen.add(n)
                    stack.append(n)
        out.append(sorted(group))
    return sorted(out, key=len, reverse=True)


# ---------- objective 2: the sibships nobody was looking for ----------


@dataclass
class MissingChild:
    """A child an act names, whose parents are both already in the tree.

    This is the whole of objective 2, made computable. Until now the frontier queue only
    knew one shape of question — "who were this person's parents" — so the tree could
    only ever grow *upwards*. A couple with one recorded child and eight unrecorded ones
    produced no frontier at all, because nothing was missing from any record that
    existed.

    Building downwards is not a nicety. It is how "all blood relatives" is reached, and
    it is the only shape of growth that scales to a commune: one couple identified yields
    a whole sibship, each of whom yields a marriage, each of which names two more
    families.
    """

    father: str
    mother: str
    name: str
    birth: str | None
    place: str | None
    act_url: str
    act_label: str
    # An existing record this child resolves to, if any. The two cases are different
    # work and must not be confused: `None` means a person to ADD, an id means a person
    # already held whose parent links are missing. Offering the second as the first is
    # how a tree acquires two copies of one person, which does not look broken — it
    # looks like two people, and the branch quietly splits.
    existing: str | None = None
    mention: object = None

    @property
    def kind(self) -> str:
        return "link" if self.existing else "add"


def missing_children(people: dict, children: dict | None = None) -> list[MissingChild]:
    """Children the corpus names for couples the tree already holds.

    The identification is deliberately strict: BOTH parents must match tree people by the
    ordinary scoring rules, and those two must already be recorded as a couple. A single
    parent agreeing is the classic way to acquire another family's children, so it is not
    enough — and the couple requirement means the shared-child invariant in the data model
    is doing double duty as a guard here.

    Nothing returned is a fact. Each is a named, checkable lead: an act, a child's name,
    and the parents it attaches them to.
    """
    if not corpus_exists():
        return []
    children = children if children is not None else children_index(people)
    index = build_index([from_person(p, people, children) for p in people.values()])

    # Which pairs each recorded person already hangs off, so a child the tree has is not
    # offered as one it lacks.
    recorded: dict[str, tuple[str | None, str | None]] = {
        pid: (p.get("father"), p.get("mother")) for pid, p in people.items()
    }

    def identify(mention) -> str | None:
        """Which tree person this mention is, or None. The project's own floor applies."""
        best = None
        for other in candidates_for(from_mention(mention), index):
            m = compare(from_mention(mention), other)
            if m.graftable and (best is None or m.bits > best[1]):
                best = (other.person_id, m.bits)
        return best[0] if best else None

    out: list[MissingChild] = []
    for act in load_corpus():
        by_pid = {p.pid: p for p in act.people}
        # Group the act's parent edges by the child they attach to, so a birth act with a
        # father and a mother yields one candidate couple rather than two halves.
        parents: dict[str, dict[str, object]] = {}
        for e in act.edges:
            if e["type"] in ("father", "mother") and e["parent"] in by_pid:
                parents.setdefault(e["child"], {})[e["type"]] = by_pid[e["parent"]]
        for child_pid, pair in parents.items():
            child = by_pid.get(child_pid)
            if not child or "father" not in pair or "mother" not in pair:
                continue
            father_id, mother_id = identify(pair["father"]), identify(pair["mother"])
            if not father_id or not mother_id:
                continue
            # The couple must already be recorded as one. The data model guarantees that
            # a shared child obliges a marriage entry, so this reads the invariant back.
            spouses = {s.get("id") for s in people[father_id].get("spouses") or []}
            if mother_id not in spouses:
                continue
            # Resolve the child through the same matcher as the parents, never by
            # comparing name strings: this tree records her as "Léonie (Philomena
            # Leonia) Paelinck" and the act calls her "Philomena Leonia Paelinck", so a
            # string comparison reported an existing person as a missing one.
            existing = identify(child)
            if existing and recorded.get(existing) == (father_id, mother_id):
                continue
            out.append(MissingChild(
                father=father_id, mother=mother_id, name=child.name,
                birth=child.birth or (str(act.year) if act.year else None),
                place=child.birth_place or act.place,
                act_url=act.url, act_label=act.label, existing=existing, mention=child,
            ))
    return out


@dataclass
class Cluster:
    """A family of one surname in one commune that the corpus knows about."""

    surname: str
    place: str
    mentions: int
    span: tuple[int | None, int | None]
    acts: list[Act]
    best_link: tuple[str, str] | None   # (person id, explanation) — the join candidate
    best_bits: float


def surname_clusters(people: dict, surname: str) -> list[Cluster]:
    """The corpus's view of one surname, grouped by commune, each cluster scored for how
    joinable it looks to the tree.

    A cluster with a strong link is where the tree should grow. A cluster with none is a
    separate root: expected and legitimate under objective 3, and exactly the thing that
    was previously invisible.
    """
    if not corpus_exists():
        return []
    key = family_key(surname)
    children = children_index(people)
    ours = [from_person(p, people, children) for p in people.values() if family_key(p.get("surname")) == key]
    index = build_index(ours) if ours else {}

    by_place: dict[str, list] = defaultdict(list)
    for act in load_corpus():
        for m in act.people:
            if family_key(m.surname) == key:
                by_place[normalise_key(act.place) or "onbekend"].append((act, m))

    out: list[Cluster] = []
    for place_key, rows in by_place.items():
        years = [a.year for a, _ in rows if a.year]
        best, best_bits = None, 0.0
        for _, m in rows:
            c = from_mention(m)
            for target in candidates_for(c, index):
                match = compare(target, c)
                if match.bits > best_bits:
                    best, best_bits = (target.ref, match.explain()), match.bits
        out.append(Cluster(
            surname=surname,
            place=rows[0][0].place or "onbekend",
            mentions=len(rows),
            span=(min(years) if years else None, max(years) if years else None),
            acts=sorted({a.id: a for a, _ in rows}.values(), key=lambda a: (a.year or 0)),
            best_link=best,
            best_bits=best_bits,
        ))
    return sorted(out, key=lambda c: (-c.best_bits, -c.mentions))


# ---------- where the tree folds back on itself ----------


@dataclass
class Collapse:
    generation: int
    distinct: int
    theoretical: int


def ancestors_of(people: dict, pid: str) -> set[str]:
    seen: set[str] = set()
    stack = [pid]
    while stack:
        cur = stack.pop()
        for parent in (people[cur].get("father"), people[cur].get("mother")):
            if parent in people and parent not in seen:
                seen.add(parent)
                stack.append(parent)
    return seen


def pedigree_collapse(people: dict, meta: dict):
    """How far the ancestor count falls short of doubling, and which couples are the
    reason.

    Two numbers matter. The per-generation shortfall says how much the 2^g projection
    overstates the tree — the assumption the storage design is sized against. The
    shared-ancestor couples are the individual causes, and each one is also a research
    signal: a marriage between cousins means the two lines were in the same parish, and
    a proposed link that would create one deserves a second look before it is grafted.
    """
    depth = generations(people, meta)
    per_generation: dict[int, set[str]] = defaultdict(set)
    for pid, d in depth.items():
        if d > 0:
            per_generation[d].add(pid)
    ladder = [Collapse(g, len(ids), 2 ** g) for g, ids in sorted(per_generation.items())]

    # A couple whose lines meet above them. Computed from the couples the tree already
    # states, so it reports what is recorded rather than looking for something to find.
    couples: set[tuple[str, str]] = set()
    for pid, p in people.items():
        if p.get("father") in people and p.get("mother") in people:
            couples.add((p["father"], p["mother"]))
        for s in p.get("spouses") or []:
            if s.get("id") in people:
                couples.add(tuple(sorted((pid, s["id"]))))

    consanguine = []
    for a, b in sorted(couples):
        shared = ancestors_of(people, a) & ancestors_of(people, b)
        if shared:
            consanguine.append((a, b, sorted(shared)))

    # Anyone reached from a root by more than one line, which is the same fact seen
    # from below.
    children = children_index(people)
    multi = []
    roots = [r for r in meta.get("roots", []) if r in people]
    for pid in people:
        paths = 0
        for root in roots:
            if pid in ancestors_of(people, root):
                paths += sum(1 for c in children.get(pid, []) if c in ancestors_of(people, root) or c == root)
        if paths > 1:
            multi.append((pid, paths))

    return ladder, consanguine, Counter(dict(multi))
