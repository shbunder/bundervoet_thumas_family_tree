#!/usr/bin/env python3
"""Write exports/family-tree.ged. Run with: uv run tools/export_gedcom.py

The exporter refuses to write if the file does not read back as the same tree: it
reparses its own output, rebuilds the parent and marriage links from that alone, and
compares them to the source records.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from familytree.gedcom import build  # noqa: E402
from familytree.people import ROOT, load_config  # noqa: E402

OUT = ROOT / "exports" / "family-tree.ged"


def main() -> int:
    lines, report, problems = build()
    if problems:
        for p in problems[:20]:
            print("error " + p, file=sys.stderr)
        print(f"\n{len(problems)} problem(s) — not written.", file=sys.stderr)
        return 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    ids = load_config()["roster"]
    print(f"Wrote {OUT.relative_to(ROOT)} — {len(ids)} individuals, {report['families']} families, "
          f"{report['sources']} sources, {len(lines)} lines.")
    print(f"Occupations recorded: {report['occupations']}")
    if report["unparsed_dates"]:
        print(f"\nDates kept as text, not parsed into GEDCOM dates ({len(report['unparsed_dates'])}):")
        for d in report["unparsed_dates"]:
            print("  " + d)
    if report["notes"]:
        print(f"\nParser debris dropped ({len(report['notes'])}):")
        for n in report["notes"]:
            print("  " + n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
