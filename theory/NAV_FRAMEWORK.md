# Internal NAV (Net Asset Value) Framework

## Core Concept

The Synthetic Dividend algorithm operates as a **NAV-based trading system**, maintaining an internal valuation (NAV) that's independent of market price and making buy/sell decisions based on deviations from that NAV.

## NAV Definition

**Internal NAV = All-Time High (ATH)**

The ATH serves as our fair value reference point:
- Represents the highest price at which the market has validated the asset
- Updates dynamically as new highs are achieved
- Acts as a "ratcheting baseline" that only moves upward

This is fundamentally different from traditional NAV (which is based on underlying asset values) - ours is based on **price discovery history**.

## Trading Rules in NAV Terms

### Buy Signal: Market Discount to NAV

**Condition:** Market price drops X% below NAV (ATH)

**Interpretation:** Market is offering shares at a discount to our internal valuation

**Example (sd8, 9.05% threshold):**
```
NAV (ATH): $100
Market price: $91.70 (9.05% below NAV)
Action: BUY - market is undervaluing relative to NAV
Expectation: Mean reversion toward NAV
```

**Buyback Stack Perspective:**
- Each buy creates a "NAV discount position"
- We bought at 9.05% below NAV
- Position profit = (Current Price - Buy Price) / Buy Price
- Unwind when price returns to NAV or better

### Sell Signal: Market Premium to NAV

**Condition:** Market price rises X% above NAV (ATH)

**Interpretation:** Market is paying a premium above our current NAV

**Example (sd8, 9.05% threshold):**
```
NAV (ATH): $100
Market price: $109.05 (9.05% above NAV)
Action: SELL - market is overvaluing relative to NAV
Update: NAV ← $109.05 (new ATH established)
```

**NAV Update Mechanism:**
- Selling at premium establishes new price discovery
- NAV ratchets up to new high
- This becomes the new baseline for future discount/premium calculations

## Gap Bonus Through NAV Lens

The multi-bracket gap fix allows **multiple NAV revaluations in a single day**, properly capturing market price discovery.

### Example: 20% Overnight Gap (sd8)

**Initial State:**
```
NAV: $100
Market opens: $120 (20% above NAV)
```

**Traditional NAV Revaluation (OLD - BUGGY):**
```
Step 1: Price $120 exceeds $109.05 threshold (9.05% above $100 NAV)
Action: SELL at $120
Update: NAV ← $120
Result: 1 transaction, missed intermediate price discovery
```

**Dynamic NAV Revaluation (NEW - CORRECT):**
```
Step 1: Price $120 exceeds $109.05 threshold (9.05% above $100 NAV)
Action: SELL at $120
Update: NAV ← $109.05 (establish new fair value)

Step 2: Price $120 exceeds $118.92 threshold (9.05% above $109.05 NAV)
Action: SELL at $120
Update: NAV ← $118.92 (establish higher fair value)

Step 3: Price $120 below $129.68 threshold (9.05% above $118.92 NAV)
No action: Price no longer at premium to latest NAV

Result: 2 transactions, proper NAV price discovery
```

**Key Insight:** Each sell establishes a new NAV level. If market price still exceeds the threshold above the NEW NAV, we have more premium to capture.

## NAV Dynamics Across Market Conditions

### Bull Market (Uptrend)

**Behavior:** NAV continuously ratchets upward
```
NAV: $100 → $109 → $119 → $130 → ...
Action: Frequent sells (profit-taking at premiums)
Holdings: Gradually decrease (profit sharing)
Bank: Accumulates cash from premium sales
```

**Outcome:** Capture gains incrementally while maintaining exposure

### Bear Market (Downtrend)

**Behavior:** NAV remains fixed at previous high
```
NAV: $100 (fixed)
Price: $100 → $91 → $83 → $76 → ...
Action: Frequent buys (accumulation at discounts)
Holdings: Gradually increase (buybacks)
Bank: Depletes as we dollar-cost-average down
```

**Outcome:** Accumulate shares at increasing discounts to NAV

### Recovery (V-Shape)

**Behavior:** Buy on the way down, sell on the way up
```
NAV: $100 (fixed during drawdown)
Price: $100 → $91 → $83 → $91 → $100 → $109

Actions:
  @ $91: BUY (9% discount to NAV)
  @ $83: BUY (17% discount to NAV)
  @ $91: No action (unwinding starts as price approaches NAV)
  @ $100: SELL (unwind first buyback at 0% profit)
  @ $109: SELL (unwind second buyback at 31% profit)
```

**Outcome:** Classic buy-low-sell-high, profit from volatility

### Choppy/Sideways

**Behavior:** Oscillate around fixed NAV
```
NAV: $100 (rarely updates)
Price: $100 ↔ $91 ↔ $100 ↔ $91 ↔ $100

Actions: Frequent buy/sell cycles at same NAV level
Holdings: Fluctuates around initial position
Bank: Accumulates incremental profits from cycles
```

**Outcome:** Generate "synthetic dividends" from oscillations

## NAV vs Traditional Valuation Methods

### Traditional NAV (Mutual Funds/ETFs)

**Definition:** Sum of underlying asset values / shares outstanding

**Use Case:** Determine if fund trades at premium/discount to holdings

**Limitation:** Requires knowing intrinsic value of assets

### Our Internal NAV (Price Discovery)

**Definition:** Highest price market has validated (ATH)

**Use Case:** Determine if current market price is at premium/discount to historical high

**Advantage:** 
- Works for ANY asset (doesn't require fundamental analysis)
- Self-adjusting based on market behavior
- Captures momentum (higher highs = higher NAV)

### Comparison to Other Strategies

| Strategy | Reference Price | Buy When | Sell When |
|----------|----------------|----------|-----------|
| **Value Investing** | Intrinsic value (DCF) | Price < intrinsic | Price > intrinsic |
| **Mean Reversion** | Moving average | Price < MA | Price > MA |
| **Momentum** | Recent trend | Price > high | Price < low |
| **Our NAV System** | ATH (dynamic) | Price < ATH-X% | Price > ATH+X% |

**Key Difference:** Our NAV only ratchets UP (like a high-water mark), while moving averages oscillate.

## Profit Sources in NAV Terms

### 1. Discount Capture (Buyback Profits)

**Mechanism:** Buy at discount to NAV, sell when price returns to NAV
```
Buy: $91 (9% discount to $100 NAV)
Sell: $100 (0% premium to $100 NAV)
Profit per share: $9 (9.9% return)
```

**Frequency:** Depends on drawdown depth and recovery speed

### 2. Premium Capture (ATH Sells)

**Mechanism:** Sell when market pays premium above NAV
```
NAV: $100
Sell: $109 (9% premium to NAV)
New NAV: $109
```

**Profit:** Locked in by selling at premium (can buy back cheaper if price drops)

### 3. Gap Bonus (Multi-Level Premium Capture)

**Mechanism:** Capture multiple premium levels when price gaps
```
NAV: $100
Gap to: $120
Sell #1: $109 (9% premium to $100 NAV) → NAV becomes $109
Sell #2: $119 (9% premium to $109 NAV) → NAV becomes $119
Total captured: $28 premium across two NAV levels
```

**Frequency:** Depends on gap frequency and magnitude (EXTREME for MSTR, BTC)

## NAV and the Rebalance Trigger (sd_n)

The rebalance trigger (X% in "Price < NAV - X%") determines the **NAV tolerance band**.

### sd8 Example (9.05% trigger)

**NAV Band:**
```
Upper bound: NAV × 1.0905 (premium threshold)
NAV: Current ATH
Lower bound: NAV × 0.9095 (discount threshold)
```

**Action Zone:**
- Price above upper: SELL (market paying premium)
- Price within band: HOLD (fair value range)
- Price below lower: BUY (market offering discount)

### Tighter Trigger (sd12: 5.95%)

**Effect:**
- Narrower NAV tolerance band
- More frequent buy/sell signals
- More transactions for same price path
- **Higher gap bonus** (more intermediate NAV levels in large gaps)

### Wider Trigger (sd4: 18.92%)

**Effect:**
- Wider NAV tolerance band
- Less frequent buy/sell signals
- Fewer transactions for same price path
- **Lower gap bonus** (fewer intermediate NAV levels)

## NAV Framework Benefits

### 1. Investor Communication

**Traditional explanation:** "We use a complex algorithm with exponential bracket thresholds and buyback stacks..."

**NAV explanation:** "We buy when the market offers a discount to our NAV, sell when the market pays a premium, and update our NAV as the asset reaches new highs."

Much clearer!

### 2. Performance Attribution

**Traditional:** "Volatility alpha of 95% from 1,908 transactions"

**NAV terms:** 
- "Captured $X in discount reversions (bought below NAV, sold at NAV)"
- "Captured $Y in premium realizations (sold above NAV)"
- "Captured $Z in gap bonuses (multiple premium levels per day)"

More intuitive!

### 3. Risk Management

**Question:** "What if the stock never returns to ATH?"

**NAV answer:** "Our buyback stack represents positions acquired at discounts to NAV. Even if NAV is never reached again, we've reduced cost basis by accumulating at lower prices. If NAV is reached, we profit from mean reversion."

### 4. Market Neutrality

The NAV framework works in any market:
- **Bull market:** Frequent NAV updates (new ATHs) → premium captures
- **Bear market:** Fixed NAV → accumulation at deepening discounts
- **Sideways:** Oscillation around NAV → synthetic dividend generation

No market prediction required - we're just trading premium/discount to our NAV.

## NAV vs Holdings Value

**Critical distinction:**

**Holdings Value:** `shares × current_market_price`
- This fluctuates with market price
- Traditional "mark-to-market" value

**NAV-Based Valuation:** `shares × NAV`
- Our internal assessment of "fair value"
- Independent of current market price

**Implication:**

When market price < NAV:
```
Market value: $91,000 (1,000 shares × $91)
NAV value: $100,000 (1,000 shares × $100 NAV)
Discount: $9,000 (9% below NAV)
```

We view this as a $9,000 "unrealized loss" relative to NAV, but it triggers a BUY signal because we expect mean reversion.

When market price > NAV:
```
Market value: $109,000 (1,000 shares × $109)
NAV value: $100,000 (1,000 shares × $100 NAV)
Premium: $9,000 (9% above NAV)
```

We SELL because the market is offering a premium. Then we update NAV to $109,000, making the premium "realized" as part of our new baseline.

## Implementation: NAV Tracking

**Current implementation** (implicit NAV via ATH):
```python
self.ath = 100.0  # This IS our NAV
self.next_sell_price = self.ath * (1 + self.alpha)  # Premium threshold
self.next_buy_price = self.ath / (1 + self.alpha)   # Discount threshold

if high >= self.next_sell_price:
    # Market is paying premium to NAV
    sell_at_premium()
    self.ath = self.next_sell_price  # Update NAV

if low <= self.next_buy_price:
    # Market is offering discount to NAV
    buy_at_discount()
    # NAV stays fixed (no new high)
```

**Potential explicit NAV tracking** (future):
```python
self.nav = 100.0  # Explicit NAV property
self.premium_threshold = 0.0905  # 9.05% for sd8
self.discount_threshold = 0.0905

def get_nav_premium(self, price):
    """Return premium % relative to NAV."""
    return (price - self.nav) / self.nav

def get_nav_discount(self, price):
    """Return discount % relative to NAV."""
    return (self.nav - price) / self.nav

if get_nav_premium(high) >= self.premium_threshold:
    sell_at_premium()
    self.nav = high  # Update NAV to new high

if get_nav_discount(low) >= self.discount_threshold:
    buy_at_discount()
    # NAV unchanged
```

This makes the NAV concept explicit in the code, improving readability.

## NAV Framework and Portfolio Theory

The NAV concept extends naturally to portfolios:

### Portfolio NAV

**Definition:** Weighted average NAV across all holdings

```
Portfolio NAV = Σ(shares_i × NAV_i) for all assets i
```

### Portfolio Rebalancing via NAV

**Traditional rebalancing:** Maintain fixed allocation percentages

**NAV-based rebalancing:** 
- Sell assets trading at large premiums to NAV
- Buy assets trading at large discounts to NAV
- This naturally rebalances toward undervalued assets

### Cross-Asset NAV Arbitrage

**Scenario:**
```
Asset A: Market at 15% premium to NAV
Asset B: Market at 10% discount to NAV
```

**Action:**
- Sell Asset A (capture premium)
- Buy Asset B (acquire at discount)
- Net effect: Rebalance from overvalued to undervalued

This is like pairs trading but using each asset's internal NAV as the reference.

## Conclusion

The NAV framework provides:

1. **Clearer mental model:** We're NAV traders, not volatility traders
2. **Better communication:** Easy to explain to investors
3. **Performance attribution:** Can break down profit sources
4. **Natural gap bonus explanation:** Multiple NAV updates per day
5. **Portfolio extension:** NAV concept scales to multi-asset systems

**The algorithm doesn't just generate "synthetic dividends from volatility" - it systematically captures premium/discount deviations from a dynamically-updated internal NAV.**

This reframing doesn't change the math, but it dramatically improves our understanding of WHY the algorithm works and HOW to optimize it.

