# Multi-Asset Portfolio Vision

## Current State: Single-Asset Analysis

**What we test**: One asset at a time (NVDA, VOO, BTC)
- Full capital deployed in single stock
- Bank tracks trading cash flow
- Opportunity cost vs single reference (VOO)

**Limitation**: No diversification, unrealistic for real portfolios

---

## Vision: Multi-Asset Portfolio with Shared Cash Pool

### Portfolio Structure

```
Initial: $100,000

Cash Reserve: $10,000 (10%) ← Tactical buyback buffer
Stock Positions: $90,000 (90%) ← Diversified across assets

Example:
- NVDA: $20,000 (20%)
- VOO: $30,000 (30%) ← Index baseline
- GOOG: $15,000 (15%)
- MSFT: $15,000 (15%)
- BTC: $10,000 (10%)
- Cash: $10,000 (10%)
```

### How It Works

**1. Independent Algorithm Execution**
- Each asset runs synthetic dividend independently
- NVDA hits ATH → sells → cash pool increases
- GOOG drops 8% → buyback → cash pool decreases
- VOO sideways → no transactions

**2. Shared Cash Pool**
```
Day 0: Cash = $10,000
Day 5: NVDA sells $2,000 → Cash = $12,000
Day 8: GOOG buys $1,500 → Cash = $10,500
Day 12: MSFT sells $3,000 → Cash = $13,500
Day 15: BTC buys $4,000 → Cash = $9,500
```

**3. Portfolio Rebalancing Triggers**
- Cash < 5%: Reduce buyback aggressiveness
- Cash > 20%: Deploy to new positions
- Position drift > 40%: Consider profit-taking

**4. Opportunity Cost Model**
- **Cash reserve** ($10K): No opportunity cost (tactical buffer)
- **Stock positions** ($90K): Each measured vs VOO
- **Trading cash flow**: Measured when deviating from 10% target

---

## Key Advantages

**Risk Management**: Diversification + cash buffer prevents forced selling

**Opportunity Harvesting**: Different assets peak at different times → steady cash flow

**Realistic Modeling**: Tests portfolio-level behavior, not isolated stocks

**Capital Efficiency**: Measure trade-off between cash drag vs buyback enablement

---

## Implementation Phases

**Phase 2A**: Multi-asset backtest engine
- Shared cash pool management
- Cross-asset transaction tracking
- Portfolio-level metrics

**Phase 2B**: Portfolio analytics
- Correlation analysis
- Cash flow timing
- Optimal cash reserve percentage

**Phase 2C**: Optimization
- Optimal asset mix
- Dynamic allocation
- Risk-adjusted return maximization

---

## Research Questions

1. **Optimal cash reserve**: 5%? 10%? 20%?
2. **Asset correlation effects**: Do uncorrelated assets smooth income?
3. **Deployment efficiency**: Trade-off between cash drag and buyback enablement
4. **Rebalancing triggers**: When to adjust allocations?

---

**Status**: Phase 1 complete (single-asset). Phase 2 planned.

**See Also**:
- [01-core-concepts.md](01-core-concepts.md) - Foundational principles
- [INCOME_GENERATION.md](INCOME_GENERATION.md) - Portfolio-level smoothing discussion
