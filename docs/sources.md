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
| `agatha` <https://agatha.arch.be/> | archive | login | name-index, image-read | 47 | Belgian civil and parish registers by commune and year, with scans. The primary route to 19th-century Belgian acts. |
| `search-arch` <https://search.arch.be/> | archive | offline | name-index, image-read | 2 | Scanned civil registers by commune and year; sibling portal to AGATHA. |
| `familysearch` <https://www.familysearch.org/> | index | login | name-index, image-read, full-text | 39 | Belgian civil and church registration, with act images. |
| `geneanet` <https://www.geneanet.org/> | index | mixed | name-index, tree, image-read | 17 | Member-submitted trees plus an indexed record collection. The member trees are the main lever on a 19th-century frontier. |
| `ancestry` <https://www.ancestry.com/> | index | paywall | name-index, image-read | 2 | West-Vlaanderen and Brabant civil-registration indexes, searchable province-wide. |
| `myheritage` <https://www.myheritage.com/> | index | paywall | name-index, tree | 5 | Indexed Belgian and French civil registration, plus member family trees with automatic Smart Matches against your own uploaded tree. |
| `vrijwilligersrab` <https://www.vrijwilligersrab.be/> | index | open | name-index | 42 | Volunteer transcriptions of West-Flemish marriage and death records. |
| `vvf` | index | mixed | name-index | 0 | Flemish marriage indexes; the layer beneath several Geneanet trees. |
| `stadsarchief-oostende` | archive | offline | image-read | 0 | Oostende civil registers after 1900 — not in AGATHA, not digitised. |
| `inmemoriam` <https://www.inmemoriam.be/> | obituary | open | name-index | 1 | Digitised Belgian obituary notices. |
| `ingedachten` <https://www.ingedachten.be/> | obituary | open | name-index | 1 | Funeral-home obituary notices. |
| `uitvaart-oostende` <https://www.uitvaart-oostende.be/> | obituary | open | name-index | 1 | Oostende funeral notices. |
| `jammart` <https://www.jammart.be/> | obituary | open | name-index | 1 | ~100,000 scanned memorial cards (bidprentjes). |
| `grafzerkje` <https://www.grafzerkje.be/> | cemetery | open | name-index | 1 | Belgian gravestone and cemetery records. |
| `family` | family | offline | testimony | 1 | Testimony, memorial cards, photographs and papers held by relatives. |
| `web` | web | open | full-text | 4 | Parenteel documents and family sites published outside the big platforms. |
| `openarch` <https://www.openarchieven.nl/> | index | open | api, name-index | 60 | About 30 million Belgian person-mentions: the Familiekunde Vlaanderen and Doodsprentjes.be bidprentjes and rouwbrieven, the heemkring collections, and the Rijksarchief civil acts transcribed by the Demogen volunteers. Coverage is uneven by province — Vlaams-Brabant has indexed civil acts with full parent roles; Oostende and Evergem are overwhelmingly 20th-century memorial cards. |
| `fv-dataindexen` <https://dataindexen.familiekunde-vlaanderen.be/> | index | open | name-index | 5 | Familiekunde Vlaanderen's regional documentation centres, in four collections: the TOTAALINDEX OP DE OUDE PAROCHIEREGISTERS (baptism, marriage and burial indexes per parish, arrondissement by arrondissement), the COD Centrum Oostende Databank, FV-Kempen, and Regio Mandelleie, plus klappers on genealogical books. |
| `fs-fulltext` <https://www.familysearch.org/search/full-text> | index | login | full-text, image-read | 5 | Machine transcription of image collections that were never name-indexed: Flemish feudal and nobility records, Gent notarial deeds, militia and military registers, land records. Reaches back to the 1460s — far beyond civil registration, and beyond most parish indexing. Critically for this tree: 'Belgium. Court Records 1639-1700, 1761-1795' — the STATEN VAN GOED, estate inventories drawn up on a death, which name the deceased, the surviving spouse and every child with ages and marriages. That is the richest single document type for pre-1796 Flemish family reconstruction and it is machine-transcribed here. The catalogue is organised as province x record type with a date span each — 'Antwerpen, Rechtsgang, 0190-1995', 'Brabant, Eigendommen, 1273-1964', and the same shape for Migraties, Religieus, Woonplaatsen, Militaire dienst and Biografieen. Property, judicial and residence records reaching back to the Middle Ages, none of it name-indexed. |
| `netradyle` <https://www.netradyle.be/actes/> | index | open | name-index | 8 | 1,353,989 indexed acts for Namur, Liège, Hainaut, BRABANT WALLON, Luxembourg and Vlaams-Brabant: 721,862 births/baptisms, 181,589 marriages, 381,148 deaths/burials, 69,390 other. Mostly 1500-1912. Runs on ExpoActes 3.2.4. Free and completely unauthenticated for visitors — the login is for administrators only, so everything here is reproducible without a session. |

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

**`netradyle`** — FOUND by discovery (2026-07-27) after Open Archives was shown to hold ZERO marriage and ZERO birth acts for Grez-Doiceau — 17,086 of its 17,091 mentions there are death acts. Netradyle reaches the Brabant-wallon layer that Open Archives does not, which makes it the open counterpart to FamilySearch's Brabant films for the Thumas line. HOW TO QUERY WITHOUT A BROWSER, all plain GET: tables are /actes/tab_naiss.php, /actes/tab_mari.php and /actes/tab_deces.php with ?args=<Commune>,<SURNAME>; the commune string for Grez-Doiceau is 'Grez [Brabant Wallon]' — the modern hyphenated name returns nothing. Tables page at 100 rows with &pg=2, and there is NO 'next' link, so a 100-row table is a truncated one and must be paged or it silently reads as complete. Detail pages are /actes/acte_naiss.php?xid=&xct= etc. THE ASYMMETRY THAT MATTERS: birth detail pages carry the father's forename and the mother's full name; MARRIAGE detail pages carry only the two spouses' names and the date — no parents, no ages, no trades, no act number. So this venue can corroborate a parent link from a birth but can never substitute for reading a marriage act. It is a volunteer dépouillement deposited in 2006, index-level throughout, with visible transcription noise (Joustens/Jousten/Jostens, Kinart/Kinar, Derrider/Deridder, and one child's mother given as Marie Thérèse where every sibling has Marie Catherine) — sup, never doc.

## Pages

### Rijksarchief AGATHA — Belgian State Archives search robot

#### `S2` — Jérôme Dekeyser's 1897 Oostende birth act (akte nr. 585)
- **Kind:** record · <https://agatha.arch.be/nl/data/acts/GEWVL_GEBWVL_01442676>
- **Yielded:** The marginal note "Gewettigd 4 5 1901" — so Édouard × Louise married 4 May 1901, legitimizing Jérôme (b. 14 Jun 1897) and Gustavus (b. 1899). Establishes the marriage date without the marriage act.
- **Saved artifact:** `data/artifacts/jerome-dekeyser-1897-birth-agatha.md`
- **Confidence:** sup
- **Accessed:** 2026-07
- **Note:** Confidence corrected doc -> sup in the §52 sweep: this is the archive's index page and AGATHA holds no scan for the act.

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
- **Confidence:** sup
- **Accessed:** 2026-07-25
- **Note:** An AGATHA act analysis — the Rijksarchief's own transcription of the register, with the act number — not the scan. Reached by matching the harvested Open Archives corpus, whose own link pointed at the retired search.arch.be. Confidence corrected doc -> sup in the §52 sweep: an AGATHA act analysis, not the scan, as this note already said.

#### `agatha-diksmuide-1880-birth-emma-vincke` — Birth act nr. 14 — Emma Celesta Vincke, Diksmuide, 24 January 1880 (AGATHA act analysis)
- **Kind:** record · <https://agatha.arch.be/nl/data/acts/GEWVL_GEBWVL_01583386>
- **Yielded:** Diksmuide birth act nr. 14, aktedatum 24/01/1880 (one day after the birth, the ordinary declaration gap): child Emma Celesta Vincke, born Diksmuide 23/01/1880, father Lucien Julianus Vincke, mother Ludovica Maria Vanalderweireldt. The full index transcription is held as data/artifacts/emma-vincke-1880-birth-diksmuide.md.
- **Saved artifact:** `data/artifacts/emma-vincke-1880-birth-diksmuide.md`
- **Confidence:** sup
- **Accessed:** 2026-07-26
- **Note:** AGATHA 'analyse van akte' — index transcription, not the register image; the act page carries no scan/IIIF/viewer link anywhere in its DOM, only the bare text 'SCAN 392 GSU' — structural (this GEWVL birth project publishes the analysis only), not a login problem. A follow-up (2026-07-27) tried the FamilySearch image ark that the vrijwilligersrab Geboorten index supplies for this same row (rab-bs-geboorten) and found the FamilySearch session itself expired — confirmed by a control navigation to a plain catalog page, also redirected to login, and a 401 from platform/users/current. Stays sup; doc needs a live session to actually read the register image.

#### `S11` — Kraainem marriage act nr. 2, 20 June 1872 — Thumas × Bossin (read on AGATHA)
- **Kind:** record · <https://agatha.arch.be/nl/data/acts/HUVLB_HUBRA_00185915_0>
- **Collection:** Burgerlijke stand — Huwelijksakten — Provincie Vlaams-Brabant en Brussels Hoofdstedelijk Gewest, Kraainem 1872, akte nr. 2
- **Yielded:** The same act as S8, read at the archive rather than through an index: Antonia Bossin's exact birth (10 Jan 1849, Sint-Stevens-Woluwe) where the tree had only a year, three occupations (fabriekwerkster, landbouwer, huishoudster), the bridegroom's trade in 1872 as fabrieksgast, and four witnesses with ages and trades.
- **Saved artifact:** `data/artifacts/thumas-bossin-1872-marriage-kraainem.md`
- **Confidence:** sup
- **Accessed:** 2026-07-25
- **Note:** Confidence corrected doc -> sup in the §52 sweep: AGATHA's transcription, not a photograph of the register page.

#### `S14` — Death act nr. 58 — George Thumas, Grez-Doiceau, 20 November 1808 (read on AGATHA)
- **Kind:** record · <https://agatha.arch.be/nl/data/acts/Visu-542_9999_999_616490_000_A_5246-00000035>
- **Collection:** Burgerlijke stand (DemoGen Visu) — België, Grez-Doiceau, overlijdensakten 1808, akte nr. 58
- **Yielded:** Four records documented from one act: George Thumas's death on 20 Nov 1808 at Grez-Doiceau and his trade as menuisier, both as held; his father Lambert Thumas, his mother Marie Leclercq and his wife Marie Catherine Noé all named. It also gives his age as 60, implying a birth around 1747-48 against the 1744 this tree records — a conflict left open rather than resolved on hearsay.
- **Saved artifact:** `data/artifacts/george-thumas-1808-death-grez-doiceau.md`
- **Confidence:** sup
- **Accessed:** 2026-07-26
- **Note:** Confidence corrected doc -> sup in the §52 sweep: an AGATHA act analysis. The DemoGen project name 'Visu' does not mean an image is attached — the page carries none.

#### `S15` — Death act nr. 35 — Marie Catherine Joostens, Grez-Doiceau, 10 June 1857 (read on AGATHA)
- **Kind:** record · <https://agatha.arch.be/nl/data/acts/Visu-542_9999_999_1076594_000_A_5561-00000008>
- **Collection:** Burgerlijke stand (DemoGen Visu) — België, Grez-Doiceau, overlijdensakten 1857, akte nr. 35
- **Yielded:** Her exact death date, 10 June 1857, where the tree had only the year; her birthplace Woluwe-Saint-Lambert and occupation ménagère; and her parents Guillaume Joostens and Jeanne Marie Deconninck read at the archive rather than from an index. It also gives her husband Georges Thumas as 63, implying a birth around 1793-94 against the 1804 the tree records — a ten-year conflict in an act whose arithmetic is right for her own age.
- **Saved artifact:** `data/artifacts/joostens-1857-death-grez-doiceau.md`
- **Confidence:** sup
- **Accessed:** 2026-07-26
- **Note:** Confidence corrected doc -> sup in the §52 sweep: same DemoGen project and same finding as S14.

#### `S19` — Zaventem marriage act nr. 1, 24 February 1846 — Bossin × Peremans
- **Kind:** record · <https://agatha.arch.be/nl/data/acts/HUVLB_HUBRA_00011036_0>
- **Collection:** Burgerlijke stand — Huwelijksakten — Provincie Vlaams-Brabant en Brussels Hoofdstedelijk Gewest, Zaventem 1846, akte nr. 1
- **Yielded:** FOUR new ancestors. The groom's parents Arnoldus Bossin x Elisabeth Deyn, both labourers of Sint-Stevens-Woluwe who attended and signed with a mark; and the bride's parents Egidius Peremans (d. Zaventem 6 Mar 1837) x Joanna Theresia Ver Elst (d. Zaventem 19 Dec 1843), both already dead. It also confirms both spouses' births as 1824-25 from their stated ages of 21, gives both their trades, and settles the bride's mother's name — Joanna Catharina Jacoba, as this tree had it, not the shortened Anna Catharina of the 1872 act.
- **Saved artifact:** `data/artifacts/bossin-peremans-1846-marriage-zaventem.md`
- **Confidence:** sup
- **Accessed:** 2026-07-26
- **Note:** Confidence corrected doc -> sup in the §52 sweep: its own artifact record ends 'The act was read as AGATHA's transcription, not as the register image.'

#### `S22` — Marriage act nr. 9 — Françiscus Pardon × Anna Maria Bossin, Sint-Stevens-Woluwe, 1 December 1853
- **Kind:** record · <https://agatha.arch.be/nl/data/acts/HUVLB_HUBRA_00051488_0>
- **Covers:** AGATHA act analysis, project Burgerlijke stand - Huwelijksakten - Provincie Vlaams-Brabant en Brussels Hoofdstedelijk Gewest. Full transcription: both spouses' birth dates and places, both sets of parents, four witnesses with ages and trades, and the clerk's remarks.
- **Yielded:** A sister for Guilielmus Bossin — the bride's parents are his, and he witnesses at 29, steenslager of Sint-Stevens-Woluwe. Her birth given to the day: Sint-Stevens-Woluwe 3 Nov 1829. Adds the Pardon couple of Winksele. Independently dates Guilielmus to 1824, agreeing with his own 1846 act.
- **Confidence:** sup
- **Accessed:** 2026-07-26
- **Note:** An analysis, not the register image — the scan is not linked from the page. Complete enough to read like an act, but it is a transcription.

#### `ssw-1873-marriage-vandenbemden-coekelberghs` — Sint-Stevens-Woluwe marriage act nr. 6, 24 April 1873 — Van den Bemden × Coekelberghs
- **Kind:** record · <https://agatha.arch.be/nl/data/acts/HUVLB_HUBRA_00057332_0>
- **Collection:** Burgerlijke stand — Huwelijksakten — Provincie Vlaams-Brabant en Brussels Hoofdstedelijk Gewest, Sint-Stevens-Woluwe 1873, akte nr. 6
- **Yielded:** All FOUR parents in one act: Maria Theresia Coekelberghs (b. Bertem 22/11/1848, dienstmeid) as daughter of Jan Baptist Coekelberghs (landbouwer, Bertem) and Anna Haesaerts (landbouwster, Bertem); Hendrik August Van den Bemden (b. Everberg 19/08/1849, dienstbode) as son of Jan Baptist Van den Bemden and Elisabeth Agatha Langes (landbouwster, Everberg). Plus her birth date and place, which the tree held only as the year 1848, and two Van den Bemden witnesses, Lodewijk (40, Sint-Stevens-Woluwe) and Willem (26, Schaarbeek).
- **Confidence:** sup
- **Accessed:** 2026-07-26
- **Note:** An AGATHA act analysis — the Rijksarchief's own transcription, Demogen project huvlb19b — NOT the scan. AGATHA records no image for this act (its URL field reads 'NN'), Open Archives holds no scan for it, and FamilySearch's full-text index does not cover Belgian civil registration. The same transcription is mirrored at https://www.openarchieven.nl/abl:87f9bbf6-4880-593a-8f37-d68346a42f2b . The AGATHA act page renders without a login.

#### `kraainem-1903-marriage-vanesch-coekelberghs` — Kraainem marriage act nr. 16, 6 November 1903 — Van Esch × Coekelberghs, her remarriage
- **Kind:** record · <https://agatha.arch.be/nl/data/acts/HUVLB_HUBRA_00222866_0>
- **Collection:** Burgerlijke stand — Huwelijksakten — Provincie Vlaams-Brabant en Brussels Hoofdstedelijk Gewest, Kraainem 1903, akte nr. 16
- **Yielded:** A second, independent naming of Maria Theresia Coekelberghs's parents — Joannes Baptista Coekelberghs (d. Bertem 19/11/1880) and Anna Haesaerts (d. Bertem 08/01/1880) — with their death dates, which no other held act gives. It also names her late first husband Henricus August Vandenbemden, d. Kraainem 12/08/1889, matching the tree exactly, and gives her a second marriage, to the widower Henricus Van Esch (b. Bertem 23/11/1836, herbergier at Zaventem), fourteen years after she was widowed.
- **Confidence:** sup
- **Accessed:** 2026-07-26
- **Note:** An AGATHA act analysis (Demogen project huvlb20), not the scan. Mirrored at https://www.openarchieven.nl/abl:c22fd42f-4ba4-db17-7908-0e97725a2f08 . Caution for whoever cites the Open Archives page: its rendered HTML gives the three death dates one day earlier than both the API record and the AGATHA page — 11/08/1889, 18/11/1880, 07/01/1880. The AGATHA values are the ones quoted above, and they agree with the API.

#### `bertem-1838-marriage-coeckelberghs-haesaerts` — Bertem marriage act nr. 8, 30 October 1838 — Coeckelberghs × Haesaerts
- **Kind:** record · <https://agatha.arch.be/nl/data/acts/HUVLB_HUBRA_00146698_0>
- **Collection:** Burgerlijke stand — Huwelijksakten — Provincie Vlaams-Brabant en Brussels Hoofdstedelijk Gewest, Bertem 1838, akte nr. 8
- **Yielded:** The marriage of the couple the 1873 and 1903 acts name as Maria Theresia's parents, with their own birth dates and their own parents: Joannes Baptista Coeckelberghs (b. Bertem 29/07/1809, slagter), son of Henricus Coeckelberghs and Petronella Elseviers; Anna Haesaerts (b. Bertem 24/10/1810, landbouwster), daughter of Joannes Baptist Haesaerts and Elisabeth Vanden Broeck. All six lived at Bertem.
- **Confidence:** sup
- **Accessed:** 2026-07-26
- **Note:** Reached from the Open Archives mirror https://www.openarchieven.nl/abl:e18081cf-3acb-279b-061b-5ebd8a678b29 which — unlike the 1873 and 1903 acts — DOES carry a scan link: https://www.familysearch.org/ark:/61903/3:1:9392-HGZ1-T?i=217&cc=1482191&cat=140936 . The image has not been read here, only the transcription. Not grafted: this is the generation above the frontier that found it.

#### `S26` — Marriage act nr. 4 — Jan Baptist Coppens × Joanna Catharina Seraphina Thumas, Kraainem, 27 July 1892
- **Kind:** record · <https://agatha.arch.be/nl/data/acts/HUVLB_HUBRA_00204117_0>
- **Collection:** Burgerlijke stand - Huwelijksakten - Provincie Vlaams-Brabant en Brussels Hoofdstedelijk Gewest, Kraainem
- **Covers:** AGATHA act analysis: full transcription of both spouses, both sets of parents and the witnesses, with birth dates, residences and trades.
- **Yielded:** Bride born Kraainem 21 Mar 1873, daughter of Georgius Carolus Josephus Thumas (fabriekbediende) and Antonia Bossin (huishoudster, alive). Groom born Sint-Stevens-Woluwe 6 Mar 1870, metser, son of Hendrik Coppens x Catharina Bossin.
- **Confidence:** sup
- **Accessed:** 2026-07-26
- **Note:** An analysis, not the register image. Complete enough to read like an act, but it is a transcription.

#### `S27` — Marriage act nr. 4 — Franciscus Coenraets × Henrica Thumas, Kraainem, 15 April 1899
- **Kind:** record · <https://agatha.arch.be/nl/data/acts/HUVLB_HUBRA_00218431_0>
- **Collection:** Burgerlijke stand - Huwelijksakten - Provincie Vlaams-Brabant en Brussels Hoofdstedelijk Gewest, Kraainem
- **Covers:** AGATHA act analysis: full transcription of both spouses, both sets of parents and the witnesses, with birth dates, residences and trades.
- **Yielded:** Bride born Kraainem 24 June 1878, daughter of Georgius Carolus Josephus Thumas (herbergier) and Antonia Bossin, the mother given as dead at Kraainem on 7 Nov 1894. Groom born Sint-Stevens-Woluwe 13 June 1872, brouwersgast, son of Franciscus Coenraets (winkelier) x Anna Amelia Godts (d. Sint-Stevens-Woluwe 5 Jan 1875).
- **Confidence:** sup
- **Accessed:** 2026-07-26
- **Note:** An analysis, not the register image. Complete enough to read like an act, but it is a transcription.

#### `S28` — Marriage act nr. 3 — Ludovicus Bossin × Maria Isabella Helena Thumas, Kraainem, 10 April 1900
- **Kind:** record · <https://agatha.arch.be/nl/data/acts/HUVLB_HUBRA_00218443_0>
- **Collection:** Burgerlijke stand - Huwelijksakten - Provincie Vlaams-Brabant en Brussels Hoofdstedelijk Gewest, Kraainem
- **Covers:** AGATHA act analysis: full transcription of both spouses, both sets of parents and the witnesses, with birth dates, residences and trades.
- **Yielded:** Bride born Sint-Stevens-Woluwe 18 Aug 1880, dienstmeid, daughter of Georgius Carolus Josephus Thumas (herbergier) and Antonia Bossin, again given as dead at Kraainem 7 Nov 1894. Groom born Sint-Stevens-Woluwe 5 Dec 1879, polijster, son of Joannes Baptista Bossin (d. 19 Mar 1887) x Maria Wolf (herbergierster). Witnesses include Georgius Thumas, 24, of Kraainem — an unidentified probable brother of the bride.
- **Confidence:** sup
- **Accessed:** 2026-07-26
- **Note:** An analysis, not the register image. Complete enough to read like an act, but it is a transcription.

#### `agatha-oostende-1907-death-eduardus-bocklandt` — Death act nr. 417 — Eduardus Bocklandt, Oostende, 4 July 1907
- **Kind:** record · <https://agatha.arch.be/nl/data/acts/OVWVL_00502217>
- **Covers:** ['Bocklandt', 'Ichau', 'Van Bergen']
- **Yielded:** Eduardus BOCKLANDT, born Hamme (OVL), died Oostende 4 Jul 1907. Father Antonius Dominicus BOCKLANDT (deceased, place not stated); mother Isabella Livina ICHAU (deceased, place not stated); previous partner Maria Ludovica Van Bergen. Sources edouard_bocklandt's parent links and his marriage, and gives him a death date and birthplace the tree did not have.
- **Confidence:** sup
- **Accessed:** 2026-07
- **Note:** AGATHA 'analyse van akte' — the volunteer index transcription, NOT the register image. The image is behind an AGATHA login and was not opened.

#### `agatha-oostende-1888-death-maria-louisa-vanbergen` — Death act nr. 721 — Maria Louisa Vanbergen, Oostende, 23 November 1888
- **Kind:** record · <https://agatha.arch.be/nl/data/acts/OVWVL_00484466>
- **Covers:** ['Van Bergen', 'Vermandel', 'Bocklandt']
- **Yielded:** Maria Louisa VANBERGEN, born WAASMUNSTER, werkvrouw, died Oostende 23 Nov 1888. Father Joannes Franciscus VANBERGEN, living at Hamme (OVL), metser; mother Ida VERMANDEL, 'overleden te Hamme'; partner Eduardus BOCKLANDT of Oostende, lijndraaiersknecht. Sources marie_vanbergen's parent links and dates her death exactly — and moves her birth from Hamme to Waasmunster.
- **Confidence:** sup
- **Accessed:** 2026-07
- **Note:** AGATHA 'analyse van akte' — index transcription, not the register image.

#### `agatha-oostende-1892-death-alphonsus-bocklandt` — Death act nr. 712 — Alphonsus Bocklandt, Oostende, 26 October 1892
- **Kind:** record · <https://agatha.arch.be/nl/data/acts/OVWVL_00487946>
- **Covers:** ['Bocklandt', 'Van Bergen']
- **Yielded:** Alphonsus BOCKLANDT, born Hamme (OVL), died Oostende 26 Oct 1892; father Eduardus BOCKLANDT, mother Maria Ludovica VAN BERGEN ('overleden te Oostende'). A previously unrecorded child of the couple, i.e. a sibling of louise_bocklandt, and a second independent statement of the couple.
- **Confidence:** sup
- **Accessed:** 2026-07
- **Note:** AGATHA 'analyse van akte' — index transcription, not the register image.

#### `agatha-roksem-1855-death-agatha-stekelorum` — Death act nr. 27 — Agatha Stekelorum, Roksem, 24 May 1855
- **Kind:** record · <https://agatha.arch.be/nl/data/acts/OVWVL_00939687>
- **Covers:** ['Stekelorum', 'Denijs', 'Perquy']
- **Yielded:** Agatha STEKELORUM died Roksem 24 May 1855; father Pieter STEKELORUM, mother Helena DENIJS, partner Joannes PERQUY. The only act in AGATHA's 13.4M-act index that names Pieter Stekelorum and Helena Denijs together, and it sources agatha_stekelorum's parents and husband at once. Act remark: 'SCAN 586 GSU'.
- **Confidence:** sup
- **Accessed:** 2026-07
- **Note:** AGATHA 'analyse van akte' — index transcription, not the register image.

#### `agatha-varsenare-1795-marriage-perquy-stekelorum` — Parish marriage — Joannes Jacobus Perquy x Agatha Francisca Stekelorum, Varsenare, 19 May 1795
- **Kind:** record · <https://agatha.arch.be/nl/data/acts/PARHUWVL_00220569>
- **Covers:** ['Perquy', 'Stekelorum']
- **Yielded:** Dates and places the Perquy x Stekelorum marriage: Varsenare, 19 May 1795. Both fathers are indexed by surname only ('Stekelorum', 'Perquy') with no forename, so it does NOT name Pieter Stekelorum.
- **Confidence:** sup
- **Accessed:** 2026-07
- **Note:** AGATHA parish-register index entry, not the register image.

#### `agatha-oostkamp-doopregister-1630-1652` — Oostkamp Sint-Pietersbanden parish register: baptisms 26 Jun 1630 - 14 Apr 1652 (and marriages 9 Aug 1631 - 14 Apr 1652), AGATHA digitised item 513_9000_000_00774
- **Kind:** collection · <https://agatha.arch.be/nl/search/genealogie/35229>
- **Covers:** ['Van Nieuwenhuyse', 'Monballiu', 'Govaert']
- **Yielded:** Resolves the reference 'agatha.arch.be scan 513_9000_000_00774' in petrus_vannieuwenhuyse's record. It is a real, unique AGATHA item: /nl/search/genealogie/35229 redirects to /nl/data/images/513/513_9000_000_00774_000/0_0001, the Oostkamp Sint-Pietersbanden baptism register 1630-1652 (the marriage section of the same volume starts at scan 0_0165, /nl/search/genealogie/35226). It is the register that would contain a 7 Mar 1649 Oostkamp baptism. The reference names the VOLUME, not a scan page or an act.
- **Confidence:** unk
- **Accessed:** 2026-07
- **Note:** The images are behind an AGATHA login ('Gelieve in te loggen om de afbeeldingen te bekijken') and were NOT opened, so nothing in the register has been read. Also note the register is Doopakten: a 1649 date read there is a BAPTISM date, not necessarily a birth date. The adjacent volume, baptisms 1652-1673, is marked 'Niet beschikbaar - hiaten in de originele registers en op de microfilms'.

#### `agatha-oostende-1903-death-angela-dekeyser` — Death act nr. 828 — Angela Luciana Dekeyser, Oostende, 20 October 1903
- **Kind:** record · <https://agatha.arch.be/nl/data/acts/OVWVL_00498208>
- **Covers:** ['Dekeyser', 'Bocklandt']
- **Yielded:** Angela Luciana DEKEYSER, born and died Oostende, d. 20 Oct 1903; father Eduardus DEKEYSER, 26, werkman; mother Louisa Maria BOCKLANDT, zonder beroep. A previously unrecorded child of edouard_dk x louise_bocklandt. Does not name Louise's own parents.
- **Confidence:** sup
- **Accessed:** 2026-07
- **Note:** AGATHA 'analyse van akte' — index transcription, not the register image.

#### `agatha-oostende-1888-marriage-bocklandt-ketels` — Marriage act nr. 80 — Petrus Dominicus Ketels x Paulina Bocklandt, Oostende, 26 May 1888
- **Kind:** record · <https://agatha.arch.be/nl/data/acts/HUWVL2_HUWVL_00579176>
- **Covers:** ['Bocklandt', 'Van Bergen', 'Ketels']
- **Yielded:** Paulina BOCKLANDT, born Hamme (O-Vl) 30 Apr 1870, werkmeid, resident Oostende, daughter of Eduardus Bocklandt (50, touwslagersknecht) and Maria Louisa Vanbergen. Married Petrus Dominicus Ketels (b. Waasmunster 15 Oct 1857, touwslagersknecht), father not named in the act (NN NN), mother Maria Louisa Ketels of Waasmunster. A previously unrecorded child of edouard_bocklandt x marie_vanbergen, and a sibling of louise_bocklandt.
- **Confidence:** sup
- **Accessed:** 2026-07-26
- **Note:** AGATHA 'analyse van akte' — index transcription, not the register image. Found inside the same NAME=Bocklandt ALL_PLACES=Hamme 'Analyses van akten' result set already logged as a miss for a different goal in research/searches.jsonl (the Eduardus x Maria Louisa marriage act itself, which is not among these 18 results).

#### `agatha-oostende-1892-marriage-bocklandt-debuf` — Marriage act nr. 42 — Fredericus Desiderius Debuf x Maria Elodia Bocklandt, Oostende, 26 March 1892
- **Kind:** record · <https://agatha.arch.be/nl/data/acts/HUWVL2_HUWVL_00583492>
- **Covers:** ['Bocklandt', 'Van Bergen', 'Debuf']
- **Yielded:** Maria Elodia BOCKLANDT, born Hamme (O-Vl) 9 Mar 1874, werkmeid, resident Oostende, daughter of Eduardus Bocklandt (54, touwslagersknecht) and the already-deceased Maria Ludovica Vanbergen (d. Oostende 22 Nov 1888). Married Fredericus Desiderius Debuf (b. Oostende 28 Sep 1871, matroos bij het zeewezen), son of Desiderius Joannes Debuf (lost at sea, akte van bekendheid 23 Feb 1892) and Silvia Clementia Vandamme. A previously unrecorded child of edouard_bocklandt x marie_vanbergen, and a sibling of louise_bocklandt.
- **Confidence:** sup
- **Accessed:** 2026-07-26
- **Note:** AGATHA 'analyse van akte' — index transcription, not the register image. Same NAME=Bocklandt ALL_PLACES=Hamme result set as agatha-oostende-1888-marriage-bocklandt-ketels.

#### `agatha-oostende-1893-marriage-bocklandt-dubuy` — Marriage act nr. 11 — Justinus Vincentius Dubuy x Maria Mathildis Bocklandt, Oostende, 21 January 1893
- **Kind:** record · <https://agatha.arch.be/nl/data/acts/HUWVL2_HUWVL_00578740>
- **Covers:** ['Bocklandt', 'Van Bergen', 'Dubuy']
- **Yielded:** Maria Mathildis BOCKLANDT, born Hamme (O-Vl) 12 May 1872, werkmeid, resident Oostende, daughter of Eduardus Bocklandt (54, touwslagersknecht) and the already-deceased Maria Louisa Vanbergen (act misdates her death 22/11/1858, against every other act's 22 Nov 1888). Married Justinus Vincentius Dubuy (b. Oostende 29 Dec 1870, touwslagersknecht), son of the already-deceased Justinus Vincentius Lud. Dubuy and Carolina Reck. A previously unrecorded child of edouard_bocklandt x marie_vanbergen, and a sibling of louise_bocklandt.
- **Confidence:** sup
- **Accessed:** 2026-07-26
- **Note:** AGATHA 'analyse van akte' — index transcription, not the register image. Same NAME=Bocklandt ALL_PLACES=Hamme result set as agatha-oostende-1888-marriage-bocklandt-ketels.

#### `agatha-diksmuide-1893-marriage-bocklandt-vincke` — Marriage act nr. 40 — Caesar Antonius Bocklandt x Florence Amelie Vincke, Diksmuide, 11 February 1893
- **Kind:** record · <https://agatha.arch.be/nl/data/acts/HUWVL2_HUWVL_00087182>
- **Covers:** ['Bocklandt', 'Van Bergen', 'Vincke', 'Vanalderweireldt']
- **Yielded:** Caesar Antonius BOCKLANDT, born Hamme (O-Vl) 2 Jul 1867, koordedraaier, resident Oostende, son of Eduard Bocklandt (53, koordedraaier) and the already-deceased Maria Louisa Vanbergen. Married Florence Amelie Vincke (b. Diksmuide 22 Apr 1869, kantwerkster), daughter of Lucien Julianus Vincke and Ludovica Maria Vanalderweireldt of Diksmuide. A previously unrecorded child of edouard_bocklandt x marie_vanbergen, and a sibling of louise_bocklandt. ACTED ON (2026-07-27, research-log §64): the bride's parents match this tree's existing lucien_vincke x ludovica_vanald (parents of emma_vincke, Van Iseghem line) by full name, and a province-wide RAB birth-index sweep found no rival couple — she now has her own record, florence_vincke, joining the Van Iseghem and De Keyser/Bocklandt branches of this tree (objective 3).
- **Confidence:** sup
- **Accessed:** 2026-07-26
- **Note:** AGATHA 'analyse van akte' — index transcription, not the register image. Same NAME=Bocklandt ALL_PLACES=Hamme result set as agatha-oostende-1888-marriage-bocklandt-ketels.

#### `agatha-oostende-1900-marriage-bocklandt-mewis` — Marriage act nr. 100 — Philemondus Bocklandt x Rosalia Cecilia Mewis, Oostende, 12 May 1900
- **Kind:** record · <https://agatha.arch.be/nl/data/acts/HUWVL2_HUWVL_00583944>
- **Covers:** ['Bocklandt', 'Van Bergen', 'Mewis']
- **Yielded:** Philemondus BOCKLANDT, born Hamme (O-Vl) 10 Jun 1880, touwslagersknecht, resident Oostende, son of Eduardus Bocklandt (62, touwslagersknecht) and the already-deceased Maria Louisa Vanbergen. Married Rosalia Cecilia Mewis (b. Oostende 29 Sep 1881, werkmeid), daughter of Franciscus Antonius Mewis and Theresia Lomard of Oostende. A previously unrecorded child of edouard_bocklandt x marie_vanbergen, and a sibling of louise_bocklandt — born two days after his infant brother ludovicus_bocklandt died at Hamme (10 Jun against 8 Jun 1880), a coincidence worth reading with caution given the birthdate is a twenty-years-later recollection, not a contemporary record.
- **Confidence:** sup
- **Accessed:** 2026-07-26
- **Note:** AGATHA 'analyse van akte' — index transcription, not the register image. Same NAME=Bocklandt ALL_PLACES=Hamme result set as agatha-oostende-1888-marriage-bocklandt-ketels.

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
- **Confidence:** sup
- **Accessed:** 2026-07-22
- **Note:** FRONTIER, unconfirmed: a Desiderius de Keyser b. 27 May 1832 with parents Arnoldus de Keyser × Angelina Sophia van Kerkhove exists, but nothing ties him to Van den Broeck. Do not graft until an act does. Confidence corrected doc -> sup in the §52 sweep: consulted as a name-index, result ambiguous, and nothing was grafted from it.

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
- **Confidence:** doc
- **Accessed:** 2026-07-26
- **Note:** FamilySearch's index entry, not the register image; the image is reachable from the record page and reading it would make the three people doc. Confidence corrected sup -> doc in the §52 sweep, an UPGRADE and the only one: the first artifact under this id was the index, but it was superseded by leonie-paelinck-1901-birth-register, where the register image itself was read. The three citing records already carried doc; the registry entry was the stale one.

#### `fs-wvl-bs` — België, West-Vlaanderen, burgerlijke stand, 1582-1950
- **Kind:** collection · <https://www.familysearch.org/search/record/results?q.surname=Vanstechelman&q.motherSurname=Wagebaert&f.recordCountry=Belgium>
- **Covers:** West-Flemish civil registration indexed by person with parents and spouses attached. Searching by a rare MOTHER's surname is what makes it useful — it isolates one couple's children out of a common paternal surname.
- **Yielded:** The Vanstechelman x Wagebaert household at Oostende. Searching the mother's rare surname returned three children of Petrus Jacobus Vanstechelman x Clementia Sophia Wagebaert that the tree does not have: Henricus Emilius (b. 1877, d. Oostende 17 Jan 1941, m. Alicia Mathildis St Martin), Leontius Ivo (m. Oostende 20 Aug 1922, Lucia Amelia Maene) and Paula Mathilde (m. Oostende 11 May 1924, Alberic Luciaan Delrue). Each act names both parents, which corroborates Augusta Vanstechelman's parentage from civil registration rather than from the stechec tree.
- **Confidence:** sup
- **Accessed:** 2026-07-26
- **Note:** Index entries; none of these acts has been read as an image, so nothing here rises above sup.

#### `S20` — Marriage act nr. 258 — Eugenius Alphonsius Devriendt × Octavia Maria Schalandrijn, Oostende, 10 November 1906
- **Kind:** record · <https://www.familysearch.org/ark:/61903/3:1:S3HT-D8M7-Y6D?i=172&cat=294936>
- **Covers:** Register image, film 004166040 image 173 (act body) and image 174, ark:/61903/3:1:S3HT-D8M7-YFW (witnesses and signatures), Oostende marriage register 1906. Read on screen while logged in; no image file has been saved yet.
- **Yielded:** Both sets of parents, from the act itself: the groom is the of-age son of the LATE Ludovicus Josephus Devriendt and of Silvia Rosalia Brissinck, werkvrouw of Steene, present and consenting; the bride is the MINOR daughter of Ludovicus Schalandrijn, werkman, resident at Oostende, present and consenting, and of the LATE Mathilde Standaert. Gives the bride's birth as Breedene 30 April 1886, two days before the act date this tree had recorded as her birth.
- **Confidence:** doc
- **Accessed:** 2026-07-26
- **Note:** FOLLOW-UP: the act body (image 173) and the witnesses/signatures page (image 174) were read on screen at the two arks above, but no image file was ever saved to data/artifacts/. That is the honest state of the evidence, not a silent gap — capturing the artifact is pass-2 material. NOTE ON THE ID: originally logged as S19; renumbered to S20 because a concurrent pass took S19 for the Zaventem Bossin x Peremans act while this id was stashed out of the working tree — see docs/research-log.md §46.

#### `S21` — Birth act nr. 116 — Octavia Maria Schalandrijn, Bredene, certificate dated 2 May 1886
- **Kind:** record · <https://www.familysearch.org/ark:/61903/3:1:33S7-9PZQ-LS7>
- **Covers:** Register image, image 84, Bredene birth register 1886. Read on screen while logged in; no image file has been saved yet.
- **Yielded:** States she was born 'eergisteren de dertigsten April ten vijf uren 's morgens' (the day before yesterday, the thirtieth of April, at five in the morning) against a certificate/act date of 2 May — the act date this tree had wrongly held as her birth date. Also gives her mother Mathilde Standaert's age as 42 and occupation 'huishoudster, geboortig van Brugge' (housekeeper, native of Bruges), and her father as Ludovicus Schalandryn.
- **Confidence:** doc
- **Accessed:** 2026-07-26
- **Note:** FOLLOW-UP: read on screen at the ark above; no image file has been saved to data/artifacts/ — the same named gap as S20.

#### `S23` — Extract from the Grez-Doiceau death register — Georges Thumas, d. 12 January 1864 (issued 28 September 1868 as a marriage annex)
- **Kind:** record · <https://www.familysearch.org/ark:/61903/3:1:3QS7-L93X-692M?view=index&personArk=%2Fark%3A%2F61903%2F1%3A1%3A6VSH-GSKT&lang=nl>
- **Collection:** Grez-Doiceau, Huwelijksakten september 1866 - april 1873, image 221 of 772 — the volume binds the huwelijksbijlagen with the acts
- **Covers:** Register image, read at full resolution. A death-act extract drawn up for a child's marriage.
- **Yielded:** Georges Thumas died at Grez-Doiceau on 12 January 1864, widower of Marie Catherine Joostens, son of Lambert Georges Thumas and Marie Catherine Quinart, both then dead. First documentary proof of his parent link, which had rested on Geneanet alone, and of the death date. Delivered free of charge for certified indigence. Gives no age, so the 1804/1794 conflict stays open.
- **Saved artifact:** `data/artifacts/georges-thumas-1864-death-extract-grez-doiceau.md`
- **Confidence:** doc
- **Accessed:** 2026-07-26
- **Note:** METHOD: AGATHA has no Grez-Doiceau death act for 1864, but the extract survives inside the MARRIAGE volume as a huwelijksbijlage. Death acts hide in marriage annexes — the route into every commune whose death series is unindexed.

#### `S24` — Birth declarations at Sint-Stevens-Woluwe for three children of Guilielmus Bossin x Peremans, 1847-1853
- **Kind:** index · <https://www.familysearch.org/search/record/results?q.surname=Bossin&q.fatherGivenName=Guilielmus&q.fatherSurname=Bossin&q.motherSurname=Peremans&f.recordCountry=Belgium&q.birthLikeDate.from=1846&q.birthLikeDate.to=1870>
- **Collection:** Belgium, Brabant, Civil Registration and Church Records, 1704-1916
- **Covers:** Indexed civil birth declarations, searchable by both parents. No register image read.
- **Yielded:** Three children of the couple at Sint-Stevens-Woluwe: Cornelius (declared 13 Sept 1847), Antonius/Antonia (11 Jan 1849 — this tree's Antonia Bossin, whose birth the 1872 act gives as 10 Jan), Ludovica (5 Oct 1853). Plus Ludovica's marriage at Alsemberg 17 Feb 1884 to Joannes Baptista Julianus Swaelens. The already-documented middle child is what makes the series safe.
- **Saved artifact:** `data/artifacts/bossin-peremans-children-sint-stevens-woluwe.md`
- **Confidence:** sup
- **Accessed:** 2026-07-26
- **Note:** An index. Declaration dates, not birth dates. Search covered 1846-1870 only, so further children are possible.

#### `S25` — The children of Georges Thumas x Marie Catherine Joostens at Grez-Doiceau, 1835-1868
- **Kind:** index · <https://www.familysearch.org/search/record/results?q.surname=Thumas&q.fatherSurname=Thumas&q.motherSurname=Joostens&f.recordCountry=Belgium>
- **Collection:** Belgium, Brabant, Civil Registration and Church Records, 1704-1916
- **Covers:** Indexed civil registration searchable by both parents at once. No register image read.
- **Yielded:** Four siblings for Georges Carolus Josephus Thumas: Marie Therese Stephanie (declared 11 Aug 1835), Georges Joseph (31 Mar 1843), Jean Baptiste Zenon (20 Aug 1845), Charles Eugene (d. 9 Apr 1851 as an infant). Plus Georges Joseph's marriage to Sophie Miranda Deridder at Grez-Doiceau on 7 Oct 1868 — the marriage the S23 death extract of 28 Sept 1868 was drawn for. The anchor is georges_cj's own declaration of 16 Sept 1836, one day after the birth read from his 1872 act.
- **Saved artifact:** `data/artifacts/thumas-joostens-children-grez-doiceau.md`
- **Confidence:** sup
- **Accessed:** 2026-07-26
- **Note:** CAUTION: two brothers named Georges — Georges Charles Joseph (b. 1836, m. Kraainem 1872) and Georges Joseph (b. 1843, m. Grez-Doiceau 1868). Do not merge.

#### `S29` — Marriage of Petrus van der Varent x Maria Josephina Peremans, Zaventem, 5 November 1840
- **Kind:** record · <https://www.familysearch.org/ark:/61903/1:1:X98K-CXNQ?lang=nl>
- **Collection:** Belgium, Brabant, Civil Registration and Church Records, 1704-1916 — volume 'Zaventem. Huwelijksakten 1840'
- **Covers:** Indexed marriage registration with the register page. The record carries no place; the VOLUME TITLE supplies Zaventem, which is what anchors the identification.
- **Yielded:** A sister for Joanna Catharina Jacoba Peremans — Maria Josephina, married Petrus van der Varent (27, b. ~1813, son of Joannes van der Varent x Anna Catharina Goossens) at Zaventem on 5 Nov 1840, her parents given as Egidius Peremans x Joanna Theresia ver Elst.
- **Saved artifact:** `data/artifacts/vandervarent-peremans-1840-marriage-zaventem.md`
- **Confidence:** sup
- **Accessed:** 2026-07-26
- **Note:** METHOD: when an indexed record gives no place, open the image and read the VOLUME TITLE — it names the commune and turns a name-only match into an anchored one. Also: Egidius was dead by 1840, so the annexes to this marriage should hold his death-act extract.

#### `S30` — Marriage banns of Cornelius Peremans, Zaventem, 21 April 1844
- **Kind:** record · <https://www.familysearch.org/ark:/61903/1:1:X98K-NBZZ?lang=nl>
- **Collection:** Belgium, Brabant, Civil Registration and Church Records, 1704-1916 — volume 'Zaventem. Kerkelijke huwelijksafkondigingen 1844'
- **Covers:** Indexed church marriage banns. As with S29 the record carries no place; the volume title supplies Zaventem.
- **Yielded:** A second sibling for Joanna Catharina Jacoba Peremans — Cornelius, son of Egidius Peremans x Theresia Verelst, banns published at Zaventem on 21 April 1844, four months after his mother's death. The index also lists Lambertus van der Pelen, Maria Catharina van der Vaeren and Maria Anna van der Vaeren in the same document WITHOUT stating their roles, so the bride is not recorded.
- **Confidence:** sup
- **Accessed:** 2026-07-26
- **Note:** Banns, not the marriage act. The act itself would name the bride and both sets of parents.

#### `S31` — Marriage of Joannes Athanasius Peremans x Maria Elisabeth Cuypers, Zaventem, November 1844
- **Kind:** record · <https://www.familysearch.org/ark:/61903/1:1:X98K-63N2?lang=nl>
- **Collection:** Belgium, Brabant, Civil Registration and Church Records, 1704-1916 — volume 'Zaventem. Kerkelijke huwelijksafkondigingen 1844'
- **Covers:** Indexed banns (17 and 24 Nov) and marriage registration (28 Nov 1844). The record carries no place; the volume title supplies Zaventem, as with S29 and S30.
- **Yielded:** A third sibling for Joanna Catharina Jacoba Peremans — Joannes Athanasius, b. about 1822, with his parents EXPLICITLY labelled Vader Egidius Peremans and Moeder Joanna Theresia ver Elst, married Maria Elisabeth Cuypers, daughter of Antonius Cuypers x Anna Maria de Hose. Four people.
- **Confidence:** sup
- **Accessed:** 2026-07-26
- **Note:** Unlike S30 this entry LABELS the roles — Vader, Moeder, spouse, and the spouse's parents as 'overige personen' — so the family shape is stated rather than inferred.

#### `fs-bertem-1838-marriage-register-nr8` — Bertem marriage register 1838, act nr. 8, 30 October 1838 — Coekelberghs × Haesaerts (REGISTER IMAGE)
- **Kind:** record · <https://www.familysearch.org/ark:/61903/3:1:9392-HG83-X>
- **Collection:** Belgium, Brabant, Civil Registration, 1582-1950 — Bertem, Geboorten 1891-1910, huwelijken 1833-1910, overlijdens 1881-1910; image 219 of 702 (image-index 218), right-hand page, lower act
- **Yielded:** The ACT IMAGE behind bertem-1838-marriage-coeckelberghs-haesaerts, read line by line. Settles the bride's forename as plain ANNA (written twice in the display hand and once in the operative declaration, with no second forename), the groom's trade as SLAGTER, and both birth dates — him Berthem 29 July 1809, her Berthem 24 October 1810. All four parents are recorded present and consenting: Henricus Coekelberghs × Petronella Elseviers, and Joannes Baptista Haesaerts × Elisabeth van den Broeck, all four landbouwers at Berthem. Adds what AGATHA omits: banns 14 and 21 October 1838; officiant Philippus Neerdaels, schepen aengesteld; four witnesses — Philippus Neerdaels 34 onderwyzer, Franciscus Massaut 55 blokmaeker, Jan Frans Vandersijpen 34 veldwagter, Dominicus Neerdaels 66 landbouwer, none stated as kin; and the fact that the bridegroom, the bride AND both sets of parents all declared they could not sign.
- **Saved artifact:** `data/artifacts/coekelberghs-haesaerts-1838-marriage-bertem.md`
- **Image:** <https://sg30p0.familysearch.org/service/records/storage/deepzoomcloud/dz/v1/3:1:9392-HG83-X/image.xml>
- **Confidence:** doc
- **Accessed:** 2026-07-26
- **Note:** The scan link on the Open Archives mirror points at ...?i=217, which the FamilySearch viewer resolves to the opening holding acts nr. 1-4 of 1838; act nr. 8 is one opening further on, at image-index 218 / 'Afbeelding 219', whose own ark is 3:1:9392-HG83-X. The image was read by stitching the deep-zoom tiles: the descriptor is at .../deepzoomcloud/dz/v1/3:1:9392-HG83-X/image.xml (5529x4021, tile 256, overlap 1, max level 13) and the tiles at .../image_files/13/<col>_<row>.jpg. Those endpoints refuse cross-origin fetch from www.familysearch.org, so the stitching has to run on the sg30p0.familysearch.org origin itself. This is the 'gelijkvormige kopij' — the duplicate register deposited with the court — not the commune's original; the printed footer of every act says so. A FamilySearch session is needed, which is why the artifact is kept.

#### `fs-stene-1924-marriage-blomme-bocklandt` — Marriage act nr. 9 — Petrus Augustus Blomme x Louisa Maria Bocklandt, Stene, 1 March 1924 (register image)
- **Kind:** record · <https://www.familysearch.org/ark:/61903/1:1:X7YH-857T>
- **Covers:** ['Bocklandt', 'Blomme', 'Van Bergen', 'Dekeyser', 'Meseure']
- **Yielded:** The act image, read. Louisa Maria Bocklandt, werkvrouw of Stene, BORN AT HAMME (OOST-VLAANDEREN) 31 DECEMBER 1877, daughter of Eduardus Bocklandt (d. Oostende 4 Jul 1907) and Maria Louisa Van Den Bergen (d. Oostende 22 Nov 1888), DIVORCED WIFE OF EDUARDUS DE KEYSER by decree of the rechtbank van eersten aanleg te Brugge of 14 November 1922; married at Stene on 1 March 1924 Petrus Augustus Blomme, werkman, born Stene 23 January 1884, son of Josephus Blomme (living, Oostende) and Mathilde Sophia Meseure (d. Oostende 21 Jul 1922). Closes the Bocklandt-Blomme frontier named in louise_bocklandt's record, sources her parent link from a primary act, and dates the divorce that the tree held only as '~1923'.
- **Saved artifact:** `data/artifacts/blomme-bocklandt-1924-marriage-stene.md`
- **Confidence:** doc
- **Accessed:** 2026-07
- **Note:** The REGISTER IMAGE was read in the FamilySearch viewer and is saved as an artifact; this is not an index page. FamilySearch's own index dates the act 1 May 1924 - the register says 1 March 1924.

#### `fs-hamme-1880-death-ludovicus-bocklandt` — Death act nr. 126 — Ludovicus Bocklandt, Hamme (O-Vl), 9 June 1880 (register image)
- **Kind:** record · <https://www.familysearch.org/ark:/61903/1:1:6TRL-6YGL>
- **Covers:** ['Bocklandt', 'Van Bergen']
- **Yielded:** The act image, read. Eduardus Bocklandt, 40, zeeldraaier of Hamme, declaring the death of his son Ludovicus Bocklandt, about 5, born and living at Hamme, son of himself and Maria Louisa Van Bergen, 39, spinster, of 't Kleinsmiske, Hamme. Places the couple at Hamme in 1880, gives Eduardus an age consistent with birth 1839, adds a further child, and carries his trade forward to the Oostende acts.
- **Saved artifact:** `data/artifacts/bocklandt-ludovicus-1880-death-hamme.md`
- **Confidence:** doc
- **Accessed:** 2026-07
- **Note:** REGISTER IMAGE read in the FamilySearch viewer, saved as an artifact. Film #004833291 item 1, image 552 of 1082.

#### `fs-hamme-civil-registers-film-004833291` — Hamme (Oost-Vlaanderen) civil registers on FamilySearch — film #004833291: births 1887-1888, deaths 1880-1888, marriages 1881-1888, 1082 browsable images
- **Kind:** collection · <https://www.familysearch.org/ark:/61903/3:1:33SQ-GPDS-ZJ5?view=index&lang=nl>
- **Covers:** ['Bocklandt', 'Van Bergen', 'Ichau', 'Vermandel']
- **Yielded:** Proof that the Hamme (O-Vl) registers ARE digitised and browsable, with a name index, on FamilySearch - the wall that stopped every Open Archives and AGATHA search for this family is a gap in those two venues only. The neighbouring films in the same series are where louise_bocklandt's birth act of 31 Dec 1877 and the Bocklandt x Van Bergen marriage of the 1860s will be.
- **Confidence:** doc
- **Accessed:** 2026-07
- **Note:** Browsable images plus a partial FamilySearch index; the 1877 birth register and the pre-1881 marriage registers are separate films in the same Hamme series and were NOT opened in this pass.

#### `fs-hamme-1865-death-ida-vermandel` — Death act nr. 123 — Ida Vermandel, Hamme (Oost-Vlaanderen), died 21 June 1865 (register image)
- **Kind:** record · <https://www.familysearch.org/ark:/61903/3:1:S3HY-67JS-YLV?i=79&cat=koha%3A349052&lang=nl>
- **Covers:** ['Vermandel', 'Van Bergen', 'Verplancken']
- **Yielded:** The act image, read. Ida Vermandel, 39, arbeidster, BORN AT ZELZATE, living at Hamme, wife of Joannes Franciscus Van Bergen, died 21 June 1865 at half past eight in the evening in the women's burgerhospitaal on the Marktplein at Hamme; act drawn up 22 June 1865 by burgemeester Jacques Johannes Vertongen, declared by Norbertus Joannes Stabbaert (38) and Petrus Seraphinus Dieriex (51, veldwachter). NAMES HER PARENTS, both still living in 1865: [P]rimus Vermandel and [?]phina Verplancken — the father's forename reads 'Primus', the mother's capital is ambiguous (Josephina / Delphina). Turns a year-only death into a day and a place, gives her birth commune, her trade, and the next generation up as a CANDIDATE, not a graft.
- **Saved artifact:** `data/artifacts/vermandel-ida-1865-death-hamme.md`
- **Confidence:** doc
- **Accessed:** 2026-07-26
- **Note:** REGISTER IMAGE, read by stitching the FamilySearch deep-zoom tiles on the sg30p0 origin. Film #1114009 / DGS 004198666, item 1, image 80 of 556. Located from the 1865 tafel on the same film, image 107.

#### `fs-hamme-civil-registers-1796-1900` — Hamme (Oost-Vlaanderen) civil registers 1796-1900 on FamilySearch — catalogue koha:349052, 88 browsable film items
- **Kind:** collection · <https://www.familysearch.org/nl/search/catalog/koha:349052>
- **Covers:** ['Bocklandt', 'Van Bergen', 'Vermandel', 'Ichau']
- **Yielded:** The full film map for Hamme (O-Vl), every item online. Births 1796-1814/1815-1822/1823-1830/1831-1839/1840-1850/1851-1857/1858-1864/1865-1871/1872 (DGS 004091375-004091384, 004091246); MARRIAGES 1796-1803 (004817680), 1803-1818 (004817776), 1819-1829 (004817777), 1830-1840 (004817778), 1841-1850 (004817779), 1851-1861 (004817780), 1862-1872 (004817781); DEATHS 1796-1801 (004198937) … 1851-1863 (004198943), 1864-1872 (004198666); plus huwelijksafkondigingen and a near-complete run of huwelijksbijlagen. This is the index that turns 'Hamme is unreachable' into 'Hamme is a browse'.
- **Confidence:** doc
- **Accessed:** 2026-07-26
- **Note:** Filmed from the originals at the Gerechtshof te Dendermonde. Supersedes the single-film entry fs-hamme-civil-registers-film-004833291 as the way in; that film is item 1768237 in this same catalogue record.

#### `fs-waasmunster-civil-registers-1796-1900` — Waasmunster (Oost-Vlaanderen) civil registers 1796-1900 on FamilySearch — catalogue koha:15958, 34 microfilm reels
- **Kind:** collection · <https://www.familysearch.org/nl/search/catalog/koha:15958>
- **Covers:** ['Van Bergen', 'Vermandel']
- **Yielded:** Establishes that Waasmunster civil registration IS digitised and browsable, which neither Open Archives nor AGATHA holds in any form. Births 1796-1814 (DGS 004794009), 1815-1843 (004794010), 1844-1872 (004794011); MARRIAGES 1796-1850 (004794012), 1851-1877 (004794013); huwelijksbijlagen 1806-1835+; ten-year tables on separate films (marriages 1833-1842 = film 1074817). Marie-Louise Van Bergen's 1842 birth act and any Van Bergen x Vermandel marriage before 1850 sit on films 004794010 and 004794012.
- **Confidence:** doc
- **Accessed:** 2026-07-26
- **Note:** Filmed from the originals at the Gerechtshof te Dendermonde. Parish registers for Waasmunster (O.-L.-Vrouw, 1586-1807) and Vervoort's transcriptions of the baptisms 1743-1779 and marriages 1733-1783 are separate catalogue records at the same place.

#### `fs-zelzate-civil-registers-1796-1870` — Zelzate (Oost-Vlaanderen) civil registers 1796-1870 on FamilySearch — catalogue koha:20457
- **Kind:** collection · <https://www.familysearch.org/nl/search/catalog/koha:20457>
- **Covers:** ['Vermandel', 'Verplancken']
- **Yielded:** The route to Ida Vermandel's own birth act, c. 1825-26. TIENJARIGE TAFELS 1802-1870 on one film (DGS 005089047) — one lookup gives the act number; Geboorten 1816-1840 (004670480); Huwelijken 1821-1860 (004670484) and 1797-1820 (004670483) for her parents' marriage; Overlijden 1811-1840 (004186911) and 1841-1870 (004186912) for [P]rimus Vermandel and [?]phina Verplancken, both alive in June 1865.
- **Confidence:** doc
- **Accessed:** 2026-07-26
- **Note:** Not yet opened. Registered here because the 1865 Hamme death act names Zelzate as Ida's birth commune, which is what makes this film set the next act to read.

#### `fs-hamme-1882-marriage-vermorgen-vandenberghe` — Marriage act, 18 May 1882, Hamme (Oost-Vlaanderen) — Petrus Vermorgen × Paulina Van Den Berghe (register image)
- **Kind:** record · <https://www.familysearch.org/ark:/61903/1:1:6TRL-HZTX?lang=nl>
- **Covers:** FamilySearch film 004833291, item 1, image 249 — the register page itself, read by stitching the deep-zoom tiles on the sg30p0.familysearch.org origin. Previously registered from the name index alone.
- **Yielded:** Names the bride as meerderjarige dochter van Joannes Franciscus Van Den Berghe, metser, 65, living at Hamme, present and consenting, en van wijlen Ida Vermandel, overleden te Hamme den eenen twintigste Juny achttien honderd vyf en zestig. That death date and place match, to the day, the Hamme death act nr. 123 read separately seventeen years earlier — so it resolves the Van Bergen / Van Den Berghe spelling as one family rather than two, and makes Paulina a graftable daughter. It also gives the father's age (65 in May 1882, so born about 1817) and his trade, metser, the same trade his daughter Marie-Louise's 1888 Oostende death act gives him.
- **Confidence:** doc
- **Accessed:** 2026-07-26
- **Note:** INDEX ENTRY ONLY — the FamilySearch name index over Hamme film #004833291, image 331ff. The register image was not read, and the index gives no place field for the birth years. The 1865 death act of Ida Vermandel spells the husband's surname VAN BERGEN, so the two spellings are the same family or two families sharing a rare wife's name; the register image of this 1882 act would settle it.

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

### Vrijwilligers RAB

#### `rab-bs-huwelijken` — West-Vlaamse Burgerlijke Stand — Huwelijken (marriage index), Rijksarchief Brugge/Kortrijk volunteers
- **Kind:** collection · <https://www.vrijwilligersrab.be/en/Civil_Status_Marriages_Index>
- **Covers:** Volunteer-transcribed index of West-Flemish CIVIL marriage acts, searchable by surname of either spouse OR of any of the four parents — which is what makes it answer a parents-unknown frontier directly. Coverage is commune-by-commune and runs from the French period into the 1930s for Oostende, Stene, Bredene, Oudenburg, Brugge. Each hit has a Detail view giving both spouses' birth date and place, residence, profession, civil status, the parents' professions and death dates, remarks, legitimated children and a FamilySearch film+image link to the act itself.
- **Yielded:** The Devriendt × Schalandryn marriage, Oostende 10 Nov 1906 act nr. 258 — naming all four parents, and pointing at FamilySearch film 004166040 image 173 where the act image was then read. Also the Schalandryn line back to Oudenburg 1836 and nine Devriendt sibling marriages. ALSO (2026-07-27): Emma Celesta Vincke's own marriage — Oostende, 28 September 1907, act nr. 212, RAB ID 668717, FamilySearch film 004166052 image i=138 — naming her parents Vincke Lucien Julianus × Vanalderweireldt Ludovica Maria, independent corroboration of the Diksmuide birth-index parent link (different commune, register and volunteer batch). The same query surfaced five of Eduardus Van Iseghem × Emma Celesta Vincke's children marrying in turn, each act naming both parents identically: Flavie Eulalie (Stene, 22 May 1920, act nr. 21), Eduardus (Oostende, 15 Jan 1927, act nr. 10), Joannes (Stene, 24 Mar 1928, act nr. 6 — his own marriage to Adrienne Devriendt, previously undated in this tree), Valentina Juliette (Stene, 14 Mar 1931, act nr. 7) and Maria Florentina Herminia (Stene, 17 Aug 1935, act nr. 21). ALSO (2026-07-27): the target act for the Janssen-Huyghebaert wall — Oostende, 28 Aug 1851, act nr. 090, RAB ID 574198, microfilm 1358587, FS waypoint QZ9J-PQZ — naming BOTH spouses' parents at once: JANSSEN Josephus Joannes s/o Joannes Janssen x Victoria Declerck, and HUYGHEBAERT Apollonia Johanna d/o Hubertus Huyghebaert x Johanna Derudder. The same surname sweep surfaced the parents' own marriages — Oostende 17 Nov 1819 (RAB 572117, Jean Janssen x Victoire Declerck, naming a further generation Jean Janssen x Karckman Catherine and Pierre Declerck x Josephe Pauwels) and Oudenburg 29 Apr 1821 nr. 24 (RAB 253572, Hubertus Franciscus Huyghebaert x Joanna Theresia Derudder, naming Ferdinandus Huyghebaert x Anna Theresia Termote and Pieter Josephus Derudder x Anna Maria Vandenbrande) — and a second marriage for the bride, not sought: Oostende 27 Oct 1868 act nr. 106 (RAB 580783), her remarriage as widow to Leopoldus Franciscus Pieren, whose "Previous Partners" table independently corroborates Josephus Janssen's death date and place, and whose Detail view also gives Hubertus Huyghebaert's own death (15/03/1857, Oudenburg) and Joanna Derudder still living in 1868 aged 76. Also the Huyghebaert siblings' marriages: Carolus Josephus × Goes (Oudenburg 8 Jun 1846 nr. 59, RAB 253852) and Augustinus Desiderius × Vantyghem (Zandvoorde 23 Nov 1859 nr. 62, RAB 361339). ALSO (2026-07-27): the Vanalderweireldt-Wyllie cluster at Diksmuide. The couple's OWN 1803 marriage — Diksmuide, 8 June 1803 (19 Prairial XI), act nr. 14, RAB ID 84989, microfilm 1166236 (data/artifacts/vanalderweireldt-wyllie-1803-marriage-diksmuide.md) — names antoine_vanald × brigitte_wyllie and all four of their parents at once; the groom's stated birth (09/05/1780) matches this tree exactly, the bride's (22/10/1779) does not, see brigitte_wyllie. A SECOND MARRIAGE for the bride, not sought: Diksmuide, 25 June 1818, act nr. 82, RAB ID 85255, microfilm 1166237 (data/artifacts/looten-wyllie-1818-marriage-diksmuide.md) — LOOTEN François Joseph × WYLLIE Brigitte Josephine Jeanne, weduwe — identified not by the name but by its own "Previous Partners" table naming VANALDERWEIRELDT Antoine, d. Diksmuide 06/07/1808. Two more of the couple's sons' own acts: petrus_vanald × Bouckaert Marie Theresia, Diksmuide 20 April 1828, act nr. 76, RAB ID 85443; and carolus_vanald's own 1828 act, Diksmuide 4 June 1828, act nr. 106, RAB ID 85449 — both restating Antonius × Brigitta Wyllie as parents. SPELLING TRAP, seen twice in one day: both 1828 acts write the surname VANALDEWEIRELDT — no R after -ALD- — so naam=Vanalderweireldt alone never returns them; they surfaced only via the mother's and brides' surnames.
- **Confidence:** sup
- **Accessed:** 2026-07-26
- **Note:** HOW TO QUERY IT WITHOUT A BROWSER. The surname search is a POST to /en/node/148 with a single field 'naam'. Each result row carries a hidden form (Gemeente, Jaar, ID); the Detail view is a GET to /en/node/172 with naam+Gemeente+Jaar+ID. SPELLING IS THE WHOLE GAME: 'Schalandrijn' returns 8 rows and 'Schalandryn' returns 44, and they are different families in different communes. Always run both -ijn and -yn. Also: the English column headers are mislabelled — the header reads 'Mother of the Groom' twice — but the Detail view labels them correctly as 'Given name Father Groom' and 'Given Name Father Bride'. And the transcription is not error-free: this index gives Ludovicus Franciscus Schalandryn's birth as 1822 where the birth index and his memorial card both say 1842. The 1928 Joannes × Adrienne act separately names the bride's parents as Devriendt Eugenius Alphonsius × Schalandryn Octavia Maria, matching this tree's already-doc eugenius_dv × octavia_schal (S20) exactly — corroboration of an already-fully-linked couple, not a new tree collapse. SPELLING TRAP CONFIRMED A SECOND TIME (2026-07-27): the Vanalderweireldt-Wyllie cluster's own acts write the surname VANALDEWEIRELDT (no R after -ALD-) at least twice (Carolus's and Petrus Antonius's 1828 marriages) — the same shape as the Vincke-family VANDERWEIRELT drop noted the same day on rab-bs-overlijdens. Always run every spelling variant, not just the one the tree already holds. ALSO (2026-07-27): joannes_vi2 x hermanie_janssen's OWN 1872 marriage act, Oostende act nr. 93 (RAB ID 582203, microfilm 4794599), names all four parents at once — VANISEGHEM Joannes Josephus x GAUTIERT Anna Maria, JANSSEN Josephus Joannes x HUYGHEBAERT Appolonia Joanna — corroborating joannes_jos_vi, anna_gautiert and josephus_janssen's held death dates a second and third time over. Four of this couple's children's own marriage acts also surfaced: arthur_vi x Schellynck Elodia Joanna (Oostende 1901 nr. 147, ID 666102), his own remarriage to Debbaut Judith Maria (Oostende 1936 nr. 40, ID 711795, Previous Partners table naming the 1901 bride — the same man, not a ninth child), and joannes_vi91 x Coenye Bertha Martha (Oostende 1911 nr. 293, ID 666909). A province-wide scan for the two remaining children, leontius_vi and gustavus_vi, found neither marrying anywhere in the transcribed window, and the same scan found no unrecorded DAUGHTER of this couple marrying either — though see rab-bs-overlijdens for why that negative cannot be read as a complete enumeration.

#### `rab-bs-geboorten` — West-Vlaamse Burgerlijke Stand — Geboorten (birth index), Rijksarchief Brugge/Kortrijk volunteers
- **Kind:** collection · <https://www.vrijwilligersrab.be/en/Civil_Status_Births_Index>
- **Covers:** The same volunteers' index of West-Flemish civil BIRTH acts, searchable on the surname of the child OR of either parent — so one query on a couple's surname returns their whole sibship. Columns: birth date, certificate date, act number, child, father, mother, remarks, plus a FamilySearch ark link to the register image.
- **Yielded:** Octavia Maria Schalandryn's Bredene birth registration, act nr. 116, certificate dated 2 May 1886, father Ludovicus Schalandryn, mother Mathilda Standaert — and with it seven siblings and the four Stene births of her own children. ALSO (2026-07-27): a province-wide sweep on 'Vincke' returned 173 Diksmuide rows, of which SEVEN name Lucien Julianus Vincke × Ludovica Maria Vanalderweireldt in full as parents — Charles Louis (30 Dec 1871, act nr. 277), Romanie Elodie (7 Oct 1873, act nr. 206 — this one row spells the father 'Lucien Julien'), Irma Maria (1 Nov 1874, act nr. 236), Camilla Celina (20 Apr 1876, act nr. 84), Eugène Lucien (23 Jul 1877, act nr. 169), Emma Celesta (23 Jan 1880, act nr. 14 — already held) and Jerome Maurice (22 Sep 1886, act nr. 167). Filtering separately by father-forename and by mother-surname returned the identical seven rows: no rival couple. Diksmuide 1866-1870 is a blind window — those rows carry only the bare father surname VINCKE, no forename and no mother at all — so Florence Amelie Vincke's own birth row (1869, act nr. 87) does NOT name her parents; her parentage instead rests on her 1893 marriage act (agatha-diksmuide-1893-marriage-bocklandt-vincke). ALSO (2026-07-27): the Janssen-Huyghebaert sibships. Josephus Janssen's own birth (Oostende, act nr. 303, 11 Aug 1820, RAB ID 623503, FS waypoint QZ9J-P7S) independently corroborates his 1851 marriage act's parents — a different register and RAB ID, checked against the duplicate-id trap. Three siblings: Petrus Jacobus (24 Nov 1822, nr. 392, RAB 624473), Hermanus Edouardus (14 Aug 1825, nr. 223, RAB 625496), Clementia Joanna (30 Mar 1832, RAB 1458577, no act nr transcribed). Hermanie Janssen's own birth (Oostende, act nr. 238, 5 Jul 1853, RAB ID 1458582) confirms her parents Josephus Janssen × Appolonia Huyghebaert, and the same sweep gives all ten of their children: Pharaildis Maria (6 Apr 1852, nr. 127, RAB 1458590), Hermania Ludovica (5 Jul 1853, nr. 238, RAB 1458582), Augustus Albertus (4 Dec 1855, nr. 472, RAB 1458574), Paulus Josephus (17 Sep 1857, nr. 417, RAB 1458589), Maria Ludovica Leonarda (26 Dec 1858, nr. 531, RAB 1458587), Victorina Francisca (21 Feb 1860, nr. 93, RAB 1458594), Florentina Maria (24 Apr 1861, nr. 158, RAB 1458578), Carolus Franciscus (13 Jun 1862, nr. 228, RAB 1458575), Seraphinus Augustus (14 Sep 1864, nr. 394, RAB 1458592) and Josephus Amandus (11 Aug 1866, nr. 348, RAB 1458584 — posthumous, born 16 days after the father's death). On the Huyghebaert side, Appolonia's own birth act was NOT found (see the miss logged against her), but her nine siblings were: Carolus Josephus (13 Mar 1822, nr. 11, and again 1 Feb 1823 nr. 12 — the name reused), Augustinus Desiderius (12 May 1824, nr. 34), Adelia Juliana (13 Jul 1826, nr. 54), Petrus Ferdinandus (5 Aug 1827, nr. 63), Adelaide Rosalie (4 Mar 1829, nr. 24), Marie Louise (4 Mar 1832, nr. 20), Magdalena Ludovica (21 Jun 1834, nr. 57) and Petrus Paulus (19 Feb 1837, nr. 22) — the last two bracketing dates the ones that show the gap at her own birth slot is an untranscribed batch, not a contradiction. ALSO (2026-07-27): Diksmuide births 1796-1815 are a SECOND, earlier blind window of the same shape as 1866-1870 above — rows for the Vanalderweireldt family (e.g. VANALDERWEIRELDT Charles, cert 12/03/1808) carry a bare father surname, no forename and no mother at all, so antoine_vanald × brigitte_wyllie's sibship cannot be fixed from the birth side; see antoine_vanald and carolus_vanald, whose own marriage acts resolve it instead. ALSO (2026-07-27): all EIGHT Oostende birth rows of joannes_vi2 x hermanie_janssen — arthur_vi (17/03/1874, nr 140, ID 1486295), augustus_vi (13/08/1875, nr 417, ID 1486298), leontius_vi (registered nr 541, ID 2042291, Birth Date column EMPTY, Certificate Date only 24/10/1876), gustavus_vi (05/01/1878, nr 13, ID 1486318), eduardus_vi (29/11/1880, nr 763, ID 1486308, already held but newly citing this row for birth.place), joannes_vi83 (21/03/1883, nr 232, ID 1486324), ludovicus_vi (20/02/1888, nr 139, ID 1486336, mother spelled 'Hermina Ludovica' on this row) and joannes_vi91 (16/05/1891, nr 415, ID 1486325). Filtering separately by father-name and by mother-surname (Janssen) returns the identical eight RAB IDs — no ninth child, no rival couple. IDENTIFYING THIS SIBSHIP AT ALL REQUIRED THE PARENT PAIR, NOT THE FATHER'S NAME: a province-wide group-by-mother found at least nine different men recorded identically as 'Joannes Vaniseghem'. SPELLING TEST (2026-07-27): 'Vaniseghem' returned the same 1568 rows as 'Van Iseghem' (byte counts differ only by the echoed search string — the two-file diff itself was NOT preserved, so this is unconfirmed rather than verified byte-for-byte); 'Van Yseghem' is a genuinely different key (25 rows, none this family); 'Vaniseghen' returns zero.
- **Confidence:** sup
- **Accessed:** 2026-07-26
- **Note:** READ THE TWO DATE COLUMNS APART. 'Birth Date' and 'Certificate Date' are separate columns and many rows fill only the second. A row showing one date is showing the DECLARATION date, not the birth — Octavia Schalandryn's row is blank in Birth Date and 02/05/1886 in Certificate Date, while the 1906 marriage act says she was born 30 April. Four of her siblings show the same one-to-two-day offset against their own marriage acts. Treating the single date as a birth date is how 1886-05-02 got into this tree. Query shape as for the marriage index: POST /en/node/114 with 'naam', detail GET /en/node/160. STRUCTURAL LIMIT ON INDEPENDENCE (2026-07-27): a Geboorten row's hidden ID is AGATHA's own act id — Emma Celesta Vincke's row carries ID=1583386, identical to AGATHA act GEWVL_GEBWVL_01583386 — so a Geboorten row and the matching AGATHA analysis are the SAME Rijksarchief volunteer transcription seen twice, not two independent sources, though the Geboorten row does add a direct FamilySearch image ark that the AGATHA page itself does not expose. The Huwelijken index (rab-bs-huwelijken) does not share this problem: a marriage act is a different register entirely.

#### `rab-bs-overlijdens` — West-Vlaamse Burgerlijke Stand — Overlijdens (death index), Rijksarchief Brugge/Kortrijk volunteers
- **Kind:** collection · <https://www.vrijwilligersrab.be/en/Civil_Status_Deceased_Index>
- **Covers:** The same volunteers' index of West-Flemish civil DEATH acts, searchable by the deceased's surname, and carrying both parents' names — which reaches children who died before ever marrying and so never appear in a marriage-act route at all.
- **Yielded:** Six Diksmuide death acts naming Lucien Julianus Vincke x Ludovica Maria Vanalderweireldt as parents: two resolve blind-window births (Carolus Ludovicus, d. 1871; Bellarmin Eugenius, d. 1872) and four give death dates for children the tree already held without one (Irma Maria, Camilla Celina, Jerome Maurice, Eugeen Lucien). A second, independent corroboration of Theophile Henri Vincke (d. Oostende 1922). One name EXCLUDED outright: Medardus Edmondus Vincke (d. 1866) is an illegitimate child of a different Vincke woman, not this couple's. A separate sweep for the five remaining blind-window forenames (Emil/Fidel, Gustav/Gustaaf, Florida, Arthur, Cyriel) returned nothing tying to this couple. ALSO (2026-07-27): the Vanalderweireldt-Wyllie cluster, one generation up. antoine_vanald's own death, Diksmuide act nr. 97, RAB ID 2299984, microfilm 4794755 (data/artifacts/vanalderweireldt-antoine-1808-death-diksmuide.md) — Age 28, Place of Birth Diksmuide, Father VANALDEWEIRELDT François, Mother VERHAEGHE Isabelle, Partner WYLLIE Brigitte, Certificate Date 21/07/1808 with the Date column BLANK. THREE more Diksmuide death acts on the same parent pair: jean_vanald, a third son who died in infancy (act 31, cert 30/01/1805, RAB ID 2300267); petrus_vanald's own death (act 4, cert 07/01/1869, RAB ID 2292938); and carolus_vanald's own death (act 230, cert 16/08/1853, RAB ID 2295013) — a fifth act naming the same couple. ONE probable sibling, not linked: Maria Joanna Vanalderweireldt, act 211, cert 30/09/1857, RAB ID 2294441, aged 82y 8m 28d, parents Jacobus Ignatius Vanalderweireldt × Isabella Clara Verhaeghe — a third rendering of the father's forename, agreeing with neither of the other two. brigitte_wyllie's OWN death, act nr. 198, RAB ID 2298609, Certificate Date 10/11/1824, Date column also blank — but corroborated, not contradicted, by both her sons' 1828 marriage acts stating 08/11/1824: a two-day registration lag, not a conflict. Her own parents' deaths, one index row each and none linked: DEMAN Catherine Bregite, act 48, cert 01/01/1801, daughter of Jean Deman × Marie Jeanne D'Hondt; WYLLIE Francois Antoine, act 175, cert 02/10/1811, son of Pierre Jacques Wyllie × Marie Barbe Lengs, remarried Colette Prudence Minne in 1807. ALSO (2026-07-27), the joannes_vi2 x hermanie_janssen family: joannes_vi2's OWN death (Stene, act nr 40, ID 2184011) — Birth Date 25/09/1852 Oostende, parents restated, widower of Hermania Ludovica Janssen, comparants VANISEGHEM Eduard (50, zoon) and VANISEGHEM Joannes (30, kleinzoon) stating the three-generation chain in the act's own words. hermanie_janssen's OWN death (Oostende, act nr 611, ID 2201502) — Birth Date 05/07/1853, partner VANISEGHEM Joannes, both parents restated. FIVE child deaths: augustus_vi (d. 04/01/1876, act 6, ID 263907, age 4mo22d, arithmetically exact against his birth act); TWO unnamed infants ('Sn', no forename) — 18/11/1878 act 626 ID 264403 (Sex M, no age given) and 06/11/1879 act 570 ID 266409 (Detail blank) — neither matches any birth row, and the hypothesis that the first is gustavus_vi dying at ten months was tested and rejected (every other named child of this couple who died appears in this index under their own name); joannes_vi83 (d. 04/09/1883, act 429, ID 267970, Detail Birth Date 21/03/1883 exact match); ludovicus_vi (d. 16/06/1889, act 788, ID 485530, ongehuwd, Detail Birth Date 20/02/1888 exact match). Cross-filtering by hermanie_janssen's own surname returns the identical five child-death rows. A province-wide scan for leontius_vi and gustavus_vi found neither in this index under any tried name-form. Also camillusgustavus_vi05's OWN death (Oostende, act nr 810, ID 500127, d. 29/11/1905, Sex M, Detail Birth Date 25/04/1905 exact match, mother spelled 'Vincke Emma Coleta', both parents 'Ongehuwd' aged 25) — corrects an earlier mis-framing that called him 'a sixth child not in the tree'; he was already held, only his death was new. And an unfetched row for joannes_vi x adrienne_dv's family: 'VAN ISEGHEM Roger Bernard', Stene, d. 27/02/1929, act 10, ID 2148819 — index row only, no Detail, not grafted.
- **Confidence:** sup
- **Accessed:** 2026-07-27
- **Note:** Query shape as the other two vrijwilligersrab indexes: POST /en/node/164 with 'naam'. The Diksmuide subset runs continuously 1798-1910, so a name absent from it there is absent from the transcription, not necessarily from life — death after 1910, elsewhere in the province, or under an unmatched name-form are the three untested alternatives, all stated as such rather than as a closed wall. READ THE TWO DATE COLUMNS APART HERE TOO (2026-07-27): this index carries the same Date-vs-Certificate-Date conflation already documented on rab-bs-geboorten's note — a re-query of the death rows first proposed 26/04/1875 for Irma Maria Vincke and 14/01/1889 for Jerome Maurice Vincke and 27/03/1900 for Albert Joseph Vincke, each one day later than the true Date column (25/04/1875, 13/01/1889, 26/03/1900 respectively); Camilla Celina (10/12/1876) and Eugène Lucien (04/04/1902) show no such offset, both columns agreeing. Read the Date column, not the Certificate Date, exactly as for the births index. THE DATE COLUMN CAN BE ENTIRELY BLANK (2026-07-27), not just later than the Certificate Date. antoine_vanald's row has no value at all in Date, only 21/07/1808 in Certificate Date, so there is no second column to offset it by a day or two the way the Vincke rows above can be. Never read a lone Certificate-Date value as the day itself; state it as a registration date and look for a second act — a child's own marriage or death act restating the parent's decease — to find the true day, exactly as brigitte_wyllie's case settles it and antoine_vanald's does not. THE 'Sn' CODE (2026-07-27): the venue's own Vocabularium does not define it. Read off the corpus itself, the codes compound ('VANISEGHEM Sn Vr', 'DEVLOO Sn Ml') — Sn is a NAME-POSITION code (registered without a forename), not a sex marker; Ml/Vr (manlijk/vrouwelijk) carry sex separately. Of 71 such rows scanned across the Van Iseghem and Janssen result sets, only 33 reproduce on a second read; not one of the 33 names a Partner, and most name both parents — the signature of a newborn, never an adult. THE DEATH DETAIL FORM HAS NO 'STILLBORN' FIELD AT ALL (only the birth form does) — record an 'Sn' row as 'unnamed child', never 'stillborn'; that distinction needs the register image.

### The family itself

#### `cosette-testimony` — Family testimony — Cosette De Keyser
- **Kind:** record
- **Yielded:** Jerome Dekeyser ❦ Léonie Paelinck are Roland's grandparents, which ruled out the earlier Gustaaf Audomarus reading and corrected the whole branch.
- **Confidence:** fam

#### `marcel-memorial-card` — Marcel Bundervoet's memorial card (Uitvaartcentrum Raes, Oostende)
- **Kind:** record
- **Yielded:** Marcel Henri Bundervoet's full name, and the Bostyn family naming that pointed to his mother Elodia Bostyn.
- **Confidence:** fam
- **Note:** Confidence corrected doc -> fam in the §52 sweep: the card is a physical family document and nobody in this project has read it. It backs no record — marcel_b cites the generic family site and is already sup.

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

#### `S17` — Memorial-card record — Louisa-Maria Bocklandt, d. Oostende 15 July 1946
- **Kind:** record · <https://www.openarchieven.nl/fwk:93d18189-14c6-9fd3-05d3-26142749d8b9>
- **Collection:** Familiekunde Vlaanderen regio Westkust, bidprentjes/rouwbrieven
- **Yielded:** Her exact death date — 15 July 1946 at Oostende, where the tree had only the year — her birthplace Hamme, and a SECOND HUSBAND: the card names her partner as Petrus Blomme, not Edouard Dekeyser. She had divorced Edouard around 1923 and evidently remarried.
- **Confidence:** sup
- **Accessed:** 2026-07-26

#### `S18` — Marriage act — Alphonsus Van Bogaert × Rosalia Moerloos, Sint-Niklaas, 7 April 1909
- **Kind:** record · <https://www.openarchieven.nl/abt:78f3eb53-a706-9e24-4a46-4203498072a3>
- **Collection:** Burgerlijke stand Sint-Niklaas, huwelijken 1909 (via Open Archives)
- **Yielded:** Confirms Carolus Ludovicus Van Bogaert x Maria Ludovica Martinet as a couple from a civil act — they are named as the bridegroom's parents — and reveals a son, Alphonsus Van Bogaert, who is a brother of Maria Magdalena and not in the tree. The bride's parents are given as Vitalis Moerloos x Nathalia Van Acker.
- **Confidence:** sup
- **Accessed:** 2026-07-26

#### `S32` — Civil birth acts naming both parents, for couples already in the tree (harvested corpus, July 2026)
- **Kind:** index · <https://www.openarchieven.nl/>
- **Collection:** Rijksarchief België, burgerlijke stand — Sint-Stevens-Woluwe, Zaventem and Bertem birth registers, via Open Archives
- **Covers:** The batch surfaced by `research.py children` over the harvested corpus: acts that name a child of a couple this tree already holds. Each person's own record carries the individual act URL.
- **Yielded:** 27 children across five couples — 9 Coppens, 4 Coenraets, 4 Pardon, 8 Van den Bemden, 2 Coekelberghs. Every one from an act naming both parents.
- **Confidence:** sup
- **Accessed:** 2026-07-26
- **Note:** Indexed acts, no register image read for any of them. The harvested mention carries a relation role but NO sex, which is why none of these records states one.

#### `kraainem-1897-marriage-vandenbemden-coenraets` — Marriage act — Felix Van den Bemden × Amelia Coenraets, Kraainem, 8 February 1897
- **Kind:** record · <https://www.openarchieven.nl/abl:c122cfac-929f-f4a8-ff56-704f485d6171>
- **Collection:** Burgerlijke stand — Huwelijksakten — Provincie Vlaams-Brabant en Brussels Hoofdstedelijk Gewest, Kraainem 1897, akte nr. 1
- **Yielded:** A second, independent naming of Felix Van den Bemden's birth (10/09/1876, Sint-Stevens-Woluwe) and his parents hendrik_vdb and coekelberghs, repeating the father's death date and place exactly (Kraainem, 12/08/1889). Names the bride, Amelia Coenraets (b. Kraainem 23/04/1876), daughter of Franciscus Coenraets and Anna Maria Deridder, and gives Felix's occupation, schaliedekker.
- **Confidence:** sup
- **Accessed:** 2026-07-26
- **Note:** An Open Archives / Demogen transcription (project huvlb19b), not the register image.

#### `kraainem-1900-marriage-vandenbemden-feyaerts` — Marriage act — Joannes (Jan) Vandenbemden × Elisabeth Leonia Feyaerts, Kraainem, 17 September 1900
- **Kind:** record · <https://www.openarchieven.nl/abl:4c6b4500-15c3-889f-9fda-ffb9021b817c>
- **Collection:** Burgerlijke stand — Huwelijksakten — Provincie Vlaams-Brabant en Brussels Hoofdstedelijk Gewest, Kraainem 1900, akte nr. 14
- **Yielded:** A second, independent naming of Jan Vandenbemden's birth (09/08/1880, Sint-Stevens-Woluwe) and his parents hendrik_vdb and coekelberghs, repeating the father's death date and place exactly (Kraainem, 12/08/1889). Names the bride, Elisabeth Leonia Feyaerts (b. Sint-Stevens-Woluwe 06/10/1878), daughter of the late Carolus Feyaerts (d. Kraainem 19/06/1884) and Petronilla Philomena Decoster, and gives Jan's occupation, fabriekwerker.
- **Confidence:** sup
- **Accessed:** 2026-07-26
- **Note:** An Open Archives / Demogen transcription (project huvlb19b), not the register image.

#### `zaventem-pardon-children-marriages-1877-1886` — Three Zaventem marriage acts of Franciscus Pardon's children, 1877–1886 — the batch that gives his death
- **Kind:** record · <https://www.openarchieven.nl/abl:13b0fac9-fbe1-1339-1809-bc419755b0e8>
- **Collection:** Burgerlijke stand — Huwelijksakten — Provincie Vlaams-Brabant en Brussels Hoofdstedelijk Gewest, Zaventem: 1877 akte 4, 1881 akte 10, 1886 akte 13
- **Yielded:** Joanna Coleta Pardon x Jan Meert (Zaventem 29/01/1877, abl:13b0fac9), Henricus Pardon x Joanna Rosina Magits (Zaventem 18/07/1881, abl:e23d9b8b) and Maria Thérèsia Pardon x Joseph Reniers (Zaventem 15/11/1886, abl:5f0f9b9e) each independently name their father as 'Frans/Franciscus/Jan Frans Pardon, deceased Zaventem 18/07/1874' and their mother as Anna Maria Bossin — three acts, three dates, one death fact this tree did not previously hold. Each also repeats the child's own birth date and place exactly, and names an until-then-unrecorded spouse (Magits, Meert, Reniers).
- **Confidence:** sup
- **Accessed:** 2026-07-26
- **Note:** Open Archives / Demogen transcriptions (project huvlb19b), not the register images. Two of the three (1877, 1886) carry a FamilySearch scan link in the underlying harvested record (SourceAvailableScans) not yet read here.

#### `S33` — Civil registration acts for the Bossin family of Sint-Stevens-Woluwe, Kraainem and Zaventem (harvested corpus, July 2026)
- **Kind:** index · <https://www.openarchieven.nl/>
- **Collection:** Rijksarchief België, burgerlijke stand — Sint-Stevens-Woluwe, Kraainem and Zaventem birth and marriage registers, via Open Archives
- **Covers:** A second pass over the already-harvested corpus, no new fetch: acts naming children, marriages and corroborating events for two Bossin couples already in the tree.
- **Yielded:** Karel Joseph Bossin (SSW nr.7, 27 Feb 1901), son of ludovicus_bossin79 x misabella_t. A second, distinct Joannes Baptista Bossin (SSW nr.19, 15 Aug 1851), a fourth child of guilielmus_bossin x peremans. A day-level birth act for ludovica_bossin (SSW nr.18, 5 Oct 1853), superseding the declaration-date reading held from S24. The marriage act of jbbossin x maria_wolf (SSW nr.4, 17 June 1858) — the anchor that supplies both spouses' exact birthdates for the first time and names jbbossin's own parents, Judocus Bossin x Maria Desmedt, a generation this tree did not have. Five further children of jbbossin x maria_wolf: Joannes Philippus (1857, SSW nr.15), Philippus Amandus (1859, SSW nr.9), Jan Philip (1876, SSW nr.8), Frans (1882, SSW nr.36) and Guillielmus Josef (1869, Kraainem, known only from his own 1896 Zaventem marriage act). Three later marriage acts — Jan Philip's 1897 SSW marriage, Joannes Philippus's 1907 SSW marriage, and Guillielmus Josef's own 1896 marriage — each independently restate the father's death (Sint-Stevens-Woluwe, 19 March 1887) or the mother's exact age against her 1836 birthdate. Ludovicus Bossin's own 1879 SSW birth act (nr.40) corroborates both his parents' ages. Misabella_t's own 1880 SSW birth act corroborates georges_cj x bossin, with the family surname spelled 'Thomas' rather than 'Thumas'.
- **Confidence:** sup
- **Accessed:** 2026-07-27
- **Note:** Indexed acts (AGATHA/Demogen transcriptions via Open Archives), no register image read for any of them. Each person's own record carries the individual act URL; the identifier-by-identifier reasoning for every match is in research/labels.jsonl.

#### `S34` — Marriage act — Joannes Baptista Peremans x Joanna Catharina Van Gindertaelen, Zaventem, 21 August 1848
- **Kind:** record · <https://agatha.arch.be/nl/data/acts/HUVLB_HUBRA_00011074_0>
- **Collection:** Burgerlijke stand — Huwelijksakten — Provincie Vlaams-Brabant en Brussels Hoofdstedelijk Gewest, Zaventem 1848, akte nr. 7 (harvested corpus, abl:22d86c23-2e3f-64fe-ca52-272ae9a71c04)
- **Covers:** Indexed marriage registration (Demogen project huvlb19a), no register image read. A FamilySearch scan exists (ark:/61903/3:1:S3HY-6423-8F1?i=24) but is behind a login wall — confirmed blocked, a one-request retry, not a scoped miss.
- **Yielded:** A fifth sibling for Joanna Catharina Jacoba Peremans — Joannes Baptista, 28, arbeider, married Joanna Catharina Van Gindertaelen, 23, arbeidster, both of Zaventem, neither able to write. Her parents Joannes Franciscus Van Gindertaelen x Anna Catharina Huenaerts, both arbeider(ster) of Zaventem, present and consenting. Also gives Egidius Peremans's own death as 1836-03-06, one year off the 1837-03-06 already held from S19 — left open, not resolved. Four witnesses: Cornelius Peremans (33) and Athanasius Peremans (26), both already-held siblings; Petrus Van Der Varen (35), a plausible but unconfirmed match for mjosephina_peremans's husband Petrus van der Varent; Franciscus Engels (38), veldwachter, a recurring professional witness and not kin.
- **Confidence:** sup
- **Accessed:** 2026-07-27
- **Note:** Index-level AGATHA/Demogen act analysis, no register image read — sup throughout, never doc. The exact day-level match this act gives on Joanna Theresia Verelst's already-held death date (1843-12-19 Zaventem, from the separately transcribed S19) is what anchors the parent link; it is a stronger identifier than the parent-name-plus-volume-title anchoring used for cornelius_peremans, jathanasius_peremans and mjosephina_peremans.

#### `S35` — Civil marriage acts for the Bossin/Swaelens/Vrebos family of Kraainem, 1884-1901 (harvested corpus, July 2026)
- **Kind:** index · <https://www.openarchieven.nl/>
- **Collection:** Rijksarchief België, burgerlijke stand — Kraainem and Werchter marriage registers, via Open Archives (abl:52c530f8-d6df-89a9-31ab-f9cb0ca019fc, abl:1ef28af4-4ec3-50f6-242d-4bec296c0051, abl:74a573c0-0ddb-9ba9-65e4-d642c39bcf6c, abl:d449cf68-4ea6-0242-2dce-78427c4b8f63)
- **Covers:** Four marriage acts already held in the local corpus, read in full for a downward sweep of guilielmus_bossin x peremans's children: Joannes Baptista Julianus Swaelens x Ludovica Bossin (Kraainem, 25 Feb 1884), Henricus Bossin x Maria Catharina Guns (Kraainem, 23 Nov 1887), Petrus Vrebos x Ludovica Bossin, her remarriage (Kraainem, 30 May 1901), and Joannes Franciscus Bossin x Maria Catharina Verstraeten (Werchter, 18 Jan 1896). No new fetch; no register image read for any of the four.
- **Yielded:** swaelens's own birth (1858-05-11 Alsemberg), trade and parents (egidius_swaelens x joanna_ackermans, her death 1877-12-27 Alsemberg); a fifth child of guilielmus_bossin x peremans, henricus_bossin (b. 1863-01-01 Kraainem), and his wife guns_mc with her parents guns_jf x vogels_a; a sixth, probable child, joannes_franciscus_bossin (b. 1866-03-17 Kraainem), and his wife verstraeten_mc with her parents verstraeten_l x torfs_r; ludovica_bossin's previously-unknown remarriage to petrus_vrebos, with his parents vrebos_hf x schoolmeesters_j; guilielmus_bossin's death sharpened from a bare year to a day (1888-10-10 Kraainem), corroborated identically in two of these four acts, five years apart. Also surfaced and left open: an eight-day, one-commune discrepancy between this corpus's 1884-02-25 Kraainem marriage date for swaelens x ludovica_bossin and the S24 declaration's 1884-02-17 Alsemberg; and a witness, Franciscus Swaelens (24, Sint-Genesius-Rode, schrijnwerker — the groom's own trade), NOT PROVEN as a relative and not grafted.
- **Confidence:** sup
- **Accessed:** 2026-07-27
- **Note:** Indexed acts (AGATHA/Demogen transcriptions via Open Archives), no register image read for any of them — sup throughout, never doc. AGATHA holds a scan for the 1884 act (HUBRA_00197982_0) but is logged out this pass: confirmed blocked, not a scoped miss. The identifier-by-identifier reasoning for every match is in research/labels.jsonl.

#### `fwk-alfons-vincke` — Memorial card — Alfons Luciaan Vincke, partner Eugenia Maria Vandecappelle
- **Kind:** record · <https://www.openarchieven.nl/fwk:bb261d5b-e241-84c8-0c3c-860a943cca23>
- **Yielded:** Alfons Luciaan Vincke, born Diksmuide 13 September 1865, partner Eugenia Maria Vandecappelle — corroborating the 1888 Diksmuide marriage act (rab-bs-huwelijken) from a source outside the vrijwilligersrab indexes.
- **Confidence:** sup
- **Accessed:** 2026-07-27

#### `fwk-eugenia-vandecappelle` — Memorial card — Eugenia Maria Vandecappelle, partner Alfons Luciaan Vincke
- **Kind:** record · <https://www.openarchieven.nl/fwk:f5704ac2-7b0f-1f02-6cfe-1829d47b9e7a>
- **Yielded:** Eugenia Maria Vandecappelle, partner Alfons Luciaan Vincke — the same couple as fwk-alfons-vincke, a second card rather than the same one counted twice.
- **Confidence:** sup
- **Accessed:** 2026-07-27

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

### Netradyle — dépouillement d'actes d'état civil et de registres paroissiaux (Cercle Historique de Perwez)

#### `netradyle-grez-mariages` — Netradyle — Grez-Doiceau, actes de mariage (tab_mari.php)
- **Kind:** collection · <http://www.netradyle.be/actes/tab_mari.php?args=Grez+[Brabant Wallon],THUMAS>
- **Covers:** The marriage table for Grez [Brabant Wallon], queried by surname. Detail pages give only the two spouses' names and the date — no parents, no ages, no act number.
- **Yielded:** Independent, second-index corroboration of Georges Joseph Thumas x Sophie Miranda Deridder's marriage (row 50, '08/10/1868 THUMAS Georges & DERRIDER Sophie'), against a one-day date conflict with S25 (7 vs 8 October) left open. Also surfaced the 1771 and 1799 Thumas marriages a generation above the documented line, and the 1839 Deridder x Lacourt marriage a generation above Sophie Miranda Deridder's candidate parents.
- **Confidence:** sup
- **Accessed:** 2026-07-27
- **Note:** See the netradyle site entry for how to query it without a browser. Marriage detail pages are the weaker of netradyle's two tables for this project: no parents, no ages, no trades, no act number, so a hit here can corroborate an event date but never itself supply or refute a parent link.

#### `netradyle-grez-naissances` — Netradyle — Grez-Doiceau, actes de naissance (tab_naiss.php)
- **Kind:** collection · <http://www.netradyle.be/actes/tab_naiss.php?args=Grez+[Brabant Wallon],THUMAS>
- **Covers:** The complete Thumas birth table for Grez [Brabant Wallon], 134 rows spanning 1730 to the 1890s, paged at 100 rows with no 'next' link (a single-page read looks complete and is wrong). Detail pages carry the father's forename and the mother's full name, but never an act number, age or trade.
- **Yielded:** A second reading of the Thumas generations around georges_cj, all index-level: Jean Baptiste Zenon Thumas's birth (19 Aug 1845, one day off S25's 20 August) with parents Georges x 'Jostens Marie Catherine', corroborating georges2_t x joostens; Georges Thumas's own 1804 birth (25 Jan, agreeing with the record) with a NEGATIVE finding that no Thumas birth is indexed at Grez 1783-1797 at all, weakening but not closing the 1793/94-vs-1804 age conflict from georges2_t's wife's 1857 death act; an unrecorded elder brother, Georges Etienne Thumas (b. 1802); Georges Carolus Josephus Thumas's own 1836 birth, matching date and both parents but indexed under the forename 'Gregoire' rather than 'Georges' — left ambiguous, not merged; Georges Lambert Thumas's 1772 birth, a new parent couple one generation above georgeslambert_t (Georges Thumas x Marie Catherine Noel, married 1771), with his own 1799 marriage conflicting by two years with the 1801 this tree holds from Geneanet; three disagreeing spellings of Marie Catherine Quinart's forename across three rows; Georges Joseph Thumas's OWN birth absent from the table despite four siblings being present, read as a coverage gap rather than a birthplace refutation; and a candidate, not a link, for Sophie Miranda Deridder (b. 1844, parents Isidore Deridder x Cordelie Victorine Lacourt) — one identifier only, her MIRANDA absent, and no way to tie her to the 1868 groom because netradyle's marriage pages carry no parents at all.
- **Confidence:** sup
- **Accessed:** 2026-07-27
- **Note:** See the netradyle site entry for how to query it without a browser. A 2006 volunteer deposit with visible transcription noise (Joustens/Jousten/Jostens, Kinart/Kinar, Derrider/Deridder) — sup throughout, never doc, and several rows here are recorded as AMBIGUOUS or CANDIDATE rather than grafted.
