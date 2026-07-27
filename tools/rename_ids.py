#!/usr/bin/env python3
"""Renumber every person id to the canonical form, and fix every reference to it.

    uv run tools/rename_ids.py plan      what would change, writing nothing
    uv run tools/rename_ids.py apply     do it

The form is `<surname>_<first given name>[_<birth year>]` — see `familytree/ids.py` for why
surname first and why the year is `point_year`.

`CLAUDE.md` says ids are stable because renaming one breaks every reference. That is true,
which is why this exists: there are 1925 wikilinks, 444 log entries, 35 artifact records and
two config files pointing at person ids, and the only safe way to move them is all at once,
by machine, with a check afterwards that nothing dangles.

WHAT IT WILL NOT DO. It never rewrites prose. 55 current ids are also ordinary words —
`alphonsus` is an id and a forename, `bossin` is an id and a surname — so a text
substitution would corrupt the sentences describing the evidence while looking like it
worked. Only exact structured positions and ``[[…]]`` links are touched, and anything
left pointing at a dead id is reported at the end rather than guessed at.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from familytree import frontmatter
from familytree.ids import WIKILINK, assign, rewrite_backticks, rewrite_wikilinks
from familytree.people import (
    ARTIFACTS_DIR, DATA, FIELDS, PEOPLE_DIR, ROOT, load_config, load_people,
)

DOCS = ROOT / "docs"
RESEARCH = ROOT / "research"


def _person_file(old: str, mapping: dict[str, str]) -> tuple[Path, Path, str]:
    """The record with every id it carries moved, read and written through the project's own
    parser so field order and quoting stay whatever `frontmatter` says they are."""
    path = PEOPLE_DIR / f"{old}.md"
    data, body = frontmatter.parse(path.read_text(encoding="utf-8"), f"{old}.md")
    data["id"] = mapping.get(old, old)
    for role in ("father", "mother"):
        if isinstance(data.get(role), dict) and data[role].get("id") in mapping:
            data[role]["id"] = mapping[data[role]["id"]]
        elif isinstance(data.get(role), str) and data[role] in mapping:
            data[role] = mapping[data[role]]
    for key in ("siblings", "spouses"):
        for entry in data.get(key) or []:
            if isinstance(entry, dict) and entry.get("id") in mapping:
                entry["id"] = mapping[entry["id"]]
    text = frontmatter.stringify(data, rewrite_wikilinks(body, mapping), FIELDS)
    return path, PEOPLE_DIR / f"{mapping.get(old, old)}.md", text


def _quoted(text: str, mapping: dict[str, str]) -> str:
    """`"old"` -> `"new"` for known ids only. A JSON string is delimited, so an exact
    whole-string match cannot collide with the same word inside a sentence."""
    return re.sub(r'"([a-z0-9_]+)"',
                  lambda m: f'"{mapping[m.group(1)]}"' if m.group(1) in mapping else m.group(0),
                  text)


def _jsonl(path: Path, mapping: dict[str, str]) -> str | None:
    """The search log and the gold standard, whose `person` field is a person id.

    Rewritten line by line as JSON rather than as text: `why` and `found` are free prose
    full of the names these ids are made of, and a substitution over the whole line would
    edit the reasoning as well as the reference.
    """
    out, changed = [], False
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            out.append(line)
            continue
        row = json.loads(line)
        if row.get("person") in mapping:
            row["person"] = mapping[row["person"]]
            changed = True
        out.append(json.dumps(row, ensure_ascii=False))
    return "\n".join(out) + "\n" if changed else None


def collect(mapping: dict[str, str], people_ids) -> tuple[list[tuple[Path, Path, str]], list[tuple[Path, str]]]:
    """Every write this rename implies: (renames, in-place edits). Nothing is written here."""
    # EVERY record, not only the ones whose own id moves. A record keeping its id still
    # points at other people, and the first run of this skipped those — `deridder_sophie`
    # kept her name and kept two dead wikilinks with it, which the dangling check below is
    # the only reason anyone found out.
    renames = [_person_file(old, mapping) for old in sorted(people_ids)]

    edits: list[tuple[Path, str]] = []
    for path in (DATA / "meta.json", DATA / "lineages.json"):
        before = path.read_text(encoding="utf-8")
        after = _quoted(before, mapping)
        if after != before:
            json.loads(after)          # refuse to write JSON this broke
            edits.append((path, after))

    for path in sorted(ARTIFACTS_DIR.glob("*.md")) if ARTIFACTS_DIR.is_dir() else []:
        data, body = frontmatter.parse(path.read_text(encoding="utf-8"), path.name)
        data["evidences"] = [mapping.get(x, x) for x in (data.get("evidences") or [])]
        after = frontmatter.stringify(data, rewrite_wikilinks(body, mapping), list(data))
        if after != path.read_text(encoding="utf-8"):
            edits.append((path, after))

    for name in ("searches.jsonl", "labels.jsonl"):
        path = RESEARCH / name
        if path.exists() and (after := _jsonl(path, mapping)):
            edits.append((path, after))

    for path in sorted(DOCS.rglob("*.md")):
        before = path.read_text(encoding="utf-8")
        after = rewrite_backticks(rewrite_wikilinks(before, mapping), mapping)
        if after != before:
            edits.append((path, after))
    return renames, edits


def dangling(mapping: dict[str, str]) -> list[str]:
    """References that still point at an id nobody has any more.

    Run after the rewrite, over everything, because the whole risk of this operation is a
    reference in a shape nobody thought of. Silence here is the only evidence that the list
    of places an id can appear was complete — and it has already earned that: the first run
    reported two, which was a record whose own id had not changed being skipped entirely.

    Checked STRUCTURALLY, never by substring. A raw `"peremans" in text` also fires on
    `\\"peremans\\"` inside a prose `why` field, which reported a rewrite that had in fact
    worked — a false alarm on a check like this is worse than none, because the next real
    one gets waved through.
    """
    gone = set(mapping) - set(mapping.values())
    found: list[str] = []

    def note(path: Path, ref: str) -> None:
        found.append(f"{path.relative_to(ROOT)}: still refers to {ref}")

    for path in sorted(PEOPLE_DIR.glob("*.md")):
        data, body = frontmatter.parse(path.read_text(encoding="utf-8"), path.name)
        refs = [data.get("id")]
        for role in ("father", "mother"):
            v = data.get(role)
            refs.append(v.get("id") if isinstance(v, dict) else v)
        for key in ("siblings", "spouses"):
            refs += [e.get("id") for e in (data.get(key) or []) if isinstance(e, dict)]
        refs += WIKILINK.findall(body)
        for ref in refs:
            if ref in gone:
                note(path, ref)

    for path in sorted(ARTIFACTS_DIR.glob("*.md")) if ARTIFACTS_DIR.is_dir() else []:
        data, body = frontmatter.parse(path.read_text(encoding="utf-8"), path.name)
        for ref in [*(data.get("evidences") or []), *WIKILINK.findall(body)]:
            if ref in gone:
                note(path, ref)

    for path in (DATA / "meta.json", DATA / "lineages.json"):
        blob = json.dumps(json.loads(path.read_text(encoding="utf-8")))
        for ref in sorted(gone):
            if f'"{ref}"' in blob:
                note(path, ref)

    for name in ("searches.jsonl", "labels.jsonl"):
        path = RESEARCH / name
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip() and json.loads(line).get("person") in gone:
                note(path, json.loads(line)["person"])

    for path in sorted(DOCS.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        refs = set(WIKILINK.findall(text)) | set(re.findall(r"`([a-z][a-z0-9_]*)`", text))
        for ref in sorted(refs & gone):
            note(path, ref)
    return sorted(set(found))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=("plan", "apply"))
    parser.add_argument("--limit", type=int, default=15)
    args = parser.parse_args()

    people = load_people(load_config()["roster"])
    mapping = {old: new for old, new in assign(people).items() if old != new}
    if not mapping:
        print("Every id is already in canonical form.")
        return 0

    renames, edits = collect(mapping, people)
    if args.command == "plan":
        print(f"{len(mapping)} of {len(people)} ids would change, "
              f"and {len(edits)} other file(s) reference them.\n")
        for old in sorted(mapping)[: args.limit]:
            print(f"  {old:<28} -> {mapping[old]}")
        if len(mapping) > args.limit:
            print(f"  …and {len(mapping) - args.limit} more.")
        print("\nFiles that would be edited:")
        for path, _ in edits[: args.limit]:
            print(f"  {path.relative_to(ROOT)}")
        if len(edits) > args.limit:
            print(f"  …and {len(edits) - args.limit} more.")
        return 0

    for path, new_path, _ in renames:
        if path != new_path:
            path.unlink()
    for _, new_path, text in renames:
        new_path.write_text(text, encoding="utf-8")
    for path, text in edits:
        path.write_text(text, encoding="utf-8")
    print(f"{len(mapping)} ids renamed, {len(edits)} other file(s) updated.")

    if stale := dangling(mapping):
        print(f"\n{len(stale)} reference(s) still point at an old id:", file=sys.stderr)
        for line in stale[:20]:
            print(f"  {line}", file=sys.stderr)
        return 1
    print("No reference anywhere still points at an old id.")
    print("Now run: uv run tools/build.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
