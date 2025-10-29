"""Strip trailing whitespace from Python files under src/ and tests/.
Run from repository root.
"""

import os


def strip_dir(root):
    changed = 0
    for dirpath, dirnames, filenames in os.walk(root):
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            path = os.path.join(dirpath, fn)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    orig = f.read()
            except Exception:
                continue
            lines = orig.splitlines()
            new = "\n".join([l.rstrip() for l in lines]) + ("\n" if lines else "")
            if new != orig:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new)
                changed += 1
    return changed


if __name__ == "__main__":
    total = 0
    total += strip_dir("src")
    total += strip_dir("tests")
    print(f"stripped trailing whitespace from {total} files")
