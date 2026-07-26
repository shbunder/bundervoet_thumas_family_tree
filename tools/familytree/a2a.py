"""A2A as XML — the same records the JSON API serves, in the form that can be had in bulk.

Open Archives publishes every act three ways, and until now this project only used the
most expensive one. `records/show` returns one act per HTTP request; at the four requests
a second the venue permits, the ~30 million Belgian person-mentions behind it are about a
month of continuous fetching, and that is the arithmetic that puts a province out of
reach.

The other two routes serve the identical payload:

    BULK      https://oa-export.s3.nl-ams.scw.cloud/xml/<archive>.xml.gz
              one gzipped `<A2ACollection>` holding every record the archive has. Lommel
              is 16,368 acts in a 1.4 MB download.
    OAI-PMH   http://api.openarch.nl/oai-pmh/?verb=ListRecords&metadataPrefix=oai_a2a
              150 full records per request, paged by resumption token. Measured at ~30
              acts a second against ~3 for the per-act endpoint.

Both hand back `<a2a:A2A>` elements, which is why one reader serves them both.

WHAT MAKES THIS SAFE TO MIX WITH THE HARVESTED CORPUS. The JSON API is this same XML
rendered by a fixed convention — attributes become `@name` keys, an element carrying both
an attribute and a value becomes `{"@attr": …, "$": value}` — which `corpus.unwrap_annotated`
already knows about, because Lommel's annotated place names forced it to. `to_json` below
reproduces that convention rather than inventing a second one, so a bulk-read act and an
API-read act normalise to the same `Act`, and `tools/tests/test_tools.py` pins that they do.

The act id is the same on both sides too: the API's identifier is the record's own
`RecordGUID` with its braces stripped and lower-cased. That is what lets a bulk harvest
deduplicate against acts already fetched one at a time, instead of storing everything twice.
"""

from __future__ import annotations

import re
from typing import Iterator
from xml.etree import ElementTree as ET

A2A = "{http://Mindbus.nl/A2A}"
OAI = "{http://www.openarchives.org/OAI/2.0/}"

# The API strips the namespace prefix from every tag — `PersonNameFirstName`, not
# `a2a:PersonNameFirstName` — so this reader does the same. The braces form is what
# ElementTree gives us.
_NS = re.compile(r"^\{[^}]*\}")


def _tag(elem) -> str:
    return _NS.sub("", elem.tag)


def to_json(elem):
    """One A2A element, in the shape `records/show` returns it.

    The convention is not invented here — it is read off the API's own output, and the
    three cases below are all of it:

      text only                    <Place>Lommel</Place>            -> "Lommel"
      text plus an attribute       <Place Remark="x">Lommel</Place> -> {"@Remark": "x", "$": "Lommel"}
      children                     <PersonName><First>…</First></>  -> {"First": …}

    A tag that occurs more than once inside its parent becomes a list, and one that occurs
    once stays bare — which is exactly the irregularity `corpus._as_list` exists to absorb.
    Reproducing it, rather than always emitting a list, is deliberate: the point is that
    nothing downstream can tell which route an act arrived by.
    """
    out: dict = {f"@{_NS.sub('', k)}": v for k, v in elem.attrib.items()}
    children = list(elem)
    if not children:
        text = (elem.text or "").strip()
        if not out:
            # A genuinely empty element is absent, not "". `(src.get("SourcePlace") or {})`
            # in corpus.py reads a missing value through `or`, and an empty string travels
            # that path safely while an empty dict would claim the element was there.
            return text or None
        if text:
            out["$"] = text
        return out
    for child in children:
        key = _tag(child)
        value = to_json(child)
        if key in out:
            if not isinstance(out[key], list):
                out[key] = [out[key]]
            out[key].append(value)
        else:
            out[key] = value
    return out


def act_id(archive: str, record: dict, fallback: str | None = None) -> str | None:
    """The id this act is stored under — identical to the one the JSON API reports.

    `RecordGUID` is `{4CC17044-D32A-…}` and the API's identifier is `4cc17044-d32a-…`, so
    the two agree once the braces come off and the case is folded. Verified against a full
    OAI page: 150 of 150 headers matched their record's own GUID.

    `fallback` is the OAI header's identifier, used when a record carries no GUID. Without
    an id an act cannot be deduplicated, so it is dropped rather than stored twice.
    """
    guid = ((record.get("Source") or {}).get("RecordGUID") or "").strip()
    if guid:
        return f"{archive}:{guid.strip('{}').lower()}"
    if fallback:
        return fallback if ":" in fallback else f"{archive}:{fallback}"
    return None


def read_acts(fileobj, archive: str, archive_org: str | None = None) -> Iterator[dict]:
    """Every act in an A2A document, streamed, in the harvest's stored row shape.

    Streamed rather than parsed whole because these files do not fit in memory: Lommel is
    28 MB of XML uncompressed and Aalst's export is a 273 MB download, which is several
    gigabytes expanded. `iterparse` plus clearing each element as it is consumed keeps the
    working set at one record however large the archive is.

    Handles both documents this project fetches — a bulk `<A2ACollection>` and an OAI-PMH
    `ListRecords` page — because in both the unit is an `<a2a:A2A>` element. An OAI record
    deleted upstream carries a header and no metadata, and simply yields nothing.
    """
    identifier: str | None = None
    for event, elem in ET.iterparse(fileobj, events=("end",)):
        if elem.tag == f"{OAI}identifier":
            identifier = (elem.text or "").strip() or None
            continue
        if elem.tag != f"{A2A}A2A":
            continue
        record = to_json(elem)
        rid = act_id(archive, record if isinstance(record, dict) else {}, identifier)
        identifier = None
        # Clearing is what makes this streaming rather than a slow way to run out of
        # memory. The element is finished with either way, so it happens before the
        # early return as well as after.
        elem.clear()
        if not rid or not isinstance(record, dict):
            continue
        yield {
            "id": rid,
            "archive": archive,
            "archive_org": archive_org,
            "record": record,
        }
