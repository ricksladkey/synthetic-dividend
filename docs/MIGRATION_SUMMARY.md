# Migration Summary: run_algorithm_backtest → run_portfolio_backtest

## Overview

This document summarizes the migration of 4 priority test files from `run_algorithm_backtest()` to `run_portfolio_backtest()` API, as specified in the PR requirements.

## Scope

### Files Migrated (4 test files)
1. [OK] `tests/test_volatility_alpha_mechanics.py` - Already using new API
2. [OK] `tests/test_price_normalization.py` - Migrated 5 test methods
3. [OK] `tests/test_portfolio_algorithms.py` - Updated 1 parity test
4. [OK] `tests/test_mock_provider.py` - Migrated 1 test method

### Documentation Updated (5 files)
1. [OK] `docs/EXAMPLES.md`
2. [OK] `theory/API_SIMPLIFICATION.md`
3. [OK] `theory/PRICE_NORMALIZATION.md`
4. [OK] `theory/INCOME_GENERATION.md`
5. [OK] `theory/STRATEGIC_ANALYSIS.md`

### Source Code Updated
1. [OK] `src/models/backtest.py` - Added deprecation warning

## Migration Pattern

### Single-Ticker Backtest Migration

**Old API:**
```python
from src.models.backtest import SyntheticDividendAlgorithm, run_algorithm_backtest

# Create algorithm instance
algo = SyntheticDividendAlgorithm(
 rebalance_size=0.0905, # 9.05%
 profit_sharing=0.5, # 50%
 buyback_enabled=True,
 bracket_seed=100.0, # Optional
)

# Run backtest
txns, summary = run_algorithm_backtest(
 df=price_df,
 ticker="NVDA",
 initial_qty=1000,
 start_date=start_date,
 end_date=end_date,
 algo=algo,
 simple_mode=True,
)

# Access results
holdings = summary["holdings"]
bank = summary["bank"]
```

**New API:**
```python
from src.models.backtest import run_portfolio_backtest
from unittest.mock import patch
import src.data.fetcher as fetcher_module

# Mock fetcher for test data
original_get_history = fetcher_module.HistoryFetcher.get_history

def mock_get_history(self, ticker, start_date, end_date):
 if ticker == "NVDA":
 return price_df
 return original_get_history(self, ticker, start_date, end_date)

# Run backtest with string-based algorithm
with patch.object(fetcher_module.HistoryFetcher, "get_history", mock_get_history):
 txns, summary = run_portfolio_backtest(
 allocations={"NVDA": 1.0},
 start_date=start_date,
 end_date=end_date,
 portfolio_algo="per-asset:sd-9.05,50,100", # String format
 initial_investment=1000 * start_price,
 simple_mode=True,
 )

# Access results from portfolio structure
holdings = summary["assets"]["NVDA"]["final_holdings"]
bank = summary["final_bank"]
```

## Algorithm String Format

The new API uses string-based algorithm specification:

### Synthetic Dividend Algorithms
- `"per-asset:sd8"` - SD8 with defaults (9.05% trigger, 50% profit sharing)
- `"per-asset:sd-9.05,50"` - Custom trigger and profit sharing
- `"per-asset:sd-9.05,50,100"` - With bracket_seed=100

### Other Algorithms
- `"per-asset:buy-and-hold"` - Buy and hold strategy
- `"quarterly-rebalance"` - Quarterly rebalancing
- `"monthly-rebalance"` - Monthly rebalancing

## Test Data Injection Pattern

For tests that use synthetic data, the new API requires mocking the `HistoryFetcher`:

```python
from unittest.mock import patch
import src.data.fetcher as fetcher_module

original_get_history = fetcher_module.HistoryFetcher.get_history

def mock_get_history(self, ticker, start_date, end_date):
 if ticker == "TEST":
 return test_dataframe
 return original_get_history(self, ticker, start_date, end_date)

with patch.object(fetcher_module.HistoryFetcher, "get_history", mock_get_history):
 txns, summary = run_portfolio_backtest(...)
```

## Result Structure Changes

### Old (run_algorithm_backtest)
```python
summary = {
 "holdings": 100,
 "bank": 5000.0,
 "total": 105000.0,
 "total_return": 0.05, # Decimal (5%)
}
```

### New (run_portfolio_backtest)
```python
summary = {
 "assets": {
 "NVDA": {
 "final_holdings": 100,
 "final_value": 100000.0,
 }
 },
 "final_bank": 5000.0,
 "total_final_value": 105000.0,
 "total_return": 5.0, # Percentage (5%)
}
```

## Files NOT Migrated (Out of Scope)

### Test Files (6 remaining)
- `tests/test_backtest_parity.py`
- `tests/test_buyback_stack.py`
- `tests/test_dividend_tracking.py`
- `tests/test_margin_modes.py`
- `tests/test_multi_bracket_gaps.py`
- `tests/test_volatility_alpha_synthetic.py`

### Source/Research Files (~12 remaining)
- `src/models/retirement_backtest.py`
- `src/compare/*.py` (4 files)
- `src/tools/*.py` (2 files)
- `src/research/*.py` (5 files)

**Total remaining:** 94 occurrences across 20+ files

## Rationale for Partial Migration

Per the "minimal changes" principle:
1. The PR focused on the 4 explicitly mentioned high-priority test files
2. Migrating all 20+ files would exceed the scope of a minimal-change PR
3. The `run_algorithm_backtest()` function remains with a deprecation warning
4. Other files can be migrated incrementally in follow-up PRs

## Testing Recommendations

To verify the migration:
1. Run the 4 migrated test files individually
2. Verify they pass with the new API
3. Check that test behavior is unchanged
4. Validate that mocking works correctly

## Next Steps

For complete migration:
1. Migrate remaining 6 test files
2. Migrate src/compare/*.py files
3. Migrate src/tools/*.py files
4. Migrate src/research/*.py files
5. Remove `run_algorithm_backtest()` function entirely
6. Remove deprecation warning from codebase

## References

- Problem Statement: PR instructions document
- API Documentation: `src/models/backtest.py` docstrings
- Algorithm Factory: `src/algorithms/factory.py`
- Portfolio Factory: `src/algorithms/portfolio_factory.py`
