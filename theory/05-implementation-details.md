# 05 - Implementation Details

**How it works in practice** - Technical execution details, parameters, and operational considerations.

**Author**: Synthetic Dividend Research Team
**Created**: October 29, 2025
**Reading Time**: 20 minutes
**Related**: 02-algorithm-variants.md, 04-income-generation.md, 07-research-validation.md

---

## Executive Summary

**Implementation Stack**:
- **Algorithm layer**: Strategy logic and state management
- **Backtest engine**: Historical simulation with transaction tracking
- **Data layer**: Price feeds with normalization and caching
- **Analysis layer**: Performance metrics and validation

**Key Parameters**:
- **Rebalance size (sdN)**: Controls bracket frequency (SD8 = 9.05% standard)
- **Profit sharing**: Income vs growth allocation (50% = balanced)
- **Algorithm variant**: Buyback and selling behavior

**Execution Flow**: Price change → bracket calculation → order generation → position update → metrics tracking.

---

## Part 1: Algorithm Architecture

### 1.1 Core Components

**AlgorithmBase**: Abstract interface for all strategies

**SyntheticDividendAlgorithm**: Main implementation with configurable parameters

**Factory pattern**: String-based algorithm instantiation (`sd-9.05,50`)

**State management**: Holdings, bank balance, buyback stack, ATH tracking

### 1.2 Key Classes

**Transaction**: Individual buy/sell records with metadata

**Holding**: Position tracking with cost basis and lot management

**Backtest**: Simulation engine with market data integration

**Asset**: Data fetching and caching layer

### 1.3 Data Flow

```
Market Data → Algorithm.on_day() → Orders Generated → Backtest Execution → Metrics Calculated
```

---

## Part 2: Rebalancing Mechanics

### 2.1 Bracket Calculation

**Exponential scaling**: `Bracket_price = Last_transaction_price × (1 ± rebalance_size)`

**SD naming convention**:
- SD4: 18.92% (2^(1/4) - 1)
- SD6: 12.25% (2^(1/6) - 1)
- SD8: 9.05% (2^(1/8) - 1)
- SD10: 7.18% (2^(1/10) - 1)

### 2.2 Trigger Detection

**Buy triggers**: Price drops to or below next lower bracket

**Sell triggers**:
- **Standard SD**: Price rises to next higher bracket
- **ATH-Only**: Price exceeds all-time high
- **ATH-Sell**: Price exceeds all-time high (for buyback shares only)

### 2.3 Order Generation

**Symmetry property**: Buy quantity at lower bracket = sell quantity from current bracket

**Share calculation**: `shares = floor(holdings × rebalance_size)`

**Price execution**: Market orders at current price

---

## Part 3: Buyback Stack Management

### 3.1 Stack Structure

**LIFO stack**: Newest buybacks sold first (Last-In-First-Out)

**Per-lot tracking**: Individual cost basis for each buyback

**Profit attribution**: Gains/losses calculated per lot

### 3.2 Unwinding Logic

**ATH-Sell variant**: Only unwind when price exceeds all-time high

**Standard SD**: Unwind at bracket levels during recovery

**Partial unwinding**: Sell available shares up to order quantity

### 3.3 Stack Metrics

**Stack size**: Number of shares available for unwinding

**Stack depth**: Number of distinct buyback lots

**Average cost**: Weighted average cost basis of stack

---

## Part 4: Bank Balance Mechanics

### 4.1 Transaction Effects

**SELL orders**: Increase bank balance

**BUY orders**: Decrease bank balance (may go negative)

**Dividend payments**: Increase bank balance

**Withdrawals**: Decrease bank balance

### 4.2 Margin Handling

**Allow margin**: Bank can go negative (borrow against future gains)

**No margin**: Bank cannot go negative (skip buys when insufficient cash)

**Default**: Margin enabled for full volatility harvesting

### 4.3 Opportunity Cost Tracking

**Bank balance**: Tracks trading cash flow

**Separate tracking**: Initial capital opportunity cost

**Risk-free rate**: Applied to positive bank balances

**Reference rate**: Applied to negative bank balances

---

## Part 5: All-Time High Tracking

### 5.1 ATH Definition

**ATH**: Highest price ever reached in the asset's history

**Reset conditions**: Never resets (permanent high watermark)

**Tracking**: Updated on every price bar

### 5.2 ATH-Sell Implementation

**Buy logic**: Same as Standard SD (bracket-based)

**Sell logic**: Only when current price > ATH

**ATH updates**: New ATHs enable selling of previously bought shares

### 5.3 ATH-Only Implementation

**Sell logic**: When current price > previous ATH

**No buybacks**: Pure profit-taking strategy

**Path independence**: Results depend only on price path extrema

---

## Part 6: Price Normalization

### 6.1 Purpose

**Deterministic brackets**: Same relative positions across assets

**Comparison fairness**: Equal starting capital across backtests

**Mental math ease**: Round numbers for intuitive understanding

### 6.2 Implementation

**Normalization**: All prices scaled so first price = $100

**Formula**: `normalized_price = raw_price × (100 / first_price)`

**Reversibility**: All calculations work on normalized or raw prices

### 6.3 Benefits

**Cross-asset comparison**: Same initial investment amount

**Visual consistency**: Charts start at same price level

**Mathematical simplicity**: Easier percentage calculations

---

## Part 7: Withdrawal Policy

### 7.1 Bank-First Approach

**Priority order**:
1. Use available bank balance
2. Sell shares if needed (ATH-Sell: only at ATH)
3. Skip withdrawal if insufficient funds (no margin mode)

### 7.2 Withdrawal Frequency

**Supported**: Daily, monthly, quarterly, annual

**Default**: Monthly for retirement modeling

**CPI adjustment**: Optional inflation protection

### 7.3 Withdrawal Rate

**Standard**: 4% annual rate (retirement planning)

**Testing range**: 2% to 8% for sustainability analysis

**Dynamic**: Can adjust based on coverage ratios

---

## Part 8: Performance Metrics

### 8.1 Primary Metrics

**Total return**: Final portfolio value / initial investment

**Annualized return**: CAGR over backtest period

**Volatility alpha**: Excess return vs buy-and-hold

### 8.2 Supplementary Metrics

**Capital utilization**: Average deployed capital percentage

**Bank metrics**: Min/max/average bank balance

**Transaction counts**: Buy/sell frequency

**Stack metrics**: Buyback accumulation and unwinding

### 8.3 Risk Metrics

**Bank negative count**: Periods of borrowing

**Bank utilization**: Cash deployment efficiency

**Drawdown protection**: Forced selling avoidance

---

## Part 9: Algorithm Factory

### 9.1 Naming Convention

```
sd-{rebalance_size},{profit_sharing} # Standard SD
sd-ath-only-{rebalance_size},{profit_sharing} # ATH-Only
sd-ath-sell-{rebalance_size},{profit_sharing} # ATH-Sell (new)
```

**Examples**:
- `sd-9.05,50`: Standard SD, 9.05% brackets, 50% profit sharing
- `sd-ath-only-9.05,50`: ATH-Only variant
- `sd-ath-sell-9.05,50`: ATH-Sell variant

### 9.2 Parameter Validation

**Rebalance size**: 0.01 to 0.50 (1% to 50%)

**Profit sharing**: 0.0 to 1.5 (0% to 150%)

**Variant validation**: Must be recognized algorithm type

### 9.3 Instantiation Flow

**Parse name** → **Extract parameters** → **Create algorithm instance** → **Validate configuration**

---

## Part 10: Backtesting Infrastructure

### 10.1 Data Requirements

**OHLC data**: Open, High, Low, Close prices

**Date indexing**: Chronological ordering required

**No gaps**: Missing data handling

### 10.2 Execution Model

**Daily processing**: One algorithm call per trading day

**Price timing**: Use Close price for decisions

**Transaction timing**: Execute at next day's Open (realistic slippage)

### 10.3 Result Validation

**Conservation laws**: Money and shares conserved

**Path consistency**: Same algorithm, different paths → consistent behavior

**Edge case handling**: Extreme volatility, gaps, dividends

---

## Key Takeaways

1. **Bracket system**: Exponential scaling ensures consistent relative positioning
2. **Buyback stack**: FIFO management with per-lot profit attribution
3. **ATH tracking**: Permanent high watermark for sell trigger logic
4. **Bank mechanics**: Separate trading cash flow from equity position
5. **Factory pattern**: String-based instantiation for easy configuration
6. **ATH-Sell innovation**: Conditional selling based on new ATH achievement

**Next**: Read `06-applications-use-cases.md` to see real-world deployment scenarios.