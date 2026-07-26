"""The family tree toolchain.

One package so that "what a person is", "what a date means" and "what counts as a
source" have a single definition rather than one per script.

HOW THE TOOLS FIND THIS. They don't have to. `uv run tools/build.py` is a script run, so
Python puts `tools/` on `sys.path` as `sys.path[0]` before the first import — and pytest
gets the same from `pythonpath = ["tools"]` in pyproject.toml. Every entry point used to
open with `sys.path.insert(0, ...)` anyway, which forced its imports below the first
statement and bought 41 `# noqa: E402` markers to silence the linter about it. Nine
copies of a line that was already true.
"""
