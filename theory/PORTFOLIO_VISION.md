# Multi-Stock Portfolio Vision

## Long-Term Goal: Portfolio-Level Synthetic Dividend Strategy

### Current State (Phase 1)
**Single-Stock Analysis**
- Backtest one stock at a time (NVDA, VOO, BTC, etc.)
- Initial capital fully deployed in that stock
- Bank tracks algorithm's trading cash flow
- Opportunity cost vs single reference asset (VOO)

**Limitations:**
- No diversification
- All capital locked in one stock
- Can't simulate realistic portfolio behavior

### Target State (Phase 2+)
**Multi-Stock Portfolio with Shared Cash Pool**

#### Portfolio Structure
```
Initial Portfolio: $100,000

Cash Reserve:        $10,000 (10%)  ← Liquid, earns 0% (true cash)
Stock Positions:     $90,000 (90%)  ← Diversified across N stocks

Example allocation:
- NVDA:  $20,000 (20%)
- VOO:   $30,000 (30%)  ← Index baseline
- GOOG:  $15,000 (15%)
- MSFT:  $15,000 (15%)
- BTC:   $10,000 (10%)
- Cash:  $10,000 (10%)  ← Buffer for buybacks & opportunities
```

#### How It Works

**1. Each Stock Runs Synthetic Dividend Algorithm Independently**
- NVDA hits ATH → Sells profit-sharing amount → **Cash pool increases**
- GOOG drops 8.3% → Buyback triggered → **Cash pool decreases**
- VOO sideways → No transactions → **No cash flow**

**2. Shared Cash Pool Dynamics**
```
Day 0: Cash = $10,000
Day 5: NVDA sells $2,000 → Cash = $12,000
Day 8: GOOG buys $1,500 → Cash = $10,500
Day 12: MSFT sells $3,000 → Cash = $13,500
Day 15: BTC buys $4,000 → Cash = $9,500  (below 10% target)
```

**3. Portfolio-Level Rebalancing Triggers**
- **Cash depletion** (< 5%): Reduce buyback aggressiveness or sell positions
- **Cash accumulation** (> 20%): Deploy into new stocks or increase allocations
- **Stock drift**: If NVDA grows to 40% of portfolio, consider taking profits

**4. Opportunity Cost Tracking**

**Three Separate Components:**

A) **Initial Cash Reserve** ($10k)
   - Earns 0% (true cash, not BIL)
   - No opportunity cost (it's meant to be liquid)
   - Purpose: Tactical buyback capital

B) **Stock Positions** ($90k total)
   - Each stock has opportunity cost vs VOO
   - NVDA return vs VOO return = NVDA alpha
   - Sum of all stock alphas = portfolio alpha

C) **Trading Cash Flow** (starts at $0, varies)
   - If cash pool > initial 10% → Could have deployed to VOO (opportunity cost)
   - If cash pool < 10% and went negative → Borrowed at VOO rate (opportunity cost)
   - If cash pool stays at 10% → No additional opportunity cost

### Key Advantages

**1. Risk Management**
- Diversification across multiple stocks
- Cash buffer prevents forced selling
- No borrowing needed for buybacks (if managed well)

**2. Opportunity Harvesting**
- Different stocks hit ATH at different times → Steady cash flow
- Volatility in one stock funded by stability in others
- Can add new positions when opportunities arise

**3. Realistic Investment Scenario**
- Mimics how real investors manage portfolios
- Tests strategy at portfolio level, not just individual stocks
- Answers the real question: "Should I adopt this for my portfolio?"

**4. Capital Efficiency**
- Cash earns 0% but enables buybacks (trade-off worth modeling)
- Measure: "Did 10% cash drag hurt more than buyback alpha helped?"
- Could discover optimal cash reserve percentage (5%? 15%? 20%?)

### Design Implications for Current Work

#### Initial Capital Opportunity Cost (Current Task)

**Single-Stock Model:**
```python
initial_capital = 100_shares * $100 = $10,000
# Track opportunity cost on full $10k vs VOO
```

**Portfolio Model:**
```python
cash_reserve = $10,000  # Earns 0%, no opportunity cost (tactical)
nvda_position = $20,000  # Opportunity cost vs VOO
voo_position = $30,000  # Baseline (0 opportunity cost vs itself)
goog_position = $15,000  # Opportunity cost vs VOO
# ... etc

total_opportunity_cost = sum(
    stock_position_opp_cost for each stock
    # Cash reserve excluded - it's meant to be liquid
    # Trading cash flow tracked separately
)
```

**Insight**: The 10% cash is NOT "idle capital with opportunity cost" - it's **tactical ammunition** with strategic value beyond returns.

### Implementation Phases

**Phase 2A: Multi-Stock Backtest Engine**
- [ ] Extend backtest to handle multiple stocks simultaneously
- [ ] Shared cash pool management
- [ ] Cross-stock transaction tracking
- [ ] Portfolio-level metrics (total return, Sharpe ratio, etc.)

**Phase 2B: Portfolio-Level Analytics**
- [ ] Correlation analysis between stocks
- [ ] Cash flow timing (are stocks complementary?)
- [ ] Optimal cash reserve percentage
- [ ] Portfolio rebalancing triggers

**Phase 2C: Optimization**
- [ ] Find optimal stock mix (which stocks work best together?)
- [ ] Dynamic allocation (shift % based on volatility?)
- [ ] Risk-adjusted return maximization
- [ ] Drawdown minimization

### Research Questions to Answer

1. **Cash Reserve Sizing**
   - Is 10% optimal? Or 5%? 15%? 20%?
   - Does it vary by portfolio volatility?
   - Trade-off: opportunity cost vs buyback enablement

2. **Stock Selection**
   - Which stocks generate best synthetic dividends?
   - How many stocks needed for diversification?
   - Should we include VOO as baseline anchor?

3. **Cross-Asset Effects**
   - Do stocks with negative correlation improve cash flow smoothness?
   - Can we time buybacks across stocks for better efficiency?
   - Does volatility in one stock create opportunities in others?

4. **Capital Allocation**
   - Equal weight (20% each for 5 stocks)?
   - Volatility-weighted (more in stable stocks)?
   - Conviction-weighted (more in high-growth picks)?

5. **Performance Metrics**
   - Portfolio return vs 100% VOO baseline
   - Cash flow consistency (std dev of monthly synthetic dividends)
   - Worst-case drawdown with cash buffer
   - "Buyback efficiency" (alpha gained per $ of cash reserved)

### Connection to Current Work

**Why This Matters for Initial Capital Opportunity Cost Analysis:**

1. **Cash Reserve Modeling**
   - Need concept of "tactical cash" with 0% opp cost (not BIL, not VOO)
   - Already supported! `risk_free_rate_pct=0.0` (default)

2. **Stock Position Opportunity Cost**
   - Each stock's opportunity cost is vs VOO (our portfolio baseline)
   - Aggregate across all stocks for total portfolio opp cost

3. **Trading Cash Flow**
   - Separate from tactical reserve
   - If depletes reserve → borrow at VOO rate (opportunity cost)
   - If exceeds reserve → could deploy to VOO (opportunity cost)

**This vision validates our current two-stream model:**
- ✅ Initial equity positions (stock allocations)
- ✅ Trading cash flow (algorithm's cash generation)
- ✅ NEW: Tactical cash reserve (strategic buffer, not measured vs VOO)

### Example Scenario: 5-Stock Portfolio (2023-2024)

**Starting Portfolio ($100k)**
```
NVDA:  $20k (100 shares @ $200)
VOO:   $30k (100 shares @ $300)
GOOG:  $15k (120 shares @ $125)
MSFT:  $15k (50 shares @ $300)
BTC:   $10k (0.5 BTC @ $20,000)
Cash:  $10k (reserve)
```

**After 1 Year:**
```
NVDA:  120 shares @ $350 = $42k  (+$22k, algorithm bought 20 shares in dips)
VOO:   100 shares @ $330 = $33k  (+$3k, buy-and-hold only)
GOOG:  110 shares @ $145 = $16k  (+$1k, sold 10 shares at ATH)
MSFT:  55 shares @ $350 = $19k   (+$4k, algorithm bought 5 shares)
BTC:   0.4 BTC @ $35,000 = $14k  (+$4k, sold 0.1 BTC at ATH)
Cash:  $12k (accumulated from sells)
Total: $136k (vs $130k buy-and-hold)
```

**Metrics:**
- Portfolio return: +36% (vs +30% buy-and-hold VOO)
- Volatility alpha: +6%
- Cash flow generated: $15k in sells, $13k in buybacks, net $2k accumulated
- Buyback efficiency: +$6k alpha from $10k cash reserve = 60% "return" on tactical capital

**Key Insight**: The cash reserve "costs" 0% in opportunity cost vs VOO, but "earns" alpha by enabling smart buybacks. This is the real trade-off to measure!

---

## Conclusion

The multi-stock portfolio vision is **essential to document now** because:

1. **Architecture decisions** - Affects how we design opportunity cost tracking
2. **Research priorities** - Guides what questions to ask
3. **Strategic clarity** - The 10% cash reserve is NOT wasted capital!
4. **Realistic testing** - Single-stock backtests don't answer "Should I adopt this?"

**Recommendation**: Document this vision, use it to inform our initial capital opportunity cost implementation (especially the three-stream model: tactical cash + stock positions + trading flow), and plan Phase 2 work accordingly.

The fact that we already support `risk_free_rate_pct=0.0` for true cash is perfect - we're architecturally ready for this future!
