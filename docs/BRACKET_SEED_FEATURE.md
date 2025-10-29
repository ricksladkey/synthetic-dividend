# Bracket Seed Control Feature

## Overview

The bracket seed control feature allows you to align all price bracket calculations to a common reference point, ensuring deterministic and reproducible behavior across different entry prices.

## Problem Statement

Without a bracket seed, each transaction price creates its own bracket ladder:

```
Trader A enters at $120.50 → Buy: $110.50, Sell: $131.41
Trader B enters at $121.00 → Buy: $110.96, Sell: $131.95
Trader C enters at $119.80 → Buy: $109.86, Sell: $130.64
```

This makes it difficult to:
- Compare results between different traders or runs
- Verify that backtests match real-world trading
- Pool orders or coordinate strategies
- Ensure reproducibility

## Solution

With a bracket seed (e.g., 100.0), all prices normalize to the same bracket ladder:

```
All traders with seed 100.0:
  Entry $120.50, $121.00, or $119.80 → All normalize to bracket 55
  → Buy: $107.59, Sell: $127.95 (identical for all)
```

## Usage

### Command Line (Order Calculator)

```bash
# Without seed (default behavior)
python -m src.tools.order_calculator \
  --ticker NVDA \
  --holdings 1000 \
  --last-price 120.50 \
  --current-price 125.30 \
  --sdn 8 \
  --profit 50

# With bracket seed for aligned positions
python -m src.tools.order_calculator \
  --ticker NVDA \
  --holdings 1000 \
  --last-price 120.50 \
  --current-price 125.30 \
  --sdn 8 \
  --profit 50 \
  --bracket-seed 100.0
```

### Python API

```python
from src.algorithms.synthetic_dividend import SyntheticDividendAlgorithm

# Create algorithm with bracket seed
algo = SyntheticDividendAlgorithm(
    rebalance_size=0.0905,      # sd8
    profit_sharing=0.5,          # 50%
    buyback_enabled=True,
    bracket_seed=100.0           # Align to brackets based on $100
)

# Or pass via params dict
algo = SyntheticDividendAlgorithm(
    rebalance_size=0.0905,
    profit_sharing=0.5,
    params={"bracket_seed": 100.0}
)
```

### Direct Function Call

```python
from src.models.backtest_utils import calculate_synthetic_dividend_orders

orders = calculate_synthetic_dividend_orders(
    holdings=100,
    last_transaction_price=120.50,
    rebalance_size=0.0905,
    profit_sharing=0.5,
    bracket_seed=100.0  # Optional
)
```

## How It Works

1. **Without seed**: Orders are calculated directly from the transaction price
   ```
   Buy:  P / (1 + r)
   Sell: P * (1 + r)
   ```

2. **With seed**: Transaction price is first normalized to the nearest bracket
   ```
   bracket_n = log(P) / log(1 + r)
   normalized_P = (1 + r) ^ round(bracket_n)
   
   Buy:  normalized_P / (1 + r)
   Sell: normalized_P * (1 + r)
   ```

This ensures all calculations align to the same geometric ladder defined by the bracket spacing.

## Benefits

✓ **Deterministic**: Same bracket positions every time
✓ **Reproducible**: Backtests match real-world trading
✓ **Comparable**: Easy to compare different entry points
✓ **Collaborative**: Multiple traders can use the same brackets
✓ **Backward Compatible**: Optional parameter, defaults to None (original behavior)

## Example

See `examples/demo_bracket_seed.py` for a complete demonstration:

```bash
python examples/demo_bracket_seed.py
```

## Technical Details

- The seed value itself doesn't need to be "special" - any positive price works
- The seed establishes the bracket ladder, and all prices normalize to that ladder
- Bracket numbers are consistent: a seed of 100.0 with sd8 puts it on bracket 53
- Order quantities are unaffected by the seed (only prices change)
- Invalid seeds (≤0) are ignored, falling back to default behavior
