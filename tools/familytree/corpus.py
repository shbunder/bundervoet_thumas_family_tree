"""The corpus: harvested acts, read as events rather than as people.

This is the inversion the whole optimisation rests on. A search is person-indexed —
one query, one person, and the other five people the act names are discarded. A record
is event-indexed: a marriage act is a single fact about six people at once, four of
them parents. Reading the harvest this way means one act answers every frontier it
touches, not the one it was fetched for.

Everything here is derived from research/harvest/ and nothing is written back. The
corpus makes no claims: it normalises what an archive published, and the parent and
couple edges it emits are what the ACT asserts, never what this project believes.
Turning one into the other is a decision, and decisions live in the person files under
the rules in CLAUDE.md.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from functools import lru_cache

from .people import ROOT, year_of

HARVEST = ROOT / "research" / "harvest"
ACTS_DIR = HARVEST / "acts"
MENTIONS_DIR = HARVEST / "mentions"
MANIFEST = HARVEST / "manifest.json"

# ---------- roles ----------
# Archive role labels are Dutch and vary between the institutions that indexed them,
# so they are matched by pattern rather than by an exhaustive list — a role this does
# not recognise becomes an unattached participant, which is visible, and never a
# silently wrong edge.
PRINCIPAL = re.compile(r"^(kind|gedoopte|overledene|bruidegom|bruid|geregistreerde|hoofdpersoon)$")
FATHER_OF = re.compile(r"^vader(\s+van\s+de\s+(bruid|bruidegom|overledene|kind))?$")
MOTHER_OF = re.compile(r"^moeder(\s+van\s+de\s+(bruid|bruidegom|overledene|kind))?$")
SPOUSE_ROLE = re.compile(r"^(partner|echtgenoot|echtgenote|weduwe|weduwnaar)")
# The archives publish anything outside their fixed vocabulary with an "other:" prefix,
# and three of those carry kinship the fixed roles do not.
#
# A grandparent is stated outright in 353 of the mentions held here — a two-generation
# edge in a single act, which is the most expensive thing there is to establish by
# search. It does not say WHICH parent's parent, so the edge is deliberately sideless.
#
# A previous partner is what distinguishes a remarriage from a second person of the same
# name. Losing it is how a widow becomes twins.
GRANDPARENT_OF = re.compile(r"^other:grootouder(\s+(van\s+de\s+)?(bruid|bruidegom|overledene|kind))?$")
FORMER_PARTNER_OF = re.compile(r"^other:(vorige partner|eerdere relatie|weduwe van|weduwnaar van)")
# Witnesses are 27% of every person-mention held, and until now none of them was read.
# They are not kin by the act's word — but in a Flemish parish or commune they are
# overwhelmingly kin in fact, and, crucially, WHO recurs across a family's acts is
# evidence that no name comparison can supply. The corpus records that they witnessed;
# what that is worth is decided in match.py, by how rare the witness is.
WITNESS = re.compile(r"^getuige")
# Explicitly not kin and explicitly not evidence: the registrar appears in every act in
# the commune. Naming them here keeps them out of the witness signal by intent rather
# than by a frequency cut-off that might one day be tuned past them.
OFFICIAL = re.compile(r"^other:(ambtenaar|beambte)")
_ATTACHES = re.compile(r"(?:van\s+de\s+)?(bruidegom|bruid|overledene|kind)\b")


# Memoised for the same reason as `family_key`, and more urgently: a profile of
# `research.py acts` counted 21,176,327 calls to this against 63,018 distinct inputs.
# It is pure — a string in, a string out, no state — so the cache cannot go stale.
@lru_cache(maxsize=None)
def normalise_key(s: str | None) -> str:
    return re.sub(r"[^a-z]", "", unicodedata.normalize("NFD", (s or "").lower()))


def _as_list(v):
    """Single-element lists arrive as bare objects, so everything is coerced to a list
    before it is read. Getting this wrong loses the only participant in an act."""
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def unwrap_annotated(v):
    """Strip the XML-attribute wrapper from every value in a record, once, at the door.

    A2A is XML rendered as JSON, so any element carrying an attribute arrives as an object
    instead of a scalar: Lommel publishes a place as
    `{"@TranscriptionRemark": "Lommel-Centrum", "$": "Lommel"}` where every other archive
    publishes `"Lommel"`. Downstream code then finds a dict where it expected text and dies
    on `.lower()`.

    This was first patched at the field that broke (EventPlace), and the patch was described
    as covering every point a scalar is read. It did not: a person's BirthPlace, Residence,
    Profession and Age can each carry the same wrapper, and the crash simply moved. Guarding
    read sites is the wrong shape of fix — there is no way to know the list is complete, and
    every new field is another chance to miss one.

    So the record is normalised whole before anything reads it. Any dict with a "$" key
    collapses to that value; everything else is walked. After this, no downstream code needs
    to know the convention exists."""
    if isinstance(v, dict):
        if "$" in v:
            return unwrap_annotated(v["$"])
        return {k: unwrap_annotated(x) for k, x in v.items()}
    if isinstance(v, list):
        return [unwrap_annotated(x) for x in v]
    return v


def _api_date(d) -> str | None:
    """Into the project's date grammar — never into anything looser. A record with a
    year and no month becomes "1902", not "1902-00", because the grammar has no syntax
    for a guess and this is exactly where one would get invented."""
    if not d:
        return None

    # These fields are not reliably numeric. Archives put "ca" in a year they are
    # unsure of, and leave dashes, question marks and empty strings in a month or day
    # they could not read. int() on any of those took the whole validator down mid-run,
    # so a part that will not parse is DROPPED rather than guessed: a record with an
    # unreadable day becomes "1902-08", and one with an unreadable year becomes nothing
    # at all. The grammar has no syntax for a guess and this is exactly where one would
    # get invented.
    def num(v):
        try:
            return int(str(v).strip())
        except (TypeError, ValueError):
            return None

    year = num(d.get("Year"))
    if not year:
        return None
    year = f"{year:04d}"
    mo, da = num(d.get("Month")), num(d.get("Day"))
    if mo and not 1 <= mo <= 12:
        mo = None
    if da and not 1 <= da <= 31:
        da = None
    if mo and da:
        return f"{year}-{mo:02d}-{da:02d}"
    if mo:
        return f"{year}-{mo:02d}"
    return year


@dataclass
class Mention:
    """One person as one act names them. Never a person — a person is a record in
    data/people/, and turning one of these into one is a decision."""

    pid: str
    name: str
    given: str
    surname: str
    sex: str | None = None
    role: str = "onbekend"
    birth: str | None = None
    birth_year: int | None = None
    implied_birth_year: int | None = None
    birth_place: str | None = None
    residence: str | None = None
    occupation: str | None = None
    age: int | None = None
    act: "Act | None" = None


@dataclass
class Act:
    id: str
    archive: str
    archive_org: str
    type: str
    source_type: str | None
    date: str | None
    year: int | None
    place: str | None
    act_number: str | None
    collection: str | None
    url: str
    scan: str | None
    original: str | None
    people: list[Mention] = field(default_factory=list)
    edges: list[dict] = field(default_factory=list)
    fetched: str | None = None

    @property
    def label(self) -> str:
        where = " ".join(x for x in (self.place, self.date) if x)
        return f"{self.type} {where}".strip()


# A name field that does not hold a name.
#
# Aalst writes transcription remarks into PersonNameLastName: "de vader is de aangever" —
# the father is the declarant — appears 128,958 times, which made it by a wide margin the
# commonest "surname" in a 4.3-million-mention corpus, ahead of De Smet. It is not a rare
# glitch either: 135,418 mentions across 4,205 distinct values are sentences, ages, dates or
# numbered lists sitting where a name belongs.
#
# Two rules, and both are deliberately narrow, because the cost of over-reaching is deleting
# somebody's actual name:
#
#   a standalone finite verb — a surname is a noun phrase and never contains "is", "doet"
#   or "zijnde" as a word of its own. ("Van Iseghem" is safe: its "Is" is inside a token.)
#
#   a digit — no Flemish surname contains one, and where one appears it is an age, a year or
#   a list index glued to a name ("Devriese 2", "De Smet - 71 j Aalst zonder"). Those are
#   dropped whole rather than picked apart: which token is the surname is exactly the sort of
#   thing this project may not guess at.
#
# Checked against the corpus before being applied. Everything of four words or more that
# survives is a real name — "De Wolf - Coevoet" (9,870), "Van Pottelsberghe de la Potterie",
# "de Cocquéau des Mottes", "Baron Van der Noot" — so the rule is not eating the long
# aristocratic and double-barrelled names that a word-count rule would have destroyed.
#
# The mention itself is kept. The act does record that somebody took part; it simply does not
# say who, and an absent name is the truthful representation of that.
_NOT_A_NAME = re.compile(r"\d|(?:^|\s)(?:is|was|doet|heeft|wordt|refuse|qui|zijnde)(?:\s|$)", re.I)


def real_name(value: str | None) -> str:
    """The value if it is a name, otherwise nothing. See _NOT_A_NAME."""
    v = (value or "").strip()
    return "" if not v or _NOT_A_NAME.search(v) else v


def _person_name(p: dict) -> tuple[str, str, str]:
    n = p.get("PersonName") or {}
    # Particles are published in their own field by some archives and folded into the
    # surname by others; the surname keeps whichever form the record used, because the
    # project's own rule is that `surname` is stated, not computed.
    surname = " ".join(
        x for x in (n.get("PersonNamePrefix"), n.get("PersonNamePrefixLastName"), n.get("PersonNameLastName")) if x
    ).strip()
    given = " ".join(x for x in (n.get("PersonNameFirstName"), n.get("PersonNameInitials")) if x).strip()
    # Each independently, because the archive that writes a remark into the surname also
    # writes it into the forename for a sixth of them.
    given, surname = real_name(given), real_name(surname)
    return given, surname, " ".join(x for x in (given, surname) if x)


def _normalise_person(p: dict, event_year: int | None) -> Mention:
    given, surname, name = _person_name(p)
    age_raw = (p.get("Age") or {}).get("PersonAgeYears")
    try:
        age = int(age_raw) if age_raw is not None else None
    except (TypeError, ValueError):
        age = None
    birth = _api_date(p.get("BirthDate"))
    m = Mention(
        pid=p.get("@pid", ""),
        name=name,
        given=given,
        surname=surname,
        sex={"Man": "m", "Vrouw": "f"}.get(p.get("Gender")),
        birth=birth,
        birth_year=year_of(birth),
        birth_place=(p.get("BirthPlace") or {}).get("Place"),
        residence=(p.get("Residence") or {}).get("Place"),
        occupation=p.get("Profession"),
        age=age,
    )
    # An age in an act is a birth year with error bars, and it is very often the only
    # second identifier available. Derived, marked as derived, never written as a date.
    if not m.birth_year and m.age is not None and event_year:
        m.implied_birth_year = event_year - m.age
    return m


def _attaches_to(role: str, principals: list[Mention]) -> Mention | None:
    """Which principal a "father of the bride" belongs to. An unqualified "Vader" in a
    birth or death act has only one candidate; in a marriage act it would be ambiguous,
    so it is left unattached rather than guessed."""
    m = _ATTACHES.search(role)
    if m:
        return next((p for p in principals if p.role == m[1]), None)
    return principals[0] if len(principals) == 1 else None


def _principal_event(r: dict) -> dict:
    """The event an act is ABOUT, when the record carries more than one.

    A2A allows several. Lommel publishes 1,620 marriage records holding both the wedding
    and the `Ondertrouw` — the banns, three weeks earlier — as two events with two dates
    for one union. `Act` models a single event, so this has to choose, and the choice is
    read off the record rather than guessed: `RelationEP` ties each participant to an event
    by `EventKeyRef`, so the event the most participants are attached to is the one the act
    is about. Ties and unreferenced events fall back to document order.

    This surfaced as a crash — `'list' object has no attribute 'get'` — the first time a
    whole-archive harvest brought in an archive whose records do this. Every surname-filtered
    harvest before it had missed them, which is worth remembering about coverage: the code
    had been wrong all along and the data had never said so.
    """
    events = _as_list(r.get("Event"))
    if len(events) <= 1:
        return events[0] if events else {}
    referenced: Counter = Counter()
    for rel in _as_list(r.get("RelationEP")):
        if rel.get("EventKeyRef"):
            referenced[rel["EventKeyRef"]] += 1
    return max(events, key=lambda e: referenced.get(e.get("@eid"), 0))


def normalise_act(row: dict) -> Act:
    # Every record enters here, so this is the one place the annotated-value convention
    # has to be dealt with. See unwrap_annotated.
    row = unwrap_annotated(row)
    r = row.get("record") or {}
    ev = _principal_event(r)
    # Coerced for the same reason: nothing guarantees an archive publishes exactly one.
    src = next(iter(_as_list(r.get("Source"))), {}) or {}
    date = _api_date(ev.get("EventDate"))
    year = year_of(date)

    people = [_normalise_person(p, year) for p in _as_list(r.get("Person"))]
    by_pid = {p.pid: p for p in people}
    for rel in _as_list(r.get("RelationEP")):
        p = by_pid.get(rel.get("PersonKeyRef"))
        if p:
            p.role = (rel.get("RelationType") or "").lower().strip() or "onbekend"

    principals = [p for p in people if PRINCIPAL.match(p.role)]
    edges = []
    for p in people:
        is_father, is_mother = bool(FATHER_OF.match(p.role)), bool(MOTHER_OF.match(p.role))
        if is_father or is_mother:
            child = _attaches_to(p.role, principals)
            if child:
                edges.append({"type": "father" if is_father else "mother", "parent": p.pid, "child": child.pid})
        elif GRANDPARENT_OF.match(p.role):
            # Sideless on purpose: the act says "grandparent of the groom" and never
            # which of his parents it belongs to. Recording a side would be inventing
            # the half of the fact the record withheld.
            grandchild = _attaches_to(p.role, principals)
            if grandchild:
                edges.append({"type": "grandparent", "parent": p.pid, "child": grandchild.pid})
        elif FORMER_PARTNER_OF.match(p.role):
            other = _attaches_to(p.role, principals)
            if other:
                edges.append({"type": "former_couple", "a": other.pid, "b": p.pid})
        elif WITNESS.match(p.role) and not OFFICIAL.match(p.role):
            # Attached to the act, not to a person: the act says this man stood witness,
            # and says nothing at all about who he is to anyone in it.
            edges.append({"type": "witness", "who": p.pid})
        elif SPOUSE_ROLE.match(p.role) and len(principals) == 1:
            edges.append({"type": "couple", "a": principals[0].pid, "b": p.pid})
    # A marriage act states the couple outright, which is why it is the richest record
    # in the registry: one act, two parent pairs and a marriage.
    groom = next((p for p in people if p.role == "bruidegom"), None)
    bride = next((p for p in people if p.role == "bruid"), None)
    if groom and bride:
        edges.append({"type": "couple", "a": groom.pid, "b": bride.pid})

    scans = [s.get("UriViewer") for s in _as_list((src.get("SourceAvailableScans") or {}).get("Scan")) if s.get("UriViewer")]
    ref = src.get("SourceReference") or {}
    act = Act(
        id=row["id"],
        archive=row.get("archive", ""),
        archive_org=row.get("archive_org") or ref.get("InstitutionName") or row.get("archive", ""),
        type=ev.get("EventType") or src.get("SourceType") or "onbekend",
        source_type=src.get("SourceType"),
        date=date,
        year=year,
        place=(ev.get("EventPlace") or {}).get("Place") or (src.get("SourcePlace") or {}).get("Place"),
        act_number=ref.get("DocumentNumber"),
        collection=ref.get("Collection"),
        url=f"https://www.openarchieven.nl/{row['id']}",
        scan=scans[0] if scans else None,
        original=src.get("SourceDigitalOriginal"),
        people=people,
        edges=edges,
        fetched=row.get("fetched"),
    )
    for p in people:
        p.act = act
    return act


def stated_kin(m: Mention) -> list[tuple[str, Mention]]:
    """Who the act says this person's relatives are — the second identifier, in the
    words of the rule that demands one.

    CLAUDE.md has always named "parent names" as a way to satisfy the two-independent-
    identifiers rule, and the scorer never implemented it: it compared two people to each
    other and ignored the four relatives standing next to them in the same document.
    This is the join that fixes that, and it is why a marriage act is worth six searches.

    Relations are returned as the ACT states them, never as this project concludes them.
    """
    act = m.act
    if not act:
        return []
    by_pid = {p.pid: p for p in act.people}
    out: list[tuple[str, Mention]] = []
    for e in act.edges:
        kind = e["type"]
        if kind in ("father", "mother", "grandparent") and e["child"] == m.pid:
            parent = by_pid.get(e["parent"])
            if parent:
                out.append((kind, parent))
        elif kind in ("couple", "former_couple") and m.pid in (e["a"], e["b"]):
            other = by_pid.get(e["b"] if e["a"] == m.pid else e["a"])
            if other:
                out.append(("spouse" if kind == "couple" else "former spouse", other))
        elif kind in ("father", "mother") and e["parent"] == m.pid:
            child = by_pid.get(e["child"])
            if child:
                out.append(("child", child))
    return out


def witnesses(act: Act) -> list[Mention]:
    """The people the act says stood witness. Not kin, and never recorded as kin — but
    the same names recur across one family's acts, and that recurrence is evidence a
    name comparison cannot reach."""
    by_pid = {p.pid: p for p in act.people}
    return [by_pid[e["who"]] for e in act.edges if e["type"] == "witness" and e["who"] in by_pid]


# ---------- the whole corpus ----------


def corpus_exists() -> bool:
    return ACTS_DIR.is_dir() and any(ACTS_DIR.glob("*.jsonl"))


@lru_cache(maxsize=1)
def load_corpus() -> tuple[Act, ...]:
    acts: list[Act] = []
    seen: set[str] = set()
    if ACTS_DIR.is_dir():
        for f in sorted(ACTS_DIR.glob("*.jsonl")):
            for line in f.read_text(encoding="utf-8").split("\n"):
                if not line.strip():
                    continue
                row = json.loads(line)
                # The same act can be reached from a surname harvest and a commune
                # harvest both.
                if row["id"] in seen:
                    continue
                seen.add(row["id"])
                acts.append(normalise_act(row))
    return tuple(acts)


def corpus_mentions(acts: tuple[Act, ...] | None = None) -> list[Mention]:
    """Every person-mention in the corpus, flattened, each still knowing its act. This
    is what candidate generation searches, and what the frequency tables count."""
    return [p for act in (acts if acts is not None else load_corpus()) for p in act.people]


# The single most expensive line in the project before it was cached.
#
# `surname_weight` asks the manifest two questions — the population, and how many
# records exist under this surname — and the scorer calls `surname_weight` once per
# comparison. A profile of `research.py acts` found 342,568 reads of this 49 KB file:
# 138 seconds of a 220-second run, 104 of them inside `json.raw_decode`, to parse the
# same bytes over and over. Caching it took that run to 13 seconds.
#
# The cache holds one entry because there is one manifest. It is invalidated by
# `reset_manifest_cache`, which `harvest.py` calls around every write — see the
# read-merge-write note on `save_manifest`, which exists precisely because this file
# changes underneath a long harvest.
@lru_cache(maxsize=1)
def load_manifest() -> dict:
    if not MANIFEST.exists():
        return {"harvests": []}
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def reset_manifest_cache() -> None:
    """Forget the held manifest, so the next read comes off disk.

    Anything that WRITES the manifest must call this, on both sides of the write: before,
    because another process may have added a harvest since this one last looked, and
    after, because the caller is about to read back what it just merged. A harvest that
    reads a stale manifest re-fetches thousands of records it already holds, which is the
    opposite of what the cache is for.
    """
    load_manifest.cache_clear()


def population() -> int:
    """How many person-mentions the venue holds for Belgium in total.

    Recorded by the harvester on its first run, because it is the denominator every
    rarity weight needs and it cannot be recovered from the harvest itself.
    """
    return load_manifest().get("population", {}).get("be", 0)


def surname_harvest(surname: str) -> dict | None:
    """The manifest row for a whole-surname harvest of this name, if one was run.

    Matched on the QUERY rather than on the harvest id, because the id is a slug and
    slugs have collided: "De Keyser" was filed once as `de-keyser` and once as
    `dekeyser`, and each lookup found only one of them.

    A harvest narrowed by commune is not a whole-surname harvest and is skipped — it
    counts one commune, so neither its total nor its coverage says anything about the
    surname as a whole.
    """
    key = normalise_key(surname)
    best = None
    for h in load_manifest()["harvests"]:
        query = h.get("query") or {}
        if query.get("eventplace") or query.get("name") in (None, "*"):
            continue
        if normalise_key(query["name"]) != key:
            continue
        # Where the slug collision has already left two rows, prefer the one that
        # actually holds more.
        if best is None or (h.get("mentions") or 0) > (best.get("mentions") or 0):
            best = h
    return best


def surname_population_count(surname: str) -> int | None:
    """How common a surname is in the WHOLE venue, not in what was harvested.

    This matters more than it looks. Counting surnames inside the corpus gives the
    wrong answer by construction: harvest "Bundervoet" and 392 of the 393 mentions you
    now hold are Bundervoets, so the rarest surname in Belgium scores as the commonest
    thing in the world. The harvester already knows the true figure — the API reports
    `number_found` before paging — so a whole-surname harvest records it, and that is
    what the weight is computed from.

    None means no whole-surname harvest has been run, and the caller falls back to
    counting the corpus with all the bias that implies.
    """
    h = surname_harvest(surname)
    return h.get("found") if h else None


def surname_coverage(surname: str) -> float | None:
    """What fraction of that surname's records are actually held.

    The distinction the search log draws between `miss` and `blocked`, applied to the
    corpus. A harvest capped at 600 of 11,795 De Keyser mentions has read five per cent
    of them — so finding no candidate is not evidence of absence, it is evidence of
    not having looked. Treating a partial harvest as a complete one made the queue sink
    those frontiers as though they had been searched and found empty.

    None means the surname has never been harvested at all, which is different again:
    unknown, and cheap to resolve.

    THE NUMERATOR IS WHAT IS HELD, NOT WHAT WAS ASKED FOR. This read the manifest's
    `mentions` — how many that surname's own query returned — which was the same number
    until acts started arriving by routes that never mentioned a surname. After nine
    whole-archive harvests the manifest still said 600 De Keyser mentions held of 11,795
    while the corpus held 3,512, and 600 of 2,370 for Damman while it held 2,334 — call
    that 98% and it is essentially finished. Both directions of that error are bad and the
    second is worse: understating coverage sinks the frontier's P, and it makes
    `frontier.py` recommend "finish the harvest" as the cheapest route to records already
    on disk. Reporting held as not-held is the same class of mistake as reporting blocked
    as miss, pointed the other way.

    The denominator stays the venue's own `found`, because that is the only figure that
    says how many exist. Only the numerator changes: count the corpus.
    """
    h = surname_harvest(surname)
    if h is None:
        return None
    if h.get("complete"):
        return 1.0
    found = h.get("found") or 0
    if not found:
        return 1.0
    return min(1.0, mentions_held(surname) / found)


def mentions_held(surname: str) -> int:
    """How many mentions of a surname the corpus actually holds, by any route.

    From the index when there is a current one, because counting it means reading every
    act. The manifest's own figure is the fallback and it is a floor rather than an
    answer: it knows only what that surname's own query returned, so it is right until
    the first act arrives some other way and low for ever after.
    """
    from . import store
    if store.is_current():
        return store.held_under(surname)
    h = surname_harvest(surname) or {}
    return h.get("mentions") or 0


# ---------- frequency ----------


@dataclass
class Frequencies:
    """The u-probabilities of probabilistic record linkage, counted from the corpus
    itself rather than assumed.

    This is the whole reason the harvest is worth holding: agreement on "Schalandrijn"
    and agreement on "Janssens" are not the same evidence, and only a population count
    can say by how much.
    """

    n: int = 0
    surnames: Counter = field(default_factory=Counter)
    givens: Counter = field(default_factory=Counter)
    places: Counter = field(default_factory=Counter)


@lru_cache(maxsize=1)
def frequencies() -> Frequencies:
    """The rarity tables — from the index when there is a current one, else counted.

    Every caller of `compare` needs these, and counting them means reading the whole
    corpus: 8.5 seconds and half a gigabyte to answer a question about one person.
    `store` counts the identical tables in the pass it already makes over the acts, and
    `count_frequencies` below stays as the definition both are measured against.

    Imported here rather than at the top because `store` imports this module. A stale
    index is never silently rebuilt — a report is not the place to spend twenty seconds
    nobody asked for — so it falls back to counting, and the tools that want the index
    call `store.ensure()` for themselves.
    """
    from . import store
    if store.is_current():
        return store.frequencies()
    return count_frequencies()


def count_frequencies() -> Frequencies:
    """The tables, counted from the corpus itself. The reference implementation: `store`
    reproduces this at index time, and the test pins that the two agree exactly."""
    f = Frequencies()
    for m in corpus_mentions():
        f.n += 1
        s = normalise_key(m.surname)
        if s:
            f.surnames[s] += 1
        # Compound given names are the norm here ("Christianus Josephus"), and each
        # element carries its own rarity, so they are counted separately.
        for g in (normalise_key(x) for x in (m.given or "").split()):
            if g:
                f.givens[g] += 1
        place = normalise_key(m.act.place if m.act else None)
        if place:
            f.places[place] += 1
    return f
