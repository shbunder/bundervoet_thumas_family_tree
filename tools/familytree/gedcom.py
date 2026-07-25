"""The tree as GEDCOM 7 — the open interchange format every genealogy program reads.

The person files stay the source of truth; this is a generated view of them, so it is
regenerated rather than edited. What GEDCOM cannot carry faithfully is reported rather
than fudged into a field that would read as fact to whatever imports it.

Deliberately GEDCOM 7 and not 5.5.1: v7 is UTF-8 throughout (these records are full of
é and ë), has no line-length limit and no CONC continuation, so the long research
notes survive intact.
"""

from __future__ import annotations

import re

from .people import FIELDS, given_names, load_config, load_people  # noqa: F401
from .sources import load_sources

MONTHS = {"jan": "JAN", "feb": "FEB", "mar": "MAR", "apr": "APR", "may": "MAY", "jun": "JUN",
          "jul": "JUL", "aug": "AUG", "sep": "SEP", "oct": "OCT", "nov": "NOV", "dec": "DEC"}
MONTH_NUM = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

# QUAY is GEDCOM's certainty scale: 3 primary, 2 secondary, 1 questionable,
# 0 unreliable. It maps onto the project's confidence codes closely enough.
QUAY = {"doc": 3, "sup": 2, "fam": 1, "unk": 0}


def gedcom_date(d: str | None) -> str | None:
    """Person dates are stored in the project's own strict grammar, so this is a
    straight translation rather than a guess. It used to be a parser working over free
    text, which is where every date bug in this exporter came from."""
    if not d:
        return None
    if (m := re.match(r"^(\d{4})-(\d{2})-(\d{2})$", d)):
        return f"{int(m[3])} {MONTH_NUM[int(m[2]) - 1]} {m[1]}"
    if (m := re.match(r"^(\d{4})-(\d{2})$", d)):
        return f"{MONTH_NUM[int(m[2]) - 1]} {m[1]}"
    if re.match(r"^\d{4}$", d):
        return d
    if (m := re.match(r"^~(\d{4})$", d)):
        return f"ABT {m[1]}"
    if (m := re.match(r"^<(\d{4})$", d)):
        return f"BEF {m[1]}"
    if (m := re.match(r"^>(\d{4})$", d)):
        return f"AFT {m[1]}"
    if (m := re.match(r"^(\d{4})\.\.(\d{4})$", d)):
        return f"BET {m[1]} AND {m[2]}"
    return None


def parse_when(raw, notes: list[str]):
    """Turn "12 Nov 1876 · Hamme (Oost-Vlaanderen)" or "6 Jan 1905 Oostende" into a
    GEDCOM date and a place. Anything it cannot read with confidence comes back as
    None so the caller keeps the original text instead."""
    if not raw:
        return None
    s = str(raw).strip()
    qualifier = ""

    s = re.sub(r"^†\s*", "", s)
    s = re.sub(r"^(b|d)\.\s*", "", s, flags=re.I)

    # Some records lead with the place — "Oostende, after 2000". Take it off the front
    # so the remainder can be read as a date.
    leading_place = None
    lead = re.match(r"^([^,0-9<>~]+),\s*(.+)$", s)
    if lead:
        leading_place = lead[1].strip()
        s = lead[2].strip()

    if re.match(r"^(bef\.?|before)\s+", s, re.I):
        qualifier, s = "BEF", re.sub(r"^(bef\.?|before)\s+", "", s, flags=re.I)
    elif s.startswith("<"):
        qualifier, s = "BEF", re.sub(r"^<\s*", "", s)
    elif re.match(r"^(aft\.?|after)\s+", s, re.I):
        qualifier, s = "AFT", re.sub(r"^(aft\.?|after)\s+", "", s, flags=re.I)
    elif s.startswith(">"):
        qualifier, s = "AFT", re.sub(r"^>\s*", "", s)
    elif re.match(r"^[~≈]\s*", s) or re.match(r"^(c\.|ca\.?|circa|about|abt\.?)\s+", s, re.I):
        qualifier = "ABT"
        s = re.sub(r"^[~≈]\s*", "", s)
        s = re.sub(r"^(c\.|ca\.?|circa|about|abt\.?)\s+", "", s, flags=re.I)

    date = None
    rest = s
    # "1575..1587" is a span, and "1913/14" means one year or the other. GEDCOM says
    # both with a range, which is more faithful than picking one end.
    if (m := re.match(r"^(\d{4})\s*\.\.\s*(\d{4})", s)):
        date, rest, qualifier = f"BET {m[1]} AND {m[2]}", s[m.end():], ""
    elif (m := re.match(r"^(\d{4})/(\d{1,2})\b", s)):
        second = m[1][:2] + m[2] if len(m[2]) == 2 else m[1][:3] + m[2]
        date, rest, qualifier = f"BET {m[1]} AND {second}", s[m.end():], ""
    elif (m := re.match(r"^(\d{1,2})\s+([A-Za-z]{3})[a-z]*\.?\s+(\d{4})", s)):
        mon = MONTHS.get(m[2].lower())
        if mon:
            date, rest = f"{int(m[1])} {mon} {m[3]}", s[m.end():]
    elif (m := re.match(r"^([A-Za-z]{3})[a-z]*\.?\s+(\d{4})", s)):
        mon = MONTHS.get(m[1].lower())
        if mon:
            date, rest = f"{mon} {m[2]}", s[m.end():]
    elif (m := re.match(r"^(\d{4})", s)):
        date, rest = m[1], s[m.end():]
    if not date:
        return None

    # "2017 & 2019 · Leuven" is two people's dates in one field — not a single event.
    if re.match(r"^\s*&", rest):
        return None

    place = leading_place or re.sub(r"^\s*[·,]\s*", "", rest).lstrip().strip() or None
    # A place name starts with a letter. Anything else is parser debris from a date
    # format not anticipated here, and is dropped rather than published as a place.
    if place and not re.match(r"^[A-Za-zÀ-ÿ]", place):
        notes.append(f'discarded "{place}" as a place — from "{raw}"')
        place = None
    return {"date": f"{qualifier} {date}" if qualifier else date, "place": place}


def parse_marriage(detail, notes):
    """Marriage details are free text like "Oostkamp, 30 Sep 1863". A leading word with
    no digits is the place; the rest is tried as a date. The raw text is always kept as
    a note, so nothing is lost to the parser's judgement."""
    if not detail:
        return None
    out = {"note": detail, "date": None, "place": None}
    s = re.sub(r"^m\.\s*", "", detail, flags=re.I)
    s = re.sub(r"^married\s+", "", s, flags=re.I)
    m = re.match(r"^([^,0-9]+),\s*(.+)$", s)
    if m:
        out["place"], s = m[1].strip(), m[2]
    when = parse_when(s, notes)
    if when:
        out["date"] = when["date"]
        if not out["place"] and when["place"] and not re.search(r"[();—]", when["place"]):
            out["place"] = when["place"]
    return out


def build():
    """Return ``(lines, report, problems)``. Nothing is written unless problems is empty."""
    config = load_config()
    ids, meta, branches = config["roster"], config["meta"], config["branches"]
    people = load_people(ids)
    report = {"unparsed_dates": [], "occupations": 0, "notes": []}

    # ---------- sex ----------
    # Stated if the record says so, otherwise inferred from being someone's father or
    # mother, otherwise U. GEDCOM has a value for "we do not know"; use it.
    sex = {pid: people[pid]["sex"] for pid in ids if people[pid].get("sex") in ("f", "m")}
    for pid in ids:
        p = people[pid]
        if p.get("father") and not sex.get(p["father"]):
            sex[p["father"]] = "m"
        if p.get("mother") and not sex.get(p["mother"]):
            sex[p["mother"]] = "f"

    # ---------- families ----------
    # A couple is either proven by a shared child or recorded as a marriage. Both
    # produce one FAM; the key is the unordered pair.
    families: dict[str, dict] = {}

    def family_for(a, b):
        key = "|".join(sorted([a, b]))
        if key not in families:
            families[key] = {"a": a, "b": b, "children": [], "marriage": None, "solo": False}
        return families[key]

    for pid in ids:
        p = people[pid]
        if p.get("father") and p.get("mother") and p["father"] in people and p["mother"] in people:
            family_for(p["father"], p["mother"])["children"].append(pid)
        for s in p.get("spouses") or []:
            if s.get("id") and s["id"] in people:
                fam = family_for(pid, s["id"])
                if not fam["marriage"] and s.get("detail"):
                    fam["marriage"] = parse_marriage(s["detail"], report["notes"])

    # A single parent with no recorded partner still needs a family record, or their
    # children have no way to point back at them.
    for pid in ids:
        p = people[pid]
        parents = [x for x in (p.get("father"), p.get("mother")) if x and x in people]
        if len(parents) == 1:
            fam = family_for(parents[0], parents[0])
            fam["solo"] = True
            if pid not in fam["children"]:
                fam["children"].append(pid)

    # ---------- sources ----------
    sites, pages = load_sources()
    registry = {s["id"]: s["title"] for s in [*sites, *pages]}

    def source_text(pid):
        p = people[pid]
        if p.get("sources"):
            return "; ".join(registry.get(s, s) for s in p["sources"])
        fallback = branches.get(p.get("branch")) or meta["defaultSource"]
        return registry.get(fallback, meta["defaultSource"])

    source_xref: dict[str, str] = {}
    for pid in ids:
        t = source_text(pid)
        if t and t not in source_xref:
            source_xref[t] = f"@S{len(source_xref) + 1}@"

    # ---------- emit ----------
    # Xrefs are sequential rather than the project's own ids, because some importers
    # still enforce the old 20-character limit. The project id is kept on every record
    # as a REFN, so the export can be matched back to the source files.
    indi_xref = {pid: f"@I{i + 1}@" for i, pid in enumerate(ids)}
    fam_xref = {k: f"@F{i + 1}@" for i, k in enumerate(families)}

    lines: list[str] = []

    def put(level, tag, payload=None):
        lines.append(f"{level} {tag}" if payload in (None, "") else f"{level} {tag} {payload}")

    def put_text(level, tag, text):
        # A payload that begins with @ would be read as a pointer; GEDCOM escapes it by
        # doubling. Newlines become CONT, which is the only continuation v7 has.
        parts = re.split(r"\r?\n", str(text))
        put(level, tag, re.sub(r"^@", "@@", parts[0]))
        for extra in parts[1:]:
            put(level + 1, "CONT", re.sub(r"^@", "@@", extra))

    put(0, "HEAD")
    put(1, "GEDC")
    put(2, "VERS", "7.0")
    put(1, "SOUR", "FAMILY_TREE")
    put_text(2, "NAME", "Family tree of Renée & Léon Bundervoet")
    put(1, "LANG", "en")
    # No HEAD.DATE on purpose: the file is committed, and a timestamp would make it
    # differ on every run even when no data changed.
    put(1, "NOTE", "Generated by tools/export_gedcom.py from data/people/*.md — regenerate rather than edit.")

    for pid in ids:
        p = people[pid]
        put(0, indi_xref[pid], "INDI")
        put(1, "REFN", pid)
        put(2, "TYPE", "project-id")

        # GEDCOM wants the surname delimited (`Jan /Van den Broucke/`), which used to
        # mean guessing where it started from a list of particles. Records now state
        # `surname`, so this is a read rather than a parse.
        if p.get("surname"):
            put_text(1, "NAME", f"{given_names(p)} /{p['surname']}/")
            put_text(2, "GIVN", given_names(p))
            put_text(2, "SURN", p["surname"])
            if p.get("nickname"):
                put_text(2, "NICK", p["nickname"])
        else:
            put_text(1, "NAME", p["name"])
            if p.get("nickname"):
                put_text(2, "NICK", p["nickname"])

        put(1, "SEX", sex[pid].upper() if sex.get(pid) else "U")

        for field, tag in (("birth", "BIRT"), ("death", "DEAT")):
            event = p.get(field)
            if not event:
                continue
            put(1, tag)
            date = gedcom_date(event.get("date"))
            if date:
                put(2, "DATE", date)
            if event.get("place"):
                put_text(2, "PLAC", event["place"])
            if event.get("raw"):
                # A date the record states in words no date syntax can express. Better
                # an honest note than a year invented to fill the field.
                put_text(2, "NOTE", f"Recorded as: {event['raw']}")
                report["unparsed_dates"].append(f"{pid} {field}: \"{event['raw']}\"")

        # `occupation` means only an occupation, so this is a straight copy. It used to
        # be a guess: the old `role` field mixed occupations with relationship labels.
        if p.get("occupation"):
            report["occupations"] += 1
            put_text(1, "OCCU", p["occupation"])

        for key, fam in families.items():
            if pid in (fam["a"], fam["b"]):
                put(1, "FAMS", fam_xref[key])
        for key, fam in families.items():
            if pid in fam["children"]:
                put(1, "FAMC", fam_xref[key])

        # Spouses who have no record of their own would vanish entirely otherwise.
        for s in p.get("spouses") or []:
            if not s.get("id"):
                detail = f" — {s['detail']}" if s.get("detail") else ""
                put_text(1, "NOTE", f"Spouse (no record of their own): {s['name']}{detail}")

        if p.get("note"):
            put_text(1, "NOTE", p["note"])

        src = source_text(pid)
        if src:
            put(1, "SOUR", source_xref[src])
            put(2, "QUAY", str(QUAY.get(p.get("confidence"), 2)))

    for key, fam in families.items():
        put(0, fam_xref[key], "FAM")
        if fam["solo"]:
            put(1, "WIFE" if sex.get(fam["a"]) == "f" else "HUSB", indi_xref[fam["a"]])
        else:
            # Whoever is known to be male takes HUSB; the other slot takes the partner.
            husb, wife = fam["a"], fam["b"]
            if sex.get(fam["b"]) == "m" or sex.get(fam["a"]) == "f":
                husb, wife = fam["b"], fam["a"]
            put(1, "HUSB", indi_xref[husb])
            put(1, "WIFE", indi_xref[wife])
        for child in fam["children"]:
            put(1, "CHIL", indi_xref[child])
        if fam["marriage"]:
            put(1, "MARR")
            if fam["marriage"]["date"]:
                put(2, "DATE", fam["marriage"]["date"])
            if fam["marriage"]["place"]:
                put_text(2, "PLAC", fam["marriage"]["place"])
            put_text(2, "NOTE", f"Recorded as: {fam['marriage']['note']}")

    for text, xref in source_xref.items():
        put(0, xref, "SOUR")
        put_text(1, "TITL", text)

    put(0, "TRLR")

    problems = _self_check(lines, ids, people)
    report["families"] = len(families)
    report["sources"] = len(source_xref)
    return lines, report, problems


def _self_check(lines, ids, people) -> list[str]:
    """Nothing here validates GEDCOM semantics, but a dangling pointer or a level that
    jumps two at once would break an import silently — and well-formed is not the same
    as faithful, so the file is also read back as if it were someone else's."""
    problems: list[str] = []
    declared = {line.split(" ")[1] for line in lines if re.match(r"^0 @", line)}
    previous_level = -1
    for i, line in enumerate(lines, start=1):
        head = line.split(" ")[0]
        if not head.isdigit():
            problems.append(f"line {i}: no level — {line}")
            continue
        level = int(head)
        if level > previous_level + 1:
            problems.append(f"line {i}: level jumps from {previous_level} to {level}")
        previous_level = level
        pointer = re.search(r" (@[A-Z0-9_]+@)$", line)
        if pointer and pointer[1] not in declared and not line.startswith("0 "):
            problems.append(f"line {i}: points at {pointer[1]}, which no record declares")
    if lines[0] != "0 HEAD":
        problems.append("file does not start with 0 HEAD")
    if lines[-1] != "0 TRLR":
        problems.append("file does not end with 0 TRLR")

    # Read the emitted file back, rebuild the family links from it alone, and check
    # they say what data/people/ says. This is what catches a HUSB and WIFE the wrong
    # way round, or a child hung off the wrong family.
    records = []
    current = None
    for line in lines:
        parts = line.split(" ")
        if parts[0] == "0":
            xref = parts[1] if len(parts) > 1 and parts[1].startswith("@") else None
            tag = parts[2] if xref and len(parts) > 2 else (parts[1] if len(parts) > 1 else None)
            current = {"xref": xref, "tag": tag, "fields": []}
            records.append(current)
        elif current:
            current["fields"].append({"tag": parts[1], "value": " ".join(parts[2:])})

    refn_of = {}
    for r in (r for r in records if r["tag"] == "INDI"):
        refn = next((f for f in r["fields"] if f["tag"] == "REFN"), None)
        if refn:
            refn_of[r["xref"]] = refn["value"]

    parsed_parents: dict[str, dict] = {}
    parsed_couples: set[str] = set()
    for fam in (r for r in records if r["tag"] == "FAM"):
        husb = next((f["value"] for f in fam["fields"] if f["tag"] == "HUSB"), None)
        wife = next((f["value"] for f in fam["fields"] if f["tag"] == "WIFE"), None)
        if husb and wife:
            parsed_couples.add("|".join(sorted([refn_of[husb], refn_of[wife]])))
        for child in (f for f in fam["fields"] if f["tag"] == "CHIL"):
            parsed_parents[refn_of[child["value"]]] = {
                "husb": refn_of.get(husb), "wife": refn_of.get(wife),
            }

    for pid in ids:
        p = people[pid]
        got = parsed_parents.get(pid, {})
        if p.get("father") and p["father"] in people and got.get("husb") != p["father"]:
            problems.append(f"round-trip: {pid}'s father reads back as {got.get('husb') or 'nobody'}, not {p['father']}")
        if p.get("mother") and p["mother"] in people and got.get("wife") != p["mother"]:
            problems.append(f"round-trip: {pid}'s mother reads back as {got.get('wife') or 'nobody'}, not {p['mother']}")
        for s in p.get("spouses") or []:
            if s.get("id") and s["id"] in people and "|".join(sorted([pid, s["id"]])) not in parsed_couples:
                problems.append(f"round-trip: the marriage of {pid} and {s['id']} is not in any family")
    individuals = sum(1 for r in records if r["tag"] == "INDI")
    if individuals != len(ids):
        problems.append(f"round-trip: {individuals} individuals in the file, {len(ids)} in the data")
    return problems
