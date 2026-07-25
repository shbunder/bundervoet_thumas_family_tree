# Sources

<!-- GENERATED from research/sources.json by tools/research.py docs — do not edit. -->

Two levels: **sites** are the base venues, **pages** are the specific trees,
collections and documents inside them that were actually opened. The search log that
references both is `research/searches.jsonl` — see [searching.md](searching.md).

Confidence: **doc** = seen in a primary act or an authoritative index · **sup** = a
single member tree, not checked against the act · **fam** = family testimony.

*Capabilities* say what a venue can be asked, not how good it is — a `name-index`
miss is only a miss for what somebody indexed, and a venue that later gains
`full-text` re-opens every one of them. `uv run tools/research.py stale` lists those.

## Sites

| Site | Kind | Access | Capabilities | Searches run | Covers |
|---|---|---|---|---|---|
| `agatha` <https://agatha.arch.be/> | archive | login | name-index, image-read | 13 | Belgian civil and parish registers by commune and year, with scans. The primary route to 19th-century Belgian acts. |
| `search-arch` <https://search.arch.be/> | archive | offline | name-index, image-read | 1 | Scanned civil registers by commune and year; sibling portal to AGATHA. |
| `familysearch` <https://www.familysearch.org/> | index | login | name-index, image-read, full-text | 4 | Belgian civil and church registration, with act images. |
| `geneanet` <https://www.geneanet.org/> | index | mixed | name-index, tree, image-read | 15 | Member-submitted trees plus an indexed record collection. The member trees are the main lever on a 19th-century frontier. |
| `ancestry` <https://www.ancestry.com/> | index | paywall | name-index, image-read | 2 | West-Vlaanderen and Brabant civil-registration indexes, searchable province-wide. |
| `myheritage` <https://www.myheritage.com/> | index | paywall | name-index, tree | 5 | Indexed Belgian and French civil registration, plus member family trees with automatic Smart Matches against your own uploaded tree. |
| `vrijwilligersrab` <https://www.vrijwilligersrab.be/> | index | open | name-index | 0 | Volunteer transcriptions of West-Flemish marriage and death records. |
| `vvf` | index | mixed | name-index | 0 | Flemish marriage indexes; the layer beneath several Geneanet trees. |
| `stadsarchief-oostende` | archive | offline | image-read | 0 | Oostende civil registers after 1900 — not in AGATHA, not digitised. |
| `inmemoriam` <https://www.inmemoriam.be/> | obituary | open | name-index | 1 | Digitised Belgian obituary notices. |
| `ingedachten` <https://www.ingedachten.be/> | obituary | open | name-index | 1 | Funeral-home obituary notices. |
| `uitvaart-oostende` <https://www.uitvaart-oostende.be/> | obituary | open | name-index | 1 | Oostende funeral notices. |
| `jammart` <https://www.jammart.be/> | obituary | open | name-index | 1 | ~100,000 scanned memorial cards (bidprentjes). |
| `grafzerkje` <https://www.grafzerkje.be/> | cemetery | open | name-index | 1 | Belgian gravestone and cemetery records. |
| `family` | family | offline | testimony | 1 | Testimony, memorial cards, photographs and papers held by relatives. |
| `web` | web | open | full-text | 0 | Parenteel documents and family sites published outside the big platforms. |
| `openarch` <https://www.openarchieven.nl/> | index | open | api, name-index | 17 | About 30 million Belgian person-mentions: the Familiekunde Vlaanderen and Doodsprentjes.be bidprentjes and rouwbrieven, the heemkring collections, and the Rijksarchief civil acts transcribed by the Demogen volunteers. Coverage is uneven by province — Vlaams-Brabant has indexed civil acts with full parent roles; Oostende and Evergem are overwhelmingly 20th-century memorial cards. |
| `fv-dataindexen` <https://dataindexen.familiekunde-vlaanderen.be/> | index | open | name-index | 5 | Familiekunde Vlaanderen's regional documentation centres, in four collections: the TOTAALINDEX OP DE OUDE PAROCHIEREGISTERS (baptism, marriage and burial indexes per parish, arrondissement by arrondissement), the COD Centrum Oostende Databank, FV-Kempen, and Regio Mandelleie, plus klappers on genealogical books. |
| `fs-fulltext` <https://www.familysearch.org/search/full-text> | index | login | full-text, image-read | 4 | Machine transcription of image collections that were never name-indexed: Flemish feudal and nobility records, Gent notarial deeds, militia and military registers, land records. Reaches back to the 1460s — far beyond civil registration, and beyond most parish indexing. Critically for this tree: 'Belgium. Court Records 1639-1700, 1761-1795' — the STATEN VAN GOED, estate inventories drawn up on a death, which name the deceased, the surviving spouse and every child with ages and marriages. That is the richest single document type for pre-1796 Flemish family reconstruction and it is machine-transcribed here. The catalogue is organised as province x record type with a date span each — 'Antwerpen, Rechtsgang, 0190-1995', 'Brabant, Eigendommen, 1273-1964', and the same shape for Migraties, Religieus, Woonplaatsen, Militaire dienst and Biografieen. Property, judicial and residence records reaching back to the Middle Ages, none of it name-indexed. |

**`agatha`** — Post-1900 Oostende civil registers are NOT here — they sit at the Stadsarchief Oostende. Go straight to commune + year + act number; 19th-c. acts are handwritten but formulaic, and the parents are named in the opening lines ('zoon/dochter van … en …').

**`search-arch`** — RETIRED. search.arch.be now redirects to an end-of-life notice and is replaced by agatha.arch.be. Act links in the harvested Open Archives corpus still point here, so they must be translated: a search.arch id like HUBRA_00221638_0 is HUVLB_HUBRA_00221638_0 on AGATHA, or the act can be found by searching name + commune + year.

**`familysearch`** — Deeper than AGATHA or Ancestry for Belgium — it broke the Dekeyser wall the other two could not. Try it before concluding an act is unindexed.

**`myheritage`** — Reached with an account (July 2026). The free/paid boundary matters for planning: SMART MATCHES against other members' trees are FREE to read — names, relationships and counts all visible — and that is where the value has been. RECORD MATCHES are not: the field values are replaced server-side with decoy strings behind a Data subscription, so only the collection name, the field list and the occasional year are free. Treat record matches as a TARGETING LIST — they say which document exists for whom, and Belgian civil acts can then be pulled free from AGATHA or FamilySearch.

**`stadsarchief-oostende`** — Holds both documents that would name Édouard Dekeyser's parents from Oostende's own registers: the 4 May 1901 marriage act and the 8 Sep 1951 death act. Death acts open after 50 years, so the 1951 one is public — the cleanest ask.

**`inmemoriam`** — Coverage gap: coastal and Brabant papers are thin, so a post-2000 coastal death may simply be absent.

**`jammart`** — Memorial cards name parents and children and sit outside the civil-registration publicity rules — the key to 20th-century walls. Match on place, never on surname alone.

**`family`** — The only key to the sealed 20th-century links. A direct descendant may also request a relative's birth, marriage or death certificate at any age — that is the decisive move on the Janssens wall, not more online searching.

**`openarch`** — The only venue in this registry with a free, unauthenticated API, so it is harvested rather than searched: tools/harvest.py pulls acts once and keeps them, and every frontier is then answered against the local corpus. Records carry structured roles — Vader, Moeder, Kind, Bruidegom, Bruid, Vader van de bruid — so a parent link is a field rather than prose, and each act links to its scan and to its search.arch.be page. Throttled to 4 requests a second; the harvester goes slower.

**`fv-dataindexen`** — FOUND by discovery (July 2026) after the whole ladder missed on Bernardus Bundervoet. It reaches the layer nothing else here does — PRE-1796 PARISH REGISTERS, where 158 of this tree's people sit and where civil registration does not exist. Every commune checked against the tree is covered. Verified ranges: Oostkamp 1631-1792 (doop/huwelijk/overlijden) — the Sabbe, Wittenheyns, Van Renterghem and De Baecke tier; Woumen 1595-1796 — the Vanstechelman line; Evergem doop 1746-1796, huwelijk 1751-1794, OVERLIJDEN 1682-1796 — which covers Joannes Bundervoet's 1760 death and Christoffel's 1786; Belsele 1585-1796 — the Paelinck line; Zwevegem 1597-1803, Varsenare 1609-1791, Oedelem 1616-1791, Ruddervoorde 1623-1796. Its COD collection covers Oostende, where the largest unverified block of this tree lives. Searched through the interactive site, not by URL. INTERFACE: a legacy PHP site. The arrondissement links call gotoDB2(db, table) which sets two hidden fields on form `selectDB` and submits it; driving that from an injected script returns the same page, so it needs real clicks on the arrondissement link and then on the parish. Coverage above was read from the static 'Lijst van bewerkte parochies' page, which is plain HTML and needs no session. NOTHING HAS BEEN RETRIEVED FROM IT YET — the coverage is established, the searching is not.

**`fs-fulltext`** — THE ROUTE TO THE PRE-1796 HALF OF THIS TREE. 158 of its people were born before civil registration and are unreachable by AGATHA, Open Archives or any name index, because the documents that name them were never indexed. This searches the manuscript itself. A first query for 'Bundervoet' returned 159 hits including a Bundervoet family holding fiefs at Saint-Pierre-Alost 1687-1701, with descent stated (Francois > Lievin; Lievin and Pasquier each holding in turn) and a Catherine Bundervoet acting as guardian for her son in 1687. NOTE: the snippets that surfaced those entries ran two adjacent surnames together and gave three wrong dates and one wrong place; the page itself had to be opened to get them right. Read the document, not the snippet. Search by surname alone and read the snippets; the place filter behaves like FamilySearch's others and should not be trusted to constrain. COVERAGE IS UNEVEN BY COLLECTION, NOT BY PROVINCE. A surname query alone looked thin for West-Vlaanderen — Wittenheyns returned a single 1657 Bruges notarial mention — while 'Sabbe Oostkamp' returned thousands, all in the court records. So the province is well covered and the rare surname simply is rare; do not read a thin surname result as thin coverage. Search surname + commune, and expect the yield to be staten van goed rather than registers. LIMITATION, FOUND THE HARD WAY: it is a discovery tool, not a lookup. Multi-word queries are ORed rather than phrased — 'sterfhuyse Sabbe Oostcamp' returned 101,134 hits — and the collection and year filters are a dynamic widget that resists scripting. So it will tell you a family is present in a body of records, and it will not hand you one named person's document. Reaching a specific act through it means filtering by hand in the browser, or paging. Budget for that; do not expect a targeted hit.

## Pages

### Rijksarchief AGATHA — Belgian State Archives search robot

#### `S2` — Jérôme Dekeyser's 1897 Oostende birth act (akte nr. 585)
- **Kind:** record · <https://agatha.arch.be/nl/data/acts/GEWVL_GEBWVL_01442676>
- **Yielded:** The marginal note "Gewettigd 4 5 1901" — so Édouard × Louise married 4 May 1901, legitimizing Jérôme (b. 14 Jun 1897) and Gustavus (b. 1899). Establishes the marriage date without the marriage act.
- **Saved artifact:** `data/artifacts/jerome-dekeyser-1897-birth-agatha.md`
- **Confidence:** doc
- **Accessed:** 2026-07

#### `hamme-merchtem-1901-marriages` — Hamme (Merchtem) marriage index (TABEL), 1901
- **Kind:** record
- **Collection:** Gemengde akten Hamme (Merchtem) 1901-1910, p. 8
- **Yielded:** A negative that settled a question: exactly one marriage in the whole of 1901, Belgrado Adeline × Leo Jean Louis (act 1). No Dekeyser — which disproves 'Hamme (Merchtem)' as the marriage place.
- **Confidence:** doc
- **Accessed:** 2026-07

#### `S5` — Kraainem marriage act nr. 2, 3 February 1902 — Thumas × Vandenbemden
- **Kind:** record · <https://agatha.arch.be/nl/data/acts/HUVLB_HUBRA_00221638_0>
- **Collection:** Burgerlijke stand — Huwelijksakten — Provincie Vlaams-Brabant en Brussels Hoofdstedelijk Gewest, Kraainem 1902, akte nr. 2
- **Yielded:** FOUR parent links in one document: Joannes Baptista Georgius Thumas as son of Georgius Carolus Josephus Thumas × Antonia Bossin, and Joanna Vandenbemden as daughter of Henricus Augustinus Vandenbemden × Maria Theresia Coekelberghs. Plus occupations for five people, a correction to Henricus Augustinus's death place (Kraainem, not Sint-Stevens-Woluwe), the spelling Antonia rather than Antoina, and four witnesses.
- **Saved artifact:** `data/artifacts/thumas-vandenbemden-1902-marriage-kraainem.md`
- **Confidence:** doc
- **Accessed:** 2026-07-25
- **Note:** An AGATHA act analysis — the Rijksarchief's own transcription of the register, with the act number — not the scan. Reached by matching the harvested Open Archives corpus, whose own link pointed at the retired search.arch.be.

#### `S11` — Kraainem marriage act nr. 2, 20 June 1872 — Thumas × Bossin (read on AGATHA)
- **Kind:** record · <https://agatha.arch.be/nl/data/acts/HUVLB_HUBRA_00185915_0>
- **Collection:** Burgerlijke stand — Huwelijksakten — Provincie Vlaams-Brabant en Brussels Hoofdstedelijk Gewest, Kraainem 1872, akte nr. 2
- **Yielded:** The same act as S8, read at the archive rather than through an index: Antonia Bossin's exact birth (10 Jan 1849, Sint-Stevens-Woluwe) where the tree had only a year, three occupations (fabriekwerkster, landbouwer, huishoudster), the bridegroom's trade in 1872 as fabrieksgast, and four witnesses with ages and trades.
- **Saved artifact:** `data/artifacts/thumas-bossin-1872-marriage-kraainem.md`
- **Confidence:** doc
- **Accessed:** 2026-07-25

#### `S14` — Death act nr. 58 — George Thumas, Grez-Doiceau, 20 November 1808 (read on AGATHA)
- **Kind:** record · <https://agatha.arch.be/nl/data/acts/Visu-542_9999_999_616490_000_A_5246-00000035>
- **Collection:** Burgerlijke stand (DemoGen Visu) — België, Grez-Doiceau, overlijdensakten 1808, akte nr. 58
- **Yielded:** Four records documented from one act: George Thumas's death on 20 Nov 1808 at Grez-Doiceau and his trade as menuisier, both as held; his father Lambert Thumas, his mother Marie Leclercq and his wife Marie Catherine Noé all named. It also gives his age as 60, implying a birth around 1747-48 against the 1744 this tree records — a conflict left open rather than resolved on hearsay.
- **Saved artifact:** `data/artifacts/george-thumas-1808-death-grez-doiceau.md`
- **Confidence:** doc
- **Accessed:** 2026-07-26

#### `S15` — Death act nr. 35 — Marie Catherine Joostens, Grez-Doiceau, 10 June 1857 (read on AGATHA)
- **Kind:** record · <https://agatha.arch.be/nl/data/acts/Visu-542_9999_999_1076594_000_A_5561-00000008>
- **Collection:** Burgerlijke stand (DemoGen Visu) — België, Grez-Doiceau, overlijdensakten 1857, akte nr. 35
- **Yielded:** Her exact death date, 10 June 1857, where the tree had only the year; her birthplace Woluwe-Saint-Lambert and occupation ménagère; and her parents Guillaume Joostens and Jeanne Marie Deconninck read at the archive rather than from an index. It also gives her husband Georges Thumas as 63, implying a birth around 1793-94 against the 1804 the tree records — a ten-year conflict in an act whose arithmetic is right for her own age.
- **Saved artifact:** `data/artifacts/joostens-1857-death-grez-doiceau.md`
- **Confidence:** doc
- **Accessed:** 2026-07-26

### FamilySearch

#### `S1` — Édouard Dekeyser's 1946 Oostende remarriage act (akte nr. 81)
- **Kind:** record · <https://www.familysearch.org/ark:/61903/1:1:X9R6-DJNV>
- **Collection:** Belgium, West Flanders, Civil Registration, 1582-1950 — Arr. Brugge, Oostende, Huwelijkscertificaten 1946
- **Yielded:** THE WALL-BREAKER. Édouard's parents = Desiderius De Keyser × Maria Theresia Van den Broeck; birthplace Hamme (Oost-Vlaanderen), b. 12 Nov 1876; his first marriage to Louisa Maria Bocklandt ended in divorce (~1923, Rechtbank van eersten aanleg Brugge); he remarried Leontine Schreel in Oostende, 9 May 1946.
- **Saved artifact:** `data/artifacts/edouard-dekeyser-1946-marriage.md`
- **Image:** <https://www.familysearch.org/ark:/61903/3:1:3QHN-LQKQ-R48T-B>
- **Confidence:** doc
- **Accessed:** 2026-07-22

#### `S4` — Desiderius De Keyser × Maria Theresia Van den Broeck, Oost-Vlaanderen
- **Kind:** record · <https://www.familysearch.org/ark:/61903/1:1:6TRG-9K8Z>
- **Collection:** Belgium, East Flanders, Church and Civil Registration, 1541-1920
- **Yielded:** The couple were a Hamme (O-Vl) family; further children incl. Augustinus (†1883 infant), Frederiens Carolus, Leontinus Josephus.
- **Confidence:** doc
- **Accessed:** 2026-07-22
- **Note:** FRONTIER, unconfirmed: a Desiderius de Keyser b. 27 May 1832 with parents Arnoldus de Keyser × Angelina Sophia van Kerkhove exists, but nothing ties him to Van den Broeck. Do not graft until an act does.

#### `fs-brabant-bs` — België, Brabant, burgerlijke stand, 1582-1950
- **Kind:** collection · <https://www.familysearch.org/search/collection/results?f.recordCountry=Belgium>
- **Covers:** Brabant civil registration, indexed by person with parents and spouses attached. Far deeper than AGATHA for this province: 1,409 Thumas records for Grez-Doiceau against AGATHA's 392.
- **Yielded:** The 1808 Grez-Doiceau death of George Thumas indexed with parents Lambert Thumas x Marie Leclercq and wife Marie Catherine Noel; Etienne Thumas's 1812 death with parents Lambert x Marie Catherine Quinart; and Catherine Josephe Thumas, b. 1745, d. 22 Feb 1823 Grez-Doiceau, daughter of Lambert Thumas x Marie Leclere - a sister of our Georges that the tree does not have.
- **Confidence:** sup
- **Accessed:** 2026-07-26
- **Note:** CAUTION: its indexed 'birth 1748' for George Thumas is DERIVED from the age of 60 stated in the 1808 death act, not an independent birth record. Two sources agreeing are not two sources when one is computed from the other.

#### `fs-brabant-church` — Belgium, Brabant, Civil Registration and Church Records, 1704-1916
- **Kind:** collection · <https://www.familysearch.org/search/collection/results?f.recordCountry=Belgium>
- **Covers:** Brabant parish and civil records, including entries indexed under a parent or spouse rather than the principal - which is how siblings surface.
- **Yielded:** Catherine Josephe Thumas (1745-1823), daughter of Lambert Thumas x Marie Leclere; and several Georges/Lambert Thumas x Quinart parent entries pointing at children not yet in the tree.
- **Confidence:** sup
- **Accessed:** 2026-07-26

#### `S16` — Birth registration nr. 997 — Philomena Leonia Paelinck, Sint-Niklaas, 31 October 1901
- **Kind:** record · <https://www.familysearch.org/ark:/61903/1:1:Q2QP-N3Z7>
- **Collection:** Belgium, East Flanders, Civil Registration, 1541-1950 — Sint-Niklaas 1901, invoernummer 997
- **Yielded:** The act AGATHA does not hold. Philomena Leonia Paelinck born 31 October 1901 at Sint-Niklaas, act 997, with both parents named: Eduardus Franciscus Paelinck and Maria Magdalena Van Bogaert. Confirms the birth date the tree had only as a year, and puts both parent links on a civil record.
- **Saved artifact:** `data/artifacts/leonie-paelinck-1901-birth-sint-niklaas.md`
- **Confidence:** sup
- **Accessed:** 2026-07-26
- **Note:** FamilySearch's index entry, not the register image; the image is reachable from the record page and reading it would make the three people doc.

### Geneanet

#### `tree-stefpaelinck` — stefpaelinck (Stef Paelinck)
- **Kind:** tree · <https://gw.geneanet.org/stefpaelinck>
- **Covers:** De Keyser and Paelinck lines, Oostende and Sint-Niklaas.
- **Yielded:** The Paelinck line back to Livinus (~1618) and the Oostende De Keyser generations. Édouard Dekeyser is top-of-branch here — no parents.

#### `tree-natamarcelle` — natamarcelle (Natacha Quinet)
- **Kind:** tree · <https://gw.geneanet.org/natamarcelle>
- **Covers:** Édouard Dekeyser (Sosa 56).
- **Yielded:** *nothing yet*
- **Note:** Édouard is top-of-branch — no parents recorded.

#### `tree-wete1998` — wete1998 (Erik Bekaert) — Hamme (O-Vl) specialist
- **Kind:** tree · <https://gw.geneanet.org/wete1998?n=bocklandt>
- **Covers:** Hamme (Oost-Vlaanderen) families; Bocklandt and Van Bergen.
- **Yielded:** Louise Bocklandt (b. 31 Dec 1877 Hamme O-Vl) → Eduardus Bocklandt (1839) × Maria Louisa Van Bergen (1842-1888) → Antonius Dominicus Bocklandt (1805-1883) × Isabella Livia Ichau (1803-1870) → Daniel Bocklandt (1768-1837) × Philippa Van Puyenbroeck (1778-1820); plus Joannes Franciscus Van Bergen (1815-1898) × Ida Vermandel (1825-1865). Six ancestors added.
- **Confidence:** sup
- **Accessed:** 2026-07-22
- **Note:** sup for the ancestors; Louise's own parents are doc, independently on her AGATHA record. Frontier: Daniel Bocklandt's parents, pre-1768 Hamme O-Vl.

#### `tree-isavdw` — isavdw — Rijksarchief-sourced, with scan links
- **Kind:** tree · <https://gw.geneanet.org/isavdw>
- **Covers:** Cappaert, Stroobandt, Keirsebilck, De Grande, Sabbe — West-Flemish.
- **Yielded:** The Stroobandt line to the ~1590s (Oliverius Stroobandt × Judoca Van Hecke), Keirsebilck +2 generations, De Grande +2, Caeckaert +1.
- **Accessed:** 2026-07
- **Note:** The most productive page found so far, and the layer beneath kathrynann. A tree that cites the zoekrobot AND transcribes the parents is the winning shape — look for an 'Ouders' section.

#### `tree-kathrynann` — kathrynann
- **Kind:** tree · <https://gw.geneanet.org/kathrynann>
- **Covers:** Stroobandt and De Vriese, Oostkamp/Tielt/Wingene; sourced to isavdw and VVF.
- **Yielded:** Juliana Stroobandt's parents and grandparents; the deep De Vriese chain to Michaël De Vriese (~1615) × Judoca Scherrens.

#### `tree-stefanieschil` — stefanieschil
- **Kind:** tree · <https://gw.geneanet.org/stefanieschil>
- **Covers:** Bostin and Perquy.
- **Yielded:** Henricus Josephus Bostyn's parents via his 1867 Sint-Andries marriage act — Henricus Josephus Bostin (1801-1867) × Anna Theresia Perquy (1806); and Joannes Perquy × Agatha Stekelorum above them.
- **Note:** Joannes Perquy has no parents here — that wall held.

#### `tree-vxnce13` — vxnce13 (Vynce Lémans)
- **Kind:** tree · <https://gw.geneanet.org/vxnce13>
- **Covers:** Bostyn–Cappaert–Desmet; his own documented ancestry.
- **Yielded:** Henricus Bostyn's parents (Henricus Josephus Bostyn 1841 × Mathilde Desmet 1841, m. 1867 Sint-Andries).

#### `tree-1960dirk` — 1960dirk (Dirk Teerlinck)
- **Kind:** tree · <https://gw.geneanet.org/1960dirk>
- **Covers:** Bostyn and Cappaert, with act numbers.
- **Yielded:** Juliana Stroobandt's dates (12 Sep 1839 Oedelem – 11 Feb 1921 Oostkamp).

#### `tree-cisken` — cisken — the Zaventem Van Craenenbroeck trunk
- **Kind:** tree · <https://gw.geneanet.org/cisken?n=van+craenenbroeck>
- **Covers:** Van Craenenbroeck, Zaventem and Sterrebeek.
- **Yielded:** The trunk to the 1830s: Amandus Franciscus Van Craenenbroeck (1835-1914) × Paulina Mommaerts (1838-1909) → Antonius Josephus (1872-1936) × Anna Maria Meeus (1877-1957) → children b. 1902-1918.
- **Confidence:** sup
- **Accessed:** 2026-07-22
- **Note:** Stops just above Anna's generation, so her specific parent is NOT established and is deliberately not grafted. Its owner is a relative who very likely holds that generation privately — one message could close the link.

#### `tree-wernero` — wernero (Werner Osaer)
- **Kind:** tree · <https://gw.geneanet.org/wernero>
- **Covers:** Devriendt, Smessaert and Ramon, West-Flemish coast.
- **Yielded:** The Ramon line to Mattheus (Bovekerke 1729), including the two generations lost at sea.

#### `tree-stechec` — stechec (Christian Vanstechelman)
- **Kind:** tree · <https://gw.geneanet.org/stechec>
- **Covers:** Vanstechelman, Woumen → Zevekote → Mariakerke.
- **Yielded:** The Vanstechelman line to Joannes Vanstechele (b. before 1673, Woumen).

#### `tree-bartvanhooren` — bartvanhooren (Bart Vanhooren)
- **Kind:** tree · <https://gw.geneanet.org/bartvanhooren>
- **Covers:** Van Iseghem and Vincke, Oostende.
- **Yielded:** Rosette Van Iseghem's ancestry, and the Vincke / Vanalderweireldt line at Diksmuide.

#### `tree-gverdievel` — gverdievel (Guy Verdievel)
- **Kind:** tree · <https://gw.geneanet.org/gverdievel>
- **Covers:** Van Iseghem, Oostende — deep and Rijksarchief-sourced.
- **Yielded:** The Van Iseghem line to Judocus Franciscus (b. 1787) × Victoria Eugenia Engelsen.

#### `tree-marcelcroon` — marcelcroon (Marcel Croon)
- **Kind:** tree · <https://gw.geneanet.org/marcelcroon>
- **Covers:** Thumas, Kraainem and Grez-Doiceau.
- **Yielded:** Jean Thumas's dates (b. 23 Oct 1907, d. 22 Mar 1995, both Kraainem).

#### `tree-jswaelens` — jswaelens
- **Kind:** tree · <https://gw.geneanet.org/jswaelens>
- **Covers:** Thumas, Grez-Doiceau.
- **Yielded:** The Thumas chain back to Antoine (b. 11 Nov 1656 Biez).

#### `tree-m2155` — m2155
- **Kind:** tree · <https://gw.geneanet.org/m2155>
- **Covers:** Thumas.
- **Yielded:** Occupations and life detail across the Thumas generations — the four carpenter generations, Antoine as bailiff of Piétrebais.

#### `tree-michelv990` — michelv990 (Michel Vandam)
- **Kind:** tree · <https://gw.geneanet.org/michelv990>
- **Covers:** Thumas, Kraainem.
- **Yielded:** *nothing yet*

#### `tree-jerome5530` — jerome5530 (Jerome Debie)
- **Kind:** tree · <https://gw.geneanet.org/jerome5530>
- **Covers:** Thumas, Kraainem.
- **Yielded:** *nothing yet*

#### `tree-paulderidder` — paulderidder
- **Kind:** tree · <https://gw.geneanet.org/paulderidder>
- **Covers:** Bundervoet, Evergem.
- **Yielded:** The Evergem Bundervoet trunk; Joannes b.1682 is Sosa 644 here. Re-read July 2026: confirmed the two same-named Joannes as father (ca 1637-1707) and son (ca 1682-1760); gave Joanna Verbrugghe's father Nicolas, Joanna van Hecke's father Willem, Livina Stockman's parents Joannes Stockman x Guillielma Dellaert, and Segerius's mother as Elisabeth NN — which refuted the 'Elisabeth Hovelynck' this tree had been credited with. Holds far more than has been taken: Pieter Bundervoet (1727) and his eight children, Segerius's siblings, and act images on several profiles.

#### `tree-glorieuxp` — glorieuxp
- **Kind:** tree · <https://gw.geneanet.org/glorieuxp>
- **Covers:** Bundervoet, Evergem.
- **Yielded:** Joannes Bundervoet's two marriages — Livina Stockman, then Livina De Wilde ~1745. That remarriage is what identifies him.

#### `tree-dvandurme1` — dvandurme1
- **Kind:** tree · <https://gw.geneanet.org/dvandurme1>
- **Covers:** Bundervoet, Evergem.
- **Yielded:** *nothing yet*

#### `tree-mjovdl` — mjovdl
- **Kind:** tree · <https://gw.geneanet.org/mjovdl>
- **Covers:** Bundervoet, Evergem.
- **Yielded:** *nothing yet*

#### `zaventem-kerkhoflaan` — Zaventem "Kerkhoflaan" cemetery index
- **Kind:** collection
- **Covers:** Zaventem burials.
- **Yielded:** Independent confirmation of several Van Craenenbroeck dates (Arthur 1908-1982, Paul 1934-2010, Elisa 1887-1967, Desiré 1859-1944); the family runs back to a 1721 Zaventem marriage.

### MyHeritage

#### `mh-tree-lucien` — Bundervoet Web Site, managed by Lucien Bundervoet (Belgium)
- **Kind:** tree
- **Covers:** A Bundervoet family tree overlapping ours at Petrus Franciscus (1879) and above.
- **Yielded:** Four Smart Matches on Petrus Franciscus alone. Names Petrus Franciscus's SIBLINGS (Maria Bundervoet + 3 more) and all SIX of his children, where our tree had only Alphonsus. Detail fields are paywalled; the names and counts are not.
- **Note:** A living Bundervoet with his own tree — the most direct lead yet for objective 3 (connecting the Bundervoet forest). Contactable through MyHeritage. Ask before grafting: his tree is unverified, so this is sup at best.

#### `mh-tree-johny` — bundervoet Web Site, managed by Johny Henricus Bundervoet (Belgium)
- **Kind:** tree
- **Covers:** A second Bundervoet tree, overlapping at Petrus Bundervoet.
- **Yielded:** Independently names Alphons Bernardus Cyprianus and five more children of Petrus Franciscus — a second tree agreeing with Lucien's on the sibling group.
- **Note:** Second living Bundervoet with a tree. Two independent trees agreeing raises the six-children claim above a single-tree assertion, though neither is a record.

#### `mh-belgium-death-1800-1950` — Belgium, Civil Death Registers, 1800-1950 (MyHeritage collection 21034)
- **Kind:** collection
- **Covers:** Belgian civil death acts.
- **Yielded:** A death record for Bernardus Bundervoet (b. circa 1837, d. 1900) that carries his FATHER and MOTHER. Values are paywalled behind a MyHeritage Data subscription — only the year 1900 and the field list are visible free.
- **Note:** Record 21034-1003940. Being a Belgian civil act, the same document should be reachable free through AGATHA or FamilySearch — pull it there rather than paying. It would independently confirm or refute Judocus x Roegiers as Bernardus's parents.

#### `mh-belgium-birth-notices` — Belgium Birth Notices (MyHeritage)
- **Kind:** collection
- **Covers:** Belgian birth announcements.
- **Yielded:** *nothing yet*
- **Note:** Two pending record matches (Alphons 1905 birth place, and one other). Paywalled.

#### `mh-france-vital-records` — France, Vital Records Index (MyHeritage)
- **Kind:** collection
- **Covers:** French civil registration.
- **Yielded:** *nothing yet*
- **Note:** Two pending record matches. Worth attention: the Van Iseghem family migrated to Lens (Pas-de-Calais) for the coal mines, and Joannes Van Iseghem was born there in 1903 — a French index is exactly where that branch should appear. Paywalled on MyHeritage.

### The family itself

#### `cosette-testimony` — Family testimony — Cosette De Keyser
- **Kind:** record
- **Yielded:** Jerome Dekeyser ❦ Léonie Paelinck are Roland's grandparents, which ruled out the earlier Gustaaf Audomarus reading and corrected the whole branch.
- **Confidence:** fam

#### `marcel-memorial-card` — Marcel Bundervoet's memorial card (Uitvaartcentrum Raes, Oostende)
- **Kind:** record
- **Yielded:** Marcel Henri Bundervoet's full name, and the Bostyn family naming that pointed to his mother Elodia Bostyn.
- **Confidence:** doc

### Standalone published genealogies

#### `fauconier-parenteel` — Fauconier / Bauwens "Bundervoet–Vermeulen" parenteel
- **Kind:** tree
- **Covers:** Bundervoet descendants, Evergem and Oostende.
- **Yielded:** The Bundervoet surname line at Evergem.

### Open Archives (openarch.nl) — open-data aggregator, Netherlands/Belgium/France

#### `S6` — Death act of George Thumas, Grez-Doiceau, 20 November 1808
- **Kind:** record · <https://www.openarchieven.nl/abb:e2375960-201a-e775-f648-11aabe4581c3>
- **Collection:** Burgerlijke stand Grez-Doiceau, overlijdens 1808 (Rijksarchief, via Open Archives)
- **Yielded:** Three links on the deep Thumas line at once: the act names George Thumas's father as Lambert Thumas, his mother as Marie Leclercq, and his wife as Marie Catherine Noël, with the death date 20 November 1808 matching the record exactly.
- **Image:** <https://familysearch.org/ark:/61903/1:2:Q21G-G5Q8>
- **Confidence:** sup
- **Accessed:** 2026-07-25
- **Note:** An Open Archives transcription of the civil act; the FamilySearch image behind it has not been read here. The corpus holds this act twice, under abb:e2375960… and abb:efe61c66…, one spelling the wife Noël and the other Noé — two index entries, one act.

#### `dbe-petrus-f-1943` — Doodsprentjes.be memorial card — Pieter Franciscus Bundervoet, d. Oostende 21 July 1943
- **Kind:** record · <https://www.openarchieven.nl/dbe:9e1d9dc7-4107-4c96-febc-2d81854a0cb2>
- **Collection:** Doodsprentjes.be bidprentjesverzameling, record 18_360290
- **Yielded:** Independent corroboration of Petrus Franciscus Bundervoet: born 19 March 1879 at Evergem, died 21 July 1943 at Oostende, partner Vanstechelman. Every date and place matches the record we held on Geneanet's word alone.
- **Image:** <https://www.doodsprentjes.be/index.php?lang=Nld&p=search&nummer=18_360290>
- **Confidence:** sup
- **Accessed:** 2026-07-25
- **Note:** A transcription of a memorial card, not a civil act and not an image anyone here has read. The card itself sits behind a session on doodsprentjes.be — the URL above returns the site's search page, not the scan — so this stays sup.

#### `fwk-petrus-f-1943` — Familiekunde Vlaanderen Westkust memorial card — Pieter-Franciscus Bundervoet, d. Oostende 21 July 1943
- **Kind:** record · <https://www.openarchieven.nl/fwk:2c8c8992-d4de-acac-3664-e3ff622219e6>
- **Collection:** Familiekunde Vlaanderen regio Westkust, bidprentjes/rouwbrieven, record 37875
- **Yielded:** The same death independently: b. 19 March 1879 Evergem, d. 21 July 1943 Oostende, partner named in full as Augusta Vanstechelman. A second archive, a separate collection, the same facts.
- **Confidence:** sup
- **Accessed:** 2026-07-25

#### `fwk-marcel-b-2015` — Familiekunde Vlaanderen Westkust memorial card — Marcel Bundervoet, d. Oostende 20 November 2015
- **Kind:** record · <https://www.openarchieven.nl/fwk:7879ce10-9feb-ee58-03bb-6ede00398ed7>
- **Collection:** Familiekunde Vlaanderen regio Westkust, bidprentjes/rouwbrieven, record 486448
- **Yielded:** Marcel Bundervoet's exact dates, which the tree had only as years: born 10 May 1933 Oostende, died 20 November 2015 Oostende. It also names BOTH partners — Francine Bisschop and a Van Iseghem — confirming the two marriages the family had reported.
- **Confidence:** sup
- **Accessed:** 2026-07-25

#### `fwk-augusta-1922` — Familiekunde Vlaanderen Westkust memorial card — Augusta Vanstechelman, d. Mariakerke 4 Oct 1922
- **Kind:** record · <https://www.openarchieven.nl/fwk:931afda2-e801-150f-7511-90565d013e47>
- **Yielded:** Augusta Vanstechelman confirmed outright: born 14 March 1882 Mariakerke, died 4 October 1922 Mariakerke, spouse Petrus Bundervoet. Every field matches the record, which had rested on the stechec tree alone.
- **Confidence:** sup
- **Accessed:** 2026-07-25

#### `fwk-alphonsus-1980` — Familiekunde Vlaanderen Westkust memorial card — Alfons Bundervoet, d. Oostende 11 Mar 1980
- **Kind:** record · <https://www.openarchieven.nl/fwk:cd4bee2a-edaa-16c4-3b90-ed85b038d395>
- **Yielded:** Alphonsus Bernardus Bundervoet: born 6 January 1905 Oostende, died 11 March 1980 Oostende, spouse Elodia Bostyn — matching the record exactly.
- **Confidence:** sup
- **Accessed:** 2026-07-25

#### `spa-alphonsus-1980` — Spaenhiers heemkring memorial-card index — Alfons Bundervoet, d. Oostende 11 Mar 1980
- **Kind:** record · <https://www.openarchieven.nl/spa:d97eeeea-26a7-ae07-e4eb-7c144416fad2>
- **Yielded:** The same death from a second, unrelated heemkring collection — same birth date, same death date, same spouse. Independent corroboration rather than a second copy of one index.
- **Image:** <https://spaenhiers.be/wp-content/uploads/2026/04/bidprentjes_2026-01-31.pdf>
- **Confidence:** sup
- **Accessed:** 2026-07-25

#### `fwk-emma-vincke-1974` — Memorial card — Emma Celesta Vincke, d. Oostende 6 October 1974
- **Kind:** record · <https://www.openarchieven.nl/fwk:dcea6020-b666-acbe-f6c3-35bdbdb2bcf2>
- **Yielded:** Emma Celesta Vincke, born Diksmuide 23 January 1880, died Oostende 6 October 1974, partner Eduard Van Iseghem — every field as the tree held it, and the marriage with it.
- **Confidence:** sup
- **Accessed:** 2026-07-25

#### `dbe-adrienne-dv-1991` — Memorial card — Adrienne Devriendt, d. Oostende 22 September 1991
- **Kind:** record · <https://www.openarchieven.nl/dbe:d089d2b6-9b0e-328b-0a98-7e6275a165c3>
- **Yielded:** Adrienne Devriendt, born Stene 12 April 1908, died Oostende 22 September 1991, partner Van Iseghem — confirming the birthplace of Stene and the marriage.
- **Confidence:** sup
- **Accessed:** 2026-07-25

#### `fwk-joannes-vi-1969` — Memorial card — Joannes Vaniseghem, d. Oostende 5 May 1969
- **Kind:** record · <https://www.openarchieven.nl/fwk:7ca5a335-186e-1d08-af4c-675bcfc20fce>
- **Yielded:** Joannes Vaniseghem, born Lens 11 May 1903, died Oostende 5 May 1969, partner Adrienne Devriendt — confirming the unusual birthplace of Lens and the marriage.
- **Confidence:** sup
- **Accessed:** 2026-07-25

#### `S7` — Birth act of Philomena Leonia Paelinck, Sint-Niklaas, 31 October 1901
- **Kind:** record · <https://www.openarchieven.nl/abt:27cd23de-b6e4-bc19-3317-fdfb6a463e26>
- **Collection:** Burgerlijke stand Sint-Niklaas, geboorten 1901 (Rijksarchief, via Open Archives)
- **Yielded:** Léonie Paelinck's exact birth date — 31 October 1901 at Sint-Niklaas, where the tree had only the year — and both her parents named in the act: Eduardus Franciscus Paelinck and Maria Magdalena Van Bogaert.
- **Confidence:** sup
- **Accessed:** 2026-07-25

#### `S8` — Marriage act — Georges Carolus Josephus Thumas × Antonia Bossin, Kraainem, 20 June 1872
- **Kind:** record · <https://www.openarchieven.nl/abl:716956c6-ff92-8ade-1234-c41e2764fd17>
- **Collection:** Burgerlijke stand — Huwelijksakten — Provincie Vlaams-Brabant en Brussels Hoofdstedelijk Gewest, Kraainem 1872, akte nr. 2
- **Yielded:** FOUR parent links: the groom Georges Carolus Josephus Thumas as son of Georges Thumas × Maria Catharina Joostens, the bride Antonia Bossin as daughter of Guilielmus Bossin × Anna Catharina Peremans. This is the index copy that located the act; it was then read on AGATHA as S11.
- **Confidence:** sup
- **Accessed:** 2026-07-25
- **Note:** Its own act link pointed at the retired search.arch.be; the AGATHA equivalent is S11.

#### `S9` — Death act of Marie Catherine Joostens, Grez-Doiceau, 10 June 1857
- **Kind:** record · <https://www.openarchieven.nl/abb:9bd0f8b8-184f-adc4-6aab-0e5280747182>
- **Collection:** Burgerlijke stand Grez-Doiceau, overlijdens 1857 (Rijksarchief, via Open Archives)
- **Yielded:** Her parents, which the tree did not have at all — Guillaume Joostens and Jeanne Marie Deconninck — plus her birthplace, Woluwe-Saint-Lambert, and her husband Georges Thumas.
- **Confidence:** sup
- **Accessed:** 2026-07-25

#### `S10` — Death act of Florentinus Stroobandt, Oostkamp, 4 March 1876
- **Kind:** record · <https://www.openarchieven.nl/fvm:38eae412-a54f-0742-4f05-2c7497691178>
- **Collection:** Burgerlijke stand Oostkamp, overlijdens 1876 (via Open Archives)
- **Yielded:** His exact death date — 4 March 1876 at Oostkamp, where the tree had only the year — and his wife Rosalia Caeckaert named with him.
- **Confidence:** sup
- **Accessed:** 2026-07-25

#### `S12` — Marriage act — Franciscus Léopoldus Smessaert × Anna Francisca Morbeé, Brugge, 16 August 1851
- **Kind:** record · <https://www.openarchieven.nl/abb:415d080b-aa90-b891-ee74-d6ce648baf8c>
- **Collection:** Burgerlijke stand Brugge, huwelijken 1851 (Rijksarchief, via Open Archives)
- **Yielded:** A LEAD, not a link. A Franciscus Léopoldus Smessaert marries an Anna Francisca Morbeé, with both sets of parents named — Paulus Smessaert × Isabella Claeys, and Petrus Josephus Morbeé × Joanna De Clerck. The groom's distinctive triple name and the bride's forenames match our couple exactly, and 1851 fits a son born 1857; but the bride's SURNAME is Morbeé where our tree says Morree, which is a disagreement rather than a gap. Not grafted.
- **Confidence:** sup
- **Accessed:** 2026-07-25

#### `S13` — Death act of Etienne Thumas, Grez-Doiceau, 18 October 1812
- **Kind:** record · <https://www.openarchieven.nl/abb:10532236-1d14-b529-7fcc-881ab83666fa>
- **Collection:** Burgerlijke stand Grez-Doiceau, overlijdens 1812 (Rijksarchief, via Open Archives)
- **Yielded:** Names the dead child's parents as Lambert Thumas and Marie Catherine Quinart — corroborating that couple, and revealing a son, Etienne, who died in 1812 and is not in the tree.
- **Confidence:** sup
- **Accessed:** 2026-07-25

### Familiekunde Vlaanderen — dataindexen (indices en klappers)

#### `fv-ttind-gent` — Totaalindex op de oude parochieregisters — Arrondissement Gent (table 008_GENT)
- **Kind:** index-page · <https://dataindexen.familiekunde-vlaanderen.be/SearchDB/search.php>
- **Covers:** Surname-by-parish presence across the old parish registers of arrondissement Gent, flagged d/h/o for baptism, marriage and burial. Queryable by Familienaam, Parochie and Akten.
- **Yielded:** Bundervoet occurs in SEVENTEEN parishes of arrondissement Gent — Balegem, Desteldonk, Drongen, Evergem, Gentbrugge, Hansbeke, Lovendegem, Mariakerke, Merelbeke, Merendree, Oostakker, Semmerzake, Sleidinge, Vinderhoute, Wachtebeke, Wondelgem, Zomergem — where this tree has them in one. The first map of the Bundervoet forest, which is objective 3. Evergem carries all three registers, so its burials cover Joannes Bundervoet (1760) and Christoffel (1786).
- **Saved artifact:** `data/artifacts/bundervoet-parishes-gent-totaalindex.md`
- **Confidence:** sup
- **Accessed:** 2026-07-26
- **Note:** A FINDING AID, not a record index: it gives surname, parish and which registers, never a person or a date. Nothing here is graftable; it says which register to read.

#### `fv-cod` — COD — Centrum Oostende Databank (Provinciaal documentatiecentrum FV-Oostende)
- **Kind:** collection · <https://dataindexen.familiekunde-vlaanderen.be/SearchKlappers/listindexen2.php?file=ID239288_indcod&table=bibliotheeknamen&database=cod>
- **Covers:** About seventy-five separate indexes held by FV-Oostende, each queryable on its own. The ones that bear on this tree: Volkstelling 1798 Oostende (a household census); Kiezerslijst Oostende 1902 and 1914-1915 (voter lists, adult men with addresses); Huwelijksbijlagen Oostende_Microfilms (marriage annexes, which carry birth extracts and parents' consents); Databank Rouwbrieven and two beeldbank collections of digitised bidprentjes and rouwbrieven; Register Hospitaal Oostende 1771-1806 and 1813-1823; Ingangsbiljetten Burgerlijk Hospitaal Oostende; Verzameling kwartierstaten, stamreeksen and viergeslachten VVF-Oostende; and several fishermen lists, including Omgekomen Vissers van Heist tot De Panne and Vissers omgekomen op zee 1902-1970.
- **Yielded:** Not yet a record. Searched Omgekomen Vissers van Heist tot De Panne for Carolus Ramon, the Oostende fisherman this tree records as lost at sea in 1883 — no match. The catalogue itself is the yield: it is the first venue found that indexes Oostende at household and document level.
- **Confidence:** sup
- **Accessed:** 2026-07-26
- **Note:** TWO THINGS TO KNOW BEFORE SEARCHING IT. First, the column called Familienaam often holds a FULL name — 'Victor Vanloocke', not 'Vanloocke' — so the '=' operator finds nothing and 'bevat' must be used. A negative taken with '=' is worthless. Second, many tables carry 'Bestand raadpleegbaar op computer' and a bibliotheeknummer, meaning the index is searchable here but the DOCUMENT is consulted on site at Oostende. So this venue can prove a document exists and name it, and often cannot deliver it. THIRD THING: the tables are not uniformly populated. Databank Rouwbrieven answers a 'bevat' query with real rows; Huwelijksbijlagen Oostende_Microfilms answers nothing at all for any query, which marks it a catalogue stub whose data lives only on the centre's own computers. Test a table with a broad query before trusting a negative from it.
