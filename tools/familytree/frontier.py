"""What to work on next — ranked by what it is worth, how likely it is to give way,
and what it will cost to try.

The old ranking was breadth-first by generation: ancestors before relatives, then
closest to the root. That encodes objective 1 correctly and nothing else, so it put
René Janssens — a surname so common the log itself calls him unsearchable — two rows
above people who could be resolved in an afternoon. Depth is a statement about VALUE.
It says nothing about probability or cost, and a queue that ignores those spends its
passes on the walls that will not move.

So the score is the one investigative genealogy already uses: expected value over
expected work.

    value   how much of the tree is blocked here. For a direct ancestor that is their
            share of the root's ancestry, which halves every generation: a wall at
            generation 3 holds back an eighth of everything above, a wall at generation
            12 holds back one thin line. For a collateral relative it is how many
            descendants they already have in the tree, which is what objective 2 is
            about. The two are not compared — see the tiering below.
    P       whether it can be resolved at all: are there records reachable for this
            surname and place, and is there enough rarity to tell the right one from
            the 191 wrong ones. Counted from the corpus, not guessed.
    cost    the cheapest untried route. A frontier the harvest already holds candidates
            for costs almost nothing; one that needs a login costs more; one behind a
            counter in Oostende costs most. Rises with every search already spent,
            because the tenth try is worth less than the first.

P falls as properly-searched misses accumulate — but never for a `blocked`, because
nothing was read, so nothing was learned.

Direct ancestors are ranked ABOVE collateral relatives as a tier, not by score, because
the charter says objective 1 outranks objective 2 when they conflict and a weight would
let a cheap collateral outbid a hard direct line. Inside each tier the score decides.

The depth term is deliberately gentler than the true 2^-g: a strict halving makes
generation 3 five hundred times generation 12, and then nothing else can ever surface
however cheap and certain it is. 2^(-g/3) keeps shallow work firmly in front while
still letting a rare surname with an indexed act win from further back.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from . import store
from .corpus import corpus_exists, corpus_mentions, frequencies, surname_coverage
from .match import build_index, candidates_for, from_mention, from_person, surname_weight
from .people import DAY, children_index, load_config, load_people, point_year
from .sources import ACCESS_COST, load_log, load_sources


def generations(people: dict, meta: dict) -> dict[str, int]:
    """Generations above the root, by the shortest line."""
    roots = [r for r in (meta.get("roots") or [meta.get("root")]) if r in people]
    depth = {r: 0 for r in roots}
    queue = list(roots)
    while queue:
        pid = queue.pop(0)
        for parent in (people[pid].get("father"), people[pid].get("mother")):
            if parent and parent in people and parent not in depth:
                depth[parent] = depth[pid] + 1
                queue.append(parent)
    return depth


def descendant_counts(people: dict) -> dict[str, int]:
    """Everyone in the tree who descends from each person.

    This is what a frontier is worth: resolving someone's parents gives an ancestry to
    every one of them.
    """
    children = children_index(people)
    counts: dict[str, int] = {}
    for pid in people:
        seen: set[str] = set()
        stack = list(children.get(pid, []))
        while stack:
            c = stack.pop()
            if c in seen:
                continue
            seen.add(c)
            stack.extend(children.get(c, []))
        counts[pid] = len(seen)
    return counts


def discriminability(c, freq) -> float:
    """How much evidence exists to tell this person apart from everyone with the same
    name. A rare surname plus a day-level date plus a commune is a searchable person;
    "Janssens, somewhere in Brabant, about 1930" is not, and the queue has to be able to
    say so without a human reading the note."""
    name = surname_weight(c.surname, freq).bits if c.surname else 0.0
    # The date is worth what it PINS DOWN, so a bound or a range is not a day. Tested with
    # `DAY.match` and not `len(...) == 10`, because "1920..1929" is exactly ten characters:
    # the third place this project made that mistake. Here it scored a person known only to
    # a decade as though a day-level date had been read, which raises P(resolvable) and
    # promotes them up the queue — a frontier ranked as searchable on evidence it lacks.
    if c.birth_date and DAY.match(c.birth_date):
        date = 8.0
    elif point_year(c.birth_date) if c.birth_date else c.birth_year:
        date = 4.0
    else:
        date = 0.0
    place = 4.0 if c.places else 0.0
    return min(1.0, (name + date + place) / 18.0)


@dataclass
class Frontier:
    id: str
    name: str
    surname: str | None
    depth: float
    is_ancestor: bool
    reach: int
    why: str
    searched: int
    misses: int
    blocked: int
    untried_sites: int
    candidates: int | None
    surname_bits: float
    value: float
    probability: float
    cost: float
    route: str
    score: float


def frontier_rows(people: dict | None = None) -> list[Frontier]:
    config = load_config()
    people = people if people is not None else load_people(config["roster"])
    meta = config["meta"]
    sites, _ = load_sources()
    log = load_log()
    depth = generations(people, meta)
    reach_of = descendant_counts(people)
    freq = frequencies()
    children = children_index(people)

    # The corpus, indexed once for all frontiers rather than scanned per person — and
    # from the persistent index when there is a current one, in which case even that is
    # not needed, because all the queue wants from the corpus is a count per frontier.
    #
    # The in-memory fallback stays because it must: an index that does not exist yet, or
    # one the harvest has moved past, has to degrade to being slow rather than to being
    # wrong. Building it here is not this function's business — the reports call
    # `store.ensure()` before they start.
    indexed = store.is_current()
    index = None if indexed or not corpus_exists() else build_index(
        from_mention(m) for m in corpus_mentions())

    rows: list[Frontier] = []
    for pid, p in people.items():
        missing_parents = not p.get("father") and not p.get("mother")
        flagged = "FRONTIER" in (p.get("note") or "")
        if not missing_parents and not flagged:
            continue

        c = from_person(p, people, children)
        tried = [e for e in log if e.get("person") == pid]
        misses = sum(1 for e in tried if e.get("result") == "miss")
        blocked = [e for e in tried if e.get("result") == "blocked"]
        untried_sites = [s for s in sites if not any(e.get("site") == s["id"] for e in tried)]
        is_ancestor = pid in depth and depth[pid] > 0
        reach = reach_of.get(pid, 0)

        if indexed:
            candidates = store.candidate_count(c)
        else:
            candidates = len(candidates_for(c, index)) if index is not None else None
        # Three states, not two, and the middle one is the whole point. Never harvested
        # is UNKNOWN and cheap to resolve. Harvested completely and empty is EVIDENCE of
        # absence. Harvested part-way and empty is neither — it is the corpus form of
        # `blocked`, and treating it as evidence sank frontiers whose acts are simply in
        # the part nobody fetched. Coverage weights between the prior and the finding.
        coverage = surname_coverage(p["surname"]) if p.get("surname") else None
        if candidates is None or coverage is None:
            presence = 0.5
        else:
            observed = max(0.05, 1 - math.exp(-candidates / 6))
            presence = coverage * observed + (1 - coverage) * 0.5
        probability = max(0.02, presence * discriminability(c, freq) * (0.8 ** misses))

        # A direct ancestor is worth their share of the blocked ancestry; a collateral
        # relative is worth the family that already hangs off them. Never the same
        # number for both — they are ranked in separate tiers.
        value = 2 ** (-depth[pid] / 3) if is_ancestor else 1 + math.log2(1 + reach) / 4

        # The cheapest thing left to try, and what it costs.
        if candidates:
            # "60+" when the count was capped — see store.CANDIDATE_CAP. Saying sixty when
            # the truth is five hundred would be a number nobody could reconcile with
            # link.py's own output.
            how_many = f"{candidates}+" if indexed and candidates >= store.CANDIDATE_CAP else str(candidates)
            route, cost = f"link — {how_many} candidates already held", 0.5
        elif p.get("surname") and coverage is None:
            route, cost = f'harvest surname "{p["surname"]}"', 1.0
        elif coverage is not None and coverage < 0.95:
            # Cheaper than any browser session, and it is the reason there are no
            # candidates — say so rather than sending someone to a login wall.
            route = f'finish the harvest of "{p["surname"]}" — only {coverage:.0%} held'
            cost = 1.0
        elif blocked:
            route, cost = f"retry {blocked[0]['site']} — blocked, never read", 2.0
        elif untried_sites:
            cheapest = min(untried_sites, key=lambda s: ACCESS_COST.get(s.get("access"), 4))
            route = f"search {cheapest['id']} ({cheapest.get('access')})"
            cost = ACCESS_COST.get(cheapest.get("access"), 4)
        else:
            route, cost = "every registered venue tried — needs a new source", 10.0
        cost *= 1 + 0.25 * len(tried)

        rows.append(Frontier(
            id=pid,
            name=p["name"],
            surname=p.get("surname"),
            depth=depth.get(pid, math.inf),
            is_ancestor=is_ancestor,
            reach=reach,
            why="parents unknown" if missing_parents else "note flags a frontier",
            searched=len(tried),
            misses=misses,
            blocked=len(blocked),
            untried_sites=len(untried_sites),
            candidates=candidates,
            surname_bits=surname_weight(p["surname"], freq).bits if p.get("surname") else 0.0,
            value=value,
            probability=probability,
            cost=cost,
            route=route,
            score=value * probability / cost,
        ))

    # The tier first — objective 1 before objective 2 — then the score inside it.
    rows.sort(key=lambda r: (not r.is_ancestor, -r.score, r.depth))
    return rows
