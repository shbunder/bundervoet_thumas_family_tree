"""Loading and interpreting the data.

Every tool goes through here, so there is one definition of what a person is rather
than four copies drifting apart.
"""

from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

from . import frontmatter

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
PEOPLE_DIR = DATA / "people"
ARTIFACTS_DIR = DATA / "artifacts"
SITE = ROOT / "site"

# The fields a person record may carry, in the order they are written.
FIELDS = [
    "id", "name", "surname", "sex", "birth", "death", "confidence", "occupation",
    "nickname", "line", "father", "mother", "siblings", "spouses", "sources",
]
EVENT_FIELDS = ["date", "place"]
# A marriage is an event too, so it is stored like one: `married` and `divorced` are
# dates in the grammar below, `place` is where the act was passed. `kind` separates a
# recorded marriage from a partnership that produced children without one — the
# difference is a fact about the couple, and inferring it from the wording of a note
# is how "wife" ends up printed under someone who never was one. `detail` survives for
# what no field can hold, but it may no longer carry a date, a place, or the position
# of the marriage in a sequence: those are fields now, or derived from list order.
# `confidence`, `source` and `note` are the same three a parent link carries — a marriage
# is a link too, and the vocabulary should not change with the role. `detail` stays for
# what the marriage fields cannot hold; `note` is why the LINK was drawn, which is a
# different thing and is what the page shows beside a red mark.
SPOUSE_FIELDS = ["id", "name", "kind", "confidence", "source", "note", "married", "place",
                 "divorced", "detail"]
SPOUSE_KINDS = ("marriage", "partnership")

# ---------- links ----------
# A link is a fact in its own right, so it carries its own confidence and its own
# citation. `father`, `mother` and each entry in `spouses` are all links.
#
# This is the same vocabulary as a person's `confidence`, deliberately, because it is the
# same question asked of a different object: how well is this KNOWN. On a person it grades
# their own facts; on a link it grades whether the two ends really belong together — and a
# parent documented to the day can still be the wrong parent. Two different objects, one
# scale.
#
# It also makes rule 2 checkable for the first time. "Every new parent link cites a source"
# was unenforceable while `sources` was a person-level list: the citation and the claim sat
# in the same file without being attached to each other, so nothing could answer *which*
# source established that this was the mother.
LINK_FIELDS = ["id", "confidence", "source", "note"]
# A sibling link, and the one relationship this project stores rather than derives.
#
# That is a real exception to "a relationship is never a field", and it is made safe by
# being GENERATED rather than by being forbidden. `familytree/edges.py` writes every
# derived sibship out as edges and the validator fails on a record that disagrees with what
# it would write — so the 994 redundant entries are a projection of the parent links,
# checked on every build, in the same way `dist/bundle.js` is. Correct a parent link and the
# sibling edges resting on it go stale loudly instead of quietly describing a family that
# changed. A copy nothing verifies is the failure the data model exists to prevent; a copy
# something verifies is a view.
#
# It also holds what no parent link can reach: an act naming two people brother and sister
# without naming a parent either can be grafted to. `antoine_vanald` states that case in its
# own prose — "she cannot be linked as a sibling while the parents themselves are only a
# frontier" — and until this field existed the answer was to lose the fact.
SIBLING_FIELDS = LINK_FIELDS
# `unk` is missing on purpose. On a person it means "we do not know their facts yet"; on a
# link there is no such state — a link whose existence is unknown is an absent link, and
# allowing the code would put a drawn edge and a nonexistent one in the same bucket.
EDGE_CONFIDENCE = ("doc", "sup", "fam", "asm")
# THE RULE THE WHOLE ARRANGEMENT RESTS ON: an assumed edge is evidence for nothing.
# `from_person` hides it from the scorer, so it can never become one of the two independent
# identifiers that licenses the next graft. Without that, a guess licenses a graft which
# licenses another, every link in the chain scoring as well-supported, and the error rate
# compounds down the line with nothing marking where it started.
#
# Only `asm`. Whether `fam` belongs here too is a real question — family testimony is one
# identifier, not two — but it is a separate one, it changes how 26 existing records score,
# and it should be settled by `evaluate.py report` rather than smuggled in with a storage
# change. Kept as a set so that decision is a one-line edit here.
NOT_EVIDENCE = ("asm",)
# Above this many people hanging off a single unverified edge, the validator says so.
# Sized at a couple of generations: below that a retraction is an afternoon's work, above
# it the guess is load-bearing and should be paid for with a document.
WEAK_EDGE_BLAST_RADIUS = 8
# An artifact is a saved primary document — a scan or photograph of an act. It is
# evidence, so it lives in data/ with the facts, not in docs/ with the writing about
# them, and it carries its own record in the same frontmatter format.
ARTIFACT_FIELDS = [
    "id", "file", "media", "bytes", "sha256", "title", "kind", "event", "date",
    "place", "repository", "collection", "source", "url", "accessed", "evidences",
]

# ---------- dates ----------
# A deliberately small grammar, so a date is queryable and sortable instead of being
# prose the next tool has to guess at:
#
#   1876-11-12   a day            1876-11   a month           1876   a year
#   ~1682        about            <1727     before            >1900  after
#   1575..1587   between two years
#
# Anything a source did not actually say is simply absent. There is no format for
# "probably March", because inventing one invites inventing the fact.
DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MONTH = re.compile(r"^\d{4}-\d{2}$")
YEAR = re.compile(r"^\d{4}$")
APPROX = re.compile(r"^~\d{4}$")
BEFORE = re.compile(r"^<\d{4}$")
AFTER = re.compile(r"^>\d{4}$")
RANGE = re.compile(r"^\d{4}\.\.\d{4}$")

_DATE_FORMS = (DAY, MONTH, YEAR, APPROX, BEFORE, AFTER, RANGE)

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def is_valid_date(s) -> bool:
    return isinstance(s, str) and any(p.match(s) for p in _DATE_FORMS)


def format_date(s: str | None) -> str:
    """The human form. The machine form is what is stored; this is only ever display."""
    if not s:
        return ""
    if DAY.match(s):
        y, m, d = s.split("-")
        return f"{int(d)} {MONTH_NAMES[int(m) - 1]} {y}"
    if MONTH.match(s):
        y, m = s.split("-")
        return f"{MONTH_NAMES[int(m) - 1]} {y}"
    if APPROX.match(s):
        return f"~{s[1:]}"
    if BEFORE.match(s):
        return f"before {s[1:]}"
    if AFTER.match(s):
        return f"after {s[1:]}"
    if RANGE.match(s):
        return s.replace("..", "–")
    return s


def year_of(date: str | None) -> int | None:
    """The year in any date the grammar allows, or None. Ranges give their start."""
    if not date:
        return None
    m = re.search(r"(\d{4})", str(date))
    return int(m.group(1)) if m else None


def point_year(date: str | None) -> int | None:
    """The year a date actually ASSERTS, or None if it only bounds one.

    `year_of` reads a number out of any date form, which is right for sorting and wrong
    for arithmetic. `<1673` means "born at some unknown time before 1673" — subtracting
    it from a child's birth year produced "mother at age -6" for a record that was
    never in conflict with anything. A bound is not a measurement, and the difference is
    invisible until something does sums with it.

    `~1682` is a point estimate, so it is returned; callers doing arithmetic on it are
    expected to allow the slack an "about" carries — `year_span` is how much.
    """
    if not date:
        return None
    s = str(date)
    if DAY.match(s) or MONTH.match(s) or YEAR.match(s) or APPROX.match(s):
        return year_of(s)
    return None


# The bounds a human life is held to. All four are deliberately looser than what is
# plausible: the point is to catch a graft that is off by a GENERATION — the recurring
# failure in this material, where a forename returns every second generation — and never
# to adjudicate an unusual but real life.
#
# They live here because both readers need the same numbers. `match.py` vetoes on them and
# `check_data._check_plausibility` warns on them, and each had its own copy: MIN_PARENT_AGE
# was inline in the validator until it was hoisted, and MAX_LIFESPAN stayed behind in
# `match.py` with the validator hardcoding 110 eleven lines below the import that would
# have given it the name. Two copies of a bound is how they drift.
MIN_PARENT_AGE = 13
MAX_LIFESPAN = 110
# A father can father a child until he dies; a mother cannot. Split, because a single
# bound wide enough for both catches neither.
MAX_MOTHER_AGE = 50
MAX_FATHER_AGE = 75


# How far an "about" year may be out, either way.
#
# REASONED, NOT MEASURED, and it should say so. The obvious instrument — compare a stated
# birth year against the one an act's age implies, over the whole corpus — cannot be built,
# because `corpus.py` only computes `implied_birth_year` when no birth year was stated, so
# the two are mutually exclusive by construction and there are zero pairs to compare. (Ages
# themselves are common enough for it to have been worth checking: 15.4% of 387,987 sampled
# mentions carry one, 54.6% in Leuven's civil acts.)
#
# So it is sized against the error this project has actually suffered instead. Every
# near-miss in the log is off by a GENERATION — the Gustaaf who was a Gustavus one
# generation out, the grandfather grafted onto the grandson, which recurs here because the
# forename is reused every second generation. That is 25 to 30 years. Five keeps the veto
# lethal against all of those while not firing on the few years an age in a 19th-century
# civil act is routinely out by. Same spirit as MAX_LIFESPAN: generous on purpose, because
# a veto is for killing impossibilities and not for adjudicating estimates.
APPROX_SLACK = 5


def year_span(date: str | None) -> tuple[int | None, int | None]:
    """The years a date does not rule out, as (earliest, latest), both inclusive.

    `point_year` says what a date asserts. This says what it PERMITS, which is the
    question every veto actually asks — and asking the other one is a bug that costs
    recall in silence.

    `year_of` flattens each form below to a single number, so `1920..1929` became "1920",
    `stated_birth_year` was set from the mere presence of a date, and an act stating any
    year in the range a record itself declares was then REJECTED as a conflict with that
    range. Gustaaf's birth is recorded `1920..1929`; acts stating 1923, 1925 and 1929
    were all vetoed against him, and he is one of the people this project most needs to
    find in a foreign register. 81 of 434 records carry a non-point date, so this was not
    an edge case.

    Bounds are read INCLUSIVELY at year granularity, which is both the truthful reading
    and the conservative one. The grammar has no `<1946-05-09`, only `<1946`, so a source
    saying "died before 9 May 1946" can only be written `<1946` — and that has to mean
    "died in 1946 or earlier", or the encoding would assert something the source did not.
    Being the wider reading, it also vetoes less, which is the safe direction for a bound.

    (None, None) means the date rules nothing out — including the case of no date at all.
    """
    if not date:
        return (None, None)
    s = str(date)
    if BEFORE.match(s):
        return (None, year_of(s))
    if AFTER.match(s):
        return (year_of(s), None)
    if RANGE.match(s):
        lo, hi = s.split("..")
        return (int(lo), int(hi))
    if APPROX.match(s):
        y = year_of(s)
        return (y - APPROX_SLACK, y + APPROX_SLACK)
    y = year_of(s)
    return (y, y) if y else (None, None)


def is_approximate(date: str | None) -> bool:
    """Whether a date carries slack — an `~1682` should not be held to the same
    tolerance as a registered day."""
    return bool(date) and bool(APPROX.match(str(date)))


def sort_key(date: str | None) -> str:
    """A date reduced to something that sorts as a plain string.

    The browser reads a sibship in birth order, and the only alternative to sending it
    this is a second copy of the date grammar in JavaScript, drifting from this one.
    The qualifier is stripped and whatever precision the date has is kept, which sorts
    correctly because a year is a prefix of its own months: "1876" < "1876-03" <
    "1876-11-12". A bound (`<1727`) sorts on its year — that is an ordering, not a
    claim, and nothing but the order of cards on a row depends on it.
    """
    m = re.match(r"^[~<>]?(\d{4}(?:-\d{2}(?:-\d{2})?)?)", str(date or ""))
    return m.group(1) if m else ""


def event_text(e: dict | None) -> str:
    if not e:
        return ""
    return " ".join(x for x in (format_date(e.get("date")), e.get("place")) if x)


def marriage_text(s: dict) -> str:
    """The line shown beside a spouse's name. Derived from the fields, never stored.

    The renderer must not have to know that `~1745` means "about" — that is the same
    reason `display_dates` lives here, and it is what keeps `assets/` free of any
    opinion about what a date says.
    """
    bits = []
    where_when = ", ".join(x for x in (s.get("place"), format_date(s.get("married"))) if x)
    if s.get("kind") == "partnership":
        bits.append("partner" + (f", {where_when}" if where_when else ""))
    elif where_when:
        bits.append(f"m. {where_when}")
    if s.get("divorced"):
        bits.append(f"divorced {format_date(s['divorced'])}")
    if s.get("detail"):
        bits.append(s["detail"])
    return " · ".join(bits)


def display_dates(p: dict) -> str:
    """The line shown under a name. Derived, never stored — one fact, one place."""
    b, d = event_text(p.get("birth")), event_text(p.get("death"))
    if b and d:
        return f"{b} – {d}"
    if b:
        return f"b. {b}"
    if d:
        return f"d. {d}"
    return ""


# ---------- loading ----------


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def on_disk() -> list[str]:
    return sorted(f.stem for f in PEOPLE_DIR.glob("*.md"))


def load_config() -> dict:
    """data/ holds facts; site/ holds the words the page shows.

    Keeping them apart is what stops a heading or a label being mistaken for
    something a record asserts.
    """
    meta = _read_json(DATA / "meta.json")
    site = _read_json(SITE / "labels.json")
    return {
        "roster": on_disk(),
        "meta": meta,
        # The explorer opens on the first root; a forest just has more of them.
        "root": meta["roots"][0],
        "lineages": _read_json(DATA / "lineages.json")["lineages"],
        "site": site,
        "groups": site["groups"],
    }


def load_forenames() -> dict[str, list[list[str]]]:
    """Forenames that are one name in another language, split by sex. See the file's own note.

    Returned without the `_comment` key so callers iterate groups and never a paragraph.
    """
    raw = _read_json(DATA / "forenames.json")
    return {k: v for k, v in raw.items() if not k.startswith("_")}


def normalise_links(data: dict) -> dict:
    """`father: lucien_vincke` and the four-line block form become one shape in memory.

    The scalar stays legal in the FILES, and that is not a concession — 646 of the tree's
    parent links are simply known, and making each of them a three-line block to say so
    would add two thousand lines of ceremony to 329 records for no fact gained. A block is
    for a link that has something to declare.

    But two shapes in memory is how this kind of change goes quietly wrong. `if
    p.get("father")` is truthy for both, and `p["father"] == pid` silently goes False
    against a dict — a missed reader would not raise, it would just stop finding parents,
    which looks exactly like a tree with fewer links in it. So the shape is settled once,
    here, at the door the records come through, and `link_of` tolerates the scalar anyway
    for the dicts that never pass this way.

    An unqualified link has NO confidence — not the person's, and not a default. The first
    draft inherited from the record, which reads well and is wrong twice over. It invents a
    grade no source stated, against rule 5. And a marriage is one link written on two
    records: inheriting made his `doc` and her `sup` disagree about the same act, which the
    validator caught as 22 errors on a tree that had nothing wrong with it.

    So absent means "not yet distinguished from the record it sits on", which is exactly
    what the tree meant before links could carry a confidence at all. The scorer reads it as
    it always has, nothing is fabricated, and the 646 existing links migrate untouched.
    """
    for role in ("father", "mother"):
        if data.get(role) and not isinstance(data[role], dict):
            data[role] = {"id": data[role]}
    return data


def link_of(p: dict, role: str) -> dict:
    """The link block for `role`, or an empty one. Never None, so callers can read a field
    off it without first asking whether the link exists.

    Tolerates the scalar form as well as the block, even though `load_person` has already
    normalised everything it read. Belt and braces, and the braces earned their place
    immediately: not every person dict comes through the loader — tests build them inline,
    and so could any tool assembling a synthetic record — and a strict accessor answered
    None for those, which is a parent link vanishing in silence. That is the same class of
    bug the normalisation exists to prevent, so the accessor must not reintroduce it.
    """
    value = p.get(role)
    if isinstance(value, dict):
        return value
    return {"id": value} if value else {}


def parent_id(p: dict, role: str) -> str | None:
    """The id at the far end of a parent link. What almost every reader wants."""
    return link_of(p, role).get("id")


def edge_confidence(p: dict, role: str) -> str | None:
    return link_of(p, role).get("confidence")


def is_weak(p: dict, role: str) -> bool:
    """Whether this link is one the scorer must not read as evidence. See NOT_EVIDENCE."""
    return edge_confidence(p, role) in NOT_EVIDENCE


def stated_siblings(p: dict) -> list[dict]:
    """The sibling links a record states outright. Malformed entries are dropped rather
    than raised on — the renderer and the scorer read this too, and only the validator is
    in a position to complain about them."""
    return [s for s in (p.get("siblings") or []) if isinstance(s, dict) and s.get("id")]


def derived_siblings(people: dict, pid: str, children: dict | None = None) -> list[str]:
    """Everyone born of either of the same parents. Half-siblings are in — they are
    siblings, and which kind is a question for the relation namer, not for membership."""
    children = children if children is not None else children_index(people)
    p = people.get(pid) or {}
    out: list[str] = []
    seen = {pid}
    for role in ("father", "mother"):
        for kid in children.get(parent_id(p, role) or "", []):
            if kid not in seen:
                seen.add(kid)
                out.append(kid)
    return out


def siblings_of(people: dict, pid: str, children: dict | None = None) -> list[str]:
    """Everyone recorded as this person's sibling, derived first and stated second.

    One list, because a reader does not care which mechanism knew it, and because the two
    cannot overlap: a stated link between two people who already share a parent fails the
    build.
    """
    out = derived_siblings(people, pid, children)
    seen = set(out) | {pid}
    for s in stated_siblings(people.get(pid) or {}):
        if s["id"] in people and s["id"] not in seen:
            seen.add(s["id"])
            out.append(s["id"])
    return out


def firm_parent(p: dict, role: str) -> str | None:
    """The parent link, or None where the link itself is only assumed.

    Everything that reads a link as EVIDENCE goes through here; everything that reads it to
    draw or count the tree reads the id. That split is the safety property — see the note
    on NOT_EVIDENCE.
    """
    return None if is_weak(p, role) else parent_id(p, role)


def load_person(person_id: str) -> dict:
    text = (PEOPLE_DIR / f"{person_id}.md").read_text(encoding="utf-8")
    data, body = frontmatter.parse(text, f"{person_id}.md")
    if body:
        data["note"] = body
    return normalise_links(data)


def load_people(roster: list[str] | None = None) -> dict[str, dict]:
    ids = roster if roster is not None else load_config()["roster"]
    return {pid: load_person(pid) for pid in ids}


def load_artifacts() -> dict[str, dict]:
    if not ARTIFACTS_DIR.is_dir():
        return {}
    out = {}
    for f in sorted(ARTIFACTS_DIR.glob("*.md")):
        data, body = frontmatter.parse(f.read_text(encoding="utf-8"), f.name)
        if body:
            data["note"] = body
        out[f.stem] = data
    return out


# ---------- names ----------
# `name` is the name as the record wrote it, particles, spelling and all. Which part
# of it is the family name cannot be computed: a quarter of these names carry a
# particle ("Van den Broucke", "Vande Woestijne", "'t Jonck"), so the last word is
# the wrong answer often enough to matter, and the exporter's particle heuristic
# silently produced no surname at all for six people. So `surname` is stated, not
# guessed — and it is the only extra name field, because "Christianus Josephus" is
# one compound given name, not a first name plus a middle name.


def given_names(p: dict) -> str:
    """The name with the surname removed. Derived, never stored.

    The surname is usually last, but not always: "Marie Anne Catherine Quinart
    (Kinart)" ends with a variant spelling, so cutting only from the end left the
    surname sitting in the given names as well.
    """
    surname = p.get("surname")
    if not surname:
        return p["name"]
    at = p["name"].rfind(surname)
    if at < 0:
        return p["name"]
    return re.sub(r"\s{2,}", " ", p["name"][:at] + p["name"][at + len(surname):]).strip()


# Memoised because the scorer calls it about seven times per comparison and a full
# `research.py acts` run makes 350,000 comparisons: 2.5 million calls, of which 31,681
# were distinct. The cache is unbounded on purpose — the key space is the set of
# surnames the corpus actually contains, which grows like the vocabulary of a corpus
# rather than like the corpus, so a bounded LRU would thrash on a scanning workload for
# no saving worth having. See the same note on `normalise_key` and `phonetic`.
@lru_cache(maxsize=None)
def family_key(surname: str | None) -> str:
    """The grouping key.

    Spelling varies by the record a person was found in — the same Oostende family is
    written "Dekeyser" and "De Keyser", and both are kept on purpose — so grouping
    compares surnames with case, spacing and accents removed. This is what lets
    objective 3 ask "who are all the Bundervoets?" without a hand-maintained list.
    """
    s = unicodedata.normalize("NFD", (surname or "").lower())
    return re.sub(r"[^a-z]", "", s)


# ---------- what the tree contains ----------


def children_index(people: dict) -> dict[str, list[str]]:
    """parent id -> the ids of their children. Derived, like every downward view.

    Here rather than in `frontier.py`, where it started: it is a fact about the records,
    not about the queue, and five tools were importing the ranked-queue module to get it
    while `check_data` and `census` each rebuilt it inline — with one of the two copies
    quietly omitting the "parent exists" guard.
    """
    children: dict[str, list[str]] = {}
    for pid, p in people.items():
        for role in ("father", "mother"):
            parent = parent_id(p, role)
            if parent and parent in people:
                children.setdefault(parent, []).append(pid)
    return children


def surname_counts(people: dict) -> dict[str, tuple[int, str]]:
    """family key -> (how many carry it, one spelling of it as written).

    The key is folded so Bostyn and Bostin are one family; the spelling comes back with
    it because every caller has to print something a person would recognise.
    """
    counts: dict[str, tuple[int, str]] = {}
    for p in people.values():
        if p.get("surname"):
            key = family_key(p["surname"])
            n, name = counts.get(key, (0, p["surname"]))
            counts[key] = (n + 1, name)
    return counts


def ancestors_of(people: dict, pid: str, skip: set[tuple[str, str]] | None = None) -> set[str]:
    """Everyone above someone in the tree. The person themselves is not in it.

    `skip` suppresses named `(person, role)` edges. That is how the cost of a weak link is
    measured — walk the pedigree once as it stands and once with the edge cut, and the
    difference is exactly who is in the tree only because of that guess.
    """
    seen: set[str] = set()
    stack = [pid]
    while stack:
        cur = stack.pop()
        for role in ("father", "mother"):
            if skip and (cur, role) in skip:
                continue
            parent = parent_id(people[cur], role)
            if parent in people and parent not in seen:
                seen.add(parent)
                stack.append(parent)
    return seen


# ---------- weak edges ----------


def weak_edges(people: dict, roots: list[str]) -> list[dict]:
    """Every link the scorer will not read as evidence, with what it is carrying.

    `at_stake` is the honest price of the guess: the people who are in the tree only
    because of this edge and who would leave with it if it were retracted. It is measured
    by walking from the roots with the edge cut, not counted from the parent's own
    ancestors — that would double-count everyone the tree also reaches by another line, and
    pedigree collapse means some of them genuinely are reached twice.

    Derived on every call and never stored. What an edge costs to be wrong is a fact about
    the tree around it, so it changes when a second route to the same ancestor is found
    without the edge itself changing at all.
    """
    live = [r for r in roots if r in people]
    full: set[str] = set()
    for r in live:
        full |= ancestors_of(people, r)

    out: list[dict] = []
    for pid, p in sorted(people.items()):
        for role in ("father", "mother"):
            if not (parent_id(p, role) and is_weak(p, role)):
                continue
            cut: set[str] = set()
            for r in live:
                cut |= ancestors_of(people, r, skip={(pid, role)})
            parent = parent_id(p, role)
            link = link_of(p, role)
            out.append({
                "person": pid,
                "name": p.get("name", pid),
                "link": role,
                "parent": parent,
                "parent_name": (people.get(parent) or {}).get("name", parent),
                "confidence": link.get("confidence"),
                "source": link.get("source") or "",
                "note": link.get("note") or "",
                # Everyone the edge is holding on. Empty when the person themselves is not
                # reachable from a root — the edge is real, it just is not yet carrying any
                # part of the answer.
                "at_stake": sorted(full - cut),
                # A guess resting on a guess. This is the compounding the scorer is
                # protected from, surfacing in the shape of the tree instead: the upper link
                # was reasoned about as if the lower one were settled, because on the page
                # it looks exactly like a settled one.
                "stacked": bool(parent and any(
                    is_weak(people.get(parent) or {}, r) for r in ("father", "mother"))),
            })
    return out


def census(people: dict, config: dict) -> dict:
    """How many people the tree holds, split by how they relate to the roots.

    These are the objectives, counted: direct ancestors is objective 1, blood
    relatives off that line is objective 2, and the rest married in. It is derived
    here, once, and every place that shows a number reads it — the landing page
    through the build, the tree's subtitle through the bundle. A count written into a
    page by hand is a fact with no source that goes quietly wrong the next time
    somebody is added, which is the same failure as a hand-kept list.

    The three groups are the ones `assets/js/kinship.js` sorts the index into, and the
    index's own headings still count their buckets — so if these two ever disagreed,
    the subtitle and the heading below it would say different things on one screen.

    `earliest` is the oldest birth year in the tree; `documented` the oldest resting on
    a record someone actually read. They are far apart, and only one of them may be
    called documented.
    """
    meta = config["meta"]
    roots = [r for r in (meta.get("roots") or [config.get("root")]) if r in people]

    ancestors: set[str] = set()
    for root in roots:
        ancestors |= ancestors_of(people, root)
    ancestors -= set(roots)

    children = children_index(people)

    # Blood is the roots, everyone above them, and everyone descended from any of
    # those — an ancestor's sibling's grandchild is a blood relative (objective 2).
    #
    # A STATED sibling is blood too, and their descendants with them. Reached through the
    # same closure rather than a pass of its own: a stated sibling's child is as much a
    # first cousin as a derived sibling's, and the tree only knows the two apart because
    # one of them had a parent that could be grafted.
    blood = set(roots) | ancestors
    queue = list(blood)
    while queue:
        at = queue.pop()
        for kin in children.get(at, []) + [s["id"] for s in stated_siblings(people.get(at) or {})]:
            if kin in people and kin not in blood:
                blood.add(kin)
                queue.append(kin)

    def earliest_birth(pool: list[dict]) -> int | None:
        years = [year_of(p["birth"]["date"]) for p in pool if (p.get("birth") or {}).get("date")]
        return min((y for y in years if y), default=None)

    return {
        "total": len(people),
        "ancestors": len(ancestors),
        "relatives": len(blood - ancestors),
        "others": len(people) - len(blood),
        "earliest": earliest_birth(people.values()),
        "documented": earliest_birth([p for p in people.values() if p.get("confidence") == "doc"]),
    }


# ---------- the shape the browser reads ----------
# The site loads a generated bundle, so the display strings are computed once here
# rather than in the renderer, and assets/ stays free of any logic about what a date
# means.
_source_titles: dict[str, str] = {}


def set_source_titles(mapping: dict[str, str]) -> None:
    """Titles for the registry ids, so records can cite `tree-isavdw` instead of
    repeating "Geneanet tree isavdw (Rijksarchief scans)" twenty-five times."""
    global _source_titles
    _source_titles = mapping


def to_browser_record(p: dict, people: dict | None = None) -> dict:
    """The record the browser reads. `people` is optional and only affects the sibling
    links: deciding whether one is derivable needs the OTHER person's parents, and without
    it every stated sibling ships — correct, just larger than it needs to be."""
    people = people or {}
    out = {
        "id": p["id"],
        "name": p["name"],
        "dates": display_dates(p),
        "confidence": p.get("confidence"),
    }
    # Both derived here rather than in the renderer, so assets/ never has to know
    # what a particle is.
    if p.get("surname"):
        out["surname"] = p["surname"]
        out["family"] = family_key(p["surname"])
    if p.get("sex"):
        out["sex"] = p["sex"]
    if p.get("birth"):
        out["born"] = event_text(p["birth"])
        # What the browser sorts a sibship by. Absent when the birth date is, and the
        # renderer puts those last rather than guessing a position for them.
        if sort_key(p["birth"].get("date")):
            out["order"] = sort_key(p["birth"].get("date"))
    if p.get("death"):
        out["died"] = event_text(p["death"])
    for field in ("occupation", "nickname", "line"):
        if p.get(field):
            out[field] = p[field]
    # `father` and `mother` stay plain ids across the wire. The page is a reader of the
    # tree, not an editor of it, and flattening here means the renderer keeps asking the
    # one question it has always asked. What a link declares about itself travels
    # separately, below, and only when there is something to declare.
    for role in ("father", "mother"):
        if parent_id(p, role):
            out[role] = parent_id(p, role)
    # Only the links a reader needs warning about. `doc`/`sup`/`fam` edges are the ordinary
    # case and shipping them would put a badge on almost every card, which is how a warning
    # stops being read. The note comes too: a red edge whose reason lives in a research log
    # nobody reading the tree will open is an unexplained doubt, and that is a worse artefact
    # than either a firm link or no link at all.
    weak = {
        role: {k: v for k, v in (("confidence", edge_confidence(p, role)),
                                 ("note", link_of(p, role).get("note")),
                                 ("source", _source_titles.get(link_of(p, role).get("source"),
                                                               link_of(p, role).get("source"))))
               if v}
        for role in ("father", "mother")
        if parent_id(p, role) and is_weak(p, role)
    }
    if weak:
        out["links"] = weak
    # Only the sibling links the page cannot work out for itself: the assumed ones, which
    # need marking, and the ones no shared parent reaches, which the browser has no other
    # route to. The records carry all 994 edges — that is what makes a record readable on
    # its own and checkable against the parent links — but shipping the derivable ones would
    # put the same fact in the bundle twice and spend bytes on every page load telling the
    # renderer something it already computes in a loop it already runs.
    shipped = []
    for s in stated_siblings(p):
        assumed = s.get("confidence") in NOT_EVIDENCE
        mine = {parent_id(p, r) for r in ("father", "mother")} - {None}
        theirs = {parent_id(people.get(s["id"]) or {}, r) for r in ("father", "mother")} - {None}
        if assumed or not (mine & theirs):
            shipped.append({k: v for k, v in (
                ("id", s["id"]),
                ("weak", assumed or None),
                ("note", s.get("note") if assumed else None),
            ) if v})
    if shipped:
        out["siblings"] = shipped
    # The marriage fields are folded into one display line here, for the same reason
    # birth and death are. `kind` goes across as itself, because the page has to say
    # "partner" rather than "wife" and that is a fact, not a formatting choice.
    if p.get("spouses"):
        out["spouses"] = [
            {k: v for k, v in (
                ("id", s.get("id")),
                ("name", s.get("name")),
                ("kind", s.get("kind")),
                ("detail", marriage_text(s)),
                # Same rule as the parent links: sent only when the marriage itself is the
                # assumption, so the mark means one thing wherever it appears.
                ("weak", s.get("confidence") in NOT_EVIDENCE or None),
                ("note", s.get("note") if s.get("confidence") in NOT_EVIDENCE else None),
            ) if v}
            for s in p["spouses"]
        ]
    # The records cite the registry by id; the browser wants something readable.
    # Resolving here keeps the citation in one place and the prose out of the data.
    if p.get("sources"):
        out["source"] = "; ".join(_source_titles.get(s, s) for s in p["sources"])
    if p.get("note"):
        out["note"] = p["note"]
    return out
