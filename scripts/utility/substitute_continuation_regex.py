#!/usr/bin/env python3
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "tests" / "test_volatility_alpha_synthetic.py"
text = path.read_text(encoding="utf8")
pattern = re.compile(r",\n(\s*)([\"'].*?[\"']\s*\)?)", re.S)
new, n = pattern.subn(lambda m: ", " + m.group(2).strip(), text)
if n:
    path.write_text(new, encoding="utf8")
print("replacements=", n)
