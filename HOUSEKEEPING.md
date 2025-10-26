# Project Housekeeping Guidelines
## Keeping Theory and Documentation Clean, Consistent, and Current

**Created**: October 26, 2025  
**Purpose**: Document best practices for maintaining conceptual clarity as the project evolves

---

## The Problem

As a research project grows rapidly, contradictions and inconsistencies naturally creep in:

- New features are implemented but old documentation isn't updated
- Theory documents make assumptions that later get invalidated
- README files fall behind actual capabilities
- Concepts get renamed but references remain scattered
- New insights don't get integrated into existing framework

**Result**: Conceptual mud—harder to onboard new contributors, harder to maintain mental model, harder to make coherent decisions.

---

## The Solution: Periodic Housekeeping

### When to Do Housekeeping

**Trigger events** that warrant a review:

1. **Major feature complete** (e.g., withdrawal policy, margin modes)
2. **Theory breakthrough** (e.g., income smoothing insight)
3. **Monthly milestone** (first weekend of each month)
4. **Before external sharing** (blog post, presentation, open-sourcing)
5. **After 10+ commits** (momentum builds, clarity can slip)

**Don't wait** until contradictions are overwhelming—proactive maintenance is cheaper than reactive cleanup.

---

## Housekeeping Checklist

### 1. Theory Folder Review

**Purpose**: Ensure all theory documents reflect current understanding

**Actions**:
- [ ] Read through each theory/*.md file
- [ ] Check for contradictions with recent work
- [ ] Add new concepts to relevant documents
- [ ] Update cross-references between documents
- [ ] Verify examples still match current implementation
- [ ] Update theory/README.md with new documents
- [ ] Regenerate concatenated system prompt if needed

**New Concepts to Integrate** (from this session):
- ✅ Irregular → regular payment transformation
- ✅ Sequence-of-returns risk mitigation
- ✅ "Never forced to sell at a loss" principle
- ✅ Coverage ratio as smoothing metric
- ✅ Dual bank management modes

---

### 2. Main README Update

**Purpose**: Keep project introduction current with capabilities

**Actions**:
- [ ] Update test count badge (currently 44)
- [ ] Add new features to "Key Features" section
- [ ] Update roadmap (completed → in progress → planned)
- [ ] Verify examples still work as shown
- [ ] Check that documentation links are valid
- [ ] Update "Last Updated" dates in documents

**This Session's Updates**:
- ✅ Test count: 20 → 44
- ✅ Added withdrawal policy, margin modes, income smoothing
- ✅ Updated roadmap phases
- ✅ Added new theory documents to documentation table

---

### 3. Concept Integration

**Purpose**: Weave new insights into existing framework rather than creating isolated documents

**Strategy**:

**❌ Wrong Approach**:
```
Create INCOME_SMOOTHING.md in isolation
→ Mentions nothing about INCOME_GENERATION.md
→ INCOME_GENERATION.md doesn't reference smoothing
→ Two documents with related but disconnected concepts
```

**✅ Right Approach**:
```
Create INCOME_SMOOTHING.md with clear purpose
→ Update INCOME_GENERATION.md to reference it
→ Update theory/README.md to show relationship
→ Add to learning path with proper sequencing
→ Update key concepts section to unify themes
```

**This Session**:
- ✅ Added smoothing reference to INCOME_GENERATION.md executive summary
- ✅ Added INCOME_SMOOTHING.md to theory/README.md
- ✅ Updated learning order (step 4: read smoothing after generation)
- ✅ Added key concepts section with unified themes

---

### 4. Contradiction Detection

**Purpose**: Find and resolve conflicting statements across documents

**Method**:

**Search for common conflict patterns**:
```bash
# Look for contradictory claims
grep -r "never" theory/*.md | grep -v "never sell at a loss"
grep -r "always" theory/*.md
grep -r "guaranteed" theory/*.md

# Look for outdated feature references
grep -r "20 tests" .
grep -r "Phase 1" . | grep -v "Completed"

# Look for duplicate numbering
grep "^[0-9]\+\." theory/README.md | sort | uniq -d
```

**Common contradictions to watch for**:
- Old test counts in multiple places
- Phase numbers that don't match roadmap
- Capability claims that predate implementation
- Example code that uses deprecated APIs

**This Session Found**:
- ✅ Duplicate "5." in theory/README.md (fixed: renumbered 5-10)
- ✅ Test count mismatch (20 in README vs 44 actual)
- ✅ Missing INCOME_SMOOTHING.md from theory/README.md

---

### 5. Cross-Reference Audit

**Purpose**: Ensure documents point to each other correctly

**Actions**:
- [ ] Check "Related" sections in theory documents
- [ ] Verify internal links work (theory/README.md → individual files)
- [ ] Check that new concepts reference prior work
- [ ] Ensure system prompt concatenation includes all files

**This Session**:
- ✅ Updated INCOME_GENERATION.md: Added INCOME_SMOOTHING.md to "Related"
- ✅ Updated theory/README.md: Added INCOME_SMOOTHING.md to concatenation command
- ✅ Added cross-references in both documents' executive summaries

---

### 6. Example Code Validation

**Purpose**: Ensure code examples in documentation actually work

**Actions**:
- [ ] Run example commands from README.md
- [ ] Verify output matches documented examples
- [ ] Check that import statements are current
- [ ] Test that file paths are correct

**Test from README**:
```bash
# Should work exactly as shown
python -m src.run_model NVDA 10/23/2023 10/23/2024 sd8 --qty 10000

# Should produce 44 passing tests
pytest tests/ -v
```

---

### 7. Metadata Updates

**Purpose**: Keep timestamps and status accurate

**Actions**:
- [ ] Update "Last Updated" in modified documents
- [ ] Update "Status" fields (Draft → Complete, etc.)
- [ ] Update "Phase" references (if roadmap changed)
- [ ] Check "Created" dates are accurate

**This Session**:
- ✅ INCOME_SMOOTHING.md: Last Updated: October 26, 2025
- ✅ theory/README.md: Status: Active development (Phase 3)
- ✅ Main README: Roadmap updated (Phase 1-2 complete, Phase 3 in progress)

---

## Specific Patterns to Maintain

### Pattern 1: Theory Document Structure

**Every theory document should have**:
1. Title with descriptive subtitle
2. Metadata block (Author, Created, Status, Related)
3. Executive Summary (Core Insight + key points)
4. Numbered parts with clear headings
5. Conclusion with "Document Status" and "Next Steps"
6. Last Updated date

**Consistency check**:
```bash
# All theory docs should have these sections
grep "^# " theory/*.md
grep "^## Executive Summary" theory/*.md
grep "^## Conclusion" theory/*.md
grep "Last Updated" theory/*.md
```

---

### Pattern 2: README Test Count

**Single source of truth**: `pytest tests/ -v` output

**Update locations when count changes**:
1. Main README badge: `[![Tests](https://img.shields.io/badge/tests-XX%20passing-brightgreen.svg)]`
2. Main README table: `| ✅ **pytest** | XX tests | ...`
3. TODO.md summary: "Total tests: XX"
4. Commit messages: "All XX tests passing"

**This Session**: Updated all 4 locations (20 → 44)

---

### Pattern 3: Roadmap Phase Tracking

**Phase definitions** (keep synchronized):
- Main README "Roadmap" section
- theory/README.md "Status" field
- TODO.md "Current Phase" section

**Update trigger**: When major milestone completes (e.g., withdrawal policy → Phase 2 complete)

**This Session**:
- ✅ Main README: Phase 1-2 complete, Phase 3 in progress
- ✅ theory/README.md: Phase 3 (income generation & smoothing)

---

### Pattern 4: Concept Introduction

**When introducing a new concept**:

1. **Define in dedicated section** (or create new document if substantial)
2. **Add to theory/README.md Key Concepts**
3. **Update related documents** to cross-reference
4. **Add to learning path** if foundational
5. **Update main README** if user-facing

**This Session's Example** (income smoothing):
1. ✅ Created INCOME_SMOOTHING.md (dedicated document)
2. ✅ Added to theory/README.md Key Concepts section
3. ✅ Updated INCOME_GENERATION.md to reference it
4. ✅ Added to learning path (step 4)
5. ✅ Updated main README (features, documentation table)

---

## Tools to Help

### Automated Checks

**Script to find common issues** (create `scripts/check_housekeeping.sh`):

```bash
#!/bin/bash

echo "Checking for common housekeeping issues..."

# Check test count consistency
echo "Test counts in documentation:"
grep -n "tests.*passing" README.md
grep -n "Total tests:" TODO.md

# Check for duplicate numbering in theory README
echo "Checking for duplicate numbers in theory/README.md:"
grep "^[0-9]\+\." theory/README.md | awk '{print $1}' | sort | uniq -d

# Check for "Last Updated" freshness
echo "Theory documents last updated:"
grep "Last Updated" theory/*.md

# Check for broken internal links
echo "Checking theory/*.md links:"
find theory -name "*.md" -exec grep -H "\[.*\](" {} \;

echo "Done!"
```

### Manual Review Triggers

**Set calendar reminders**:
- First weekend of each month: Full housekeeping review
- After every 10 commits: Quick contradiction check
- Before pushing to main: Example code validation

---

## Success Metrics

**Good housekeeping should result in**:

1. **Zero contradictions** across documents
2. **Current test counts** everywhere
3. **Working examples** in README
4. **Cross-referenced concepts** (no orphaned documents)
5. **Updated roadmap** (reflects actual progress)
6. **Fresh timestamps** (within 30 days for active areas)

**Red flags**:
- ⚠️ Test count mismatches across files
- ⚠️ "Last Updated" > 90 days old for core documents
- ⚠️ Roadmap "In Progress" items completed 30+ days ago
- ⚠️ New features not mentioned in README
- ⚠️ Theory concepts that don't reference related work

---

## This Session's Housekeeping Results

**Completed**:
- ✅ Updated INCOME_SMOOTHING.md with 3 new concepts (irregular→regular, sequence-of-returns, never sell at loss)
- ✅ Updated INCOME_GENERATION.md to reference smoothing
- ✅ Updated theory/README.md (added INCOME_SMOOTHING.md, fixed duplicate numbering)
- ✅ Updated main README.md (test count 44, new features, updated roadmap)
- ✅ All cross-references verified and updated
- ✅ All examples tested (44/44 tests passing)

**Contradictions Resolved**:
- ✅ Test count: 20 → 44 (unified across all documents)
- ✅ Duplicate "5." in theory/README.md → renumbered 5-10
- ✅ Missing INCOME_SMOOTHING.md reference → added to all relevant places

**Concepts Integrated**:
- ✅ Irregular → regular transformation (smoothing)
- ✅ Sequence-of-returns protection (for growth stocks)
- ✅ "Never forced to sell at a loss" principle
- ✅ Coverage ratio as smoothing metric
- ✅ Portfolio diversification benefits

---

## Lessons Learned

**From this housekeeping session**:

1. **Theory evolves faster than documentation** - need proactive updates
2. **New insights should immediately update related docs** - not just create new ones
3. **Test counts appear in 4+ places** - single source of truth needed
4. **Cross-references are fragile** - maintain bidirectional links
5. **Roadmap phases drift** - update when milestones complete, not later

**Best practices going forward**:
- Run housekeeping after every major feature (not just monthly)
- Update test counts as soon as they change
- Add new concepts to theory/README.md immediately
- Keep "Last Updated" current (part of commit for that file)
- Verify examples work before documenting them

---

## Appendix: Quick Housekeeping Command

**One-liner to check common issues**:

```bash
echo "=== Test Counts ===" && \
grep -n "test.*passing\|Total tests" README.md TODO.md && \
echo "=== Last Updated ===" && \
grep "Last Updated" theory/*.md && \
echo "=== Duplicate Numbers ===" && \
grep "^[0-9]\+\." theory/README.md | awk '{print $1}' | sort | uniq -d
```

**Expected output** (after good housekeeping):
```
=== Test Counts ===
README.md:9:[![Tests](https://img.shields.io/badge/tests-44%20passing-brightgreen.svg)]
README.md:312:| ✅ **pytest** | 44 tests | ...
TODO.md:15:Total tests: 44 (all passing ✅)

=== Last Updated ===
theory/INCOME_GENERATION.md:**Last Updated**: October 25, 2025
theory/INCOME_SMOOTHING.md:**Last Updated**: October 26, 2025
theory/README.md:**Last Updated**: October 2025

=== Duplicate Numbers ===
(no output = good!)
```

---

**Remember**: Clean theory → clear thinking → better code → faster progress

**Document this advice**: This file itself is the documentation of the advice to do periodic housekeeping!

---

**Last Updated**: October 26, 2025  
**Next Review**: November 1, 2025 (or after next major feature)
