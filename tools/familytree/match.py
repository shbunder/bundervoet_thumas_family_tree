"""Candidate generation and scoring — how a person in the tree is compared with a
person in an act, without comparing everybody with everybody.

Two ideas, both borrowed rather than invented.

BLOCKING: never compare all pairs. Group records by cheap keys that a true match must
share, and compare only inside the groups. Several keys, not one, because any single
key fails on the variant it is blind to — a phonetic key misses "Vanstechele" against
"Vanstechelman", a date key misses an undated record.

WEIGHTED SCORING: agreement is worth what the value is rare, measured in bits. Two
people both called Janssens have told you almost nothing; two people both called
Schalandrijn have told you almost everything. The frequencies come from the harvested
corpus itself, so this is counted, not assumed.

What this does NOT do is decide. It ranks, and it vetoes: a stated conflict kills a
pair outright, and the project's rule that a graft needs two INDEPENDENT identifiers is
enforced as a floor no score can buy its way past — a matching forename and surname are
one identifier, not two, however rare they are. The output is a candidate list for a
human or the verifier to refute.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from functools import lru_cache

from .corpus import (
    Frequencies, Mention, frequencies, normalise_key, population, stated_kin,
    surname_population_count,
)
from .people import DAY, family_key, given_names, point_year, year_of, year_span

# ---------- phonetics ----------
# Flemish orthography drifted for centuries and the same family is spelled several ways
# in this tree already — Bostyn/Bostin, Dekeyser/De Keyser, Vanstechele/Vanstechelman.
# These rules fold the variations that are known to occur here; they are deliberately
# conservative, because over-folding merges families and a merged family is the failure
# this project is built to avoid.
_RULES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"ij"), "i"), (re.compile(r"y"), "i"),        # Bostyn → Bostin
    (re.compile(r"sch"), "s"),                                # Dutch -sch is a plain s
    (re.compile(r"ck"), "k"), (re.compile(r"q"), "k"), (re.compile(r"x"), "ks"),
    (re.compile(r"c(?=[eiy])"), "s"), (re.compile(r"c"), "k"),  # Craenenbroeck → Kraenenbroek
    (re.compile(r"gh"), "g"), (re.compile(r"ph"), "f"), (re.compile(r"th"), "t"),
    (re.compile(r"ae"), "a"), (re.compile(r"oe"), "u"), (re.compile(r"ou"), "u"),
    (re.compile(r"uy"), "u"), (re.compile(r"ui"), "u"),
    (re.compile(r"z"), "s"), (re.compile(r"w"), "v"), (re.compile(r"v"), "f"),
    (re.compile(r"(.)\1+"), r"\1"),                           # Stroobandt → Strobant
    (re.compile(r"dt$"), "t"), (re.compile(r"d$"), "t"),      # Devriendt → Defrient
]


# Sixteen regex substitutions per call, and `block_keys` calls it for every candidate on
# both sides of every comparison: 1,404,305 calls against 39,335 distinct surnames in one
# `research.py acts` run. Pure, so memoising it is free. See `family_key` on the maxsize.
@lru_cache(maxsize=None)
def phonetic(surname: str | None) -> str:
    s = normalise_key(surname)
    if not s:
        return ""
    for pattern, repl in _RULES:
        s = pattern.sub(repl, s)
    return re.sub(r"(.)\1+", r"\1", s)


# ---------- the shape both sides are compared in ----------
# Tree records and corpus mentions are different objects; everything below works on
# this one, so there is a single definition of "what can be compared" instead of two
# that drift.


@dataclass
class Candidate:
    ref: str
    name: str
    surname: str = ""
    given: str = ""
    sex: str | None = None
    birth_year: int | None = None
    birth_date: str | None = None
    birth_place: str | None = None
    death_year: int | None = None
    # The death date as the grammar wrote it, next to `birth_date` — which was here from
    # the start while this was not, so a death recorded `<1748` reached the scorer only as
    # the number 1748 and every veto treated a bound as a measurement.
    death_date: str | None = None
    places: list[str] = field(default_factory=list)
    # Where the RECORD happened, as opposed to where this person was. Weak evidence.
    context_places: list[str] = field(default_factory=list)
    # The year of the record this candidate was read from. A hard bound on who can be in
    # it, and often the only bound an act offers about a participant it dates not at all.
    event_year: int | None = None
    occupation: str | None = None
    # Stated, so it can be told apart from a year implied by an age in an act. Only a
    # stated year is strong enough to veto on.
    stated_birth_year: bool = False
    # The relatives each side names, as (bucket, surname key, forename keys). Two people
    # who agree on a mother's maiden name are not two people who happen to share a
    # surname; this is what lets the scorer tell those apart.
    kin: list[tuple[str, str, frozenset[str]]] = field(default_factory=list)
    mention: Mention | None = None
    person_id: str | None = None

    def __hash__(self):
        return hash(self.ref)


# Which stated relations may be compared with which. A father in the tree answers a
# father in an act and nothing else — matching someone's father against someone else's
# husband is exactly the class of error the two-identifier rule exists to stop. Spouse
# and former spouse share a bucket because a remarriage is one person's two marriages,
# and keeping them apart is how a widow turns into twins.
_KIN_BUCKET = {
    "father": "father", "mother": "mother", "grandparent": "grandparent",
    "child": "child", "spouse": "spouse", "former spouse": "spouse",
}


# Particles and placeholders are not forenames, and treating them as ones manufactures
# agreement out of nothing: "van" is a token in a large share of Flemish names, so a
# spouse recorded as "Catharina van Hecke" matched every "… Van Keymeulen" in the corpus
# and scored it as a shared forename. "NN" is this project's marker for a name a record
# never gave, which makes it the emptiest evidence there is.
_NOT_A_FORENAME = frozenset({
    "van", "de", "den", "der", "des", "ten", "ter", "het", "t", "d", "le", "la", "du",
    "vande", "vanden", "vander", "vandc", "nn", "onbekend", "ux", "uxor",
})


def given_keys(text: str | None) -> frozenset[str]:
    """The comparable forename tokens in a name. One definition, because a particle
    slipping through here is indistinguishable from evidence downstream."""
    return frozenset(g for g in (normalise_key(x) for x in (text or "").split())
                     if g and g not in _NOT_A_FORENAME)


def _kin_entry(bucket: str, name: str, surname: str) -> tuple[str, str, frozenset[str]] | None:
    key = family_key(surname)
    given = given_keys(name) - ({key} if key else set())
    if not given and not key:
        return None
    return (bucket, key, given)


def from_person(p: dict, people: dict | None = None, children: dict | None = None) -> Candidate:
    """A tree record, in the comparable shape.

    `people` and `children` are optional because most callers only need the person's own
    fields; pass them and the relatives come too, which is what turns a name agreement
    into a second independent identifier.
    """
    birth, death = p.get("birth") or {}, p.get("death") or {}
    kin: list[tuple[str, str, frozenset[str]]] = []
    # The data model says being a father or a mother already settles sex, so the record
    # is allowed to omit it — but the scorer was reading the omission as "unknown" and
    # declining to veto. Every parent in the tree was therefore comparable with every
    # candidate of the opposite sex, and the kin evidence pushed those to the top.
    sex = p.get("sex")
    if not sex and children:
        for cid in children.get(p["id"], []):
            child = (people or {}).get(cid) or {}
            if child.get("father") == p["id"]:
                sex = "m"
            elif child.get("mother") == p["id"]:
                sex = "f"
            if sex:
                break
    if people:
        for role, pid in (("father", p.get("father")), ("mother", p.get("mother"))):
            other = people.get(pid) if pid else None
            if other:
                kin.append(_kin_entry(role, other["name"], other.get("surname") or ""))
        for s in p.get("spouses") or []:
            spouse = people.get(s.get("id")) if s.get("id") else None
            name = spouse["name"] if spouse else s.get("name")
            surname = (spouse or {}).get("surname") or ""
            if name:
                kin.append(_kin_entry("spouse", name, surname))
        for cid in (children or {}).get(p["id"], []):
            child = people.get(cid)
            if child:
                kin.append(_kin_entry("child", child["name"], child.get("surname") or ""))
    return Candidate(
        ref=p["id"],
        name=p["name"],
        surname=p.get("surname") or "",
        given=given_names(p) if p.get("surname") else p["name"],
        sex=sex,
        birth_year=year_of(birth.get("date")),
        birth_date=birth.get("date"),
        birth_place=birth.get("place"),
        death_year=year_of(death.get("date")),
        death_date=death.get("date"),
        places=[x for x in (birth.get("place"), death.get("place")) if x],
        occupation=p.get("occupation"),
        stated_birth_year=bool(birth.get("date")),
        kin=[k for k in kin if k],
        person_id=p["id"],
    )


def from_mention(m: Mention) -> Candidate:
    act = m.act
    kin = [_kin_entry(_KIN_BUCKET[rel], other.name, other.surname)
           for rel, other in stated_kin(m) if rel in _KIN_BUCKET]
    return Candidate(
        ref=f"{act.id}#{m.pid}" if act else m.pid,
        name=m.name,
        surname=m.surname or "",
        given=m.given or "",
        sex=m.sex,
        birth_year=m.birth_year or m.implied_birth_year,
        birth_date=m.birth,
        birth_place=m.birth_place,
        # ONLY the deceased. A death act names the dead person's parents, spouse and
        # informants, and all of them are alive to be named — giving every participant
        # the act's year as their own death year made anyone in this tree who died in
        # 1861 match the living father in an 1861 death act.
        death_year=(act.year if act and act.type == "Overlijden"
                    and re.match(r"^(overledene|gedoopte)?$|^overledene", m.role or "") else None),
        # The person's OWN places only. The act's commune goes in context_places: a
        # marriage held at Oostende says where the wedding was, not where either party
        # was born or lived, and treating it as theirs matched a third of this tree.
        places=[x for x in (m.birth_place, m.residence) if x],
        context_places=[act.place] if act and act.place else [],
        event_year=act.year if act else None,
        occupation=m.occupation,
        stated_birth_year=bool(m.birth_year),
        kin=[k for k in kin if k],
        mention=m,
    )


# ---------- blocking ----------


# The particles, as they look AFTER phonetic() has run — v and w both fold to f, so "van"
# is "fan" and "ver" is "fer" by the time this sees them.
#
# They are stripped before the prefix key is taken, because otherwise the prefix IS the
# particle and carries no information about the family. A quarter of Flemish surnames begin
# "Van den", "Van der" or "De", so `x:{ph[:6]}` put 150,611 mentions under `x:fanden`,
# 137,463 under `x:defade` and 116,538 under `x:fander` — 17% of a 1.7-million-act corpus in
# fourteen buckets. A block that holds a sixth of the population is not blocking; it is a
# scan with extra steps, and it is what made `research.py acts` seven minutes.
#
# Stripping also FIXES a case the old key missed: "Vandenberghe" and "Van Berghe" share no
# six-character prefix at all (`fanden` vs `fanber`) and were never compared. On the stem
# they are both `berge`.
_PARTICLE = re.compile(r"^(?:fanden|fander|fande|fan|des|den|der|de|ten|ter|fer|het|le|la|du|t)+")
# Below this, the particle was most of the name and what is left cannot discriminate:
# "Devos" would become "fos". Those keep the whole phonetic form instead.
_STEM_FLOOR = 4

# How much of the stem the prefix key keeps — and it depends on how long the stem is, which
# is the part that took two measurements to get right.
#
# A SHORT stem needs generosity, because that is where a single trailing character decides
# everything: "Vandevelde" and "Vandevelden" have stems "felde" and "felden" and are one
# family. Four characters bridges them.
#
# A LONG stem needs none, and four characters actively harm it. "Wittenheyns" has the stem
# "fitenheins"; cut to four it becomes "fite", which is also what "De Witte" reduces to — so
# a surname with no exact matches in the corpus at all was pulling 28,089 mentions of an
# unrelated family, and throwing away six highly discriminating characters to do it.
#
# Measured against the 223 open frontiers, mentions pulled through this key:
#   ph[:6], as it was     2,542,433     the particle ate the prefix
#   stem[:4]              1,282,568     particle stripped, fixed length
#   stem, adaptive          941,505     this
# Both later schemes keep all seven variant pairs the key exists for; only the adaptive one
# also keeps Wittenheyns and De Witte apart. Strict improvements, not trades — nothing that
# was compared before is uncompared now.
_SHORT_STEM = 6
_PREFIX_SHORT, _PREFIX_LONG = 4, 6


def _prefix_key(ph: str) -> str:
    s = surname_stem(ph)
    return s[:_PREFIX_SHORT] if len(s) <= _SHORT_STEM else s[:_PREFIX_LONG]


@lru_cache(maxsize=None)
def surname_stem(ph: str) -> str:
    """A phonetic surname with its leading particle removed, for blocking only.

    Never used as evidence and never shown: `family_key` and `phonetic` remain what decides
    whether two surnames agree. This only decides which pairs are worth comparing at all.
    """
    s = _PARTICLE.sub("", ph)
    return s if len(s) >= _STEM_FLOOR else ph


def block_keys(c: Candidate) -> list[str]:
    """Several passes over the same records. A pair that agrees on ANY key is compared;
    a pair that agrees on none never is. That is what keeps this off the O(n²) curve as
    the tree goes from 302 people to thousands and the corpus to millions."""
    ph = phonetic(c.surname)
    keys: list[str] = []
    if ph:
        keys.append(f"p:{ph}")
        # Catches truncated and extended forms — Vanstechele against Vanstechelman — on the
        # part of the name that identifies the family rather than on its particle.
        keys.append(f"x:{_prefix_key(ph)}")
        if c.birth_year:
            keys.append(f"pd:{ph}:{c.birth_year // 10}")
        for place in c.places:
            keys.append(f"pp:{ph}:{normalise_key(place)}")
    # The pass that survives a surname nobody spelled the same way twice.
    givens = [g for g in (normalise_key(x) for x in (c.given or "").split()) if g]
    if givens and c.birth_year:
        keys.append(f"g:{givens[0]}:{c.birth_year // 10}")
    return list(dict.fromkeys(keys))


def build_index(candidates) -> dict[str, list[Candidate]]:
    index: dict[str, list[Candidate]] = {}
    for c in candidates:
        for k in block_keys(c):
            index.setdefault(k, []).append(c)
    return index


def candidates_for(c: Candidate, index: dict[str, list[Candidate]]) -> list[Candidate]:
    out: dict[str, Candidate] = {}
    for k in block_keys(c):
        for other in index.get(k, []):
            if other.ref != c.ref:
                out[other.ref] = other
    return list(out.values())


# ---------- weights ----------
MAX_BITS = 14.0  # a surname seen once is very strong evidence, not infinite evidence
MAX_LIFESPAN = 110  # beyond this the pair is two people, whatever else agrees
# An act can name someone long dead — a deceased parent, a grandparent — but not
# indefinitely long. Generous on purpose: the point is to kill the case where an act
# gives a participant no dates at all, so nothing else can veto, and a man born in 1665
# is matched to a father named in a marriage of 1911.
MAX_POSTHUMOUS_MENTION = 120
_NO_CORPUS = {"surname": 6.0, "given": 3.0, "place": 4.0}


def _bits(count: float, n: int, cap: float = MAX_BITS) -> float:
    if not n:
        return 0.0
    return min(cap, math.log2(n / max(count, 0.5)))


@dataclass
class Weight:
    bits: float
    count: int | None
    estimated: bool


def surname_weight(surname: str | None, freq: Frequencies | None = None) -> Weight:
    """How much a surname is worth as evidence, before anything else is compared.

    Also the single most useful number a strategist can have: it is the difference
    between a frontier that is searchable and one that is not.

    Measured against the whole venue where that figure is known, and only against the
    harvest when it is not — a harvest is filtered to the surname it was run for, so
    counting inside it makes every harvested surname look common.
    """
    freq = freq if freq is not None else frequencies()
    n = population()
    count = surname_population_count(surname)
    if n and count is not None:
        return Weight(_bits(count, n), count, False)
    if not freq.n:
        return Weight(_NO_CORPUS["surname"], None, True)
    return Weight(_bits(freq.surnames.get(family_key(surname), 0), freq.n), None, True)


# ---------- comparison ----------
# The classes of evidence, kept apart on purpose. "Two independent identifiers" means
# two of THESE, not two fields — a matching forename and a matching surname are both
# the name, and the log is full of right-name/wrong-province rejections that prove it.
CLASSES = ("name", "date", "place", "role", "kin")
# Agreements that are real evidence but must never be one of the two independent
# identifiers. Both were promoted to full classes once and both produced false grafts:
# an act HELD at Oostende matched everyone in the tree who lived there, and two men's
# wives sharing the forename Simonne matched across seventy years. They still add bits —
# they are not nothing — but they cannot carry a graft on their own.
WEAK_CLASSES = ("context", "kin-forename", "name-forename")


@dataclass
class Match:
    a: Candidate
    b: Candidate
    bits: float
    # The evidence that is NOT the name, which is what identity actually turns on. A
    # rare surname is enormous evidence of the same FAMILY and almost none of the same
    # PERSON: every Bundervoet in Belgium agrees on it, including the 396 who are not
    # this man. Banding on the total let a bare surname clear the bar and buried the
    # two real matches under two hundred relatives.
    distinguishing: float
    agree: list[tuple[str, str, float]]
    conflict: list[str]
    classes: list[str]
    independent: int
    graftable: bool
    band: str

    def explain(self) -> str:
        if self.conflict:
            return "REJECTED — " + "; ".join(self.conflict)
        agreed = ", ".join(label for _, label, _ in self.agree)
        return (f"{self.bits:.1f} bits ({self.distinguishing:.1f} beyond the name), "
                f"{self.independent} independent ({'+'.join(self.classes)}) — {agreed}")


def _asserts(date: str | None, year: int | None) -> int | None:
    """The year to SCORE on: what the date claims, or None if it only bounds one.

    `~1682` claims 1682 and still earns its bits against an act saying 1682. `<1673` and
    `1920..1929` claim no year at all, so an act stating 1920 agrees with the lower edge of
    a range by arithmetic rather than by evidence, and must not be paid for it.

    Falls through to the plain year where there is no grammar string — a mention's year
    comes from an act, and where it was implied by an age `stated_birth_year` is already
    False, so it can score and cannot veto.
    """
    return point_year(date) if date else year


def _permits(date: str | None, year: int | None) -> tuple[int | None, int | None]:
    """The years to VETO on: everything the date leaves open, inclusive both ends."""
    lo, hi = year_span(date)
    if lo is None and hi is None and year:
        return (year, year)
    return (lo, hi)


def _cannot_meet(x: tuple[int | None, int | None], y: tuple[int | None, int | None],
                 slack: int = 0) -> bool:
    """True only if no year satisfies both spans, even allowing `slack` between them.

    The whole discipline of this file's vetoes in one function: certain, or nothing. An
    open end means unknown, and unknown never vetoes.
    """
    return bool((x[1] is not None and y[0] is not None and y[0] - x[1] > slack)
                or (y[1] is not None and x[0] is not None and x[0] - y[1] > slack))


def _show(span: tuple[int | None, int | None]) -> str:
    lo, hi = span
    if lo == hi:
        return str(lo)
    return f"{lo if lo is not None else '?'}–{hi if hi is not None else '?'}"


def compare(a: Candidate, b: Candidate, freq: Frequencies | None = None) -> Match:
    freq = freq if freq is not None else frequencies()
    # Every date is read twice below, and the two readings answer different questions: what
    # it asserts (evidence) and what it permits (vetoes). Conflating them is what let a
    # record saying "some year in the 1920s" be REJECTED for disagreeing with 1925.
    a_born, b_born = _asserts(a.birth_date, a.birth_year), _asserts(b.birth_date, b.birth_year)
    a_died, b_died = _asserts(a.death_date, a.death_year), _asserts(b.death_date, b.death_year)
    a_birth, b_birth = _permits(a.birth_date, a.birth_year), _permits(b.birth_date, b.birth_year)
    a_death, b_death = _permits(a.death_date, a.death_year), _permits(b.death_date, b.death_year)
    agree: list[tuple[str, str, float]] = []
    conflict: list[str] = []
    classes: list[str] = []
    score = 0.0

    def add(cls: str, label: str, bits: float) -> None:
        nonlocal score
        score += bits
        agree.append((cls, label, bits))
        if cls not in classes:
            classes.append(cls)

    # --- name ---
    same_surname = bool(family_key(a.surname)) and family_key(a.surname) == family_key(b.surname)
    same_phonetic = bool(phonetic(a.surname)) and phonetic(a.surname) == phonetic(b.surname)
    if same_surname or same_phonetic:
        w = surname_weight(a.surname, freq).bits
        # A spelling variant is real evidence but weaker than an exact agreement — the
        # fold could have merged two families that were never the same.
        label = f"surname {a.surname}" if same_surname else f"surname {a.surname}~{b.surname}"
        add("name", label, w if same_surname else w * 0.6)

    ga, gb = given_keys(a.given), given_keys(b.given)
    given_bits = 0.0
    for g in ga & gb:
        given_bits += _bits(freq.givens.get(g, 0), freq.n, 8.0) if freq.n else _NO_CORPUS["given"]
    if given_bits:
        # A forename is only half a name. On its own it matched Henricus Josephus BOSTYN
        # to Henricus Amandus MOMBAERTS, Joanna KEIRSEBILCK to Joanna Maria GOORIS and
        # Anna Maria GAUTIERT to Anna Catharina VAN RENTERGHEM — three people whose
        # surnames have nothing to do with ours. It still scores, because a shared
        # forename plus a shared year is worth noticing; it cannot be one of the two
        # independent identifiers unless the surname agrees too.
        cls = "name" if (same_surname or same_phonetic) else "name-forename"
        add(cls, f"forename{'s' if len(ga & gb) > 1 else ''}", min(given_bits, 10.0))

    # --- date ---
    # A day-level agreement between two independently written records is close to
    # conclusive on its own; a shared year in a commune of a few thousand is not.
    # `DAY.match`, not `len(...) == 10`. "1920..1929" is exactly ten characters, so a range
    # was being read as a day-level date and compared as a string: two people who each know
    # only that they were born in the 1920s scored 12 bits for "the same day", and one of
    # them against an act stating a real day was vetoed for "birth dates 1920..1929 vs
    # 1920-06-01". A length is not a format.
    if a.birth_date and b.birth_date and DAY.match(a.birth_date) and a.birth_date == b.birth_date:
        add("date", f"birth {a.birth_date}", 12.0)
    elif a_born and b_born:
        gap = abs(a_born - b_born)
        if gap == 0:
            add("date", f"birth year {a_born}", 6.0)
        elif gap <= 2:
            add("date", f"birth year ±{gap}", 2.0)
    if a_died and b_died and a_died == b_died:
        add("date", f"death year {a_died}", 5.0)

    # --- place ---
    # The class that did all the rejecting in the log so far: the Van Craenenbroeck and
    # Janssens false positives were every one of them right-name/wrong-province.
    pa = {normalise_key(x) for x in a.places if normalise_key(x)}
    pb = {normalise_key(x) for x in b.places if normalise_key(x)}
    shared = sorted(pa & pb)
    if not shared:
        # Fall back to where the record was drawn up. Same bits, weaker class: it cannot
        # anchor a graft, because a busy commune appears in thousands of acts.
        ca = pa | {normalise_key(x) for x in a.context_places if normalise_key(x)}
        cb = pb | {normalise_key(x) for x in b.context_places if normalise_key(x)}
        ctx = sorted(ca & cb)
        if ctx:
            w = _bits(freq.places.get(ctx[0], 0), freq.n, 5.0) if freq.n else _NO_CORPUS["place"]
            add("context", f"record at {ctx[0]}", max(w, 2.0))
    if shared:
        # Capped low on purpose. Place counts come from the harvest, and a harvest is
        # filtered to one surname — so the commune that family lived in looks rare
        # simply because the corpus is mostly them. Unlike the surname, there is no
        # population figure to correct it with, so the weight is bounded instead of
        # trusted.
        w = _bits(freq.places.get(shared[0], 0), freq.n, 5.0) if freq.n else _NO_CORPUS["place"]
        add("place", f"place {shared[0]}", max(w, 2.0))
    if a.birth_place and b.birth_place and normalise_key(a.birth_place) == normalise_key(b.birth_place):
        add("place", f"birthplace {a.birth_place}", 4.0)

    # --- occupation ---
    if a.occupation and b.occupation and normalise_key(a.occupation) == normalise_key(b.occupation):
        add("role", f"occupation {a.occupation}", 3.0)

    # --- kin ---
    # The identifier the rule always named and the scorer never had. Two Petrus
    # Bundervoets born the same decade in the same commune are genuinely hard to tell
    # apart; the one whose mother is Livina Stockman is not hard to tell apart at all.
    #
    # Only relatives in the same bucket are compared, and the weight follows the same
    # rule as everything else — what the agreement would cost to get by chance.
    kin_bits, kin_labels, kin_anchored = 0.0, [], False
    # Named apart from the `same_surname`/`shared` above on purpose. These are facts about
    # a RELATIVE; those are facts about the two people being compared. Reusing the names
    # here rebound them, and the surname veto below — which reads `same_surname` — was
    # then answering a question about somebody's father instead. See the note there.
    for bucket, surname_key, givens in a.kin:
        for o_bucket, o_surname, o_givens in b.kin:
            if bucket != o_bucket:
                continue
            shared_givens = givens & o_givens
            kin_surname_agrees = bool(surname_key) and surname_key == o_surname
            if not shared_givens and not kin_surname_agrees:
                continue
            bits = sum(_bits(freq.givens.get(g, 0), freq.n, 8.0) if freq.n else _NO_CORPUS["given"]
                       for g in shared_givens)
            # A father shares his son's surname, so counting it again would be counting
            # the principal's own name twice. A mother's maiden name is new information
            # every time, which is why it is the classic second identifier.
            if kin_surname_agrees and surname_key != family_key(a.surname):
                bits += surname_weight(surname_key, freq).bits
            if bits:
                kin_bits += bits
                kin_labels.append(bucket)
                # A relative's SURNAME agreeing is the classic second identifier. A
                # relative's forename agreeing is not: Simonne, Maria and Joanna are
                # each a large fraction of the women in this material.
                # ...and only when that surname is NEW information. A son carries his
                # father's surname, so "the child's surname agrees" is the principal's
                # own name counted a second time. A mother's maiden name is the case
                # this is really for.
                if kin_surname_agrees and surname_key != family_key(a.surname):
                    kin_anchored = True
                break
    if kin_bits:
        seen = ", ".join(dict.fromkeys(kin_labels))
        cls = "kin" if kin_anchored else "kin-forename"
        add(cls, f"{seen} name{'s' if len(kin_labels) > 1 else ''}", min(kin_bits, 16.0))

    # --- vetoes ---
    # Defaults to rejecting, in the verifier's spirit. Only STATED values veto; a birth
    # year implied by an age in an act carries a year or two of slack and must never be
    # allowed to kill a true match on its own.
    if a.sex and b.sex and a.sex != b.sex:
        conflict.append("sex disagrees")
    # On the SPANS, not the years. `1920..1929` against a stated 1925 is not a conflict — it
    # is the range saying it does not know, which is the opposite of disagreeing.
    if a.stated_birth_year and b.stated_birth_year and _cannot_meet(a_birth, b_birth, slack=2):
        conflict.append(f"stated birth years {_show(a_birth)} vs {_show(b_birth)}")
    if (a.birth_date and b.birth_date and DAY.match(a.birth_date) and DAY.match(b.birth_date)
            and a.birth_date != b.birth_date):
        conflict.append(f"birth dates {a.birth_date} vs {b.birth_date}")
    # Both directions. This tested only a's death against b's birth, so `compare(x, y)` and
    # `compare(y, x)` could disagree about whether the pair was even possible — and callers
    # do pass them both ways round: act_coverage compares (target, mention) while
    # missing_children compares (mention, target).
    for died, born in ((a_death, b_birth), (b_death, a_birth)):
        if died[1] is not None and born[0] is not None and born[0] > died[1]:
            conflict.append("born after the other died")
            break
    # If the pair were one person, that person lived this long. Kept generous on
    # purpose — the point is to kill the grandfather-grafted-onto-grandson case, which
    # recurs in this material because the forename is reused every second generation,
    # and not to adjudicate anyone's actual longevity.
    # The SHORTEST lifespan the two spans allow, so the veto only fires when even that is
    # impossible: latest possible birth against earliest possible death.
    for birth, death in ((a_birth, b_death), (b_birth, a_death)):
        if birth[1] is not None and death[0] is not None and death[0] - birth[1] > MAX_LIFESPAN:
            conflict.append(f"implied lifespan {death[0] - birth[1]} years")
            break
    # The record's own year against the person's life. This catches what nothing else
    # can: an act that gives a participant no dates whatsoever still cannot name someone
    # who died two centuries before it was drawn up, or who was not yet born.
    # Again on the bound that makes it certain: the LATEST they could have died, and the
    # EARLIEST they could have been born.
    for (cand, other), death, birth in (((a, b), a_death, a_birth), ((b, a), b_death, b_birth)):
        if not other.event_year:
            continue
        if death[1] is not None and other.event_year - death[1] > MAX_POSTHUMOUS_MENTION:
            conflict.append(f"record of {other.event_year} is "
                            f"{other.event_year - death[1]} years after they died")
            break
        if birth[0] is not None and other.event_year < birth[0]:
            conflict.append(f"record of {other.event_year} predates their birth in {_show(birth)}")
            break

    # Reads the two names computed at the top, before any kin comparison. It has to: for
    # eight months the kin loop rebound `same_surname` to "this relative's surname agrees",
    # so a pair whose own surnames plainly disagreed cleared this veto whenever any one
    # relative matched. Measured over 100 people and 298,816 pairs it fired once, and on
    # the worst possible pair — Maria Anna Vandenhoven scored as Maria Theresia
    # Coekelberghs, at 21.6 bits and graftable, which is the exact identification a
    # verifier had already refuted in writing and retracted a record over
    # (research/labels.jsonl, act abl:2c0d71d9…). Latent, not harmless.
    surnames_disagree = bool(
        family_key(a.surname) and family_key(b.surname) and not same_surname and not same_phonetic
    )
    independent = sum(1 for c in classes if c in CLASSES)
    distinguishing = sum(bits for cls, _, bits in agree if cls != "name")
    return Match(
        a=a, b=b,
        bits=0.0 if conflict else score,
        distinguishing=0.0 if conflict else distinguishing,
        agree=agree,
        conflict=conflict,
        classes=classes,
        independent=independent,
        # The project's rule, not a threshold: two independent identifiers is the floor
        # for a graft, and no amount of accumulated score substitutes for it. The bits
        # only decide how far up the list it goes.
        # A surname disagreement is disqualifying, not merely unhelpful. Judocus
        # Bundervoet was matched to Judocus ROTIER and Edouard Dekeyser to Edouard BARBE,
        # each on a forename plus a date — two people who share nothing but a Christian
        # name and a decade. Where both sides state a surname and the two do not agree,
        # even phonetically, the pair can still be shown as a lead but must never be
        # graftable. Women recorded under a married name are the known cost of this, and
        # they are better handled as a lead than as a silent graft.
        graftable=(not conflict and independent >= 2 and distinguishing >= 6
                   and not surnames_disagree),
        band=("rejected" if conflict else
              "strong" if distinguishing >= 12 and independent >= 2 else
              "read the act" if distinguishing >= 6 and independent >= 2 else "noise"),
    )
