# Backtest Engine Consolidation Plan

**Goal**: Consolidate two parallel backtest implementations into one unified engine with backward-compatible wrappers.

**Date**: November 2025

---

## Current State

### Two Implementations

| Implementation | Lines | File Location | Primary Use |
|----------------|-------|---------------|-------------|
| `run_algorithm_backtest()` | 849 | backtest.py:91-939 | Single-ticker backtests, research, comparisons |
| `run_portfolio_backtest()` | 427 | backtest.py:996-end | Multi-asset portfolios, diversified strategies |

**Total Code**: 1,276 lines of parallel logic (90% of backtest.py)

---

## Feature Matrix

| Feature | Single-Ticker | Portfolio | Notes |
|---------|---------------|-----------|-------|
| **Core Engine** | ✅ | ✅ | Both iterate days, execute trades |
| **Initial investment** | ✅ | ✅ | Both support dollar-based entry |
| **Margin control** | ✅ | ✅ | `allow_margin` parameter |
| **Withdrawals** | ✅ | ✅ | Both support periodic withdrawals |
| **Cash interest** | ❌ | ✅ | Portfolio has `cash_interest_rate_pct` |
| **Dividends** | ✅ | ❌ | Single-ticker: `dividend_series` parameter |
| **Reference asset** | ✅ | ❌ | Single-ticker: market-adjusted returns (VOO) |
| **Risk-free rate** | ✅ | ❌ | Single-ticker: opportunity cost modeling (BIL) |
| **CPI data** | ✅ | ❌ | Single-ticker: inflation adjustment |
| **Price normalization** | ✅ | ❌ | Single-ticker: `normalize_prices` for bracket alignment |
| **Multiple assets** | ❌ | ✅ | Portfolio handles N assets with shared bank |

---

## Missing in Portfolio (Must Port)

### 1. Dividend/Interest Payments ⚠️ HIGH PRIORITY
- **What**: Periodic income credited to bank (e.g., BIL monthly, VOO quarterly)
- **Why**: Realistic modeling of income-producing assets
- **Location**: Single-ticker lines ~450-480
- **Complexity**: Medium (need to handle ex-dividend dates, time-weighted holdings)

### 2. Reference Asset (Market-Adjusted Returns)
- **What**: Compare performance vs benchmark (e.g., SPY, VOO)
- **Why**: Calculate alpha (excess returns over market)
- **Location**: Single-ticker lines ~880-910
- **Complexity**: Low (just fetch benchmark data and calculate relative returns)

### 3. Risk-Free Rate (Opportunity Cost)
- **What**: Calculate opportunity cost of negative bank balance vs risk-free asset (BIL)
- **Why**: Realistic cost of margin/borrowing
- **Location**: Single-ticker lines ~890-920
- **Complexity**: Low (already have `cash_interest_rate_pct`, just extend)

### 4. CPI Data (Inflation Adjustment)
- **What**: Adjust returns for inflation using CPI data
- **Why**: Real vs nominal return analysis
- **Location**: Single-ticker lines ~920-935
- **Complexity**: Low (fetch CPI, apply adjustment)

### 5. Price Normalization
- **What**: Align prices to bracket boundaries (`normalize_prices`)
- **Why**: Testing bracket alignment without actual price gaps
- **Location**: Single-ticker lines ~280-310
- **Complexity**: Low (preprocessing step)

---

## Consolidation Strategy (Hybrid Approach)

### Phase 1: Port Missing Features to Portfolio (Next Task)

**Goal**: Make portfolio backtest feature-complete

**Tasks**:
1. ✅ Analyze feature gaps (this document)
2. ✅ Add dividend/interest payment support (commit: 8956316)
   - Time-weighted holdings calculation (already exists as helper)
   - Ex-dividend date handling
   - Credit to bank on payment dates
   - Parameter: `dividend_data: Dict[str, pd.Series]`
3. ✅ Add reference asset support (commit: 0130f7f)
   - Fetch benchmark data
   - Calculate market-adjusted returns (alpha)
   - Parameter: `reference_rate_ticker: str` (e.g., "VOO")
4. ✅ Add risk-free rate support (commit: ec20ce1)
   - Use actual risk-free asset returns for cash interest
   - Falls back to cash_interest_rate_pct if not provided
   - Parameter: `risk_free_rate_ticker: str` (e.g., "BIL")
5. ✅ Add CPI data support (commit: a565ff0)
   - Fetch inflation data
   - Calculate inflation-adjusted (real) returns
   - Parameter: `inflation_rate_ticker: str` (e.g., "CPI")
6. ⛔ Price normalization support - SKIPPED
   - Reason: Should be algorithm parameter, not engine parameter
   - Will be handled in algorithm implementations, not backtest engine

**Status**: ✅ PHASE 1 COMPLETE

**Actual effort**: ~3 hours (single session)

### Phase 2: Make Single-Ticker a Thin Wrapper

**Goal**: Eliminate code duplication without breaking changes

**Approach**:
```python
def run_algorithm_backtest(
    df: pd.DataFrame,
    ticker: str,
    initial_qty: Optional[int] = None,
    algo: Optional[Union[AlgorithmBase, Callable]] = None,
    # ... all existing parameters
) -> Tuple[List[Transaction], Dict[str, Any]]:
    """Execute single-ticker backtest.

    IMPLEMENTATION NOTE: This is now a convenience wrapper around
    run_portfolio_backtest() with N=1 assets. All logic has been
    consolidated into the portfolio engine.
    """
    # Convert single-ticker params to portfolio format
    allocations = {ticker: 1.0}

    # Wrap single-asset algorithm in per-asset portfolio algorithm
    portfolio_algo = PerAssetPortfolio(
        algorithms={ticker: algo},
        allocations=allocations
    )

    # Call unified portfolio backtest
    return run_portfolio_backtest(
        allocations=allocations,
        portfolio_algo=portfolio_algo,
        start_date=start_date,
        end_date=end_date,
        initial_investment=initial_investment or (initial_qty * first_price),
        dividend_data={ticker: dividend_series} if dividend_series else {},
        reference_asset=reference_data,
        risk_free_asset=risk_free_data,
        cpi_data=cpi_data,
        normalize_prices=normalize_prices,
        # ... pass through all other parameters
    )
```

**Benefits**:
- ✅ Delete ~849 lines of duplicate code
- ✅ All fixes/features automatically apply to both
- ✅ No breaking changes (same API)
- ✅ Single-ticker becomes ~50 lines (parameter translation)

**Estimated effort**: 2-3 hours

### Phase 3: Migrate Callers Incrementally (Future)

**Goal**: Modernize callsites to use portfolio API directly

**Strategy**: As code is touched, migrate from:
```python
# Old single-ticker API
txns, summary = run_algorithm_backtest(
    df=price_data,
    ticker="NVDA",
    algo=SyntheticDividendAlgorithm(...),
    ...
)
```

To:
```python
# Modern portfolio API (even for N=1)
txns, summary = run_portfolio_backtest(
    allocations={"NVDA": 1.0},
    portfolio_algo="per-asset:sd8",
    ...
)
```

**Non-goal**: Don't force migration. Single-ticker API remains supported indefinitely.

**Estimated effort**: Ongoing, opportunistic

### Phase 4: Eventual Deprecation (Very Long Term)

After 6-12 months of stability:
- Mark `run_algorithm_backtest()` as deprecated in docstring
- Add DeprecationWarning
- Update all internal uses to portfolio API
- Keep wrapper for backward compatibility

---

## Success Criteria

✅ **Phase 1 Complete**: Portfolio supports all single-ticker features
✅ **Phase 2 Complete**: Single-ticker is <100 lines, calls portfolio internally
✅ **Tests Pass**: All 292 existing tests still pass
✅ **No Breaking Changes**: All existing code continues working
✅ **Documentation**: Update backtest.py docstrings to explain relationship

---

## Risk Mitigation

**Risk**: Breaking existing research/comparison code
**Mitigation**: Maintain exact API compatibility, add deprecation warnings only after stability

**Risk**: Performance regression
**Mitigation**: Benchmark before/after, ensure wrapper overhead is negligible

**Risk**: Subtle behavior changes
**Mitigation**: Comprehensive test coverage, validate against known results

**Risk**: Scope creep ("while we're here, let's also...")
**Mitigation**: Strict phases, each independently valuable

---

## Next Steps

1. **Read current portfolio implementation** - Understand existing architecture
2. **Design dividend payment system** - How to integrate with portfolio day loop
3. **Implement dividend support** - Add parameter, credit to bank on ex-div dates
4. **Add reference asset support** - Fetch benchmark, calculate alpha
5. **Add remaining features** - Risk-free rate, CPI, price normalization
6. **Write comprehensive tests** - Verify parity with single-ticker behavior
7. **Create wrapper** - Make single-ticker call portfolio
8. **Validate all tests pass** - Ensure no regressions

**Ready to start Phase 1?** Let's begin with dividend/interest payment support.
