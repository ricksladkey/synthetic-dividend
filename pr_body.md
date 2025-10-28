Summary:
Prefer registered Asset providers via AssetRegistry; fallback to a small yfinance-backed cache. Fixed a corrupted `src/data/asset.py` and added a backtest kwargs compatibility shim.

Files:
- src/data/asset.py
- src/models/backtest.py

Tests:
Locally ran full test suite using the project .venv:
C:/build/synthetic-dividend/.venv/Scripts/python.exe -m pytest -q (205 passed)

Checklist:
- [x] Branch created from origin/main
- [x] Unit tests passed locally (full suite)
- [ ] CI green on latest push
- [ ] Lint & typecheck (optional)
- [ ] Documentation updated if needed

How to test locally:
Use the repo .venv and run:
C:/build/synthetic-dividend/.venv/Scripts/python.exe -m pytest -q

Notes:
- This is a focused refactor to isolate asset-provider changes for review.
- If CI shows failures, I'll iterate in this branch and push fixes; the Draft PR will be updated automatically.
