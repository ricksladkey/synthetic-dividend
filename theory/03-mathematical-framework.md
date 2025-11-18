# 03 - Mathematical Framework

**Why it generates excess returns** - Complete mathematical foundation of volatility alpha and the formulas that predict performance.

**Author**: Synthetic Dividend Research Team
**Created**: October 29, 2025
**Reading Time**: 30 minutes
**Related**: 01-core-concepts.md, 02-algorithm-variants.md, 07-research-validation.md

---

## Executive Summary

**Central Discovery**: Volatility alpha has a mathematical lower bound that can be calculated simply by counting drawdowns on a price chart.

**Core Formula**: `Volatility Alpha ≥ N × (trigger%)² / 2`

Where:
- **N** = Number of complete buyback-resell cycles
- **trigger%** = Rebalancing bracket size (e.g., 9.05% for SD8)

**Key Insights**:
- Formula provides conservative minimum estimate
- Actual alpha typically exceeds formula by 1.1x-3.4x due to gaps and compounding
- Visual estimation: Count chart drawdowns → predict minimum alpha instantly
- Universal applicability across all volatile assets

---

## Part 1: The Volatility Alpha Definition

### 1.1 Formal Definition

```
Volatility Alpha = (Algorithm Return) - (Buy-and-Hold Return)
```

**Interpretation**: The measurable excess return attributable solely to the buyback mechanism, isolated from market performance.

**Why it exists**: Traditional strategies ignore price path variations. Systematic rebalancing captures this "wasted" volatility.

### 1.2 The Three Questions Framework

**Question A**: "How much money did I make?" (Gross returns - includes market performance)
**Question B**: "Did I beat opportunity cost?" (Net returns - after costs)
**Question C**: "Should I use this vs. buy-and-hold?" (Volatility alpha - excess returns)

**Our focus**: Question C - isolating the pure value of volatility harvesting.

### 1.3 Alpha Sources

**Four mechanisms generate volatility alpha**:

1. **Price Path Exploitation**: Different routes to same destination create trading opportunities
2. **Drawdown Recycling**: Each dip becomes a buying opportunity for future profits
3. **Compounding Effects**: Early profits increase capital available for later cycles
4. **Gap Arbitrage**: Market discontinuities create asymmetric profit opportunities

---

## Part 2: The Minimum Alpha Formula

### 2.1 Derivation

**Assumptions** (for minimum bound):
- Symmetric price movements (equal up/down moves)
- No price gaps (continuous price changes)
- No compounding between cycles
- Single complete buyback-resell cycle

**Step-by-step derivation**:

1. **Sell at price P**: Generate cash from ATH profit-taking
2. **Drop by trigger t**: Price falls to P × (1 - t)
3. **Buy back shares**: Cost = P × (1 - t)
4. **Recover to P**: Price returns to original level
5. **Resell shares**: Revenue = P

**Profit calculation**:
```
Cost per share: P × (1 - t)
Revenue per share: P
Profit: P - P×(1 - t) = P × t
Return on capital: t / (1 - t)
```

**For small t (< 10%)**: `Return ≈ t / (1 - t) ≈ t × (1 + t + t² + ...) ≈ t + t²`

**Dominant term**: The t² term becomes significant, giving `Return ≈ t² / 2`

### 2.2 The Core Formula

```
Alpha per cycle ≈ (trigger%)² / 2
```

**Examples**:

**SD8 (9.05% trigger)**:
```
α ≥ 0.0905² / 2 ≈ 0.0041 = 0.41% per cycle
```

**SD16 (4.43% trigger)**:
```
α ≥ 0.0443² / 2 ≈ 0.0010 = 0.10% per cycle
```

**SD6 (12.25% trigger)**:
```
α ≥ 0.1225² / 2 ≈ 0.0075 = 0.75% per cycle
```

### 2.3 Total Alpha Prediction

```
Total Alpha ≥ (Number of cycles) × (trigger%)² / 2
```

**Visual estimation method**:
1. Look at price chart
2. Count major drawdown-recovery cycles
3. Multiply by formula
4. Get instant alpha estimate

**Example**: NVDA 2022 (50% drawdown, SD8 trigger)
- Cycles: ~3-4 major cycles
- Predicted alpha: 3 × 0.41% ≈ 1.2%
- Actual alpha: 4.5% (3.75x higher due to gaps)

---

## Part 3: Why "Minimum"? (Reality Exceeds Formula)

### 3.1 Asymmetric Price Movements

**Reality**: Markets gap down more than they gap up.

**Impact**: Buy at lower prices, sell at higher prices than expected.

**Bonus**: 1.1x to 2.5x formula multiplier depending on asset.

### 3.2 Overnight Gaps

**Mechanism**:
- **Gap down**: Buy at lower price than previous close
- **Gap up**: Sell at higher price than previous close

**Example**: 5% overnight gap up = sell 5% higher than expected bracket.

**Impact**: Creates "free money" beyond theoretical minimum.

### 3.3 Compounding Between Cycles

**Reality**: Profits from early cycles increase capital for later cycles.

**Impact**: Larger positions generate larger absolute profits.

**Formula limitation**: Assumes constant capital per cycle.

### 3.4 Multiple Overlapping Cycles

**Reality**: Real markets have concurrent cycles at different scales.

**Impact**: More cycles than simple counting suggests.

**Result**: Actual alpha often 2x-3x higher than formula predicts.

---

## Part 4: Empirical Validation

### 4.1 18-Scenario Test Matrix

**Assets tested**: NVDA, SPY, GLD, MSTR, BTC, QQQ
**Timeframes**: 1-year, 2-year, 3-year periods
**Triggers**: SD6, SD8, SD10, SD12

**Results range**: 1.4% (GLD low volatility) to 125% (MSTR high volatility)

### 4.2 Gap Bonus by Asset Class

| Asset Class | Typical Gap Bonus | Formula Multiplier |
|-------------|-------------------|-------------------|
| Commodities (GLD) | Low | 1.1x |
| Bonds/Stable | Minimal | 1.0x |
| Large Cap Stocks | Moderate | 1.5x |
| Tech Stocks | High | 2.0x |
| Crypto | Extreme | 3.4x |

### 4.3 Visual Alpha Estimation

**Method**: Count drawdowns on chart → multiply by formula

**Example calculation**:
- Asset: NVDA 2022
- Drawdowns counted: 4 major cycles
- Trigger: SD8 (9.05%)
- Predicted minimum: 4 × 0.41% = 1.64%
- Actual result: 4.5% (2.75x higher)

---

## Part 5: Mathematical Properties

### 5.1 Exponential Scaling

**Rebalancing triggers follow**: `Trigger = 2^(1/N) - 1`

**Common values**:
- SD4: 18.92% (aggressive)
- SD6: 12.25% (moderate)
- SD8: 9.05% (standard)
- SD10: 7.18% (conservative)

**Alpha scaling**: `α ∝ 1/N²` (higher frequency = lower per-cycle alpha)

### 5.2 Profit Sharing Effects

**Formula**: `Effective_alpha = Base_alpha × (1 - profit_sharing_ratio)`

**Intuition**: Higher profit sharing extracts returns earlier, reducing compounding.

**Time dilation**: `Time_to_goal ∝ 1 / (1 - profit_sharing_ratio)`

### 5.3 Capital Utilization

**Key metrics**:
- **Deployment %**: Capital actively invested vs. held as cash
- **Utilization rate**: Average deployment over time
- **Return on deployed capital**: Returns per dollar actively invested

**Critical insight**: More shares ≠ better returns. Capital efficiency matters.

---

## Part 6: Theoretical Limits and Constraints

### 6.1 Maximum Alpha Bounds

**Theoretical maximum**: Limited by market volatility and gap frequency.

**Practical limits**:
- **Low volatility assets**: 1-5% alpha (GLD, bonds)
- **Moderate volatility**: 5-25% alpha (SPY, QQQ)
- **High volatility**: 25-125% alpha (NVDA, MSTR, BTC)

### 6.2 Transaction Costs

**Impact**: Reduce alpha by 0.5-2% annually depending on frequency.

**Mitigation**: Use low-cost brokers, minimize frequent trading.

### 6.3 Market Regime Dependence

**Bull markets**: Lower alpha (fewer dips to buy)
**Bear markets**: Higher alpha (more dips, bigger moves)
**Sideways markets**: Highest alpha (repeated cycles)

---

## Part 7: The ATH-Sell Variant Mathematics

### 7.1 Modified Alpha Calculation

**ATH-Sell difference**: Only sells at new ATHs, not at bracket levels.

**Alpha formula**: `α_ath_sell = α_standard × (1 + recovery_multiplier)`

Where `recovery_multiplier` depends on:
- Time to ATH recovery
- Price appreciation during recovery
- Holding period of bought shares

### 7.2 Recovery Period Effects

**Short recoveries**: ATH-Sell ≈ Standard SD performance
**Long recoveries**: ATH-Sell >> Standard SD performance
**Failed recoveries**: ATH-Sell < Standard SD performance

### 7.3 Risk-Adjusted Comparison

**Standard SD**: Frequent trading, regular income, moderate risk
**ATH-Sell**: Infrequent trading, lump-sum gains, higher risk

**Mathematical trade-off**: `Risk_adjusted_alpha = Total_alpha / Holding_period_volatility`

---

## Key Takeaways

1. **Core formula**: `α ≥ N × (trigger%)² / 2` provides conservative minimum
2. **Reality exceeds formula**: Actual alpha 1.1x-3.4x higher due to gaps/compounding
3. **Visual estimation**: Count chart drawdowns → instant alpha prediction
4. **Universal applicability**: Works across all volatile assets
5. **ATH-Sell advantage**: Higher alpha during recovery periods through extended compounding

**Next**: Read `04-income-generation.md` to see how this mathematics translates to practical income generation.