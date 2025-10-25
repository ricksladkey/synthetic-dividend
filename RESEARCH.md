# Research: Optimal Rebalancing Frequencies

## Overview

This document explains the **exponential scaling** (`sdN`) parameterization for the Synthetic Dividend algorithm and provides research tools for determining optimal rebalancing frequencies across different asset classes.

## Exponential Scaling: The `sdN` Convention

### Formula

```
sdN → rebalance_trigger = (2^(1/N) - 1) × 100%
```

Where **N** = number of equal **geometric** steps to reach a doubling (100% gain).

### Rationale

Unlike arithmetic spacing (dividing 100% by N), exponential scaling ensures **equal proportional gains** between each rebalance. This is critical because:

1. **Geometric consistency**: Each rebalance represents the same percentage move
2. **Volatility adaptation**: More volatile assets need higher N (more frequent checks)
3. **Mathematical elegance**: Based on roots of 2 (doubling)
4. **Scale invariance**: Works equally well for $100 stocks and $1,000 stocks

### Reference Table

| sdN  | Trigger % | Description                           | Use Case                        |
|------|-----------|---------------------------------------|---------------------------------|
| sd4  | 18.92%    | Aggressive (high volatility)          | Crypto, highly volatile stocks  |
| sd5  | 14.87%    | Aggressive-moderate                   | Growth stocks in bull markets   |
| sd6  | 12.25%    | Moderate-aggressive                   | Tech growth stocks              |
| **sd8**  | **9.05%**     | **Balanced (legacy default)**         | **General growth stocks**       |
| sd10 | 7.18%     | Moderate                              | Mature growth stocks            |
| sd12 | 5.95%     | Moderate-conservative                 | Large cap stocks                |
| sd16 | 4.43%     | Conservative                          | Stable assets, commodities      |
| sd20 | 3.53%     | Very conservative                     | Index ETFs, low volatility      |
| sd24 | 2.93%     | Ultra-conservative                    | Bond proxies, defensive assets  |

### Examples

```bash
# Balanced approach (default)
python -m src.run_model NVDA 2024-01-01 2025-01-01 sd8

# Aggressive for high volatility
python -m src.run_model BTC-USD 2024-01-01 2025-01-01 sd4

# Conservative for stable assets
python -m src.run_model GLD 2024-01-01 2025-01-01 sd16

# Custom profit sharing
python -m src.run_model NVDA 2024-01-01 2025-01-01 sd8,75  # 75% profit sharing
```

## Asset Classes

### Growth Stocks (High Volatility)
**Tickers**: NVDA, GOOG, PLTR, MSTR, SHOP  
**Recommended**: `sd6, sd8, sd10, sd12`  
**Rationale**: High volatility requires more frequent rebalancing to capture volatility alpha

### Cryptocurrencies (Extreme Volatility)
**Tickers**: BTC-USD, ETH-USD  
**Recommended**: `sd4, sd6, sd8, sd10`  
**Rationale**: Extreme price swings benefit from aggressive rebalancing

### Commodities (Moderate Volatility)
**Tickers**: GLD, SLV  
**Recommended**: `sd8, sd10, sd12, sd16`  
**Rationale**: Lower volatility means less frequent rebalancing needed

### Index ETFs (Low-Moderate Volatility)
**Tickers**: SPY, QQQ, DIA  
**Recommended**: `sd10, sd12, sd16, sd20`  
**Rationale**: Stable indices work well with conservative rebalancing

## Research Tools

### Quick Single-Asset Test

Test optimal sdN for a specific asset over 1 year:

```bash
python -m src.research.optimal_rebalancing --ticker NVDA --quick
```

### Asset Class Sweep

Test all tickers in an asset class:

```bash
python -m src.research.optimal_rebalancing \
    --asset-class growth_stocks \
    --start 2020-01-01 \
    --end 2025-01-01 \
    --output growth_stocks_results.csv
```

### Comprehensive Multi-Asset Study

Test all asset classes with recommended sdN values:

```bash
python -m src.research.optimal_rebalancing \
    --start 2020-01-01 \
    --end 2025-01-01 \
    --output comprehensive_results.csv
```

### Custom Parameters

```bash
python -m src.research.optimal_rebalancing \
    --ticker NVDA \
    --start 2023-01-01 \
    --end 2024-01-01 \
    --profit 75 \
    --qty 5000 \
    --output nvda_75pct_profit.csv
```

## Research Questions

The framework is designed to answer:

1. **Optimal N by Asset Class**: What sdN value maximizes risk-adjusted returns for each volatility regime?

2. **Volatility Correlation**: Does higher realized volatility correlate with optimal N? (Hypothesis: Yes, higher vol → lower N)

3. **Time Period Sensitivity**: Are optimal N values consistent across bull markets, bear markets, and sideways markets?

4. **Transaction Cost Trade-offs**: What is the point of diminishing returns where transaction costs outweigh volatility harvesting?

5. **Profit Sharing Interaction**: Does optimal N change when profit sharing percentage varies?

## Output Format

Research scripts generate CSV files with the following metrics:

- `ticker`: Asset symbol
- `asset_class`: Category (growth_stocks, crypto, commodities, indices)
- `strategy`: Full strategy identifier (e.g., "sd8", "sd12,75")
- `sd_n`: The N value used
- `profit_pct`: Profit sharing percentage
- `rebalance_trigger`: Calculated trigger percentage
- `total_return_pct`: Total return vs initial investment
- `max_drawdown_pct`: Maximum peak-to-trough decline
- `sharpe_ratio`: Risk-adjusted return metric
- `transaction_count`: Number of rebalances executed
- `final_holdings`: Share count at end
- `final_bank`: Cash balance at end
- `final_value`: Total portfolio value at end

## Hypothesis Framework

### H1: Volatility-Optimal Mapping

**Hypothesis**: Each asset class has an optimal N that balances volatility harvesting against transaction costs.

**Test**: Run comprehensive sweep and identify peak Sharpe ratio for each asset class.

**Expected**: Lower N (more frequent) for high volatility, higher N (less frequent) for stable assets.

### H2: Universal Goldilocks Zone

**Hypothesis**: Despite varying volatility, most assets perform well with `sd8` (9.05% trigger).

**Test**: Compare sd8 performance against class-optimal N across all assets.

**Expected**: sd8 should be within 90% of optimal for most assets, justifying it as a universal default.

### H3: Profit Sharing Independence

**Hypothesis**: Optimal N is independent of profit sharing percentage.

**Test**: Run same asset with varying profit_pct (25%, 50%, 75%, 100%) and check if optimal N changes.

**Expected**: Optimal N remains constant; profit sharing affects cash generation but not rebalancing frequency.

## Mathematical Background

### Why Exponential (Geometric) Scaling?

Consider a stock that doubles from $100 to $200:

**Arithmetic spacing** (linear):
- Trigger every 25% → rebalances at $125, $150, $175, $200
- Percentage gains: 25%, 20%, 16.67%, 14.29% (uneven!)

**Exponential spacing** (geometric):
- sd4: Trigger = 18.92%
- Rebalances at $118.92, $141.39, $168.08, $200
- Percentage gains: 18.92%, 18.92%, 18.92%, 18.92% (uniform!)

This ensures **consistent volatility harvesting** regardless of price level.

### Derivation

To find N equal geometric steps from price P to 2P:

```
P × r^N = 2P
r^N = 2
r = 2^(1/N)
trigger = r - 1
```

Therefore: `rebalance_trigger = (2^(1/N) - 1) × 100%`

## Next Steps

1. **Run baseline study**: Execute comprehensive sweep on 5-year history (2020-2025)
2. **Analyze results**: Identify optimal N per asset class
3. **Validate hypotheses**: Test H1, H2, H3
4. **Publish findings**: Update README with empirical recommendations
5. **Iterate**: Expand to more assets and time periods

## References

- `src/research/asset_classes.py` - Asset class definitions and sdN lookup
- `src/research/optimal_rebalancing.py` - Multi-asset research script
- `src/models/backtest.py` - Core algorithm implementation
- `INVESTING_THEORY.md` - Theoretical foundation

---

**Last Updated**: October 2025  
**Status**: Research framework complete, awaiting empirical studies
