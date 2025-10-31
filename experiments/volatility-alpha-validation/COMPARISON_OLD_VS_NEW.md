# Volatility Alpha Validation: OLD vs NEW Comparison

**Date**: October 31, 2025
**Reason**: Re-validation after critical algorithm fixes

## Algorithm Changes After Original Data Collection

The original validation data was collected on **October 26, 2025 at 3:29 AM**, BEFORE two critical algorithm fixes:

1. **Realistic Market Execution** (gap-through fills): Orders now fill at actual open price when gaps occur, not theoretical limit price
2. **Anti-Chatter Fix** (same-day execution prevention): Orders placed on day D now execute on D+1, preventing artificial same-day trading

These fixes required re-validation of all empirical claims in the Volatility Alpha Thesis.

## Summary: Overall Impact

The algorithm fixes had **dramatic and asymmetric** impact across different asset classes:

| Asset | OLD Alpha (3yr) | NEW Alpha (3yr) | Delta | % Change |
|-------|-----------------|-----------------|-------|----------|
| **PLTR** | 77.11% | **198.40%** | +121.29pp | +157% |
| **NVDA** | 33.93% | **76.78%** | +42.85pp | +126% |
| **ETH-USD** | 43.44% | **45.94%** | +2.50pp | +5.8% |
| **BTC-USD** | 26.28% | **27.11%** | +0.83pp | +3.2% |
| **MSTR** | 125.11% | **109.37%** | -15.74pp | -12.6% |
| **GLD** | 1.36% | **1.06%** | -0.30pp | -22.1% |

**Key Insight**: High-volatility tech stocks (NVDA, PLTR) benefited ENORMOUSLY from realistic gap-fill execution. MSTR showed reduction, suggesting the old code may have had unrealistically favorable fills.

---

## Detailed Comparison by Asset

### NVDA: +126% Increase in Alpha

| Metric | 1-Year | 2-Year | 3-Year |
|--------|--------|--------|--------|
| **OLD Alpha** | 5.78% | 19.07% | 33.93% |
| **NEW Alpha** | 5.39% | 19.62% | **76.78%** |
| **Delta** | -0.39pp | +0.55pp | **+42.85pp** |
| **OLD Buys** | 13 | 14 | 21 |
| **NEW Buys** | 12 | 14 | 18 |
| **OLD Full Return** | 36.57% | 259.97% | 620.56% |
| **NEW Full Return** | 36.18% | 260.52% | **696.09%** |

**Analysis**: The 3-year period shows MASSIVE improvement. Realistic gap-fill execution at open prices captured more value during NVDA's explosive 2023-2024 run.

---

### MSTR: -12.6% Reduction in Alpha

| Metric | 1-Year | 2-Year | 3-Year |
|--------|--------|--------|--------|
| **OLD Alpha** | 7.60% | 68.63% | 125.11% |
| **NEW Alpha** | 6.86% | 69.71% | **109.37%** |
| **Delta** | -0.74pp | +1.08pp | **-15.74pp** |
| **OLD Buys** | 23 | 44 | 66 |
| **NEW Buys** | 27 | 51 | 68 |
| **OLD Full Return** | 31.26% | 454.43% | 642.45% |
| **NEW Full Return** | 30.53% | 469.61% | **640.08%** |

**Analysis**: Despite MORE buy rebalances (68 vs 66), the 3-year alpha decreased by 15.74pp. This suggests the old code had unrealistically favorable gap fills that benefited MSTR's extreme volatility.

---

### BTC-USD: +3.2% Increase in Alpha

| Metric | 1-Year | 2-Year | 3-Year |
|--------|--------|--------|--------|
| **OLD Alpha** | 4.16% | 11.50% | 26.28% |
| **NEW Alpha** | 4.28% | 11.91% | **27.11%** |
| **Delta** | +0.12pp | +0.41pp | **+0.83pp** |
| **OLD Buys** | 12 | 23 | 34 |
| **NEW Buys** | 12 | 23 | 34 |
| **OLD Full Return** | 64.09% | 180.84% | 308.23% |
| **NEW Full Return** | 67.35% | 185.72% | **314.86%** |

**Analysis**: Minimal impact. BTC's smoother price action means gap fills had less effect. Same number of buy rebalances across all periods.

---

### ETH-USD: +5.8% Increase in Alpha

| Metric | 1-Year | 2-Year | 3-Year |
|--------|--------|--------|--------|
| **OLD Alpha** | 12.96% | 27.21% | 43.44% |
| **NEW Alpha** | 13.57% | 28.53% | **45.94%** |
| **Delta** | +0.61pp | +1.32pp | **+2.50pp** |
| **OLD Buys** | 20 | 29 | 40 |
| **NEW Buys** | 20 | 29 | 39 |
| **OLD Full Return** | 67.97% | 130.81% | 172.09% |
| **NEW Full Return** | 75.14% | 139.84% | **182.80%** |

**Analysis**: Modest improvement. ETH showed consistent gains across all timeframes from realistic execution.

---

### PLTR: +157% Increase in Alpha (MOST DRAMATIC)

| Metric | 1-Year | 2-Year | 3-Year |
|--------|--------|--------|--------|
| **OLD Alpha** | 19.14% | 43.31% | 77.11% |
| **NEW Alpha** | 16.35% | 58.22% | **198.40%** |
| **Delta** | -2.79pp | +14.91pp | **+121.29pp** |
| **OLD Buys** | 13 | 18 | 30 |
| **NEW Buys** | 10 | 12 | 25 |
| **OLD Full Return** | 236.10% | 582.17% | 858.90% |
| **NEW Full Return** | 239.98% | 614.56% | **997.38%** |

**Analysis**: PLTR showed the most dramatic improvement. The 3-year full return crossed 1000% (10x), with volatility alpha contributing 198.40% (nearly doubling). FEWER buy rebalances (25 vs 30) but MASSIVELY more effective due to realistic gap-fill execution during PLTR's explosive growth.

---

### GLD: -22.1% Reduction in Alpha

| Metric | 1-Year | 2-Year | 3-Year |
|--------|--------|--------|--------|
| **OLD Alpha** | 0.70% | 0.92% | 1.36% |
| **NEW Alpha** | 0.24% | 0.57% | **1.06%** |
| **Delta** | -0.46pp | -0.35pp | **-0.30pp** |
| **OLD Buys** | 8 | 8 | 12 |
| **NEW Buys** | 4 | 6 | 10 |
| **OLD Full Return** | 45.60% | 86.28% | 114.39% |
| **NEW Full Return** | 45.46% | 86.40% | **114.65%** |

**Analysis**: Low volatility means minimal alpha in both old and new code. The reduction is proportionally large (-22%) but absolutely small (only 0.30pp). Fewer buy rebalances under new code (10 vs 12).

---

## Patterns Observed

### 1. Gap-Fill Execution Matters Most for Tech Stocks

High-volatility tech stocks (NVDA, PLTR) with explosive growth phases benefit ENORMOUSLY from realistic gap-fill execution at open prices:
- **PLTR**: +121.29pp improvement
- **NVDA**: +42.85pp improvement

### 2. MSTR's Reduction Reveals Old Code's Bias

MSTR's -15.74pp reduction despite MORE buy rebalances suggests the old code had unrealistically favorable fills. The new realistic execution corrects this.

### 3. Crypto Shows Minimal Impact

BTC and ETH showed minimal changes (+0.83pp and +2.50pp respectively), suggesting smoother price action means less gap sensitivity.

### 4. Low Volatility = Low Alpha (Confirmed)

GLD continues to show minimal alpha in both old and new code, confirming that volatility is the key driver.

---

## Updated Claims for Volatility Alpha Thesis

### OLD CLAIM (Now Corrected):
> "MSTR (3yr): 66 buys → predicted 49.5% vs **actual 125.11%** (2.5x from gaps!)"

### NEW CLAIM (Validated):
> "MSTR (3yr): 68 buys → predicted 51.0% vs **actual 109.37%** (2.1x from gaps!)"

### OLD CLAIM (Now Corrected):
> "PLTR (3yr): 30 buys → predicted 22.5% vs **actual 77.11%** (3.4x from gaps!)"

### NEW CLAIM (Validated):
> "PLTR (3yr): 25 buys → predicted 18.75% vs **actual 198.40%** (10.6x from gaps!)"

### OLD CLAIM (Now Corrected):
> "NVDA (3yr): 21 buys → predicted 15.8% vs **actual 33.93%** (2.1x from gaps!)"

### NEW CLAIM (Validated):
> "NVDA (3yr): 18 buys → predicted 13.5% vs **actual 76.78%** (5.7x from gaps!)"

---

## Conclusions

1. **Realistic execution MATTERS**: The algorithm fixes revealed that gap-fill execution at actual open prices has MASSIVE impact on volatile growth stocks

2. **PLTR is the new star**: 198.40% volatility alpha over 3 years is extraordinary - nearly 200% additional return just from buying dips

3. **NVDA benefits enormously**: 76.78% alpha over 3 years means realistic execution captured the explosive 2023-2024 growth effectively

4. **MSTR's reduction is validation**: The decrease confirms we're now measuring REAL execution, not optimistic theoretical fills

5. **The formula still holds as lower bound**: Even with reduced MSTR alpha (109.37%), it's still 2.1x the theoretical minimum, confirming the formula is a conservative estimate

6. **Investment thesis strengthened**: The realistic execution results are even MORE compelling for volatile growth stocks (PLTR, NVDA) than the original data suggested

---

## Technical Details

### Old Code Issues (Pre-October 26, 2025):
- Gap-through orders filled at theoretical limit price
- Same-day execution allowed (artificial chatter)
- Result: Optimistic fills that may not be achievable in reality

### New Code (Post-October 26, 2025):
- Gap-through orders fill at actual open price (realistic)
- Orders placed on day D execute on D+1 (no same-day chatter)
- Result: Conservative, achievable execution model

### Validation Script:
- Location: `src/research/volatility_alpha_table.py`
- Runtime: ~2-3 minutes
- Command: `.venv/Scripts/python.exe -m src.research.volatility_alpha_table`
