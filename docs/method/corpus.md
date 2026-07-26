# The corpus

## The inversion

The search strategy that got this tree to three hundred people does not reach ten
thousand, and the reason is structural rather than a matter of effort.

**The unit of work was wrong.** A search is *person-indexed* — one query, one person. A
record is *event-indexed*. A marriage act is a single document naming six people, four of
them parents:

```
                    Huwelijk, Gent, 1901-12-21
                            │
      ┌─────────────────────┼─────────────────────┐
   bruidegom              bruid                getuigen
      │                     │                     │
  ┌───┴───┐             ┌───┴───┐            (witnesses,
vader   moeder        vader   moeder          usually kin)
```

Searching per person pays the cost of finding that act once *per person* and throws away
the other five. Harvest it once, keep it, and it answers every frontier it touches —
including frontiers that do not exist yet.

This is family reconstitution, which historical demography has done since Louis Henry;
the modern form is the IISG's [LINKS project](../prior-work.md#links-netherlands-iisg-cbg).

## The venue

[Open Archives](https://openarch.nl) publishes Dutch, Belgian and French archive indexes
as open data over an unauthenticated JSON API — roughly 30 million Belgian person
mentions, including Familiekunde Vlaanderen, the Doodsprentjes memorial cards, and the
Rijksarchief civil acts transcribed by the Demogen volunteers.

It is the venue everything rests on because it is *cheap, reproducible by anyone else,
and keeps what it finds*. It does not replace the logged-in archives; it goes first.

```bash
uv run tools/harvest.py bulk gnt                 a whole archive in ONE request
uv run tools/harvest.py oai den                  a whole archive, 150 acts a request
uv run tools/harvest.py surname Bundervoet
uv run tools/harvest.py surname "Van Craenenbroeck" --place Zaventem
uv run tools/harvest.py place Oostende
uv run tools/harvest.py frontiers --limit 5
uv run tools/harvest.py status
```

Two phases, because the API has two levels:

1. A **search** returns person-*mentions*: one row per person per act. These say which
   acts exist.
2. An **act**, fetched by `(archive, identifier)`, returns the whole record — every
   participant, their role, their age, their birthplace, the act number, a link to the
   scan. These are the evidence.

The cache is authoritative: nothing already held is re-fetched. The store is gitignored
because it is re-fetchable open data that grows without limit; `manifest.json` is
committed instead, so the exact queries — and therefore the corpus — are reproducible
from the repository alone. A partial harvest is recorded as **partial**, because a capped
harvest that looks complete is the corpus equivalent of an unlogged miss.

!!! note "Rate limiting"
    Open Archives throttles to 4 requests/second per IP and asks for a descriptive
    user-agent. The harvester deliberately runs under that. Losing access to the one open
    venue in the registry would cost far more than the wait.

## Reading acts as events

`familytree/corpus.py` normalises an act into participants with **roles**, and emits the
edges the act *asserts*. It makes no claims: turning an asserted edge into a believed one
is a decision, and decisions live in the person files under the
[rules of evidence](evidence.md).

Roles are Dutch and vary between the institutions that indexed them, so they are matched
by pattern rather than by an exhaustive list. **A role the parser does not recognise
becomes an unattached participant — which is visible — and never a silently wrong edge.**

### What the roles yield

From ~3,000 acts currently held:

| Edge | Count | Notes |
|---|---:|---|
| `witness` | 4,161 | 27% of all person-mentions |
| `mother` | 2,813 | |
| `father` | 2,775 | |
| `couple` | 2,264 | |
| `grandparent` | 359 | Two generations in a single act |
| `former_couple` | 233 | Distinguishes a remarriage from a second person |

Three of these were being discarded until recently, and they are the interesting ones:

**Grandparents** are stated outright in the Belgian marriage acts
(`other:Grootouder bruidegom`). A two-generation edge in one document is the most
expensive thing there is to establish by search. The edge is deliberately **sideless** —
the act says "grandparent of the groom" and never which of his parents it belongs to.
Recording a side would be inventing the half of the fact the record withheld.

**Previous partners** (`other:Vorige partner bruid`) are what distinguish a remarriage
from a second person of the same name. Losing them is how a widow becomes twins.

**Witnesses** are 27% of every person-mention held. They are *not* kin by the act's word,
and the corpus never records them as kin — but in a Flemish commune they are
overwhelmingly kin in fact, and *who recurs across a family's acts* is evidence no name
comparison can supply. What that is worth is decided in [linkage](linkage.md), by how
rare the witness is. Registrars (`other:Ambtenaar`) are excluded by name rather than by a
frequency cut-off, because a cut-off can be tuned past them.

## Frequencies

The corpus is also the population count. Agreement on *Janssens* and agreement on
*Schalandrijn* are not the same evidence, and only a population can say by how much.

The subtlety that cost this project a correction: **a harvest is filtered to the surname
it was run for**, so counting rarity inside the harvest makes every harvested surname
look common — exactly inverting the truth. Rarity is therefore measured against the
venue's total holdings where that figure is known, and only against the harvest when it
is not, with the estimate flagged as an estimate.
