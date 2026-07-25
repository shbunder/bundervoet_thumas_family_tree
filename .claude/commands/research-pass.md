---
description: Run one full research pass — choose a frontier, search, verify, record, build, commit.
argument-hint: "[optional: person id or line to work on]"
---

Run one complete research pass on the family tree. Target: $1 (if empty, let the
strategist choose).

The four roles exist so that no single agent both finds a match and decides it is
true. Keep them separate; that separation is the main defence against grafting the
wrong person, which is the failure mode this whole project is built around.

1. **Strategist** — launch the `strategist` subagent. It returns one frontier, the
   sites and pages to try in order, and what would count as proof. If a target was
   given above, tell it to work on that one and explain the best route.

2. **Searcher** — launch the `searcher` subagent with that plan. It runs the
   searches in the logged-in browser and logs every one, hit or miss. It returns
   candidates, never conclusions.

3. **Verifier** — launch the `verifier` subagent on each candidate. It tries to
   refute. Do not skip this even when a match looks obvious — especially then. Its
   verdicts are ACCEPT, REJECT or NOT PROVEN, and NOT PROVEN is the common one.

4. **Recorder** — launch the `recorder` subagent with the accepted findings and the
   stated confidence. It writes the person files, registers sources, adds the
   narrative section to `docs/research-log.md`, runs `node tools/build.mjs` and
   commits.

Then report back to me, briefly:

- what was found, and what it is grafted on — which two identifiers agreed;
- what was searched and came back empty, and whether it is worth retrying;
- anything the verifier rejected, and why;
- the next frontier.

If the browser is not running, say so and stop rather than falling back to
unauthenticated fetches — the archives that matter are all behind a session.

If a pass ends with nothing grafted, that is a normal outcome. A logged set of
negatives is worth more than a speculative link, and saying "this needs the
Stadsarchief" is a real result.
