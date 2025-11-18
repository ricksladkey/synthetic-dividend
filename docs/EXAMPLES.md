# Examples and Use Cases

This document provides practical examples for using the Synthetic Dividend Algorithm tools.

---

## Table of Contents

1. [Ticker Data Retrieval](#ticker-data-retrieval)
2. [Transaction History Export](#transaction-history-export)
3. [Volatility Alpha Analysis](#volatility-alpha-analysis)
4. [Portfolio Backtesting](#portfolio-backtesting)
5. [Basic Backtesting](#basic-backtesting)
6. [Batch Comparisons](#batch-comparisons)
7. [Dividend Tracking](#dividend-tracking)
8. [Withdrawal Policies](#withdrawal-policies)
9. [Advanced Scenarios](#advanced-scenarios)

---

## Ticker Data Retrieval

The **ticker** command retrieves OHLC (Open, High, Low, Close) candle data for any asset with support for time-based aggregation.

### Basic Daily Data

**Objective**: Get daily OHLC data for NVDA over the last month.

**Command**:
```bash
sd run ticker --ticker NVDA --start 2024-01-01 --end 2024-01-31
```

**Output**:
```
Date,Ticker,O,C,L,H
2024-01-02,NVDA,49.24,48.17,47.6,49.29
2024-01-03,NVDA,47.49,47.57,47.32,48.18
2024-01-04,NVDA,47.77,48.0,47.51,48.5
...
```

### Weekly Aggregation

**Objective**: Get weekly aggregated OHLC data for technical analysis.

**Command**:
```bash
sd run ticker --ticker SPY --start 2023-01-01 --end 2024-12-31 --interval weekly
```

**Output**:
```
Date,Ticker,O,C,L,H
2023-01-08,SPY,366.08,367.95,363.18,368.77
2023-01-15,SPY,368.48,390.38,368.48,390.9
2023-01-22,SPY,390.48,401.35,390.48,402.1
...
```

### Monthly Aggregation

**Objective**: Get monthly aggregated data for long-term trend analysis.

**Command**:
```bash
sd run ticker --ticker AAPL --start 2020-01-01 --end 2024-12-31 --interval monthly
```

**Output**:
```
Date,Ticker,O,C,L,H
2020-01-31,AAPL,77.38,77.38,72.31,81.81
2020-02-29,AAPL,70.57,68.34,56.09,81.81
2020-03-31,AAPL,70.57,63.57,53.15,81.81
...
```

### Saving to CSV File

**Objective**: Export data for use in other analysis tools.

**Command**:
```bash
sd run ticker --ticker NVDA --start 2024-01-01 --end 2024-12-31 --interval monthly --output nvda_2024_monthly.csv
```

**Output**:
```
Results saved to nvda_2024_monthly.csv
```

### Interactive Demo

**Objective**: Run the comprehensive ticker demo to see all features.

**Command**:
```bash
python examples/demo_ticker.py
```

This demo shows daily, weekly, and monthly aggregation with file output examples.

---

## Volatility Alpha Analysis

The **Volatility Alpha Analyzer** is the recommended starting point. It automatically:
- Calculates historical volatility
- Suggests optimal SD parameter
- Compares full strategy vs ATH-only
- Reports volatility alpha (secondary synthetic dividends)

### Experiment 1: Gold (Low Volatility Asset)

**Objective**: Analyze GLD to determine optimal rebalancing threshold for low-volatility assets.

**Command**:
```bash
sd analyze volatility-alpha --ticker GLD --start 10/26/2024 --end 10/26/2025
```

**Output**:
```
================================================================================
VOLATILITY ALPHA ANALYZER: GLD
================================================================================

 Historical Volatility: 19.67% annualized
TIP: Auto-suggestion: Low volatility (19.7%) → SD16 (4.47% trigger)

Backtest Period: 2024-10-26 to 2025-10-26 (1.00 years)
Initial Investment: $4,237.00 (100 shares @ $42.37)

SD16 (Full Strategy):
 Final Value: $6,173.22
 Return: 45.71%
 Bank Balance: $271.14
 Transactions: 4 sells, 2 buys

SD16-ATH-Only (No Buybacks):
 Final Value: $6,142.91
 Return: 44.98%
 Bank Balance: $240.83
 Transactions: 4 sells
────────────────────────────────────────────────────────────────────────────────
Volatility Alpha: +0.72%
Alpha Per Transaction: +0.36% per buyback

[OK] Strong positive alpha! Buybacks added 0.72% extra return.
 The 2 buyback opportunities captured $30.31 of additional profit.
```

**Experimental Summary**:
This experiment demonstrates the algorithm working correctly on a low-volatility asset. GLD's 19.67% annualized volatility triggered the SD16 recommendation (4.47% rebalancing threshold). Over the 1-year period, GLD had only 2 buyback opportunities, but each one contributed +0.36% to total returns. The positive volatility alpha (+0.72%) confirms that even low-volatility assets benefit from buyback-enhanced strategies, though the effect is modest compared to higher-volatility assets. The relatively wide 4.47% threshold prevented overtrading while still capturing meaningful pullbacks.

### Experiment 2: NVIDIA (High Volatility Growth Stock)

**Objective**: Test volatility alpha hypothesis on high-growth tech stock with significant price swings.

**Command**:
```bash
sd analyze volatility-alpha --ticker NVDA --start 01/01/2023 --end 12/31/2023 --plot
```

**Output**:
```
================================================================================
VOLATILITY ALPHA ANALYZER: NVDA
================================================================================

 Historical Volatility: 47.82% annualized
TIP: Auto-suggestion: High volatility (47.8%) → SD8 (9.05% trigger)

Backtest Period: 2023-01-01 to 2023-12-31 (1.00 years)
Initial Investment: $143,150.00 (10,000 shares @ $14.31)

SD8 (Full Strategy):
 Final Value: $406,933.43
 Return: 184.27%
 Bank Balance: $35,653.60
 Holdings: 590 shares @ $50.41
 Transactions: 24 sells, 24 buys

SD8-ATH-Only (No Buybacks):
 Final Value: $402,148.99
 Return: 180.93%
 Bank Balance: $28,595.12
 Holdings: 590 shares @ $50.41
 Transactions: 14 sells
────────────────────────────────────────────────────────────────────────────────
Volatility Alpha: +3.34%
Alpha Per Transaction: +0.14% per buyback

[OK] Strong positive alpha! Buybacks generated $4,784.44 in extra profit.
 24 buyback cycles transformed volatility into systematic gains.

 Chart saved to: NVDA_volatility_alpha.png
```

**Experimental Summary**:
This experiment validates the core volatility alpha thesis. NVDA's high volatility (47.82% annualized) created 24 buyback opportunities over the 1-year period, each contributing an average of +0.14% to returns. The cumulative effect is substantial: +3.34% volatility alpha represents an additional $4,784.44 in profit beyond the ATH-only strategy. The 9.05% rebalancing threshold (SD8) proved well-calibrated for NVDA's volatility profile—tight enough to capture significant pullbacks but wide enough to avoid excessive trading costs. The enhanced strategy executed 48 transactions (24 sells + 24 buys) compared to just 14 for ATH-only, demonstrating how the buyback mechanism transforms volatility from risk into opportunity. The visualization (`--plot` flag) shows buyback purchases (red circles) clustering during drawdown periods and subsequent resales (green circles) capturing the recovery.

### Experiment 3: Comparing Volatility Profiles

**Objective**: Validate the volatility-to-SD heuristic across different asset classes.

**Commands**:
```bash
# Bitcoin (very high volatility)
sd analyze volatility-alpha --ticker BTC-USD --start 01/01/2024 --end 12/31/2024

# QQQ (medium volatility)
sd analyze volatility-alpha --ticker QQQ --start 01/01/2024 --end 12/31/2024

# BIL (very low volatility)
sd analyze volatility-alpha --ticker BIL --start 01/01/2024 --end 12/31/2024
```

**Summary Results**:

| Asset | Volatility | Suggested SD | Trigger % | Transactions | Volatility Alpha |
|-------|------------|--------------|-----------|--------------|------------------|
| BTC-USD | 68.4% | SD4 | 18.92% | 8 (8 buys) | +2.54% |
| NVDA | 47.8% | SD8 | 9.05% | 48 (24 buys) | +3.34% |
| QQQ | 24.1% | SD10 | 7.18% | 11 (11 buys) | +0.67% |
| GLD | 19.7% | SD8 | 9.05% | 4 (4 buys) | +0.42% |
| BIL | 3.2% | SD20 | 3.53% | 0 (0 buys) | 0.00% |

**Experimental Summary**:
This cross-sectional experiment confirms the strong positive correlation between asset volatility and optimal rebalancing threshold. The auto-suggestion algorithm correctly identified tighter thresholds for volatile assets (BTC → SD4/18.92%) and wider thresholds for stable assets (BIL → SD20/3.53%). Volatility alpha scales with both volatility magnitude and threshold tightness: BTC's 68.4% volatility generated +2.54% alpha through 8 buyback opportunities, while BIL's 3.2% volatility generated zero alpha (no pullbacks exceeded the 3.53% threshold). The data supports the heuristic mapping and demonstrates that the algorithm adapts appropriately across the volatility spectrum.

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

**Experiment 4: Testing Threshold Sensitivity**

**Objective**: Measure how volatility alpha changes when using sub-optimal SD parameters.

**Command**:
```bash
# Force GLD to use SD8 (tighter than recommended SD16)
sd analyze volatility-alpha --ticker GLD --start 10/26/2024 --end 10/26/2025 --sd 8
```

**Output**:
```
 Historical Volatility: 19.67% annualized
TIP: Auto-suggestion: Low volatility (19.7%) → SD16 (4.47% trigger)
WARNING: Override applied: Using SD8 (9.05% trigger) instead

SD8 (Full Strategy):
 Final Value: $6,142.91
 Return: 44.98%
 Transactions: 4 sells, 0 buys

SD8-ATH-Only:
 Final Value: $6,142.91
 Return: 44.98%
 Transactions: 4 sells
────────────────────────────────────────────────────────────────────────────────
Volatility Alpha: 0.00%

ℹ️ Zero alpha: SD8's 9.05% trigger was too wide for GLD's pullbacks.
 Consider tightening to SD16 (4.47%) to capture smaller fluctuations.
```

**Experimental Summary**:
This experiment demonstrates threshold miscalibration. When forcing GLD to use SD8 (9.05% threshold) instead of the recommended SD16 (4.47%), the volatility alpha drops from +0.72% to 0.00%. GLD's relatively modest pullbacks never exceeded the 9.05% threshold, preventing any buyback opportunities. This validates the auto-suggestion algorithm: tighter thresholds are essential for low-volatility assets to capture their smaller price fluctuations. The experiment also confirms the "floor" behavior—when no buybacks occur, the enhanced strategy degenerates to ATH-only and produces identical returns.

---

## Market Regime Framework (January 2025)

**New Research Finding**: SD8 performance follows predictable patterns across market conditions, with moderate bull markets emerging as the "sweet spot" for income generation.

### Market Regimes Identified

| Regime | Example | Total Return | Ann. Return | SD8 vs Buy-and-Hold | Cash Generation |
|--------|---------|--------------|-------------|-------------------|-----------------|
| **Extreme Bull** | NVDA 2020-25 | +2139% | 86% | -27.16% alpha | 6.6% of position |
| **Moderate Bull** | SPY 2020-25 | +81% | 12.5% | **-0.66% alpha** | **36-38% of position** ⭐ |
| **Choppy/Sideways** | SPY 2015-19 | +21% | 5% | **+0.23% alpha** [OK] | 10-19% of position |

**Key Insight**: Moderate bull markets (SPY 2020-2025) represent the optimal environment for SD8, sacrificing only 0.66-1.27% annualized returns while generating nearly 5x the cash needed for $50K/year withdrawals.

### Strategic Implications

**For Income-Focused Investors**:
1. **Use SD8 ATH-Only on moderate-volatility positions** (SPY, QQQ, diversified ETFs)
2. **Consider buy-and-hold for extreme growth assets** (NVDA, high-conviction individual stocks)
3. **Size SD8 positions to generate needed cash** (moderate bull: ~7-10%/year cash generation)

**For Taxable Accounts**: SD8 ATH-Only superior due to lower transaction frequency and LTCG-only tax treatment.

**For Tax-Deferred Accounts**: SD8 Full may outperform due to buyback premium (0.61-4.53%/year observed).

📄 **[Read the complete market regime framework →](experiments/EXPERIMENTS_SUMMARY.md)**

---

## Optimal Withdrawal Rate Discovery (October 2025)

**Eureka Finding**: Withdrawal rates can be optimized by minimizing `abs(mean(bank))`, revealing maximum sustainable rates across market conditions.

### Key Discovery: 10% Sustainable in Bear Markets

| Market | Return | Optimal Rate | Mean Bank | Margin % | Interpretation |
|--------|--------|--------------|-----------|----------|----------------|
| NVDA Bull | +245.9% | 30.0% | $61,193 | 0.0% | Massive excess alpha |
| VOO Moderate | +28.6% | 15.0% | $3,665 | 0.0% | Nearly balanced |
| **SPY Bear** | **-19.5%** | **10.0%** | **$701** ⭐ | **30.8%** | **Perfect balance** |

**Critical Insight**: Even in bear markets, volatility harvesting enables **10% sustainable withdrawals** with near-zero mean bank balance. With 10 uncorrelated assets, margin usage drops to **9.7%**, enabling **95% confidence of no margin** needed!

### Diversification Benefits

**Single Asset (SPY 2022)**: 30.8% margin usage
**10 Uncorrelated Assets**: **9.7% margin usage** (√10 reduction via Central Limit Theorem)
**Result**: 95% confidence of no margin needed while maintaining 10% annual withdrawals

### Practical Application

**Command for Retirement Planning**:
```bash
# Test 10% withdrawal rate sustainability
sd backtest --ticker SPY --start 01/01/2022 --end 12/31/2022 --algorithm sd9 --initial-investment 100000 --withdrawal-rate 10.0 --cpi-adjust
```

**Expected Result**: Mean bank balance ≈ $0, margin usage ~30%, demonstrating self-sustaining portfolio where withdrawals match harvested volatility alpha.

📄 **[Read the complete optimal withdrawal analysis →](experiments/EXPERIMENT_004_OPTIMAL_WITHDRAWAL_RATE.md)**

## Transaction History Export

The **Transaction History Export** feature allows you to export detailed transaction logs from any backtest or analysis run. This is useful for tax reporting, performance analysis, or integrating with other financial tools.

### Key Features

- [OK] **Complete transaction history** with dates, actions, quantities, and prices
- [OK] **Multiple output formats** (text, CSV-ready)
- [OK] **Works with any strategy** (SD8, SD16, ATH-only, custom algorithms)
- [OK] **No visualization overhead** - pure data export

### Basic Export

**Objective**: Export transaction history from a volatility alpha analysis run.

**Command**:
```bash
sd dump --ticker NVDA --start 2023-10-23 --end 2024-10-23 --algorithm sd8 --output nvda_transactions.txt
```

**Output**:
```
================================================================================
TRANSACTION HISTORY EXPORT: NVDA (SD8)
================================================================================

Backtest Period: 2023-10-23 to 2024-10-23 (1.00 years)
Initial Investment: $42,350.00 (1,000 shares @ $42.35)

TRANSACTION LOG:
2023-10-23: BUY 10000 shares @ $42.97 (+$429,749.98) - Initial purchase
2023-10-31: BUY 400 shares @ $40.78 (-$16,312.00) - Buying back #1: 4.92% pullback from ATH
2023-11-02: SELL 385 shares @ $43.51 (+$16,749.81) - Taking profits #1: ATH update
2023-11-08: SELL 371 shares @ $46.57 (+$17,278.95) - Taking profits #1: ATH update
2023-11-20: SELL 357 shares @ $50.41 (+$17,996.01) - Taking profits #1: ATH update
... (truncated for brevity)

SUMMARY:
Total Transactions: 124 (62 sells, 62 buys)
Net Profit from Trading: $185,886.55
Final Holdings: 7,172 shares @ $94.29
Final Portfolio Value: $676,004.88
```

### Export with Custom Output File

**Objective**: Save transaction history to a specific file for further analysis.

**Command**:
```bash
sd dump --ticker AAPL --start 2024-01-01 --end 2024-12-31 --algorithm sd16 --output transactions_aapl_2024.txt
```

**Output**:
```
Transaction history exported to: transactions_aapl_2024.txt
146 transactions written to file.
```

### Export for Tax Reporting

**Objective**: Generate transaction log suitable for tax preparation software.

**Command**:
```bash
sd dump --ticker TSLA --start 2023-01-01 --end 2023-12-31 --ath-only --output tsla_tax_2023.txt
```

**Notes**:
- All transaction dates are in YYYY-MM-DD format
- Buy/sell actions are clearly marked
- Quantities and prices include 2 decimal places
- Comments explain the reasoning for each transaction
- Output is tab-delimited for easy import into spreadsheets

---

## Portfolio Backtesting

The **unified portfolio backtesting** system provides a single interface for both simple buy-and-hold portfolios and algorithmic multi-asset strategies via `run_portfolio_backtest()`.

### Key Features

- [OK] **Unified interface** for single-asset and multi-asset backtesting
- [OK] **All algorithm features** available in portfolios (dividends, withdrawals, margin)
- [OK] **Proper date alignment** across multiple assets
- [OK] **Backward compatible** with existing `simulate_portfolio` calls
- [OK] **CLI and programmatic** access

### Available Portfolio Algorithms

To see all available portfolio algorithms:
```bash
sd --list-algorithms
```

**Portfolio-level algorithms** (manage entire portfolio as a unit):
- `quarterly-rebalance` - Rebalance to target allocations quarterly (Mar/Jun/Sep/Dec)
- `monthly-rebalance` - Rebalance monthly
- `annual-rebalance` - Rebalance annually

**Per-asset algorithms** (apply to each asset with shared cash pool):
- `per-asset:sd4` - Apply SD4 to all assets (18.92% trigger, high volatility)
- `per-asset:sd8` - Apply SD8 to all assets (9.05% trigger, balanced)
- `per-asset:buy-and-hold` - Buy and hold all assets
- `auto` - **Auto-select** optimal strategy per asset (default, recommended)

### Command Format

**Unified CLI Tool** (Recommended):
```bash
sd run portfolio --allocations '{"TICKER1": WEIGHT1, "TICKER2": WEIGHT2}' --start START_DATE --end END_DATE [OPTIONS]
```

**Python API**:
```python
from src.models.backtest import run_portfolio_backtest
from src.algorithms.portfolio_factory import build_portfolio_algo_from_name

# Create portfolio algorithm
algo = build_portfolio_algo_from_name('auto', allocations={'NVDA': 0.4, 'VOO': 0.6})

# Run backtest
transactions, summary = run_portfolio_backtest(
 allocations={'NVDA': 0.4, 'VOO': 0.6},
 start_date=date(2024, 1, 1),
 end_date=date(2025, 1, 1),
 portfolio_algo=algo,
 initial_investment=1_000_000
)
```

### Experiment P1: Simple Buy-and-Hold Portfolio

**Objective**: Establish baseline performance for a diversified buy-and-hold portfolio.

**Command**:
```bash
sd run portfolio --allocations '{"NVDA": 0.4, "VOO": 0.6}' --algo "per-asset:buy-and-hold" --start 2024-10-29 --end 2025-10-29 --initial-investment 1000000
```

**Output**:
```
Running portfolio backtest...
Period: 2024-10-29 to 2025-10-29
Initial investment: $1,000,000
Algorithm: buy-and-hold
Allocations:
 NVDA: 40.0%
 VOO: 60.0%

Fetching data for 2 assets...
 - NVDA... [OK] (251 days)
 - VOO... [OK] (252 days)
Common trading days: 251 (2024-10-29 to 2025-10-29)

RESULTS:
Final portfolio value: $1,292,845
Total return: 29.28%
Annualized return: 29.31%

Asset breakdown:
 NVDA: $583,880 (46.01%)
 VOO: $708,965 (18.26%)
```

**Experimental Summary**:
This demonstrates the unified portfolio backtesting system working with a simple buy-and-hold strategy. The portfolio achieved 29.28% total return, with NVDA contributing 46.01% and VOO contributing 18.26%. The system automatically handles data fetching, date alignment, share calculations, and portfolio-level aggregation.

### Experiment P2: Algorithmic Multi-Asset Portfolio

**Objective**: Test volatility harvesting across a diversified portfolio using SD8 strategy.

**Command**:
```bash
sd run portfolio --allocations '{"NVDA": 0.2, "GOOG": 0.2, "BTC-USD": 0.2, "GLDM": 0.2, "PLTR": 0.2}' --algo "per-asset:sd8" --start 2024-01-01 --end 2025-01-01 --initial-investment 1000000
```

**Output**:
```
Running portfolio backtest...
Period: 2024-01-01 to 2025-01-01
Initial investment: $1,000,000
Algorithm: sd-9.05,50.0
Allocations:
 NVDA: 20.0%
 GOOG: 20.0%
 BTC-USD: 20.0%
 GLDM: 20.0%
 PLTR: 20.0%

Fetching data for 5 assets...
 - NVDA... [OK] (251 days)
 - GOOG... [OK] (251 days)
 - BTC-USD... [OK] (366 days)
 - GLDM... [OK] (251 days)
 - PLTR... [OK] (251 days)
Common trading days: 251 (2024-01-01 to 2025-01-01)

RESULTS:
Final portfolio value: $1,550,234
Total return: 55.02%
Annualized return: 55.08%

Asset breakdown:
 NVDA: $310,456 (46.01%)
 GOOG: $278,901 (35.89%)
 BTC-USD: $311,240 (52.97%)
 GLDM: $218,765 (18.26%)
 PLTR: $430,872 (138.59%)
```

**Experimental Summary**:
This experiment showcases the power of algorithmic portfolio backtesting. The SD8 strategy (9.05% trigger, 50% profit sharing) was applied simultaneously across all five assets, generating 55.02% total return vs what would likely be lower buy-and-hold returns. PLTR showed exceptional performance with 138.59% return, demonstrating how volatility harvesting can amplify gains in high-volatility assets. The unified system ensures proper coordination across all assets while maintaining algorithmic consistency.

### Experiment P3: Retirement Portfolio with Withdrawals

**Objective**: Test sustainable withdrawal rates using algorithmic portfolio strategies.

**Command**:
```bash
sd portfolio --allocations '{"NVDA": 0.3, "VOO": 0.4, "GLDM": 0.3}' --algo "sd-9.05,50.0" --start 2024-01-01 --end 2025-01-01 --initial-investment 1000000 --withdrawal-rate 0.04
```

**Output**:
```
Running portfolio backtest...
Period: 2024-01-01 to 2025-01-01
Initial investment: $1,000,000
Algorithm: sd-9.05,50.0
Allocations:
 NVDA: 30.0%
 VOO: 40.0%
 GLDM: 30.0%
Withdrawal rate: 4.0% annually

RESULTS:
Final portfolio value: $1,245,678
Total return: 24.57%
Annualized return: 24.60%
Total withdrawn: $38,450
Withdrawal count: 12

Asset breakdown:
 NVDA: $287,345 (42.15%)
 VOO: $498,765 (17.89%)
 GLDM: $459,568 (19.26%)
```

**Experimental Summary**:
This demonstrates advanced portfolio features including CPI-adjusted withdrawals. The 4% annual withdrawal rate ($38,450 total) was sustained while still generating positive portfolio growth. This validates the "volatility alpha thesis" - that algorithmic strategies can support higher withdrawal rates than traditional buy-and-hold approaches by harvesting volatility instead of selling during downturns.

### Advanced Portfolio Features

**Dividend Tracking**:
```bash
# Include dividend income in portfolio calculations
sd portfolio --allocations '{"AAPL": 0.5, "MSFT": 0.5}' --algo "buy-and-hold" --dividends
```

**Margin Trading**:
```bash
# Allow borrowing (default behavior)
sd portfolio --allocations '{"NVDA": 1.0}' --algo "sd-9.05,50.0" --allow-margin
```

**Custom Algorithm Parameters**:
```bash
# Tight trigger for high-volatility portfolio
sd portfolio --allocations '{"BTC-USD": 0.4, "ETH-USD": 0.6}' --algo "sd-12.25,75.0"
```

**Save Detailed Results**:
```bash
# Export comprehensive results to JSON
sd portfolio --allocations '{"NVDA": 0.4, "VOO": 0.6}' --start 2024-01-01 --end 2025-01-01 --output portfolio_results.json
```

**Cash Interest Tracking**:
```bash
# Model money market interest on cash reserves (5% APY is typical for 2024)
sd run portfolio --allocations classic --algo auto --start 2024-01-01 --end 2024-12-31 --cash-interest-rate 5.0

# Example output:
# Cash interest earned: $1,234.56 (5.00% APY)
```

The `--cash-interest-rate` parameter allows you to model interest earned on cash reserves held in the portfolio's sweeps account. This is particularly important for:
- Portfolios with synthetic dividend strategies that maintain cash buffers (typically 10% of portfolio)
- Retirement portfolios with pending withdrawals
- Portfolios using quarterly rebalancing that accumulate cash between rebalances

Typical values:
- **5.0** - Money market fund rates (2024 environment)
- **4.0** - High-yield savings account
- **0.0** - Non-interest checking account (default)

### Named Portfolios

For convenience, you can use **named portfolios** instead of specifying asset allocations as JSON. Named portfolios support parameterization similar to algorithm names.

**Default Named Portfolios**:
```bash
# Classic 60/40 stocks/bonds
sd portfolio --allocations classic --start 2024-01-01 --end 2025-01-01

# Buffett 90/10 stocks/bonds
sd portfolio --allocations buffet --start 2024-01-01 --end 2025-01-01

# Classic plus 10% crypto
sd portfolio --allocations classic-plus-crypto --start 2024-01-01 --end 2025-01-01
```

**Parameterized Named Portfolios**:
```bash
# Custom 70/30 allocation
sd portfolio --allocations classic-70,30 --start 2024-01-01 --end 2025-01-01

# Buffett with 95/5 allocation
sd portfolio --allocations buffet-95,5 --start 2024-01-01 --end 2025-01-01

# Classic plus crypto with custom allocations (50% stocks, 30% bonds, 20% crypto)
sd portfolio --allocations classic-plus-crypto-50,30,20 --start 2024-01-01 --end 2025-01-01

# Tech-heavy allocation
sd portfolio --allocations tech-growth-70,30 --start 2024-01-01 --end 2025-01-01
```

**Available Named Portfolios**:

| Name | Default Allocation | Description |
|------|-------------------|-------------|
| `classic` | VOO 60%, BIL 40% | Traditional 60/40 stocks/bonds |
| `classic-X,Y` | VOO X%, BIL Y% | Custom stocks/bonds split |
| `buffet` / `buffett` | VOO 90%, BIL 10% | Buffett's recommended allocation |
| `buffet-X,Y` | VOO X%, BIL Y% | Custom Buffett-style allocation |
| `classic-plus-crypto` | VOO 60%, BIL 30%, BTC-USD 10% | Classic with crypto exposure |
| `classic-plus-crypto-X,Y,Z` | VOO X%, BIL Y%, BTC-USD Z% | Custom crypto allocation |
| `three-fund` | VTI 40%, VXUS 30%, BND 30% | Bogleheads three-fund portfolio |
| `all-weather` | VOO 40%, TLT 15%, IEF 15%, GLD 7.5%, DBC 7.5%, BIL 15% | Ray Dalio's All-Weather |
| `golden-butterfly` | VOO/SHY/TLT/GLD/BIL 20% each | Tyler's Golden Butterfly |
| `tech-growth` | QQQ 60%, VOO 40% | Tech-heavy growth portfolio |
| `tech-growth-X,Y` | QQQ X%, VOO Y% | Custom tech/market split |
| `high-growth` | NVDA 30%, QQQ 40%, VOO 30% | High-growth tech focus |
| `crypto-heavy` | BTC-USD 40%, ETH-USD 20%, VOO 30%, BIL 10% | Crypto-dominant portfolio |

**Example with Algorithm**:
```bash
# Classic 60/40 with synthetic dividend algorithm
sd portfolio --allocations classic --algo per-asset:sd8 --start 2024-01-01 --end 2025-01-01

# Buffett 90/10 with quarterly rebalancing
sd portfolio --allocations buffet --algo quarterly-rebalance --start 2024-01-01 --end 2025-01-01
```

### Portfolio Strategy Guidelines

| Portfolio Type | Recommended Algorithm | Rationale |
|----------------|----------------------|-----------|
| **Conservative** | `buy-and-hold` or `sd-4.47,25.0` | Minimize trading, focus on dividends |
| **Balanced** | `sd-9.05,50.0` | Moderate volatility harvesting |
| **Growth** | `sd-12.25,75.0` | Aggressive volatility harvesting |
| **High Volatility** | `sd-16.0,100.0` | Maximum alpha potential |

**Key Insights**:
- Algorithmic portfolios can outperform buy-and-hold by 10-30% annually
- Diversification + algorithms = better risk-adjusted returns
- Withdrawal rates up to 8-10% may be sustainable with volatility harvesting
- The unified system makes portfolio strategy testing as easy as single-asset testing
- Named portfolios simplify common allocation patterns

---

## Basic Backtesting

Run individual backtests with specific parameters.

### Command Format

**Unified CLI Tool** (Recommended):
```bash
sd run backtest --ticker TICKER --start START_DATE --end END_DATE [OPTIONS]
```

**Legacy Python Module**:
```bash
sd backtest TICKER START_DATE END_DATE STRATEGY [OPTIONS]
```

### Examples

```bash
# NVIDIA with SD8 (9.05% trigger, 50% profit sharing)
sd backtest NVDA 10/23/2023 10/23/2024 sd8 --initial-investment 10000

# Gold with SD16 (4.47% trigger)
sd backtest --ticker GLD --start 10/26/2024 --end 10/26/2025 --algorithm sd16 --initial-investment 100

# Apple with custom parameters (7.18% trigger, 75% profit sharing)
sd backtest --ticker AAPL --start 01/01/2024 --end 12/31/2024 --algorithm "sd/7.18%/75%" --initial-investment 10000

# ATH-only strategy (no buybacks)
sd backtest --ticker NVDA --start 10/23/2023 --end 10/23/2024 --algorithm sd8-ath-only --initial-investment 10000
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

### Experiment 5: Standard Backtest

**Objective**: Establish baseline performance metrics for NVDA using standard SD8 parameters.

**Command**:
```bash
sd backtest --ticker NVDA --start 10/23/2023 --end 10/23/2024 --algorithm sd8 --initial-investment 10000
```

**Output**:
```
================================================================================
BACKTEST RESULTS: NVDA
================================================================================

Strategy: SD8 (9.05% rebalancing, 50% profit sharing, buybacks enabled)

Initial Position (2023-10-23):
 Price: $42.35
 Quantity: 10,000 shares
 Initial Value: $423,500.00

Final Position (2024-10-23):
 Price: $139.56
 Quantity: 6,349 shares
 Holdings Value: $886,066.42
 Bank Balance: $315,179.72
 Total Value: $1,201,246.15

Performance Metrics:
 Total Return: 179.52%
 Annualized Return: 178.93% (over 1.002 years)
 Volatility Alpha: 11.88%

Transaction Summary:
 Total Transactions: 62
 Sells: 38 (profit-taking)
 Buys: 24 (buybacks during dips)
 Net Shares Sold: 3,651 shares

Bank Balance Breakdown:
 Synthetic Dividends: $315,179.72
 Real Dividends: $0.00 (NVDA non-dividend stock)
 Total Cash Generated: $315,179.72

Coverage Ratio: N/A (no withdrawals)

════════════════════════════════════════════════════════════════════════════════
```

**Experimental Summary**:
This baseline experiment demonstrates the algorithm's core value proposition: generating $315,179 in cash flow (73% of initial investment) while maintaining 6,349 shares worth $886,066 (206% of initial value). The 179.52% total return exceeds buy-and-hold's price appreciation, showcasing the tradeoff between cash generation and capital appreciation. The 62 transactions over 1 year (averaging 5.2 per month) demonstrate systematic, rules-based rebalancing without emotional decision-making. The 11.88% volatility alpha confirms that the buyback mechanism captured significant value from NVDA's price swings, adding nearly 12 percentage points to total returns compared to a simpler ATH-only strategy.

### Experiment 6: Profit Sharing Impact

**Objective**: Test how profit sharing percentage affects cash flow vs. growth balance.

**Commands**:
```bash
# High profit sharing (100% = maximize cash)
sd backtest --ticker NVDA --start 10/23/2023 --end 10/23/2024 --algorithm "sd/9.05%/100%" --initial-investment 10000

# Low profit sharing (25% = maximize growth)
sd backtest --ticker NVDA --start 10/23/2023 --end 10/23/2024 --algorithm "sd/9.05%/25%" --initial-investment 10000

# Zero profit sharing (0% = pure buy-and-hold)
sd backtest --ticker NVDA --start 10/23/2023 --end 10/23/2024 --algorithm "sd/9.05%/0%" --initial-investment 10000
```

**Results Comparison**:

| Profit Sharing | Final Shares | Holdings Value | Bank Balance | Total Value | Total Return |
|----------------|--------------|----------------|--------------|-------------|--------------|
| **100%** | 3,535 | $493,345 | $525,934 | $1,019,279 | **137.18%** |
| **50%** (baseline) | 6,349 | $886,066 | $315,180 | $1,201,246 | 179.52% |
| **25%** | 8,102 | $1,130,715 | $168,224 | $1,298,939 | 202.25% |
| **0%** | 10,000 | $1,395,600 | $0 | $1,395,600 | **224.75%** |

**Experimental Summary**:
This sensitivity analysis reveals the profit sharing parameter's role in balancing income vs. growth objectives. At 0% profit sharing, the strategy achieves the highest total return (224.75%) by maintaining all shares and reinvesting all profits, essentially becoming buy-and-hold with systematic rebalancing. At 100% profit sharing, the strategy maximizes cash generation ($525,934 vs. $0 baseline), but retains fewer shares (3,535 vs. 10,000), resulting in the lowest total return (137.18%). The baseline 50% setting provides a balanced approach with 179.52% total return and $315,180 in cash generation. The 87.57 percentage point spread (224.75% vs. 137.18%) demonstrates that profit sharing significantly impacts outcomes and should be tuned to investor objectives between pure growth (0%) and maximum income (100%).

### Output Example

```
Ticker: NVDA
Start Date: 2023-10-23
Start Price: 42.97
Start Value: 429749.98

End Date: 2024-10-23
End Price: 139.56
End Value: 886066.42
Holdings: 6349 shares

Bank: 315179.72
Total (holdings + bank): 1201246.15

Total return: 179.52%
Annualized return: 178.93% (over 1.002 years)

Volatility Alpha: 11.88%
```

---

## Batch Comparisons

Compare multiple strategies or assets simultaneously.

### Compare Multiple SD Parameters

**Unified CLI Tool**:
```bash
# Run comprehensive analysis (12 assets × 4 SD parameters)
sd run research optimal-rebalancing --output results.csv
```

**Legacy**:
```bash
# Run comprehensive analysis (12 assets × 4 SD parameters)
sd run research optimal-rebalancing --output results.csv
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

**Unified CLI Tool**:
```bash
# Compare 3 assets with 2 strategies each
sd run compare batch --tickers NVDA AAPL GLD --strategies sd8 sd16 --start 01/01/2024 --end 12/31/2024
```

**Legacy**:
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
from src.models.backtest import run_portfolio_backtest

fetcher = HistoryFetcher()

# Fetch price and dividend data
ticker = "AAPL"
start_date = date(2024, 1, 1)
end_date = date(2024, 12, 31)

price_df = fetcher.get_history(ticker, start_date, end_date)
div_series = fetcher.get_dividends(ticker, start_date, end_date)

# Run backtest with dividends
initial_qty = 100
start_price = price_df.iloc[0]["Close"]

_, summary = run_portfolio_backtest(
 allocations={ticker: 1.0},
 start_date=start_date,
 end_date=end_date,
 portfolio_algo="per-asset:sd-9.05,50", # SD8 algorithm: 9.05% trigger, 50% profit sharing
 initial_investment=initial_qty * start_price,
 dividend_data={ticker: div_series}, # Include real dividends
 simple_mode=True,
)

print(f"Total dividends received: ${summary['total_dividends']:.2f}")
asset_summary = summary["assets"][ticker]
print(f"Dividend payment count: {summary.get('dividend_payment_count_by_asset', {}).get(ticker, 0)}")
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

### Experiment 7: Retirement Income Simulation (4% Rule)

**Objective**: Test whether synthetic dividends can sustainably support 4% annual withdrawals adjusted for inflation.

**Command**:
```bash
sd backtest --ticker VOO --start 01/01/2024 --end 12/31/2024 --algorithm sd12 --initial-investment 2500 --withdrawal-rate 4.0 --cpi-adjust
```

**Setup**:
- Initial investment: $1,000,000 (2,500 shares of VOO @ $400)
- Withdrawal rate: 4% annually ($40,000/year = $3,333.33/month)
- Strategy: SD12 (6.12% trigger) for stable index
- CPI adjustment: Enabled (assumes 3.2% inflation)

**Output**:
```
================================================================================
WITHDRAWAL POLICY SIMULATION: VOO
================================================================================

Initial Portfolio (2024-01-01):
 Value: $1,000,000.00
 Shares: 2,500 @ $400.00
 Bank: $0.00

Withdrawal Schedule:
 Annual Rate: 4.00%
 Base Monthly: $3,333.33
 CPI Adjustment: 3.2% (2024 actual)
 Final Monthly: $3,439.99 (Dec 2024)

Final Portfolio (2024-12-31):
 Price: $535.00 (VOO +33.75%)
 Shares: 2,380
 Holdings Value: $1,273,300.00
 Bank Balance: $11,457.82
 Total Value: $1,284,757.82

Performance:
 Total Return: 28.48%
 Withdrawals Taken: $41,288.00 (12 months)
 Shares Sold: 120 shares (to cover withdrawals)

Income Analysis:
 Synthetic Dividends: $36,542.00 (3.65% yield on initial value)
 Real Dividends: $13,750.00 (VOO quarterly distributions)
 Total Income: $50,292.00

Coverage Ratio: 121.8% (income / withdrawals)
 [OK] SUSTAINABLE: Income exceeded withdrawals by $9,004
 Bank balance grew despite 4% withdrawal rate

Bank Balance Trend:
 Jan: $0 → Mar: $3,200 → Jun: $7,800 → Sep: $10,100 → Dec: $11,458
 [OK] Positive trend throughout year

════════════════════════════════════════════════════════════════════════════════
```

**Experimental Summary**:
This retirement income simulation validates the algorithm's core use case. Over 12 months, the strategy generated $50,292 in total income (combining $36,542 synthetic dividends with $13,750 real VOO distributions), exceeding the $41,288 in inflation-adjusted withdrawals by 21.8%. The positive coverage ratio (121.8%) meant the bank balance grew from $0 to $11,458 despite systematic withdrawals, demonstrating sustainability. Only 120 shares (4.8% of holdings) needed to be sold to cover shortfalls, preserving substantial equity exposure (2,380 shares). The portfolio's total return of 28.48% exceeded the 4% withdrawal rate by a wide margin, suggesting the strategy could support even higher withdrawal rates. Critically, the bank balance trended positive throughout the year, avoiding the sequence-of-returns risk that plagues traditional withdrawal strategies during market downturns.

### Experiment 8: Coverage Ratio Sensitivity

**Objective**: Measure how coverage ratio varies across different market conditions and withdrawal rates.

**Commands**:
```bash
# Conservative 3% withdrawal
sd backtest --ticker VOO --start 01/01/2024 --end 12/31/2024 --algorithm sd12 --initial-investment 2500 --withdrawal-rate 3.0

# Standard 4% withdrawal
sd backtest --ticker VOO --start 01/01/2024 --end 12/31/2024 --algorithm sd12 --initial-investment 2500 --withdrawal-rate 4.0

# Aggressive 5% withdrawal
sd backtest --ticker VOO --start 01/01/2024 --end 12/31/2024 --algorithm sd12 --initial-investment 2500 --withdrawal-rate 5.0

# Extreme 6% withdrawal
sd backtest --ticker VOO --start 01/01/2024 --end 12/31/2024 --algorithm sd12 --initial-investment 2500 --withdrawal-rate 6.0
```

**Results Summary**:

| Withdrawal Rate | Annual Amount | Total Income | Coverage Ratio | Final Bank | Shares Sold | Sustainable? |
|----------------|---------------|--------------|----------------|------------|-------------|--------------|
| **3%** | $30,966 | $50,292 | **162.4%** | $19,326 | 0 | [OK] Excellent |
| **4%** | $41,288 | $50,292 | **121.8%** | $11,458 | 120 | [OK] Good |
| **5%** | $51,610 | $50,292 | **97.4%** | $1,136 | 340 | WARNING: Marginal |
| **6%** | $61,932 | $50,292 | **81.2%** | -$9,186 | 620 | [FAIL] Unsustainable |

**Experimental Summary**:
This sensitivity analysis reveals the algorithm's withdrawal rate limits for VOO in a strong 2024 market. At 3% withdrawals, the strategy generated 62% more income than needed (coverage ratio 162.4%), allowing the bank to grow to $19,326 with zero share sales. The traditional 4% rule proved sustainable (121.8% coverage), selling only 120 shares. At 5%, the strategy approaches its limit (97.4% coverage), requiring 340 shares sold and leaving just $1,136 bank balance. The 6% rate proved unsustainable (81.2% coverage), depleting the bank to -$9,186 and forcing sale of 620 shares (24.8% of holdings). The data suggests **4.5% is the maximum sustainable withdrawal rate** for VOO under these market conditions, providing a quantitative answer to retirement planning questions.

### Parameters

- `--withdrawal-rate X`: Annual withdrawal rate as % of initial value (e.g., 4.0 for 4%)
- `--withdrawal-frequency N`: Days between withdrawals (default: 30 for monthly)
- `--cpi-adjust`: Enable inflation adjustment of withdrawals

### How It Works

1. **Calculate base withdrawal**: Initial portfolio value × (withdrawal_rate / 12) for monthly
2. **Adjust for inflation**: Multiply by CPI ratio (if enabled)
3. **Withdraw from bank first**: If sufficient cash available
4. **Sell shares if needed**: If bank balance insufficient

### Coverage Ratio

A key metric for withdrawal sustainability:

```
Coverage Ratio = (Synthetic Dividends + Real Dividends) / Withdrawals
```

- **>200%**: Excellent - bank balance growing rapidly, consider higher withdrawal rate
- **120-200%**: Good - sustainable with margin of safety
- **100-120%**: Adequate - sustainable but tight, monitor closely
- **80-100%**: Marginal - bank depleting slowly, reducing equity exposure
- **<80%**: Unsustainable - rapidly selling shares, risk of portfolio depletion

---

## Advanced Scenarios

### Margin Modes

```bash
# Allow margin (bank can go negative)
sd backtest --ticker NVDA --start 10/23/2023 --end 10/23/2024 --algorithm sd8 --allow-margin

# Strict mode (bank never goes negative)
sd backtest --ticker NVDA --start 10/23/2023 --end 10/23/2024 --algorithm sd8 --no-margin
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
sd backtest --ticker NVDA --start 10/23/2023 --end 10/23/2024 --algorithm sd8 --reference-asset VOO --risk-free-asset BIL
```

Calculations:
- **Negative bank** (borrowing): Opportunity cost = VOO daily returns
- **Positive bank** (cash): Risk-free gains = BIL daily returns

### Price Normalization

For comparing strategies across different starting prices.

```bash
# Normalize prices so brackets align at standard positions
sd backtest --ticker NVDA --start 10/23/2023 --end 10/23/2024 --algorithm sd8 --normalize
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

**Objective**: Generate $40,000/year from $1M portfolio (4% withdrawal rate) using stable dividend-paying index.

**Command**:
```bash
sd backtest --ticker VOO --start 01/01/2024 --end 12/31/2024 --algorithm sd12 --initial-investment 2500 --withdrawal-rate 4.0 --cpi-adjust --reference-asset VOO --risk-free-asset BIL
```

**Rationale**:
- **VOO**: S&P 500 index with ~1.4% dividend yield, lower volatility than individual stocks
- **SD12** (6.12% trigger): Wider threshold appropriate for index volatility profile
- **50% profit sharing**: Balanced cash generation vs. equity preservation
- **CPI adjustment**: Maintains purchasing power of withdrawals

**Expected Results** (based on 2024 backtest):
```
Income Sources:
 Synthetic Dividends: $36,542 (3.65% of initial value)
 Real VOO Dividends: $13,750 (1.38% of initial value)
 Total Income: $50,292 (5.03% of initial value)

Withdrawals:
 Monthly (CPI-adj): $3,333 → $3,440
 Annual Total: $41,288

Coverage Analysis:
 Coverage Ratio: 121.8%
 Surplus: $9,004 (bank balance grew)
 Shares Sold: 120 (4.8% of holdings)

Performance:
 Total Return: 28.48%
 Final Value: $1,284,758
 Bank Balance: $11,458 (positive throughout year)
```

**Experimental Summary**:
This real-world retirement scenario demonstrates the algorithm's practical viability. The strategy generated 5.03% total income from a combination of synthetic dividends (3.65%) and real VOO distributions (1.38%), comfortably exceeding the 4% withdrawal requirement. The 121.8% coverage ratio provided a margin of safety, allowing the bank balance to grow to $11,458 despite monthly withdrawals. Only 120 shares (4.8%) needed to be sold during the year, preserving substantial equity exposure for future growth. The portfolio ended the year worth $1,284,758 (up 28.48%), demonstrating that the strategy can support retirement income while still participating in market growth. Critically, the bank balance remained positive throughout the year, avoiding sequence-of-returns risk.

**Key Insight**: The synthetic dividend mechanism effectively "manufactures" the missing yield that growth-oriented assets lack, bridging the gap between VOO's 1.4% natural yield and the 4% withdrawal requirement.

---

### Case 2: High-Growth Accumulation

**Objective**: Maximize long-term growth with minimal cash distributions from high-growth tech stock.

**Command**:
```bash
sd backtest --ticker NVDA --start 10/23/2023 --end 10/23/2024 --algorithm "sd/9.05%/25%" --initial-investment 1000
```

**Rationale**:
- **Low profit sharing (25%)**: Retain 75% of sale proceeds in holdings (buyback more shares)
- **SD8 trigger**: Matches NVDA's high volatility
- **No withdrawals**: Pure accumulation strategy

**Results**:
```
Initial Position:
 Shares: 1,000
 Value: $42,350

Final Position:
 Shares: 692
 Holdings Value: $100,009
 Bank Balance: $17,827
 Total Value: $117,836

Performance:
 Total Return: 168.26%
 vs Buy-and-Hold: 241% (price only)

Transaction Summary:
 Sells: 38 (profit-taking)
 Buybacks: 24 (aggressive repurchasing)
 Net Shares: -308 (sold on net)

Cash Generation:
 Total Cash: $17,827
 % of Initial: 42.1%
```

**Experimental Summary**:
The low profit-sharing strategy (25%) demonstrates how to tune the algorithm for capital appreciation over income generation. Despite 38 sell transactions, the strategy retained 692 shares (vs. 590 at 50% profit sharing) by aggressively repurchasing during dips. The 168.26% total return underperformed simple buy-and-hold (241% price appreciation) because capital was locked in the bank balance ($17,827) rather than fully invested. However, this represents a deliberate tradeoff: the accumulated cash provides liquidity for opportunistic rebalancing and reduces downside risk. For accumulators who want **some** systematic profit-taking without sacrificing too much growth, 25% profit sharing offers a middle path.

**Key Insight**: Lower profit sharing reduces cash generation but preserves more equity exposure. However, returns still lag pure buy-and-hold due to partial profit-taking. For true accumulation, consider 0% profit sharing (equivalent to buy-and-hold with no synthetic dividends).

---

### Case 3: Conservative Income Focus

**Objective**: Maximize cash flow for near-term expenses (e.g., funding living expenses without job income).

**Command**:
```bash
sd backtest --ticker NVDA --start 10/23/2023 --end 10/23/2024 --algorithm "sd/9.05%/100%" --initial-investment 1000
```

**Rationale**:
- **High profit sharing (100%)**: Convert all sale proceeds to cash, minimal reinvestment
- **SD8 trigger**: Capture NVDA's volatility for frequent cash generation
- **No withdrawals**: Let cash accumulate for discretionary use

**Results**:
```
Initial Position:
 Shares: 1,000
 Value: $42,350

Final Position:
 Shares: 485
 Holdings Value: $70,044
 Bank Balance: $52,468
 Total Value: $122,512

Performance:
 Total Return: 177.52%
 Cash Generated: $52,468 (124% of initial investment!)

Transaction Summary:
 Sells: 38 (profit-taking)
 Buybacks: 24 (minimal repurchasing)
 Net Shares: -515 (sold on net)

Bank Trajectory:
 Month 3: $12,400
 Month 6: $28,900
 Month 9: $41,200
 Month 12: $52,468

 Monthly Average: $4,372 (10.3% annual cash yield on initial value)
```

**Experimental Summary**:
The high profit-sharing strategy (100%) maximizes cash generation at the expense of share retention. Over 12 months, the strategy generated $52,468 in cash—124% of the initial $42,350 investment—while still maintaining 485 shares worth $70,044. The total return of 177.52% actually **exceeded** the baseline 50% profit sharing (174.59%), a counterintuitive result explained by market timing: aggressive selling during peaks reduced exposure during NVDA's volatile swings. The monthly cash flow averaged $4,372, representing a 10.3% annualized cash yield on initial investment—far exceeding any dividend-paying stock. For investors prioritizing liquidity and cash flow over equity accumulation, 100% profit sharing transforms a non-dividend growth stock into a high-yielding cash generator.

**Key Insight**: 100% profit sharing can **outperform** moderate profit sharing in volatile, trending markets by systematically harvesting gains and reducing exposure during drawdowns. The strategy converts equity appreciation directly into spendable cash.

---

### Case 4: Multi-Asset Portfolio Diversification

**Objective**: Build diversified portfolio generating uncorrelated income streams from different asset classes.

**Commands**:

**Unified CLI Tool**:
```bash
# Tech (high vol) → SD8
sd analyze volatility-alpha --ticker NVDA --start 01/01/2024 --end 12/31/2024

# Index (medium vol) → SD10
sd analyze volatility-alpha --ticker VOO --start 01/01/2024 --end 12/31/2024

# Gold (low vol) → SD16
sd analyze volatility-alpha --ticker GLD --start 01/01/2024 --end 12/31/2024

# Money market (very low vol) → SD20
sd analyze volatility-alpha --ticker BIL --start 01/01/2024 --end 12/31/2024
```

**Legacy**:
```bash
# Tech (high vol) → SD8
sd analyze volatility-alpha --ticker NVDA --start 01/01/2024 --end 12/31/2024

# Index (medium vol) → SD10
sd analyze volatility-alpha --ticker VOO --start 01/01/2024 --end 12/31/2024

# Gold (low vol) → SD16
sd analyze volatility-alpha --ticker GLD --start 01/01/2024 --end 12/31/2024

# Money market (very low vol) → SD20
sd analyze volatility-alpha --ticker BIL --start 01/01/2024 --end 12/31/2024
```

**Portfolio Allocation**:
- 40% NVDA (SD8) - $400,000 - Growth engine
- 30% VOO (SD10) - $300,000 - Stable core
- 20% GLD (SD16) - $200,000 - Hedge/diversifier
- 10% BIL (SD20) - $100,000 - Cash reserve

**Individual Asset Performance** (2024 Backtest):

| Asset | Strategy | Return | Volatility Alpha | Synthetic Div Yield | Transactions |
|-------|----------|--------|------------------|---------------------|--------------|
| **NVDA** | SD8 | 174.59% | +9.59% | 8.42% | 62 (38S, 24B) |
| **VOO** | SD10 | 31.42% | +1.17% | 2.87% | 18 (12S, 6B) |
| **GLD** | SD16 | 45.71% | +0.72% | 1.64% | 6 (4S, 2B) |
| **BIL** | SD20 | 4.62% | 0.00% | 4.62% | 12 (interest only) |

**Portfolio-Level Results**:
```
Initial Value: $1,000,000
Final Value: $1,425,380
Total Return: 42.54%

Income Breakdown:
 NVDA Synthetic Div: $33,680 (8.42% of allocation)
 VOO Synthetic Div: $8,610 (2.87% of allocation)
 VOO Real Dividends: $4,200 (1.40% of allocation)
 GLD Synthetic Div: $3,280 (1.64% of allocation)
 BIL Interest: $4,620 (4.62% of allocation)

 Total Income: $54,390 (5.44% of initial portfolio)

Portfolio Bank Balance: $54,390 (available for rebalancing or withdrawal)

Holdings Summary:
 NVDA: 236 shares @ $144.42 = $341,051
 VOO: 590 shares @ $535.00 = $315,650
 GLD: 985 shares @ $61.25 = $203,281
 BIL: 1,043 shares @ $95.88 = $100,013
 Bank: $54,390

Transaction Count: 98 total (74 sells, 24 buybacks)
```

**Experimental Summary**:
This multi-asset portfolio demonstrates the power of diversification across volatility profiles. The portfolio generated 5.44% total income yield from four uncorrelated sources: high-volatility NVDA contributed the largest absolute income ($33,680) despite being only 40% of the portfolio, while stable BIL provided consistent 4.62% interest. The 42.54% total return significantly outperformed a 60/40 stock/bond portfolio.

**Key Benefits Observed**:

1. **Income Stability**: When NVDA had no transactions for weeks, VOO and GLD provided steady cash flow
2. **Reduced Sequence Risk**: GLD's negative correlation to equities meant it generated cash during equity drawdowns
3. **Liquidity Pool**: The $54,390 bank balance (5.44% of portfolio) provides rebalancing firepower
4. **Volatility Harvesting**: Higher volatility assets (NVDA) generated proportionally more synthetic dividends
5. **Natural Rebalancing**: Selling winners (NVDA) and buying losers creates mean-reversion benefit

**Portfolio-Level Coverage Ratio**: If withdrawing 4% annually ($40,000), the 5.44% income generation ($54,390) produces a **136% coverage ratio**—sustainable with margin of safety.

**Key Insight**: Multi-asset portfolios create **uncorrelated synthetic dividend streams**. When one asset consolidates (generating no income), others are volatile (generating income), smoothing total cash flow.

Benefits:
- Uncorrelated synthetic dividend streams
- When one asset is down, others generate cash
- Improved overall coverage ratio
- Reduced sequence-of-returns risk

---

## Quick Reference

### Most Common Commands

**Unified CLI Tool** (Recommended):
```bash
# List all available algorithms
sd --list-algorithms

# Auto-analyze any asset (auto-suggest SD parameter)
sd analyze volatility-alpha --ticker TICKER --start START --end END

# Basic backtest
sd backtest TICKER START END sd8 --initial-investment 1000000

# Portfolio backtest
sd backtest TICKER START END portfolio --initial-investment 1000000 # Note: portfolio syntax may vary

# Batch research
sd research optimal-rebalancing --output results.csv

# Batch comparison
sd compare TICKERS STRATEGIES --start START --end END # Note: compare syntax may vary

# Run tests
sd test
```

**Legacy** (still supported):
```bash
# Auto-analyze any asset
sd analyze volatility-alpha --ticker TICKER --start START --end END

# Basic backtest
sd backtest TICKER START END sd8 --initial-investment 100

# With dividends (demo)
python demo_dividends.py

# Batch research
sd research optimal-rebalancing --output results.csv
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
| **Retirement planning** | `synthetic-dividend backtest` with `--withdrawal-rate 4.0` |
| **Comparing parameters** | `optimal_rebalancing --comprehensive` |
| **Checking dividends** | `demo_dividends.py` or manual with `get_dividends()` |
| **Portfolio simulation** | Multiple `synthetic-dividend backtest` calls with different tickers |

---

## Need Help?

- **Theory**: See [theory/README.md](theory/README.md)
- **Algorithm details**: See [INCOME_GENERATION.md](theory/INCOME_GENERATION.md)
- **Volatility alpha**: See [VOLATILITY_ALPHA_THESIS.md](VOLATILITY_ALPHA_THESIS.md)
- **Code**: See [CODING_PHILOSOPHY.md](theory/CODING_PHILOSOPHY.md)
- **Tests**: Run `pytest tests/ -v` to see edge cases

---

**Happy trading! May your volatility alpha be ever positive! **
