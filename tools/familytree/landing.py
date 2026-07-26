"""What the landing page says about the size of the tree.

index.html is three links and a paragraph, and it loads no JavaScript at all — so
unlike the tree page, which reads the census out of the bundle, its numbers have to be
written into it. That makes them the one kind of fact that can go stale without
anything failing: the tree grows, the paragraph still says 302.

So the sentence lives here rather than in the build script, for the same reason
`bundle.py` does: the validator has to be able to ask the same question the build
answers — is what the page says still what the data says — and refuse a commit when it
is not. The wording is generated, the numbers are derived, and neither is typed twice.
"""

from __future__ import annotations

import re

from .people import census

# What the build writes between, left visible in the page so the next person to open it
# knows the paragraph is generated and where from.
MARKERS = ("census", "updated")


def _plural(count: int, one: str, many: str) -> str:
    return f"{count} {one if count == 1 else many}"


def _listed(parts: list[str]) -> str:
    """"a, b and c", and nothing at all for an empty list — a group with nobody in it
    is absent rather than stated as a zero."""
    if not parts:
        return ""
    return parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " and " + parts[-1]


def _decade(year: int) -> str:
    """The decade a year falls in. The oldest dates in this tree are approximate
    (`~1440`), and a decade is what an approximate year actually supports — naming the
    year would read as a precision the record has not got."""
    return f"{year // 10 * 10}s"


def census_sentence(people: dict, config: dict) -> str:
    """The paragraph, from the same census the tree page shows in its subtitle."""
    c = census(people, config)

    groups = _listed([part for part in (
        _plural(c["ancestors"], "direct ancestor", "direct ancestors") if c["ancestors"] else "",
        _plural(c["relatives"], "other blood relative", "other blood relatives") if c["relatives"] else "",
        f"{c['others']} married in" if c["others"] else "",
    ) if part])

    text = _plural(c["total"], "person", "people") + (f" — {groups}." if groups else ".")
    # "Documented" is a claim about evidence, so it may only be made of the dates that
    # have some. This page claimed the tree was documented into the 1400s while the
    # 1400s rested on a member tree and the oldest act anyone had read was from 1649.
    if c["earliest"]:
        text += f" It reaches back to the {_decade(c['earliest'])}"
        if c["documented"]:
            text += f", and to the {_decade(c['documented'])} on records read in the archive"
        text += "."
    return text


def fill(page: str, marker: str, value: str) -> str:
    """Replace what sits between one pair of markers, leaving the markers in place."""
    return re.sub(
        f"(<!--{marker}-->).*?(<!--/{marker}-->)",
        lambda m: m.group(1) + value + m.group(2),
        page,
        flags=re.S,
    )


def missing_markers(page: str) -> list[str]:
    """Markers the page has lost. A guard that silently stops guarding is worse than
    no guard: without this, deleting a marker makes the page permanently "current",
    because there is then nothing to compare and nothing to replace."""
    return [m for m in MARKERS if f"<!--{m}-->" not in page or f"<!--/{m}-->" not in page]


def stale_reason(page: str, people: dict, config: dict) -> str | None:
    """Why the page no longer matches the data, or None if it does.

    Only the counts are compared. The `updated` date comes from git rather than from
    data/, and a validator that failed because a checkout had no history would be
    failing for a reason that has nothing to do with the tree.
    """
    if gone := missing_markers(page):
        return (
            f"index.html has lost its {', '.join(f'<!--{m}-->' for m in gone)} marker(s), "
            "so the build can no longer keep its numbers current"
        )
    if fill(page, "census", census_sentence(people, config)) != page:
        return "index.html's counts are out of date with data/ — run: uv run tools/build.py"
    return None
