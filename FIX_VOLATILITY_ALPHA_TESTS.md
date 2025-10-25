## Bug Fix Summary: Volatility Alpha Test Failures

### Problem
Tests in `test_volatility_alpha_synthetic.py` were failing with negative alpha values when comparing Enhanced (with buybacks) vs ATH-only strategies.

### Root Cause Analysis

**Key Insight**: In a pure uptrend (gradual doubling scenario), Enhanced and ATH-only strategies execute **identical transactions** because there are no drawdowns to trigger buybacks.

**The Bug**: Tests were checking `enhanced_summary.get('volatility_alpha', 0)` which compares:
- **Enhanced vs Buy-and-Hold** (wrong comparison)

But tests should compare:
- **Enhanced vs ATH-Only** (correct comparison)

### Why This Matters

The `summary['volatility_alpha']` field is calculated as:
```python
volatility_alpha = total_return - baseline_total_return  # vs buy-and-hold
```

This measures how the algorithm performs against **buy-and-hold**, not against **ATH-only**.

In a pure uptrend:
- Enhanced and ATH-only have identical transactions
- They have identical total_return values
- They may both underperform buy-and-hold (negative alpha vs baseline)
- But Enhanced vs ATH-only alpha = 0 (identical performance)

### The Fix

Changed two test assertions in `tests/test_volatility_alpha_synthetic.py`:

**1. test_gradual_double_enhanced_vs_ath (line ~196)**
```python
# OLD (wrong):
vol_alpha = enhanced_summary.get('volatility_alpha', 0)  # vs buy-and-hold
self.assertAlmostEqual(vol_alpha, 0, places=2)

# NEW (correct):
vol_alpha = enhanced_summary['total_return'] - ath_summary['total_return']
self.assertAlmostEqual(vol_alpha, 0, places=4)
```

**2. test_volatile_double_has_positive_volatility_alpha (line ~246)**
```python
# OLD (wrong):
vol_alpha = enhanced_summary.get('volatility_alpha', 0)  # vs buy-and-hold
self.assertGreater(vol_alpha, 0)

# NEW (correct):
vol_alpha = enhanced_return - ath_return
self.assertGreater(vol_alpha, 0)
```

### Invariant Established

**New Invariant**: If Enhanced and ATH-only execute identical transactions, then volatility alpha (Enhanced vs ATH-only) MUST be zero.

### Expected Test Results

After this fix:
- ✅ `test_gradual_double_enhanced_vs_ath` - Should pass (0% alpha between identical strategies)
- ✅ `test_volatile_double_has_positive_volatility_alpha` - Should pass if buybacks genuinely occur
- Other volatility alpha tests may still need investigation

### Additional Notes

The algorithm's `self.total_volatility_alpha` field (accumulated from buyback transactions) is separate from `summary['volatility_alpha']` (vs buy-and-hold). These measure different things:
- `self.total_volatility_alpha` = profit from buyback cycles only
- `summary['volatility_alpha']` = algorithm performance vs buy-and-hold baseline

Tests should use explicit comparison of returns when comparing Enhanced vs ATH-only.
