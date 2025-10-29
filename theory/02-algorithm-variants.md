# 02 - Algorithm Variants

**The four strategy implementations** - Complete catalog of Synthetic Dividend algorithms with mechanics, trade-offs, and use cases.

**Author**: Synthetic Dividend Research Team
**Created**: October 29, 2025
**Reading Time**: 20 minutes
**Related**: 01-core-concepts.md, 03-mathematical-framework.md, 04-income-generation.md

---

## Executive Summary

The Synthetic Dividend Algorithm comes in four variants, each providing different risk/reward profiles through strategic buyback and selling mechanisms:

| Variant | Buybacks | Sell Triggers | Risk Profile | Best For |
|---------|----------|---------------|--------------|----------|
| Buy-and-Hold | ❌ | Never | Lowest | Traditional investors |
| ATH-Only | ❌ | New ATHs only | Low | Conservative profit-taking |
| Standard SD | ✅ | ATHs + brackets | Medium | Balanced growth + income |
| **ATH-Sell** | ✅ | New ATHs only | Medium-High | Maximum compounding |

**Key Innovation**: The ATH-Sell variant (new) combines aggressive dip-buying with conservative ATH-only selling for maximum long-term compounding during recovery periods.

---

## Part 1: Buy-and-Hold (Baseline)

### 1.1 Mechanism

**Strategy**: Traditional buy-and-hold investing.
- **No rebalancing**: Hold shares indefinitely
- **No profit-taking**: Never sell shares
- **No buybacks**: Never add to position

**Cash Flow**: Zero synthetic dividends.

### 1.2 Characteristics

**Returns**: Pure market returns (price appreciation + dividends if any).

**Risk**: Full market exposure with no volatility harvesting.

**Use Case**: Traditional investors who want pure market returns without algorithmic intervention.

### 1.3 Example

```
Initial: $10,000 → 100 shares @ $100
Year 1: Price → $120 (+20%)
Year 2: Price → $110 (-8.3%)
Year 3: Price → $140 (+27%)

Final: 100 shares worth $14,000 (+40% total return)
```

**Strength**: Simple, no trading costs, pure market exposure.
**Weakness**: No income generation, full volatility exposure.

---

## Part 2: ATH-Only (Conservative Profit-Taking)

### 2.1 Mechanism

**Strategy**: Profit-taking at all-time highs only.
- **Primary**: Sell small portions when price exceeds previous all-time high
- **No buybacks**: Never repurchase sold shares
- **Path-independent**: Final result depends only on ending price, not the path

**Cash Flow**: Predictable total cash, unpredictable timing.

### 2.2 Characteristics

**Returns**: Market returns + profit-taking at peaks.

**Risk**: Reduced market exposure as shares are sold over time.

**Mathematical Guarantee**: If price quadruples, you get double your money + bank equals initial investment.

### 2.3 Example

```
Initial: $10,000 → 100 shares @ $100

Day 1: $100 → $120 (new ATH) → Sell 10 shares @ $120 = +$1,200
Day 30: $120 → $140 (new ATH) → Sell 9 shares @ $140 = +$1,260
Day 60: $140 → $110 (drawdown) → HOLD (no action)
Day 90: $110 → $150 (new ATH) → Sell 8 shares @ $150 = +$1,200

Final: 73 shares worth $10,950 + $3,660 cash = $14,610 (+46%)
```

**Strength**: Path-independent, guaranteed minimum returns, simple.
**Weakness**: Misses volatility harvesting opportunities, reduced compounding.

---

## Part 3: Standard SD (Balanced Volatility Harvesting)

### 3.1 Mechanism

**Strategy**: ATH profit-taking + systematic buybacks during dips.
- **Primary**: Sell at all-time highs (same as ATH-only)
- **Secondary**: Buy back shares during drawdowns using rebalancing brackets
- **Repetition**: Each volatility cycle creates buy/sell opportunities
- **Profit sharing**: Configurable extraction vs. reinvestment ratio

**Cash Flow**: Higher total cash through repeated cycles, more frequent but still irregular.

### 3.2 Characteristics

**Returns**: Market returns + volatility alpha from harvesting price swings.

**Risk**: Medium - maintains market exposure while generating income.

**Volatility Alpha**: Typically 5-40% excess returns depending on asset volatility.

### 3.3 Example (SD8 = 9.05% trigger, 50% profit sharing)

```
Initial: $10,000 → 331 shares @ $30.12

Jan: $30.12 → $32.85 (new ATH) → Sell 17 shares @ $32.85 = +$558
Mar: $32.85 → $29.80 (-9.3%) → Buy 17 shares @ $29.80 = -$506
Jun: $29.80 → $34.20 (new ATH) → Sell 18 shares @ $34.20 = +$616
Sep: $34.20 → $31.00 (-9.4%) → Buy 18 shares @ $31.00 = -$558
Dec: $31.00 → $35.50 (new ATH) → Sell 19 shares @ $35.50 = +$675

Final: 312 shares worth $11,092 + $785 cash = $11,877 (+19% vs buy-and-hold +40%)
Volatility Alpha: +21% excess return
```

**Strength**: Balanced growth + income, measurable excess returns.
**Weakness**: More complex, path-dependent results.

---

## Part 4: ATH-Sell (Maximum Compounding) ⭐ NEW

### 4.1 Mechanism

**Strategy**: Aggressive dip-buying with conservative ATH-only selling.
- **Primary**: Buy back shares aggressively during any drawdown (same as Standard SD)
- **Secondary**: Only sell bought-back shares when price reaches new all-time highs
- **Maximum hold**: Bought shares compound until absolute peaks
- **Recovery optimization**: Designed for maximum gains during recovery periods

**Cash Flow**: Lower frequency but higher quality - sells only represent pure gains from recovery.

### 4.2 Characteristics

**Returns**: Highest potential among variants through extended compounding periods.

**Risk**: Medium-high - holds through volatility but only realizes gains at peaks.

**Volatility Alpha**: Variable - lower during high volatility, higher during recoveries.

**Key Innovation**: Separates buying (aggressive during dips) from selling (conservative at peaks).

### 4.3 Example (NVDA 2022 bear market)

```
Initial: $10,000 → 331 shares @ $30.12

Jan-Jun: NVDA drops 50% to $15.06
- Multiple buybacks during decline, accumulating 207 shares
- Bank balance decreases as shares purchased

Oct-Dec: NVDA recovers to $30.47 (new ATH)
- Sell ALL 207 bought shares at $30.47 = +$6,308 profit
- Only original shares remain + massive profit extraction

Final: 331 shares worth $10,070 + $3,769 cash = $13,839 (+38%)
Buybacks: 12 (vs 65 for Standard SD)
Sell events: 0 until ATH recovery
Volatility Alpha: +4.5% (vs +26% for Standard SD)
```

**Strength**: Maximum compounding during recoveries, pure profit realization.
**Weakness**: Lower income frequency, higher risk during extended drawdowns.

### 4.4 When ATH-Sell Excels

**Ideal conditions**:
- **Recovery markets**: Post-crash rallies where holding through volatility pays off
- **Long-term horizons**: Time to wait for ATH recoveries
- **High-conviction assets**: Where you believe in eventual new highs

**Performance vs Standard SD**:
- **During drawdowns**: ATH-Sell buys more aggressively (lower prices)
- **During recoveries**: ATH-Sell holds longer (more compounding)
- **At peaks**: ATH-Sell sells larger positions (bigger gains)

---

## Part 5: Comparative Analysis

### 5.1 Risk-Return Profiles

```
Buy-and-Hold: ■■■□□□□□□□ (Low risk, low income)
ATH-Only:     ■■■■□□□□□□ (Low risk, moderate income)
Standard SD:  ■■■■■■■□□□ (Medium risk, high income)
ATH-Sell:     ■■■■■■■■□□ (Higher risk, highest income potential)
```

### 5.2 Cash Flow Characteristics

| Variant | Frequency | Predictability | Total Amount | Path Dependence |
|---------|-----------|----------------|--------------|-----------------|
| Buy-and-Hold | Never | N/A | $0 | No |
| ATH-Only | Irregular | Low | Moderate | No |
| Standard SD | Frequent | Medium | High | Yes |
| ATH-Sell | Rare | High | Highest | Yes |

### 5.3 Use Case Recommendations

**Conservative investors**: Start with ATH-Only
**Income-focused retirees**: Use Standard SD
**Growth-oriented long-term**: Consider ATH-Sell
**Traditional portfolios**: Stick with Buy-and-Hold

---

## Part 6: Implementation Details

### 6.1 Algorithm Parameters

**Rebalance Size (sdN)**: Controls bracket spacing
- SD4: 18.92% (aggressive rebalancing)
- SD6: 12.25% (moderate)
- SD8: 9.05% (standard)
- SD10: 7.18% (conservative)

**Profit Sharing**: Controls income vs growth
- 0%: Pure growth (buy-and-hold behavior)
- 50%: Balanced
- 100%+: Income generation

### 6.2 Factory Naming Convention

```
sd-9.05,50           # Standard SD: 9.05% trigger, 50% profit sharing
sd-ath-only-9.05,50  # ATH-Only variant
sd-ath-sell-9.05,50  # ATH-Sell variant (new)
```

### 6.3 Backtesting Considerations

**All variants support**:
- Price normalization
- Withdrawal policies
- Risk-free rate calculations
- Multi-asset portfolios

**Variant-specific features**:
- ATH-Only: Path-independent validation
- Standard SD: Buyback stack tracking
- ATH-Sell: ATH recovery monitoring

---

## Key Takeaways

1. **Four distinct approaches**: Each variant serves different investor needs
2. **ATH-Sell innovation**: Separates aggressive buying from conservative selling
3. **Risk-reward spectrum**: Higher returns come with increased complexity
4. **No single "best"**: Choice depends on goals, risk tolerance, time horizon
5. **Measurable trade-offs**: Each variant has quantifiable advantages and costs

**Next**: Read `03-mathematical-framework.md` to understand why these algorithms generate excess returns.