# Abstraction Level Audit

This document tracks violations of the "Abstraction Level Determines Naming" principle and their remediation status.

## Type Aliases

**Status**: [OK] Implemented

- `Data = pd.DataFrame` - Clean abstraction for tabular data parameters

## pd.DataFrame Parameter Type Violations

Parameters typed as `pd.DataFrame` that should use `Data` alias for clean abstraction:

### High Priority (Public API)

**src/models/backtest.py**:
- [OK] Line 89: `df: Data` - FIXED
- [OK] Line 98: Already uses `Data` for `reference_data`
- [OK] Line 99: Already uses `Data` for `risk_free_data`
- [OK] Line 107: Already uses `Data` for `cpi_data`

**src/models/retirement_backtest.py**:
- [OK] Line 26: `df: Data` - FIXED
- [OK] Line 139: `df: Data` - FIXED
- [OK] Line 208: `df: Data` - FIXED

**src/synthetic_dividend_tool.py**:
- [OK] Line 128: `reference_data: Optional[Data]` - FIXED (was reference_df)
- [OK] Line 129: `risk_free_data: Optional[Data]` - FIXED (was risk_free_df)

**src/compare/batch_comparison.py**:
- [OK] Line 47: `df: Data` - FIXED
- [OK] Line 55: `reference_data: Data` - FIXED (was reference_asset_df)
- [OK] Line 56: `risk_free_data: Data` - FIXED (was risk_free_asset_df)

**src/compare/runner.py, table.py, validator.py**:
- TODO: Multiple instances of `df: pd.DataFrame` → `df: Data`

**src/gui/layout.py**:
- Line 177: `df: pd.DataFrame` → `df: Data`

### Medium Priority (Research/Tools)

**src/tools/volatility_alpha_analyzer.py**:
- Line 23: `df: pd.DataFrame` → `df: Data`
- Line 128: `df: pd.DataFrame` → `df: Data`

**src/research/** (all files):
- Multiple instances in experimental code

### Low Priority (Internal/Private)

**src/algorithms/base.py, buy_and_hold.py, synthetic_dividend.py**:
- `history: pd.DataFrame` - Internal state, can keep as-is or use `Data`

**src/data/yahoo_provider.py**:
- Line 154, 160, 189, 203: Cache management - internal implementation

**src/models/backtest_utils.py**:
- Line 52: `df: pd.DataFrame` - Utility function, lower priority

**src/data/cpi_fetcher.py**:
- Line 44: `self._cache: Optional[pd.DataFrame]` - Private cache

## _pct Parameter Violations

Parameters ending with `_pct` imply non-universal units (percentages stored as 0-100 instead of decimal 0.0-1.0).

### Critical Issues (Require Unit Conversion)

**src/models/backtest.py**:
- [FAIL] Line 96: `reference_return_pct: float = 0.0` → Should be `reference_return: float = 0.0` (stored as decimal)
- [FAIL] Line 97: `risk_free_rate_pct: float = 0.0` → Should be `risk_free_rate: float = 0.0` (stored as decimal)
- [FAIL] Line 105: `withdrawal_rate_pct: float = 0.0` → Should be `withdrawal_rate: float = 0.0` (stored as decimal)
- Line 243-244: Requires division by 100 because input is percentage
- Line 366: Requires division by 100 because input is percentage

**src/models/retirement_backtest.py**:
- Line 145: `target_final_value_pct: float = 1.0` - Actually stored as decimal (1.0 = 100%), name is misleading

**src/algorithms/buy_and_hold.py**:
- Line 16: `rebalance_size_pct: float = 0.0` → Should be `rebalance_size: float = 0.0` (decimal)
- Line 17: `profit_sharing_pct: float = 0.0` → Should be `profit_sharing: float = 0.0` (decimal)

**src/algorithms/factory.py**:
- Lines 49, 60-63, 69-72, 78-81, 87-90: `profit_pct` variables used for conversion (divide by 100)
- Lines 60, 69, 78, 87: `rebalance_pct` variables used for conversion

**src/tools/order_calculator.py**:
- Line 30: `profit_sharing_pct: float` → `profit_sharing: float` (should be decimal internally)
- Line 76: `profit_pct: float` - Display/CLI parameter (acceptable if documented as UI layer)

### Acceptable (Display/Summary Variables)

These are internal calculations for display purposes, not API parameters:

**src/models/backtest.py**:
- Lines 688-689: `deployment_min_pct`, `deployment_max_pct` - Summary statistics
- Lines 790, 795, 802: `universal_income_pct`, etc. - Display values
- Lines 811-815: Income classification dict keys - Display format

**src/tools/volatility_alpha_analyzer.py**:
- Lines 64-77: `trigger_pct`, `vol_pct` - Recommendation display
- Line 80-95: Display/calculation helpers

**tests/test_buyback_stack.py**:
- Line 65: `rebalance_pct: float` - Test parameter (converted to decimal before use)

**tests/test_price_normalization.py**:
- Lines 260, 294: `trigger_pct` - Test data

## Remediation Strategy

### Phase 1: Type Aliases ([OK] DONE)
- Add `Data = pd.DataFrame` alias to backtest.py
- Update public API parameters in backtest.py

### Phase 2: Core API Parameters (NEXT)
1. Update backtest.py to use `Data` for `df` parameter
2. Update retirement_backtest.py to use `Data`
3. Update synthetic_dividend_tool.py parameter names and types
4. Update compare/ module public APIs

### Phase 3: Unit Standardization (CRITICAL)
1. Change API parameters from `*_pct` (percentage) to universal units (decimal)
 - `reference_return_pct` → `reference_return` (0.10 instead of 10.0)
 - `risk_free_rate_pct` → `risk_free_rate`
 - `withdrawal_rate_pct` → `withdrawal_rate`
2. Update all callers to pass decimals instead of percentages
3. Remove division by 100 from backtest.py implementation
4. Update documentation to clarify decimal format

### Phase 4: Research Code (LOW PRIORITY)
- Update experimental scripts after core API is stable
- Can be done incrementally

## Principle Violations Found

1. **Mixed abstraction in type hints**: `pd.DataFrame` exposes pandas implementation detail
 - **Fix**: Use `Data` type alias

2. **Non-universal units in API**: `_pct` suffix indicates percentage (0-100) instead of decimal (0-1)
 - **Fix**: Store as decimal, convert only at UI/display layer

3. **Inconsistent naming**: `reference_asset_df` mixed domain + implementation, now partially fixed
 - **Fix**: Use `reference_data` consistently

## Benefits of Remediation

1. **Cleaner abstraction**: `Data` type shows intent without implementation details
2. **Universal units**: Decimal format (0-1) is standard in financial math
3. **Easier refactoring**: Can swap pd.DataFrame for polars/arrow without changing signatures
4. **Less error-prone**: No "did I divide by 100?" questions
5. **Better documentation**: Type hints convey meaning, not implementation

## Notes

- GUI code can use `_pct` suffix since it's display layer (acceptable)
- Internal display variables (summary stats) can use percentages
- Test code can use percentages if documented
- The key principle: **API parameters should use universal units (decimals), not display units (percentages)**
