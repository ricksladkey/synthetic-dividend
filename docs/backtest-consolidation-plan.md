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
| **Dividends** | ✅ | ✅ | Both support dividends (single-ticker: `dividend_series`, portfolio: `dividend_data`) |
| **Reference asset** | ✅ | ✅ | Both support market-adjusted returns |
| **Risk-free rate** | ✅ | ✅ | Both support opportunity cost modeling |
| **CPI data** | ✅ | ✅ | Both support inflation adjustment |
| **Price normalization** | ✅ | ✅ | Both support price normalization (implemented at data layer) |
| **Multiple assets** | ❌ | ✅ | Portfolio handles N assets with shared bank |

---

## Missing in Portfolio (Must Port)

**Status**: ✅ ALL FEATURES IMPLEMENTED

The portfolio backtest now supports all single-ticker features:
- ✅ Dividend/interest payments (via `dividend_data` parameter)
- ✅ Reference asset support (via `reference_rate_ticker` parameter)  
- ✅ Risk-free rate support (via `risk_free_rate_ticker` parameter)
- ✅ CPI data support (via `inflation_rate_ticker` parameter)
- ✅ Price normalization (implemented at data layer, not backtest level)

**Date Completed**: November 4, 2025

---

## Consolidation Strategy (Hybrid Approach)

### Phase 1: Port Missing Features to Portfolio ✅ COMPLETE

**Goal**: Make portfolio backtest feature-complete

**Status**: ✅ COMPLETED - All single-ticker features now supported in portfolio backtest

**Actual effort**: Already implemented in current codebase

**Date Completed**: November 4, 2025

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
⬜ **Phase 2 Complete**: Single-ticker is <100 lines, calls portfolio internally
✅ **Tests Pass**: All 302 existing tests still pass
✅ **No Breaking Changes**: All existing code continues working
⬜ **Documentation**: Update backtest.py docstrings to explain relationship

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

**Phase 2: Make Single-Ticker a Thin Wrapper** ⬜ NEXT

1. **Create parameter mapping function** - Convert single-ticker params to portfolio format
2. **Implement wrapper** - Make `run_algorithm_backtest()` call `run_portfolio_backtest()` internally
3. **Test equivalence** - Verify identical results for single-asset portfolios
4. **Update documentation** - Mark single-ticker as wrapper, update docstrings
5. **Run full test suite** - Ensure no regressions

**Ready to start Phase 2?** Let's implement the single-ticker wrapper.
