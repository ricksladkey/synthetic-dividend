# Income Classification Framework

**Author**: Rick Sladkey
**Date**: October 27, 2025
**Purpose**: Classify and measure different sources of portfolio income

---

## Overview

Portfolio income from volatility harvesting strategies can be decomposed into three distinct components, each with different economic sources and behavioral characteristics. This classification enables precise attribution of returns and meaningful strategy comparisons.

---

## The Three-Tier Framework

### Universal Income: Real Dividends

**Definition**: Dividend and interest payments from underlying assets, calculated using time-weighted average holdings over the accrual period.

**Economic Source**:
- Corporate profit distributions (equity dividends)
- Interest payments (bonds, money market funds)
- ETF distributions (dividend ETFs, bond ETFs)

**Calculation Method**:
```
For each dividend payment on date D:
 accrual_period = [D - 90 days, D] # Typical quarterly period
 avg_holdings = time_weighted_average(holdings_history, accrual_period)
 dividend_income = div_per_share × avg_holdings
```

**Time-Weighted Rationale**:
- **IRS-approved**: Reflects actual economic ownership during accrual period
- **Mathematically correct**: Accounts for holdings changes within dividend period
- **Fair attribution**: You only earn dividends for days you held shares

**Example**:
```
Quarterly dividend: $0.25/share, ex-date Feb 15
Purchase date: Jan 1 (45 days before dividend)
90-day lookback: Nov 17 - Feb 15

Holdings: 100 shares continuously from Jan 1
Time-weighted average: 100 shares × 45 days / 90 days = 50 shares
Dividend payment: $0.25 × 50 = $12.50

Note: Only 50% of dividend because shares held for 50% of accrual period
```

**Characteristics**:
- [OK] **Universal**: All strategies receive this (buy-and-hold, ATH-only, full algorithm)
- [OK] **Predictable**: Quarterly/monthly schedule, relatively stable amounts
- [OK] **Passive**: No trading required, asset-dependent
- [OK] **Tax-advantaged**: Qualified dividends taxed at preferential rates
- WARNING: **Holding-sensitive**: Frequent trading reduces time-weighted average

---

### Primary Income: ATH Profit-Taking

**Definition**: Profits from systematic selling at new all-time high prices.

**Economic Source**:
- Capturing **permanent** upward price movements
- Monetizing **secular growth** in asset value
- Realizing gains that exceed previous peaks

**Mechanism**:
```
When price reaches new ATH:
 sell_quantity = rebalance_size × holdings × profit_sharing
 proceeds = sell_quantity × ATH_price
 profit = proceeds - cost_basis_of_sold_shares
```

**Strategy Presence**:
- **Buy-and-hold**: [FAIL] Zero (never sells)
- **ATH-only baseline**: [OK] Full (only sells at ATH)
- **Full algorithm**: [OK] Full (sells at ATH + rebalancing)

**Characteristics**:
- **Core strategy feature**: Primary mechanism for profit realization
- **Trend-following**: Captures secular bull markets
- **Irreversible**: ATH sales lock in permanent gains
- ⏳ **Infrequent**: Only triggers on new price records
- **High quality**: Selling at peaks maximizes proceeds

**Example Timeline**:
```
Price progression: $100 → $110 (ATH) → $105 → $120 (ATH)

ATH-only triggers:
 - $110: Sell at new ATH
 - $120: Sell at new ATH

Between ATHs: No action (holds through dip to $105)
```

---

### Secondary Income: Volatility Alpha

**Definition**: Excess profits from mean-reversion harvesting during price oscillations below all-time high.

**Economic Source**:
- **Temporary** price dislocations (volatility, sentiment)
- Mean reversion within long-term uptrend
- Buying dips, selling bounces (while below ATH)

**Mechanism**:
```
Below ATH, place symmetric orders:
 Buy at: last_price / (1 + rebalance_size) [dip buying]
 Sell at: last_price × (1 + rebalance_size) [bounce selling]

When buy executes:
 - Add shares to buyback stack (LIFO tracking)
 - Profit = (previous_sell_price - buy_price) × quantity

When sell executes:
 - Unwind buyback stack (LIFO/FIFO)
 - Already captured profit on the prior buy
```

**Mathematical Definition**:
```
Volatility Alpha = (Full algorithm return) - (ATH-only return)
```

This isolates the **pure mean-reversion component** by comparing:
- **Full**: ATH selling + volatility harvesting
- **ATH-only**: ATH selling only (no buybacks)

**Strategy Presence**:
- **Buy-and-hold**: [FAIL] Zero (never trades)
- **ATH-only baseline**: [FAIL] Zero (by design, no buybacks)
- **Full algorithm**: [OK] Full (buyback-enabled)

**Characteristics**:
- 🎁 **Pure bonus**: Additive to ATH profits
- 🌊 **Volatility-dependent**: Requires oscillating prices
- ⚡ **High frequency**: Many small transactions
- 🔄 **Reversible**: Profits from round-trips (buy low, sell high)
- **Market-neutral component**: Works in sideways/choppy markets

**Example Cycle**:
```
Price: $100 (ATH) → $91.62 → $100 → $91.62 → $100 → $109.15 (new ATH)

Full algorithm actions:
 1. $100→$91.62: BUY (dip) - stack: [91.62]
 2. $91.62→$100: SELL (bounce) - unwind, profit: $8.38/share
 3. $100→$91.62: BUY (dip again) - stack: [91.62]
 4. $91.62→$100: SELL (bounce) - unwind, profit: $8.38/share
 5. $100→$109.15: SELL at new ATH - primary income

Volatility alpha: 2 × $8.38 = $16.76 per cycle
Primary income: ATH sale at $109.15
```

---

## Income Attribution

### Total Return Decomposition

```
Total Return = Universal + Primary + Secondary + Capital Appreciation
```

Where:
- **Universal**: ∑(dividends) over holding period
- **Primary**: ∑(ATH sell proceeds - cost basis)
- **Secondary**: Total return - ATH-only return (isolates vol alpha)
- **Capital Appreciation**: Change in unrealized holdings value

### Comparative Analysis

| Strategy | Universal | Primary | Secondary | Use Case |
|----------|-----------|---------|-----------|----------|
| **Buy-and-hold** | [OK] | [FAIL] | [FAIL] | Baseline comparison |
| **ATH-only** | [OK] | [OK] | [FAIL] | Primary income baseline |
| **Full algorithm** | [OK] | [OK] | [OK] | Complete volatility harvesting |

**Insight**: The three-tier comparison reveals:
1. **Dividend contribution**: Buy-and-hold vs. zero
2. **ATH selling value**: ATH-only vs. buy-and-hold
3. **Volatility harvesting value**: Full vs. ATH-only

---

## Nuances and Edge Cases

### Dividend Timing with Frequent Trading

**Challenge**: Volatile strategies change holdings frequently, reducing time-weighted dividend payments.

**Example**:
```
Scenario: Quarterly dividend on stock with 9.15% volatility harvesting

Holdings timeline (100 shares initial):
 Day 1-30: 100 shares (bought dip +10)
 Day 31-60: 90 shares (sold bounce -10)
 Day 61-90: 100 shares (bought dip +10)

Time-weighted average: (100×30 + 90×30 + 100×30) / 90 = 96.67 shares

Dividend payment: $0.25 × 96.67 = $24.17
Snapshot (wrong): $0.25 × 100 = $25.00

Difference: -$0.83 (3.3% reduction from trading)
```

**Implication**: High-frequency volatility harvesting creates **dividend drag** through reduced time-weighted holdings.

**Mitigation**:
- Use smaller rebalance sizes (fewer trades)
- Focus on low-dividend/high-volatility assets
- Accept dividend drag as cost of volatility alpha

---

### ATH-Only as Perfect Control

**Why ATH-only is the ideal baseline**:

1. **Isolates volatility component**:
 - Same ATH-selling mechanism as full algorithm
 - Only difference: buyback feature enabled/disabled
 - Clean A/B test of mean reversion value

2. **Controls for trend exposure**:
 - Both strategies profit from secular growth
 - Both realize gains at new highs
 - Secondary income = pure volatility harvesting

3. **Equivalent risk profile below ATH**:
 - ATH-only holds through dips
 - Full algorithm buys dips (adds risk)
 - But symmetric: sells bounces (reduces risk)
 - Net: similar risk, additional alpha

**Mathematical Purity**:
```
α_volatility = R_full - R_ath_only

Where both share:
 - Same initial investment
 - Same dividend stream (approximately, modulo time-weighting)
 - Same ATH profit-taking

Different only in:
 - Buyback behavior (disabled vs. enabled)
```

---

### Multi-Bracket Gaps and Stack Mechanics

**Challenge**: Large gaps (>1 bracket) create multiple stack entries.

**Example**:
```
Price: $100 → $83.94 (gap down 2 brackets, 9.15% each)

Iteration 1: Buy at $91.62 → stack: [(91.62, qty)]
Iteration 2: Buy at $83.94 → stack: [(91.62, qty), (83.94, qty)]

Later recovery:
 $83.94 → $91.62: Sell → unwind (83.94, qty) → profit per bracket
 $91.62 → $100: Sell → unwind (91.62, qty) → profit per bracket

Result: Two separate LIFO entries ensure symmetric unwinding
```

**Why this matters for income classification**:
- Each bracket crossing is a separate **secondary income event**
- Primary income: Still just the ATH sale (when price exceeds $100)
- Gap bonuses accumulate in secondary income bucket

---

### Withdrawals Impact on Income

**Systematic withdrawals affect all three components**:

1. **Universal (dividends)**:
 - Reduced holdings → lower time-weighted average
 - Linear reduction in dividend income

2. **Primary (ATH sales)**:
 - Smaller position → smaller ATH sale quantities
 - Linear reduction in ATH proceeds

3. **Secondary (volatility alpha)**:
 - Trade sizes scale with holdings
 - Alpha percentage may stay constant
 - But absolute dollar alpha reduces

**Example**:
```
4% withdrawal rate, $100k portfolio

Year 1: No withdrawals
 - Holdings: ~1000 shares
 - Vol alpha: $3,500 (3.5% of portfolio)

Year 10: After $40k withdrawals
 - Holdings: ~600 shares (60% of original)
 - Vol alpha: $2,100 (60% of original, same 3.5% rate)
```

---

## Practical Applications

### Portfolio Reporting

**Recommended output format**:
```
═══════════════════════════════════════════════════════
INCOME BREAKDOWN (Synthetic Dividend Strategy)
═══════════════════════════════════════════════════════

Universal Income (Asset Dividends):
 Total Dividends: $1,250.00
 Payment Count: 16
 Average per Payment: $78.13
 Yield on Initial Investment: 1.25%

Primary Income (ATH Profit-Taking):
 Total ATH Sales: $8,750.00
 Transaction Count: 12
 Average per Sale: $729.17
 Return on Initial: 8.75%

Secondary Income (Volatility Alpha):
 Total Harvested: $3,420.00
 Buyback Cycles: 87
 Average per Cycle: $39.31
 Alpha vs ATH-only: 3.42%

──────────────────────────────────────────────────────
Total Income: $13,420.00
Total Return: 13.42%
Annualized Return: 6.23%
═══════════════════════════════════════════════════════
```

### Research Questions

This framework enables precise hypothesis testing:

1. **Does volatility alpha persist across asset classes?**
 - Compare secondary income % for stocks, ETFs, crypto

2. **What rebalance size maximizes secondary income?**
 - Plot volatility alpha vs. rebalance_size parameter

3. **How much dividend drag from frequent trading?**
 - Compare time-weighted dividends: full vs. ATH-only vs. buy-and-hold

4. **Is secondary income tax-efficient?**
 - Analyze holding periods: short-term vs. long-term gains

---

## Summary

The three-tier income classification provides:

[OK] **Clear attribution**: Know exactly where returns come from
[OK] **Meaningful comparisons**: Isolate each component's contribution
[OK] **Research framework**: Test hypotheses about each income source
[OK] **Economic insight**: Understand what drives strategy performance

**Universal income** = What the asset gives you (passive)
**Primary income** = What the trend gives you (ATH selling)
**Secondary income** = What volatility gives you (mean reversion)

The sum is greater than the parts: all three working together create a **complete volatility harvesting system**.
