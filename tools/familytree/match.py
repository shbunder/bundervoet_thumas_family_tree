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

from .corpus import (
    Frequencies, Mention, frequencies, normalise_key, population, stated_kin,
    surname_population_count,
)
from .people import family_key, given_names, year_of

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
    places: list[str] = field(default_factory=list)
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
        death_year=act.year if act and act.type == "Overlijden" else None,
        places=[x for x in (m.birth_place, m.residence, act.place if act else None) if x],
        occupation=m.occupation,
        stated_birth_year=bool(m.birth_year),
        kin=[k for k in kin if k],
        mention=m,
    )


# ---------- blocking ----------


def block_keys(c: Candidate) -> list[str]:
    """Several passes over the same records. A pair that agrees on ANY key is compared;
    a pair that agrees on none never is. That is what keeps this off the O(n²) curve as
    the tree goes from 302 people to thousands and the corpus to millions."""
    ph = phonetic(c.surname)
    keys: list[str] = []
    if ph:
        keys.append(f"p:{ph}")
        keys.append(f"x:{ph[:6]}")  # catches truncated and extended forms
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


def compare(a: Candidate, b: Candidate, freq: Frequencies | None = None) -> Match:
    freq = freq if freq is not None else frequencies()
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
        add("name", f"forename{'s' if len(ga & gb) > 1 else ''}", min(given_bits, 10.0))

    # --- date ---
    # A day-level agreement between two independently written records is close to
    # conclusive on its own; a shared year in a commune of a few thousand is not.
    if a.birth_date and b.birth_date and len(a.birth_date) == 10 and a.birth_date == b.birth_date:
        add("date", f"birth {a.birth_date}", 12.0)
    elif a.birth_year and b.birth_year:
        gap = abs(a.birth_year - b.birth_year)
        if gap == 0:
            add("date", f"birth year {a.birth_year}", 6.0)
        elif gap <= 2:
            add("date", f"birth year ±{gap}", 2.0)
    if a.death_year and b.death_year and a.death_year == b.death_year:
        add("date", f"death year {a.death_year}", 5.0)

    # --- place ---
    # The class that did all the rejecting in the log so far: the Van Craenenbroeck and
    # Janssens false positives were every one of them right-name/wrong-province.
    pa = {normalise_key(x) for x in a.places if normalise_key(x)}
    pb = {normalise_key(x) for x in b.places if normalise_key(x)}
    shared = sorted(pa & pb)
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
    kin_bits, kin_labels = 0.0, []
    for bucket, surname_key, givens in a.kin:
        for o_bucket, o_surname, o_givens in b.kin:
            if bucket != o_bucket:
                continue
            shared = givens & o_givens
            same_surname = bool(surname_key) and surname_key == o_surname
            if not shared and not same_surname:
                continue
            bits = sum(_bits(freq.givens.get(g, 0), freq.n, 8.0) if freq.n else _NO_CORPUS["given"]
                       for g in shared)
            # A father shares his son's surname, so counting it again would be counting
            # the principal's own name twice. A mother's maiden name is new information
            # every time, which is why it is the classic second identifier.
            if same_surname and surname_key != family_key(a.surname):
                bits += surname_weight(surname_key, freq).bits
            if bits:
                kin_bits += bits
                kin_labels.append(bucket)
                break
    if kin_bits:
        seen = ", ".join(dict.fromkeys(kin_labels))
        add("kin", f"{seen} name{'s' if len(kin_labels) > 1 else ''}", min(kin_bits, 16.0))

    # --- vetoes ---
    # Defaults to rejecting, in the verifier's spirit. Only STATED values veto; a birth
    # year implied by an age in an act carries a year or two of slack and must never be
    # allowed to kill a true match on its own.
    if a.sex and b.sex and a.sex != b.sex:
        conflict.append("sex disagrees")
    if (a.stated_birth_year and b.stated_birth_year and a.birth_year and b.birth_year
            and abs(a.birth_year - b.birth_year) > 2):
        conflict.append(f"stated birth years {a.birth_year} vs {b.birth_year}")
    if (a.birth_date and b.birth_date and len(a.birth_date) == 10 and len(b.birth_date) == 10
            and a.birth_date != b.birth_date):
        conflict.append(f"birth dates {a.birth_date} vs {b.birth_date}")
    if a.death_year and b.birth_year and b.birth_year > a.death_year:
        conflict.append("born after the other died")
    # If the pair were one person, that person lived this long. Kept generous on
    # purpose — the point is to kill the grandfather-grafted-onto-grandson case, which
    # recurs in this material because the forename is reused every second generation,
    # and not to adjudicate anyone's actual longevity.
    for birth, death in ((a.birth_year, b.death_year), (b.birth_year, a.death_year)):
        if birth and death and death - birth > MAX_LIFESPAN:
            conflict.append(f"implied lifespan {death - birth} years")
            break

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
        graftable=not conflict and independent >= 2 and distinguishing >= 6,
        band=("rejected" if conflict else
              "strong" if distinguishing >= 12 and independent >= 2 else
              "read the act" if distinguishing >= 6 and independent >= 2 else "noise"),
    )
