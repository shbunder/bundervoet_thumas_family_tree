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
