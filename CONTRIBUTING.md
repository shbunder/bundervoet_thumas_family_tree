# Contributing

The rules here are stricter than most genealogy projects, and the strictness is the
point. The failure mode this project is organised against is **silently grafting the
wrong person** — a link that does not look broken, looks like an ancestor, and is
unfindable ten years later.

Read [Rules of evidence](docs/method/evidence.md) before proposing any change to `data/`.

## The bar for adding a person or a link

1. **Two independent identifiers**, and say which two. Not two fields — two *classes*:
   name, date, place, role, kin. A matching forename and a matching surname are both the
   name.
2. **A citation** that resolves to an id in `research/sources.json`.
3. **Honest confidence.** `doc` means a primary act or its image was *actually read*.
   Downgrading is always fine; upgrading needs a document.
4. **A strong lead is not a link.** Put it in the person's prose body as a named
   frontier. Do not graft it.
5. **Never invent a field.** If the source did not say it, it is absent.

If you cannot meet the bar, the contribution is still valuable — as a **frontier**, or as
a **logged miss**. Both are first-class here.

## Log the negatives

An unrecorded miss is a dead end the next person walks again.

```bash
uv run tools/research.py log … --why "…"     # every search, hit or miss
uv run tools/evaluate.py label … --why "…"   # every accept/refute ruling
```

A miss must state its **scope** — what was actually covered. "This archive is exhausted"
is almost never true; "this archive's name index for 1800–1850 has no such person" is.
Venues are retro-fitting AI full-text search over previously unindexed images, so an
over-broad miss becomes a wall that nothing can reopen.

## Before you commit

```bash
uv run tools/build.py          # validates first; refuses to generate from a broken tree
uv run --group dev pytest
```

The build must be green. `check_data.py` also fails on stale generated files, so the
"green before commit" rule covers regeneration too.

One commit per research pass, with a numbered section added to
[docs/research-log.md](docs/research-log.md) saying what was found, what came back
negative, and what the next frontier is.

## Changing the linkage code

`familytree/match.py` and `familytree/corpus.py` are where a mistake becomes systematic
rather than local. Two requirements:

- **Pin both directions in the tests.** Variants that must fold *and* distinct families
  that must not. Over-folding merges families, which is the failure mode.
- **Re-run the gold standard** and report the effect:

  ```bash
  uv run tools/evaluate.py report
  ```

  Labels are re-scored by the code as it stands, precisely so that a change to scoring
  can be measured against judgements that were already made.

If a change increases the number of refuted pairs the scorer would graft, it is a
regression regardless of what else it improves. Precision over recall: a missed link is
found again next pass, a false link is invisible forever.

## Corrections

Corrections are first-class. When a past conclusion is wrong:

1. Retract it explicitly in the research log, with the reasoning.
2. Fix every record it touched.
3. Write a superseding label if a verifier ruling was involved — later labels win.

A project that cannot record being wrong accumulates errors it cannot find.

## Style

- Plain text in data files (`é`, `&`), never HTML entities. The renderer escapes.
- Comments explain **why**, with the concrete failure that motivated the rule. The
  codebase is written this way throughout; match it.
- No new runtime dependencies. `pyproject.toml` declares none on purpose — a dependency
  is a thing that has to still resolve in ten years for the tree to be readable. Dev and
  docs tooling goes in a dependency group.
- `data/` is the only place a name or a date may appear. `site/` holds wording that
  cannot change what the tree claims. `assets/` contains neither.

## Privacy

Belgian civil registration becomes public on a schedule: deaths after 50 years, marriages
after 75, births after 100. Do not add records of living people, and note that Git does
not forget.
