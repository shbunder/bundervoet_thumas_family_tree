# Prior work

Nothing here is unprecedented, and pretending otherwise would be the fastest way to
repeat mistakes that were solved decades ago. This page is the reading behind the design
decisions, and — where the design departs from established practice — why.

Four traditions matter, and they barely cite each other: academic historical demography,
crowd-sourced genealogy, statistical record linkage, and the recent machine-learning work
on archival documents.

---

## 1. Family reconstitution and historical demography

The founding method. **Louis Henry** and Michel Fleury established in the 1950s that
parish registers could be linked into families and used as demographic data, not merely
as biography — *Des registres paroissiaux à l'histoire de la population* (1956). Every
project below is a descendant of that idea. So is this one: `familytree/corpus.py` reads
acts as events over several people rather than as records about one, which is family
reconstitution's central move.

### BALSAC (Quebec, 1972– )

[balsac.uqac.ca](https://balsac.uqac.ca/apercu-des-donnees/?lang=en) ·
[overview paper](https://hlcs.nl/article/view/9299)

Over 4 million records covering close to 5 million individuals, 17th century to the
contemporary period, built by linking baptisms, marriages and burials into families.
Begun by Gérard Bouchard with one region's 660,000 records, now a national research
infrastructure used in both social science and biomedical genetics.

**What this project takes from it:** the demonstration that a whole population *can* be
reconstructed from registers, and the architecture that made it possible — a relational
store with linkage as a separate, re-runnable layer rather than as hand-asserted edges.

### LINKS (Netherlands, IISG + CBG)

[Project page](https://iisg.amsterdam/en/hsn/projects/links) ·
[system paper](https://hlcs.nl/article/view/14685)

Reconstructing *all* 19th and early-20th-century Dutch families from the civil registry
index. The pipeline is explicit and worth copying wholesale: **standardise every input
first, then link nominally, then identify unique persons.** Linked certificates are
published back through [WieWasWie](https://www.wiewaswie.nl/en/sources/links).

**What this project takes from it:** the insistence that standardisation precedes
linkage. Also the reminder that this is the *same venue* — Open Archives harvests the
Dutch and Belgian archives that LINKS works from.

### The Antwerp COR\*-database (Flanders)

[2020 IDS release](https://hlcs.nl/article/view/9301) ·
[EHPS-Net entry](https://ehps-net.eu/databases/antwerp-cor-database)

The closest existing work to this project's geography: a longitudinal micro-database of
the Antwerp district, 1846–1920, from population registers and vital registration,
~33,000 individuals.

Its sampling design is the most useful idea in the whole literature for anyone who wants
Flanders but cannot have it at once: **take every surname beginning `COR`, plus everyone
who shared a household with them.** That preserves household and kin structure inside the
sample instead of truncating it, which a geographic or chronological slice would not. It
is very close to this project's third objective — *connect all Bundervoets* — arrived at
independently and for the same reason.

A **West-Flemish Demographic Database** covering 239 communities, 1600–1910, is
referenced in this literature; the [Quetelet Center at UGent](https://www.queteletcenter.ugent.be/en/databases/lokstat/)
is the place to pursue it, along with LOKSTAT. That is this project's exact region and
period, and checking it before harvesting more is simply cheaper than re-deriving it.

### The Intermediate Data Structure (IDS)

COR\* was re-released in IDS, the interchange format historical demography settled on for
cross-national comparison. It is the discipline's answer to the same problem GEDCOM
solves for genealogists, and it models *events and their sources* rather than
*conclusions about people* — much closer to how `corpus.py` already works. It is the
natural second export target after GEDCOM 7.

---

## 2. Statistical record linkage

### Fellegi–Sunter

Fellegi, I. P., & Sunter, A. B. (1969). *A Theory for Record Linkage.* **Journal of the
American Statistical Association**, 64(328), 1183–1210.

The formal basis for deciding whether two records describe the same entity. Three
parameters: **λ** (the prior that any two records match), **m** (probability a field
agrees *given* the pair is a true match — i.e. the model of transcription error), and
**u** (probability it agrees *by chance* — i.e. rarity). The weight of an agreement is
`log2(m/u)`.

`familytree/match.py` implements the *u* side, counted from the venue's own population
figures rather than assumed. It does not yet estimate *m*. This is the single largest
known gap in the method: without *m*, a disagreement caused by a clerk's spelling cannot
be told from a disagreement caused by it being a different person, and every threshold
stays a judgement call. See [Record linkage](method/linkage.md).

### Splink

[moj-analytical-services/splink](https://github.com/moj-analytical-services/splink) ·
[Fellegi–Sunter guide](https://moj-analytical-services.github.io/splink/topic_guides/theory/fellegi_sunter.html)

The UK Ministry of Justice's open-source implementation: full Fellegi–Sunter with *m* and
*u* estimated by expectation-maximisation, DuckDB and Spark backends, roughly a million
records linked on a laptop in about a minute and 100M+ on a cluster.

The obvious candidate to take over scoring when this project's corpus outgrows a
single-process Python loop. The parts worth keeping in that migration are the ones Splink
does *not* have: the two-independent-classes floor, and the vetoes.

### Blocking

Standard practice, and non-negotiable at any real size: never compare all pairs; group
records by cheap keys a true match must share and compare only within groups. `match.py`
uses several keys rather than one, because any single key is blind to the variant it
cannot see — a phonetic key misses a truncated surname, a date key misses an undated
record.

---

## 3. Crowd-sourced trees and their limits

### Geni → FamiLinx

Kaplanis, J., Gordon, A., Shor, T., et al. (2018). *Quantitative analysis of
population-scale family trees with millions of relatives.* **Science**, 360(6385).
[Dataset](https://www.familinx.org/)

86 million crowd-sourced Geni profiles cleaned by graph-theoretic methods into a
connected tree of 13 million people spanning ~11 generations, released anonymised for
research. The clearest demonstration both of what crowd-sourced genealogy is worth in
aggregate *and* of how much cleaning it takes to get there.

### WikiTree and FamilySearch

[WikiTree](https://www.wikitree.com/wiki/Help:Collaborative_Family_Tree) maintains a
single shared tree of ~40 million profiles, free to use and explicitly friendly to
open-source reuse, with a clear privacy rule (profiles public once born >150 years ago or
died >100). The FamilySearch Family Tree is far larger — on the order of 1.5–1.8 billion
people — one conclusion per person, free but not open data.

**Why this project does not simply contribute there:** neither model keeps the *reasoning*
attached to the link. A merged profile records the conclusion and loses the argument, and
the argument is the part that lets a later researcher find the error. That is a
disagreement about emphasis, not a claim that those projects are wrong; the intended
relationship is to publish *into* them, not to replace them.

---

## 4. Machine reading of archival documents

### LLM transcription of historical handwriting

Humphries, M., Leddy, L. C., Downton, Q., et al. (2024). *Unlocking the Archives: Using
Large Language Models to Transcribe Handwritten Historical Documents.*
[arXiv:2411.03340](https://arxiv.org/abs/2411.03340)

Multimodal LLMs transcribe 18th–19th century handwriting at character error rates around
5.7–7%, beating specialised HTR software such as Transkribus, and reaching ~1.8% CER with
LLM post-correction. Released with an open tool, *Transcription Pearl*.

### Genealogical extraction from parish registers

*Large-scale genealogical information extraction from handwritten Quebec parish records.*
**IJDAR** (2023). [Springer](https://link.springer.com/article/10.1007/s10032-023-00427-w)

The direct template for the long tail: going from *what volunteers have indexed* to *what
the registers actually contain*. It is deliberately last on this project's roadmap — the
indexed material is nowhere near exhausted, and transcription is only worth automating
once the linkage that consumes it is trustworthy.

### AI in production genealogy

FamilySearch's Full-Text Search applied generative AI to roughly 2 billion images of
handwritten records, launching out of Labs in August 2025. It changes what "already
searched" means: a venue that was exhausted against a name index may be wide open against
a full-text index. This is why every miss in `research/searches.jsonl` records its
**scope** — what was actually covered — and why `research.py stale` exists to find misses
a venue has since outgrown.

---

## 5. The venues themselves

**[Open Archives](https://openarch.nl/datasets)** (openarch.nl, by Bob Coret) —
Netherlands, Belgium and France, 140+ archives, ~277 million person mentions. Free,
unauthenticated JSON API throttled to 4 requests/second; also OAI-PMH and bulk dumps in
the **A2A** model as N-Triples, XML and CSV. Records retrievable as JSON, XML, GEDCOM,
Turtle or N-Triples. This is the backbone of the corpus, and the bulk-dump path is the
[scaling plan](method/scaling.md)'s first move.

**[Rijksarchief België](https://arch.arch.be/index.php?l=nl&m=databanken&r=zoeken-naar-personen)** —
"Zoeken naar personen" exposes 42M+ indexed names, transcribed by volunteers through the
[Demogen](https://www.arch.be/index.php?l=nl&m=genealoog&r=demogen) project. Much of this
flows into Open Archives; the Brussels dataset alone contributes ~2.36M acts and ~10M
person mentions.

**Privacy in Belgian civil registration** — records become public on a schedule: deaths
after 50 years, marriages after 75, births after 100. At regional scale this stops being
a convention and becomes a validator rule.

---

## What this project adds

Stated narrowly, because the honest list is short:

1. **Adversarial verification as a pipeline stage.** A dedicated agent whose task is to
   *refute* a candidate, defaulting to rejection when uncertain. Academic linkage handles
   this statistically through thresholds; crowd genealogy does not handle it at all.
2. **The miss log as first-class data.** `research/searches.jsonl` records every search,
   its basis, and — for failures — its *scope*. Linkage projects publish match scores;
   essentially nobody publishes what was searched and found nothing.
3. **Checksummed evidence.** `data/artifacts/` stores the scan alongside a record
   carrying `sha256` and `bytes`, recomputed by the validator. A citation whose evidence
   silently changed is worse than an uncited claim, because it still reads as sourced.
4. **The gold standard as a by-product of verification.** Every accept/refute ruling is
   written back as a labelled pair (`tools/evaluate.py`), which is what will eventually
   let the thresholds be measured instead of argued. As far as this project's survey
   found, no open labelled linkage set exists for Flemish records.
