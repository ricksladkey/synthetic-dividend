# Gap Bonus Theory Reassessment

## Executive Summary

The multi-bracket gap fix reveals that **gap bonus amplifies volatility alpha far beyond theoretical minimum**, fundamentally changing the relationship between volatility and optimal rebalance triggers. This requires reassessing the entire sd_n optimization framework.

## Key Findings

### 1. Gap Bonus Multipliers are Extreme

**Transaction count multipliers (actual vs theoretical):**

| Asset | sd_n | Theoretical Txns | Actual Txns | Multiplier |
|-------|------|-----------------|-------------|------------|
| MSTR  | sd12 | 12 | **2,815** | **234.6x** |
| MSTR  | sd10 | 10 | **1,908** | **190.8x** |
| MSTR  | sd8  | 8  | **979**   | **122.4x** |
| ETH-USD | sd10 | 10 | **1,004** | **100.4x** |
| BTC-USD | sd10 | 10 | **555**   | **55.5x** |
| NVDA  | sd12 | 12 | **453**   | **37.8x** |
| NVDA  | sd8  | 8  | **76**    | **9.5x** |

**Low-volatility assets:** ~1-3x multiplier (SPY, GLD, DIA)

### 2. Strong Correlation: Transactions → Alpha

**Correlation coefficient: 0.689**

Transaction count is a strong predictor of volatility alpha, which makes sense:
- More transactions = more gap events captured
- Gap events = free profit (buying dips, selling spikes within same day)
- Gap bonus scales with both frequency AND magnitude of gaps

### 3. Volatility Amplification Factor

**High vs Low Volatility Assets:**
- High volatility avg: **703 transactions**
- Low volatility avg: **8 transactions**  
- **Amplification: 86x**

This is WILDLY higher than the algorithm was originally designed for.

## Theory vs Practice Divergence

### Original Theoretical Framework (PRE-FIX)

The algorithm was validated assuming **gradual price movements only**:

1. **sd4** (18.92% brackets): Expect ~4 transactions to double
2. **sd8** (9.05% brackets): Expect ~8 transactions to double
3. **sd12** (5.95% brackets): Expect ~12 transactions to double

**Assumption:** Price moves smoothly from bracket to bracket, one per trading period.

### Actual Behavior (POST-FIX)

With gap bonus correctly implemented, we see:

**MSTR:** 
- sd12 generates **234.6x** more transactions than theory
- Why? Frequent intraday volatility + overnight gaps spanning multiple brackets
- Each gap can trigger 3-5+ transactions in ONE day

**Consequence:** The guaranteed minimum alpha (from gradual moves) is just the **baseline**. The gap bonus is the **real profit driver** for volatile assets.

## Implications for sd_n Optimization

### Old Framework (WRONG)

"Tighter triggers (higher sd_n) are better for volatile assets because they capture more volatility cycles."

**Problem:** This was validated with the BUGGY algorithm that only processed 1 transaction per day.

### New Framework (CORRECT)

"Tighter triggers (higher sd_n) are DRAMATICALLY better for volatile assets because they capture exponentially more gap events."

**Why the exponential difference?**

1. **More gap events detected:** sd12 (5.95% brackets) detects 2x more gaps than sd6 (12.25% brackets)
2. **More transactions PER gap:** A 20% overnight gap triggers:
   - sd6: 1-2 transactions
   - sd12: 3-4 transactions
3. **Multiplicative effect:** 2x gap frequency × 2x txns/gap = **4x total transactions**

**Actual data confirms this:** MSTR sd12 has **8.3x** more transactions than MSTR sd6 (2,815 vs 338).

## Critical Questions for Reassessment

### 1. Is the optimal sd_n different now?

**Old validation:** sd8 (9.05%) was optimal for most assets

**New hypothesis:** Tighter triggers (sd10, sd12, sd16) may be optimal for volatile assets due to gap bonus amplification.

**Evidence from current data:**
- MSTR optimal: **sd10** (95.72% alpha, 1,908 txns)
- Note: sd12 has MORE txns (2,815) but LOWER alpha (79.38%)
- This suggests there's a sweet spot where transaction overhead exceeds gap bonus

### 2. What's the gap frequency by asset class?

Need to measure:
- **Gap frequency:** % of days with >1 bracket movement
- **Gap magnitude:** Average bracket levels crossed per gap
- **Gap distribution:** Overnight vs intraday gaps

This will inform sd_n selection by asset characteristics, not just historical volatility.

### 3. How does profit sharing interact with gap bonus?

Current data uses 50% profit sharing. Questions:
- Does gap bonus favor higher profit sharing (sell more aggressively)?
- Or lower profit sharing (hold through gaps for larger eventual gains)?
- Does the answer depend on gap direction bias (up vs down)?

### 4. What's the theoretical maximum gap bonus?

For extremely volatile assets (MSTR, crypto):
- What's the ceiling on transaction count growth?
- Is there a point where the stack gets too deep to benefit from gaps?
- Do transaction costs (ignored in current model) eventually dominate?

### 5. Does gap bonus change the volatility threshold?

**Old framework:** "Algorithm only works on assets with sufficient volatility"

**New framework:** "Algorithm EXCELS on assets with frequent gaps, regardless of base volatility"

Example: An asset with 10% annual volatility but frequent small gaps might outperform an asset with 30% volatility but smooth trends.

## Recommended Research Priorities

### Immediate (validate gap bonus mechanism)

1. **Measure gap frequency and magnitude:**
   - Parse price data to identify gaps (high/low ranges not overlapping day-to-day)
   - Calculate gap distribution by asset class
   - Correlate gap metrics with observed transaction counts

2. **Verify gap bonus formula:**
   - For a known gap size (e.g., 20% with sd8), verify we get 2 transactions
   - Test edge cases: gaps exactly on bracket boundaries
   - Confirm iteration counter in transaction notes matches expectations

3. **Profit sharing sensitivity:**
   - Re-run optimal_rebalancing with profit_pct = [25, 50, 75, 100]
   - Check if gap bonus changes optimal profit sharing for volatile assets

### Medium-term (optimize sd_n framework)

4. **Gap-adjusted sd_n recommendations:**
   - Develop formula: `optimal_sd_n = f(base_volatility, gap_frequency, gap_magnitude)`
   - Test on historical data: does this predict observed alpha better than volatility alone?
   - Create lookup table by asset characteristics

5. **Transaction cost modeling:**
   - Add realistic transaction costs (commission + slippage)
   - Find optimal sd_n where gap bonus exceeds transaction costs
   - This may reduce extreme cases (MSTR sd12: 2,815 txns)

6. **Backtest longer periods:**
   - Current data: 1 year (2023-10-23 to 2024-10-23)
   - Test: 3 years, 5 years, full history
   - Verify gap bonus is consistent, not a 1-year anomaly

### Long-term (theoretical framework)

7. **Gap bonus mathematics:**
   - Derive closed-form formula for expected gap bonus
   - Input: gap frequency distribution + sd_n
   - Output: expected transaction count multiplier
   - This becomes the new theoretical foundation

8. **Asset classification system:**
   - Category 1: Smooth (SPY, GLD) - minimal gap bonus
   - Category 2: Choppy (NVDA, PLTR) - moderate gap bonus
   - Category 3: Explosive (MSTR, BTC) - extreme gap bonus
   - Different sd_n recommendations for each category

## Conclusion

**The gap bonus is not a minor correction - it's a regime change.**

For MSTR, the gap bonus amplifies transactions by **234x theoretical**. This means:

1. Our original sd_n optimization was based on INCOMPLETE algorithm behavior
2. The "guaranteed minimum" volatility alpha is tiny compared to gap bonus
3. Volatile assets are VASTLY more profitable than we thought
4. We need a completely new framework for sd_n selection

**Bottom line:** The algorithm in practice is "wildly more successful" than theory predicted because theory assumed gradual moves only. Gap bonus is the dominant profit source for volatile assets, not the base volatility alpha.

**Next step:** Systematically measure gap frequency/magnitude across all assets and derive gap-adjusted sd_n optimization formula.

---

## Multi-Bracket Gap FIFO Symmetry (Implementation Detail)

### The Challenge

When a price gaps down 2+ brackets in a single day, we face a design choice:

**Option A: Single Combined Transaction**
- Record: Buy 201 shares at gap opening price ($80)
- Problem: Breaks FIFO symmetry when unwinding
- Example: If we later gap up 2 brackets, we'd sell at 2 different prices but have only 1 stack entry

**Option B: Separate Transactions Per Bracket** ✅ (Our Implementation)
- Record: Buy 100 shares @ $91.62, then buy 101 shares @ $83.94
- Advantage: Perfect FIFO symmetry when unwinding
- Example: Later gap up unwinds stack entries one-at-a-time at matching bracket prices

### Implementation: Iterative Gap Handling

The algorithm handles multi-bracket gaps through **iteration**:

1. **Iteration 1**: Buy order at $91.62 triggers (price hit $78)
   - Fill at theoretical bracket price: $91.62
   - Add stack entry: `($91.62, 100 shares)`
   - Place new orders based on $91.62

2. **Iteration 2**: New buy order at $83.94 triggers (price still at $78)
   - Fill at theoretical bracket price: $83.94
   - Add stack entry: `($83.94, 101 shares)`
   - Place new orders based on $83.94

3. **Iteration 3**: New buy order at $76.91 doesn't trigger (price=$78 > $76.91)
   - Stop iterating

**Result**: Two separate "normal-sized" stack entries, each indistinguishable for selling purposes.

### Why This Matters for Symmetry

When we later gap UP 2 brackets:

1. **FIFO unwind #1**: Sell at $91.62 → matches first stack entry perfectly
2. **FIFO unwind #2**: Sell at $100.00 → matches second stack entry perfectly

Each bracket crossing (up or down) creates/unwinds exactly **one stack entry** at the **theoretical bracket price**.

This ensures:
- ✅ Buy-back stack unwinding is **exactly symmetrical**
- ✅ No accumulation of "odd lots" from gap slippage
- ✅ Clean FIFO accounting even across multi-bracket gaps

### Technical Note

This required changing `Order.get_execution_price()` to **always fill limit orders at their limit price** (not at gap opening price). The iteration logic then naturally handles multi-bracket gaps by creating separate transactions.

**Trade-off**: We model theoretical fills at bracket prices rather than realistic gap slippage. This is acceptable because:
1. The symmetry benefits outweigh the minor inaccuracy
2. In practice, limit orders often fill near their limit during volatile gaps
3. The alternative (slippage model) breaks FIFO symmetry permanently


