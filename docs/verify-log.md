# Verification log

One row per verification pass, newest at the bottom. This is an index into
[research-log.md](research-log.md) and the git history, not a second copy of either.

`bucket` is where `uv run tools/verify_all.py` had the person: CORROBORATED (a date or
place agrees, not only names), KIN-ONLY (names and a relative, nothing anchored), PARTIAL,
NOT REACHED (nothing held under that surname).

`verdict`: DOCUMENTED (act read) · CORROBORATED (index agrees, act unread) · LEAD ·
REJECTED · NOT FOUND · BLOCKED · NEW SOURCE (a venue the registry lacked).

NOT FOUND is earned, not assumed: it means the venue ladder was walked to the bottom
*and* a search was made for a venue the registry does not have. The row names the
venues. A single miss at one archive is not a negative — it is one archive missing.

| pass | date | person | bucket | verdict | evidence | commit |
|------|------|--------|--------|---------|----------|--------|
| 1 | 2026-07-26 | leonie_p | CORROBORATED | NOT FOUND | AGATHA holds no Sint-Niklaas 1901 birth acts — 8 Paelinck records there, none ours. Stays `sup`. | — |
| 2 | 2026-07-26 | — (method) | — | — | Janssens: 121,923 mentions capped at 600 = 0.5% held. Queued 126 surname+commune harvests so common surnames are fetched where our people actually lived. | — |
| 3 | 2026-07-26 | georges1_t | CORROBORATED | DOCUMENTED | Grez-Doiceau death act nr. 58, read + saved. Death 20/11/1808 and *menuisier* both confirmed. | 60fe2b0 |
| 3 | 2026-07-26 | jeanlambert_t | — | DOCUMENTED | Named as father in the same act. | 60fe2b0 |
| 3 | 2026-07-26 | leclercq_t | — | DOCUMENTED | Named as mother in the same act. | 60fe2b0 |
| 3 | 2026-07-26 | noel_t | — | DOCUMENTED | Named as partner (as *Noé*) in the same act. | 60fe2b0 |
| 3 | 2026-07-26 | georges1_t | — | CONFLICT | Act gives age 60 → birth ~1747-48; tree says 1744-03-14. Left open; Grez-Doiceau baptisms would settle it. | 60fe2b0 |
| 4 | 2026-07-26 | joostens | CORROBORATED | DOCUMENTED | Grez-Doiceau death act nr. 35 read + saved. Death fixed to 10/06/1857; *ménagère*; birthplace confirmed. | 90009d6 |
| 4 | 2026-07-26 | guillaume_joostens | — | DOCUMENTED | Named as father in the same act — the act behind last pass's index entry. | 90009d6 |
| 4 | 2026-07-26 | jeanne_deconninck | — | DOCUMENTED | Named as mother in the same act. | 90009d6 |
| 4 | 2026-07-26 | georges2_t | — | CONFLICT | Act gives him age 63 → birth ~1793-94; tree says 1804-01-24. Wife's age in the same act is right. Left open. | 90009d6 |
| 5 | 2026-07-26 | georges2_t | CONFLICT | NOT FOUND | No Thumas act of 1864 in AGATHA's Grez-Doiceau index (392 records there, early 1800s). Age conflict stays open. | cbef785 |
| 5 | 2026-07-26 | — (method) | — | — | AGATHA's Plaats and Periode filters match anything mentioned in an act, not the act's own commune/date. Read the result list, don't trust the filter. | cbef785 |
| 6 | 2026-07-26 | georges1_t | CONFLICT | LEAD | FamilySearch has 1,409 Thumas/Grez-Doiceau records vs AGATHA's 392. Its 'birth 1748' is derived from the 1808 act's age — not independent. Sister Catherine Josephe (b.1745) leans toward 1744. | 81b5705 |
| 6 | 2026-07-26 | — | — | NEW SOURCE | Registered two FamilySearch Brabant collections. The ladder's step 2 was never used; it outperforms step 3 by 3.6x on this commune. | 81b5705 |
| 6 | 2026-07-26 | — (tooling) | — | BLOCKED | Validator crashed: corpus parser assumes EventPlace.Place is a string; archive `sla` returns `{'@TranscriptionRemark':…, '$': 'Lommel'}`. 20 rows quarantined to go green. Needs a fix in familytree/corpus.py. | 81b5705 |
| 7 | 2026-07-26 | leonie_p | NOT FOUND (p1) | CORROBORATED | **Reverses pass 1.** FamilySearch has the 1901 Sint-Niklaas birth act nr. 997 that AGATHA lacks, with both parents. | 19920ff |
| 7 | 2026-07-26 | eduardus_p | — | CORROBORATED | Named as father on the same act. | 19920ff |
| 7 | 2026-07-26 | magdalena_vb | — | CORROBORATED | Named as mother on the same act. | 19920ff |
| 7 | 2026-07-26 | — (method) | — | — | FamilySearch's place filter returns 0 for a surname with 3,259 Belgian records. Filter by name, read the results. | 19920ff |
