# Withdrawal Policy

## Overview

The withdrawal policy is an **orthogonal dimension** of the backtest system, applying uniformly to all strategies (buy-and-hold, SD8 Full, SD8 ATH-only, etc.). This architectural decision reflects the reality that withdrawal needs are independent of investment strategy.

## Key Principle: Orthogonality

**Withdrawals are NOT a special variant of buy-and-hold.**

Instead, withdrawals are a configurable policy that applies to ANY strategy:
- Buy-and-hold WITH withdrawals
- SD8 Full WITH withdrawals  
- SD8 ATH-only WITH withdrawals

This design reveals the true value proposition of cash-generating strategies: they avoid forced selling to fund withdrawals.

## Implementation

### Parameters

```python
run_algorithm_backtest(
    ...
    withdrawal_rate_pct: float = 0.0,           # Annual withdrawal as % of initial portfolio
    withdrawal_frequency_days: int = 30,        # Days between withdrawals (30 = monthly)
    cpi_adjustment_df: Optional[pd.DataFrame] = None,  # CPI data for inflation adjustment
    simple_mode: bool = False,                  # Disable inflation if True
)
```

### Standard Configuration

The default configuration follows the "4% rule":
- **Withdrawal Rate**: 4.0% of initial portfolio value annually
- **Frequency**: Monthly (30 days)
- **CPI Adjustment**: Enabled (withdrawals increase with inflation)
- **Base Amount**: `(initial_value × 0.04) × (30 / 365.25) ≈ 0.33% per month`

### Withdrawal Logic

The system implements a **bank-first** approach:

```python
if withdrawal_due:
    if bank >= withdrawal_amount:
        # Withdraw from cash (no forced selling)
        bank -= withdrawal_amount
    else:
        # Insufficient cash - must sell shares
        cash_needed = withdrawal_amount - bank
        shares_to_sell = ceil(cash_needed / current_price)
        # Execute forced sale
        holdings -= shares_to_sell
        bank = 0.0  # Bank depleted
```

This creates an observable difference between strategies:
- **SD8 strategies**: Generate cash → withdraw from bank → maintain position
- **Buy-and-hold**: Generate $0 → must sell shares → position erodes over time

## CPI Adjustment

Withdrawals can be inflation-adjusted using CPI data:

```python
# Initial withdrawal (month 1)
base_withdrawal = initial_value × (withdrawal_rate_pct / 100) × (30 / 365.25)

# Adjusted withdrawal (month N)
if cpi_data_available and not simple_mode:
    current_cpi = cpi_data[current_date]
    start_cpi = cpi_data[start_date]
    adjustment_factor = current_cpi / start_cpi
    actual_withdrawal = base_withdrawal × adjustment_factor
else:
    actual_withdrawal = base_withdrawal  # Nominal (no inflation adjustment)
```

**Real-world example** (2020-2024):
- Initial withdrawal: $333.33/month (4% of $100K)
- After 4 years with 20% cumulative inflation: $400.00/month
- Maintains purchasing power despite inflation

## Simple Mode

For clean unit testing, `simple_mode=True` disables:
1. **Opportunity cost** (free borrowing: `daily_reference_rate = 0`)
2. **Risk-free gains** (cash holds value: `daily_risk_free_rate = 0`)
3. **CPI adjustment** (no inflation: withdrawals stay constant)

This provides deterministic behavior ideal for testing withdrawal mechanics without confounding factors.

## Tracking Metrics

The system tracks three withdrawal-specific metrics:

```python
summary = {
    ...
    "total_withdrawn": float,              # Total $ withdrawn over backtest
    "withdrawal_count": int,               # Number of withdrawal events
    "shares_sold_for_withdrawals": int,    # Shares sold to fund withdrawals
    "withdrawal_rate_pct": float,          # Echo of input parameter
}
```

These metrics enable apples-to-apples comparison:

| Strategy | Total Withdrawn | Shares Sold | Final Holdings |
|----------|----------------|-------------|----------------|
| SD8 Full | $48,000 | 12 shares | 988 shares |
| Buy-and-hold | $48,000 | 480 shares | 520 shares |

The SD8 strategy maintains nearly full position by withdrawing from generated cash, while buy-and-hold loses ~48% of position to forced selling.

## Economic Interpretation

### The 4% Rule

The "4% rule" (Bengen, 1994) suggests retirees can withdraw 4% of their initial portfolio annually with high confidence of not depleting capital over 30 years.

**Traditional implementation**: Sell shares quarterly/annually
**SD8 implementation**: Withdraw from cash flow, sell only if needed

### Withdrawal vs Profit Sharing

These are **independent concepts**:

**Profit Sharing** (strategy parameter):
- Controls what % of rebalance profit to sell
- 50% = balanced growth vs income
- 100% = maximize cash generation
- Affects: transaction frequency, cash flow rate

**Withdrawal Rate** (lifestyle parameter):
- Controls how much cash you need for living expenses
- 4% = standard retirement withdrawal
- Higher = more aggressive spending
- Affects: sustainability, forced selling

### Sustainability Analysis

The combination of profit sharing and withdrawal rate determines sustainability:

| Profit Sharing | Withdrawal Rate | Cash Flow | Forced Selling | Sustainable? |
|----------------|----------------|-----------|----------------|--------------|
| 50% | 2% | Moderate | None | ✅ High |
| 50% | 4% | Moderate | Minimal | ✅ Good |
| 50% | 6% | Moderate | Some | ⚠️ Depends |
| 25% | 4% | Low | Frequent | ⚠️ Marginal |
| 100% | 4% | High | None | ✅ Excellent |

The SD8 algorithm's ability to generate cash flow determines how much withdrawal it can support without forced selling.

## Implementation History

### Bug Discovery (Critical)

**Initial Implementation** (BROKEN):
```python
tx = algo.on_day(...)
if tx is None:
    continue  # ← Skips withdrawal logic!

# Withdrawal code here (unreachable for buy-and-hold)
```

Buy-and-hold returns `None` every day → hits `continue` → skips withdrawal processing.

**Fix**:
```python
tx = algo.on_day(...)

# Process algorithm transaction (if any)
if tx is not None:
    # Execute SELL or BUY
    ...

# Withdrawal logic ALWAYS runs (outside conditional)
if withdrawal_due:
    # Process withdrawal
```

**Validation**: Debug script showed 0 withdrawals → identified structural issue → moved withdrawal logic outside transaction conditional → validated 12 monthly withdrawals.

### Test Suite

Three comprehensive tests validate orthogonality:

1. **`test_withdrawal_from_bank_balance()`**
   - SD8 generates cash
   - Withdrawals come from bank
   - Minimal forced selling (only in early periods)

2. **`test_withdrawal_forces_selling_for_buy_and_hold()`**
   - Buy-and-hold generates $0
   - Must sell shares every withdrawal
   - Holdings decline proportionally

3. **`test_simple_mode_no_opportunity_cost()`**
   - Validates simple_mode disables costs/gains
   - Clean behavior for unit tests
   - No confounding factors

## Future Enhancements

Potential additions:

1. **Variable Withdrawal Schedules**
   - Quarterly instead of monthly
   - Seasonal patterns (higher in certain months)
   - Dynamic adjustment based on portfolio value

2. **Withdrawal Strategies**
   - Fixed dollar amount (no inflation adjustment)
   - Fixed percentage (of current value, not initial)
   - Guardrails (reduce if portfolio declines)

3. **Tax Optimization**
   - Prefer selling long-term vs short-term lots
   - Harvest losses when forced to sell
   - Track cost basis for tax reporting

4. **Emergency Reserve**
   - Maintain minimum cash buffer
   - Don't withdraw if bank < threshold
   - Skip withdrawals during drawdowns

## References

- Bengen, W. P. (1994). "Determining Withdrawal Rates Using Historical Data." *Journal of Financial Planning*.
- Trinity Study (1998). "Retirement Savings: Choosing a Withdrawal Rate That Is Sustainable."
- Kitces, M. (2018). "Understanding Sequence of Return Risk: Safe Withdrawal Rates, Bear Market Crashes, and Withdrawal Rate Guardrails."

## Conclusion

The withdrawal policy implementation demonstrates that cash generation is valuable precisely because it avoids forced selling. By treating withdrawals as orthogonal to strategy, we can quantify the true benefit of volatility harvesting: **maintaining equity exposure while funding living expenses**.
