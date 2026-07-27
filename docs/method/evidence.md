# Rules of evidence

Eight rules. Each one exists because its absence produced a specific, recoverable error —
two different Hammes, two Simonne Vandewalles, Van Craenenbroecks in the wrong province,
the Gustaaf/Gustavus confusion. They are enforced by the validator and the scorer, not by
good intentions.

Rule 4 has a qualification, § 4a, which is the one place this project permits a link on a
single identifier. It is worth reading with rule 1 rather than instead of it: the floor
holds because a link that declares itself assumed is evidence for nothing.

---

## 1. Never match on name alone

A graft needs **at least two independent identifiers** to agree — and the record must say
which two.

"Independent" means two different *classes* of evidence, not two fields:

| Class | Examples |
|---|---|
| `name` | surname, forename |
| `date` | birth date, birth year, death year |
| `place` | birthplace, residence, event commune |
| `role` | occupation |
| `kin` | father's name, mother's maiden name, spouse, child, grandparent |

A matching forename *and* a matching surname are one identifier, not two: they are both
the name. Every false positive in this project's log so far has been
right-name/wrong-place, which is exactly what a name-only match cannot see.

This is a **floor, not a threshold**. No amount of accumulated score substitutes for it —
`match.py` computes the bits and the class count separately, and a candidate that scores
40 bits on the name alone is still not graftable.

!!! note "Why `kin` matters disproportionately"
    Two Petrus Bundervoets born the same decade in the same commune are genuinely hard to
    tell apart. The one whose mother is Livina Stockman is not hard to tell apart at all.
    A mother's maiden name is the classic second identifier because it introduces a
    surname that is *not* already implied by the subject's own.

## 2. Record the evidence, then the fact

Every new parent link cites a source in `research/sources.json`. A claim with no citation
does not go in the tree — not as a low-confidence entry, not as a note. It stays a
frontier.

## 3. Confidence is honest, not aspirational

| Code | Meaning |
|---|---|
| `doc` | A primary act or its image was **actually read** |
| `sup` | One member tree, unverified |
| `fam` | Family testimony |
| `unk` | To research |

Downgrading is always allowed. **Upgrading requires a document.** An index entry that
merely quotes an act is not the act: `data/artifacts/` records must state whether the
image was read or only an index page, because they are different evidence and only one
of them is `doc`.

## 4. A strong lead is not a link

Record it in the person's prose body as a named frontier. Do not graft it. The temptation
to graft a 90%-likely parent is exactly the mechanism by which trees become unreliable,
because nothing downstream will ever remember the 10%.

## 4a. …unless the link itself says it is assumed

The rule above is right about the mechanism and wrong about the remedy, and at the scale
this tree is aiming for the difference matters. Refusing every one-identifier link buys
correctness at a price paid in coverage: a marriage act naming six people yields one graft
instead of five, and the four it withheld are not recorded as doubts — they are recorded
nowhere a tool can read. The 10% nothing downstream remembers is the real problem. Refusing
the link is only one way to solve it.

So a link may be drawn on one identifier **if it declares that about itself**:

```yaml
mother:
  id: ludovica_vanald
  confidence: asm
  source: agatha-diksmuide-1880-birth
  note: birth act names a Ludovica Vanalderweireldt; commune and year agree, no second identifier
```

Four things then hold, and it is only safe because all four do:

1. **An `asm` link is evidence for nothing.** `from_person` hides it from the scorer in
   both directions — as a parent, and as a child reaching back. This is the whole safety
   property. Without it, guess A licenses graft B, which licenses C, every one scoring as
   well-supported, and the error rate compounds down the line with nothing marking where it
   started. The two-independent-identifiers floor in rule 1 stays a floor precisely because
   the tree's own guesses cannot be counted towards it.
2. **It must say what it rests on.** A link with `confidence: asm` and no `note` fails the
   build. An assumption nobody explained cannot be checked by anyone later, including
   whoever made it — the note *is* the finding, and the link is only its consequence.
3. **It is visible.** The page draws the join red, with the note on hover; the GEDCOM
   export carries a note on the `FAMC` link, because an exported tree is exactly where a
   bad graft goes to become unfindable, copied into other trees and cited back as
   agreement.
4. **It is queued, and the queue is derived.** `research.py weak` lists every one, ordered
   by how many people are in the tree *only* through it — measured by walking the pedigree
   with the link cut, not counted from the parent's ancestry, which double-counts wherever
   the tree folds back on itself. Because the queue is computed from the records on every
   run, an assumption cannot be forgotten and cannot go stale.

What this does **not** license: an `asm` link with no note, an `asm` link nobody ever
returns to, or `asm` as a way to avoid the argument. Rule 3 still applies — upgrading to
`doc` needs a document — and a stated conflict still vetoes outright, whatever the link
says about itself.

There is deliberately no "assumed since" date. Git already knows when a line was written,
and a hand-kept date beside it is the second copy the data model forbids.

## 5. Never invent a field

If an occupation or a day-level date was not in the source, it is **absent**, not
guessed. The date grammar deliberately has no syntax for "probably March" — a format for
a guess is an invitation to record one. See [Data model](../data-model.md).

## 6. Corrections are first-class

When a past conclusion is wrong, retract it explicitly in the research log with the
reasoning, and fix every record it touched. A tree that cannot record being wrong will
accumulate errors it cannot find.

## 7. Log every search, especially the ones that found nothing

An unrecorded miss is a dead end the next pass will walk again. Every entry states its
`basis` — *how* the material was consulted — and every miss states its `scope` — what was
actually covered.

## 8. The build must be green before any commit

```bash
uv run tools/build.py
```

---

## What the validator enforces

The rules above are prose; these are the ones that fail a build:

- **Marriage is mutual.** If A lists B as a spouse, B lists A.
- **A shared child proves a couple.** A record with `father: A` and `mother: B` obliges
  A and B to list each other.
- **Every referenced person exists.** No one may exist only as a string inside someone
  else's note.
- **Every citation resolves** to an id in the source registry.
- **Every artifact's checksum matches.** `sha256` and `bytes` are recomputed on every
  build; evidence that changed underneath a citation is a hard failure.
- **Nothing generated is stale.** The bundle and the GEDCOM must match the data.
- **Demographic plausibility.** A parent aged under 13 or over 50 (mother) / 75 (father)
  at a child's birth, a child born after its mother's death, a lifespan over 110 years —
  each is reported. These are the arithmetic signatures of a graft that is off by a
  generation, which is the recurring failure in material where forenames return every
  second generation.

!!! warning "Bounds are not measurements"
    `<1673` means "born at some unknown time before 1673". Doing arithmetic on it once
    produced *"is mother at age -6"* for a record that was never in conflict with
    anything. `point_year()` returns a year only for date forms that actually assert
    one; `year_of()` remains for sorting. The distinction is invisible until something
    does sums, which is exactly when it matters.
