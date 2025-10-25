# Initial Capital Theory: The Missing Opportunity Cost

## Current Implementation Details

### What We Track Now (src/models/backtest.py)

**Initialization (lines 636-649):**
```python
# Initialize portfolio state
holdings: int = int(initial_qty)  # e.g., 1000 shares
bank: float = 0.0  # ← Starts at ZERO, not negative!

# Record initial purchase
start_value = holdings * start_price  # e.g., $100,000
transactions.append(
    f"{first_idx.isoformat()} BUY {holdings} {ticker} @ {start_price:.2f} = {start_value:.2f}"
)
```

**Opportunity Cost Calculation (lines 794-808):**
```python
opportunity_cost_total = 0.0

for d, bank_balance in bank_history:
    if bank_balance < 0:
        # Negative balance: opportunity cost of borrowed money
        daily_return = reference_returns.get(d, daily_reference_rate_fallback)
        opportunity_cost_total += abs(bank_balance) * daily_return
    elif bank_balance > 0:
        # Positive balance: risk-free interest earned on cash
        daily_return = risk_free_returns.get(d, daily_risk_free_rate_fallback)
        risk_free_gains_total += bank_balance * daily_return
```

**What This Means:**
- ✅ We track opportunity cost when algorithm trading causes negative bank balance
- ✅ We track risk-free gains when algorithm accumulates positive cash
- ❌ We DON'T track opportunity cost on the initial $100k capital
- ❌ Implicitly assumes investor had $100k sitting idle with no opportunity cost

### Example: Current Behavior

**Scenario:** NVDA backtest, $100k initial, bank never goes negative
```
Start: 1000 shares @ $100 = $100,000
End:   1500 shares @ $200 = $300,000
Bank:  $0 (all gains reinvested)

Current Metrics:
- Total Return: 200% = ($300k - $100k) / $100k
- Opportunity Cost: $0 (bank never negative)
- Risk-Free Gains: $0 (bank never positive)

Missing Information:
- What did VOO return over same period? (e.g., 150%)
- Opportunity cost on $100k initial capital: ~$150k
- True net return: 200% - 150% = 50% (this is volatility alpha!)
```

**The $100k Question:** Where did it come from?
- **If borrowed:** We owe interest at market rate (VOO return)
- **If owned:** We gave up earning VOO return on that cash
- **Either way:** There's an opportunity cost we're not tracking!

## The Conceptual Inconsistency

### Current Model
```
Day 0: BUY 1000 shares @ $100 = $100,000
       Bank: $0
       Opportunity Cost: $0

Day 1-N: Track opportunity cost only on negative bank from trading
```

**Problem:** Where did the initial $100,000 come from? It represents borrowed capital with opportunity cost from day 1!

### Corrected Model
```
Day 0: BUY 1000 shares @ $100 = $100,000
       Bank: -$100,000 (borrowed to fund initial position)
       Opportunity Cost: Begins accruing immediately at VOO return rate

Day 1-N: Continue tracking opportunity cost on entire negative balance
```

## Theoretical Implications

### 1. **True Break-Even Calculation**

**Current (Wrong):**
- Algorithm breaks even when: `total_value >= start_value`
- Ignores cost of capital

**Corrected:**
- Algorithm breaks even when: `total_value >= start_value + opportunity_cost_on_initial_capital`
- Must beat the reference return (VOO) to justify the strategy

### 2. **Volatility Alpha Interpretation**

**Current:**
```python
volatility_alpha = total_return - buy_and_hold_return
```

**This is actually correct!** Because:
- Both strategies borrow $100,000 on day 0
- Both pay opportunity cost on that capital
- The alpha is the DIFFERENCE in outcomes
- Opportunity cost cancels out in the subtraction

**But we're not surfacing it correctly in reporting.**

### 3. **Return Metrics Need Adjustment**

**Current `total_return`:**
```
total_return = (end_value - start_value) / start_value
```

**Two interpretations:**

A) **Return on Borrowed Capital** (current):
- "If I borrowed $100k, what % return did I generate?"
- This is what we currently calculate
- Valid for comparing strategies

B) **Net Return After Opportunity Cost** (proposed):
```
net_return = (end_value - start_value - total_opportunity_cost) / start_value
```
- "After paying back my loan at market rates, what % return did I keep?"
- More realistic investor perspective
- Could be negative even if end_value > start_value

## The "Skin in the Game" Question

### Scenario: Investor has $100k cash

**Option 1: Buy VOO**
- Cost: $0 (using own money)
- Return: VOO market return
- Opportunity cost: $0 (baseline)

**Option 2: Buy NVDA with Synthetic Dividend Algorithm**
- Cost: $0 (using own money)  
- Return: Algorithm total return
- Opportunity cost: What VOO would have returned
- **Real gain: total_return - VOO_return** ← This is volatility_alpha!

**Option 3: Buy NVDA with leverage (borrowed $100k)**
- Cost: Interest on $100k loan
- Return: Algorithm total return
- Opportunity cost: Interest payments
- Real gain: total_return - interest_rate

## Worked Example: NVDA 2020-2024

### Scenario Setup
- Initial: 100 shares @ $100 = $10,000
- Period: 2020-01-01 to 2024-12-31
- VOO return over period: +80% (example)
- NVDA buy-and-hold return: +300%
- NVDA with algorithm return: +336%

### Current Reporting (What We Show)
```
Algorithm Total Return: +336%
  Start Value: $10,000
  End Value:   $43,600
  Profit:      $33,600

Buy-and-Hold Return: +300%
  Start Value: $10,000
  End Value:   $40,000
  Profit:      $30,000

Volatility Alpha: +36% (336% - 300%)
Opportunity Cost: $0 (bank never went negative)
```

### What We're Missing
```
Opportunity Cost on Initial $10k:
  VOO gained 80% over period = $8,000
  This is the "cost" of deploying capital in NVDA vs VOO

Net Return After Opportunity Cost:
  Algorithm: +336% gross - 80% opp cost = +256% net
  Buy-Hold:  +300% gross - 80% opp cost = +220% net
  
Alpha (unchanged): +36% (same as before, cancels out!)
```

### Key Insight
The **volatility alpha (+36%)** is correct because:
```
Algorithm net:  (336% - 80%) = 256%
Buy-hold net:   (300% - 80%) = 220%
Difference:      256% - 220% = 36% ✓
```

But we're not showing investors the **full picture**:
- "You made 336%!" (Current)
- "You made 336% gross, paid 80% opportunity cost, kept 256% net" (Better)

### Three Different Backtests, Three Different Stories

**Test 1: Bank Always Zero (All Gains Reinvested)**
```
Current Opportunity Cost: $0
Missing Opportunity Cost: Initial capital only
Should Track: ~$8,000 on $10k over 5 years
```

**Test 2: Bank Goes Negative (Algorithm Borrows)**
```
Current Opportunity Cost: $2,500 (from trading)
Missing Opportunity Cost: Initial capital
Should Track: ~$8,000 + $2,500 = $10,500
```

**Test 3: Bank Goes Positive (Algorithm Accumulates Cash)**
```
Current: Opp Cost $0, Risk-Free Gains $1,200
Missing: Initial capital opp cost
Should Track: Opp Cost $8,000, Risk-Free Gains $1,200
Net Cost: $8,000 - $1,200 = $6,800
```

## Implementation Considerations

### Option A: Start Bank at -start_value (Realistic)
```python
# Initialize portfolio state
holdings: int = int(initial_qty)
bank: float = -1.0 * (holdings * start_price)  # Borrowed to fund position
```

**Pros:**
- Conceptually accurate
- Opportunity cost tracked from day 1
- Clear "pay back the loan" narrative

**Cons:**
- Changes all existing metrics
- Bank will almost always be negative
- May confuse existing tests/reports

### Option B: Track "Virtual Initial Debt" Separately
```python
# Initialize portfolio state
holdings: int = int(initial_qty)
bank: float = 0.0  # Algorithm's trading balance
initial_capital_deployed: float = holdings * start_price  # Separate tracking
```

**Pros:**
- Doesn't break existing code
- Clearer separation: "investor capital" vs "algorithm trades"
- Can add new metric: `total_opportunity_cost` (initial + trading)

**Cons:**
- More complex bookkeeping
- Two sources of opportunity cost to track

### Option C: Post-Calculation Adjustment (Minimal Change)
```python
# At end of backtest
total_opportunity_cost = (
    opportunity_cost_from_trading +  # Current calculation
    opportunity_cost_from_initial_capital  # New calculation
)
```

**Pros:**
- Minimal code changes
- Backward compatible
- Can add as optional "enhanced reporting"

**Cons:**
- Doesn't fix conceptual model
- Harder to track intra-period metrics

## Proposed Metrics Suite

### Primary Metrics (Investor Perspective)
1. **Gross Return**: `(end_value - start_value) / start_value`
   - Raw performance, ignoring opportunity cost
   - Current `total_return` metric

2. **Net Return After Opportunity Cost**: `(end_value - start_value - total_opportunity_cost) / start_value`
   - What you keep after "paying back the loan"
   - Could be negative!

3. **Volatility Alpha** (unchanged): `gross_return - buy_and_hold_return`
   - Relative performance vs baseline
   - Opportunity cost cancels in subtraction

### Supplementary Metrics (Diagnostic)
4. **Total Opportunity Cost**: Cost of capital across entire period
   - Initial capital: Always accruing
   - Trading balance: When bank < 0

5. **Opportunity Cost Ratio**: `total_opportunity_cost / start_value`
   - What % of initial capital was "paid in interest"

6. **Hurdle Return**: `reference_asset_return`
   - The return needed to break even
   - Algorithm must beat this to justify strategy

## Visualization Opportunities

### 1. **Cumulative Opportunity Cost Over Time**
```
$120k ┤     ╭─────────  Total Opportunity Cost
$100k ┤  ╭──╯           (Initial + Trading)
 $80k ┤╭─╯
 $60k ┤╯   ╭───────────  From Initial Capital
 $40k ┤ ╭──╯
 $20k ┤─╯               From Trading (negative bank)
   $0 └─────────────────────────────────────>
      Jan    Apr    Jul    Oct    Jan    Apr
```

### 2. **Net Value After Opportunity Cost**
```
$150k ┤           ╭─────  End Value
$125k ┤       ╭───╯
$100k ┼═══════╪═══════  Start Value (Break-even line)
 $75k ┤       │    ╭───  Net Value (after opp. cost)
 $50k ┤       │╭───╯
 $25k ┤   ────╯         
   $0 └─────────────────────────────────────>
```

### 3. **Decomposition Chart**
```
Gross Return:         +45.2%  ████████████████████
Opportunity Cost:     -12.3%  ██████
Net Return:           +32.9%  ██████████████

vs Buy-and-Hold:      +38.1%  ████████████████
Volatility Alpha:      +7.1%  ████
```

## Questions to Explore

1. **Does opportunity cost on initial capital matter for strategy comparison?**
   - If both strategies start with same capital, it cancels in alpha calculation
   - But matters for absolute return reporting

2. **Should we report "net return" as primary metric?**
   - More realistic investor perspective
   - Could be negative even with positive gross return
   - Emphasizes "beat the market or go home"

3. **How does this affect capital utilization metrics?**
   - Currently: `avg_deployed / start_value`
   - Should it be: `avg_deployed / (start_value + bank_balance)`?

4. **What about "positive bank" scenarios?**
   - If algorithm accumulates cash (bank > 0), did we over-capitalize?
   - Should measure: "optimal capital deployment"

5. **Time-series vs endpoint calculation?**
   - Track cumulative opportunity cost daily
   - Or just calculate total at end?
   - Daily tracking enables better visualization

## Recommended Next Steps

1. **Document current behavior** - Clarify that opportunity cost on initial capital is NOT currently tracked

2. **Create analysis script** - Calculate what opportunity cost WOULD be if we tracked initial capital

3. **Compare scenarios**:
   - Current reporting (no initial capital opp. cost)
   - Option B reporting (separate virtual debt tracking)
   - Option C reporting (post-calculation adjustment)

4. **Visualize the difference** - Show how metrics change with proper accounting

5. **Update theoretical framework** - Decide which interpretation best serves research goals

6. **Implementation** - If warranted, update backtest engine with chosen approach

## Philosophy Note

This is fundamentally about **what question we're asking**:

**Question A:** "Given I've deployed $100k in this strategy, how much money did I make?"
- Current model works fine
- Total return is clear

**Question B:** "Given I borrowed $100k at market rates, did this strategy beat the opportunity cost?"
- Need opportunity cost on initial capital
- Net return tells the story

**Question C:** "Should I use this strategy vs buy-and-hold with the same capital?"
- Volatility alpha answers this
- Opportunity cost cancels out (both strategies pay it)

**We're asking Question C, but reporting like Question A.**

The fix: Surface the opportunity cost explicitly, even though it cancels in the alpha calculation, to give complete picture of capital efficiency.

---

## Summary: Current Implementation Status

### What We Track ✅
1. **Opportunity cost on negative bank during trading**
   - When algorithm borrows money (bank < 0), we charge VOO returns
   - Calculated daily using actual reference asset returns
   - Reported in `summary['opportunity_cost']`

2. **Risk-free gains on positive bank**
   - When algorithm accumulates cash (bank > 0), we credit BIL returns
   - Calculated daily using actual risk-free asset returns
   - Reported in `summary['risk_free_gains']`

3. **Volatility alpha (correctly calculated)**
   - Algorithm return - buy-and-hold return
   - Opportunity cost cancels out in subtraction
   - Reported in `summary['volatility_alpha']`

### What We DON'T Track ❌
1. **Opportunity cost on initial capital**
   - The $100k to buy initial position came from somewhere
   - Either borrowed (owe interest) or owned (gave up returns)
   - We implicitly assume it's "free money" with no opportunity cost
   - **This is the gap we need to address**

2. **True net return after all costs**
   - Currently: `total_return = (end_value - start_value) / start_value`
   - Missing: Cost of capital on initial deployment
   - Should be: `net_return = (end_value - start_value - total_opp_cost) / start_value`

3. **Complete capital efficiency picture**
   - How much did we "borrow" total? (initial + negative bank)
   - What was the cumulative "interest bill"? (opp cost on both)
   - Did we make enough to justify the borrowed capital?

### Impact Assessment
- **For volatility alpha:** No impact (cancels in subtraction) ✓
- **For absolute returns:** Overstated by ~80-150% of initial capital over 5 years ⚠️
- **For investor understanding:** Missing the "borrowed capital" narrative ⚠️
- **For strategy comparison:** Misleading if different capital deployment patterns ⚠️

### Next Steps (see work plan in tasks)
Task 2 will quantify the magnitude of missing opportunity cost across real backtests.
