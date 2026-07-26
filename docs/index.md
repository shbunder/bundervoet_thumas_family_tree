# Reconstructing Flanders

This repository is a working attempt at a hard problem: **reconstruct the families of a
region from its surviving parish and civil registers, with every link traceable to the
document that supports it, using machine assistance without inheriting machine
credulity.**

It began as one family — the ancestors and blood relatives of Renée and Léon Bundervoet
— and the immediate objectives are still theirs. But every design decision is made
against a much larger target, because the decisions that work at three hundred people
and the ones that work at three million are not the same decisions, and you only get to
choose once.

## The problem

Genealogy at scale has one dominant failure mode: **silently grafting the wrong person.**

It is not a rare accident. It is the expected outcome of the ordinary method. Names in
Flemish registers repeat relentlessly — a forename returns every second generation, a
surname fills a commune, spelling drifts within a single family's own records
(*Bostyn*/*Bostin*, *De Keyser*/*Dekeyser*, *Vanstechele*/*Vanstechelman*). Match on a
name and a plausible date, and you will be right most of the time and wrong often
enough to poison the tree. A wrong link does not look broken. It looks like an ancestor.
Ten years later it is load-bearing, cited by three other trees, and unfindable.

Automation makes this worse before it makes it better, because it removes the friction
that used to make a researcher hesitate.

So the entire architecture here is organised around one question: *how do you go fast
without going wrong?*

## The claim

Three commitments, each enforced by code rather than by discipline:

1. **A link needs two independent identifiers.** Not two fields — two *classes* of
   evidence. A matching forename and a matching surname are both the name, and the
   research log is full of right-name/wrong-province rejections that prove it. See
   [Rules of evidence](method/evidence.md).
2. **Evidence is weighed by what it would cost to get by chance.** Agreement on
   *Janssens* and agreement on *Schalandrijn* are not the same evidence. Every agreement
   is scored in bits of surprise, counted against the venue's own population. See
   [Record linkage](method/linkage.md).
3. **Every judgement is kept, including the negative ones.** Searches that found
   nothing, candidates that were refuted, conclusions that were retracted. An unrecorded
   miss is a dead end the next pass walks again — and a refuted candidate is a labelled
   training pair. See [Verification and measurement](method/verification.md).

## What is actually here

| | |
|---|---|
| **Records** | ~307 people, one Markdown file each: strict frontmatter for facts, free prose for reasoning |
| **Corpus** | ~3,000 acts harvested from [Open Archives](https://openarch.nl), read as events rather than as people |
| **Linkage** | Blocking, Flemish phonetic folding, rarity-weighted scoring, adversarial verification |
| **Outputs** | A static site, a GEDCOM 7 export that round-trip-verifies itself |
| **Tooling** | Python, standard library only. A clone runs with nothing installed |

Everything derived — children, generations, kinship, lineages, the site itself — is
computed from `father`/`mother` links. Nothing is listed twice.

## What is honest about its limits

- The corpus is a few thousand acts against a venue holding tens of millions. Coverage
  is uneven and *known* to be uneven — Vlaams-Brabant has indexed civil acts where
  Oostende has mostly 20th-century memorial cards.
- The linkage model estimates the *u*-side of Fellegi–Sunter (how rare an agreement is)
  and not yet the *m*-side (how often a true match disagrees, because a clerk misheard).
  Thresholds are therefore reasoned, not measured — and `tools/evaluate.py` exists to
  start measuring them.
- One person, one file is right for the people who have been reasoned about, and will
  not survive contact with a million. The [scaling plan](method/scaling.md) says what
  gives way first.

## Where this sits in the literature

Whole-population family reconstruction is a mature discipline, and this project is a
late and small entrant to it. [BALSAC](https://balsac.uqac.ca/) has reconstructed
Quebec from parish registers since the 1970s; [LINKS](https://iisg.amsterdam/en/hsn/projects/links)
is doing the Netherlands; the [Antwerp COR\*-database](https://hlcs.nl/article/view/9301)
did a principled sample of Flanders itself. What is *not* established practice is doing
this in the open, per-person, with the evidence attached and the reasoning legible — and
with an autonomous agent doing the searching under rules strict enough to trust.

The honest summary of the novelty is narrow and specific: **the adversarial verification
loop, the miss log, and the checksummed evidence store.** Everything else here is
borrowed, and [Prior work](prior-work.md) says from whom.
