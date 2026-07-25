"""
A parser for the small, fixed shape of YAML the person files use — and only that shape.

Writing a hundred lines here keeps the project's "no dependencies" rule, which is what
lets the whole thing run from a clone with nothing installed.

What is supported, because it is all the records need::

    key: scalar
    key:                (nested map, one level)
      sub: scalar
    key:                (list of maps, one level)
      - sub: scalar
        sub2: scalar

Anything else is a syntax error rather than a silent misread. A parser that guesses is
worse than no parser: it would let a malformed record through, and the mistake would
surface as a missing person months later.
"""

from __future__ import annotations

import json
import re

KEY = re.compile(r"^([A-Za-z_][\w-]*):(.*)$")


class FrontmatterError(ValueError):
    """A record that does not parse. Always names the file and the line."""


def _unquote(raw: str) -> str:
    s = raw.strip()
    if s == "":
        return ""
    if len(s) > 1 and s[0] == s[-1] and s[0] in "\"'":
        body = s[1:-1]
        return body.replace('\\"', '"').replace("\\\\", "\\") if s[0] == '"' else body.replace("''", "'")
    return s


def parse(text: str, filename: str = "<string>") -> tuple[dict, str]:
    """Return ``(data, body)`` for one frontmatter document."""
    if not text.startswith("---\n"):
        raise FrontmatterError(f"{filename}: does not start with a --- frontmatter block")
    end = text.find("\n---\n", 3)
    if end == -1:
        raise FrontmatterError(f"{filename}: frontmatter block is never closed with ---")

    head = text[4 : end + 1]
    body = text[end + 5 :].lstrip("\n").rstrip()

    data: dict = {}
    pending: set[str] = set()  # keys whose shape the first child line will decide
    current_key: str | None = None
    current_item: dict | None = None

    for lineno, line in enumerate(head.split("\n"), start=1):
        if not line.strip() or line.strip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        trimmed = line.strip()

        if indent == 0:
            m = KEY.match(trimmed)
            if not m:
                raise FrontmatterError(f'{filename}: line {lineno} is not "key: value" — {json.dumps(line)}')
            key, rest = m.group(1), m.group(2)
            if rest.strip() == "":
                current_key, current_item = key, None
                pending.add(key)
                data[key] = None
            else:
                data[key] = _unquote(rest)
                pending.discard(key)
                current_key, current_item = None, None
            continue

        if not current_key:
            raise FrontmatterError(f"{filename}: line {lineno} is indented but belongs to nothing")

        if trimmed.startswith("- "):
            if current_key in pending:
                data[current_key] = []
                pending.discard(current_key)
            if not isinstance(data[current_key], list):
                raise FrontmatterError(f'{filename}: line {lineno} mixes a list into the map "{current_key}"')
            item = trimmed[2:]
            m = KEY.match(item)
            if m:
                # A list of maps, like spouses.
                current_item = {m.group(1): _unquote(m.group(2))}
                data[current_key].append(current_item)
            else:
                # A list of plain values, like source ids.
                current_item = None
                data[current_key].append(_unquote(item))
            continue

        m = KEY.match(trimmed)
        if not m:
            raise FrontmatterError(f'{filename}: line {lineno} is not "key: value" — {json.dumps(line)}')
        if isinstance(data[current_key], list):
            if current_item is None:
                raise FrontmatterError(f"{filename}: line {lineno} has no list item to belong to")
            current_item[m.group(1)] = _unquote(m.group(2))
        else:
            if current_key in pending:
                data[current_key] = {}
                pending.discard(current_key)
            data[current_key][m.group(1)] = _unquote(m.group(2))

    for key in pending:
        raise FrontmatterError(f'{filename}: "{key}" has no value and no indented block')
    return data, body


# Quote only when the value would otherwise be misread. Leaving ordinary prose
# unquoted is what makes these files readable, which is the point of the format.
_NEEDS_QUOTING = (
    re.compile(r"^[\s>|&*!%@`{}\[\]#]"),
    re.compile(r": "),
    re.compile(r"\s$"),
    re.compile(r"^(true|false|null|yes|no|on|off|~)$", re.I),
    re.compile(r"^-?\d+(\.\d+)?$"),
)


def _scalar(value) -> str:
    s = str(value)
    if s == "" or any(p.search(s) for p in _NEEDS_QUOTING):
        return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return s


def stringify(data: dict, body: str = "", key_order: list[str] | None = None) -> str:
    """Write a record back out, fields in the project's canonical order."""
    key_order = key_order or []
    keys = [k for k in key_order if k in data] + [k for k in data if k not in key_order]
    out = ["---"]
    for key in keys:
        value = data[key]
        if value is None or value == "":
            continue
        if isinstance(value, list):
            if not value:
                continue
            out.append(f"{key}:")
            for item in value:
                if isinstance(item, dict):
                    entries = [(k, v) for k, v in item.items() if v is not None and v != ""]
                    for i, (k, v) in enumerate(entries):
                        out.append(f"  {'- ' if i == 0 else '  '}{k}: {_scalar(v)}")
                else:
                    out.append(f"  - {_scalar(item)}")
        elif isinstance(value, dict):
            entries = [(k, v) for k, v in value.items() if v is not None and v != ""]
            if not entries:
                continue
            out.append(f"{key}:")
            for k, v in entries:
                out.append(f"  {k}: {_scalar(v)}")
        else:
            out.append(f"{key}: {_scalar(value)}")
    out += ["---", ""]
    if body and body.strip():
        out += [body.strip(), ""]
    return "\n".join(out)
