# Return Adjustment Framework

**Author**: Rick Sladkey
**Date**: October 27, 2025
**Purpose**: Standardize how returns are displayed across all tool subcommands with inflation and market adjustments

---

## Overview

Portfolio returns can be expressed in three fundamentally different ways, each answering a different economic question:

1. **Nominal Returns**: "How much money did I make?"
2. **Inflation-Adjusted Returns**: "Is my money worth as much as it used to be?"
3. **Market-Adjusted Returns**: "Did I beat the market?"

This framework provides a **unified mechanism** across all synthetic-dividend-tool subcommands to display returns in any or all of these formats.

---

## The Three Return Perspectives

### 1. Nominal Returns (Default)

**Question**: How much money did I make in absolute dollar terms?

**Calculation**:
```
nominal_return = (final_value - initial_investment) / initial_investment
nominal_dollars = final_value - initial_investment
```

**Use Cases**:
- Tax reporting (IRS cares about nominal gains)
- Portfolio valuation (bank statements show nominal dollars)
- Withdrawal planning (spending nominal dollars)

**Example**:
```
Initial: $10,000
Final: $15,000
Nominal Return: +50.0% ($5,000 gain)
```

**Pros**: Simple, matches bank statements
**Cons**: Ignores purchasing power, ignores opportunity cost

---

### 2. Inflation-Adjusted Returns (Real Returns)

**Question**: Is my money worth as much as it used to be? Did I preserve purchasing power?

**Calculation**:
```
Using CPI (Consumer Price Index):
 cpi_multiplier = CPI_end / CPI_start
 inflation_adjusted_value = final_value / cpi_multiplier
 real_return = (inflation_adjusted_value - initial_investment) / initial_investment
 real_dollars = inflation_adjusted_value - initial_investment
```

**Use Cases**:
- Retirement planning (will I maintain living standards?)
- Long-term wealth preservation
- Cross-decade comparisons (1980s vs 2020s)
- International comparisons (high-inflation environments)

**Example**:
```
Initial: $10,000 (Jan 2020, CPI = 257.97)
Final: $15,000 (Jan 2024, CPI = 308.42)
CPI multiplier: 308.42 / 257.97 = 1.1955

Nominal: +50.0% ($5,000 gain)
Real (inflation-adjusted): $15,000 / 1.1955 = $12,548
Real Return: +25.5% ($2,548 real gain)

Interpretation: Made $5,000 nominal, but $2,452 lost to inflation
```

**Pros**: Reflects purchasing power, meaningful for long horizons
**Cons**: CPI methodology debates, regional variations

---

### 3. Market-Adjusted Returns (Alpha)

**Question**: Did I beat a passive index investment? Was active management worth it?

**Calculation**:
```
Using market benchmark (e.g., S&P 500 via VOO):
 benchmark_return = (benchmark_end - benchmark_start) / benchmark_start
 market_adjusted_return = portfolio_return - benchmark_return
 market_adjusted_dollars = portfolio_gain - (initial_investment × benchmark_return)
```

**Use Cases**:
- Strategy evaluation (is volatility harvesting worth the complexity?)
- Manager performance (active vs passive)
- Risk-adjusted analysis (did extra risk pay off?)
- Opportunity cost measurement

**Example**:
```
Initial: $10,000
Final: $15,000
Portfolio Return: +50.0%

S&P 500 (VOO):
 Start: $400
 End: $560
 Market Return: +40.0%

Market-Adjusted Return: 50% - 40% = +10.0%
Market-Adjusted Dollars: $5,000 - $4,000 = +$1,000

Interpretation: Beat market by 10%, earned $1,000 alpha
```

**Pros**: Contextualizes performance, measures opportunity cost
**Cons**: Benchmark selection matters, doesn't account for risk differences

---

## Unified CLI Interface

### Standard Arguments (All Subcommands)

**Return Adjustment Flags**:
```bash
--adjust-inflation # Show inflation-adjusted returns
--adjust-market # Show market-adjusted returns
--adjust-both # Show both adjustments

# Data source specifications:
--inflation-ticker CPI # Ticker for inflation data (default: CPI)
--market-ticker VOO # Ticker for market benchmark (default: VOO for S&P 500)
```

**Alternative Benchmark Tickers**:
- `VOO` - S&P 500 (default, broad US market)
- `VTI` - Total US stock market
- `QQQ` - Nasdaq 100 (tech-heavy)
- `AGG` - US aggregate bonds
- `GLD` - Gold (inflation hedge)
- `BIL` - T-Bills (risk-free rate)

### Implementation Strategy

**Leverage Existing Asset Provider System**:
Since we already have `Asset("VOO")` and can add `Asset("CPI")`, the adjustment mechanism reuses existing infrastructure:

```python
# In backtest or analysis code:
if args.adjust_inflation:
 cpi_asset = Asset("CPI")
 cpi_prices = cpi_asset.get_prices(start_date, end_date)
 # Calculate adjustment...

if args.adjust_market:
 market_asset = Asset(args.market_ticker) # default "VOO"
 market_prices = market_asset.get_prices(start_date, end_date)
 # Calculate adjustment...
```

This approach:
[OK] Zero new data fetching logic (reuses `Asset` system)
[OK] Works with any ticker (flexibility)
[OK] Supports future providers (e.g., FRED for official CPI)
[OK] Consistent caching behavior

---

## Output Formats

### Compact Format (Single Line)

```
Return: +50.0% ($5,000) | Real: +25.5% ($2,548) | Alpha: +10.0% ($1,000 vs VOO)
```

### Verbose Format (Multi-Line)

```
======================================================================
RETURN BREAKDOWN
======================================================================

Nominal Return:
 Total Return: +50.0%
 Dollar Gain: $5,000.00
 Initial Investment: $10,000.00
 Final Value: $15,000.00

Inflation-Adjusted Return (CPI):
 Real Return: +25.5%
 Real Dollar Gain: $2,548.00
 Purchasing Power Lost: $2,452.00
 CPI Multiplier: 1.196
 Period Inflation: +19.6%

Market-Adjusted Return (vs VOO):
 Alpha: +10.0%
 Alpha Dollars: $1,000.00
 Portfolio Return: +50.0%
 Market Return: +40.0%
 Outperformance: $1,000.00

======================================================================
```

### CSV Output (for research commands)

```csv
ticker,start_date,end_date,nominal_return,nominal_dollars,real_return,real_dollars,alpha,alpha_dollars,benchmark
NVDA,2024-01-01,2024-12-31,150.5,15050.00,135.2,13520.00,110.5,11050.00,VOO
```

---

## Subcommand Integration Examples

### backtest

```bash
# Nominal only (default)
synthetic-dividend-tool backtest --ticker NVDA --start 2024-01-01 --end 2024-12-31

# With inflation adjustment
synthetic-dividend-tool backtest --ticker NVDA --start 2024-01-01 --end 2024-12-31 \
 --adjust-inflation

# With market adjustment (vs custom benchmark)
synthetic-dividend-tool backtest --ticker GLD --start 2024-01-01 --end 2024-12-31 \
 --adjust-market --market-ticker SPY

# Both adjustments
synthetic-dividend-tool backtest --ticker NVDA --start 2024-01-01 --end 2024-12-31 \
 --adjust-both --market-ticker QQQ
```

### research optimal-rebalancing

```bash
# Add adjusted returns to output CSV
synthetic-dividend-tool research optimal-rebalancing \
 --start 2024-01-01 --end 2024-12-31 \
 --output results.csv \
 --adjust-both

# Output CSV will include: nominal_return, real_return, alpha columns
```

### compare batch

```bash
# Compare with all three return perspectives
synthetic-dividend-tool compare batch \
 --tickers NVDA AAPL GLD \
 --strategies sd8 sd16 buyhold \
 --start 2024-01-01 --end 2024-12-31 \
 --adjust-both \
 --output comparison.csv
```

### analyze volatility-alpha

```bash
# Auto-suggest SD parameter with inflation-adjusted analysis
synthetic-dividend-tool analyze volatility-alpha \
 --ticker NVDA --start 2024-01-01 --end 2024-12-31 \
 --adjust-inflation \
 --plot
```

---

## CPI Data Provider Implementation

### Asset("CPI") Behavior

**Option 1: Use CPI ETF Proxy** (Quick implementation)
```python
# Map "CPI" to inflation-tracking ETF
Asset("CPI") → Asset("VTIP") # Vanguard Short-Term Inflation-Protected Securities
```

**Option 2: FRED Data Provider** (Accurate, requires new provider)
```python
# Custom provider for Federal Reserve Economic Data
class FREDAssetProvider(AssetProvider):
 def get_prices(self, start, end):
 # Fetch CPI-U (Consumer Price Index - All Urban Consumers)
 # Series: CPIAUCSL
 ...
```

**Option 3: Manual CSV** (Offline, reproducible)
```python
# CSVAssetProvider loads cache/CPI.csv
# User maintains CPI data manually or via script
```

**Recommended**: Start with Option 1 (VTIP proxy), add Option 2 (FRED) later for precision.

---

## Standard Argument Names (Consistency Mandate)

**All subcommands MUST use identical names for identical concepts**:

| Concept | Standard Argument | Variants to Avoid |
|---------|------------------|-------------------|
| Asset ticker | `--ticker` | ~~--symbol, --asset, --stock~~ |
| Start date | `--start` | ~~--start-date, --begin, --from~~ |
| End date | `--end` | ~~--end-date, --finish, --to~~ |
| Initial quantity | `--initial-qty` | ~~--qty, --shares, --quantity~~ |
| Rebalance size | `--sd-n` | ~~--rebalance, --trigger~~ |
| Profit sharing | `--profit-pct` | ~~--profit, --sharing, --profit-sharing~~ |
| Output file | `--output` | ~~--out, --file, --csv~~ |
| Inflation ticker | `--inflation-ticker` | Default: `CPI` |
| Market benchmark | `--market-ticker` | Default: `VOO` |
| Adjust for inflation | `--adjust-inflation` | Boolean flag |
| Adjust for market | `--adjust-market` | Boolean flag |
| Both adjustments | `--adjust-both` | Boolean flag |

**Enforcement**: All new subcommands and refactored old ones must follow this standard.

---

## Use Case Examples

### Use Case 1: Retirement Planning (Inflation Focus)

**Question**: "Will my synthetic dividend strategy preserve purchasing power over 30 years?"

```bash
synthetic-dividend-tool backtest \
 --ticker VOO \
 --start 1995-01-01 \
 --end 2025-01-01 \
 --initial-qty 1000 \
 --sd-n 8 \
 --adjust-inflation \
 --verbose
```

**Expected Output**:
```
Nominal Return: +1,240% ($124,000)
Real Return: +523% ($52,300)
Purchasing Power Lost to Inflation: $71,700 (58% erosion)

Conclusion: Strategy significantly beat inflation but shows
 importance of accounting for purchasing power.
```

---

### Use Case 2: Strategy Evaluation (Market Focus)

**Question**: "Does volatility harvesting beat passive VOO investment?"

```bash
synthetic-dividend-tool compare batch \
 --tickers NVDA AAPL MSFT \
 --strategies sd8 buyhold \
 --start 2024-01-01 --end 2024-12-31 \
 --adjust-market \
 --market-ticker VOO \
 --output vs_voo.csv
```

**Expected CSV Output**:
```csv
ticker,strategy,nominal_return,alpha_vs_voo
NVDA,sd8,145.2,+12.3
NVDA,buyhold,142.8,+9.9
AAPL,sd8,28.5,-4.4
AAPL,buyhold,25.1,-7.8
```

**Conclusion**: SD8 beats buy-and-hold, but AAPL underperforms VOO overall.

---

### Use Case 3: High Inflation Period Analysis

**Question**: "How did my portfolio perform during 2021-2023 high inflation?"

```bash
synthetic-dividend-tool backtest \
 --ticker GLD \
 --start 2021-01-01 \
 --end 2023-12-31 \
 --adjust-both \
 --market-ticker VOO
```

**Expected Output**:
```
Nominal Return: +15.0%
Real Return: -5.2% (inflation ate 20.2% of purchasing power)
Alpha vs VOO: +22.1% (gold outperformed stocks during inflation)

Conclusion: Lost purchasing power nominally, but beat equity market.
 Gold hedge worked relative to stocks but not absolute.
```

---

### Use Case 4: Cross-Asset Comparison (Complete Picture)

**Question**: "Which asset class performed best when accounting for inflation AND market?"

```bash
synthetic-dividend-tool compare batch \
 --tickers NVDA GLD BIL AGG VOO \
 --strategies sd8 \
 --start 2024-01-01 --end 2024-12-31 \
 --adjust-both \
 --market-ticker VOO \
 --output all_metrics.csv
```

**Expected Output**:
```
Asset Nominal Real Alpha_vs_VOO Winner_Dimension
NVDA +150% +135% +110% All three
GLD +8% -5% -32% None (lost real value)
BIL +4.5% -8% -35% None (cash drag)
AGG +3% -10% -37% None (bonds struggled)
VOO +40% +27% 0% Benchmark
```

**Conclusion**: Tech (NVDA) dominated all dimensions. GLD/BIL/AGG lost real value despite nominal gains.

---

## Implementation Checklist

### Phase 1: Core Infrastructure
- [ ] Add `--adjust-inflation`, `--adjust-market`, `--adjust-both` to all subcommands
- [ ] Add `--inflation-ticker` (default: CPI) and `--market-ticker` (default: VOO)
- [ ] Standardize ALL argument names across subcommands (use consistency table)
- [ ] Create `calculate_adjusted_returns()` utility function
- [ ] Add CPI asset provider (start with VTIP proxy)

### Phase 2: Output Formatting
- [ ] Implement compact return display format
- [ ] Implement verbose return breakdown format
- [ ] Add adjusted return columns to CSV outputs
- [ ] Update all print statements to show adjustments when requested

### Phase 3: Documentation
- [ ] Update tool help text with adjustment examples
- [ ] Add examples to README.md
- [ ] Create tutorial: "Understanding Your Returns: Nominal vs Real vs Alpha"
- [ ] Document CPI data sourcing methodology

### Phase 4: Testing
- [ ] Unit tests for adjustment calculations
- [ ] Integration tests with real CPI/market data
- [ ] Verify CSV output includes all columns
- [ ] Test edge cases (deflation, market crash, outliers)

---

## Technical Notes

### CPI Data Nuances

**CPI-U vs CPI-W**: Use CPI-U (All Urban Consumers) as it's the standard headline inflation measure.

**Frequency**: CPI is monthly; interpolate for daily if needed:
```python
# Linear interpolation between monthly CPI readings
daily_cpi = cpi_monthly.resample('D').interpolate(method='linear')
```

**Base Year**: CPI is an index (1982-84 = 100). Only relative changes matter, not absolute values.

### Market Benchmark Selection Guidance

| Benchmark | Use When... |
|-----------|------------|
| **VOO** (S&P 500) | Default, broad US equity |
| **VTI** (Total Market) | Include small/mid caps |
| **QQQ** (Nasdaq 100) | Tech-heavy portfolio |
| **AGG** (Aggregate Bonds) | Fixed income comparison |
| **GLD** (Gold) | Inflation hedge evaluation |
| **BIL** (T-Bills) | Risk-free rate baseline |
| **Custom** | Specific strategy benchmark |

### Calculation Precision

**Order of Operations for Combined Adjustments**:
```python
# Option 1: Sequential (inflation first, then market)
real_value = nominal_value / cpi_multiplier
real_return = (real_value - initial) / initial
market_real_return = (market_value / cpi_multiplier - initial) / initial
alpha = real_return - market_real_return

# Option 2: Independent (both relative to nominal)
real_return = nominal_return - inflation_rate
alpha = nominal_return - market_return
```

**Recommendation**: Use Option 1 (sequential) for reporting clarity. Real alpha is more meaningful than nominal alpha when inflation is high.

---

## Summary

This framework provides:

[OK] **Three return perspectives**: Nominal, Real, Alpha
[OK] **Unified CLI interface**: Same flags across all subcommands
[OK] **Argument consistency**: Standard names eliminate confusion
[OK] **Flexible benchmarks**: Any ticker as inflation/market reference
[OK] **Extensible design**: Reuses Asset provider system
[OK] **Clear use cases**: Retirement, evaluation, comparison, analysis

**Core Insight**: Returns are multi-dimensional. Show all dimensions, let users decide which matters most for their goals.
