# research/findings/

**Staging, not the record.** Each file here is the output of one research pass that could
not write to the tree at the time — usually because another session held the hot files
(`research/searches.jsonl`, `research/labels.jsonl`, `docs/research-log.md`,
`data/people/`).

Nothing in this directory is a fact about the tree. A finding here has **not** been
grafted, **not** been labelled with `evaluate.py label`, and **not** been logged with
`research.py log`. The validator does not read this directory and `build.py` does not
generate from it.

A file is deleted once its content has been landed properly: person files written,
searches logged with their scope, rulings labelled against `<act-id>#<pid>`, sources
registered, and a numbered section added to `docs/research-log.md`. **Landing it is the
point — a finding that stays here is a finding the project cannot cite.**
