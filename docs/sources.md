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
| `agatha` <https://agatha.arch.be/> | archive | login | name-index, image-read | 5 | Belgian civil and parish registers by commune and year, with scans. The primary route to 19th-century Belgian acts. |
| `search-arch` <https://search.arch.be/> | archive | offline | name-index, image-read | 1 | Scanned civil registers by commune and year; sibling portal to AGATHA. |
| `familysearch` <https://www.familysearch.org/> | index | login | name-index, image-read, full-text | 2 | Belgian civil and church registration, with act images. |
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
| `openarch` <https://www.openarchieven.nl/> | index | open | api, name-index | 6 | About 30 million Belgian person-mentions: the Familiekunde Vlaanderen and Doodsprentjes.be bidprentjes and rouwbrieven, the heemkring collections, and the Rijksarchief civil acts transcribed by the Demogen volunteers. Coverage is uneven by province — Vlaams-Brabant has indexed civil acts with full parent roles; Oostende and Evergem are overwhelmingly 20th-century memorial cards. |

**`agatha`** — Post-1900 Oostende civil registers are NOT here — they sit at the Stadsarchief Oostende. Go straight to commune + year + act number; 19th-c. acts are handwritten but formulaic, and the parents are named in the opening lines ('zoon/dochter van … en …').

**`search-arch`** — RETIRED. search.arch.be now redirects to an end-of-life notice and is replaced by agatha.arch.be. Act links in the harvested Open Archives corpus still point here, so they must be translated: a search.arch id like HUBRA_00221638_0 is HUVLB_HUBRA_00221638_0 on AGATHA, or the act can be found by searching name + commune + year.

**`familysearch`** — Deeper than AGATHA or Ancestry for Belgium — it broke the Dekeyser wall the other two could not. Try it before concluding an act is unindexed.

**`myheritage`** — Reached with an account (July 2026). The free/paid boundary matters for planning: SMART MATCHES against other members' trees are FREE to read — names, relationships and counts all visible — and that is where the value has been. RECORD MATCHES are not: the field values are replaced server-side with decoy strings behind a Data subscription, so only the collection name, the field list and the occasional year are free. Treat record matches as a TARGETING LIST — they say which document exists for whom, and Belgian civil acts can then be pulled free from AGATHA or FamilySearch.

**`stadsarchief-oostende`** — Holds both documents that would name Édouard Dekeyser's parents from Oostende's own registers: the 4 May 1901 marriage act and the 8 Sep 1951 death act. Death acts open after 50 years, so the 1951 one is public — the cleanest ask.

**`inmemoriam`** — Coverage gap: coastal and Brabant papers are thin, so a post-2000 coastal death may simply be absent.

**`jammart`** — Memorial cards name parents and children and sit outside the civil-registration publicity rules — the key to 20th-century walls. Match on place, never on surname alone.

**`family`** — The only key to the sealed 20th-century links. A direct descendant may also request a relative's birth, marriage or death certificate at any age — that is the decisive move on the Janssens wall, not more online searching.

**`openarch`** — The only venue in this registry with a free, unauthenticated API, so it is harvested rather than searched: tools/harvest.py pulls acts once and keeps them, and every frontier is then answered against the local corpus. Records carry structured roles — Vader, Moeder, Kind, Bruidegom, Bruid, Vader van de bruid — so a parent link is a field rather than prose, and each act links to its scan and to its search.arch.be page. Throttled to 4 requests a second; the harvester goes slower.

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
