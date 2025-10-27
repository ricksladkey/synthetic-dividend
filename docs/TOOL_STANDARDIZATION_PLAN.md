# Synthetic Dividend Tool - Standardization & Return Adjustment Implementation Plan

**Date**: October 27, 2025  
**Goal**: Standardize argument names and add return adjustment framework across all subcommands

---

## Phase 1: Argument Name Standardization

### Current Inconsistencies (MUST FIX)

| Concept | Current Variants | Standard (Required) |
|---------|------------------|---------------------|
| Profit sharing | `--profit`, `--profit-pct`, `--profit-sharing` | **`--profit-pct`** |
| Initial quantity | `--qty`, `--initial-qty` | **`--initial-qty`** |
| Date formats | `MM/DD/YYYY`, `YYYY-MM-DD` | **`YYYY-MM-DD`** |

### Files to Update

**src/synthetic_dividend_tool.py** - Main CLI tool:
- Line 101: `--profit` → `--profit-pct` (optimal-rebalancing)
- Line 102: `--qty` → `--initial-qty` (optimal-rebalancing)
- Line 99-100: Date defaults from `10/23/2023` → `2023-10-23` format
- Line 112-113: Same date format fixes for volatility-alpha
- Line 191: `--profit-sharing` → `--profit-pct` (analyze volatility-alpha)

**Action Items**:
```python
# BEFORE (optimal-rebalancing):
optimal_parser.add_argument('--profit', type=float, default=50.0, help='Profit sharing % (default: 50)')
optimal_parser.add_argument('--qty', type=int, default=10000, help='Initial quantity (default: 10000)')

# AFTER:
optimal_parser.add_argument('--profit-pct', type=float, default=50.0, help='Profit sharing % (default: 50)')
optimal_parser.add_argument('--initial-qty', type=int, default=10000, help='Initial quantity (default: 10000)')
```

---

## Phase 2: Add Return Adjustment Arguments

### Add to ALL Subcommands

Add these arguments to every subcommand that produces return metrics:
- `backtest`
- `research optimal-rebalancing`
- `research volatility-alpha`
- `research asset-classes`
- `compare algorithms`
- `compare strategies`
- `compare batch`
- `analyze volatility-alpha`

**Standard Argument Block** (copy-paste this):
```python
# Return adjustment options (add to each subcommand parser)
parser.add_argument('--adjust-inflation', action='store_true', 
                   help='Show inflation-adjusted (real) returns')
parser.add_argument('--adjust-market', action='store_true',
                   help='Show market-adjusted returns (alpha)')
parser.add_argument('--adjust-both', action='store_true',
                   help='Show both inflation and market adjustments')
parser.add_argument('--inflation-ticker', default='CPI',
                   help='Ticker for inflation data (default: CPI)')
parser.add_argument('--market-ticker', default='VOO',
                   help='Ticker for market benchmark (default: VOO)')
```

### Implementation Locations

**File**: `src/synthetic_dividend_tool.py`

**Lines to modify**:
- ~Line 74-82: `backtest` command
- ~Line 99-105: `research optimal-rebalancing`
- ~Line 112-114: `research volatility-alpha`
- ~Line 121-123: `research asset-classes`
- ~Line 138-141: `compare algorithms`
- ~Line 148-151: `compare strategies`
- ~Line 158-163: `compare batch`
- ~Line 187-193: `analyze volatility-alpha`

---

## Phase 3: Create Utility Functions

### New File: `src/models/return_adjustments.py`

```python
"""Return adjustment utilities for inflation and market adjustments."""

from datetime import date
from typing import Dict, Any, Optional
import pandas as pd
from src.data.asset import Asset


def calculate_adjusted_returns(
    summary: Dict[str, Any],
    start_date: date,
    end_date: date,
    inflation_ticker: str = "CPI",
    market_ticker: str = "VOO",
    adjust_inflation: bool = False,
    adjust_market: bool = False,
) -> Dict[str, Any]:
    """Calculate inflation and market-adjusted returns.
    
    Args:
        summary: Backtest summary dict with 'total_return', 'start_value', etc.
        start_date: Period start date
        end_date: Period end date
        inflation_ticker: Ticker for inflation data (default: CPI)
        market_ticker: Ticker for market benchmark (default: VOO)
        adjust_inflation: Calculate real (inflation-adjusted) returns
        adjust_market: Calculate alpha (market-adjusted) returns
    
    Returns:
        Dict with adjusted metrics:
            - nominal_return, nominal_dollars
            - real_return, real_dollars (if adjust_inflation)
            - alpha, alpha_dollars (if adjust_market)
            - cpi_multiplier (if adjust_inflation)
            - market_return (if adjust_market)
    """
    nominal_return = summary['total_return']
    start_val = summary['start_value']
    end_val = summary['total']
    nominal_dollars = end_val - start_val
    
    result = {
        'nominal_return': nominal_return,
        'nominal_dollars': nominal_dollars,
    }
    
    # Inflation adjustment
    if adjust_inflation:
        inflation_asset = Asset(inflation_ticker)
        inflation_prices = inflation_asset.get_prices(start_date, end_date)
        
        cpi_start = float(inflation_prices.iloc[0]['Close'])
        cpi_end = float(inflation_prices.iloc[-1]['Close'])
        cpi_multiplier = cpi_end / cpi_start
        
        real_end_val = end_val / cpi_multiplier
        real_dollars = real_end_val - start_val
        real_return = real_dollars / start_val
        
        result.update({
            'real_return': real_return,
            'real_dollars': real_dollars,
            'cpi_multiplier': cpi_multiplier,
            'inflation_rate': (cpi_multiplier - 1.0),
        })
    
    # Market adjustment
    if adjust_market:
        market_asset = Asset(market_ticker)
        market_prices = market_asset.get_prices(start_date, end_date)
        
        market_start = float(market_prices.iloc[0]['Close'])
        market_end = float(market_prices.iloc[-1]['Close'])
        market_return = (market_end - market_start) / market_start
        
        alpha = nominal_return - market_return
        alpha_dollars = nominal_dollars - (start_val * market_return)
        
        result.update({
            'market_return': market_return,
            'alpha': alpha,
            'alpha_dollars': alpha_dollars,
            'benchmark': market_ticker,
        })
    
    return result


def print_adjusted_returns(
    adjustments: Dict[str, Any],
    verbose: bool = False
) -> None:
    """Print formatted adjusted return metrics.
    
    Args:
        adjustments: Dict from calculate_adjusted_returns()
        verbose: If True, print detailed multi-line format. 
                 If False, print compact single-line format.
    """
    if verbose:
        print("\n" + "=" * 70)
        print("RETURN BREAKDOWN")
        print("=" * 70)
        print()
        print("Nominal Return:")
        print(f"  Total Return:                {adjustments['nominal_return']*100:>10.2f}%")
        print(f"  Dollar Gain:                 ${adjustments['nominal_dollars']:>10,.2f}")
        
        if 'real_return' in adjustments:
            print()
            print("Inflation-Adjusted Return:")
            print(f"  Real Return:                 {adjustments['real_return']*100:>10.2f}%")
            print(f"  Real Dollar Gain:            ${adjustments['real_dollars']:>10,.2f}")
            print(f"  CPI Multiplier:              {adjustments['cpi_multiplier']:>10.3f}")
            print(f"  Period Inflation:            {adjustments['inflation_rate']*100:>10.2f}%")
            
            purchasing_power_lost = adjustments['nominal_dollars'] - adjustments['real_dollars']
            print(f"  Purchasing Power Lost:       ${purchasing_power_lost:>10,.2f}")
        
        if 'alpha' in adjustments:
            print()
            print(f"Market-Adjusted Return (vs {adjustments['benchmark']}):")
            print(f"  Alpha:                       {adjustments['alpha']*100:>10.2f}%")
            print(f"  Alpha Dollars:               ${adjustments['alpha_dollars']:>10,.2f}")
            print(f"  Market Return:               {adjustments['market_return']*100:>10.2f}%")
        
        print("=" * 70)
    else:
        # Compact format
        parts = [f"Nominal: {adjustments['nominal_return']*100:+.2f}% (${adjustments['nominal_dollars']:,.2f})"]
        
        if 'real_return' in adjustments:
            parts.append(f"Real: {adjustments['real_return']*100:+.2f}% (${adjustments['real_dollars']:,.2f})")
        
        if 'alpha' in adjustments:
            parts.append(f"Alpha: {adjustments['alpha']*100:+.2f}% (${adjustments['alpha_dollars']:,.2f} vs {adjustments['benchmark']})")
        
        print(" | ".join(parts))


def add_adjusted_columns_to_csv(
    df: pd.DataFrame,
    start_date_col: str = 'start_date',
    end_date_col: str = 'end_date',
    inflation_ticker: str = 'CPI',
    market_ticker: str = 'VOO',
) -> pd.DataFrame:
    """Add inflation and market-adjusted columns to research CSV.
    
    Args:
        df: DataFrame with backtest results
        start_date_col: Column name containing start dates
        end_date_col: Column name containing end dates
        inflation_ticker: Ticker for inflation data
        market_ticker: Ticker for market benchmark
    
    Returns:
        DataFrame with added columns:
            - real_return, real_dollars
            - alpha, alpha_dollars
            - market_return
    """
    # Implementation would iterate through rows and call calculate_adjusted_returns()
    # Left as exercise - requires row-by-row processing
    pass
```

---

## Phase 4: Integrate Into Commands

### Update Command Handlers

**File**: `src/synthetic_dividend_tool.py`

For each command that calls `run_algorithm_backtest()`, add:

```python
# After getting summary from backtest:
if args.adjust_inflation or args.adjust_market or args.adjust_both:
    from src.models.return_adjustments import calculate_adjusted_returns, print_adjusted_returns
    
    adjust_both = args.adjust_both
    adjustments = calculate_adjusted_returns(
        summary=summary,
        start_date=start_date,
        end_date=end_date,
        inflation_ticker=args.inflation_ticker,
        market_ticker=args.market_ticker,
        adjust_inflation=adjust_both or args.adjust_inflation,
        adjust_market=adjust_both or args.adjust_market,
    )
    
    print_adjusted_returns(adjustments, verbose=args.verbose)
```

---

## Phase 5: CSV Output Enhancement

### Add Columns to Research Output

For commands that generate CSV (research, compare batch):

**Columns to add**:
- `real_return` (if inflation adjustment enabled)
- `real_dollars`
- `inflation_rate`
- `alpha` (if market adjustment enabled)
- `alpha_dollars`
- `market_return`
- `benchmark` (ticker used for market comparison)

**Implementation**:
```python
# In research/compare commands:
if args.adjust_inflation or args.adjust_market or args.adjust_both:
    # Add adjusted metrics to each row before writing CSV
    for row in results:
        adjustments = calculate_adjusted_returns(...)
        row.update({
            'real_return': adjustments.get('real_return'),
            'alpha': adjustments.get('alpha'),
            # ... etc
        })
```

---

## Phase 6: Update Help Text

### Update Examples in Docstring

**File**: `src/synthetic_dividend_tool.py`, lines ~30-60

Add examples showing new flags:
```python
Examples:
    # ... existing examples ...
    
    # Inflation-adjusted backtest
    synthetic-dividend-tool backtest --ticker NVDA --start 2024-01-01 --end 2024-12-31 --adjust-inflation
    
    # Market-adjusted comparison
    synthetic-dividend-tool backtest --ticker GLD --start 2024-01-01 --end 2024-12-31 --adjust-market --market-ticker VOO
    
    # Complete analysis (nominal + real + alpha)
    synthetic-dividend-tool backtest --ticker AAPL --start 2024-01-01 --end 2024-12-31 --adjust-both --verbose
```

---

## Testing Plan

### Unit Tests

**New file**: `tests/test_return_adjustments.py`

```python
def test_inflation_adjustment():
    """Test CPI-based inflation adjustment calculation."""
    # Mock summary with known values
    # Mock CPI data
    # Verify real_return calculation
    pass

def test_market_adjustment():
    """Test market benchmark alpha calculation."""
    # Mock summary
    # Mock market data
    # Verify alpha calculation
    pass

def test_combined_adjustments():
    """Test both adjustments together."""
    pass

def test_print_formats():
    """Test verbose and compact output formats."""
    pass
```

### Integration Tests

**Test scenarios**:
1. Run backtest with `--adjust-inflation`, verify CPI data fetched
2. Run backtest with `--adjust-market`, verify VOO data fetched
3. Run batch comparison with `--adjust-both`, verify CSV has extra columns
4. Test with custom tickers: `--inflation-ticker VTIP --market-ticker QQQ`

---

## Backward Compatibility

### Breaking Changes

**These are BREAKING changes** (require version bump):
- `--profit` → `--profit-pct`
- `--qty` → `--initial-qty`

### Migration Guide for Users

**Update user scripts**:
```bash
# OLD (will break):
synthetic-dividend-tool research optimal-rebalancing --profit 50 --qty 10000

# NEW:
synthetic-dividend-tool research optimal-rebalancing --profit-pct 50 --initial-qty 10000
```

**Deprecation warning approach** (alternative to hard break):
```python
# In argument parsing:
if args.profit:
    warnings.warn("--profit is deprecated, use --profit-pct", DeprecationWarning)
    args.profit_pct = args.profit
```

---

## Documentation Updates

### Files to Update

1. **README.md**: Add return adjustment section
2. **docs/TOOL_USE_CASES.md**: ✅ Already created
3. **theory/RETURN_ADJUSTMENT_FRAMEWORK.md**: ✅ Already created
4. **CHANGELOG.md**: Document breaking changes

### Example README section:

```markdown
## Return Adjustments

View returns in three dimensions:

- **Nominal**: How much money did I make?
- **Real**: Did I beat inflation?
- **Alpha**: Did I beat the market?

```bash
# Show all three:
synthetic-dividend-tool backtest --ticker NVDA --start 2024-01-01 --end 2024-12-31 --adjust-both

Output:
  Nominal: +150% ($15,000)
  Real: +135% ($13,520) - beat inflation
  Alpha: +110% ($11,000 vs VOO) - crushed market
```

See [docs/TOOL_USE_CASES.md](docs/TOOL_USE_CASES.md) for complete guide.
```

---

## Implementation Checklist

### Must-Have (Phase 1-2)
- [ ] Fix argument name inconsistencies (profit, qty)
- [ ] Add return adjustment flags to all subcommands
- [ ] Create `src/models/return_adjustments.py` utility module
- [ ] Add CPI asset support (proxy with VTIP or add FRED provider)
- [ ] Update help text with new examples

### Should-Have (Phase 3-4)
- [ ] Integrate adjustments into backtest command
- [ ] Integrate adjustments into compare batch
- [ ] Integrate adjustments into research commands
- [ ] Add CSV column outputs for adjusted returns
- [ ] Write unit tests for adjustment calculations

### Nice-to-Have (Phase 5)
- [ ] Add verbose/compact output format choice
- [ ] Create deprecation warnings for old argument names
- [ ] Add FRED provider for official CPI data
- [ ] Create visualization for nominal vs real vs alpha
- [ ] Add pre-commit hook to enforce argument naming standard

---

## Summary

This plan achieves:

✅ **Argument consistency**: All subcommands use identical names  
✅ **Return adjustments**: Inflation and market adjustments available everywhere  
✅ **Extensibility**: Uses existing Asset provider system  
✅ **Documentation**: Theory docs + use case guide + inline help  
✅ **Testing**: Unit and integration test coverage  

**Estimated effort**: 2-3 days implementation + 1 day testing + 0.5 day docs
