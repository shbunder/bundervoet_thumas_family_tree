# Record linkage

How a person in the tree is compared with a person in an act, without comparing everybody
with everybody, and without treating every agreement as worth the same.

Two ideas, both borrowed. See [Prior work](../prior-work.md#2-statistical-record-linkage).

---

## Blocking

Never compare all pairs. Group records by cheap keys that a true match *must* share, and
compare only inside the groups.

Several keys, not one — because any single key is blind to the variant it cannot see. A
phonetic key misses *Vanstechele* against *Vanstechelman*; a date key misses an undated
record.

```python
p:<phonetic surname>                  # the main pass
x:<phonetic surname STEM, 4 or 6>     # truncated and extended forms — see below
pd:<phonetic>:<birth decade>          # tightened by date
pp:<phonetic>:<place>                 # tightened by place
g:<first forename>:<birth decade>     # survives a surname nobody spelled twice
```

A pair agreeing on **any** key is compared; a pair agreeing on none never is. That is
what keeps this off the O(n²) curve as the corpus grows.

### The prefix key strips the particle, and its length adapts

The `x:` key was `ph[:6]` — the first six characters of the phonetic surname — and in Flemish
that is usually the *particle*, which says nothing about the family. A quarter of these
surnames begin "Van den", "Van der" or "De", so the key put 150,611 mentions under `fanden`,
137,463 under `defade` and 116,538 under `fander`: **17% of a 1.7-million-act corpus in
fourteen buckets.** A block holding a sixth of the population is not blocking, it is a scan
with extra steps, and it is what made `research.py acts` take seven minutes.

Stripping the particle also *fixes* a case the old key missed. "Vandenberghe" and "Van
Berghe" share no six-character prefix at all (`fanden` against `fanber`) and were never
compared; on the stem both are `berge`.

How much of the stem to keep depends on how long it is, and that took two measurements:

- a **short** stem needs generosity, because a single trailing character decides everything —
  "Vandevelde" and "Vandevelden" have stems `felde` and `felden` and are one family, which
  four characters bridges;
- a **long** stem needs none, and four characters actively harm it. "Wittenheyns" has the stem
  `fitenheins`; cut to four it is `fite`, which is also what "De Witte" reduces to. A surname
  with no exact match anywhere in the corpus was pulling 28,089 mentions of an unrelated
  family, and throwing away six highly discriminating characters to do it.

Measured against the 223 open frontiers, mentions pulled through this key:

| scheme | mentions pulled | |
|---|---|---|
| `ph[:6]`, as it was | 2,542,433 | the particle ate the prefix |
| `stem[:4]` | 1,282,568 | particle stripped, fixed length |
| `stem`, adaptive | **941,505** | this |

Both later schemes keep all seven variant pairs the key exists for; only the adaptive one
*also* keeps Wittenheyns and De Witte apart. These are strict improvements rather than
trades — nothing that was compared before is uncompared now.

Below four characters the particle was most of the name and what remains cannot discriminate
("Devos" would become `fos`), so those keep the whole phonetic form instead. The stem is used
for **blocking only**: `family_key` and `phonetic` still decide whether two surnames *agree*,
and this only decides which pairs are worth comparing at all.

### Flemish phonetics

Flemish orthography drifted for centuries, and the same family is spelled several ways
within this tree's own records. The folding rules are deliberately **conservative**:

```
ij → i     y → i        Bostyn      → Bostin
sch → s                 Dutch -sch is a plain s
ck → k     c → k        Craenenbroeck → Kraenenbroek
gh → g     ph → f       th → t
ae → a     oe/ou → u    uy/ui → u
z → s      w → v        v → f
dt$ → t    d$ → t       Devriendt   → Defrient
(doubled letters collapse)            Stroobandt → Strobant
```

Over-folding merges families, and a merged family is the failure this project exists to
avoid. So the rules fold variations *known to occur here*, and the test suite pins both
directions: `Bostyn`/`Bostin` must fold, `Janssens`/`Jansen` must not.

---

## Weighted scoring

Agreement is worth what the value is rare, measured in **bits of surprise**:

$$\text{bits} = \log_2 \frac{N}{\text{count}}$$

Two people both called *Janssens* have told you almost nothing. Two people both called
*Schalandrijn* have told you almost everything.

This is the **u-probability** of the Fellegi–Sunter model, counted rather than assumed.
Weights are capped at 14 bits: a surname seen once is very strong evidence, not infinite
evidence.

### Where the counts come from

Rarity is measured against the **venue's whole Belgian holdings** where that figure is
known, and against the harvest only when it is not — with the fallback flagged as an
estimate. This matters more than it sounds: a harvest is filtered to the surname it was
run for, so *Van Craenenbroeck* made up 14% of the corpus and would have been scored as
one of the most common names in Flanders. Population counts invert that back.

### Bits beyond the name

The total score is not the interesting number. A rare surname is enormous evidence of the
same **family** and almost none of the same **person** — every Bundervoet in Belgium
agrees on it, including the 396 who are not this man.

So `Match` reports `distinguishing` separately: the evidence that is *not* the name.
Banding on the total let a bare surname clear the bar and buried the real matches under
two hundred relatives.

| Band | Condition |
|---|---|
| `strong` | ≥12 distinguishing bits, ≥2 independent classes |
| `read the act` | ≥6 distinguishing bits, ≥2 independent classes |
| `noise` | anything less |
| `rejected` | any stated conflict |

### A near miss is corroboration, not identification

An **exact** birth-year agreement is one of the two identifiers a graft needs. A year off by
one or two is not, and it now sits in a weak class — it still scores its two bits, because it
is worth noticing, but it cannot carry a graft.

This was suspected long before it could be shown: *"birth year ±1 is nearly free when the tree
holds a bare year."* The gold standard settled it. Once act-level rejections became scoreable,
both Van Bergen rivals turned out to have reached graftable on exactly this — surname plus a
±1 year — with the wrong province, the wrong parents and the wrong death year in each case.
Demoting it took precision from 88.9% to **96.0% and lost no true match at all**.

The alternative the sweep offered was raising the floor from two agreeing classes to three.
That kills all three false positives — and one true match with them, and it would contradict
rule 1 of the charter, which says two. Fixing something that was never an identifier is not
the same as raising the bar, and only one of the two is available to us.

---

## The kin class

The identifier the rules always named and the scorer did not have until recently.

Each candidate carries the relatives its side names, as `(bucket, surname key, forename
keys)`. Only **like buckets** are compared — a father in the tree answers a father in an
act and nothing else. Matching one person's father against another's husband is precisely
the class of error the two-identifier rule exists to stop.

`spouse` and `former spouse` share a bucket, because a remarriage is one person's two
marriages and keeping them apart is how a widow turns into twins.

Weighting has one wrinkle worth stating: **a father shares his son's surname**, so
counting it again would count the principal's own name twice. A mother's maiden name is
new information every time — which is why it is the classic second identifier.

---

## Vetoes

Scoring ranks; vetoes reject. Defaulting to rejection is the whole posture.

- **Sex disagrees.** Derived from the links where the record omits it, because the data
  model says being a father or a mother already settles it. Reading the omission as
  "unknown" made every parent comparable with every candidate of the opposite sex.
- **Stated birth years differ by more than 2.** Only *stated* values veto — a year
  implied by an age in an act carries slack and must never kill a true match alone.
- **Day-level birth dates differ.**
- **Born after the other died.** Both ways round, because callers pass the pair in both
  orders and a possibility test that is not symmetric is not a possibility test.
- **Implied lifespan over 110 years.** Kills the grandfather-grafted-onto-grandson case,
  which recurs because the forename returns every second generation.
- **A parent born after their own child.** An act that says "X is the father of Y" and dates
  Y has bounded X's birth, and reading that bound is free. It vetoes even where the parent
  mention carries no date at all — which is the case it exists for, and the case nothing else
  can reach. A Brussels marriage of 1888 naming Charles Thomas Jean Van Iseghem as father of a
  groom born 1856 scored 29.7 bits against a Joannes Van Iseghem born 1852, on surname,
  forename and commune, with no veto able to fire. The act states both halves.

### The same name in another language

Flanders wrote its registers in Latin, then in French, then in Dutch. So one man is **Joannes**
at his baptism, **Jean** at his marriage and **Jan** at his death, and until
[`data/forenames.json`](../data-model.md) existed those were three unrelated names. It is not a
small effect: `joannes` + `jan` + `jean` is 353,553 mentions, **8% of every person the corpus
names**; `petrus` + `pieter` + `pierre` is 232,893; `maria` + `marie` is 449,453.

The table is **data, not code** — the surname phonetic rules are regex patterns containing no
names, and these are names. It is also **curated, not learned**, and that is the interesting
part. Measured over the obvious candidates:

| fold these | | never fold these | |
|---|---|---|---|
| Henricus / Hendrik | 0.67 | Ludovicus / **Ludovica** | 0.82 |
| Joannes / Jan | 0.60 | Franciscus / **Francisca** | 0.84 |
| Ludovicus / Lodewijk | 0.35 | Augustinus / **Augustina** | 0.84 |

The distributions are **inverted**, so no similarity threshold separates them — and the first
thing a threshold reaches for is a brother and his sister, in a tree that leans on a sex veto.
Learning the pairs from confirmed matches is the other trap: that equivalence would not be
independent of the match that taught it, which manufactures a second identifier out of the
first and inflates confidence on exactly the borderline pairs.

So the table is split by sex, and a fold can never cross the partition **by construction**
rather than by a check. The split does not license reading sex off a forename — the data model
forbids that and it stays forbidden. A folded agreement is scored below an exact one, the same
way a phonetic surname variant is, because a fold is a claim that could be wrong.

### Every veto reads what a date *rules out*, never what it says

The [date grammar](../data-model.md) has forms for a year, an *about*, a *before*, an
*after* and a *between*, and each answers two different questions:

| | asserts (`point_year`) | permits (`year_span`) |
|---|---|---|
| `1876-11-12` | 1876 | 1876 – 1876 |
| `~1682` | 1682 | 1677 – 1687 |
| `<1727` | — | ? – 1727 |
| `>1900` | — | 1900 – ? |
| `1575..1587` | — | 1575 – 1587 |

Evidence reads the left column, so `~1682` still earns its bits against an act saying 1682.
Vetoes read the right one and fire only when **no** year satisfies both — an open end means
unknown, and unknown never vetoes.

Reading a single number for both is a bug that costs recall in silence, and it was in here
for months. `1920..1929` flattened to "1920", so an act stating 1925 was rejected as
*conflicting* with a range that contains it — the one thing a record admits it does not know
becoming a reason to refuse every record that would have told us. 81 of 434 records carry a
non-point date. The same flattening was applied a second time as a SQL pre-filter over the
index, which dropped those mentions before the scorer could see them and left no trace at
all.

The corollary is a rule about the *data*, not the code: a date the grammar **can** hold does
not belong in `raw`. A record whose only date was prose was, to the matcher, entirely
undated — which is how a boy born 1901 was offered as a man whose birth was declared in
1847, with nothing able to veto it.

### The veto rule lives in three places, and that is a cost being paid on purpose

`match.compare` is the definition. But `store._veto_sql` re-states two of the vetoes — sex,
and a stated birth year — as a SQL `WHERE` clause, and `check_data._check_plausibility`
re-states the age and lifespan bounds as build-time warnings. Three copies of a rule is
exactly what the rest of this project forbids, so it is worth being explicit about why these
survive:

- **The SQL copy buys the corpus.** A common Flemish surname now blocks against tens of
  thousands of acts, and reading each one so the scorer could reject it on a birth year two
  centuries out was most of the cost of a lookup. It is a *pre-filter*, conservative by
  construction — an unknown sex, an absent year and an implied-rather-than-stated year all
  survive it — so it can only ever be a performance change, never a decision. The equivalence
  is pinned by a test against the scanning route rather than argued.
- **The validator copy asks a different question.** `compare` asks "could these two records be
  one person"; the validator asks "is this tree internally plausible", and it *warns* where the
  scorer *vetoes*, because a record can be right and strange and no validator gets to overrule
  a document.

What keeps them from drifting is that the numbers themselves are not duplicated:
`MIN_PARENT_AGE`, `MAX_LIFESPAN`, `MAX_MOTHER_AGE` and `MAX_FATHER_AGE` are defined once in
`familytree/people.py` and imported by both readers. They were not always — the validator
hardcoded `110` eleven lines below the import that would have named it — and that is the form
this kind of duplication actually fails in.

---

## What this does *not* do

It does not decide. It ranks, and it vetoes. Everything surviving is a **candidate for
the verifier to try to refute**, and the two-independent-classes rule is enforced as a
floor no score can buy its way past.

## Known gap: the *m* side

Fellegi–Sunter has two probabilities. This implements **u** (how often an agreement
happens by chance) and not **m** (how often a *true* match still disagrees, because a
clerk misheard a name or a widow's age was estimated).

Without *m*:

- a disagreement caused by transcription cannot be distinguished from a disagreement
  caused by it being a different person;
- the weights are relative rather than calibrated, so thresholds like "6 distinguishing
  bits" are reasoned judgements rather than measurements.

Closing it needs labelled data, which is what
[verification and measurement](verification.md) is for, and eventually either an EM
estimator or [Splink](https://github.com/moj-analytical-services/splink).
