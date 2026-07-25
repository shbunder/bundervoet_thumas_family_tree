---
description: Verify the people already in the index against records, unattended, until every one has a verdict.
argument-hint: "[number of passes, default 12]"
---

Run $1 verification passes (default 12), back to back, without checking in.

`/autopilot` grows the tree — it asks "who were this person's parents". **This command does
the other job: it takes the people already in the index and gets evidence for each one.** A
pass here ends with records cited, corrected, or explicitly marked unverifiable-and-why —
never with a person left silently resting on a member tree.

I am not at the computer. **Do not ask me questions.** Where you would ask, choose what
[CLAUDE.md](../../CLAUDE.md) already implies, write the choice into the log, and continue.
Derive every queue fresh from the tools; nothing here should be remembered from earlier in a
conversation.

Do not edit `tools/`, `.claude/` or `CLAUDE.md`. If a pass seems to need it, that is a
finding for the final report, not a change to make now.

## Before the first pass

1. `uv run tools/check_data.py` — green, or stop and say why. Never start from a broken tree.
2. **Finish the corpus before sweeping anything.** `uv run tools/harvest.py status`, then
   harvest every surname still listed as never harvested and re-run every PARTIAL with the
   command the status output prints. This is the single biggest unlock: most people the sweep
   cannot reach are unreachable only because their surname was never fetched.
3. **Stop the harvester before you sweep.** `verify_all.py` reading a store that is being
   rewritten produces different scores on every run — a sweep during a harvest once reported
   13 corroborations where the true figure was 67. Harvest, let it finish, then sweep.

## Each pass

`uv run tools/verify_all.py` puts every person in one of four buckets. Work them in this
order, and take the next unrecorded person from the top of the bucket:

1. **CORROBORATED** — a date or place agrees, not just names. Go read the act.
2. **NAME AND KIN ONLY** — leads. Try to anchor one with a date or place; if nothing
   anchors it, record it as a lead and move on.
3. **PARTIAL** — one identifier. Usually needs a different venue, not a closer look.
4. **NOT REACHED** — the corpus holds nothing under that surname. Harvest it, or search
   AGATHA and the open web directly.

### Reading the act is the point

A corroboration from an index is not a verification. For each one, go to the record itself:

- **AGATHA** (`agatha.arch.be`) — "Analyses van akten", search name + commune + year. This
  is where the Rijksarchief publishes its own transcriptions, with act numbers.
- **`search.arch.be` is retired.** Every act link in the harvested corpus points at it. An id
  like `HUBRA_00221638_0` becomes `HUVLB_HUBRA_00221638_0` on AGATHA, or find the act by
  name + commune + year.
- **FamilySearch** for act images where AGATHA has only an index entry.
- **The open web** — WebSearch/WebFetch reach public indexes, WikiTree, Find A Grave,
  digitised newspapers, parish transcriptions. Register anything that pays off in
  `research/sources.json`.

Save what you read: a full-page screenshot into `data/artifacts/` with its `.md` record,
sha256 and `evidences:` list. An act read but not saved has to be read again.

### What each verdict does to the record

- **Act read, two independent identifiers anchored** → cite it, `confidence: doc`, fill in
  what the act states and nothing it does not.
- **Index agrees, act not read** → cite it, stay `sup`, say in the prose that no image was read.
- **Nothing found** → leave the record alone and log the miss **with its scope** — which
  venue, which years, which communes. An unrecorded miss is a dead end walked again.
- **Contradiction** → correct the record, and say in the prose what was wrong, what the act
  says, and which is now believed. Corrections are first-class.

## The rules that matter most when nobody is watching

1. **Two independent identifiers, and one of them anchored.** A surname plus a relative's
   forename is not two identifiers — for common Flemish surnames it is close to none. The
   scorer has offered a 1809 Aalst man for a boy born in 1920s Oostende, and a woman bearing
   children a decade before her supposed birth. Both scored "strong". A date or a place must
   agree.
2. **Never upgrade to `doc` without having actually read the act or its image.** An index
   transcription is `sup`, however authoritative the archive.
3. **Never invent a field.** If the act does not give an occupation or a day, it is absent.
4. **A strong lead is not a link.** Record it in the prose as a named frontier with the
   record that would settle it. Do not graft it.
5. **A pass that verifies nothing and logs five honest misses is a successful pass.** Do not
   lower the bar to have something to report.
6. **Assert your edits landed.** A bulk edit that inserts a citation after a `sources:` line
   silently does nothing on records that have no `sources:` block — and if the same script
   also sets `confidence: doc`, the result is a documented claim citing nothing. That has
   happened. After any batch edit, re-check the records you meant to change.

## Write, every pass

- The person files — citation by id, honest confidence, no invented field.
- `uv run tools/research.py log …` for every search, hit or miss; a miss states its scope.
- `uv run tools/evaluate.py label …` for every ruling, **rejections included** — a rejected
  pair that scored well is the most useful label the scorer can get.
- New sources and artifacts registered.
- A numbered section in `docs/research-log.md`.
- One row in `docs/verify-log.md`. Create it if absent, with this header:

  ```
  | pass | date | person | bucket | verdict | evidence | commit |
  |------|------|--------|--------|---------|----------|--------|
  ```

  `verdict` is DOCUMENTED / CORROBORATED / LEAD / REJECTED / NOT FOUND / BLOCKED.
- `uv run tools/build.py`, then one commit per pass. **Do not push.**

## Stop early if

- `build.py` fails for a reason the validator's own message does not explain. Leave the tree
  as it is; never force it green.
- Three passes in a row come back entirely `blocked` — the browser session or the network is
  gone, and further passes will only log noise.
- Continuing would require breaking a rule above.

## At the end

Append a summary to `docs/verify-log.md` and print the same here:

- people with act-level evidence, before → after, and how many reached `doc`;
- every correction made, with what the act said;
- everything rejected, and what refuted it;
- the people who **cannot** be verified from records, grouped by reason — living, Oostende
  post-1900 (Stadsarchief, offline), pre-registration parish gaps, surname absent from every
  open index — because that list is the real answer to "is everyone verified", and it is
  worth more than a number;
- the single most valuable thing to do next, and whether it needs me.

I will read `docs/verify-log.md`, not the transcript. Keep it short enough to read in a minute.
