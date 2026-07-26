# Scaling to Flanders

The stated ambition is the whole region: everyone who lived in Flanders, as far back as
the registers reach. This page is the honest engineering assessment of the distance
between here and there, in the order the constraints actually bind.

Current state: **~307 people, ~3,000 acts.** Target: order **10⁷ person-records**.

---

## 1. Ingestion — done, and it was the binding constraint

Harvesting used to fetch one act per API call at ~3 requests/second. Belgium is on the
order of 8 million acts: **roughly a month of continuous fetching**, against a free
service run by other people. Possible, but the wrong tool and a poor guest.

**The fix already existed at the venue.** Open Archives publishes:

- **bulk data dumps** in the A2A model — N-Triples (linked data), XML, and CSV;
- an **OAI-PMH provider** for incremental harvesting.

Both are now used. `harvest.py bulk <archive>` downloads and streams a whole archive's
gzipped A2A export; `harvest.py oai <archive>` pages the OAI-PMH feed at 150 full records
a request; `records/show` is retained for gap-filling and for the archives that publish
neither. `familytree/a2a.py` reads that XML into the exact shape the JSON API returns, so
the routes are interchangeable rather than merely similar — checked against real data:
all 1,361 Kortrijk acts held from the API normalise to records identical to the same acts
read out of the bulk export.

The measured difference is the whole argument. Kortrijk is **140,543 acts in a 19 MB
download, parsed in 12 seconds**, where months of per-act harvesting had reached 1,361 of
them. Where an archive publishes an export, nothing else should be used.

**What is still missing.** The two collections this tree mostly rests on — the Rijksarchief
civil acts (`ab*`) and the Familiekunde Vlaanderen sets (`fv*`, `fwk`) — publish neither an
export nor an OAI set, so for those the per-act endpoint remains the only route. That is now
the binding constraint on ingestion, and it is a question to put to the venue rather than an
engineering problem. 18 of the 52 archives already represented in the corpus do have exports;
`harvest.py status` lists them.

The side benefit promised here has arrived with the same caveat: rarity counts stop depending
on which surnames happened to be harvested *for the archives pulled whole*, and still depend
on it everywhere else.

## 2. Storage — two tiers, not one

One Markdown file per person is right for people who have been *reasoned about*, and
impossible for millions. The split is not a compromise; it is the correct model, and it
makes an existing rule physical:

| Tier | Holds | Scale | Where |
|---|---|---|---|
| **Conclusions** | Verified identities, citations, prose reasoning | 10³–10⁵ | `data/people/*.md`, in git |
| **Corpus** | Acts, mentions, scored candidate links, clusters | 10⁷+ | Columnar store (DuckDB/Parquet), re-buildable, gitignored |

The first half of that row exists: `familytree/store.py` is a SQLite index over the harvest —
blocking keys, per-mention fields, the frequency tables, and byte offsets into the JSONL
rather than a second copy of the acts. It made a candidate lookup a query instead of a parse
of the whole corpus (`link.py`: 12 s → 0.3 s), and it carries the signature of every harvest
file so it rebuilds instead of silently lagging behind the acts.

SQLite rather than DuckDB/Parquet for one reason: it is stdlib, and `pyproject.toml`
deliberately declares no dependencies. The columnar store is the right answer at 10⁷ and the
wrong answer at 10⁵, and the schema here is ordinary enough to port when the time comes. What
should *not* change is the invariant below, which is why the index holds no evidence of its
own — deleting it loses nothing.

The invariant that keeps this honest:

> A link in the corpus is a **hypothesis with a score**.
> A link in a person file is a **decision with a citation**.

`corpus.py` already says "the corpus makes no claims"; this makes it structural. Both
BALSAC and LINKS converged on exactly this separation — with linkage as a computed,
re-runnable artefact rather than hand-asserted edges — and both arrived there at around
500,000 records, not 5 million.

## 3. Linkage — calibrate, then delegate

Order matters here. Adding scale to an uncalibrated scorer produces more wrong links
faster.

1. **Accumulate labels** ([verification](verification.md)) until the thresholds can be
   measured rather than argued.
2. **Estimate *m*-probabilities** by EM, closing the
   [known gap](linkage.md#known-gap-the-m-side).
3. **Delegate the scoring engine** to [Splink](https://github.com/moj-analytical-services/splink)
   if and when a single-process Python loop stops being enough — it does full
   Fellegi–Sunter on a DuckDB backend at 100M+ records.

What must survive that migration is the part Splink does not have: the
**two-independent-classes floor** and the **vetoes**. A probability threshold alone will
graft on a name.

## 3a. What a large harvest sets off — the ordered list

Ingestion being solved changes the other constraints rather than removing them, and it does
so in a predictable order. Recorded here because each of these is invisible until the
corpus is large and then obvious, and because the temptation on meeting one is to tune it
rather than recognise which item on this list it is.

**The rarity weights recalibrate, so every score moves.** `frequencies()` is counted from
the corpus, so a corpus ten times larger is a different measuring instrument. This is a
gain — the counts get closer to the population — but it means comparisons made before and
after a big harvest are not the same comparison. The instrument for checking it already
exists: `evaluate.py report` re-scores every past ruling with the current code, so run it
after any large ingest and read what moved. A drop in precision after a harvest is not the
harvest being wrong; it is the old thresholds having been fitted to a smaller sample.

**`surname_weight`'s two paths diverge.** It prefers the venue's own figure for a surname
(`surname_population_count`, recorded by a whole-surname harvest, filtered to Belgium) and
falls back to counting the corpus. A whole-ARCHIVE harvest fills the corpus without
recording any per-surname population, so it widens the set of surnames on the fallback
path — where the count is now measured against a corpus that is one archive's worth of one
commune, not against Belgium. The fallback is the weaker estimator and it is now used more.

**A harvest scoped by archive is not scoped by country.** The API queries were all
`country_code=be`; an export is the whole archive. `harvest.py` refuses an archive the
venue registers outside Belgium (see `out_of_scope`) because pulling one would fill the
corpus with out-of-scope records and skew the fallback above. The general answer is a
country filter at parse time, and it needs the gazetteer in §5.

**The scanning reports become the bottleneck.** `research.py acts`, `research.py children`
and `verify_all.py` genuinely touch every act, so they scale linearly with the corpus while
the targeted lookups stay flat. At a few million acts these are minutes, and that is the
signal that §2's two-tier split has stopped being optional. The index does not help them —
measured, not assumed: `verify_all.py` is slower through it.

**The index rebuild scales with the corpus, and it is rebuilt whole.** About 20 seconds per
100,000 acts. That is deliberate — an incremental index is the kind of cleverness that
quietly misses the acts fetched during the run that crashed — but past a few million acts
the rebuild wants to become incremental with a periodic full verify, not simply faster.
`harvest.py bulk` takes several archives at once for this reason: one rebuild, not nine.

**Nothing above changes what the tree claims.** Worth stating because every item here is a
change to how confident the scorer *sounds*. The two-independent-identifiers floor and the
vetoes are not statistical and do not move with the corpus, and no amount of recalibration
may be allowed to promote a graft that the floor rejects.

## 4. Clustering and cluster-level validation

At scale, links form connected components, and that is where the errors surface: a
cluster with two different birth dates, two mothers, or a lifespan of 130 years is
self-evidently wrong even when every individual pairwise link looked plausible.

Connected components plus cluster invariants is the scale version of `check_data.py`, and
it is how LINKS catches its own mistakes. `research.py components` is the seed of this.

## 5. A historical gazetteer

Place is the class that does most of the rejecting, which means a normalisation failure
silently kills **good** links. String comparison on place names cannot handle:

- the **1977 fusion of Belgian communes** — a parish and its post-fusion commune are
  different names for overlapping ground;
- **French/Dutch parallel names** — Ostende/Oostende, Gand/Gent;
- **parish ≠ commune**, which is the normal case before 1796.

Needed: a commune table with NIS/INS codes, validity intervals, and merge parentage.
Wikidata plus the NIS code lists covers most of it.

## 6. Additional evidence, in value order

**Population registers (bevolkingsregisters)** are the strongest linkage evidence that
exists: a whole household, co-resident, with stated relationships *and* birth dates *and*
migration in and out. The [Antwerp COR\* database](../prior-work.md#the-antwerp-cor-database-flanders)
is built on them for exactly this reason. Currently out of scope in the harvest, and the
first thing to add.

**Witness networks.** Already extracted (4,161 edges); not yet used as a linkage signal.
Godparents and marriage witnesses in a Flemish commune are overwhelmingly kin, and *who
recurs* across a family's acts is evidence no name comparison can reach. The natural
weighting is the one already in use: a witness appearing in two of a family's acts is
informative, one appearing in two hundred is the registrar.

**The necronym rule.** Flemish families reused a dead infant's forename for the next
child. Without an explicit rule for it, a linker either merges the two siblings or
rejects both. It needs to be a named case, not an accident of thresholds.

## 7. Sampling — how to have Flanders before having all of it

COR\*'s design is the most useful idea in the literature for this: take **every surname
beginning `COR`, plus everyone who shared a household with them.** That preserves kin and
household structure *inside* the sample, which a geographic or chronological slice
destroys.

This project's third objective — *connect all Bundervoets* — is the same manoeuvre,
arrived at independently. Generalising it into a declared, documented sampling frame is
what would turn "a large family tree" into "a research dataset with known coverage".

## 8. Privacy becomes a hard constraint

At 307 people you know everyone. At regional scale the corpus will contain living people,
and this stops being a convention:

- Belgian civil registration is public on a schedule — **deaths after 50 years, marriages
  after 75, births after 100**.
- GDPR applies to the living, including in a published static site and in a Git history,
  which does not forget.

This belongs in the validator as a rule that fails the build, not in a document that asks
people to be careful.

---

## Summary of the order

1. Bulk ingestion (unblocks everything)
2. Two-tier storage
3. Labels → calibration → *m* estimation
4. Clustering + cluster validation
5. Gazetteer
6. Population registers, then witness networks
7. Declared sampling frame
8. Privacy enforcement

Transcription of unindexed images ([LLM HTR](../prior-work.md#4-machine-reading-of-archival-documents))
is deliberately **last**. The indexed material is nowhere near exhausted, and machine
transcription is only worth automating once the linkage that consumes it can be trusted.
