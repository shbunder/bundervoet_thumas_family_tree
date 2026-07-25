# Verification log

One row per verification pass, newest at the bottom. This is an index into
[research-log.md](research-log.md) and the git history, not a second copy of either.

`bucket` is where `uv run tools/verify_all.py` had the person: CORROBORATED (a date or
place agrees, not only names), KIN-ONLY (names and a relative, nothing anchored), PARTIAL,
NOT REACHED (nothing held under that surname).

`verdict`: DOCUMENTED (act read) · CORROBORATED (index agrees, act unread) · LEAD ·
REJECTED · NOT FOUND · BLOCKED.

| pass | date | person | bucket | verdict | evidence | commit |
|------|------|--------|--------|---------|----------|--------|
| 1 | 2026-07-26 | leonie_p | CORROBORATED | NOT FOUND | AGATHA holds no Sint-Niklaas 1901 birth acts — 8 Paelinck records there, none ours. Stays `sup`. | — |
| 2 | 2026-07-26 | — (method) | — | — | Janssens: 121,923 mentions capped at 600 = 0.5% held. Queued 126 surname+commune harvests so common surnames are fetched where our people actually lived. | — |
