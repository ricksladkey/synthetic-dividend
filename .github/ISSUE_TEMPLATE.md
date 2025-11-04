# Bug Report: optimal_rebalancing.py Metrics Calculation

## Description
The `src/research/optimal_rebalancing.py` script successfully downloads data and runs simulations, but fails to properly calculate and save final performance metrics. All results are written as zeros to the output CSV.

## Evidence
When running a single-ticker backtest:
```
Synthetic Dividend Algorithm total volatility alpha: 5.58%  ← Calculation works
  [OK] sd6: 0.00% return, 0 txns, 0.00% max drawdown        ← Metrics not captured
```

## Root Cause
The `run_algorithm_backtest()` function's returned `summary` dictionary is not being populated with the calculated metrics:
- `total_return_pct` → returns 0 (should be calculated from final vs initial value)
- `transaction_count` → returns 0 (should count executed transactions)
- `max_drawdown_pct` → returns 0
- `sharpe_ratio` → returns 0
- `rebalance_trigger_pct` → returns 0

## Location
File: `src/research/optimal_rebalancing.py`
Function: `run_single_backtest()` (line 45-101)
- Calls `run_algorithm_backtest()` (line 73)
- Expects populated `summary` dict (line 90)
- Uses `summary.get("total_return_pct", 0)` defaulting to 0

## Expected Behavior
CSV output should contain actual calculated metrics:
```csv
ticker,sd_n,total_return_pct,transaction_count,...
NVDA,6,5.58,12,...
NVDA,8,5.01,10,...
```

## Actual Behavior
CSV output contains all zeros:
```csv
ticker,sd_n,total_return_pct,transaction_count,...
NVDA,6,0,0,...
NVDA,8,0,0,...
```

## Impact
- Phase 1 research cannot be completed (84 backtests return invalid data)
- Hypothesis testing blocked
- Cannot validate optimal rebalancing frequencies

## Suggested Fix
Investigate `run_algorithm_backtest()` or the function it calls to ensure:
1. Metrics are being calculated during simulation
2. Results are properly stored in `summary` dict
3. Dict keys match what `run_single_backtest()` expects

## Workaround
Use `src/synthetic_dividend_tool.py` directly for individual backtests (known to work correctly), then manually aggregate results.

## Priority
High - blocks core research objectives outlined in RESEARCH_PLAN.md

## Related Files
- `src/research/optimal_rebalancing.py` (broken)
- `src/synthetic_dividend_tool.py` (working reference implementation)
- `RESEARCH_PLAN.md` (research framework requiring this tool)
- `research-phase1.bat` (automation script waiting for fix)
