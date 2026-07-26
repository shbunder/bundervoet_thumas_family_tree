"""The rendered documentation, checked for staleness.

`dist/docs/` is committed for the same reason `dist/bundle.js` is: Pages serves this
repository as it stands, so the rendered pages have to be in it. Unlike the bundle,
nothing checked it — and the hole was structural rather than an oversight. The validator
regenerates the bundle in memory and compares, which it can do because `bundle.py` is
stdlib; it cannot regenerate the docs, because MkDocs is an optional dependency group and
the validator is required to run from a bare clone with nothing fetched.

So this checks the one thing a dependency-free validator can: a **signature over the
inputs**, recorded when the site was last built. Same shape as `store.signature()` for the
corpus index, and the same reasoning — an artefact that silently lags its source reads as
current, which is worse than one that is obviously missing.

WHAT IT CATCHES: a `docs/` edit committed without a rebuild. That is the actual failure —
the docs became load-bearing for content that used to live in CLAUDE.md, so a stale page
is now a wrong answer rather than a cosmetic lag.

WHAT IT CANNOT CATCH: a `dist/docs/` that was hand-edited, or one built from these inputs
by a different version of MkDocs. Both would need the renderer to detect, which is exactly
what is not available here. The signature is over inputs, not output, and says so.

The signature file lives INSIDE `dist/docs/`, and is named WITHOUT a leading dot. Both
halves are load-bearing. MkDocs empties its output directory before every build, so a bare
`mkdocs build` deletes the signature and the validator then says the site was built by
something that did not record one — which is exactly true, and fails closed. Storing it
outside `dist/docs/` would leave a signature that still matched after a hand-run build,
and the check would pass without anything having verified it. The dot matters because
MkDocs's clean deliberately skips dotfiles (it has to: `site_dir` may hold `.git`), so
`.build-signature` SURVIVED a bare build and the check reported a fresh site as stale —
fail-closed, but for the wrong reason and with a misleading message.
"""

from __future__ import annotations

from hashlib import sha256

from .people import ROOT

CONFIG = ROOT / "mkdocs.yml"
DOCS_DIR = ROOT / "docs"
SITE_DIR = ROOT / "dist" / "docs"
SIGNATURE = SITE_DIR / "build-signature"

REBUILD = "uv run tools/build.py"

# Editor and OS droppings are not inputs, and letting one into the signature means a
# .DS_Store appearing next to the docs reports the whole site as stale.
_IGNORED = {".DS_Store", "Thumbs.db"}


def inputs() -> list:
    """Every file the rendered site is built from, in a stable order."""
    if not DOCS_DIR.is_dir():
        return []
    return sorted(
        (f for f in DOCS_DIR.rglob("*")
         if f.is_file() and f.name not in _IGNORED and not f.name.startswith(".")),
        key=lambda f: str(f.relative_to(ROOT)),
    )


def signature() -> str:
    """What the rendered site should have been built from.

    Content, not mtime — unlike `store.signature()`, which may use size and mtime because
    a harvest only ever appends and hashing 284 MB per command would cost more than the
    read. `docs/` is 452 KB and is edited in place, so mtime would both miss a revert and
    fire on a `touch`.
    """
    h = sha256()
    h.update(CONFIG.read_bytes() if CONFIG.exists() else b"")
    for f in inputs():
        h.update(str(f.relative_to(ROOT)).encode("utf-8"))
        h.update(f.read_bytes())
    return h.hexdigest()


def record() -> None:
    """Write the signature. Called after a build that actually succeeded, never before."""
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    SIGNATURE.write_text(signature() + "\n", encoding="utf-8")


def stale_reason() -> str | None:
    """None when the rendered site matches the sources it was built from."""
    if not SITE_DIR.is_dir() or not (SITE_DIR / "index.html").exists():
        return f"dist/docs/ has not been built — run: {REBUILD}"
    if not SIGNATURE.exists():
        return (f"dist/docs/ was built without recording what it was built from "
                f"(a bare `mkdocs build` does not) — run: {REBUILD}")
    if SIGNATURE.read_text(encoding="utf-8").strip() != signature():
        return f"dist/docs/ is out of date with docs/ — run: {REBUILD}"
    return None
