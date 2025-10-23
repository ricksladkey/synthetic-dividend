# Algorithm Comparison Results

## Test Parameters
- **Ticker**: NVDA
- **Period**: October 22, 2024 - October 22, 2025
- **Initial Quantity**: 10,000 shares
- **Strategy Parameters**: 9.05% rebalance, 50% profit sharing

## Results Table

| Algorithm Name | Ending Shares | Ending Value | Ending Bank | Ending Total | Total Return % |
|----------------|--------------|--------------|-------------|--------------|----------------|
| Buy and Hold | 10,000 | $1,802,799.99 | $0.00 | $1,802,799.99 | 25.59% |
| Synthetic Dividend (9.05%/50.0%) | 8,989 | $1,620,536.91 | $236,493.04 | $1,857,029.94 | 29.37% |
| SD ATH-Only (9.05%/50.0%) | 8,806 | $1,587,545.67 | $203,351.42 | $1,790,897.09 | 24.76% |

## Key Findings

### Performance vs Buy-and-Hold
- **Synthetic Dividend Full**: +$54,229.96 (+3.78% return)
  - Volatility Alpha: 5.29%
  - Reduced holdings: 8,989 shares (sold 1,011)
  - Cash generated: $236,493.04

- **SD ATH-Only**: -$11,902.90 (-0.83% return)
  - Reduced holdings: 8,806 shares (sold 1,194)
  - Cash generated: $203,351.42

### Share Count Analysis
- Full SD has **183 more shares** than ATH-only (8,989 vs 8,806)
- These extra shares represent **incomplete buyback cycles**
- Value of extra shares: 183 × $180.28 = $32,991.24

### Cash Balance Analysis
- Full SD has **$33,141.62 more cash** than ATH-only ($236,493 vs $203,351)
- Total advantage: $32,991 (shares) + $33,142 (cash) ≈ $66,133

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

The relationship holds approximately! The 0.68% difference could be due to:
1. Integer rounding in share calculations
2. Price gaps beyond bracket boundaries
3. Timing differences in when buybacks occur

## Observations

### Why ATH-Only Underperforms Buy-and-Hold
- Sold 1,194 shares at ATH prices
- Missing upside from shares sold too early
- Cash not reinvested (sitting idle at 0% return)
- Market continued rising after ATH sells

### Why Full SD Outperforms Both
- **Volatility harvesting**: Buys low, sells high within trends
- **Cash generation**: $236K cash from profits
- **Partial exposure**: 8,989 shares still capture most upside
- **Alpha generation**: 5.29% from volatility trading

### The Magic of Buybacks
- Buybacks allow the algorithm to:
  1. Generate cash during dips (buy low)
  2. Recover that cash during recovery (sell high)
  3. Maintain higher share count than ATH-only
  4. Capture both volatility alpha AND trend following

## Running the Comparison

### Command Line
```powershell
python -m src.compare.table NVDA 10/22/2024 10/22/2025 9.05 50
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

### Planned Enhancement
Track specific buy transactions to unwind them exactly (FIFO/LIFO) when selling. This will:
- Ensure precise unwinding of buyback cycles
- Properly attribute volatility alpha to specific trades
- Validate the formula relationship more accurately
- Account for price gaps beyond bracket boundaries

### Current Approximation
The current implementation uses a formula-based approach that:
- ✅ Is algebraically symmetric
- ✅ Captures the essence of the strategy
- ✅ Produces good results empirically
- ⚠️ May have small rounding errors with changing holdings
- ⚠️ Doesn't track individual purchase lots

### Proposed Exact Implementation
```python
# Pseudocode for exact unwinding
class SyntheticDividendExact:
    def __init__(self):
        self.purchase_queue = []  # Track (price, qty) for each buy
    
    def on_buy(self, price, qty):
        self.purchase_queue.append((price, qty))
    
    def on_sell(self, sell_price, sell_qty):
        # FIFO: Unwind oldest purchases first
        remaining = sell_qty
        while remaining > 0 and self.purchase_queue:
            buy_price, buy_qty = self.purchase_queue[0]
            to_sell = min(remaining, buy_qty)
            profit = (sell_price - buy_price) * to_sell
            # ... track profit exactly
            if to_sell == buy_qty:
                self.purchase_queue.pop(0)
            else:
                self.purchase_queue[0] = (buy_price, buy_qty - to_sell)
            remaining -= to_sell
```

This would provide:
- Exact profit tracking per transaction
- Perfect unwinding of buyback cycles
- Validation that formula relationship holds precisely
