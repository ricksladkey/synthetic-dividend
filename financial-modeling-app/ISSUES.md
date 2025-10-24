# Known Issues

## ~~Bug: optimal_rebalancing.py Returns Zero Metrics~~ [RESOLVED]

**Status:** ✅ RESOLVED (Fixed in commit 08be65e)  
**Priority:** High  
**Created:** 2025-10-24  
**Resolved:** 2025-10-24  

### Description
The `src/research/optimal_rebalancing.py` script successfully downloads historical data and runs synthetic dividend simulations, but fails to properly calculate and save final performance metrics to the output CSV. All results are written as zeros.

### Evidence
Terminal output shows successful simulation:
```
Synthetic Dividend Algorithm total volatility alpha: 5.58%  ← Calculation works!
  [OK] sd6: 0.00% return, 0 txns, 0.00% max drawdown        ← Metrics not captured
```

CSV output contains all zeros:
```csv
ticker,sd_n,total_return_pct,transaction_count,max_drawdown_pct
NVDA,6,0,0,0
NVDA,8,0,0,0
```

### Root Cause Analysis
The `run_single_backtest()` function (line 45-101 in `src/research/optimal_rebalancing.py`):
1. Calls `run_algorithm_backtest()` which performs the simulation
2. Receives a `summary` dictionary as return value
3. Extracts metrics using `summary.get("total_return_pct", 0)`
4. All `.get()` calls return the default value of 0

**Hypothesis:** The `run_algorithm_backtest()` function is not populating the `summary` dict with calculated metrics, or is using different key names than expected.

### Files Affected
- `src/research/optimal_rebalancing.py` - broken metrics collection
- `research-phase1.bat` - automation script blocked
- `RESEARCH_PLAN.md` - research framework dependent on this tool

### Impact
- **Blocks Phase 1 research:** Cannot execute 84 planned backtests
- **Blocks hypothesis testing:** No empirical data to validate H1-H4
- **Blocks data-driven recommendations:** Cannot determine optimal sdN values per asset class

### Suggested Fix
1. Locate `run_algorithm_backtest()` function definition
2. Verify it calculates: total_return_pct, transaction_count, max_drawdown_pct, sharpe_ratio
3. Ensure metrics are stored in returned `summary` dict with correct key names
4. Add unit test to prevent regression

### Workaround
Use `src/run_model.py` directly for individual backtests (known to work), then manually aggregate results into CSV.

Example:
```bash
python -m src.run_model NVDA 10/23/2023 10/23/2024 sd6 --qty 10000
# Manually copy output to spreadsheet
# Repeat 84 times for all asset/sdN combinations
```

### Reference Implementation
`src/run_model.py` correctly calculates and displays all metrics. Compare its implementation for guidance.

---

## Future Enhancements

### Research Phase 2 & 3
Once Phase 1 bug is fixed:
- Phase 2: Test profit-sharing independence (84 backtests)
- Phase 3: Extended time horizons - 3-year and 5-year periods (168 backtests)

### Visualization Suite
Create data visualization tools:
- Heatmaps: Asset × sdN performance matrices
- Scatter plots: Volatility vs optimal sdN correlation
- Line charts: Return curves by asset class
- Box plots: Distribution analysis

### Statistical Analysis Module
Implement hypothesis testing:
- Spearman correlation for H1
- Chi-square tests for H2
- ANOVA for H3
- Regression analysis for H4
