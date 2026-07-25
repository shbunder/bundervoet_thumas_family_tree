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
| 8 | 2026-07-26 | bernardus | NOT REACHED | NOT FOUND | Ladder walked: corpus (396 acts, none above noise) → FamilySearch (4 name hits, all fuzzy non-matches; filters don't constrain) → AGATHA (**zero** Bundervoet records for Evergem). | 8f3cafa |
| 8 | 2026-07-26 | — | — | NEW SOURCE | `fv-dataindexen` — Familiekunde Vlaanderen indices. Covers Evergem deaths 1796-1970 and **Oostende**. Found by the discovery step. | 8f3cafa |
| 9 | 2026-07-26 | — | — | NEW SOURCE | **The pre-1796 layer.** FV Totaalindex covers every commune in the tree: Oostkamp 1631-1792, Woumen 1595-1796, Evergem burials 1682-1796, Belsele 1585-1796, +. Reaches the 158 people no other venue can. | 0583a1e |
| 9 | 2026-07-26 | joannes_b | — | LEAD | His 1760 Evergem death falls inside FV's burial index 1682-1796 — the act whose only scan was an illegible 230×38 crop. Not yet retrieved: the search UI needs real clicks. | 0583a1e |
| 10 | 2026-07-26 | joannes_b | — | NEW SOURCE | FV Totaalindex queried. **Bundervoet in 17 parishes of arr. Gent**, tree has 1 (Evergem). First map of the Bundervoet forest — objective 3. | 1291614 |
| 10 | 2026-07-26 | — (method) | — | — | The Totaalindex is a *finding aid*: surname × parish × d/h/o flags. Never a person or date — nothing from it is graftable. | 1291614 |
| 11 | 2026-07-26 | — | — | NEW SOURCE | **COD Oostende catalogue** — ~75 indexes incl. Volkstelling 1798 Oostende, Kiezerslijsten 1902/1914, Huwelijksbijlagen microfilms, rouwbrieven. First venue indexing Oostende at household level. | 70321eb |
| 11 | 2026-07-26 | carolus_ramon | NOT REACHED | NOT FOUND | Not in the Heist-De Panne drowned-fishermen list (searched with `bevat`, table sanity-checked). Other COD tables untried. | 70321eb |
| 11 | 2026-07-26 | — (method) | — | — | COD's `Familienaam` column holds FULL names — `=` finds nothing, use `bevat`. A negative taken with `=` is worthless. | 70321eb |
| 12 | 2026-07-26 | elodia | NOT REACHED | NOT FOUND | COD Rouwbrieven has 7 Bostyns, none hers. Table verified populated, so this is a real negative. | 1d5fc20 |
| 12 | 2026-07-26 | henricus_bostyn | NOT REACHED | BLOCKED | Huwelijksbijlagen Oostende returns nothing for any query — a catalogue stub; microfilms are on-site only (O-1013MM). | 1d5fc20 |
| 12 | 2026-07-26 | — (method) | — | — | COD tables are not uniformly populated. Test with a broad query before trusting a negative. | 1d5fc20 |
| 13 | 2026-07-26 | joannes_b | — | NOT FOUND | FamilySearch's indexed Oost-Vlaanderen content is 19th-c civil registration; 99 Joannes Bundervoet hits, none the 1760 Evergem burial. Parish registers aren't name-indexed. | 648d2ca |
| 13 | 2026-07-26 | petrus_bundervoet1560 | — | **NEW SOURCE** | **FamilySearch full-text.** Machine-reads unindexed manuscripts back to 1463. 159 Bundervoet hits incl. a 3-generation fief chain 1687-1700. The route to the 158 pre-1796 people. | 648d2ca |
| 14 | 2026-07-26 | petrus_sabbe | — | **NEW SOURCE** | Full-text reaches the Oostkamp block via **staten van goed** (Belgium Court Records 1639-1795) — estate inventories naming spouse + every child with ages. | 043ef34 |
| 14 | 2026-07-26 | petrus_wittenheyns | — | LEAD | Only full-text hit: a 1657 Bruges notarial deed naming 'Lieuen wittenheyns haer broeder'. Right region, wrong century. Not grafted. | 043ef34 |
| 14 | 2026-07-26 | — (method) | — | — | A thin surname result ≠ thin coverage. Wittenheyns is rare; 'Sabbe Oostkamp' returns thousands. Search surname + commune. | 043ef34 |
| 15 | 2026-07-26 | petrus_sabbe | — | NOT FOUND | Could not pinpoint his 1652 staat van goed: full-text ORs multi-word queries (101k hits) and its year/collection filters resist scripting. A tool limit, not a statement about the document. | d52ec9d |
| 15 | 2026-07-26 | — (method) | — | — | Full-text is a **discovery tool, not a lookup**. It proves a family is present in a body of records; it won't hand you one person's act. Budget for hand-filtering. | d52ec9d |
| 16 | 2026-07-26 | georgeslambert_t | — | NOT FOUND | No Grez-Doiceau death act for 1863 in AGATHA. | 11623eb |
| 16 | 2026-07-26 | — (correction) | — | — | **Pass 5's inference was wrong.** AGATHA's Grez-Doiceau Thumas coverage does *not* stop at 1859 — it reaches 1911. Specifically the 1860s *death* acts are missing. | 11623eb |
| 17 | 2026-07-26 | — (artifact) | — | — | Retook the full-text artifact: the first capture had a promo modal over the results. | 067bf0b |
| 17 | 2026-07-26 | petrus_bundervoet1560 | — | **CORRECTION** | Read the actual page. Snippets had merged two surnames: 'Meirelbeke 1587' is VAN DEN BUNDERE, not Bundervoet. Real entries: Saint-Pierre-Alost 1687-1701. Two dates also wrong. | 067bf0b |
| 17 | 2026-07-26 | — (method) | — | — | **Artifacts should be the document, not the index page about it.** A snippet merges adjacent entries; the page does not. | 067bf0b |
| 18 | 2026-07-26 | leonie_p | CORROBORATED | **DOCUMENTED** | Register page read: Sint-Niklaas 1901 act nr. 997, image 268/337. | aa3b302 |
| 18 | 2026-07-26 | eduardus_p | — | **DOCUMENTED** | Named as father *geboortig te Belsele* — birthplace independently confirmed. | aa3b302 |
| 18 | 2026-07-26 | magdalena_vb | — | **DOCUMENTED** | Named as mother, *huishoudster* — occupation new. | aa3b302 |
| 19 | 2026-07-26 | augusta | CORROBORATED | CORROBORATED | Parentage now attested by 3 siblings' Oostende acts naming both parents — civil registration, not the stechec tree. | 4fea424 |
| 19 | 2026-07-26 | clementia_w, petrusjacobus_v | — | CORROBORATED | Named together as parents on all three acts. | 4fea424 |
| 19 | 2026-07-26 | — (frontier) | — | LEAD | 3 siblings of Augusta not in the tree: Henricus Emilius (1877-1941), Leontius Ivo, Paula Mathilde. Objective 2. | 4fea424 |
| 19 | 2026-07-26 | — (method) | — | — | **Search the rare maternal surname.** Her given name found nothing; Wagebaert isolated the household immediately. | 4fea424 |
| 20 | 2026-07-26 | +18 people | — | ADDED | **Policy change: be generous.** Transcribing a documented child ≠ identifying a person. 309 → 327. | 4eeeeee |
| 20 | 2026-07-26 | henricus_e_v, leontius_v, paula_v | — | ADDED | Augusta's siblings, from Oostende civil acts naming both parents. | 4eeeeee |
| 20 | 2026-07-26 | marie_anna_dedeckere +8 | — | ADDED | Pieter Bundervoet's wife and all eight children (paulderidder). | 4eeeeee |
| 20 | 2026-07-26 | livinus_b1615, maria_b1623, catharina_vanhecke, wilhelmina_b1650 | — | ADDED | Segerius's siblings, his father's 2nd wife and her daughter. | 4eeeeee |
| 20 | 2026-07-26 | etienne_thumas, henrica_thumas | — | ADDED | From the 1812 Grez-Doiceau death act and the 1899 Kraainem marriage index. | 4eeeeee |
