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
x:<phonetic surname, first 6 chars>   # truncated and extended forms
pd:<phonetic>:<birth decade>          # tightened by date
pp:<phonetic>:<place>                 # tightened by place
g:<first forename>:<birth decade>     # survives a surname nobody spelled twice
```

A pair agreeing on **any** key is compared; a pair agreeing on none never is. That is
what keeps this off the O(n²) curve as the corpus grows.

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
