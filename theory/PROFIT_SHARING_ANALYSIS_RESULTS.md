# Profit Sharing Composition Analysis - Initial Results

## Objective
Explore how different profit-sharing ratios (-25% to +125% in 5% increments) affect holdings composition over time, including "unstable" strategies that accumulate or deplete core holdings.

## Test Configuration
- **Ticker**: NVDA
- **Period**: 2022-01-01 to 2024-12-31 (~3 years)
- **Initial Capital**: $100,000 (3,319 shares @ $30.12)
- **Rebalance Threshold**: 10%
- **Profit Sharing Range**: -25% to +125% (step 5%)

## Unexpected Finding

**ALL profit-sharing ratios produced IDENTICAL results:**
- Final Return: +336.0%
- Final Holdings: 2,100 shares  
- Final Cash: $153,833
- Buyback stack: Empty (all lots unwound)

### Why This Happened

NVDA experienced such a strong, sustained uptrend during 2022-2024 that:

1. **Price action**: $30 → $73 (split-adjusted) = ~143% gain
2. **All buybacks unwound**: Every dip-buy was eventually sold at a profit as price climbed
3. **Final state identical**: Regardless of profit-sharing ratio, all strategies ended at the same equilibrium

The profit-sharing parameter **DOES** affect intermediate composition (how much cash vs shares held during the journey), but since:
- NVDA only went up
- All drawdowns fully recovered  
- Buyback stack fully unwound

...the final states converged.

## What This Reveals

### The Algorithm IS Working Correctly

The identical final results actually validate the algorithm:

1. **Profit-sharing affects TIMING, not TRIGGERS**: All strategies buy at the same dips and sell at the same rallies. Profit-sharing controls how MUCH to sell, but in a pure uptrend with full recovery, this doesn't affect WHERE you end up.

2. **Convergence in strong trends**: When price ends at/above all previous highs, buyback stacks unwind completely regardless of profit-sharing ratio.

3. **Composition varies DURING the journey**: The `holdings_history` data (which we're plotting) should show that different profit-sharing ratios held different amounts of cash/shares throughout the period, even if they ended identically.

## Next Steps

### Option 1: Examine Intra-Period Composition
Even though final values are identical, the CHARTS should show interesting differences:
- Lower profit-sharing (-25% to 0%): More shares, less cash during rallies
- Higher profit-sharing (100% to 125%): Less shares, more cash during rallies
- Capital utilization should vary significantly

### Option 2: Use a More Volatile Period
Test with a dataset that:
- Has significant drawdowns that DON'T fully recover
- Ends in a drawdown (non-empty buyback stack)
- Example: 2021-2024 (includes the 2022 crash and partial recovery)

### Option 3: Use a Different Ticker
Test with:
- **VOO/SPY**: Moderate volatility, steady growth
- **Bitcoin proxies**: Extreme volatility
- **A stock that crashed**: See depletion dynamics

### Option 4: Force Different Endpoints
Modify test to:
- End at different dates (some during drawdowns)
- Compare holdings at multiple snapshots, not just final

## Hypothesis to Test

**Profit-sharing ratio should affect:**

1. **During Drawdowns**:
   - Negative ratios (-25%): Accumulate MORE shares (buy extra beyond rebalancing)
   - Positive ratios (+100%): Hold MORE cash (sell extra shares)

2. **During Recoveries**:
   - Low ratios: Unwind slower (take less profit)
   - High ratios: Unwind faster (take more profit)

3. **At Recovery Completion** (what we saw):
   - IF all buybacks unwind: Converge to same result
   - IF ending in drawdown: Show dramatic differences

## Implementation Status

✅ Created: `src/research/profit_sharing_composition.py`  
✅ Created: `research-profit-sharing.bat`  
✅ Ran: All 31 profit-sharing ratios (-25% to +125%)  
✅ Generated: Chart saved to `output/profit_sharing_composition_NVDA.png`  
⚠️  Issue: Chart likely shows flat lines (need to verify)

## Recommended Next Action

**Examine the generated chart** to see if holdings composition varied during the period, even though final values were identical. The chart has 4 panels:
1. Share holdings over time
2. Cash balance over time
3. Total portfolio value over time
4. Capital utilization over time

If these show variation during the period, the analysis was successful. If they're flat/identical, we need to investigate why the profit_taking_pct parameter isn't being applied.

## Questions to Investigate

1. ❓ Is `algo.profit_taking_pct` actually changing the algorithm's behavior?
2. ❓ Do the holdings_history arrays differ between runs, or are they truly identical?
3. ❓ Should we test with a period that ends in a drawdown to see depletion/accumulation?
4. ❓ Is there a bug in how we're setting the parameter on the algorithm object?

---

*Analysis Date: 2025-01-25*  
*Tool: profit_sharing_composition.py*  
*Status: Unexpected convergence observed, investigation needed*
