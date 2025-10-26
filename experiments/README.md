# Experiments

This folder contains versioned snapshots of research experiment results. Each experiment is tied to a specific repository revision and documents what the algorithm produced at that point in time.

## Purpose

**Experiments vs Output:**
- `experiments/` → Versioned lab results (committed to git)
- `output/` → Sandbox/scratch space (ignored by git)

This distinction allows:
1. **Reproducibility**: Future you (or others) can see what results were produced with a specific version of the code
2. **Scientific record**: Track how algorithm changes affect results over time
3. **Sandbox freedom**: Play around in `output/` without cluttering git history

## Structure

```
experiments/
├── README.md                        # This file
├── volatility-alpha-validation/    # Formula validation dataset
│   ├── README.md                    # Analysis and findings
│   ├── generate-data.bat            # Reproduction script
│   └── volatility_alpha_table.csv   # 18 scenarios across 6 assets
├── 2025-01-25_profit-sharing/      # Experiment date + name
│   ├── README.md                    # Experiment documentation
│   ├── params.json                  # Parameters used
│   ├── results.csv                  # Raw results
│   └── charts/                      # Generated visualizations
│       └── composition.png
└── ...
```

## Current Experiments

### volatility-alpha-validation/
**Purpose**: Validate the mathematical formula `Alpha ≈ (trigger%)² / 2 × buy_count`

**Assets**: NVDA, MSTR, BTC-USD, ETH-USD, PLTR, GLD  
**Timeframes**: 1, 2, 3 years ending Oct 26, 2025  
**Key Finding**: Formula provides reliable conservative lower bound. High volatility assets show 2-3x theoretical minimum due to gap bonuses.

**Reproduce**:
```bash
cd experiments/volatility-alpha-validation
generate-data.bat
```

## Naming Convention

**Format:** `YYYY-MM-DD_experiment-name/`

Examples:
- `2025-01-25_profit-sharing-composition/`
- `2025-01-26_optimal-rebalancing-phase1/`
- `2025-02-15_nvda-crash-analysis/`

## What to Include

Each experiment folder should contain:

### 1. README.md (required)
Documents:
- Research question
- Hypothesis
- Parameters used
- Key findings
- Git commit hash
- Date run

### 2. params.json (recommended)
Machine-readable parameters:
```json
{
  "ticker": "NVDA",
  "start_date": "2022-01-01",
  "end_date": "2024-12-31",
  "profit_sharing_range": [-0.25, 1.25],
  "step": 0.05,
  "commit": "abc123def"
}
```

### 3. Results
- CSV files with raw data
- Charts/visualizations
- Summary statistics
- Analysis notebooks

### 4. Code Snapshot (optional)
If the experiment used custom parameters or modifications not in the main codebase, include:
- Script copy
- Config files
- Custom modifications

## Example Experiment README

```markdown
# Profit Sharing Composition Analysis

**Date:** 2025-01-25  
**Commit:** `35aa755`  
**Script:** `src/research/profit_sharing_composition.py`

## Research Question
How do different profit-sharing ratios (-25% to +125%) affect holdings composition over a 3-year period?

## Hypothesis
- Negative ratios should accumulate shares
- High ratios (>100%) should deplete core holdings
- Composition should vary significantly during drawdowns

## Parameters
- Ticker: NVDA
- Period: 2022-01-01 to 2024-12-31
- Profit sharing: -25% to +125% (5% steps)
- Rebalance threshold: 10%
- Initial capital: $100,000

## Key Findings
1. All profit-sharing ratios converged to identical final values
2. NVDA's strong uptrend meant all buyback stacks unwound
3. Need to test with period ending in drawdown

## Files
- `results_summary.csv` - Final values for each ratio
- `charts/composition_nvda.png` - 4-panel visualization
- `params.json` - Full parameter set

## Next Steps
- Re-run with 2021-2024 (includes crash)
- Test with VOO for moderate volatility
- Examine intra-period composition differences
```

## Best Practices

### Do:
✅ Run experiments from a clean git state (committed code)  
✅ Record git commit hash in experiment README  
✅ Include date in folder name for chronological sorting  
✅ Document unexpected findings  
✅ Keep raw data (CSV) alongside visualizations  

### Don't:
❌ Modify experiment results after the fact  
❌ Cherry-pick successful runs (document failures too)  
❌ Use experiments/ for in-progress work (use output/ instead)  
❌ Commit huge files (>10MB) - use Git LFS or summarize  

## Workflow

### Quick sandbox test:
```bash
# Results go to output/ (ignored)
python src/research/profit_sharing_composition.py
```

### Documented experiment:
```bash
# 1. Commit code changes
git add -A
git commit -m "Add new analysis feature"

# 2. Create experiment folder
mkdir experiments/2025-01-25_my-experiment

# 3. Run with output to experiments/
python src/research/profit_sharing_composition.py --output experiments/2025-01-25_my-experiment/

# 4. Document findings
# Create experiments/2025-01-25_my-experiment/README.md

# 5. Commit results
git add experiments/2025-01-25_my-experiment/
git commit -m "Add experiment: my-experiment results"
```

## Migration Notes

Existing results that should be migrated to experiments/:
- Any CSV files in root matching `*_results.csv`, `research_*.csv`, `volatility_alpha_*.csv`
- Charts in `output/` that represent important findings
- Analysis notebooks with documented conclusions

These can be organized into retroactive experiment folders with appropriate dates.
