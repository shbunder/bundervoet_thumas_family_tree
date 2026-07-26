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
| 21 | 2026-07-26 | louise_bocklandt | CORROBORATED | CORROBORATED | Death fixed to **15 Jul 1946** Oostende, and a **second husband — Petrus Blomme**, after the ~1923 divorce from Édouard. | 8eb229a |
| 21 | 2026-07-26 | carolus_vb, martinet | CORROBORATED | CORROBORATED | Couple attested by their son's 1909 Sint-Niklaas marriage act. | 8eb229a |
| 21 | 2026-07-26 | alphonsus_vb | — | ADDED | Their son, brother of magdalena_vb, from the same act. 328 people. | 8eb229a |
| 21 | 2026-07-26 | — (tooling) | — | — | Second `_text()` gap fixed: person-level place/residence/profession/age also arrive as dicts. verify_all crashed on it. | 8eb229a |
| 22 | 2026-07-26 | hubert_devriese | CORROBORATED | REJECTED | b.1665 Tielt matched to a **1911 Brussels** marriage. ~200 years out. | 69665d9 |
| 22 | 2026-07-26 | edouard_dk | CORROBORATED | REJECTED | d.1951 matched to a 1963 Oostende death (Albert Dekeyser). | 69665d9 |
| 22 | 2026-07-26 | gustaaf | CORROBORATED | REJECTED | Matched via **Simonne Barbier** d.2016 — because his wife was also a Simonne. | 69665d9 |
| 22 | 2026-07-26 | joannes_jos_vi, joannes_vi2 | CORROBORATED | REJECTED | Van Iseghems with different forenames (Jacobus; Charles Thomas Jean). | 69665d9 |
| 22 | 2026-07-26 | — (finding) | — | — | **The bucket is still too generous.** All five anchored on a big commune merely *appearing* in the act, with kin agreement on a forename. §43's rule was necessary, not sufficient. | 69665d9 |
| 23 | 2026-07-26 | — (scorer) | — | — | **Fixed §44's two leaks.** The act's own commune and a relative's forename now add bits but cannot be an independent identifier. Corroborated 35 → 26. | 708acd7 |
| 23 | 2026-07-26 | hubert_devriese, edouard_dk, gustaaf, joannes_vi2 | CORROBORATED → KIN-ONLY | — | All four false positives dropped out of the corroborated bucket; joannes_jos_vi dropped out entirely. | 708acd7 |
| 23 | 2026-07-26 | louise_bocklandt, augusta | — | — | The genuine ones stayed. 3 regression tests added; 62 pass. | 708acd7 |
| 24 | 2026-07-26 | — (scorer) | — | — | Four more leaks closed: act-year veto; forename-only *name* demoted; kin needs a **new** surname; surname disagreement blocks a graft. | b5f0e66 |
| 24 | 2026-07-26 | — (bug) | — | — | **Every participant in a death act was given the act's year as their own death year** — including living fathers. Now only the deceased. | b5f0e66 |
| 24 | 2026-07-26 | 12 verified people | — | — | All stayed CORROBORATED across every change — the discriminating test. 9 of 11 known-wrong dropped out. 63 tests. | b5f0e66 |
| 25 | 2026-07-26 | eugenius_dv, octavia_schal | CORROBORATED | DOCUMENTED | Oostende marriage act nr. 258, 10 Nov 1906 (S20), read as an image. Both moved to `doc`. | — |
| 25 | 2026-07-26 | octavia_schal | — | CORRECTED | Bredene birth act nr. 116 (S21): born **30 April 1886**, not 2 May — the tree had been holding the certificate's date as the birth. | — |
| 25 | 2026-07-26 | ludovicus_dv, silvia_brissinck, ludovicus_schal, mathilde_standaert | — | NEW | Four parents transcribed from S20, which names both couples. `doc` on what the act states; every index lead left as a named frontier. | — |
| 25 | 2026-07-26 | mathilde_standaert | — | DOCUMENTED | S21 states her age (42) and "geboortig van Brugge". The birthplace is the act's; the ~1844 birth year it implies is **not** recorded — an age is not a date. | — |
| 25 | 2026-07-26 | emma_vincke | PARTIAL | CORROBORATED | AGATHA index: Diksmuide birth act nr. 14, act date 24 Jan 1880, *Emma Celesta Vincke* — one day after the held birth. Index only, stays `sup`. | — |
| 25 | 2026-07-26 | lucien_vincke | — | LEAD | A probable elder daughter, *Romanie Elodie Vincke*, Diksmuide 8 Oct 1873, both parents matching by full name. Not grafted: index only, and "Lucien Julien" ≠ the "Lucien Julianus" held here. | — |
| 25 | 2026-07-26 | adrienne_dv | — | CORROBORATED | vrijwilligersrab Geboorten: Stene, 12 April 1908, act 29 — to the day. Index only, stays `sup`. | — |
| 25 | 2026-07-26 | — (registry) | — | NEW SOURCE | `rab-bs-huwelijken` and `rab-bs-geboorten` registered under vrijwilligersrab. The site's own description named marriages and deaths; it carries births too. | — |
| 25 | 2026-07-26 | — (correction) | — | — | **Two sessions allocated source id S19 to different acts.** Caught by the validator, not by either session. See §46. | — |
| 26 | 2026-07-26 | guilielmus_bossin, peremans | CORROBORATED | DOCUMENTED | Their own marriage act — Zaventem nr. 1, 24 Feb 1846 (S19), read as an image. Both aged 21, confirming the 1824 both carried from a member tree; birthplaces new. | — |
| 26 | 2026-07-26 | peremans | — | RESOLVED | The Joanna/Anna Catharina forename dispute goes **the tree's way**: the act that married her writes *Joanna Catharina Jacoba* in full. The 1872 act's shorter form is the outlier. | — |
| 26 | 2026-07-26 | arnoldus_bossin, elisabeth_deyn, egidius_peremans, joanna_verelst | — | NEW | Four parents named by S19. The Bossins living, present, unable to write; both Peremans parents dead — Zaventem 6 Mar 1837 and 19 Dec 1843, dates given exactly by the act. | — |
| 26 | 2026-07-26 | joanna_verelst, egidius_peremans | — | DEAD END (documented) | The bride declared, with her witnesses, that **she had never known her grandparents nor where they died**. That generation is unreachable through the family and must come from registers. | — |
| 26 | 2026-07-26 | bossin | NOT REACHED | NOT FOUND | Her 1849 Sint-Stevens-Woluwe birth act: AGATHA holds **only marriages** for that commune. Not a name failure — the birth series is absent. Her parents' 1846 marriage was found instead. | — |
| 26 | 2026-07-26 | petrus_f | — | BLOCKED | Oostende 1943. Post-1900 Oostende civil registration is in no open index; it is at the Stadsarchief, offline. Needs a visit, not another search. | — |
| 26 | 2026-07-26 | — (tooling) | — | — | `_api_date` took the validator down mid-run on a harvested act whose month read `ca`. Unparseable parts are now **dropped, never guessed**. 64 tests. | 3af3326 |
| 27 | 2026-07-26 | egidius_peremans, joanna_verelst | — | NOT FOUND (coverage) | **AGATHA holds no Zaventem death acts of any year.** Plaats=Zaventem + Overlijdensakten with no name returns 58 acts, none of them Zaventem's — all merely mention it. There is no Vlaams-Brabant death project in the index. | — |
| 27 | 2026-07-26 | anna_maria_bossin | — | NEW | A sister for Guilielmus Bossin. Sint-Stevens-Woluwe marriage act nr. 9, 1 Dec 1853 (S22): same parents named, and he witnesses in person. Born 3 Nov 1829, to the day. | — |
| 27 | 2026-07-26 | guilielmus_bossin | — | DOCUMENTED (2nd act) | **29** in Dec 1853 against **21** in Feb 1846 — the windows overlap only in 1824, between late Feb and early Dec. Two acts seven years apart agreeing on a year held from a member tree. | — |
| 27 | 2026-07-26 | franciscus_pardon, guilielmus_pardon, maria_anna_pergijsels | — | NEW | The Pardon household of Winksele, married in via Anna Maria. All three transcribed from S22. | — |
| 27 | 2026-07-26 | arnoldus_bossin | — | EXTENDED | Alive and consenting on 1 Dec 1853, so his death bound moves seven years. *Daglooner* here where 1846 said *arbeider*; each act keeps its own word. | — |
| 27 | 2026-07-26 | elisabeth_deyn | — | NOT INFERRED | S22 gives her as a bare name where it gives her husband residence, trade and consent. Absence in a transcription is not death: her bound stays at 1846 and nothing is read from the silence. | — |
| 27 | 2026-07-26 | guilielmus_pardon | — | NOT FOUND | The Bossin × Deyn marriage itself. Only 11 acts in all of AGATHA match Bossin+Deyn; both relevant ones name them as parents. Their own act is not indexed. | — |
| 28 | 2026-07-26 | georges2_t | — | NOT FOUND ×2 (coverage) | Both routes to the 1804/1794 age conflict are closed at AGATHA. Grez-Doiceau **births are indexed for 1813–14 only** (57 acts, no other year); deaths are near-complete for 1860 then 2–4/year to 1874, with no Georges among them. Needs register images. | — |
| 28 | 2026-07-26 | georges2_t | — | REFINED | The earlier note compared only the father's *birth* year and called the link neutral. It missed the **marriage**: his parents married 9 Feb 1801, so a birth in 1793–94 precedes it by seven years. Weight moves to 1804; still not proof. | — |
| 28 | 2026-07-26 | — (method) | — | — | **A reported age is not one number but two kinds.** The 1857 act got the *deceased's* 47 right and gave the *surviving spouse* 63. Those are not equally checked figures, and one being right says nothing about the other. | — |
| 28 | 2026-07-26 | — (trap) | — | — | All 18 Thumas hits in Grez-Doiceau death acts 1860–80 are **Charles Julien Thumas as *Belanghebbende***, a commune official in dozens of acts. A standing name-and-place trap on this line. | — |
| 29 | 2026-07-26 | georges2_t | PARTIAL | **DOCUMENTED** | **His own death act, read as a register image** (S23). *Le douze janvier mil huit cent soixante quatre… Georges Thumas, veuf de Marie Catherine Joostens, fils de Lambert Georges Thumas et de Marie Catherine Quinart, décédés.* Death date and parent link both move off Geneanet and onto civil registration. | — |
| 29 | 2026-07-26 | georgeslambert_t, quinart | — | DOCUMENTED (first evidence) | Both named as parents of the deceased, both *décédés* by Sept 1868. These records had rested **entirely** on Geneanet; this is their first document of any kind. | — |
| 29 | 2026-07-26 | georges2_t | — | STILL OPEN | The extract gives **no age**, so §49's 1804-vs-1794 conflict is untouched by it. | — |
| 29 | 2026-07-26 | — (method) | — | **NEW ROUTE** | **Death acts hide in marriage annexes.** AGATHA has no Grez-Doiceau 1864 death act, but the extract survives inside the *marriage* volume as a huwelijksbijlage. This is the way into every commune whose death series is unindexed. | — |
| 29 | 2026-07-26 | georges_cj | — | LEAD | The extract was drawn 28 Sept 1868 *for a marriage*, so a **sibling** of his married at Grez-Doiceau around then. Same volume, near image 221. | — |
| 30 | 2026-07-26 | cornelius_bossin, ludovica_bossin | — | NEW | Two siblings for Antonia, from Sint-Stevens-Woluwe birth declarations naming both parents (S24): Cornelius 13 Sept 1847, Ludovica 5 Oct 1853. `sup` — index rows, no image read. | — |
| 30 | 2026-07-26 | bossin | — | CORROBORATED | Her declaration of **11 January 1849** sits one day after the **10 January** birth read from her 1872 act. A documented child in the middle of the series is what makes the two new siblings safe rather than merely plausible. | — |
| 30 | 2026-07-26 | swaelens | — | NEW | Ludovica married Joannes Baptista Julianus Swaelens at Alsemberg, 17 Feb 1884. Nothing else held — the index gives him no dates and no parents, so this record has none. | — |
| 30 | 2026-07-26 | peremans | — | NOTED | **Four spellings of her forename across four acts** — Joanna Catharina Jacoba (her own), Anna Catharina (1872, and the birth declarations), Joanna Maria (1884). Her own act is the documented one; the rest are clerks writing a parent's name from memory. | — |
| 31 | 2026-07-26 | mtstephanie_t, georgesjoseph_t, jbzenon_t, charleseugene_t | — | NEW | Four siblings for georges_cj, all Grez-Doiceau, both parents named on every row (S25). Charles Eugène died an infant in 1851 — and is independently in AGATHA too. | — |
| 31 | 2026-07-26 | georges_cj | — | ANCHOR | His own declaration, 16 Sept 1836, sits one day after the 15 Sept birth read from his 1872 act. A documented child inside the series is what licenses the other four. | — |
| 31 | 2026-07-26 | georgesjoseph_t, deridder_sophie | — | LOOP CLOSED | Their marriage — Grez-Doiceau, 7 Oct 1868, banns 20 & 27 Sept — **is the wedding S23's death extract of 28 Sept 1868 was drawn for.** The annex is explained from the other side. | — |
| 31 | 2026-07-26 | — (hazard) | — | — | **Two brothers named Georges**: Georges Charles Joseph (b. 1836, m. Kraainem 1872) and Georges Joseph (b. 1843, m. Grez-Doiceau 1868). Recorded in both records so no later pass merges them. | — |
| 31 | 2026-07-26 | Théophile Thumas | — | REJECTED | Grez-Doiceau death 6 July 1837, father Georges — but mother given as **Marie Thérèse**, not Marie Catherine. Commune, decade and father's forename agree; the mother does not. Two of three is not enough. | — |
| 32 | 2026-07-26 | henrica_thumas | LEAD | **DOCUMENTED** | The 1899 Kraainem act her record had been waiting on was opened (S27): born **Kraainem 24 June 1878**, married **Franciscus Coenraets**. Placeholder spouse "(husband not yet read)" replaced by a person. | — |
| 32 | 2026-07-26 | jcseraphina_t, misabella_t | — | NEW | Two more daughters of georges_cj × bossin, from acts naming both parents: b. Kraainem 21 Mar 1873 (m. 1892) and Sint-Stevens-Woluwe 18 Aug 1880 (m. 1900). | — |
| 32 | 2026-07-26 | bossin | — | **CORRECTED** | Death was the bare year "1894". Two of her daughters' acts state it independently: **Kraainem, 7 November 1894**. She was forty-five. | — |
| 32 | 2026-07-26 | jbcoppens, coenraets_f, ludovicus_bossin79 + 6 parents | — | NEW | The three husbands and all six of their parents, every one named by an act. Eleven people from three acts. | — |
| 32 | 2026-07-26 | ludovicus_bossin79, catharina_bossin, jbbossin | — | NOT GRAFTED | Three Bossins of Sint-Stevens-Woluwe marry into a family whose mother is a Bossin of Sint-Stevens-Woluwe. Very likely kin, **no link drawn** — a shared surname in one village is not evidence. | — |
| 32 | 2026-07-26 | georges_cj | — | LEAD | A **fifth child, probably a son**: *Georgius Thumas, 24, of Kraainem*, witnesses at his sisters' 1900 wedding and again in 1902. Not grafted — a witness entry names no parents, and this family already has two brothers called Georges one generation up. | — |
