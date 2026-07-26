# Verification and measurement

## The asymmetry

Everything in this method follows from one observation:

!!! danger "A missed link is found again next pass. A false link is invisible forever."

A missed link costs a search. A false link costs the tree: it does not look broken, it
looks like an ancestor, and everything grafted above it inherits the error. At scale it
becomes unfindable, and — if the data is ever published or cited — unretractable.

So verification defaults to **rejecting when uncertain**, and every threshold is chosen
for precision over recall.

## Adversarial verification

Candidates are not reviewed. They are **attacked**.

The verifier agent's task is to *refute* the proposed identity — to find the reason these
are two people rather than one. It is read-only, it never edits the tree, and it defaults
to rejection when it cannot decide. It runs on every candidate the searcher returns,
before anything is written.

This is the separation that makes the loop trustworthy: the agent that found the evidence
does not get to accept it. An agent that both finds and accepts will accept what it
found.

Things the verifier is looking for, in rough order of how often they have worked:

1. **Wrong place.** Every false positive in this project's log so far has been
   right-name/wrong-province.
2. **Wrong generation.** The forename returns every second generation, so a grandfather
   fits his grandson's slot suspiciously well. Check the arithmetic, not the name.
3. **A second person of the same name in the same commune.** Common, and the reason
   `research.py components` exists.
4. **An index entry standing in for an act.** An index quoting an act is not the act.

## The gold standard

Every ruling — accept *or* refute — is a **labelled pair**: two records and a judgement
about whether they are the same person. Until recently those judgements were made and
thrown away, which meant no threshold in the scorer could ever be measured.

```bash
uv run tools/evaluate.py label anna_vc abt:c59c…#Person3 --match    --basis act   --why "act names both parents"
uv run tools/evaluate.py label anna_vc gnt:d4f1…#Person1 --nonmatch --basis index --why "wrong province"
```

A label records **who decided, on what basis, and why**. A label without a reason is
rejected by the tool. `basis` is kept explicit — `act`, `index`, `tree`, `reasoning` —
because a label from a read act and a label from a plausible-looking index page are not
the same evidence, and a gold standard that mixes them silently measures the wrong thing.

**Label the mention, not the act** — the `#Person3` above is not decoration. An act names
six people, so `abt:c59c…` alone does not say which of them the ruling concerned. 45 of the
first 48 labels here were written without it, and the scorer was handed whichever
participant the record happened to list first: Maria Thérèsia Pardon was scored against
Joseph Reniers, her own husband; Hendrik Vandenbemden against a witness. Each came back
REJECTED on a sex or birth-date conflict and was counted as a confirmed match the scorer
had *missed*, which is how this page could once report 33% recall for a scorer that had no
known errors at all. The ambiguity was measuring itself.

`evaluate.py refs` lists every label still owed a pid, with the act's participants and
their roles, and prints the command to re-record each one. It resolves nothing by itself —
where an act names a bride *and* her father of the same surname, only a human can say which
the ruling was about, and guessing is what caused this.

Sorting the 45 turned out to be mostly mechanical, and the shape of the split is the useful
part. **Twenty** named exactly one participant carrying the person's own forename or birth
year: a `--match` label *asserts* the person is in the act, so finding them is a lookup and
not a judgement. **Ten** named no participant resembling them at all — those are not pairwise
rulings but judgements about an *act*, and forcing a pid onto one would invent the thing it
denies. Re-scored pairs went from 8 to 28 without a single new ruling being made, and
precision and recall held at 100%.

The reverse also matters: **an act-level ruling is not merely a weaker label, it is an
uncounted one**, and reporting all of them as work-for-a-human overstated the backlog four
times over. Most were waiting on a harvest, not on anybody. Counting them apart is the
difference between a number someone acts on and a number everyone ignores.

Labels are append-only, and later labels supersede earlier ones for the same pair:
corrections are first-class here exactly as they are in the tree.

## The rulings feed the queues, not only the scorer

For a long time `research/labels.jsonl` was read by `evaluate.py` and nothing else. The
search log had `research.py tried`, `untried` and `stale` from the start, precisely so a
*miss* is never walked twice — but a **ruling**, which costs someone the reading of an act,
had no equivalent. So a refutation could be recorded with its full reasoning and the queue
that proposed the pair would propose it again the next night.

`research.py children` now holds back any pair a verifier refuted, and prints each one with
its reason rather than dropping it silently, so a wrong refutation can be spotted and
re-pointed instead of quietly removing a lead forever. An act-level refutation covers every
mention in that act — broader than the label strictly says, and the right way round: too
broad costs one label a re-point, too narrow costs the loop where every night re-grafts what
last night refuted.

An **accept** is deliberately not read here. A queue that skipped what was already confirmed
would hide the corroboration.

### What it buys

```bash
uv run tools/evaluate.py report
```

Every labelled pair is **re-scored by the scorer as it stands today** — never by the score
stored when the label was written. That is the whole point: you want to see what a change
to `match.py` does to judgements that were already made.

```
  confirmed matches the scorer would graft   ...
  confirmed matches it would MISS            ...   ← recall
  refuted pairs it would wrongly graft       ...   ← the ones that matter
  refuted pairs it correctly rejects         ...
```

```bash
uv run tools/evaluate.py sweep
```

...prices the thresholds: for each setting of *distinguishing bits* and *independent
classes*, how many labelled pairs would be grafted, how many of those are right, how many
are wrong, and how many true links would be missed.

It deliberately does **not** choose. The trade between a missed link and a false graft is
a judgement about this project's purpose, not something a table decides.

!!! note "How many labels are enough"
    Around fifty makes the report meaningful. A few hundred makes it possible to estimate
    the *m*-probabilities that [linkage](linkage.md#known-gap-the-m-side) currently
    lacks — at which point the weights become calibrated rather than relative, and the
    thresholds stop being arguments.

As far as this project's survey of the literature found, **no open labelled linkage set
exists for Flemish parish and civil records.** Producing one as a by-product of ordinary
research is the most transferable thing here.

## Recording the negatives

The same principle applies one level up, to searches rather than pairs.

```bash
uv run tools/research.py log … --why "…"    # a miss states why, and its scope
```

An unrecorded miss is a dead end the next pass will walk again — the difference between a
loop that converges and one that searches the same index every night forever.

Two distinctions carry real weight:

- **`miss` vs `blocked`.** A `miss` means the material was read and he was not in it. A
  `blocked` means nothing was ever read. Only one of them is exhausted.
- **Scope.** Every miss records what was *actually* covered. "AGATHA is exhausted" was
  only ever true of AGATHA's name index. A miss with no extent reads as *everywhere* and
  becomes a permanent wall — which matters now that venues are retro-fitting AI full-text
  search over images that were never indexed. `research.py stale` finds the misses a
  venue has since outgrown.
