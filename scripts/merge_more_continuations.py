#!/usr/bin/env python3
"""Merge more continuation lines where a previous line ends with a comma and next line contains only a short string literal."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "tests" / "test_volatility_alpha_synthetic.py"
if not path.exists():
    print("File not found:", path)
    raise SystemExit(1)

text = path.read_text(encoding="utf8")
lines = text.splitlines()
changed = False
out = []
i = 0
while i < len(lines):
    ln = lines[i]
    if i + 1 < len(lines):
        nxt = lines[i + 1]
        if ln.rstrip().endswith(","):
            # if next line contains a standalone string literal (possibly followed by ) or ), comment
            if re.match(r"^\s*(['\"]).*\1\s*\)?\s*$", nxt):
                # merge
                merged = ln.rstrip() + " " + nxt.strip()
                out.append(merged)
                i += 2
                changed = True
                continue
    out.append(ln)
    i += 1

if changed:
    path.write_text("\n".join(out) + "\n", encoding="utf8")
print("merged=", changed)
