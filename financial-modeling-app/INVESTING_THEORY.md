# Synthetic Dividend Investment Theory

This document explains the investment philosophy and mathematical foundations of the Synthetic Dividend algorithm.

## Origin: Why "Synthetic Dividend"?

The term **"synthetic dividend"** addresses a fundamental misconception in investing: that dividends provide "free cash" without sacrificing growth potential.

### The Dividend Illusion

**Traditional thinking**:
- Dividend stocks → get cash without selling holdings → keep all future profit potential
- Growth stocks → must sell shares to get cash → forfeit future gains on sold shares

**Economic reality**: 
- **Dividends don't matter** - only total return matters
- **ALL cash withdrawals cost opportunity money equally**, regardless of mechanism
- Whether you lose opportunity at the track, invest in a meme stock, receive a dividend, or sell shares - the economic result is identical

### The Universal Problem

When you need cash from a portfolio:
- **Dividend received**: Company sends cash, stock price drops by dividend amount → your total value is unchanged
- **Shares sold**: You receive cash, holdings decrease → your total value is unchanged
- **Net effect**: Identical! Both reduce your future compound potential by the same amount

The question isn't "dividends vs. selling" - it's "**how do you systematically withdraw cash while maintaining long-term position value?**"

### The Synthetic Dividend Solution

If the stock is up, it's worth more. You can:
1. **Sell a share or two** at the higher price
2. **Pocket the profit** (cash for distributions/income/new opportunities)
3. **Remaining shares are worth more** than when you initially invested
4. **Total VALUE is up** - you haven't "sold your principal" in dollar terms
5. You've sold shares, but your **remaining position is worth proportionally more**

**This is the "synthetic dividend"**: 
- Self-generated cash flow from appreciation
- Rules-based (no market timing required)
- Allows asset to grow arbitrarily large
- Accepts that **all withdrawals reduce upside** (opportunity cost is universal)
- Systematically captures profit while maintaining dollar-value exposure

### Key Insight: Total Return Is All That Matters

**Dividend stocks**:
- Total return = Price appreciation + Dividends
- Example: Stock at $100 → $105, pays $2 dividend → 7% total return
- You receive $2 cash, stock now worth $105

**Growth stocks with synthetic dividends**:
- Total return = Price appreciation
- Example: Stock at $100 → $107 → sell 1.87% of shares for $2 → 7% total return
- You receive $2 cash, remaining position worth $105

**Economically identical**. The only differences:
- **Tax efficiency**: You control when to realize gains (growth stock wins)
- **Flexibility**: You choose distribution amount and timing (growth stock wins)  
- **Simplicity**: Dividend arrives automatically (dividend stock wins)

The Synthetic Dividend algorithm provides the **flexibility and tax efficiency of growth stocks** with the **predictable cash flow of dividend stocks**, using simple rules that require no discretionary decisions.

## Overview

The **Synthetic Dividend Algorithm** is a rules-based position-sizing and profit-taking strategy that generates cash flow from growth assets without traditional dividend income. It operates on a simple principle: systematically take profits at all-time highs (ATHs) and reinvest during drawdowns.

## Core Concept: Profit Sharing Ratio

The **profit sharing ratio** is a critical parameter that controls the balance between profit-taking and long-term growth.

### The 50% Sweet Spot

**Profit sharing of 50% is a strategic value** that balances immediate profit realization while allowing continued position growth. This ratio ensures:

1. **Half of volatility gains are captured** as cash (bank balance)
2. **Half of the position remains invested** to compound long-term
3. **Over extended periods**, the position fully capitalizes on growth trends
4. **Short-term volatility** provides regular income without sacrificing long-term exposure

In bull markets (like the 1-year NVDA example showing 29% returns), the growth penalty from profit-taking is minimal because the remaining position continues to appreciate substantially.

### Extended Range: Beyond 0-100%

The algorithm **mathematically supports profit sharing values outside the conventional 0-100% range**, with predictable and useful effects:

**Profit Sharing > 100%**:
- **Systematically reduces position size** as new all-time highs are reached
- Sells more shares than the rebalance would naturally dictate
- Useful for **position exit strategies** or **de-risking** at targets
- Example: 150% profit sharing will steadily convert equity to cash on uptrends

**Profit Sharing < 0% (Negative)**:
- **Steadily increases investment from cash** as asset price rises
- Buys additional shares even when selling would normally occur
- Useful for **dollar-cost averaging** into strength
- Example: -50% profit sharing converts rallies into accumulation opportunities

**Practical Implication**: The algorithm becomes a flexible position-sizing tool where profit sharing controls the **direction and rate** of position changes relative to price movements.

### Rebalancing Trigger vs. Profit Sharing

**Key Insight**: Varying the **rebalancing trigger** (e.g., 5%, 9.05%, 15%, 25%) has significantly more impact on returns than varying the profit sharing ratio.

**Why?**
- **Rebalancing trigger** determines transaction frequency and volatility harvesting opportunities
- Lower triggers (5-7.5%) → more frequent trades → more alpha from volatility
- Higher triggers (15-25%) → fewer trades → lower transaction costs but less harvesting
- **Profit sharing** primarily affects position trajectory, not opportunity identification

**Empirical Evidence** (from batch comparison results):
- `sd-7.5,100` → 34.14% return (67 transactions)
- `sd-7.5,50` → 31.41% return (67 transactions)
- `sd-25,100` → 33.14% return (23 transactions)
- `sd-25,50` → 30.14% return (23 transactions)

Changing rebalance threshold from 7.5% to 25% reduces transaction count by 66% while maintaining similar returns. Changing profit sharing within same rebalance threshold shows smaller impact (~2-3% difference).

**Design Recommendation**: 
1. **Optimize rebalancing trigger first** based on asset volatility and transaction costs
2. **Set profit sharing to 50%** as the balanced default
3. **Adjust profit sharing** only for specific strategic goals (accumulation, de-risking)

## Bank Balance and Opportunity Costs

The algorithm tracks **bank balance statistics** to measure cash management efficiency:

**Metrics Tracked**:
- `bank_min`: Most negative balance (maximum margin used)
- `bank_max`: Highest cash balance
- `bank_avg`: Average cash position over backtest period
- `bank_negative_count`: Number of days with negative balance (borrowing)
- `bank_positive_count`: Number of days with positive balance (cash earning interest)

**Financial Adjustments**:

1. **Opportunity Cost** (when bank < 0):
   - Represents the cost of borrowing to maintain position
   - Calculated using reference return (e.g., S&P 500 TR ~10% annually)
   - Formula: `sum(abs(negative_bank_balance) * daily_reference_rate)`
   - Penalizes strategies that require sustained margin

2. **Risk-Free Gains** (when bank > 0):
   - Represents interest earned on cash reserves
   - Calculated using risk-free rate (e.g., Treasury bills ~4.5% annually)
   - Formula: `sum(positive_bank_balance * daily_risk_free_rate)`
   - Rewards strategies that maintain cash buffers

**Interpretation**: Strategies with large negative bank balances incur opportunity costs (foregone returns from alternative investments). Strategies with large positive balances earn risk-free returns but may sacrifice growth.

**Example**:
- Algorithm with avg bank = -$50,000 over 1 year at 10% reference return
- Opportunity cost ≈ $5,000 (reduces net return by ~0.35% on $1.4M portfolio)

This adjustment provides a more **realistic comparison** between strategies by accounting for the cost of capital.

## Asset-Based Financial Adjustments: The Real-World Model

**Critical Insight**: Fixed annual rates (10% reference, 4.5% risk-free) are **unrealistic** because they assume constant benchmark returns regardless of market conditions. The actual cost/benefit of capital varies with market performance.

**Enhanced Model** (implemented October 2025):

Instead of fixed rates, we now use **actual historical returns** from competing assets:
- **Reference Asset** (default: VOO - Vanguard S&P 500 ETF)
- **Risk-Free Asset** (default: BIL - SPDR 1-3 Month T-Bill ETF)

**Why This Matters**:

1. **Opportunity Cost Isn't a Penalty, It's a Comparison**
   - When bank is negative, we're not "paying interest" to anyone
   - We're measuring: "This capital could have been in VOO instead"
   - If VOO drops 5% that day → our "cost" is negative (we SAVED 5%!)
   - If VOO gains 2% that day → our cost is 2% of borrowed amount
   - This captures **relative performance**, not absolute penalty

2. **Example: Market Downturn Scenario**
   - Strategy A: Aggressive trading, -$200K avg bank
   - Strategy B: Conservative trading, -$50K avg bank
   
   **Old Model** (Fixed 10% rate):
   - Strategy A: -$20K opportunity cost (looks terrible)
   - Strategy B: -$5K opportunity cost (looks better)
   
   **New Model** (VOO actually returned -15% during period):
   - Strategy A: **+$30K** (saved by staying in NVDA, not VOO!)
   - Strategy B: **+$7.5K** (smaller benefit)
   - Strategy A is **better** because it avoided VOO's decline

3. **The Barbell Philosophy: Cash as Stability Mechanism**
   - As the target asset rallies → profit-taking → **cash accumulates**
   - This cash is **"gold"** - a barbell stabilizer for the portfolio
   - Cash earns BIL returns (T-bill equivalent, essentially risk-free)
   - Provides liquidity for distributions without forced selling
   - Protects against having to sell during downturns

4. **Daily Return Calculation**
   - Fetch historical data for VOO and BIL during backtest period
   - Calculate actual daily returns: `(today_price - yesterday_price) / yesterday_price`
   - Apply these actual returns to each day's bank balance
   - Sum across all days for total opportunity cost / risk-free gains

**Realistic Interpretation**:
- **Negative bank** = Capital "borrowed" from potential VOO investment
- **Positive bank** = Cash earning risk-free rate (BIL)
- **Neither is inherently good or bad** - depends on relative performance
- During bull markets: negative bank has higher cost (missing VOO gains)
- During bear markets: negative bank has negative cost (avoiding VOO losses)

**Implementation Example** (NVDA 10/22/2024-10/22/2025):
```
Bank Min: -$262,230 (max margin used)
Bank Avg: -$77,578 (mostly borrowed capital)
Opportunity Cost (VOO): -$8,306
Risk-Free Gains (BIL): +$33
Net Financial Adjustment: +$8,339
```

The **negative opportunity cost** means VOO actually declined during days when we had borrowed capital - we benefited by being in NVDA instead!

## Profit Sharing as Position Sizing: The Complete Strategy Spectrum

**Key Insight**: Profit sharing percentage determines **long-term position trajectory**, not just profit-taking amount.

**The Strategy Spectrum**:

1. **0% Profit Sharing = Buy-and-Hold**
   - Never take profits (never SELL except initial rebalance)
   - Position stays at 100% of initial shares
   - Equivalent to traditional buy-and-hold
   - No bank account needed
   - Maximum growth exposure, zero cash generation

2. **100% Profit Sharing = Constant-Weight Rebalancing**
   - Take full profits on every rebalance
   - Position shrinks toward single maximum share allocation
   - Equivalent to traditional constant-weight portfolio strategy
   - Over 10 years: locks into single maximum exposure (in nominal terms!)
   - Generates maximum cash, sacrifices long-term growth

3. **50% Profit Sharing = Best of Both Worlds**
   - Balanced profit-taking and position maintenance
   - Position can grow over long periods while still generating cash
   - Solves the **universal growth portfolio problem**: generating distributions without sufficient dividends
   - Creates predictable rules-based cash flow
   - Only unknown: **when** ATHs occur, not **whether** they occur

### The 10-Year Perspective

Why 50% beats 100% over long horizons:

- **100% Case**: After first ATH, you lock into maximum share count
  - Can never increase position size in nominal terms
  - Inflation erodes real exposure over time
  - Miss compound growth on the position itself
  - Example: Start with 10,000 shares → peak at 11,000 → stay at ~11,000 forever

- **50% Case**: Position can grow steadily
  - Half of gains stay in the position
  - Compound growth on growing share count
  - Still generate meaningful cash distributions
  - Example: Start with 10,000 → 12,000 → 14,000 → 16,000 over years
  - Generates cash while maintaining growth exposure

- **0% Case**: Maximum position growth, zero distributions
  - Full compound growth exposure
  - No cash for new opportunities or living expenses
  - Forced to sell externally if cash needed

### Why This Solves a Universal Problem

Traditional growth portfolios face a dilemma:
- **Dividends alone** are never enough for meaningful distributions (~1-2% yields)
- **Forced selling** for cash creates timing risk and tax events
- **Rebalancing to fixed income** sacrifices growth potential

**Synthetic Dividend Solution**:
- **Rules-based**: Profit-taking only at ATHs (strength, not weakness)
- **Predictable**: Formula-driven, no discretionary timing
- **Growth-preserving**: 50% keeps position growing with asset
- **Distribution-generating**: Creates cash flow without external sales
- **Only unknown**: WHEN ATHs occur, not IF they occur (assumes long-term growth)

### Strategic Use Cases

- **<0% (e.g., -25%)**: Accumulation mode - actually ADD on strength
  - Use when building position in quality asset
  - Buy more at ATHs instead of selling
  - Negative bank grows (requires external capital source)

- **0-25%**: Growth emphasis with minimal distributions
  - Near buy-and-hold performance
  - Small cash generation for optionality

- **25-50%**: Balanced growth and distributions
  - Sweet spot for most scenarios
  - Meaningful cash flow + position growth

- **50-75%**: Income emphasis with growth participation
  - Higher distributions, slower position growth
  - Good for transitioning to distribution phase

- **75-100%**: Maximum distributions, position maintenance
  - Position plateaus at max exposure
  - Maximum cash generation

- **>100% (e.g., 125%)**: De-risking mode
  - Actively reduce position at ATHs
  - Rotate out of concentrated holdings
  - Build cash reserves for redeployment

## Design Philosophy Summary

The Synthetic Dividend algorithm is a **flexible position-sizing tool** disguised as a profit-taking strategy. By adjusting a single parameter (profit sharing percentage), you control the position trajectory from aggressive accumulation (<0%) to maximum de-risking (>100%), while the rebalancing trigger determines transaction frequency and volatility harvesting efficiency.

The 50% default represents the **optimal balance** for most growth-oriented portfolios: maintain long-term compound exposure while generating predictable cash flow for distributions and new opportunities, all governed by simple rules that require no market timing or discretionary decisions.

---

**Last Updated**: October 2025
**Contributors**: Project maintainers and investment strategists
