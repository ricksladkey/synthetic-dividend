# Price Normalization Feature

## Overview

Price normalization ensures that all backtests using the same rebalance trigger (e.g., sd8) hit brackets at the same relative positions, making bracket placement **deterministic** and **mathematically convenient**.

## The Problem It Solves

**Before normalization:**
- Starting a backtest at $50 creates brackets at: $50.00, $54.53, $59.46, ...
- Starting a backtest at $200 creates brackets at: $200.00, $218.10, $237.84, ...
- **Different bracket positions** make comparisons difficult and arbitrary

**After normalization:**
- Both backtests align to standard bracket positions: 1.0, 1.0905, 1.1893, 1.2968, ...
- Starting at $50 scales to bracket n=45 → $49.34
- Starting at $200 scales to bracket n=61 → $197.32
- **Same relative bracket structure** makes comparisons deterministic

## How It Works

### Mathematical Foundation

For a given rebalance trigger `r`, brackets exist at positions:

```
price = 1.0 × (1 + r)^n
```

Where `n` is an integer bracket number.

For sd8 (r = 9.05%):
- Bracket n=0 → $1.00
- Bracket n=1 → $1.0905
- Bracket n=2 → $1.1893
- Bracket n=55 → $117.38
- Bracket n=56 → $128.00

### Normalization Algorithm

1. **Calculate bracket number**: `n = log(start_price) / log(1 + r)`
2. **Round to nearest integer**: `n_int = round(n)`
3. **Calculate target price**: `target = (1 + r)^n_int`
4. **Scale all prices**: `scale_factor = target / start_price`

### Example

Original start price: $120.50
Rebalance trigger: 9.05% (sd8)

```python
n = log(120.50) / log(1.0905) = 54.95
n_int = round(54.95) = 55
target = 1.0905^55 = 117.38
scale = 117.38 / 120.50 = 0.9741

# All prices multiplied by 0.9741
# Start price becomes: 120.50 × 0.9741 = 117.38 (bracket n=55)
```

## Usage

### In Backtests

```python
from src.models.backtest import run_algorithm_backtest, SyntheticDividendAlgorithm

algo = SyntheticDividendAlgorithm(
    rebalance_size_pct=9.05,
    profit_sharing_pct=50.0,
    buyback_enabled=True,
)

txns, results = run_algorithm_backtest(
    df=price_df,
    ticker="NVDA",
    initial_qty=1000,
    start_date=date(2020, 1, 1),
    end_date=date(2024, 1, 1),
    algo=algo,
    normalize_prices=True,  # Enable normalization
)
```

### In Order Calculator

The order calculator now shows bracket positions:

```bash
python -m src.tools.order_calculator \
    --ticker NVDA \
    --holdings 1000 \
    --last-price 120.50 \
    --current-price 125.30 \
    --sdn 8 \
    --profit 50
```

Output includes:
```
📍 BRACKET POSITIONS
  Your position is on bracket n=55
  
  Standard bracket ladder for sd8 (normalized to 1.0):
    Bracket n=  54  →  $  107.63  [BUY TARGET]
    Bracket n=  55  →  $  117.38  [YOUR POSITION]
    Bracket n=  56  →  $  128.00  [SELL TARGET]
```

## Benefits

### 1. **Deterministic Comparisons**
All backtests on the same stock with the same trigger use identical bracket positions, eliminating arbitrary differences based on start date.

### 2. **Mathematical Convenience**
Brackets at clean integer powers of `(1 + r)` make calculations simpler and more intuitive.

### 3. **Cross-Asset Consistency**
Different assets with the same strategy (e.g., sd8) follow the same bracket structure, just at different absolute levels.

### 4. **Easier Analysis**
You can compare:
- "This stock is on bracket n=55"
- "That stock is on bracket n=42"
- Both using sd8, but at different price levels

## Test Results

The unit tests validate:

1. **Same transaction counts**: Different starting prices produce identical transaction counts
2. **Integer bracket positions**: Normalized prices land exactly on integer brackets
3. **Identical progressions**: All tests follow the same relative bracket pattern
4. **Backward compatibility**: Disabled by default (opt-in with `normalize_prices=True`)
5. **Multiple triggers**: Works with sd4, sd8, sd16, etc.

Example test output:
```
$50 start:   Bracket sequence: [46, 48, 48, 49, 50, 51, 52, 53]
$200 start:  Bracket sequence: [62, 64, 64, 65, 66, 67, 68, 69]
$1000 start: Bracket sequence: [81, 83, 83, 84, 85, 86, 87, 88]

Relative progression (all identical): [0, 2, 2, 3, 4, 5, 6, 7]
```

## Implementation Details

### Files Modified

1. **src/models/backtest.py**
   - Added `normalize_prices` parameter
   - Added normalization logic before backtest execution
   - Scales all OHLC prices by calculated factor

2. **src/tools/order_calculator.py**
   - Added bracket position calculations
   - Display bracket ladder in output
   - Show normalized prices alongside actual prices

3. **tests/test_price_normalization.py** (new)
   - 5 comprehensive unit tests
   - Validates deterministic behavior
   - Tests multiple scenarios and triggers

### Backward Compatibility

- Default: `normalize_prices=False` (no change to existing behavior)
- Opt-in: Set `normalize_prices=True` to enable feature
- All existing tests pass without modification

## Future Enhancements

Potential additions:
- Command-line flag for experiments: `--normalize`
- Bracket visualization in reports
- Cross-stock bracket comparison tools
- Bracket heatmap showing where trades occur

## Mathematical Properties

### Symmetry

Brackets maintain perfect symmetry:
- Buy at bracket n → can sell back at bracket n+1
- Sell at bracket n+1 → can buy back at bracket n

### Spacing

Bracket spacing is exponential, not linear:
- Each bracket is `(1 + r)` times the previous
- For sd8: each bracket is 1.0905× the previous
- This matches the multiplicative nature of price movements

### Universality

All assets using sd8 share the same bracket structure:
- NVDA at $120 might be on bracket n=55
- BTC at $90,000 might be on bracket n=109
- Both follow the same mathematical pattern

## Conclusion

Price normalization transforms arbitrary bracket placement into a deterministic, mathematically elegant system. It enables meaningful cross-backtest comparisons while maintaining the core volatility harvesting mechanics unchanged.
