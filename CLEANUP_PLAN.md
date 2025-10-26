# Root Directory Cleanup Plan
**Date**: October 26, 2025  
**Status**: Proposed

## Analysis Summary

Total files in root: ~60 files/folders
- Production code: src/, tests/ ✅ Keep
- Documentation: Multiple .md files (some redundant)
- Scripts: .bat files, .py demos, .ps1 utilities
- Build artifacts: htmlcov/, .pytest_cache/, output/
- Config: pyproject.toml, .gitignore, etc. ✅ Keep

---

## Cleanup Actions

### 🗑️ DELETE - Obsolete/Redundant Files

**Checkpoint files (3 files) - OBSOLETE**
- `CHECKPOINT.md` - 377 lines, verification doc from Oct 25
- `CHECKPOINT_SUMMARY.md` - 249 lines, summary from Oct 25
- Reason: Point-in-time verification, no longer needed

**Legacy demo/test scripts (3 files) - MOVE TO EXAMPLES**
- `demo_dividends.py` - Should be in examples/ or tests/
- `test_dividends.py` - Ad-hoc test, should be in tests/ or deleted
- Reason: Clutter in root, belong in proper folders

**Generated artifacts (1 file) - DELETE**
- `GLD_volatility_alpha.png` - Generated chart
- Reason: Can be regenerated, should be in output/ or gitignored

**Comparison results (1 file) - MOVE TO DOCS**
- `COMPARISON_RESULTS.md` - Historical comparison data
- Reason: Should be in theory/ or experiments/

**Research plan (1 file) - CONSOLIDATE**
- `RESEARCH_PLAN.md` - May be obsolete or mergeable into README
- Reason: Evaluate if still relevant

**Income roadmap (1 file) - MOVE**
- `INCOME_GENERATION_ROADMAP.md` - Specific feature roadmap
- Reason: Should be in theory/ with other conceptual docs

**Profit sharing analysis (1 file) - MOVE**
- `PROFIT_SHARING_ANALYSIS_RESULTS.md` - Research results
- Reason: Should be in experiments/ or theory/

**Test analysis (1 file) - EVALUATE**
- `TEST_ANALYSIS.md` - Test documentation
- Reason: Determine if still relevant or merge into README

---

### 📁 MOVE - Reorganize into Better Locations

**Move to theory/**
- `INCOME_GENERATION_ROADMAP.md` → `theory/INCOME_GENERATION_ROADMAP.md`
- `PROFIT_SHARING_ANALYSIS_RESULTS.md` → `theory/PROFIT_SHARING_ANALYSIS_RESULTS.md`
- `COMPARISON_RESULTS.md` → `theory/COMPARISON_RESULTS.md` (or experiments/)

**Move to experiments/**
- Consider: Some of these might fit better in experiments/

**Move to examples/**
- `demo_dividends.py` → `examples/demo_dividends.py`

**Move to docs/** (create if needed)
- `QUICK_REFERENCE.md` - Quick reference guide
- `EXAMPLES.md` - Examples and usage
- `CONTRIBUTORS.md` - Contributor guide
- `HOUSEKEEPING.md` - Project maintenance guide

**Move to scripts/** (create if needed)
- `generate-system-prompt.ps1`
- `generate-system-prompt.sh`
- `dev.ps1`

---

### ✅ KEEP - Essential Files

**Root documentation (keep in root)**
- `README.md` - Main entry point ✅
- `TODO.md` - Active task list ✅
- `CODING_ASSISTANCE_MANIFESTO.md` - Project meta-doc ✅
- `LICENSE` - Legal ✅
- `INSTALLATION.md` - Setup instructions ✅

**Configuration files**
- `pyproject.toml` - Python project config ✅
- `requirements.txt` - Dependencies ✅
- `requirements-dev.txt` - Dev dependencies ✅
- `mypy.ini` - Type checker config ✅
- `.gitignore` - Git config ✅
- `.flake8` - Linter config ✅
- `MANIFEST.in` - Package manifest ✅
- `Makefile` - Build automation ✅

**Batch scripts (user-facing tools)**
- `run-tests.bat` - Run test suite ✅
- `run-model.bat` - Run backtests ✅
- `calc-orders.bat` - Calculate orders ✅
- `analyze-volatility-alpha.bat` - Analyze alpha ✅
- `compare-algorithms.bat` - Compare strategies ✅
- `compare-strategies.bat` - Strategy comparison ✅
- `compare-table.bat` - Comparison table ✅
- `test-*.bat` (7 files) - Test runners ✅

**Directories**
- `src/` - Source code ✅
- `tests/` - Test suite ✅
- `theory/` - Theory documents ✅
- `experiments/` - Research experiments ✅
- `research/` - Research scripts ✅
- `.github/` - GitHub config ✅
- `.venv/` - Virtual environment ✅
- `.pytest_cache/` - Test cache ✅
- `htmlcov/` - Coverage reports ✅
- `output/` - Generated outputs ✅

---

## Proposed New Structure

```
synthetic-dividend/
├── README.md                          # Main entry point
├── TODO.md                            # Active tasks
├── INSTALLATION.md                    # Setup guide
├── LICENSE                            # Legal
├── CODING_ASSISTANCE_MANIFESTO.md     # Meta-documentation
│
├── docs/                              # ← NEW: User documentation
│   ├── QUICK_REFERENCE.md
│   ├── EXAMPLES.md
│   ├── CONTRIBUTORS.md
│   └── HOUSEKEEPING.md
│
├── scripts/                           # ← NEW: Utility scripts
│   ├── generate-system-prompt.ps1
│   ├── generate-system-prompt.sh
│   └── dev.ps1
│
├── examples/                          # ← NEW: Example code
│   └── demo_dividends.py
│
├── *.bat                              # User-facing tools (keep in root)
│
├── src/                               # Source code
├── tests/                             # Test suite
├── theory/                            # Theory documents
├── experiments/                       # Research experiments
├── research/                          # Research scripts
│
├── output/                            # Generated files (gitignored)
├── htmlcov/                           # Coverage reports (gitignored)
├── .venv/                             # Virtual env (gitignored)
│
└── [config files]                     # pyproject.toml, .gitignore, etc.
```

---

## Action Items

### Phase 1: Create New Folders
- [ ] Create `docs/` folder
- [ ] Create `scripts/` folder  
- [ ] Create `examples/` folder

### Phase 2: Delete Obsolete Files
- [ ] Delete `CHECKPOINT.md`
- [ ] Delete `CHECKPOINT_SUMMARY.md`
- [ ] Delete `test_dividends.py` (or move to tests/)
- [ ] Delete `GLD_volatility_alpha.png` (add to .gitignore pattern)

### Phase 3: Move Files
- [ ] Move docs to `docs/`
- [ ] Move scripts to `scripts/`
- [ ] Move examples to `examples/`
- [ ] Move theory/analysis docs appropriately

### Phase 4: Update References
- [ ] Update README.md links
- [ ] Update TODO.md references
- [ ] Update any batch files that reference moved files
- [ ] Update .gitignore if needed

### Phase 5: Cleanup output/
- [ ] Review output/ contents
- [ ] Move or delete as appropriate
- [ ] Ensure .gitignore covers generated files

---

## Questions to Resolve

1. **RESEARCH_PLAN.md** - Still relevant? Merge into README or keep separate?
2. **TEST_ANALYSIS.md** - Still useful? Update or archive?
3. **research/** folder batch files - Keep structure or reorganize?
4. **output/** system-prompt files - Part of build process or should be in docs/?
5. **Batch files** - 14 total - any that can be consolidated or moved to scripts/?

---

## Risk Assessment

**Low Risk** (safe to execute):
- Deleting checkpoint files (no dependencies)
- Moving demo files to examples/
- Deleting generated PNG files
- Creating new folders

**Medium Risk** (verify first):
- Moving documentation (check for links)
- Moving scripts (check for references in batch files)
- Moving theory/analysis files (check cross-references)

**High Risk** (careful review needed):
- Deleting any .bat files (user-facing tools)
- Changing folder structure of src/tests/theory/
- Modifying config files

---

## Next Steps

1. **Review this plan** - Get approval for proposed changes
2. **Execute Phase 1** - Create new folders (safe)
3. **Execute Phase 2** - Delete obsolete files (safe)
4. **Execute Phase 3** - Move files (medium risk, reversible)
5. **Execute Phase 4** - Update references (critical)
6. **Test** - Ensure all batch files and imports still work
7. **Commit** - Document cleanup in commit message
