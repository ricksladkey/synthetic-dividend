#!/usr/bin/env python3
"""Merge continuation lines that contain only a string literal into the previous line,
and reduce excessive blank lines inside functions/classes.

This targets tests/test_volatility_alpha_synthetic.py and tests/test_cpi_fetcher.py.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def merge_continuation_literals(path: Path):
    changed = False
    lines = path.read_text(encoding="utf8").splitlines()
    out = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        if i + 1 < len(lines):
            next_ln = lines[i + 1]
            # if current line ends with a comma and next line is an indented string literal
            if ln.rstrip().endswith(",") and re.match(r"^\s*['\"]", next_ln.lstrip()):
                # merge: remove leading whitespace from next_ln and append to ln
                merged = ln.rstrip() + " " + next_ln.strip()
                out.append(merged)
                i += 2
                changed = True
                continue
        out.append(ln)
        i += 1
    if changed:
        path.write_text("\n".join(out) + "\n", encoding="utf8")
    return changed


def collapse_excess_blank_lines(path: Path, max_blank=2):
    changed = False
    lines = path.read_text(encoding="utf8").splitlines()
    out = []
    blank = 0
    for ln in lines:
        if ln.strip() == "":
            blank += 1
        else:
            if blank > max_blank:
                out.extend([""] * max_blank)
                changed = True
            else:
                out.extend([""] * blank)
            blank = 0
            out.append(ln)
    if blank:
        if blank > max_blank:
            out.extend([""] * max_blank)
            changed = True
        else:
            out.extend([""] * blank)
    if changed:
        path.write_text("\n".join(out) + "\n", encoding="utf8")
    return changed


changed_any = False
p1 = ROOT / "tests" / "test_volatility_alpha_synthetic.py"
if p1.exists():
    merged = merge_continuation_literals(p1)
    changed_any = changed_any or merged
p2 = ROOT / "tests" / "test_cpi_fetcher.py"
if p2.exists():
    # collapse to max 1 blank inside classes; globally collapse to 2
    merged2 = collapse_excess_blank_lines(p2, max_blank=1)
    changed_any = changed_any or merged2

print("Merged/normalized:", changed_any)
