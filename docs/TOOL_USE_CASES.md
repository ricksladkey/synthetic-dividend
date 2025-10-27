# Synthetic Dividend Tool - Primary Use Cases

**Quick Reference Guide**  
**Last Updated**: October 27, 2025

---

## Standard Arguments (Use Consistently Across All Subcommands)

| Argument | Type | Description | Default |
|----------|------|-------------|---------|
| `--ticker` | string | Asset ticker symbol | Required in most commands |
| `--start` | date | Start date (YYYY-MM-DD) | Command-specific |
| `--end` | date | End date (YYYY-MM-DD) | Command-specific |
| `--initial-qty` | int | Initial share quantity | 1000 |
| `--sd-n` | int | SD-N rebalance parameter (4-32) | 8 |
| `--profit-pct` | float | Profit sharing percentage | 50.0 |
| `--output` | path | Output file for results | None (stdout) |
| `--verbose` | flag | Detailed output | False |
| `--adjust-inflation` | flag | Show inflation-adjusted returns | False |
| `--adjust-market` | flag | Show market-adjusted returns | False |
| `--adjust-both` | flag | Show both adjustments | False |
| `--inflation-ticker` | string | Ticker for inflation data | CPI |
| `--market-ticker` | string | Ticker for market benchmark | VOO |

---

## Primary Use Cases

### 1. Quick Backtest (Single Asset)

**Question**: "How would synthetic dividend have performed on NVDA last year?"

```bash
synthetic-dividend-tool backtest \
    --ticker NVDA \
    --start 2024-01-01 \
    --end 2024-12-31 \
    --initial-qty 100
```

**Output**: Transaction log, final portfolio value, return percentage

**When to use**: Initial exploration, quick performance check

---

### 2. Auto-Suggest Optimal SD Parameter

**Question**: "What SD-N should I use for this asset?"

```bash
synthetic-dividend-tool analyze volatility-alpha \
    --ticker GLD \
    --start 2024-01-01 \
    --end 2024-12-31 \
    --plot
```

**Output**: 
- Recommended SD-N based on asset volatility
- Volatility alpha analysis
- Price chart with recommended brackets (if --plot)
- Transaction overlay showing where trades would occur

**When to use**: Setting up new asset, unsure about parameters

---

### 3. Compare SD vs Buy-and-Hold

**Question**: "Is volatility harvesting worth the complexity?"

```bash
synthetic-dividend-tool compare algorithms \
    --ticker SPY \
    --start 2023-01-01 \
    --end 2024-12-31 \
    --adjust-market
```

**Output**: Side-by-side comparison with alpha metrics

**When to use**: Strategy validation, client presentations

---

### 4. Batch Compare Multiple Assets

**Question**: "Which assets work best with volatility harvesting?"

```bash
synthetic-dividend-tool compare batch \
    --tickers NVDA AAPL GLD BIL AGG \
    --strategies sd8 sd16 buyhold \
    --start 2024-01-01 \
    --end 2024-12-31 \
    --output results.csv
```

**Output**: CSV with returns for each ticker × strategy combination

**When to use**: Portfolio construction, asset selection

---

### 5. Optimal Rebalancing Research

**Question**: "What's the sweet spot for rebalance size across asset classes?"

```bash
synthetic-dividend-tool research optimal-rebalancing \
    --start 2024-01-01 \
    --end 2024-12-31 \
    --output optimal_sd.csv
```

**Output**: CSV showing SD-4 through SD-32 performance for multiple assets

**When to use**: Academic research, parameter optimization

---

### 6. Real-World Order Calculation

**Question**: "I own 1,000 shares of NVDA at $125. What orders should I place?"

```bash
synthetic-dividend-tool order \
    --ticker NVDA \
    --holdings 1000 \
    --last-price 125.00 \
    --sd-n 8 \
    --profit-pct 50
```

**Output**: 
```
Buy Order:  900 shares @ $114.53 (dip buying)
Sell Order: 825 shares @ $136.44 (profit taking)
```

**When to use**: Live trading, portfolio rebalancing

---

### 7. Inflation-Adjusted Long-Term Analysis

**Question**: "Did my 30-year strategy preserve purchasing power?"

```bash
synthetic-dividend-tool backtest \
    --ticker VOO \
    --start 1995-01-01 \
    --end 2025-01-01 \
    --adjust-inflation \
    --verbose
```

**Output**:
```
Nominal Return: +1,240% ($124,000)
Real Return: +523% ($52,300)
Purchasing Power Lost: $71,700 (58% inflation erosion)
```

**When to use**: Retirement planning, long-term wealth preservation

---

### 8. Market-Adjusted Performance Evaluation

**Question**: "Did I beat the S&P 500?"

```bash
synthetic-dividend-tool backtest \
    --ticker AAPL \
    --start 2024-01-01 \
    --end 2024-12-31 \
    --adjust-market \
    --market-ticker VOO
```

**Output**:
```
Portfolio Return: +28.5%
Market Return (VOO): +32.9%
Alpha: -4.4% (underperformed market)
```

**When to use**: Strategy evaluation, manager performance review

---

### 9. Complete Return Analysis (All Three Dimensions)

**Question**: "Show me nominal, real, and market-adjusted returns"

```bash
synthetic-dividend-tool backtest \
    --ticker NVDA \
    --start 2024-01-01 \
    --end 2024-12-31 \
    --adjust-both \
    --market-ticker QQQ \
    --verbose
```

**Output**:
```
Nominal Return: +150.0% ($15,000)
Real Return: +135.2% ($13,520) [CPI adjustment]
Alpha vs QQQ: +18.3% ($1,830) [Market adjustment]

Income Classification:
  Universal (Dividends): $175 (1.75%)
  Primary (ATH Selling): $4,825 (48.25%)
  Secondary (Vol Alpha): $175 (1.75%)
```

**When to use**: Comprehensive analysis, research papers, client reports

---

### 10. High-Frequency Research (Gap Bonus Analysis)

**Question**: "How much alpha comes from multi-bracket gaps?"

```bash
synthetic-dividend-tool analyze gap-bonus \
    --input research_results.csv \
    --output gap_analysis.csv
```

**Output**: Breakdown of alpha from single vs multi-bracket gaps

**When to use**: Understanding volatility alpha sources, academic research

---

### 11. Asset Class Comparison

**Question**: "Which asset class has the best volatility alpha profile?"

```bash
synthetic-dividend-tool research asset-classes \
    --start 2024-01-01 \
    --end 2024-12-31 \
    --output by_class.csv \
    --adjust-both
```

**Output**: CSV grouping results by asset class (tech, commodity, bonds, etc.)

**When to use**: Portfolio diversification, asset allocation strategy

---

### 12. Comparison Table Generation

**Question**: "Create a nice table from my batch comparison results"

```bash
synthetic-dividend-tool compare table \
    --input batch_results.csv
```

**Output**: Formatted markdown/ASCII table for reports

**When to use**: Documentation, presentation slides, reports

---

## Command Combinations (Advanced Usage)

### Full Research Workflow

```bash
# Step 1: Find optimal SD-N for each asset
synthetic-dividend-tool research optimal-rebalancing \
    --start 2024-01-01 --end 2024-12-31 \
    --output step1_optimal.csv

# Step 2: Run batch comparison with optimal parameters
synthetic-dividend-tool compare batch \
    --tickers NVDA AAPL GLD \
    --strategies sd8 sd16 buyhold \
    --start 2024-01-01 --end 2024-12-31 \
    --adjust-both \
    --output step2_comparison.csv

# Step 3: Analyze gap bonus contribution
synthetic-dividend-tool analyze gap-bonus \
    --input step2_comparison.csv \
    --output step3_gap_analysis.csv

# Step 4: Generate formatted table
synthetic-dividend-tool compare table \
    --input step3_gap_analysis.csv
```

---

### Live Trading Workflow

```bash
# Morning: Analyze which assets need rebalancing
for ticker in NVDA AAPL MSFT; do
    synthetic-dividend-tool order \
        --ticker $ticker \
        --holdings <your_quantity> \
        --last-price <current_price> \
        --sd-n 8
done

# Place limit orders based on output

# Evening: Backtest actual day's transactions
synthetic-dividend-tool backtest \
    --ticker NVDA \
    --start 2024-12-01 \
    --end 2024-12-31 \
    --verbose
```

---

## Return Adjustment Examples

### Example 1: Tech Stock (High Nominal, High Real, High Alpha)

```bash
synthetic-dividend-tool backtest --ticker NVDA --start 2024-01-01 --end 2024-12-31 --adjust-both
```
```
Nominal: +150% (made money)
Real: +135% (beat inflation)  
Alpha: +110% (crushed market)
→ Winner on all dimensions
```

---

### Example 2: Gold (Low Nominal, Negative Real, Negative Alpha)

```bash
synthetic-dividend-tool backtest --ticker GLD --start 2024-01-01 --end 2024-12-31 --adjust-both
```
```
Nominal: +8% (made some money)
Real: -5% (lost purchasing power)
Alpha: -32% (lagged market badly)
→ Lost real value and opportunity cost
```

---

### Example 3: T-Bills (Low Nominal, Negative Real, Negative Alpha)

```bash
synthetic-dividend-tool backtest --ticker BIL --start 2024-01-01 --end 2024-12-31 --adjust-both --market-ticker VOO
```
```
Nominal: +4.5% (cash return)
Real: -8% (inflation ate it)
Alpha: -35% (huge opportunity cost vs stocks)
→ "Safe" but lost on both fronts
```

---

### Example 4: Bonds in 2022 (Negative All Dimensions)

```bash
synthetic-dividend-tool backtest --ticker AGG --start 2022-01-01 --end 2022-12-31 --adjust-both
```
```
Nominal: -13% (lost money)
Real: -21% (lost more after inflation)
Alpha: -31% (stocks also fell but less)
→ Rare triple-negative scenario
```

---

## Best Practices

### DO:
✅ Always use `--adjust-both` for comprehensive analysis  
✅ Standardize on argument names (`--ticker`, never `--symbol`)  
✅ Save CSV outputs for reproducibility (`--output results.csv`)  
✅ Use `--verbose` when you need detailed breakdowns  
✅ Specify custom benchmarks when appropriate (`--market-ticker QQQ`)  

### DON'T:
❌ Mix argument names across commands (breaks scripts)  
❌ Ignore inflation on multi-year backtests  
❌ Use default VOO benchmark for non-equity assets  
❌ Forget to specify `--initial-qty` (default 1000 may not match reality)  
❌ Run backtests without checking data availability first  

---

## Quick Reference: When to Use Which Adjustment

| Scenario | Use | Why |
|----------|-----|-----|
| **Short-term trading** (< 1 year) | Nominal only | Inflation negligible, focus on absolute gains |
| **Retirement planning** (10+ years) | `--adjust-inflation` | Purchasing power matters most |
| **Strategy evaluation** | `--adjust-market` | Need to beat passive alternative |
| **Complete analysis** | `--adjust-both` | Show all dimensions, let data speak |
| **High inflation period** (2021-2023) | `--adjust-inflation` MANDATORY | Nominal returns misleading |
| **Client reporting** | `--adjust-both --verbose` | Show complete picture, build trust |

---

## Troubleshooting

### "No data available for ticker CPI"
```bash
# Solution: Use inflation-tracking ETF as proxy
synthetic-dividend-tool backtest --ticker NVDA --adjust-inflation --inflation-ticker VTIP
```

### "Benchmark ticker VOO not appropriate for gold"
```bash
# Solution: Use gold benchmark or no market adjustment
synthetic-dividend-tool backtest --ticker GLD --adjust-inflation  # Skip market adjustment
# OR use gold benchmark:
synthetic-dividend-tool backtest --ticker GLD --adjust-market --market-ticker GLD  # Self-benchmark
```

### "Different results from web tools"
- Check if they use nominal vs real returns
- Verify they account for dividends
- Confirm same time period (exact dates matter)
- Check if fees are included

---

## Summary

The synthetic-dividend-tool provides:

📊 **Three return perspectives**: Nominal, Real (inflation-adjusted), Alpha (market-adjusted)  
🎯 **Unified interface**: Same arguments across all subcommands  
🔧 **Flexible analysis**: Quick backtests to deep research studies  
📈 **Live trading support**: Order calculation and rebalancing tools  
📝 **Complete documentation**: Theory, use cases, and examples  

**Core Philosophy**: Show returns in their full economic context. A 50% nominal return means nothing without knowing inflation and market performance.
