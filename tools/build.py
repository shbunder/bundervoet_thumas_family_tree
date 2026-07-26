#!/usr/bin/env python3
"""Regenerates everything derived from data/. Run with: uv run tools/build.py

    dist/bundle.js          the whole tree in one request, for the browser
    exports/family-tree.ged the GEDCOM 7 export
    docs/sources.md         the readable source list

It validates first and refuses to build from data that does not pass, so the generated
files can never be produced from a broken tree.
"""

from __future__ import annotations

import re
import subprocess
import sys
from datetime import date
from hashlib import sha256
from pathlib import Path

from familytree.bundle import build_bundle
from familytree.landing import census_sentence, fill, missing_markers
from familytree.people import ROOT, format_date, load_config, load_people

HERE = Path(__file__).resolve().parent


def run(script: str, *args: str) -> None:
    r = subprocess.run([sys.executable, str(HERE / script), *args])
    if r.returncode != 0:
        raise SystemExit(r.returncode)


def _last_data_change() -> str:
    """When the tree last changed — the last commit that touched data/, not the last
    time the build ran, because a rebuild is not an update to the family tree."""
    try:
        r = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", "data"],
            cwd=ROOT, capture_output=True, text=True, timeout=5,
        )
        if r.returncode == 0 and r.stdout.strip():
            return format_date(r.stdout.strip())
    except (OSError, subprocess.SubprocessError):
        pass
    return format_date(date.today().isoformat())


def fill_landing_page() -> None:
    """Write the tree's own numbers into index.html.

    That page loads no JavaScript, so anything it says about the size of the tree has
    to be put there. It comes from the same census the tree page reads out of the
    bundle, so the two pages can use different words but never different numbers, and
    the validator refuses to pass once what is written here has gone stale.
    """
    config = load_config()
    sentence = census_sentence(load_people(config["roster"]), config)

    page = ROOT / "index.html"
    before = page.read_text(encoding="utf-8")
    if gone := missing_markers(before):
        raise SystemExit(
            f"index.html is missing the {', '.join(gone)} marker(s) the build writes between — "
            "restore them, or its numbers stop being maintained."
        )
    after = fill(fill(before, "census", sentence), "updated", _last_data_change())
    if after != before:
        page.write_text(after, encoding="utf-8")
    print(f"index.html — {sentence}{' (unchanged)' if after == before else ''}")


def stamp_pages() -> None:
    """GitHub Pages caches for ten minutes, so every asset is referenced with a ?v=
    stamp; bumping it by hand was a step that got forgotten, and forgetting it means a
    change that looks like it failed. The stamp is a hash of what is actually served,
    so it changes when — and only when — the bytes do."""
    inputs = sorted(
        [ROOT / "dist" / "bundle.js", *(ROOT / "assets" / "js").iterdir(), *(ROOT / "assets" / "css").iterdir()],
        key=lambda p: str(p),
    )
    h = sha256()
    for f in inputs:
        h.update(f.read_bytes())
    stamp = h.hexdigest()[:8]

    changed = []
    for page in ("index.html", "Renee-Leon-family-tree.html"):
        f = ROOT / page
        if not f.exists():
            continue
        before = f.read_text(encoding="utf-8")
        after = re.sub(r"\?v=[\w.]+", f"?v={stamp}", before)
        if after != before:
            f.write_text(after, encoding="utf-8")
            changed.append(page)
    print(f"\nCache stamp → ?v={stamp} ({', '.join(changed)})" if changed
          else f"\nCache stamp unchanged at ?v={stamp}")


def main() -> int:
    check = subprocess.run([sys.executable, str(HERE / "check_data.py"), "--skip-generated"])
    if check.returncode != 0:
        print("\nValidation failed — nothing was generated.", file=sys.stderr)
        return 1

    bundle = build_bundle()
    out = ROOT / "dist" / "bundle.js"
    out.parent.mkdir(parents=True, exist_ok=True)
    before = out.read_text(encoding="utf-8") if out.exists() else None
    out.write_text(bundle, encoding="utf-8")
    kb = round(len(bundle.encode("utf-8")) / 1024)
    unchanged = " (unchanged)" if before == bundle else ""
    # Flushed, because the steps below write straight to the terminal from a
    # subprocess and would otherwise appear above this line.
    print(f"\ndist/bundle.js — {len(load_config()['roster'])} people, {kb} KB{unchanged}", flush=True)

    run("export_gedcom.py")
    run("research.py", "check")
    run("research.py", "docs")
    fill_landing_page()
    stamp_pages()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
