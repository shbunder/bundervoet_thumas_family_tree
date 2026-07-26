"""The gold standard, in the library rather than inside the tool that scores it.

Every verifier ruling this project makes lands in `research/labels.jsonl`, and it is the
only labelled data it will ever produce. Until now exactly one thing read the file —
`evaluate.py report`, to measure the scorer — and nothing else did. So a refutation could
be written down, with its reasoning, by a verifier that had read the act, and the queue
that proposed the pair would propose it again the next night, and the night after.

That is not a hypothetical. `docs/autopilot-log.md` ends on it:

    All three remaining entries in `research.py children` are decisions this run already
    made: a graft it retracted, a link it declined, and a proposal that a man born 1847
    is a child born 1901. The refutations are recorded, with reasoning, and nothing reads
    them back. Left as it is, the next unattended run re-grafts the wrong Appolonia — and
    the run after that.

The search log has had this from the beginning: `research.py tried`, `untried` and `stale`
exist precisely so a miss is not walked twice. Rulings had no equivalent, and a ruling is
the more expensive thing to produce — a miss costs a query, a refutation costs someone
reading an act.

WHAT A REFUTATION SUPPRESSES. A label names a person and a mention, `<act-id>#<pid>`, and
that pair is suppressed. A label naming only the act — which 45 of the first 48 do —
suppresses every mention in that act for that person. That is deliberately broader than
what the label strictly says, and it is the right way round: the cost of being too broad
is one lead needing its label re-pointed at the right participant, and the cost of being
too narrow is the re-graft loop above. It is also announced rather than silent; the
reports say what they suppressed and why.

A refutation is never a fact about the world. It says a human looked and said no. So this
removes things from a QUEUE and never from the tree, and an ACCEPT label is not read here
at all — a queue that skipped what was already accepted would hide the corroboration.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache

from .people import ROOT

LABELS = ROOT / "research" / "labels.jsonl"

# Who decided, and how much that is worth. Kept explicit because a label from a read act
# and a label from a plausible-looking index page are not the same evidence, and a gold
# standard that mixes them silently measures the wrong thing.
BASES = ("act", "index", "tree", "reasoning")


@dataclass
class Label:
    person: str
    ref: str
    match: bool
    basis: str
    why: str
    date: str

    @property
    def act_id(self) -> str:
        return self.ref.split("#", 1)[0]

    @property
    def names_a_mention(self) -> bool:
        """Whether the ref says WHICH of an act's people the ruling was about."""
        return "#" in self.ref


def read_labels() -> list[Label]:
    if not LABELS.exists():
        return []
    out = []
    for line in LABELS.read_text(encoding="utf-8").split("\n"):
        if line.strip():
            r = json.loads(line)
            out.append(Label(r["person"], r["ref"], r["match"], r.get("basis", "reasoning"),
                             r.get("why", ""), r.get("date", "")))
    # Later labels supersede earlier ones for the same pair — corrections are first-class
    # here exactly as they are in the tree.
    latest: dict[tuple[str, str], Label] = {}
    for lab in out:
        latest[(lab.person, lab.ref)] = lab
    return list(latest.values())


@dataclass
class Refutations:
    """Every "no" a verifier has recorded, indexed for the question a queue asks."""

    # (person, mention ref) — the precise ones.
    mentions: dict[tuple[str, str], Label]
    # (person, act id) — the act-level ones, which cover every mention in that act.
    acts: dict[tuple[str, str], Label]

    def __len__(self) -> int:
        return len(self.mentions) + len(self.acts)

    def of(self, person: str | None, ref: str | None) -> Label | None:
        """The ruling that refuses this pair, or None. `ref` is `<act-id>#<pid>`."""
        if not person or not ref:
            return None
        hit = self.mentions.get((person, ref))
        if hit is not None:
            return hit
        return self.acts.get((person, ref.split("#", 1)[0]))


@lru_cache(maxsize=1)
def refutations() -> Refutations:
    """Cached: the queues ask this once per candidate over hundreds of thousands of them,
    and the file is a few dozen lines that cannot change inside one command."""
    mentions: dict[tuple[str, str], Label] = {}
    acts: dict[tuple[str, str], Label] = {}
    for lab in read_labels():
        if lab.match:
            continue
        if lab.names_a_mention:
            mentions[(lab.person, lab.ref)] = lab
        else:
            acts[(lab.person, lab.act_id)] = lab
    return Refutations(mentions=mentions, acts=acts)


def reset_cache() -> None:
    """After a label is written, so a long-running process does not keep the old view."""
    refutations.cache_clear()
