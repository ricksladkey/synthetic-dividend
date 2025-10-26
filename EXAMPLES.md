# 📚 Examples and Use Cases

This document provides practical examples for using the Synthetic Dividend Algorithm tools.

---

## Table of Contents

1. [Volatility Alpha Analysis](#volatility-alpha-analysis)
2. [Basic Backtesting](#basic-backtesting)
3. [Batch Comparisons](#batch-comparisons)
4. [Dividend Tracking](#dividend-tracking)
5. [Withdrawal Policies](#withdrawal-policies)
6. [Advanced Scenarios](#advanced-scenarios)

---

## Volatility Alpha Analysis

The **Volatility Alpha Analyzer** is the recommended starting point. It automatically:
- Calculates historical volatility
- Suggests optimal SD parameter
- Compares full strategy vs ATH-only
- Reports volatility alpha (secondary synthetic dividends)

### Quick Start

```bash
# Analyze gold (auto-suggests SD parameter based on volatility)
analyze-alpha.bat GLD 10/26/2024 10/26/2025

# Analyze NVIDIA
analyze-alpha.bat NVDA 10/23/2023 10/23/2024

# Analyze Apple with custom quantity
analyze-alpha.bat AAPL 01/01/2024 12/31/2024 --qty 200
```

### Example Output

```
================================================================================
VOLATILITY ALPHA ANALYZER: GLD
================================================================================

📊 Historical Volatility: 19.67% annualized
💡 Auto-suggestion: Low volatility (19.7%) → SD16 (4.47% trigger)

SD16 (Full) Return:         45.71%
SD16-ATH-Only Return:       44.98%
────────────────────────────────────────────────────────────────────────────────
Volatility Alpha:           +0.72%

✅ Strong positive alpha! Buybacks added 0.72% extra return.
```

### Interpreting Results

**Volatility Alpha > 0**: Buybacks generated extra profit (secondary synthetic dividends)
- The asset had enough volatility to create profitable buyback opportunities
- Example: NVDA with +7.53% alpha

**Volatility Alpha ≈ 0**: Smooth trend, minimal volatility to harvest
- Asset went up steadily without significant pullbacks
- Example: GLD with SD8 (0.00% alpha - trigger too wide)

**Volatility Alpha < 0**: Strategy slightly underperformed ATH-only
- Rare, usually indicates extremely smooth uptrend
- Buybacks used capital that could have stayed invested

### Volatility-to-SD Heuristic

The tool uses this mapping:

| Volatility Range | Suggested SD | Trigger % | Asset Examples |
|------------------|--------------|-----------|----------------|
| **>50%** | SD6 | 12.25% | BTC, volatile tech stocks |
| **30-50%** | SD8 | 9.05% | NVDA, high-growth stocks |
| **20-30%** | SD10 | 7.18% | QQQ, tech indices |
| **10-20%** | SD16 | 4.47% | GLD, stable stocks |
| **<10%** | SD20 | 3.53% | BIL, bonds, very stable assets |

### Override Auto-Suggestion

```bash
# Force specific SD parameter
analyze-alpha.bat GLD 10/26/2024 10/26/2025 --sd 8

# Custom profit sharing (default is 50%)
analyze-alpha.bat GLD 10/26/2024 10/26/2025 --profit-sharing 75
```

---

## Basic Backtesting

Run individual backtests with specific parameters.

### Command Format

```bash
python -m src.run_model TICKER START_DATE END_DATE STRATEGY [OPTIONS]
```

### Examples

```bash
# NVIDIA with SD8 (9.05% trigger, 50% profit sharing)
python -m src.run_model NVDA 10/23/2023 10/23/2024 sd8 --qty 10000

# Gold with SD16 (4.47% trigger)
python -m src.run_model GLD 10/26/2024 10/26/2025 sd16 --qty 100

# Apple with custom parameters (7.18% trigger, 75% profit sharing)
python -m src.run_model AAPL 01/01/2024 12/31/2024 "sd/7.18%/75%"

# ATH-only strategy (no buybacks)
python -m src.run_model NVDA 10/23/2023 10/23/2024 sd8-ath-only --qty 10000
```

### Strategy Naming Conventions

| Format | Example | Meaning |
|--------|---------|---------|
| `sdN` | `sd8` | SD8: 9.05% trigger, 50% profit sharing, buybacks enabled |
| `sdN-ath-only` | `sd8-ath-only` | SD8 ATH-only: 9.05% trigger, 50% profit sharing, NO buybacks |
| `sd/R%/P%` | `sd/9.05%/75%` | Custom: 9.05% trigger, 75% profit sharing, buybacks enabled |
| `sd-ath-only/R%/P%` | `sd-ath-only/9.05%/50%` | Custom ATH-only: 9.05% trigger, 50% profit sharing, NO buybacks |

Where:
- `N` = SD parameter (4, 6, 8, 10, 12, 16, 20, 24...)
- `R` = Rebalance trigger percentage
- `P` = Profit sharing percentage (0-100+)

### Output Example

```
Ticker: NVDA
Start Date: 2023-10-23
Start Price: 42.35
Start Value: 423500.00

End Date: 2024-10-23
End Price: 144.42
End Value: 8520780.00
Holdings: 59000 shares

Bank: 3565360.00
Total (holdings + bank): 12086140.00

Total return: 174.59%
Annualized return: 185.47% (over 1.003 years)

Volatility Alpha: 9.59%
```

---

## Batch Comparisons

Compare multiple strategies or assets simultaneously.

### Compare Multiple SD Parameters

```bash
# Run comprehensive analysis (12 assets × 4 SD parameters)
python -m src.research.optimal_rebalancing --comprehensive --output results.csv
```

Assets tested:
- **Tech**: NVDA, GOOG, AAPL, MSFT
- **Indices**: QQQ, VOO, VTI
- **Commodities**: GLD
- **Crypto**: BTC-USD
- **International**: TSM
- **Cash**: BIL
- **Energy**: XLE

SD parameters tested: SD4, SD6, SD8, SD10

### Custom Batch Run

```bash
# Compare 3 assets with 2 strategies each
python -m src.compare.batch_comparison \
  --tickers NVDA AAPL GLD \
  --strategies sd8 sd16 \
  --start 01/01/2024 \
  --end 12/31/2024
```

---

## Dividend Tracking

The system automatically tracks dividend and interest payments.

### Example with Dividend-Paying Stock

```python
from datetime import date
from src.data.fetcher import HistoryFetcher
from src.models.backtest import SyntheticDividendAlgorithm, run_algorithm_backtest

fetcher = HistoryFetcher()

# Fetch price and dividend data
price_df = fetcher.get_history("AAPL", date(2024, 1, 1), date(2024, 12, 31))
div_series = fetcher.get_dividends("AAPL", date(2024, 1, 1), date(2024, 12, 31))

# Run backtest with dividends
algo = SyntheticDividendAlgorithm(9.05, 50)
_, summary = run_algorithm_backtest(
    df=price_df,
    ticker="AAPL",
    initial_qty=100,
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31),
    algo=algo,
    dividend_series=div_series,  # Include real dividends
    simple_mode=True,
)

print(f"Total dividends received: ${summary['total_dividends']:.2f}")
print(f"Dividend payment count: {summary['dividend_payment_count']}")
```

### Pre-built Demo

```bash
# Run dividend integration demo with AAPL
python demo_dividends.py
```

Output shows:
- AAPL 2024: 4 quarterly dividends ($0.99/share)
- With 100 shares: $96.75 total dividends
- Bank balance boost: +$96.75
- Total return improvement: +0.52%

### Assets with Significant Dividends/Interest

| Asset | Type | 2024 Payments | Annual Yield |
|-------|------|---------------|--------------|
| **AAPL** | Equity dividend | 4 quarterly ($0.99/share) | ~0.5% |
| **MSFT** | Equity dividend | 4 quarterly | ~0.7% |
| **BIL** | Money market interest | 12 monthly ($4.60/share) | ~4.6% |
| **VTI** | ETF distribution | 4 quarterly | ~1.3% |
| **VOO** | ETF distribution | 4 quarterly | ~1.4% |

---

## Withdrawal Policies

Model retirement scenarios with systematic withdrawals.

### 4% Rule with CPI Adjustment

```bash
# Backtest with 4% annual withdrawals (monthly)
python -m src.run_model NVDA 10/23/2023 10/23/2024 sd8 \
  --qty 10000 \
  --withdrawal-rate 4.0 \
  --cpi-adjust
```

### Parameters

- `--withdrawal-rate X`: Annual withdrawal rate as % of initial value (e.g., 4.0 for 4%)
- `--withdrawal-frequency N`: Days between withdrawals (default: 30 for monthly)
- `--cpi-adjust`: Enable inflation adjustment of withdrawals

### How It Works

1. **Calculate base withdrawal**: Initial portfolio value × (withdrawal_rate / 12) for monthly
2. **Adjust for inflation**: Multiply by CPI ratio (if enabled)
3. **Withdraw from bank first**: If sufficient cash available
4. **Sell shares if needed**: If bank balance insufficient

Example:
- Initial value: $100,000
- Withdrawal rate: 4% annually
- Monthly withdrawal: $100,000 × 0.04 / 12 = $333.33
- After 1 year (3% inflation): $333.33 × 1.03 = $343.33

### Coverage Ratio

A key metric for withdrawal sustainability:

```
Coverage Ratio = Synthetic Dividends / Withdrawals
```

- **>200%**: Excellent - bank balance growing
- **100-200%**: Good - sustainable
- **50-100%**: Marginal - selling shares occasionally
- **<50%**: Poor - frequently selling shares

---

## Advanced Scenarios

### Margin Modes

```bash
# Allow margin (bank can go negative)
python -m src.run_model NVDA 10/23/2023 10/23/2024 sd8 --allow-margin

# Strict mode (bank never goes negative)
python -m src.run_model NVDA 10/23/2023 10/23/2024 sd8 --no-margin
```

**Allow Margin (default)**:
- BUY orders always execute (bank can go negative)
- Withdrawals only cover withdrawal amount
- Tracks opportunity cost of negative bank balance

**Strict Mode**:
- BUY orders skipped if insufficient cash
- Withdrawals must cover amount AND repay negative balance
- True "closed system" - no external capital

### Financial Adjustments

Model realistic costs and gains from cash positions.

```bash
# Use actual market benchmarks (VOO for opportunity cost, BIL for risk-free rate)
python -m src.run_model NVDA 10/23/2023 10/23/2024 sd8 \
  --reference-asset VOO \
  --risk-free-asset BIL
```

Calculations:
- **Negative bank** (borrowing): Opportunity cost = VOO daily returns
- **Positive bank** (cash): Risk-free gains = BIL daily returns

### Price Normalization

For comparing strategies across different starting prices.

```bash
# Normalize prices so brackets align at standard positions
python -m src.run_model NVDA 10/23/2023 10/23/2024 sd8 --normalize
```

Without normalization:
- Start price: $42.35
- First bracket: varies based on start price

With normalization:
- Prices scaled so brackets are at 1.0, 1.0905, 1.1893, etc.
- Makes bracket placement deterministic
- Useful for comparing algorithms across runs

---

## Real-World Use Cases

### Case 1: Retirement Income Generation

**Goal**: Generate $40,000/year from $1M portfolio (4% withdrawal rate)

```bash
# Use stable, dividend-paying index
python -m src.run_model VOO 01/01/2024 12/31/2024 sd12 \
  --qty 2500 \
  --withdrawal-rate 4.0 \
  --cpi-adjust \
  --reference-asset VOO \
  --risk-free-asset BIL

# Also fetch dividends
# VOO pays ~1.4% dividends, providing $14,000/year
# Need synthetic dividends to cover remaining $26,000
```

Expected result:
- Synthetic dividends: ~2-3% (volatility harvesting)
- Real dividends: ~1.4%
- Total income: ~3.4-4.4%
- Coverage ratio: 85-110%

### Case 2: High-Growth Accumulation

**Goal**: Maximize growth with minimal cash distributions

```bash
# Low profit sharing (25%) = keep more shares, less cash
python -m src.run_model NVDA 10/23/2023 10/23/2024 "sd8/9.05%/25%"
```

Results:
- More shares retained
- Less cash generated
- Higher exposure to price appreciation
- Lower downside protection

### Case 3: Conservative Income Focus

**Goal**: Maximize cash flow for near-term expenses

```bash
# High profit sharing (100%) = maximize cash, minimal reinvestment
python -m src.run_model NVDA 10/23/2023 10/23/2024 "sd8/9.05%/100%"
```

Results:
- Maximum cash generation
- Fewer shares retained
- Lower exposure to price swings
- Higher downside protection (larger bank buffer)

### Case 4: Multi-Asset Portfolio

Diversify across asset classes with different SD parameters:

```bash
# Tech (high vol) → SD8
analyze-alpha.bat NVDA 01/01/2024 12/31/2024

# Index (medium vol) → SD10
analyze-alpha.bat VOO 01/01/2024 12/31/2024

# Gold (low vol) → SD16
analyze-alpha.bat GLD 01/01/2024 12/31/2024

# Money market (very low vol) → SD20
analyze-alpha.bat BIL 01/01/2024 12/31/2024
```

Portfolio allocation example:
- 40% NVDA (SD8) - growth engine
- 30% VOO (SD10) - stable core
- 20% GLD (SD16) - hedge/diversifier
- 10% BIL (SD20) - cash reserve

Benefits:
- Uncorrelated synthetic dividend streams
- When one asset is down, others generate cash
- Improved overall coverage ratio
- Reduced sequence-of-returns risk

---

## Quick Reference

### Most Common Commands

```bash
# Auto-analyze any asset
analyze-alpha.bat TICKER START END

# Basic backtest
python -m src.run_model TICKER START END sd8 --qty 100

# With dividends (demo)
python demo_dividends.py

# Batch research
python -m src.research.optimal_rebalancing --comprehensive
```

### Key Metrics to Watch

- **Total Return**: Overall portfolio performance
- **Volatility Alpha**: Extra return from buybacks (secondary dividends)
- **Bank Balance**: Cash available for withdrawals
- **Coverage Ratio**: Synthetic dividends / withdrawals (if applicable)
- **Dividend Payment Count**: Real dividends received

### When to Use Each Strategy

| Scenario | Recommended Approach |
|----------|---------------------|
| **Exploring new asset** | `analyze-alpha.bat` (auto-suggest) |
| **Retirement planning** | `run_model` with `--withdrawal-rate 4.0` |
| **Comparing parameters** | `optimal_rebalancing --comprehensive` |
| **Checking dividends** | `demo_dividends.py` or manual with `get_dividends()` |
| **Portfolio simulation** | Multiple `run_model` calls with different tickers |

---

## Need Help?

- **Theory**: See [theory/README.md](theory/README.md)
- **Algorithm details**: See [INCOME_GENERATION.md](theory/INCOME_GENERATION.md)
- **Volatility alpha**: See [VOLATILITY_ALPHA_THESIS.md](VOLATILITY_ALPHA_THESIS.md)
- **Code**: See [CODING_PHILOSOPHY.md](theory/CODING_PHILOSOPHY.md)
- **Tests**: Run `pytest tests/ -v` to see edge cases

---

**Happy trading! May your volatility alpha be ever positive! 📈💰**
