# Autopilot log

**This is the file to read after an unattended run.** One row per research pass, appended
by `/autopilot`. It is an index into [the research log](research-log.md) and the git
history — not a second copy of either — so every row stays on one line and the reasoning
stays where reasoning belongs.

- `dir` — **up** = whose parents are unknown (`research.py frontiers`),
  **down** = children of couples already held (`research.py children`).
- `verdict` — **GRAFTED** a link was made · **NOT PROVEN** plausible, insufficient, now a
  named frontier · **REJECTED** refuted · **BLOCKED** the material was never reached.
- `added` — the person ids created, or `—`.

Most passes end NOT PROVEN. That is the system working: the verifier defaults to rejecting
when unsure, because a missed link is found again next pass and a false link is invisible
forever. A run of ten passes producing two grafts and thirty logged misses is a good run —
the misses and the labels are the accumulating asset.

| pass | date | dir | frontier | verdict | added | commit |
|------|------|-----|----------|---------|-------|--------|
| 1 | 2026-07-26 | up | octavia_schal | GRAFTED | ludovicus_schal, mathilde_standaert, ludovicus_dv, silvia_brissinck | — |
| 2 | 2026-07-26 | down | anna_maria_bossin | GRAFTED | anna_maria_bossin, franciscus_pardon, guilielmus_pardon, maria_anna_pergijsels | — |
| 3 | 2026-07-26 | up | coekelberghs | GRAFTED | jb_coekelberghs, anna_haesaerts, jb_vandenbemden, elisabeth_langes, henricus_vanesch | — |
| 4 | 2026-07-26 | — | confidence sweep (all AGATHA sources) | CORRECTED | — | — |
| 5 | 2026-07-26 | up | jb_coekelberghs | GRAFTED | henricus_coekelberghs, petronella_elseviers, jb_haesaerts, elisabeth_vdbroeck | — |
| 6 | 2026-07-26 | down | hendrik_vdb + coekelberghs | GRAFTED | lodewijk_bemden73, victor_bemden74, adela_bemden84, amelia_coenraets76, elisabeth_feyaerts78 | — |
| 7 | 2026-07-26 | up | six bare-agatha citations | GRAFTED | angela_dk, josephus_blomme, mathilde_meseure, paulina_bocklandt, elodia_bocklandt, mathildis_bocklandt, caesar_bocklandt, philemondus_bocklandt, alphonsus_bocklandt, ludovicus_bocklandt | — |
| 8 | 2026-07-26 | down | commune harvest (5 communes) | NOT PROVEN | — | — |
| 9 | 2026-07-26 | up | ida_vermandel | GRAFTED | paulina_vdberghe, petrus_vermorgen | — |
| 10 | 2026-07-26 | down | commune-harvest yield | NOT PROVEN | — | — |
| 1 | 2026-07-27 | up | emma_vincke | GRAFTED | charles_vincke, romanie_vincke, irma_vincke, camilla_vincke, eugene_vincke, jerome_vincke, florence_vincke, flavie_vi, eduardus_vi2, valentina_vi, maria_vi, angela_gunst | — |
| 2 | 2026-07-27 | down | bossin children | GRAFTED | karel_bossin01, joannes_bossin51, jphilippus_bossin57, pamandus_bossin59, janphilip_bossin76, frans_bossin82, gjosef_bossin69, judocus_bossin, maria_desmedt, petronella_wolf | — |
| 3 | 2026-07-27 | act | thumas grez-doiceau 1868 | NOT PROVEN | — | — |
| 4 | 2026-07-27 | up | appolonia_huyghebaert | GRAFTED | joannes_janssen, victoria_declerck, hubertus_huyghebaert, joanna_derudder, leopoldus_pieren, carolus_huyghebaert22, carolus_huyghebaert23, augustinus_huyghebaert24, adelia_huyghebaert26, petrus_huyghebaert27, adelaide_huyghebaert29, marielouise_huyghebaert32, magdalena_huyghebaert34, petruspaulus_huyghebaert37, nn_goes, nn_vantyghem, petrus_janssen22, hermanus_janssen25, clementia_janssen32, pharaildis_janssen52, augustus_janssen55, paulus_janssen57, marialudovica_janssen58, victorina_janssen60, florentina_janssen61, carolus_janssen62, seraphinus_janssen64, amandus_janssen66 | — |
| 5 | 2026-07-27 | down | lucien_vincke 1866–1870 | GRAFTED | theophil_vincke, valerie_bolle, bellarmin_vincke, karolus_vincke, alfons_vincke, eugenia_vandecappelle, mariesophie_vincke, leopoldmaurice_vincke95, marielouise_vincke, madeleinemarie_vincke, leopoldmaurice_vincke00, eduardushieronymus_vincke, juliettegabrielle_vincke, georgesremi_vincke, karel_vincke, louisacamilla_vincke, camillecyrille_vincke, andrejerome_vincke, camillusgustavus_vi05, camillushenricus_vi11 | — |
| 6 | 2026-07-27 | act | zaventem 1848 peremans | GRAFTED | jbaptista_peremans, vangindertaelen_jc, vangindertaelen_jf, huenaerts_ac | — |
| 7 | 2026-07-27 | up | antoine_vanald + brigitte_wyllie | NOT PROVEN | francois_looten, petrus_vanald, jean_vanald, marietheresia_bouckaert, catharina_looten, renatus_looten, ludovica_looten, maria_looten | — |
| 8 | 2026-07-27 | down | joannes_vi2 sibship | GRAFTED | arthur_vi, augustus_vi, leontius_vi, gustavus_vi, joannes_vi83, ludovicus_vi, joannes_vi91 | — |

---

## Run summary — 2026-07-26, ten passes

**345 → 434 people.** Corpus **40,347 → 103,705 acts** (90 harvests → 194), including five
commune harvests. 26 commits. `research/searches.jsonl` 166 entries, `research/labels.jsonl`
48 labels — more than half written today.

**Caveat on the numbers: other Claude Code sessions were editing this repository throughout
the run.** Some commits in the range are theirs, and part of the growth above is theirs. The
passes below are this run's; §54's retraction was of another session's graft.

### Grafted, and the two independent identifiers that carried each

| pass | graft | identifier 1 | identifier 2 |
|---|---|---|---|
| 1 | `octavia_schal` + `eugenius_dv` parents — 4 people, **doc** | 1906 Oostende marriage act **image**: groom b. Steene 13 Apr 1882, to the day | Bredene birth act image: *"geboren eergisteren de dertigsten April"* |
| 2 | `anna_maria_bossin` + Pardon parents — 4 people, sup | parents named identically to her brother's 1846 act | her brother **Guilielmus Bossin, 29**, a witness at the wedding |
| 3 | `coekelberghs` + `hendrik_vdb` parents — 5 people, sup | marriage date 24 Apr 1873 | groom's birth, Everberg 19 Aug 1849, to the day |
| 5 | `jb_coekelberghs` + `anna_haesaerts` parents — 4 people, sup | 1838 Bertem marriage act **image**, spousal pair | father self-declaring aged 44 (1853) and 48 (1858), both consistent with b. Jul 1809 |
| 6 | 11 children of three couples, sup | each act's father b. **Everberg**, mother b. **Bertem** | every date inside the marriage-to-death window |
| 7 | `louise_bocklandt` restored to **doc**, + 10 people | 1924 Stene marriage act **image**: b. 31 Dec 1877 Hamme, to the day | the De Keyser marriage *and* divorce |
| 9 | `paulina_vdberghe` + `petrus_vermorgen`, **doc** | 1882 Hamme act **image** dates the mother's death 21 Jun 1865 Hamme | father's trade *metser*, matching two other acts |

Four act **images** were read (1838 Bertem, 1865 Hamme, 1882 Hamme, 1924 Stene), each by
stitching FamilySearch deep-zoom tiles on the `sg30p0` origin — the viewer does not work.

### Refuted, and by what

- **`appolonia_vandenbemd77` — deleted.** Her 1877 act names *Willem Edouard Vandenbemden ×
  Maria Anna Vandenhoven*, not this couple. A rival family, same surname, same commune.
- **`joannes_coekelberg58` — mother link removed.** The act says *Anna **Catharina***
  Haesaerts, the variant §51/§53 deliberately left unmerged.
- **Two Octavia Schalandryns**, first cousins, both dying in 1964 — separated by birthplace,
  birth year, death place and death date.
- **Two rival Van Bergens** (Aarschot 1923, Wuustwezel 1906) that the scorer would graft at
  28.6 and 23.7 bits — wrong province, wrong parents.
- **Two Stekelorum near-collisions** — a Jabbeke *Pieter* who survived Joanna Francisca
  Verplancke, and a Varsenare *Helena Deschacht* married to a *Joannes* Stekelorum.

### Corrected

- **Pass 4: 24 records went `doc` → `sup`.** Six AGATHA pages registered `doc` are act
  *analyses* with no scan. The site line changed from "reaches back to the 1640s on records
  read in the archive" to **the 1800s** — nine centuries of claimed documentary depth were an
  artefact of the confidence code. One source went the other way (`S16`).
- `octavia_schal` b. 1886-05-02 → **1886-04-30** (the first was the act date).
- `marie_vanbergen` born **Waasmunster**, not Hamme; `ida_vermandel` born **Zelzate**.
- Louise Bocklandt's divorce `~1923` → **1922-11-14**.
- Geneanet's "Agatha Langa" → **Elisabeth Agatha Langes**.

### Blocked — needs you

- **AGATHA is not logged in.** Act pages render by direct id, but images show *"Gelieve in te
  loggen"*. That is the one thing standing between `petrus_vannieuwenhuyse` and `doc`: his
  scan reference resolves to a real, specific volume (Oostkamp doopakten 1630–1652).
- **Geneanet `/fonds/` returns 403** unauthenticated, though Chrome is signed in to Geneanet
  — worth one manual visit.

### What the labels say about the scorer

Precision **80.0%**, recall **33.3%** over 33 re-scored labels. The two false positives are
both `marie_vanbergen`, both clearing 23 bits on *surname + birth-year ±1 + father's
forename* — that combination is nearly free on a common surname and wants a threshold look.
The recall figure partly measures the **labels**, not the code: several cite an act id where
an act names six people, so the scorer compares a woman against her husband. Labels using
the `…#Person1` form score correctly.

### The single most valuable thing to do next — and it needs you

**Make the queues read `research/labels.jsonl`.** All three remaining entries in
`research.py children` are decisions *this run already made*: a graft it retracted, a link it
declined, and a proposal that a man born 1847 is a child born 1901. The refutations are
recorded, with reasoning, and nothing reads them back. Left as it is, the next unattended run
re-grafts the wrong Appolonia — and the run after that.

It is a change to `tools/`, so this run did not make it. **Until it exists, every downward
queue entry must be checked against the labels by hand.**

Two more `tools/` findings, same reason: Open Archives' `records/search` **returns HTTP 400
past ~10,000 mentions** and the harvester then keeps *nothing*, so a large commune needs
slicing (Oostende is 262,554 — twenty-six ceilings deep); and `harvest.py place X --max 1`
caches a 100-mention stub that silently blocks the real harvest.

One change to `tools/` **was** made, by a subagent, before this constraint was enforced —
commit `3af3326`, a crash fix in `corpus.py` for archive dates like `"ca"` and `"-"` that
was killing the validator, with six cases pinned in a test. It is load-bearing for the rest
of the run. **It needs your review.**
