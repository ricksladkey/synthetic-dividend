# Portfolio Backtest Functions Analysis

## The Two Functions

### `run_portfolio_backtest()` (Original)
**Location**: `src/models/backtest.py:987`
**Created**: Commit `ae7a221` - "Unify portfolio backtesting"

**Architecture**:
- Runs each asset **independently** with separate algorithm instances
- Each asset gets its own bank/cash position
- No shared cash pool
- Supports both buy-and-hold and algorithmic strategies via string/callable/AlgorithmBase
- Extensive parameter list (dividends, CPI, reference assets, etc.)
- Returns aggregated portfolio results

**Current Usage**:
- `src/models/portfolio_simulator.py` - Legacy `simulate_portfolio()` wrapper
- Used for backward compatibility with old code

### `run_portfolio_backtest()` (New Architecture)
**Location**: `src/models/backtest.py:1166`
**Created**: Commit `270c161` - "Implement quarterly rebalancing and portfolio backtest runner"

**Architecture**:
- Uses **single shared cash pool** across all assets
- Portfolio algorithm sees full portfolio state on each day
- Calls `portfolio_algo.on_portfolio_day()` once per day
- Supports PortfolioAlgorithmBase (portfolio-level and per-asset algorithms)
- Minimal parameter list (focused on core functionality)
- Returns transactions + summary with daily_bank_values tracking

**Current Usage**:
- `src/research/baseline_diagnostic.py` - Validation studies
- `src/research/compare_with_without_btc.py` - BTC contribution analysis
- `src/research/quick_validation.py` - Withdrawal rate testing
- `src/research/find_narrow_neck.py` - Narrow neck finder
- `src/synthetic_dividend_tool.py` - CLI `run portfolio` command

---

## Key Differences

| Feature | `run_portfolio_backtest()` | `run_portfolio_backtest()` |
|---------|---------------------------|------------------------------|
| **Cash Architecture** | Separate bank per asset | Single shared bank |
| **Algorithm Interface** | String/Callable/AlgorithmBase | PortfolioAlgorithmBase only |
| **Portfolio Awareness** | No - each asset isolated | Yes - full portfolio state |
| **Portfolio-Level Algos** | Not supported | Quarterly/monthly rebalancing |
| **Per-Asset Coordination** | Not possible | Via PerAssetPortfolioAlgorithm |
| **Withdrawal Support** | Per-asset withdrawals | Portfolio-level withdrawals |
| **Daily Bank Tracking** | No | Yes (`daily_bank_values`) |
| **Validation Results** | N/A | +120% volatility alpha proven |

---

## The Critical Difference: Shared Cash Pool

### Old Architecture (`run_portfolio_backtest`)
```
Asset VOO: Bank=$300K → Algo makes decisions based on VOO's bank only
Asset BIL: Bank=$200K → Algo makes decisions based on BIL's bank only
Asset BTC: Bank=$100K → Algo makes decisions based on BTC's bank only

Problem: Can't rebalance across assets, can't handle portfolio-level withdrawals
```

### New Architecture (`run_portfolio_backtest`)
```
Shared Bank: $600K → Portfolio algo sees full state:
 - VOO: 1000 shares @ $400
 - BIL: 5000 shares @ $100
 - BTC: 2.5 shares @ $40,000
 - Shared bank: $600K

Portfolio algo can:
 - Rebalance across assets (sell VOO, buy BTC)
 - Handle withdrawals from shared pool
 - Coordinate per-asset strategies
```

---

## Why We Have Both

1. **Backward Compatibility**: `simulate_portfolio()` still uses old function
2. **Different Use Cases**:
 - Old: Simple buy-and-hold with independent assets
 - New: Portfolio-level coordination and synthetic dividends
3. **Migration In Progress**: New research uses v2, legacy code uses v1
4. **Feature Parity Not Complete**: v1 has more parameters (dividends, CPI, reference assets)

---

## Should We Unify Them?

### Arguments For Unification

**Pros**:
- Single source of truth for portfolio backtesting
- Reduce maintenance burden
- Eliminate confusion about which to use
- Shared cash pool is strictly superior architecture

**Cons**:
- Breaking change for `simulate_portfolio()` users
- Would need to port features from v1 to v2:
 - Dividend tracking
 - CPI adjustment
 - Reference asset adjustments
 - Risk-free rate calculations

### Recommendation: **Phased Unification**

**Phase 1: Feature Parity** (Do This)
1. Add missing features to `run_portfolio_backtest()`:
 - `dividend_series` parameter
 - `cpi_data` parameter
 - `reference_data` and `risk_free_data` parameters
2. Update `simulate_portfolio()` to use v2 with shared bank
3. Test that all legacy code still works

**Phase 2: Deprecation**
1. Add deprecation warning to `run_portfolio_backtest()`
2. Update docs to recommend v2
3. Migrate all internal code to v2

**Phase 3: Removal** (After 1-2 releases)
1. Delete `run_portfolio_backtest()`
2. Rename `run_portfolio_backtest()` → `run_portfolio_backtest()`

---

## Migration Path

### For `simulate_portfolio()` (in `portfolio_simulator.py`)

**Current**:
```python
transactions, portfolio_summary = run_portfolio_backtest(
 allocations=allocations,
 start_date=start_date,
 end_date=end_date,
 initial_investment=initial_value,
 algo="buy-and-hold",
 simple_mode=True,
)
```

**After Migration**:
```python
from src.algorithms.portfolio_factory import build_portfolio_algo_from_name

algo = build_portfolio_algo_from_name("per-asset:buy-and-hold", allocations)

transactions, portfolio_summary = run_portfolio_backtest(
 allocations=allocations,
 start_date=start_date,
 end_date=end_date,
 portfolio_algo=algo,
 initial_investment=initial_value,
)
```

**Key Change**: Shared bank means all assets draw from same cash pool, which is more realistic and enables portfolio-level strategies.

---

## Git History Analysis

```bash
$ git log --oneline --all --grep="portfolio.*backtest"
270c161 Implement quarterly rebalancing and portfolio backtest runner # v2 introduced
ae7a221 Unify portfolio backtesting, add comprehensive docs # v1 created
5a96748 Add multi-asset portfolio infrastructure # Original
```

**Timeline**:
1. Original multi-asset support (separate banks per asset)
2. Unified v1 (still separate banks, but cleaner interface)
3. New v2 architecture (shared bank for portfolio coordination)

The v2 was created to enable the **portfolio algorithm architecture** (portfolio-level + per-asset algorithms with shared cash pool) which proved the +120% volatility alpha.

---

## Conclusion

**Current State**: We have two functions serving different purposes:
- v1: Legacy support, independent asset backtests
- v2: Modern portfolio coordination, proven validation results

**Recommended Action**: **Add feature parity to v2, then deprecate v1**

**Rationale**:
- Shared cash pool is architecturally superior
- All validation results use v2
- V2 enables portfolio-level algorithms (quarterly rebalance, etc.)
- Migration is straightforward once features are ported

**Next Steps**:
1. Audit what parameters v1 has that v2 doesn't
2. Port those features to v2 (dividends, CPI, reference assets)
3. Test `simulate_portfolio()` with v2
4. Add deprecation warning to v1
5. Update all documentation to reference v2

---

Generated: 2025-10-30
Analysis by: Claude (Anthropic)
