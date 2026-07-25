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


def normalise_key(s: str | None) -> str:
    return re.sub(r"[^a-z]", "", unicodedata.normalize("NFD", (s or "").lower()))


def _as_list(v):
    """Single-element lists arrive as bare objects, so everything is coerced to a list
    before it is read. Getting this wrong loses the only participant in an act."""
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def _text(v):
    """The scalar behind a field, whatever shape the archive published it in.

    A2A is XML rendered as JSON, so an element that carries an attribute arrives as an
    object rather than a string: Lommel publishes a place as
    `{"@TranscriptionRemark": "Lommel-Centrum", "$": "Lommel"}` where every other archive
    publishes `"Lommel"`. Reading that straight put a dict where the rest of the code
    expected text, and the whole validator died on `.lower()` — one commune's annotation
    habit taking down a run over three hundred people.

    Applied at every point a scalar is read, not only at the one that broke, because the
    same convention can attach to a name or a date just as easily as to a place."""
    if isinstance(v, dict):
        return v.get("$")
    if isinstance(v, list):
        return next((t for t in (_text(x) for x in v) if t), None)
    return v


def _api_date(d) -> str | None:
    """Into the project's date grammar — never into anything looser. A record with a
    year and no month becomes "1902", not "1902-00", because the grammar has no syntax
    for a guess and this is exactly where one would get invented."""
    if not d:
        return None
    y, mo, da = _text(d.get("Year")), _text(d.get("Month")), _text(d.get("Day"))
    if not y:
        return None
    year = str(y)
    if mo and da:
        return f"{year}-{int(mo):02d}-{int(da):02d}"
    if mo:
        return f"{year}-{int(mo):02d}"
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


def _person_name(p: dict) -> tuple[str, str, str]:
    n = p.get("PersonName") or {}
    # Particles are published in their own field by some archives and folded into the
    # surname by others; the surname keeps whichever form the record used, because the
    # project's own rule is that `surname` is stated, not computed.
    surname = " ".join(
        x for x in (_text(n.get("PersonNamePrefix")), _text(n.get("PersonNamePrefixLastName")),
                    _text(n.get("PersonNameLastName"))) if x
    ).strip()
    given = " ".join(x for x in (_text(n.get("PersonNameFirstName")), _text(n.get("PersonNameInitials"))) if x).strip()
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


def normalise_act(row: dict) -> Act:
    r = row.get("record") or {}
    ev = r.get("Event") or {}
    src = r.get("Source") or {}
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
        place=_text((ev.get("EventPlace") or {}).get("Place")) or _text((src.get("SourcePlace") or {}).get("Place")),
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


def load_manifest() -> dict:
    if not MANIFEST.exists():
        return {"harvests": []}
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


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
    """
    h = surname_harvest(surname)
    if h is None:
        return None
    if h.get("complete"):
        return 1.0
    found = h.get("found") or 0
    return min(1.0, (h.get("mentions") or 0) / found) if found else 1.0


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
