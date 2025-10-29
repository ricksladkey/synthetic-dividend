#!/usr/bin/env python3
"""Fix over-indentation (E127) and double-underscore unused var names introduced by prior automated edits.

- For E127: remove up to 4 leading spaces on the reported line.
- For F841 where variable name starts with '__': replace '__var' with '_var' at the reported line.

Run from repo root: python scripts/fix_overindents_and_vars.py
"""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
proc = subprocess.run([
    str(ROOT / ".venv" / "Scripts" / "python.exe"),
    "-m",
    "flake8",
    "src",
    "tests",
], capture_output=True, text=True)
output = proc.stdout + proc.stderr

issue_re = re.compile(r"(?P<file>[^:]+):(?P<line>\d+):(?P<col>\d+): (?P<code>[A-Z]\d{3}) (?P<msg>.*)")
issues_by_file = {}
for ln in output.splitlines():
    m = issue_re.match(ln)
    if not m:
        continue
    fi = Path(m.group('file'))
    line = int(m.group('line'))
    code = m.group('code')
    msg = m.group('msg')
    issues_by_file.setdefault(fi, []).append((line, code, msg))

for fi, issues in issues_by_file.items():
    if not fi.exists():
        continue
    lines = fi.read_text(encoding='utf8').splitlines()
    orig = list(lines)
    for line_no, code, msg in sorted(issues, key=lambda x: -x[0]):
        idx = line_no - 1
        if idx < 0 or idx >= len(lines):
            continue
        if code == 'E127':
            # remove up to 4 leading spaces
            lines[idx] = re.sub(r'^(\s{1,4})', '', lines[idx])
        elif code == 'F841':
            mvar = re.search(r"local variable '(?P<var>[^']+)' is assigned to", msg)
            if mvar:
                var = mvar.group('var')
                # if var starts with '__', replace with single underscore at this line
                if var.startswith('__'):
                    newvar = '_' + var.lstrip('_')
                    # replace only first occurrence on the line
                    lines[idx] = re.sub(rf"\b{re.escape(var)}\b", newvar, lines[idx], count=1)
    if lines != orig:
        fi.write_text('\n'.join(lines) + '\n', encoding='utf8')
        print(f"Patched: {fi}")

print('Done')
