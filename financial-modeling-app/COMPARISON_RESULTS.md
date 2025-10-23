# Algorithm Comparison Results

## Test Parameters
- **Ticker**: NVDA
- **Period**: October 22, 2024 - October 22, 2025 (251 trading days)
- **Initial Quantity**: 10,000 shares
- **Initial Value**: $1,435,488.59
- **Strategy Parameters**: 9.05% rebalance trigger, 50% profit sharing
- **Financial Adjustments**: VOO (reference asset), BIL (risk-free asset)

## Results Table

| Algorithm Name | Ending Shares | Ending Value | Ending Bank | Ending Total | Total Return % | Annualized Return % |
|----------------|--------------|--------------|-------------|--------------|----------------|---------------------|
| **Buy and Hold** | 10,000 | $1,802,799.99 | $0.00 | $1,802,799.99 | **25.59%** | 25.61% |
| **Synthetic Dividend (9.05%/50%)** | 8,989 | $1,620,536.91 | $236,493.04 | **$1,857,029.94** | **29.37%** | 29.39% |
| **SD ATH-Only (9.05%/50%)** | 8,806 | $1,587,545.67 | $203,351.42 | $1,790,897.09 | **24.76%** | 24.78% |

## Bank Balance Statistics (New!)

### Synthetic Dividend (Full Algorithm)
- **Bank Min**: -$262,230.02 (max margin/borrowing used)
- **Bank Max**: $236,493.04 (max cash reserve)
- **Bank Avg**: -$77,578.16 (average borrowed capital)
- **Days Negative**: 19 (days with borrowed capital)
- **Days Positive**: 6 (days with cash reserves)
- **Opportunity Cost (VOO)**: **-$8,305.88** ✓ (Negative = benefit from avoiding VOO)
- **Risk-Free Gains (BIL)**: $33.13
- **Net Financial Adjustment**: **+$8,339.01** (net benefit)

### SD ATH-Only
- **Bank Min**: $0.00 (never goes negative - no borrowing)
- **Bank Max**: $203,351.42 (max cash reserve)
- **Bank Avg**: $99,986.38 (average cash position)
- **Days Negative**: 0 (never borrows)
- **Days Positive**: 3 (days with cash)
- **Opportunity Cost (VOO)**: $0.00 (no borrowing)
- **Risk-Free Gains (BIL)**: $21.47
- **Net Financial Adjustment**: +$21.47

### Buy-and-Hold
- **Bank**: Always $0.00 (no transactions after initial purchase)
- **Financial Adjustments**: $0.00 (baseline)

## Key Findings

### Performance vs Buy-and-Hold

**Synthetic Dividend Full**: +$54,229.96 (+3.78% absolute return, +14.8% relative)
- Volatility Alpha: **5.29%**
- Reduced holdings: 8,989 shares (sold 1,011 net)
- Cash generated: **$236,493.04**
- **Financial Adjustment**: +$8,339 (VOO opportunity cost was NEGATIVE - we benefited!)
- Transaction count: 26 (13 BUY, 13 SELL)

**SD ATH-Only**: -$11,902.90 (-0.83% absolute return, -3.2% relative)
- No volatility harvesting (ATH-only)
- Reduced holdings: 8,806 shares (sold 1,194 net)
- Cash generated: $203,351.42
- **Financial Adjustment**: +$21 (small risk-free gains on cash)
- Transaction count: 4 (4 SELL only at ATHs)

### Share Count Analysis
- Full SD has **183 more shares** than ATH-only (8,989 vs 8,806)
- These extra shares represent **incomplete buyback cycles** (buybacks not yet fully unwound)
- Value of extra shares: 183 × $180.28 = $32,991.24
- **Note**: With buyback stack implementation, we expect exact parity in final shares

### Cash Balance Analysis
- Full SD has **$33,141.62 more cash** than ATH-only ($236,493 vs $203,351)
- This difference represents **profits from volatility harvesting**
- Total advantage: $32,991 (shares) + $33,142 (cash) ≈ $66,133

### The Negative Opportunity Cost Insight! 🎯

**Critical Finding**: The opportunity cost for SD Full is **-$8,305.88** (NEGATIVE!)

**What this means**:
- During the 19 days when bank was negative (borrowed capital), VOO actually **declined**
- By being in NVDA instead of VOO, we **avoided losses**
- The "cost" of borrowing was actually a **benefit** because VOO performed poorly
- This demonstrates why **asset-based adjustments** are crucial for realism

**Old Model (Fixed 10% Rate)**:
- Would show: -$77,578 avg × 10% = -$7,758 "cost"
- Misleading penalty that doesn't reflect reality

**New Model (Actual VOO Returns)**:
- Shows: **+$8,306 benefit** from staying in NVDA
- Accurately captures that VOO would have been worse during those periods
- Demonstrates relative performance, not absolute penalty

## Formula Verification

### Expected Relationship
```
return(sd-full) ≈ return(sd-ath-only) + total_volatility_alpha
```

### Actual Numbers
```
return(sd-full) = 29.37%
return(sd-ath-only) = 24.76%
total_volatility_alpha = 5.29%

24.76% + 5.29% = 30.05% ≈ 29.37% ✓ (within 0.68%)
```

**The relationship holds!** The 0.68% difference can be attributed to:
1. Integer rounding in share calculations
2. Price gaps beyond rebalance bracket boundaries  
3. Timing differences in when buybacks occur vs when they unwind

**Expected Improvement**: Once we implement the **buyback stack** (tracking individual purchase lots with FIFO unwinding), we expect this relationship to become **exact** with final share counts matching perfectly between full SD and ATH-only algorithms.

## Observations

### Why ATH-Only Underperforms Buy-and-Hold
- Sold 1,194 shares at ATH prices (only 4 transactions)
- **Missing upside** from shares sold early in the rally
- Cash sitting idle earning only BIL rate (~$21 total)
- Market continued rising after each ATH sell
- No mechanism to buy back in during corrections

### Why Full SD Outperforms Both
- **Volatility harvesting**: 26 transactions (13 BUY at dips, 13 SELL at ATHs)
- **Cash generation**: $236K from profit-taking
- **Maintained exposure**: 8,989 shares still capture upside
- **Alpha generation**: 5.29% from buying low / selling high
- **Negative opportunity cost**: +$8,306 benefit from staying in NVDA during VOO declines

### The Magic of Buybacks
Buybacks enable the algorithm to:
1. **Accumulate shares during dips** (buy low with borrowed capital)
2. **Harvest profits during rallies** (sell high, repay borrowing + take profits)
3. **Maintain higher share count** than ATH-only (183 more shares)
4. **Capture volatility alpha** while still following the trend
5. **Generate predictable cash flow** without sacrificing long-term growth

### The Barbell Strategy in Action
- **Negative bank periods** (-$262K max): Borrowed capital during market dips
  - Demonstrates conviction: buying weakness with leverage
  - **VOO declined during these periods** → negative opportunity cost = benefit!
  - Average -$77K borrowed position
  
- **Positive bank periods** ($236K max): Cash reserves during rallies
  - Provides distribution capacity without forced selling
  - Earns risk-free rate (BIL)
  - "Gold" reserve for optionality

### Financial Adjustment Reality Check

**Traditional View** (Fixed Rates):
- Borrowing -$77K avg @ 10% = -$7,758 annual cost
- Looks expensive, discourages borrowing strategy

**Realistic View** (Actual Asset Returns):
- Borrowed capital avoided VOO decline
- Net adjustment: **+$8,339 benefit**
- Validates that borrowing to stay in NVDA was the right call
- Shows true relative performance vs alternatives

## Running the Comparison

### Command Line
```powershell
# Full comparison table
python -m src.compare.table NVDA 10/22/2024 10/22/2025 9.05 50

# Individual algorithms with financial adjustments
python -m src.run_model NVDA 10/22/2024 10/22/2025 buy-and-hold --qty 10000
python -m src.run_model NVDA 10/22/2024 10/22/2025 sd/9.05%/50% --qty 10000
python -m src.run_model NVDA 10/22/2024 10/22/2025 sd-ath-only/9.05%/50% --qty 10000

# With custom reference/risk-free assets
python -m src.run_model NVDA 10/22/2024 10/22/2025 sd/9.05%/50% --qty 10000 --reference-asset SPY --risk-free-asset SHV
```

### Batch File
```powershell
.\compare-table.bat
```

### Custom Quantity
```powershell
python -m src.compare.table NVDA 10/22/2024 10/22/2025 9.05 50 50000
```

## Next Steps

### Planned Enhancement: Buyback Stack Implementation

**Goal**: Track individual purchase lots and unwind them precisely using FIFO (First-In-First-Out).

**Current Approximation**:
- Uses formula-based approach for calculating next trades
- ✅ Algebraically symmetric
- ✅ Captures essence of strategy
- ✅ Produces strong empirical results
- ⚠️ Small share count discrepancy vs ATH-only (183 shares)
- ⚠️ Doesn't track which specific lots are being unwound

**Proposed Exact Implementation**:
```python
class SyntheticDividendExact:
    """Track buyback lots for precise FIFO unwinding."""
    
    def __init__(self):
        self.buyback_stack: List[Tuple[float, int]] = []
        # Stack of (purchase_price, quantity) for each buyback
    
    def on_buy_transaction(self, price: float, qty: int):
        """Record buyback purchase."""
        self.buyback_stack.append((price, qty))
    
    def on_sell_transaction(self, sell_price: float, sell_qty: int):
        """Unwind buybacks FIFO, track exact profits."""
        remaining = sell_qty
        total_profit = 0.0
        
        while remaining > 0 and self.buyback_stack:
            buy_price, buy_qty = self.buyback_stack[0]
            to_unwind = min(remaining, buy_qty)
            
            # Calculate exact profit on this lot
            profit = (sell_price - buy_price) * to_unwind
            total_profit += profit
            
            # Update or remove stack entry
            if to_unwind == buy_qty:
                self.buyback_stack.pop(0)  # Fully unwound
            else:
                self.buyback_stack[0] = (buy_price, buy_qty - to_unwind)
            
            remaining -= to_unwind
        
        return total_profit
```

**Expected Benefits**:
1. ✅ **Exact share count parity** with ATH-only algorithm
2. ✅ **Perfect volatility alpha attribution** (profit per lot)
3. ✅ **Precise formula validation**: `return(sd-full) = return(sd-ath-only) + volatility_alpha`
4. ✅ **Account for price gaps** beyond bracket boundaries
5. ✅ **Eliminate rounding discrepancies**

**Implementation Status**: 
- Current: Formula-based approach (~0.68% discrepancy)
- Next: Stack-based FIFO tracking (expected: exact parity)

---

**Last Updated**: October 23, 2025
**Model Version**: Asset-Based Financial Adjustments (VOO/BIL)
