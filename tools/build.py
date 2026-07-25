#!/usr/bin/env python3
"""Regenerates everything derived from data/. Run with: uv run tools/build.py

    dist/bundle.js          the whole tree in one request, for the browser
    exports/family-tree.ged the GEDCOM 7 export
    docs/sources.md         the readable source list

It validates first and refuses to build from data that does not pass, so the generated
files can never be produced from a broken tree.
"""

from __future__ import annotations

import subprocess
import sys
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from familytree.bundle import build_bundle  # noqa: E402
from familytree.people import ROOT, load_config  # noqa: E402


def run(script: str, *args: str) -> None:
    r = subprocess.run([sys.executable, str(HERE / script), *args])
    if r.returncode != 0:
        raise SystemExit(r.returncode)


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

    import re

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
    stamp_pages()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
