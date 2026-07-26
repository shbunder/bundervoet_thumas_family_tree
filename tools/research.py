#!/usr/bin/env python3
"""The research log: what was searched, where, and what came back — and, from the
records themselves, what to search next.

    uv run tools/research.py frontiers          what to work on next, ranked by value/cost
    uv run tools/research.py acts               which held acts answer the most frontiers
    uv run tools/research.py tried <person>     what was tried, what it found, why it failed
    uv run tools/research.py untried <person>   sites and pages not yet used on them
    uv run tools/research.py sources            the registry, sites then pages
    uv run tools/research.py yield              which sites and pages actually pay off
    uv run tools/research.py stale              misses a venue has since outgrown
    uv run tools/research.py components         disconnected families — objective 3
    uv run tools/research.py collapse           where the tree folds back on itself
    uv run tools/research.py report             where the effort has gone
    uv run tools/research.py log …              record a search
    uv run tools/research.py check              validate log + registry
    uv run tools/research.py docs               regenerate docs/sources.md
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from familytree import sources as reg  # noqa: E402
from familytree import store  # noqa: E402
from familytree.corpus import corpus_exists, load_corpus, load_manifest  # noqa: E402
from familytree.coverage import (  # noqa: E402
    act_coverage, greedy_cover, missing_children, pedigree_collapse, surname_clusters,
    tree_components,
)
from familytree.frontier import frontier_rows  # noqa: E402
from familytree.people import ROOT, family_key, load_artifacts, load_config, load_people  # noqa: E402

LOG_FIELDS = ("found", "why", "scope", "url", "artifact", "note")


def name_of(people, pid):
    return people[pid]["name"] if pid in people else pid


# ---------- commands ----------


def cmd_log(args):
    sites, pages = reg.load_sources()
    people = load_people()
    entry = {
        "date": args.date or dt.date.today().isoformat(),
        "person": args.person,
        "goal": args.goal,
        "site": args.site,
        "page": args.page,
        "basis": args.basis,
        "query": args.query,
        "result": args.result,
    }
    for field in LOG_FIELDS:
        value = getattr(args, field, None)
        if value:
            entry[field] = value

    # Registering a source is not paperwork — a venue searched but never registered is
    # one the next pass cannot know about, and `untried` silently under-reports. So an
    # unregistered source is refused here rather than caught later.
    if not reg.site_by_id(sites, entry["site"] or ""):
        raise SystemExit(
            f'error unknown site "{entry["site"]}". Register it in research/sources.json first — '
            "a venue searched but never registered is one the next pass cannot know about."
        )
    problems = reg.entry_problems(entry, "this search", sites, pages, people)
    if problems:
        for p in problems:
            print("error " + p.replace("this search: ", ""), file=sys.stderr)
        if any("basis" in p for p in problems):
            print("\n--basis is one of:", file=sys.stderr)
            for k, v in reg.BASIS.items():
                print(f"  {k:<12} {v}", file=sys.stderr)
        if any("scope" in p for p in problems):
            print('\n--scope example: "Oostende civil marriages 1895-1905, both spellings"', file=sys.stderr)
        raise SystemExit(1)

    reg.append_log(entry)
    where = f"{entry['site']}/{entry['page']}" if entry["page"] else entry["site"]
    print(f"logged: {entry['person']} · {where} · {entry['goal']} → {entry['result']} ({entry['basis']})")


def cmd_tried(args):
    people = load_people()
    rows = [e for e in reg.load_log() if e.get("person") == args.person]
    if not rows:
        return print(f"Nothing logged for {name_of(people, args.person)} yet — everything is untried.")

    print(f"{name_of(people, args.person)} — {len(rows)} search(es)\n")
    for e in rows:
        where = f"{e['site']}/{e['page']}" if e.get("page") else e["site"]
        print(f"  {reg.MARK[e['result']]} {e['result'].upper():<10} {where:<30} goal: {e['goal']}   ({e['date']})")
        print(f"      basis:    {e.get('basis', '—')}")
        if e.get("query"):
            print(f"      searched: {e['query']}")
        if e.get("scope"):
            print(f"      COVERED:  {e['scope']}")
        if e.get("found"):
            print(f"      FOUND:    {e['found']}")
        if e.get("why"):
            print(f"      WHY NOT:  {e['why']}")
        print()

    dead = sorted({(f"{e['site']}/{e['page']}" if e.get("page") else e["site"]) for e in rows if e["result"] == "miss"})
    retry = sorted({e["site"] for e in rows if e["result"] == "blocked"})
    if dead:
        print(f"  Searched and empty — do not repeat without a new angle:\n    {', '.join(dead)}")
    if retry:
        print(f"  Never actually reached — WORTH RETRYING:\n    {', '.join(retry)}")
    stale = reg.stale_misses([e for e in rows if e["result"] != "blocked"], reg.load_sources()[0])
    if stale:
        print("\n  Re-openable — the venue has changed since these were run:")
        for e in stale:
            print(f"    {e['site']:<20} {e['reasons'][0]}")


def cmd_untried(args):
    sites, pages = reg.load_sources()
    rows = [e for e in reg.load_log() if e.get("person") == args.person]
    used_sites = {e["site"] for e in rows}
    used_pages = {e["page"] for e in rows if e.get("page")}

    fresh_sites = [s for s in sites if s["id"] not in used_sites]
    print(f"Sites never searched for {args.person} ({len(fresh_sites)}):\n")
    for s in fresh_sites:
        print(f"  {s['id']:<24} {(s.get('access') or '-'):<8} {s['title']}")

    fresh_pages = [p for p in pages if p["id"] not in used_pages and p.get("kind") != "record"]
    print(f"\nPages never opened for them ({len(fresh_pages)}) — those with a track record first:\n")
    for p in sorted(fresh_pages, key=lambda p: 0 if p.get("yielded") else 1):
        track = "has yielded before" if p.get("yielded") else "—".ljust(18)
        print(f"  {p['id']:<24} {p['site']:<14} {track} {p.get('covers', '')}")


def cmd_sources(args):
    sites, pages = reg.load_sources()
    print(f"SITES ({len(sites)}) — base venues\n")
    for s in sites:
        caps = ",".join(s.get("capabilities") or []) or "—"
        print(f"  {s['id']:<24} {(s.get('access') or '-'):<8} {s['kind']:<9} {caps:<24} {s['title']}")
    print(f"\nPAGES ({len(pages)}) — specific trees, collections and documents\n")
    by_site: dict[str, list] = {}
    for p in pages:
        by_site.setdefault(p["site"], []).append(p)
    for site, listed in by_site.items():
        print(f"  {site}")
        for p in listed:
            print(f"    {p['id']:<30} {p['kind']:<11} {'✓ yielded' if p.get('yielded') else '·'}  {p['title']}")


def cmd_yield(args):
    log = reg.load_log()
    sites, pages = reg.load_sources()

    def tally(key):
        out: dict[str, dict] = {}
        for e in log:
            k = key(e)
            if not k:
                continue
            row = out.setdefault(k, dict.fromkeys(reg.RESULTS, 0) | {"total": 0})
            row[e["result"]] += 1
            row["total"] += 1
        return out

    print("BY SITE — searches run, and how they went\n")
    print(f"  {'site':<24} {'run':>3}  {'hit':>3} {'miss':>4} {'amb':>3} {'blk':>3}")
    by_site = tally(lambda e: e.get("site"))
    for sid, t in sorted(by_site.items(), key=lambda kv: (-kv[1]["hit"], -kv[1]["total"])):
        print(f"  {sid:<24} {t['total']:>3}  {t['hit']:>3} {t['miss']:>4} {t['ambiguous']:>3} {t['blocked']:>3}")

    # Which BASIS pays off, which the flat site tally cannot show. It is the difference
    # between "Geneanet is unproductive" and "reading other people's trees is
    # unproductive, wherever they are hosted".
    print("\nBY BASIS — how the material was consulted\n")
    print(f"  {'basis':<14} {'run':>3}  {'hit':>3} {'miss':>4} {'amb':>3} {'blk':>3}")
    for basis, t in sorted(tally(lambda e: e.get("basis")).items(), key=lambda kv: (-kv[1]["hit"], -kv[1]["total"])):
        print(f"  {basis:<14} {t['total']:>3}  {t['hit']:>3} {t['miss']:>4} {t['ambiguous']:>3} {t['blocked']:>3}")

    print("\nPAGES THAT HAVE YIELDED\n")
    for p in (p for p in pages if p.get("yielded")):
        print(f"  {p['id']} ({p['site']})")
        print(f"    {p['yielded']}")

    untouched = [s for s in sites if s["id"] not in by_site]
    if untouched:
        print(f"\nSITES NEVER SEARCHED AT ALL ({len(untouched)}) — the untapped list:\n")
        for s in untouched:
            print(f"  {s['id']:<24} {(s.get('access') or '-'):<8} {s['title']}")
    open_pages = [p for p in pages if not p.get("yielded") and p.get("kind") != "record"]
    if open_pages:
        print(f"\nPAGES REGISTERED BUT NOT YET PRODUCTIVE ({len(open_pages)}):\n")
        for p in open_pages:
            print(f"  {p['id']:<30} {p['site']:<14} {p.get('covers', '')}")


def cmd_stale(args):
    """A miss is a claim about a moment, not for ever."""
    sites, _ = reg.load_sources()
    stale = reg.stale_misses(reg.load_log(), sites)
    if not stale:
        return print("Nothing to re-open — no venue has gained a capability since it was last searched.")
    people = load_people()
    print(f"{len(stale)} search(es) worth running again — the venue is not what it was.\n")
    for e in stale:
        print(f"  {name_of(people, e['person']):<32} {e['site']:<16} {e['result']} via {e.get('basis', '—')}  ({e['date']})")
        for reason in e["reasons"]:
            print(f"      → {reason}")
        if e.get("scope"):
            print(f"      last covered: {e['scope']}")
        print()


def cmd_frontiers(args):
    rows = frontier_rows()
    if not corpus_exists():
        print("note: nothing harvested yet, so P is a prior rather than a count.")
        print("      uv run tools/harvest.py frontiers   fills it in.\n")
    print(f"{len(rows)} open frontiers, ranked by value × P(resolvable) ÷ cost.\n")
    print(f"  {'score':>6} {'':<34} {'gen':>4} {'below':>5} {'P':>5} {'cost':>5}  next move")
    for r in rows[: args.limit]:
        gen = "—" if r.depth == float("inf") else str(int(r.depth))
        kind = "anc" if r.is_ancestor else "rel"
        print(f"  {r.score:>6.2f} {r.name:<34} {gen:>4} {r.reach:>5} {r.probability:>5.2f} {r.cost:>5.1f}  {r.route}")
        print(f"  {'':>6} {kind} · {r.why} · {r.searched} searched"
              f"{f' · {r.blocked} blocked' if r.blocked else ''}"
              f"{f' · surname {r.surname_bits:.0f} bits' if r.surname else ''}"
              f"    uv run tools/research.py tried {r.id}")
    if len(rows) > args.limit:
        print(f"\n  …and {len(rows) - args.limit} more.")


def cmd_acts(args):
    """The act that answers the most open questions, not the frontier that shouts loudest."""
    if not corpus_exists():
        raise SystemExit("error nothing harvested yet — run: uv run tools/harvest.py frontiers")
    people = load_people()
    frontier_ids = {r.id for r in frontier_rows(people)}
    ordered = greedy_cover(act_coverage(people, frontier_ids))
    if not ordered:
        return print("No held act touches an open frontier. Harvest more: uv run tools/harvest.py frontiers")

    covered = sum(len(new) for _, new in ordered)
    print(f"{len(ordered)} acts cover {covered} of {len(frontier_ids)} open frontiers, best first.\n")
    for cov, new in ordered[: args.limit]:
        act = cov.act
        print(f"  {act.label}  ({act.archive_org})")
        print(f"    {act.url}")
        if act.scan:
            print(f"    scan: {act.scan}")
        if act.original:
            print(f"    act:  {act.original}")
        for pid, why in cov.resolves:
            if pid in new:
                print(f"    RESOLVES {pid:<24} {why}")
        for pid, why in cov.mentions:
            if pid in new:
                print(f"    mentions {pid:<24} {why}")
        print()


def cmd_children(args):
    """Objective 2, which had no queue at all until now.

    Every other report here asks the upward question — who were this person's parents.
    That grows the tree one generation at a time and never finds a sibling. This asks the
    downward one: which children does the corpus name for couples the tree already holds?
    """
    people = load_people()
    if not corpus_exists():
        return print("Nothing harvested yet — this reads the corpus:\n"
                     "  uv run tools/harvest.py surname <X>")
    leads = missing_children(people)
    if not leads:
        births = sum(1 for a in load_corpus() if a.type == "Geboorte")
        print("No unrecorded children in the held acts.\n")
        print(f"The corpus holds {births} birth acts of {len(load_corpus())}. That is the "
              "limit here, not the tree:")
        print("  harvests so far were driven by SURNAME, which finds ancestors — a birth act "
              "is indexed\n  under the child, so a sibling is only reachable through the "
              "commune or the parents.")
        print("\n  uv run tools/harvest.py place <commune>    the harvest objective 2 needs")
        return

    add = [x for x in leads if x.kind == "add"]
    link = [x for x in leads if x.kind == "link"]
    print(f"{len(leads)} unrecorded children — {len(add)} to add, {len(link)} already "
          "held but not linked to these parents.\n")
    for mc in leads[: args.limit]:
        tag = "ADD" if mc.kind == "add" else f"LINK → {mc.existing}"
        print(f"  [{tag}] {mc.name}")
        print(f"      b. {mc.birth or '?'}{' ' + mc.place if mc.place else ''}"
              f" · child of {mc.father} + {mc.mother}")
        print(f"      {mc.act_label} — {mc.act_url}")
    print("\nNone of these is a fact. Each is an act naming a child of a couple this tree")
    print("already holds — verify it, then record it like any other finding.")


def cmd_components(args):
    """Objective 3, as the graph problem it is."""
    people = load_people()
    groups = tree_components(people)
    print(f"The tree is {len(groups)} connected component(s).\n")
    for g in groups:
        surnames = sorted({people[p].get("surname") for p in g if people[p].get("surname")})
        print(f"  {len(g):>4} people — {', '.join(surnames[:6])}{' …' if len(surnames) > 6 else ''}")
        if len(g) <= 6:
            print(f"         {', '.join(g)}")

    if not corpus_exists():
        return print("\nHarvest a surname to see the families the corpus knows and the tree does not:"
                     "\n  uv run tools/harvest.py surname Bundervoet")

    surname = args.surname or _largest_surname(people)
    print(f"\nCorpus clusters for \"{surname}\", by commune — where the forest could join up:\n")
    clusters = surname_clusters(people, surname)
    if not clusters:
        return print(f"  nothing harvested for {surname} yet — uv run tools/harvest.py surname \"{surname}\"")
    for c in clusters[: args.limit]:
        span = f"{c.span[0]}–{c.span[1]}" if c.span[0] else "undated"
        print(f"  {c.place:<28} {c.mentions:>4} mentions  {span:<12} {len(c.acts)} acts")
        if c.best_link:
            print(f"      joins to {c.best_link[0]} — {c.best_link[1]}")
        else:
            print("      NO LINK to anyone in the tree — a separate root, which objective 3 expects")


def _largest_surname(people):
    counts: dict[str, tuple[int, str]] = {}
    for p in people.values():
        if p.get("surname"):
            key = family_key(p["surname"])
            n, name = counts.get(key, (0, p["surname"]))
            counts[key] = (n + 1, name)
    return max(counts.values(), key=lambda v: v[0])[1] if counts else ""


def cmd_collapse(args):
    config = load_config()
    people = load_people(config["roster"])
    ladder, consanguine, multi = pedigree_collapse(people, config["meta"])

    print("Ancestors per generation, against the 2^g the architecture is sized for.\n")
    print(f"  {'gen':>3} {'known':>6} {'of':>8}  {'':<28}")
    for row in ladder:
        share = row.distinct / row.theoretical
        bar = "█" * max(1, round(share * 28))
        print(f"  {row.generation:>3} {row.distinct:>6} {row.theoretical:>8}  {bar:<28} {share:>5.0%}")
    print("\n  The gap is mostly unfinished research, not collapse — but every couple below")
    print("  is a place where two lines genuinely rejoin, and 2^g overstates the tree.")

    if consanguine:
        print(f"\n{len(consanguine)} couple(s) share an ancestor — the tree folds back here:\n")
        for a, b, shared in consanguine[: args.limit]:
            print(f"  {people[a]['name']} × {people[b]['name']}")
            print(f"      common ancestor(s): {', '.join(people[s]['name'] for s in shared)}")
    else:
        print("\nNo couple in the tree yet shares a recorded ancestor.")
    if multi:
        print(f"\n{len(multi)} person(s) reached by more than one line from a root.")


def cmd_report(args):
    log = reg.load_log()
    people = load_people()
    if not log:
        return print("The search log is empty.")

    by_result: dict[str, int] = {}
    for e in log:
        by_result[e["result"]] = by_result.get(e["result"], 0) + 1
    print(f"{len(log)} searches logged\n")
    for r, desc in reg.RESULTS.items():
        print(f"  {reg.MARK[r]} {r:<10} {by_result.get(r, 0):>3}   {desc}")

    manifest = load_manifest()["harvests"]
    if manifest:
        acts = sum(h["acts"] for h in manifest)
        print(f"\n{len(manifest)} harvests held · {acts} acts · answerable without a browser or a login")

    per_person: dict[str, list] = {}
    for e in log:
        per_person.setdefault(e["person"], []).append(e)
    print("\nEffort per person — no hits after several tries means change the angle:\n")
    for pid, rows in sorted(per_person.items(), key=lambda kv: -len(kv[1])):
        hits = sum(1 for r in rows if reg.succeeded(r["result"]))
        blocked = sum(1 for r in rows if r["result"] == "blocked")
        print(f"  {name_of(people, pid):<32} {len(rows):>2} searched · {hits} hit"
              + (f" · {blocked} still blocked" if blocked else "")
              + ("   ← stuck" if not hits and len(rows) >= 3 else ""))


def cmd_check(args):
    sites, pages = reg.load_sources()
    problems = reg.registry_problems(sites, pages, reg.load_log(), load_people(), load_artifacts())
    for p in problems:
        print("error " + p, file=sys.stderr)
    if problems:
        print(f"\n{len(problems)} problem(s).")
        raise SystemExit(1)
    print(f"OK — {len(sites)} sites, {len(pages)} pages, {len(reg.load_log())} searches logged.")


def cmd_docs(args):
    sites, pages = reg.load_sources()
    log = reg.load_log()
    per_site: dict[str, int] = {}
    for e in log:
        per_site[e["site"]] = per_site.get(e["site"], 0) + 1

    out = [
        "# Sources",
        "",
        "<!-- GENERATED from research/sources.json by tools/research.py docs — do not edit. -->",
        "",
        "Two levels: **sites** are the base venues, **pages** are the specific trees,",
        "collections and documents inside them that were actually opened. The search log that",
        "references both is `research/searches.jsonl` — see [searching.md](searching.md).",
        "",
        "Confidence: **doc** = seen in a primary act or an authoritative index · **sup** = a",
        "single member tree, not checked against the act · **fam** = family testimony.",
        "",
        "*Capabilities* say what a venue can be asked, not how good it is — a `name-index`",
        "miss is only a miss for what somebody indexed, and a venue that later gains",
        "`full-text` re-opens every one of them. `uv run tools/research.py stale` lists those.",
        "",
        "## Sites",
        "",
        "| Site | Kind | Access | Capabilities | Searches run | Covers |",
        "|---|---|---|---|---|---|",
    ]
    for s in sites:
        covers = (s.get("covers") or "").replace("|", "\\|")
        url = f" <{s['url']}>" if s.get("url") else ""
        caps = ", ".join(s.get("capabilities") or []) or "—"
        out.append(f"| `{s['id']}`{url} | {s['kind']} | {s.get('access') or '—'} | {caps} | {per_site.get(s['id'], 0)} | {covers} |")
    out.append("")
    for s in (s for s in sites if s.get("note")):
        out += [f"**`{s['id']}`** — {s['note']}", ""]

    out += ["## Pages", ""]
    by_site: dict[str, list] = {}
    for p in pages:
        by_site.setdefault(p["site"], []).append(p)
    for site in sites:
        listed = by_site.get(site["id"])
        if not listed:
            continue
        out += [f"### {site['title']}", ""]
        for p in listed:
            out.append(f"#### `{p['id']}` — {p['title']}")
            out.append(f"- **Kind:** {p['kind']}" + (f" · <{p['url']}>" if p.get("url") else ""))
            if p.get("collection"):
                out.append(f"- **Collection:** {p['collection']}")
            if p.get("covers"):
                out.append(f"- **Covers:** {p['covers']}")
            out.append(f"- **Yielded:** {p.get('yielded') or '*nothing yet*'}")
            if p.get("artifact"):
                out.append(f"- **Saved artifact:** `data/artifacts/{p['artifact']}.md`")
            if p.get("image"):
                out.append(f"- **Image:** <{p['image']}>")
            if p.get("confidence"):
                out.append(f"- **Confidence:** {p['confidence']}")
            if p.get("accessed"):
                out.append(f"- **Accessed:** {p['accessed']}")
            if p.get("note"):
                out.append(f"- **Note:** {p['note']}")
            out.append("")
    (ROOT / "docs" / "sources.md").write_text("\n".join(out), encoding="utf-8")
    print(f"docs/sources.md regenerated — {len(sites)} sites, {len(pages)} pages.")


# ---------- wiring ----------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("log", help="record a search — hit or miss")
    p.add_argument("--person", required=True)
    p.add_argument("--goal", required=True)
    p.add_argument("--site", required=True)
    p.add_argument("--page")
    p.add_argument("--result", required=True, choices=list(reg.RESULTS))
    p.add_argument("--basis", required=True, choices=list(reg.BASIS),
                   help="how the material was consulted — what makes a miss re-openable later")
    p.add_argument("--query")
    p.add_argument("--scope", help="what was actually covered: commune and years, or the whole province")
    p.add_argument("--found")
    p.add_argument("--why")
    p.add_argument("--url")
    p.add_argument("--artifact")
    p.add_argument("--note")
    p.add_argument("--date")
    p.set_defaults(fn=cmd_log)

    for name, fn, help_text in (
        ("tried", cmd_tried, "what was searched for one person, and how it went"),
        ("untried", cmd_untried, "sites and pages not yet used on them"),
    ):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("person")
        p.set_defaults(fn=fn)

    for name, fn, help_text, limit in (
        ("frontiers", cmd_frontiers, "what to work on next, ranked", 20),
        ("acts", cmd_acts, "which held acts answer the most open frontiers", 15),
        ("children", cmd_children, "children the corpus names for couples we hold — objective 2", 25),
        ("collapse", cmd_collapse, "where the tree folds back on itself", 20),
    ):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("--limit", type=int, default=limit)
        p.set_defaults(fn=fn)

    p = sub.add_parser("components", help="disconnected families — objective 3")
    p.add_argument("--surname", help="which surname's corpus clusters to show")
    p.add_argument("--limit", type=int, default=15)
    p.set_defaults(fn=cmd_components)

    for name, fn, help_text in (
        ("sources", cmd_sources, "the registry, sites then pages"),
        ("yield", cmd_yield, "which sites, pages and methods actually pay off"),
        ("stale", cmd_stale, "misses a venue has since outgrown"),
        ("report", cmd_report, "where the effort has gone"),
        ("check", cmd_check, "validate the log and registry"),
        ("docs", cmd_docs, "regenerate docs/sources.md"),
    ):
        p = sub.add_parser(name, help=help_text)
        p.set_defaults(fn=fn)

    args = parser.parse_args()
    # The reports that read the corpus want the index current before they start, so the
    # rebuild is announced and attributed rather than appearing as an unexplained pause
    # in the middle of a report. The rest — the log, the registry, the docs — never touch
    # the corpus and must not pay for it.
    if args.command in ("frontiers", "acts", "children", "components"):
        store.ensure(verbose=True)
    args.fn(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
