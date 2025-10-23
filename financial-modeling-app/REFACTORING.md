# Synthetic Dividend Algorithm - Unified Implementation

## Overview

Successfully refactored the synthetic dividend implementation to use a **single unified algorithm class** with a `buyback_enabled` parameter instead of maintaining two separate classes.

## Architecture

### Before (Two Classes)
```python
class SyntheticDividendAlgorithm:
    # Full algorithm with buybacks
    ...

class SyntheticDividendATHOnlyAlgorithm:
    # ATH-only sells, no buybacks
    ...
```

### After (One Unified Class)
```python
class SyntheticDividendAlgorithm:
    def __init__(self, rebalance_size_pct, profit_sharing_pct, 
                 buyback_enabled=True):
        """
        buyback_enabled=True  -> Full algorithm with buyback cycles
        buyback_enabled=False -> ATH-only sells, no buybacks
        """
```

## Usage

### Creating Algorithms Directly
```python
# Full algorithm
algo_full = SyntheticDividendAlgorithm(
    rebalance_size_pct=9.05,
    profit_sharing_pct=50,
    buyback_enabled=True
)

# ATH-only
algo_ath = SyntheticDividendAlgorithm(
    rebalance_size_pct=9.05,
    profit_sharing_pct=50,
    buyback_enabled=False
)
```

### Parsing from Name Strings
```python
# Full algorithm
algo1 = build_algo_from_name("synthetic-dividend/9.05%/50%")
# Returns: SyntheticDividendAlgorithm(9.05, 50, buyback_enabled=True)

# ATH-only
algo2 = build_algo_from_name("synthetic-dividend-ath-only/9.05%/50%")
# Returns: SyntheticDividendAlgorithm(9.05, 50, buyback_enabled=False)
```

## Implementation Details

### Unified State Management
```python
class SyntheticDividendAlgorithm(AlgorithmBase):
    def __init__(self, ...):
        self.buyback_enabled = buyback_enabled
        self.ath_price = 0.0  # Tracked for ATH-only mode
        self.total_volatility_alpha = 0.0  # For full mode
        # ... other state
```

### Conditional Logic in on_day()
```python
def on_day(self, date_, price_row, holdings, bank, history):
    if not self.buyback_enabled:
        # ATH-only mode: check for new ATH and sell
        if high > self.ath_price:
            self.ath_price = high
            if high >= self.next_sell_price:
                # Execute sell at new ATH
                ...
    else:
        # Full mode: check for both buy and sell opportunities
        if low <= self.next_buy_price:
            # Execute buy (buyback)
            ...
        if high >= self.next_sell_price:
            # Execute sell (profit-taking)
            ...
```

## Benefits

### Code Quality
- ✅ **Single Source of Truth**: One class for all synthetic dividend logic
- ✅ **DRY Principle**: Eliminated ~80 lines of duplicate code
- ✅ **Easier Maintenance**: Changes to core logic only needed in one place
- ✅ **Better Extensibility**: Easy to add more parameters/modes

### Testing
- ✅ All 9 unit tests pass
- ✅ Validator confirms identical behavior
- ✅ No regression in functionality

### Performance
- ✅ Same performance characteristics
- ✅ Minimal overhead from conditional logic

## Test Results

### Full Algorithm (buyback_enabled=True)
```
Command: synthetic-dividend/9.05%/50%
Holdings: 899 shares
Bank: $23,615.10
Total Return: 29.35%
Transactions: 26
```

### ATH-Only (buyback_enabled=False)
```
Command: synthetic-dividend-ath-only/9.05%/50%
Holdings: 881 shares
Bank: $20,273.12
Total Return: 24.77%
Transactions: 4
```

### Holdings Difference
- **18 shares** (899 - 881)
- Represents incomplete buyback cycles in full algorithm
- Expected behavior, not a bug

## API Compatibility

### Backward Compatible
All existing code continues to work without changes:
- ✅ `build_algo_from_name()` recognizes both name formats
- ✅ GUI dropdown options work unchanged
- ✅ CLI commands work unchanged
- ✅ Batch files work unchanged

### Command Line
```powershell
# Full algorithm
python -m src.run_model NVDA 10/22/2024 10/22/2025 "synthetic-dividend/9.05%/50%"

# ATH-only
python -m src.run_model NVDA 10/22/2024 10/22/2025 "synthetic-dividend-ath-only/9.05%/50%"

# Comparison
python -m src.compare.validator NVDA 10/22/2024 10/22/2025 9.05 50
```

## Future Enhancements

With the unified architecture, it's now easier to add:
1. **More modes**: Could add `profit_lock_enabled`, `trailing_stop`, etc.
2. **Dynamic parameters**: Change rebalance_size based on volatility
3. **Risk management**: Add position sizing, stop losses
4. **Portfolio features**: Multi-asset support

## Summary

The refactoring successfully unified two separate algorithm classes into a single, more maintainable implementation while preserving all functionality and test coverage. The code is now cleaner, easier to extend, and follows better software engineering practices.
