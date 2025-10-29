#!/usr/bin/env python3
"""Final aggressive adjustments: fix remaining E128 continuation indents and E303 too many blank lines.

- For E128: set continuation line indent to prev_non_empty_indent + 8 spaces
- For E303: collapse sequences of blank lines to at most 2
"""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = str(ROOT / ".venv" / "Scripts" / "python.exe")

proc = subprocess.run([PY, "-m", "flake8", "src", "tests"], capture_output=True, text=True)
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

print(f"Final fixer found issues in {len(issues_by_file)} files")

for fi, issues in issues_by_file.items():
    if not fi.exists():
        continue
    print(f"Processing: {fi}")
    lines = fi.read_text(encoding='utf8').splitlines()
    orig = list(lines)

    # Fix E303: collapse multiple blank lines
    collapsed = []
    blank_count = 0
    for ln in lines:
        if ln.strip() == '':
            blank_count += 1
        else:
            if blank_count > 2:
                collapsed.extend([''] * 2)
            elif blank_count > 0:
                collapsed.extend([''] * blank_count)
            blank_count = 0
            collapsed.append(ln)
    # trailing blanks
    if blank_count > 0:
        if blank_count > 2:
            collapsed.extend([''] * 2)
        else:
            collapsed.extend([''] * blank_count)

    lines = collapsed

    # Now fix E128: set continuation indent to prev_non_empty_indent + 8
    for line_no, code, msg in sorted(issues, key=lambda x: x[0]):
        if code != 'E128':
            continue
        idx = line_no - 1
        if idx < 0 or idx >= len(lines):
            continue
        # find prev non-empty
        prev = idx - 1
        while prev >= 0 and lines[prev].strip() == '':
            prev -= 1
        if prev < 0:
            continue
        prev_indent = len(re.match(r"^\s*", lines[prev]).group())
        new_indent = prev_indent + 8
        stripped = lines[idx].lstrip()
        lines[idx] = ' ' * new_indent + stripped

    if lines != orig:
        fi.write_text('\n'.join(lines) + '\n', encoding='utf8')
        print(f"Patched: {fi}")

print('Final aggressive fixes applied.')
