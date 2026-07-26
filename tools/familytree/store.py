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

DB = HARVEST / "corpus.db"

SCHEMA = """
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
-- Where the act lives, not the act. See the note on duplication above.
CREATE TABLE acts (id TEXT PRIMARY KEY, path TEXT, offset INTEGER, length INTEGER);
CREATE TABLE mentions (ref TEXT PRIMARY KEY, act_id TEXT, pid TEXT, surname_key TEXT);
CREATE TABLE blocks (key TEXT, ref TEXT);
CREATE TABLE freq (kind TEXT, value TEXT, n INTEGER);
CREATE INDEX blocks_key ON blocks (key);
CREATE INDEX mentions_surname ON mentions (surname_key);
CREATE INDEX freq_lookup ON freq (kind, value);
"""


def signature() -> str:
    """What the index was built from. Any change to any harvest file changes this.

    Size and mtime rather than a content hash: hashing 284 MB on every command to decide
    whether to read it would cost more than the read. A harvest only ever appends, so a
    file whose size and mtime both match has not changed in any way this cares about.
    """
    if not ACTS_DIR.is_dir():
        return "empty"
    parts = []
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
                        mention_rows.append((ref, act.id, m.pid, skey))
                        for key in block_keys(from_mention(m)):
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
    # Renamed into place only once it is complete, so an interrupted build leaves the
    # previous index intact rather than a half-written one that reads as current.
    close()
    tmp.replace(DB)
    if verbose:
        print(f"\r  indexed {len(seen)} acts, {n} mentions.        ")
    return len(seen)


def _flush(db, acts_rows, mention_rows, block_rows) -> None:
    db.executemany("INSERT OR IGNORE INTO acts VALUES (?, ?, ?, ?)", acts_rows)
    db.executemany("INSERT OR IGNORE INTO mentions VALUES (?, ?, ?, ?)", mention_rows)
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


def candidate_count(c: Candidate) -> int:
    """How many corpus mentions could be this person, without building any of them.

    The frontier queue asks only this — `P(resolvable)` rises with the number of
    candidates the corpus holds — and answering it by materialising every candidate was
    most of what made the queue expensive. A count is one indexed query.
    """
    keys = block_keys(c)
    if not keys:
        return 0
    marks = ",".join("?" * len(keys))
    with _connect() as db:
        row = db.execute(
            f"SELECT count(DISTINCT ref) FROM blocks WHERE key IN ({marks}) AND ref <> ?",
            [*keys, c.ref],
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

    by_path: dict[str, list[tuple[int, int, str]]] = {}
    marks = ",".join("?" * len(missing))
    for aid, path, offset, length in db.execute(
        f"SELECT id, path, offset, length FROM acts WHERE id IN ({marks})", missing
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
    with _connect() as db:
        marks = ",".join("?" * len(keys))
        refs = {r for (r,) in db.execute(
            f"SELECT DISTINCT ref FROM blocks WHERE key IN ({marks})", keys)}
        refs.discard(c.ref)
        if not refs:
            return []
        acts = _hydrate(db, sorted({r.split("#", 1)[0] for r in refs}))
    out: list[Candidate] = []
    for ref in sorted(refs):
        act_id, _, pid = ref.partition("#")
        act = acts.get(act_id)
        if not act:
            continue
        mention = next((m for m in act.people if m.pid == pid), None)
        if mention is not None:
            out.append(from_mention(mention))
    return out
