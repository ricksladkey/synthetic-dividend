#!/usr/bin/env python3
"""Auto-fix safe lexical issues across the repo.

Fixes performed:
- Convert constant f-strings (f"..." or f'...') that contain no braces to normal strings
- Trim trailing whitespace on each line
- Ensure file ends with exactly one newline

This script edits files under `src/` and `tests/` only.

Run from repo root: python scripts/auto_fix_lexical.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET_DIRS = [ROOT / "src", ROOT / "tests"]

# Regex to find f-strings (simple, conservative). Captures the quote char and the body.
FSTRING_RE = re.compile(
    r"(?P<prefix>\b)(?P<f>[fF])(?P<quote>['\"])(?P<body>(?:[^\\]|\\.)*?)(?P=quote)"
)

files_changed = []
for base in TARGET_DIRS:
    if not base.exists():
        continue
    for path in base.rglob("*.py"):
        try:
            text = path.read_text(encoding="utf8")
        except Exception:
            continue
        original = text
        changed = False

        # 1) Convert constant f-strings with no braces
        def replace_f(match):
            f = match.group("f")
            quote = match.group("quote")
            body = match.group("body")
            # if there are braces, skip
            if "{" in body or "}" in body:
                return match.group(0)
            # else return normal string with same quoting
            return match.group("prefix") + quote + body + quote

        text2 = FSTRING_RE.sub(replace_f, text)
        if text2 != text:
            text = text2
            changed = True

        # 2) Trim trailing whitespace on each line
        lines = [re.sub(r"[ \t]+$", "", ln) for ln in text.splitlines()]
        # Ensure one trailing newline
        new_text = "\n".join(lines) + "\n"
        if new_text != text:
            text = new_text
            changed = True

        if changed and text != original:
            path.write_text(text, encoding="utf8")
            files_changed.append(str(path.relative_to(ROOT)))

print(f"Files modified: {len(files_changed)}")
for p in files_changed:
    print(p)
