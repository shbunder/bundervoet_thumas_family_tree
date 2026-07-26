---
description: Verify the people already in the index against records, unattended, until every one has a verdict.
argument-hint: "[number of passes, default 12]"
---

Run $1 verification passes (default 12), back to back, without checking in.

`/autopilot` grows the tree — it asks "who were this person's parents". **This command does
the other job: it takes the people already in the index and gets evidence for each one.** A
pass here ends with records cited, corrected, or explicitly marked unverifiable-and-why —
never with a person left silently resting on a member tree.

**The rules for an unattended run are in [CLAUDE.md](../../CLAUDE.md) § Unattended runs** and
are not repeated here. This file is only what is particular to *verifying*: the buckets, the
venue ladder, the duty to go looking for a venue that is not in it, and this run's own log.

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

A corroboration from an index is not a verification. Go to the record itself.

### EXHAUST THE VENUES BEFORE YOU CONCLUDE ANYTHING

One venue missing is not a negative. It is one venue missing. Before any person is written
up as NOT FOUND, run **`uv run tools/research.py untried <person>`** and work down what it
lists. That command exists precisely for this, and it has caught the failure: a person was
recorded NOT FOUND after a single AGATHA search while `untried` still listed *sixteen*
unsearched sites.

Go in this order — it is the order the log's own hit rates justify, not a guess.
`uv run tools/research.py yield` will tell you if it has shifted.

1. **The held corpus** — free and local. `uv run tools/link.py <person>`.
2. **FamilySearch** — the highest-value venue in the registry and the least used. It is the
   only registered source with **full-text search over unindexed images**, which is the only
   thing that reaches parish registers. Use both its indexed collections and full-text.
3. **AGATHA** — "Analyses van akten", name + commune + year. Note its `Plaats` and `Periode`
   filters match anything *mentioned* in an act, not the act's own commune or date, so read
   the result list rather than trusting the filter. It indexes the registration date, so an
   act can sit a day after the event.
4. **Geneanet** — its indexed *record collections*, not only the member trees.
5. **vrijwilligersrab** and **vvf** — volunteer transcriptions of West-Flemish marriages and
   deaths. Never yet searched, and West-Vlaanderen is where most unverified people are.
6. **The obituary and cemetery cluster** — jammart, grafzerkje, inmemoriam, ingedachten,
   uitvaart-oostende. Memorial cards name parents and children and sit outside the
   civil-registration privacy rules, which makes them the way into the 20th century.
7. **Ancestry / MyHeritage** — paywalled. Treat as a *targeting list*: they say which
   document exists for whom, and the act itself can then be pulled free elsewhere.
8. **The open web** — WebSearch/WebFetch: published genealogies, WikiTree, Find A Grave,
   digitised newspapers, parish transcriptions, heemkring publications.

`search.arch.be` is retired; its ids translate (`HUBRA_00221638_0` →
`HUVLB_HUBRA_00221638_0`) or find the act on AGATHA by name + commune + year.

### WHEN THE WHOLE LADDER MISSES, GO LOOKING FOR A VENUE THAT IS NOT IN IT

A pass that reaches the bottom of the list with nothing is not finished. It has only proved
the registry is too small for this person. **Spend the rest of that pass hunting for a source
nobody here has heard of**, then register it and use it. This is where the registry grows,
and a venue found once answers every later frontier in the same commune.

Where to look, roughly in order of how often it works:

- **The commune, in its own language.** Search `<commune> parochieregisters online`,
  `<commune> burgerlijke stand index`, `gedigitaliseerd`, `klappers`, `registres paroissiaux`.
  Many communes have an index nobody has aggregated.
- **The local history society** — *heemkring*, *geschiedkundige kring*, *cercle d'histoire*.
  They publish transcriptions, cemetery surveys and memorial-card collections that no
  national aggregator holds. De Plate for Oostende is the example already in the registry.
- **Provincial and university digitisation** — provincial archives, Erfgoedbibliotheek,
  KBR's **BelgicaPress** for digitised Belgian newspapers (death and marriage notices,
  1850–1950).
- **Population registers** (*bevolkingsregisters*). Underused and unusually rich: they follow
  a whole household across a decade, so they place children, lodgers and moves that no single
  act mentions.
- **Surname-specific work** — one-name studies, Geneanet and Vlaamse Stam forums, parenteel
  publications. A rare surname often has someone who has already done the work.
- **Outside Belgium when the person left.** The De Keyser wartime family is the standing
  example: England & Wales GRO and FreeBMD for Roland's 1943 Tottenham birth and for Rita
  and Simonne, CWGC and the Free Belgian Forces / Brigade Piron rolls for Gustaaf. The
  Belgian corpus has already returned clean negatives for all three, which is a signpost,
  not a dead end.

Register whatever you find in `research/sources.json` before searching it — id, kind, access,
what it covers, and its `capabilities` — so the next pass can see it and `untried` can offer
it. Register it even if it then yields nothing: a venue checked and empty is worth recording.

**NOT FOUND means "the ladder was walked and a new venue was looked for and neither had
them", and the log entry must say which venues.** Anything less is BLOCKED or simply
unfinished.

Save what you read: a full-page screenshot into `data/artifacts/` with its `.md` record,
sha256 and `evidences:` list. An act read but not saved has to be read again.

### What each verdict does to the record

- **Act read, two independent identifiers anchored** → cite it, `confidence: doc`, fill in
  what the act states and nothing it does not.
- **Index agrees, act not read** → cite it, stay `sup`, say in the prose that no image was read.
- **Nothing found, ladder walked, discovery attempted** → leave the record alone and log the
  miss **with its scope**: which venues, which years, which communes, and what was looked for
  and not found in the discovery step. An unrecorded miss is a dead end walked again.
- **Nothing found, ladder not walked** → not a verdict. Keep going, or leave the person
  unrecorded for the next pass. Do not spend a NOT FOUND you have not earned.
- **Contradiction** → correct the record, and say in the prose what was wrong, what the act
  says, and which is now believed. Corrections are first-class.
- **A venue found that the registry lacked** → register it, and log the discovery even when
  the venue then yields nothing. Finding where the records are is progress in itself, and it
  is the only thing that grows the ladder for everyone below.

## The rules that matter most when nobody is watching

1. **Two independent identifiers, and one of them anchored.** A surname plus a relative's
   forename is not two identifiers — for common Flemish surnames it is close to none. The
   scorer has offered a 1809 Aalst man for a boy born in 1920s Oostende, and a woman bearing
   children a decade before her supposed birth. Both scored "strong". A date or a place must
   agree.
2. **A strong lead is not a link — but a named child is not a lead.** Keep the two apart.
   *Identifying* someone — deciding a person in a record IS a person in the tree — needs two
   independent identifiers and stays a frontier until it has them. *Transcribing* someone —
   adding a person a document names as another's child, spouse or parent — is not that, and
   should be done freely. **Be generous in adding people.** A record naming both parents is
   better evidence than the member trees much of this tree was built on, and every person
   added brings their own dates, spouses and frontiers with them. Add them at the confidence
   the source earns, cite it, and say in the prose what has not been read.
3. **Assert your edits landed.** A bulk edit that inserts a citation after a `sources:` line
   silently does nothing on records that have no `sources:` block — and if the same script
   also sets `confidence: doc`, the result is a documented claim citing nothing. That has
   happened. After any batch edit, re-check the records you meant to change.

## This run's own log

Everything else that gets written is in CLAUDE.md § Unattended runs. Specific to this command:

- One row in `docs/verify-log.md`. Create it if absent, with this header:

  ```
  | pass | date | person | bucket | verdict | evidence | commit |
  |------|------|--------|--------|---------|----------|--------|
  ```

  `verdict` is DOCUMENTED / CORROBORATED / LEAD / REJECTED / NOT FOUND / BLOCKED /
  NEW SOURCE. A NOT FOUND row must name the venues walked; otherwise it is not one.

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
