"""The canonical form of a person id, and every place one is referenced.

    <surname>_<first given name>[_<birth year>]

lowercase ASCII, particles folded in — "Van den Bemden" is `vandenbemden`, so a family is
one prefix and `ls data/people/ | grep dekeyser` is a line of descent. That is the whole
reason for surname-first: the directory listing sorts into families, which is what makes an
id useful for finding something by hand rather than only for pointing at it.

The birth year is included whenever the record ASSERTS one. `point_year`, not `year_of`:
`<1727` bounds a birth without stating it, and an id ending `_1727` for a record that only
says "before 1727" would be the id claiming more than the record does.

WHY THIS IS RISKY AND WHAT MAKES IT SAFE. `CLAUDE.md` says ids are stable because renaming
one breaks every reference, and it is right — there are 1925 wikilinks, 444 log entries, 35
artifacts and two config files pointing at them. So renaming is done by machine, over every
one of those, in one pass. What is deliberately NOT done is a text substitution: 55 ids are
also ordinary words (`alphonsus` is an id and a forename, `bossin` is an id and a surname),
so replacing them in prose would quietly corrupt the sentences that describe the evidence.
Only exact structured positions and ``[[…]]`` links are touched.
"""

from __future__ import annotations

import re
import unicodedata

from .people import family_key, given_names, point_year


def _ascii(text: str) -> str:
    """Lowercase, accents stripped, everything but a-z dropped. `family_key` already does
    this for surnames; given names go through the same door so the two halves of an id can
    never be normalised two different ways."""
    s = unicodedata.normalize("NFD", (text or "").lower())
    return re.sub(r"[^a-z]", "", s)


def first_given(p: dict) -> str:
    """The first given name, which is what someone is filed under.

    Not all of them. "Adriana Theresia Judoca Sabbe" would make an id nobody types twice,
    and the disambiguation it buys is already bought by the birth year. Where it is not —
    two Adriana Sabbes born the same year — the suffix below settles it, which is rarer and
    cheaper than lengthening every id in the tree against the chance of a clash.
    """
    return _ascii((given_names(p).split() or [""])[0])


def canonical(p: dict) -> str:
    surname = family_key(p.get("surname"))
    given = first_given(p)
    year = point_year((p.get("birth") or {}).get("date"))
    stem = "_".join(x for x in (surname, given) if x) or _ascii(p.get("name", "")) or p["id"]
    return f"{stem}_{year}" if year else stem


def assign(people: dict) -> dict[str, str]:
    """old id -> new id, for everyone. Deterministic, so re-running gives the same answer.

    Clashes are broken by a numeric suffix in old-id order rather than by reaching for
    another field. A second identifier in the id would have to be one every record carries,
    and there isn't one — the tree holds 141 people with no birth year at all.
    """
    out: dict[str, str] = {}
    taken: dict[str, int] = {}
    for old in sorted(people):
        base = canonical(people[old])
        n = taken.get(base, 0) + 1
        taken[base] = n
        out[old] = base if n == 1 else f"{base}_{n}"
    return out


# ---------- where an id is referenced ----------
#
# Structured positions only. Every entry here is an exact match against a known id, never a
# substring of prose — see the note at the top of this module for why that line matters.

WIKILINK = re.compile(r"\[\[([a-z0-9_]+)\]\]")


def rewrite_wikilinks(text: str, mapping: dict[str, str]) -> str:
    """`[[old]]` -> `[[new]]`, and anything that is not a known id is left exactly as it is.

    The brackets are what make this safe: they are a reference by construction, so there is
    no way to confuse one with the same word used as a word.
    """
    return WIKILINK.sub(lambda m: f"[[{mapping.get(m.group(1), m.group(1))}]]", text)


def rewrite_backticks(text: str, mapping: dict[str, str]) -> str:
    """``old`` -> ``new`` in the written-up docs, for known ids only.

    The research log refers to people both ways. Restricting to ids the mapping knows is
    what keeps this off the 582 other backticked tokens in `docs/` — source ids, field
    names, commands — which look identical and are not people.
    """
    return re.sub(r"`([a-z][a-z0-9_]*)`",
                  lambda m: f"`{mapping[m.group(1)]}`" if m.group(1) in mapping else m.group(0),
                  text)
