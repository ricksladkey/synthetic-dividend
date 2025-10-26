# Price Normalization

## Overview

Price normalization converts real historical prices to a standard $100 starting point. This enables deterministic comparisons across assets and timeframes.

---

## The Problem It Solves

**Without normalization**:
- BTC: $30,000 → need $30K to buy 1 unit
- NVDA: $450 → need $450 to buy 1 unit
- VOO: $400 → need $400 to buy 1 unit

**Challenges**:
- Can't compare "100 shares" across assets
- Different amounts of capital required
- Results vary based on arbitrary price levels

**With normalization**:
- All assets: $100 at start
- Buy 100 units = $10,000 regardless of asset
- Deterministic, comparable results

---

## How It Works

### Mathematical Foundation

**Normalization factor**:
```python
first_price = df.iloc[0]['Close']  # First historical price
normalization_factor = 100.0 / first_price
```

**Apply to all prices**:
```python
df['Close'] = df['Close'] × normalization_factor
df['Open'] = df['Open'] × normalization_factor
df['High'] = df['High'] × normalization_factor
df['Low'] = df['Low'] × normalization_factor
```

**Example**:
```
BTC original: $30,000, $31,500, $29,000
Factor: 100 / 30,000 = 0.00333
BTC normalized: $100, $105, $96.67
```

---

## Usage

### In Backtests

```python
from data.fetcher import load_data

# Automatic normalization
df = load_data('BTC-USD', start_date, end_date)
# df['Close'][0] == 100.0  (always!)

# Run backtest with normalized prices
result = run_algorithm_backtest(df, ...)
```

### In Order Calculator

```python
from tools.order_calculator import calculate_orders

# Normalizes prices internally
orders = calculate_orders(
    symbol='NVDA',
    start_date='2024-01-01',
    current_shares=100,
    current_price=450.0  # Will be normalized to $100 baseline
)
```

---

## Benefits

**1. Deterministic Comparisons**
- Same initial capital across all assets
- Apples-to-apples strategy comparison

**2. Mathematical Convenience**
- Easy mental math ($100 baseline)
- Percentage calculations intuitive

**3. Cross-Asset Consistency**
- 100 shares always = $10,000 initial
- Removes arbitrary price level effects

**4. Easier Analysis**
- Focus on returns, not absolute prices
- Charts visually comparable

---

## Mathematical Properties

**Symmetry preserved**:
- 10% gain normalized = 10% gain real
- Returns unchanged by normalization

**Scaling invariant**:
- All relationships preserved
- Only absolute price level changes

**Reversible**:
```python
real_price = normalized_price / normalization_factor
```

---

## Implementation

**Location**: `src/data/fetcher.py`

```python
def normalize_prices_to_100(df: pd.DataFrame) -> pd.DataFrame:
    first_close = df.iloc[0]['Close']
    factor = 100.0 / first_close
    
    df['Close'] *= factor
    df['Open'] *= factor
    df['High'] *= factor
    df['Low'] *= factor
    
    return df
```

**Backward compatibility**: All existing code works unchanged (normalization applied at data load)

---

**Last Updated**: October 2025
