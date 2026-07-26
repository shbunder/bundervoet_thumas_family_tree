# Rules of evidence

Eight rules. Each one exists because its absence produced a specific, recoverable error —
two different Hammes, two Simonne Vandewalles, Van Craenenbroecks in the wrong province,
the Gustaaf/Gustavus confusion. They are enforced by the validator and the scorer, not by
good intentions.

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
