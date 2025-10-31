#!/usr/bin/env python3
"""Apply targeted lexical fixes using flake8 output.

Fixes implemented:
- E402: add "# noqa: E402" to `from src.` imports when file contains sys.path.insert earlier
- F841: prefix unused local variable with underscore at the exact reported line
- E226: add spaces around binary operators on reported line (simple heuristic)
- E128: increase leading indent by 4 spaces on reported continuation lines

This script runs flake8, parses issues, and applies fixes in-place for files under src/ and tests/.

Run from repo root: python scripts/auto_fix_flake_issues.py
"""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Run flake8 and capture output (do not fail on non-zero)
proc = subprocess.run(
    [
        str(ROOT / ".venv" / "Scripts" / "python.exe"),
        "-m",
        "flake8",
        "src",
        "tests",
    ],
    capture_output=True,
    text=True,
)
output = proc.stdout + proc.stderr

issue_re = re.compile(
    r"(?P<file>[^:]+):(?P<line>\d+):(?P<col>\d+): (?P<code>[A-Z]\d{3}) (?P<msg>.*)"
)
issues_by_file = {}
for ln in output.splitlines():
    m = issue_re.match(ln)
    if not m:
        continue
    fi = Path(m.group("file"))
    line = int(m.group("line"))
    code = m.group("code")
    msg = m.group("msg")
    issues_by_file.setdefault(fi, []).append((line, code, msg))

print(f"Found issues in {len(issues_by_file)} files")

for fi, issues in issues_by_file.items():
    if not fi.exists():
        continue
    lines = fi.read_text(encoding="utf8").splitlines()
    orig_lines = list(lines)
    # Sort issues descending by line to avoid shifting issues
    for line_no, code, msg in sorted(issues, key=lambda x: -x[0]):
        idx = line_no - 1
        if idx < 0 or idx >= len(lines):
            continue
        line = lines[idx]
        if code == "E402":
            # If file modifies sys.path earlier, append noqa to this import line to silence E402
            earlier = "\n".join(lines[:idx])
            if "sys.path.insert" in earlier and "noqa" not in line:
                # Append noqa for E402 to any import line after sys.path.insert
                if line.strip().startswith("from ") or line.strip().startswith("import "):
                    lines[idx] = line + "  # noqa: E402"
        elif code == "F841":
            # extract variable name
            mvar = re.search(r"local variable '(?P<var>[^']+)' is assigned to", msg)
            if mvar:
                var = mvar.group("var")
                # Only modify exact assignment at this line if present
                assign_re = re.compile(rf"^(?P<indent>\s*){re.escape(var)}(?P<rest>\s*[=:\(].*)$")
                massign = assign_re.match(line)
                if massign:
                    indent = massign.group("indent")
                    rest = massign.group("rest")
                    newvar = "_" + var
                    lines[idx] = f"{indent}{newvar}{rest}"
        elif code == "E226":
            # Add spaces around simple binary operators on this line (heuristic)
            new = line
            # Avoid touching lines that appear to be comments or contain '==' '>=' '<='
            if "==" in line or ">=" in line or "<=" in line or "!=" in line or "->" in line:
                continue
            # Replace sequences like 'a+b' -> 'a + b'
            new2 = re.sub(r"(?P<a>\S)(?P<op>[+\-*/%])(?P<b>\S)", r"\g<a> \g<op> \g<b>", new)
            # Repeat until stable
            while new2 != new:
                new = new2
                new2 = re.sub(r"(?P<a>\S)(?P<op>[+\-*/%])(?P<b>\S)", r"\g<a> \g<op> \g<b>", new)
            lines[idx] = new
        elif code == "E128":
            # Increase indent by 4 spaces for this continuation line
            lines[idx] = "    " + line
    if lines != orig_lines:
        fi.write_text("\n".join(lines) + "\n", encoding="utf8")
        print(f"Patched: {fi}")

print("Done.")
