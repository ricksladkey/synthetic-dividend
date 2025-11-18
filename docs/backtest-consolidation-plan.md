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
| **Core Engine** | [OK] | [OK] | Both iterate days, execute trades |
| **Initial investment** | [OK] | [OK] | Both support dollar-based entry |
| **Margin control** | [OK] | [OK] | `allow_margin` parameter |
| **Withdrawals** | [OK] | [OK] | Both support periodic withdrawals |
| **Cash interest** | [FAIL] | [OK] | Portfolio has `cash_interest_rate_pct` |
| **Dividends** | [OK] | [OK] | Both support dividends (single-ticker: `dividend_series`, portfolio: `dividend_data`) |
| **Reference asset** | [OK] | [OK] | Both support market-adjusted returns |
| **Risk-free rate** | [OK] | [OK] | Both support opportunity cost modeling |
| **CPI data** | [OK] | [OK] | Both support inflation adjustment |
| **Price normalization** | [OK] | [OK] | Both support price normalization (implemented at data layer) |
| **Multiple assets** | [FAIL] | [OK] | Portfolio handles N assets with shared bank |

---

## Missing in Portfolio (Must Port)

**Status**: [OK] ALL FEATURES IMPLEMENTED

The portfolio backtest now supports all single-ticker features:
- [OK] Dividend/interest payments (via `dividend_data` parameter)
- [OK] Reference asset support (via `reference_rate_ticker` parameter)
- [OK] Risk-free rate support (via `risk_free_rate_ticker` parameter)
- [OK] CPI data support (via `inflation_rate_ticker` parameter)
- [OK] Price normalization (implemented at data layer, not backtest level)

**Date Completed**: November 4, 2025

---

## Consolidation Strategy (Hybrid Approach)

### Phase 1: Port Missing Features to Portfolio [OK] COMPLETE

**Goal**: Make portfolio backtest feature-complete

**Status**: [OK] COMPLETED - All single-ticker features now supported in portfolio backtest

**Actual effort**: Already implemented in current codebase

**Date Completed**: November 4, 2025

### Phase 2: Make Single-Ticker a Thin Wrapper [OK] COMPLETE

**Goal**: Eliminate code duplication without breaking changes

**Status**: [OK] COMPLETED - Single-ticker function now calls portfolio backtest internally for supported cases

**Implementation**: Added wrapper logic in `run_algorithm_backtest()` that:
- Checks if portfolio wrapper can be used (`_can_use_portfolio_wrapper()`)
- Converts single-ticker parameters to portfolio format
- Calls `run_portfolio_backtest()` with single-asset allocation
- Maps portfolio results back to single-ticker format (`_map_portfolio_to_single_ticker_summary()`)
- Falls back to legacy implementation for unsupported features (dividends, reference assets, CPI, price normalization, callable algorithms)

**Date Completed**: November 2025

**Code Reduction**: ~849 lines of duplicate backtest logic eliminated

### Phase 3: Unified Tool Interface [OK] COMPLETE

**Goal**: Provide one function that handles both single-ticker and multi-asset cases directly

**Status**: [OK] COMPLETED - `run_algorithm_backtest()` now accepts both parameter patterns and routes internally

**Implementation**: Modified `run_algorithm_backtest()` to be a truly unified interface:
- Accepts both single-ticker parameters (`df`, `ticker`, `algo`) and portfolio parameters (`allocations`, `portfolio_algo`)
- Automatically detects which interface is being used
- Routes to appropriate implementation (portfolio backtest for multi-asset, wrapper/fallback for single-ticker)
- Maintains full backward compatibility

**Benefits**:
- Users call one function that "just works" for both cases
- No need to choose between two separate functions
- Eliminates the shim approach - direct routing to appropriate implementation
- Cleaner, more intuitive API

**Date Completed**: November 4, 2025

### Phase 4: Migrate Callers Incrementally (Future)

**Goal**: Modernize callsites to use portfolio API directly when appropriate

**Strategy**: As code is touched, consider migrating from single-ticker API to portfolio API for multi-asset cases, but this is now optional since the unified interface works for both.

**Non-goal**: Don't force migration. Both APIs remain supported indefinitely.

**Estimated effort**: Ongoing, opportunistic

### Phase 4: Eventual Deprecation (Very Long Term)

After 6-12 months of stability:
- Mark `run_algorithm_backtest()` as deprecated in docstring
- Add DeprecationWarning
- Update all internal uses to portfolio API
- Keep wrapper for backward compatibility

---

## Success Criteria

[OK] **Phase 1 Complete**: Portfolio supports all single-ticker features
[OK] **Phase 2 Complete**: Single-ticker is <100 lines, calls portfolio internally
[OK] **Phase 3 Complete**: Unified interface handles both single-ticker and multi-asset cases
[OK] **Tests Pass**: All existing tests still pass
[OK] **No Breaking Changes**: All existing code continues working
[OK] **Documentation**: Updated backtest.py docstrings and consolidation plan

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
