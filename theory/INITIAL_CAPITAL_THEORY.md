# Initial Capital and Opportunity Cost Theory

## The Core Question

When backtesting, what opportunity cost should we measure against the initial capital?

---

## Current Implementation

**What we track**:
```python
# Starting state
holdings = 100 shares × $100 = $10,000 deployed
bank = $0 # Starts at zero

# We measure opportunity cost on:
# - Bank balance (when negative = borrowed capital)
# - Nothing else (initial deployment ignored)
```

**Problem**: We bought $10K of stock but don't measure the opportunity cost of that initial purchase.

---

## The Conceptual Inconsistency

### Current Model (Incomplete)

**Day 1**: Buy 100 shares @ $100 = $10,000 deployed
- No opportunity cost tracked (it's the "starting state")

**Day 100**: Bank = -$5,000 (borrowed for buybacks)
- Opportunity cost accrues on the $5K (could have been in VOO)

**Inconsistency**: Why measure opportunity cost on $5K borrowed but not $10K initially deployed?

### Corrected Model

**Reality**: ALL capital has opportunity cost from day 1.

When you deploy $10K into NVDA:
- You could have deployed it into VOO instead
- Every day NVDA ≠ VOO, you have opportunity cost/gain
- This is the **relative performance** we should measure

**Formula**:
```python
total_opportunity_cost = sum(
 (stock_return[day] - VOO_return[day]) × deployed_capital[day]
)
```

This measures: "Did I beat VOO, and by how much?"

---

## Theoretical Implications

### 1. True Break-Even

**Current**: Strategy "breaks even" when final value = initial capital
**Corrected**: Strategy breaks even when final value = (initial capital × VOO growth)

If VOO doubled during backtest, you need to double your money just to break even!

### 2. Volatility Alpha Interpretation

**Volatility alpha** = excess return beyond asset's buy-and-hold
**Initial capital opportunity cost** = asset's return vs reference (VOO)

These are **separate dimensions**:
- Alpha: SD8 vs buy-and-hold NVDA
- Opportunity cost: NVDA vs VOO

### 3. Return Metrics

**Current** (asset-only):
```python
return = (final_value - initial_value) / initial_value
```

**Enhanced** (vs reference):
```python
asset_return = (final_value - initial) / initial
voo_return = (voo_final - voo_initial) / voo_initial
relative_return = asset_return - voo_return
```

---

## The "Skin in the Game" Question

**Scenario**: Investor has $100K cash

**Option A**: Deploy $10K into NVDA (SD8 strategy)
**Option B**: Deploy $100K into NVDA (SD8 strategy)

**Question**: Should option B show 10x the opportunity cost?

**Answer**: YES! Option B has 10x more capital at risk.

**Current limitation**: Our backtest starts with "100 shares" but doesn't know if that's $100K or $10M depending on when you started.

---

## Worked Example: NVDA 2020-2024

**Setup**:
- Buy 100 shares @ $120 = $12,000 initial
- VOO: $320 → $480 (50% gain)
- NVDA: $120 → $140 (17% gain)

**Current reporting**:
```
Final value: $14,000
Return: 17% (looks good!)
```

**Missing**:
```
VOO would have grown to: $18,000 (50%)
Opportunity cost: -$4,000
True performance: 17% - 50% = -33% relative
```

**Key insight**: NVDA grew 17% but **underperformed VOO by 33%**. Current metrics hide this.

---

## Implementation Approach

**Option A**: Track from day 1
```python
# Day 1: Initial purchase
opportunity_cost = initial_capital × (voo_daily_return - 0)
# Day 2+: Ongoing tracking
opportunity_cost += deployed_capital × (voo_return - asset_return)
```

**Option B**: Post-calculation adjustment
```python
# Run backtest as-is
final_value = backtest_result

# Calculate what VOO would have done
voo_final = initial_capital × (1 + voo_total_return)

# Report relative performance
relative_performance = final_value - voo_final
```

**Recommendation**: Option B (simpler, same result)

---

## Practical Implications

**For strategy comparison**: Opportunity cost matters less (all strategies start with same capital in same asset)

**For absolute performance**: Opportunity cost is critical (did you beat the index?)

**For multi-asset portfolios**: Each asset has its own opportunity cost vs reference

---

**Status**: Conceptual framework documented, implementation pending

**See Also**:
- [01-core-concepts.md](01-core-concepts.md) - Foundational principles
- [RETURN_ADJUSTMENT_FRAMEWORK.md](RETURN_ADJUSTMENT_FRAMEWORK.md) - Return metrics framework
