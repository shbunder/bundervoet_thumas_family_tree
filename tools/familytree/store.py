"""The corpus as an index, so a question about one person does not cost the whole harvest.

`load_corpus` reads every held act, parses the JSON, and builds an `Act` and its
`Mention`s — 9.5 seconds and half a gigabyte for the 99,787 acts held today. That is the
right shape for the reports that genuinely scan everything (`research.py acts` compares
every mention against every frontier), and completely the wrong shape for the question
asked most often: what does the corpus say about THIS person. `link.py` pays the full
parse to look at a few dozen candidates, and pays it again for the next person.

The fix is the one the blocking already implies. `match.block_keys` says which records
could possibly be compared with which; if those keys live in an index, the answer is a
lookup instead of a scan. So this builds one — in SQLite, which is stdlib and therefore
costs the project nothing in the sense that matters here.

WHAT IT STORES, AND WHAT IT DOES NOT. Not the acts. The JSONL files in research/harvest/
remain the only copy of the evidence; the index holds byte offsets into them, so nothing
is duplicated, nothing can drift out of step with the harvest, and deleting the database
loses no data at all. What it does hold is the derived part that is expensive and pure:
the blocking keys, the per-mention fields the scorer compares, and the frequency tables
the rarity weights are counted from.

STALENESS IS NOT NEGOTIABLE. An index that silently lags the harvest would answer "no
candidates" for an act that was fetched an hour ago — the corpus form of reporting
`blocked` as `miss`, which is the failure this whole project is arranged against. So the
signature of every source file is stored alongside it, and `ensure()` rebuilds whenever
they disagree. A rebuild is the cost of one `load_corpus`, paid once instead of per
command.

This module decides nothing. It returns the same `Candidate` objects `match.py` compares,
carrying the same `Mention` and `Act`, so a candidate found through the index and one
found by scanning are indistinguishable — and `tools/tests/test_tools.py` pins that.
"""

from __future__ import annotations

import json
import sqlite3
from collections import Counter

from .corpus import ACTS_DIR, HARVEST, Frequencies, normalise_act, normalise_key
from .match import Candidate, block_keys, from_mention
from .people import year_span

DB = HARVEST / "corpus.db"

SCHEMA = """
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
-- Where the act lives, not the act. See the note on duplication above.
CREATE TABLE acts (id TEXT PRIMARY KEY, path TEXT, offset INTEGER, length INTEGER);
-- `birth_year`/`stated`/`sex` are here to be VETOED on before anything is read. See
-- candidates_for: they are the only two conflicts in `match.compare` that turn on scalars,
-- so they are the only two that can be applied without reproducing the scorer in SQL.
--
-- `cand` is the comparable Candidate itself, as JSON. Comparing used to mean rebuilding the
-- whole Act a mention belongs to — every participant, every edge, `unwrap_annotated` over
-- the entire record — to look at one person: a profile of forty frontiers showed 280,594
-- acts parsed to make 393,369 comparisons, 101 of 202 seconds in hydration and only 14 in
-- the scorer. The act is still the evidence and is still read from the JSONL, but only for
-- the handful of candidates that survive scoring.
CREATE TABLE mentions (ref TEXT PRIMARY KEY, act_id TEXT, pid TEXT, surname_key TEXT,
                       birth_year INTEGER, stated INTEGER, sex TEXT, cand TEXT);
CREATE TABLE blocks (key TEXT, ref TEXT);
CREATE TABLE freq (kind TEXT, value TEXT, n INTEGER);
"""

# Built AFTER the rows are in, not alongside them. `blocks` gets five or six keys per
# mention — about thirty million rows at a corpus of 1.7 million acts — and maintaining a
# B-tree across every one of those inserts was most of the build time: the first attempt
# at this scale was heading for twenty minutes, which is far too slow for something the
# validator triggers before a commit. Indexing a table that has stopped changing is one
# sequential sort instead.
INDEXES = """
CREATE INDEX blocks_key ON blocks (key);
CREATE INDEX mentions_surname ON mentions (surname_key);
CREATE INDEX freq_lookup ON freq (kind, value);
"""


# Every field of a Candidate that `match.compare` reads. Listed once, used by both
# directions, so a field added to the scorer and forgotten here fails the round-trip test
# rather than silently comparing as absent — which would look like a weaker match, not a
# bug. `mention` is deliberately absent: it holds the Act, which is what this avoids
# rebuilding, and callers who need the evidence hydrate it for the survivors.
_CAND_FIELDS = (
    "ref", "name", "surname", "given", "sex", "birth_year", "birth_date", "birth_place",
    "death_year", "death_date", "places", "context_places", "event_year", "occupation",
    "stated_birth_year", "birth_before",
)


def _dump(c: Candidate) -> str:
    d = {f: getattr(c, f) for f in _CAND_FIELDS}
    # kin is a list of (bucket, surname_key, frozenset(givens)); JSON has neither tuples
    # nor sets, so the shape is restored on the way back in.
    d["kin"] = [[b, s, sorted(g)] for b, s, g in c.kin]
    return json.dumps(d, ensure_ascii=False, separators=(",", ":"))


def _load(blob: str) -> Candidate:
    d = json.loads(blob)
    kin = [(b, s, frozenset(g)) for b, s, g in d.pop("kin", [])]
    return Candidate(**d, kin=kin)


# Bump whenever what is DERIVED changes shape or meaning: the blocking keys, the fields of
# the stored Candidate, how the frequencies are counted.
#
# Because the rest of `signature()` covers the harvest FILES, which catches every new act and
# not one change to the code that reads them. An index built by yesterday's `block_keys`
# reported itself current, and the docstring above promises the opposite — "an index that
# silently lags the harvest would answer 'no candidates' for an act that was fetched an hour
# ago", which is exactly as true of an act re-keyed an hour ago. Both of the last two changes
# here would have shipped a stale index: the particle-stripped prefix key changed which pairs
# are comparable, and adding `death_date` changed what a stored candidate carries.
#
#   1  the original: blocking keys + candidate fields as of the first index
#   2  particle-stripped adaptive prefix key; `death_date` on the stored Candidate
#   3  `birth_before` on the stored Candidate — the parent-predates-child bound, which is
#      derived from the act's edges at index time and cannot be recovered from the row later
FORMAT = 3


def signature() -> str:
    """What the index was built from — the harvest files AND the code that derived it.

    Size and mtime rather than a content hash: hashing 284 MB on every command to decide
    whether to read it would cost more than the read. A harvest only ever appends, so a
    file whose size and mtime both match has not changed in any way this cares about.
    """
    if not ACTS_DIR.is_dir():
        return f"v{FORMAT}|empty"
    parts = [f"v{FORMAT}"]
    for f in sorted(ACTS_DIR.glob("*.jsonl")):
        st = f.stat()
        parts.append(f"{f.name}:{st.st_size}:{st.st_mtime_ns}")
    return "|".join(parts)


_conn: sqlite3.Connection | None = None
# Acts already read off disk, kept because a whole-tree sweep asks 434 separate questions
# and the answers overlap heavily — one busy commune's marriage act is a candidate for
# every member of that family. Without this the same act is sought, read and re-parsed
# once per person who blocks against it, and the sweep costs more than the scan it
# replaced. Bounded: the point is to catch the overlap, not to rebuild `load_corpus` in
# memory one act at a time.
_acts: dict[str, object] = {}
_ACT_CACHE_MAX = 60000


def _connect() -> sqlite3.Connection:
    """One connection for the life of the process.

    Opening a new one per query is cheap in isolation and not cheap 1,300 times: each
    reopens the file, re-reads the header and rebuilds the page cache that the previous
    query had just warmed.
    """
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB)
    return _conn


def close() -> None:
    """Drop the connection and the act cache — used after a rebuild replaces the file."""
    global _conn
    if _conn is not None:
        _conn.close()
        _conn = None
    _acts.clear()


def is_current() -> bool:
    if not DB.exists():
        return False
    try:
        with _connect() as db:
            row = db.execute("SELECT value FROM meta WHERE key = 'signature'").fetchone()
    except sqlite3.DatabaseError:
        return False
    return bool(row) and row[0] == signature()


def build(verbose: bool = False) -> int:
    """Read the harvest once and write down everything derived from it.

    Deliberately a full rebuild rather than an incremental update. The harvest appends,
    so an incremental path is possible — and it is the kind of cleverness that produces an
    index quietly missing the acts fetched during the run that crashed. A rebuild takes
    about as long as the `load_corpus` every command pays today, and it is paid once.
    """
    DB.parent.mkdir(parents=True, exist_ok=True)
    tmp = DB.with_suffix(".db.building")
    tmp.unlink(missing_ok=True)

    surnames: Counter = Counter()
    givens: Counter = Counter()
    places: Counter = Counter()
    n = 0
    seen: set[str] = set()

    with sqlite3.connect(tmp) as db:
        # Safe to relax both: this is a scratch file built from scratch, and if the machine
        # dies mid-build the answer is to build it again, not to recover it. The real
        # database is only ever created by the atomic rename at the end.
        db.execute("PRAGMA journal_mode = OFF")
        db.execute("PRAGMA synchronous = OFF")
        db.executescript(SCHEMA)
        acts_rows, mention_rows, block_rows = [], [], []
        for path in sorted(ACTS_DIR.glob("*.jsonl")) if ACTS_DIR.is_dir() else []:
            offset = 0
            with path.open("rb") as f:
                for raw in f:
                    length = len(raw)
                    start = offset
                    offset += length
                    if not raw.strip():
                        continue
                    row = json.loads(raw)
                    # The same act is reachable from a surname harvest and a commune
                    # harvest both, and now from a whole-archive export as well.
                    if row["id"] in seen:
                        continue
                    seen.add(row["id"])
                    act = normalise_act(row)
                    acts_rows.append((act.id, path.name, start, length))
                    for m in act.people:
                        ref = f"{act.id}#{m.pid}"
                        skey = normalise_key(m.surname)
                        c = from_mention(m)
                        # Taken off the Candidate rather than the Mention, so what is stored
                        # is exactly what the scorer would compare — `birth_year` already
                        # falls back to the year implied by an age, and `stated` records
                        # which of the two it is, because only a stated year may veto.
                        mention_rows.append((ref, act.id, m.pid, skey, c.birth_year,
                                             1 if c.stated_birth_year else 0, c.sex,
                                             _dump(c)))
                        for key in block_keys(c):
                            block_rows.append((key, ref))
                        # The frequency tables, counted in the same pass rather than in a
                        # second one over the same 350,000 mentions.
                        n += 1
                        if skey:
                            surnames[skey] += 1
                        for g in (normalise_key(x) for x in (m.given or "").split()):
                            if g:
                                givens[g] += 1
                        place = normalise_key(act.place)
                        if place:
                            places[place] += 1
                    if len(acts_rows) >= 20000:
                        _flush(db, acts_rows, mention_rows, block_rows)
                        if verbose:
                            print(f"\r  indexed {len(seen)} acts…", end="", flush=True)
        _flush(db, acts_rows, mention_rows, block_rows)
        db.executemany("INSERT INTO freq VALUES ('surname', ?, ?)", surnames.items())
        db.executemany("INSERT INTO freq VALUES ('given', ?, ?)", givens.items())
        db.executemany("INSERT INTO freq VALUES ('place', ?, ?)", places.items())
        db.executemany("INSERT INTO meta VALUES (?, ?)",
                       [("signature", signature()), ("n", str(n)), ("acts", str(len(seen)))])
        if verbose:
            print(f"\r  indexed {len(seen)} acts, {n} mentions — building the lookups…",
                  end="", flush=True)
        db.executescript(INDEXES)
    # Renamed into place only once it is complete, so an interrupted build leaves the
    # previous index intact rather than a half-written one that reads as current.
    close()
    tmp.replace(DB)
    if verbose:
        print(f"\r  indexed {len(seen)} acts, {n} mentions.        ")
    return len(seen)


def _flush(db, acts_rows, mention_rows, block_rows) -> None:
    db.executemany("INSERT OR IGNORE INTO acts VALUES (?, ?, ?, ?)", acts_rows)
    db.executemany("INSERT OR IGNORE INTO mentions VALUES (?, ?, ?, ?, ?, ?, ?, ?)", mention_rows)
    db.executemany("INSERT INTO blocks VALUES (?, ?)", block_rows)
    acts_rows.clear()
    mention_rows.clear()
    block_rows.clear()


def ensure(verbose: bool = False) -> bool:
    """The index, current. Returns False when there is no corpus to index."""
    if not (ACTS_DIR.is_dir() and any(ACTS_DIR.glob("*.jsonl"))):
        return False
    if not is_current():
        if verbose:
            print("  the corpus has changed since the index was built — reindexing.")
        build(verbose)
    return True


# ---------- reading ----------


def frequencies() -> Frequencies:
    """The rarity tables, read rather than recounted.

    Identical to `corpus.frequencies()` by construction — the same counting loop, run at
    index time. That equivalence is what the test pins, because a divergence here would
    change every weight in the scorer without changing a single visible threshold.
    """
    f = Frequencies()
    with _connect() as db:
        row = db.execute("SELECT value FROM meta WHERE key = 'n'").fetchone()
        f.n = int(row[0]) if row else 0
        for kind, target in (("surname", f.surnames), ("given", f.givens), ("place", f.places)):
            for value, count in db.execute("SELECT value, n FROM freq WHERE kind = ?", (kind,)):
                target[value] = count
    return f


def held_under(surname: str) -> int:
    """How many mentions the corpus holds under a surname — the "nothing harvested here
    yet" check, without reading the corpus to answer it."""
    with _connect() as db:
        row = db.execute("SELECT count(*) FROM mentions WHERE surname_key = ?",
                         (normalise_key(surname),)).fetchone()
    return row[0] if row else 0


def acts_by_id(act_ids) -> dict:
    """Named acts, read straight out of the JSONL by offset.

    The lookup the gold standard needs. `evaluate.py` was resolving 48 label refs by
    building a dictionary of every mention in the corpus — fine at a hundred thousand acts,
    and at 1.7 million it is a three-minute wait to answer a question about 48 of them.
    """
    ids = sorted(set(act_ids))
    if not ids:
        return {}
    with _connect() as db:
        return _hydrate(db, ids)


# Past this many candidates the queue cannot tell the difference, so counting further is
# work bought for nothing. `frontier.discriminability` feeds the count through
# `1 - exp(-n/6)`, which is 0.9987 at forty and 1.0000 at sixty to four places — so a
# frontier with sixty candidates and one with five hundred score identically, and one of
# them was a count over a third of a million index rows. A capped count is reported as
# "60+" rather than as sixty, because a number that is not the number should say so.
CANDIDATE_CAP = 60

# Comfortably under SQLite's bound-variable limit, which is 999 on older builds. Anything
# that binds one variable per row has to batch — see _hydrate.
_SQL_VARS = 900


def _veto_sql(c: Candidate) -> tuple[str, list]:
    """`compare`'s two scalar vetoes, as a WHERE clause — the pre-filter that makes this
    affordable at a corpus of millions.

    Not an optimisation of the scoring: it is the same two conflicts, applied earlier. A
    Flemish surname now blocks against tens of thousands of acts, and `candidates_for` was
    reading and parsing every one of them so that `compare` could reject most on a stated
    birth year two centuries out. Rejecting those in the index instead means they are never
    read.

    CONSERVATIVE BY CONSTRUCTION, and it has to be: a pre-filter that drops a pair the
    scorer would have accepted is a missed link, invisible and unfindable. So each clause
    keeps every row unless the veto is CERTAIN — an unknown sex, an absent year and an
    implied-rather-than-stated year all survive, exactly as they do in `compare`, where
    only a stated value may veto. The equivalence is checked against the scanning route
    rather than argued.
    """
    where, params = "", []
    if c.sex:
        where += " AND (m.sex IS NULL OR m.sex = ?)"
        params.append(c.sex)
    if c.stated_birth_year:
        # The WINDOW the person's own date permits, widened by the same ±2 `compare` allows —
        # not a ±2 around a single number. This read `abs(m.birth_year - c.birth_year) <= 2`,
        # and `c.birth_year` is `year_of`, which turns `1920..1929` into 1920: every mention
        # of Gustaaf born 1923 or later was dropped in SQL before the scorer could see it,
        # so the false veto was enforced twice over and the second one left no trace at all.
        lo, hi = year_span(c.birth_date)
        if lo is None and hi is None and c.birth_year:
            lo = hi = c.birth_year
        if lo is not None or hi is not None:
            where += " AND (m.stated = 0 OR m.birth_year IS NULL OR (1"
            if lo is not None:
                where += " AND m.birth_year >= ?"
                params.append(lo - 2)
            if hi is not None:
                where += " AND m.birth_year <= ?"
                params.append(hi + 2)
            where += "))"
    return where, params


def candidate_count(c: Candidate, cap: int = CANDIDATE_CAP) -> int:
    """How many corpus mentions could be this person, without building any of them.

    The frontier queue asks only this — `P(resolvable)` rises with the number of
    candidates the corpus holds — and answering it by materialising every candidate was
    most of what made the queue expensive. A count is one indexed query, and a capped one
    stops as soon as the answer cannot change.
    """
    keys = block_keys(c)
    if not keys:
        return 0
    marks = ",".join("?" * len(keys))
    where, params = _veto_sql(c)
    with _connect() as db:
        row = db.execute(
            f"SELECT count(*) FROM (SELECT DISTINCT b.ref FROM blocks b "
            f"JOIN mentions m ON m.ref = b.ref "
            f"WHERE b.key IN ({marks}) AND b.ref <> ?{where} LIMIT ?)",
            [*keys, c.ref, *params, cap],
        ).fetchone()
    return row[0] if row else 0


def _hydrate(db, act_ids: list[str]) -> dict[str, object]:
    """The acts behind a candidate list, read out of the JSONL by offset.

    Only the acts a block key actually pointed at, which for a typical person is a few
    dozen out of a hundred thousand. This is the whole saving.
    """
    out: dict[str, object] = {}
    missing = []
    for aid in act_ids:
        if aid in _acts:
            out[aid] = _acts[aid]
        else:
            missing.append(aid)
    if not missing:
        return out

    # Chunked, because `IN (?,?,?…)` is one bound variable per id and SQLite caps those.
    # It held until a surname started blocking against tens of thousands of acts, which is
    # what a 1.7-million-act corpus does to a common Flemish name: "too many SQL variables",
    # from a query that had worked for months.
    by_path: dict[str, list[tuple[int, int, str]]] = {}
    for start in range(0, len(missing), _SQL_VARS):
        batch = missing[start:start + _SQL_VARS]
        marks = ",".join("?" * len(batch))
        for aid, path, offset, length in db.execute(
            f"SELECT id, path, offset, length FROM acts WHERE id IN ({marks})", batch
        ):
            by_path.setdefault(path, []).append((offset, length, aid))
    for path, wanted in by_path.items():
        with (ACTS_DIR / path).open("rb") as f:
            # In offset order, so a run of acts from one file is a forward walk through it
            # rather than a seek per act.
            for offset, length, aid in sorted(wanted):
                f.seek(offset)
                act = normalise_act(json.loads(f.read(length)))
                out[aid] = act
                if len(_acts) < _ACT_CACHE_MAX:
                    _acts[aid] = act
    return out


def candidates_for(c: Candidate) -> list[Candidate]:
    """Every corpus mention that shares a blocking key with this person.

    The same contract as `match.candidates_for` against an in-memory index, and the same
    keys — `block_keys` is imported rather than reimplemented, because two copies of the
    blocking rule drifting apart would mean the index and the scan disagree about what is
    even comparable.
    """
    keys = block_keys(c)
    if not keys:
        return []
    where, params = _veto_sql(c)
    marks = ",".join("?" * len(keys))
    with _connect() as db:
        rows = db.execute(
            f"SELECT DISTINCT b.ref, m.cand FROM blocks b JOIN mentions m ON m.ref = b.ref "
            f"WHERE b.key IN ({marks}){where}", [*keys, *params]).fetchall()
    # Straight from the stored Candidate — no act is read to make a comparison. The evidence
    # is fetched by `attach` for whatever survives scoring, which is a few hundred rather
    # than a few hundred thousand.
    return [_load(blob) for ref, blob in rows if ref != c.ref and blob]


def attach(candidates) -> list[Candidate]:
    """Give these candidates their act back, for the ones worth showing a person.

    Scoring does not need the act; reporting does — the url, the scan, the roles, the
    parent edges an act asserts. So it is read here, once, for the survivors only.
    """
    wanted = [c for c in candidates if c.mention is None]
    if not wanted:
        return list(candidates)
    acts = acts_by_id(c.ref.split("#", 1)[0] for c in wanted)
    for c in wanted:
        act_id, _, pid = c.ref.partition("#")
        act = acts.get(act_id)
        if act is not None:
            c.mention = next((m for m in act.people if m.pid == pid), None)
    return list(candidates)
