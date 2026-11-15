"""Convert percent-format Python sources (labs/_src/*.py) into clean notebooks.

    uv run python _tools/py2nb.py                 # all sources
    uv run python _tools/py2nb.py D1_1_two_providers  # one source

Cell markers:
    # %% [markdown]   -> markdown cell; leading "# " is stripped from each line
    # %%              -> code cell

Exercise regions (code cells only):
    # BEGIN SOLUTION
    ...reference code...
    # END SOLUTION
A line "# @header" in a markdown cell becomes the lab's title, session, summary, tasks with
minutes and stretch item, read from course.json, so the notebook always matches the manifest.

Student notebooks (labs/*.ipynb) get a placeholder that raises NotImplementedError;
solution notebooks (labs/solutions/*.ipynb) keep the code, minus the markers.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

LABS = Path(__file__).resolve().parents[1]
SRC = LABS / "_src"
COURSE = LABS.parent / "course.json"


def header(stem: str) -> list[str]:
    course = json.loads(COURSE.read_text(encoding="utf-8"))
    for d_i, day in enumerate([d for d in course["days"] if d.get("kind") == "day"], start=1):
        for s_i, sess in enumerate(day["sessions"], start=1):
            lab = sess.get("lab") or {}
            if Path(lab.get("href", "")).stem == stem:
                lines = [f"# Lab {lab['id']} · {lab['title']}", "",
                         f"Day {d_i} · Session {s_i} ({sess['title']}) · {lab['minutes']} min.", "",
                         lab["summary"], "", "**Tasks**"]
                lines += [f"- [ ] {st['text']} · {st['minutes']} min" for st in lab["steps"]]
                lines.append(f"- [ ] ✱ Stretch · {lab['stretch']}")
                return ["# " + l if l else "#" for l in lines]
    raise SystemExit(f"no lab in course.json has the href {stem}.ipynb")


def strip_solutions(lines: list[str], student: bool) -> list[str]:
    out, inside = [], False
    for line in lines:
        tag = line.strip()
        if tag == "# BEGIN SOLUTION":
            inside = True
            if student:
                indent = line[: len(line) - len(line.lstrip())]
                out.append(f"{indent}# ✏️ YOUR CODE HERE")
                out.append(f'{indent}raise NotImplementedError("✏️ Exercise: write your solution here")')
            continue
        if tag == "# END SOLUTION":
            inside = False
            continue
        if not (inside and student):
            out.append(line)
    return out


def convert(src: Path, student: bool) -> Path:
    cells, kind, buf = [], None, []

    def flush():
        if kind is None:
            return
        lines = buf[:]
        while lines and not lines[-1].strip():
            lines.pop()
        while lines and not lines[0].strip():
            lines.pop(0)
        if not lines:
            return
        if kind == "markdown":
            lines = [l[2:] if l.startswith("# ") else l.lstrip("#") for l in lines]
        else:
            lines = strip_solutions(lines, student)
        source = [l + "\n" for l in lines]
        source[-1] = source[-1].rstrip("\n")
        cell = {"cell_type": kind, "metadata": {}, "source": source}
        if kind == "code":
            cell.update(execution_count=None, outputs=[])
        cells.append(cell)

    text = src.read_text(encoding="utf-8").splitlines()
    expanded = []
    for line in text:
        expanded.extend(header(src.stem) if line.strip() == "# @header" else [line])
    for line in expanded:
        if line.startswith("# %%"):
            flush()
            kind, buf = ("markdown" if "[markdown]" in line else "code"), []
        else:
            buf.append(line)
    flush()

    nb = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"},
            "colab": {"provenance": []},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    for i, c in enumerate(nb["cells"]):
        c["id"] = f"{src.stem[:20].lower().replace('_', '-')}-{i:03d}"
    out_dir = LABS if student else LABS / "solutions"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / f"{src.stem}.ipynb"
    out.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return out


if __name__ == "__main__":
    names = sys.argv[1:]
    sources = [SRC / f"{n}.py" for n in names] if names else sorted(SRC.glob("*.py"))
    for s in sources:
        for student in (True, False):
            print("wrote", convert(s, student).relative_to(LABS))
