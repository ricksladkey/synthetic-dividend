# Volatility Alpha — Theory (sd8 and general)

This document captures the formal theory and recommended measurement approach for "volatility alpha" used in the project. It complements `theory/PORTFOLIO_VISION.md` by providing formulas, examples (sd8), and practical tracking guidance (realized vs. unrealized alpha).

## Definitions

- volatility alpha: outperformance created by systematic buy-low / sell-high cycles relative to an ATH-only baseline (e.g., sd8 ATH-only).
- realized alpha: cash profits actually credited to the bank when buyback lots are unwound (sold).
- unrealized alpha (potential): the sum of expected profits on buyback lots that remain on the stack.

## Two equivalent measurement approaches

1) Baseline comparison

- Compute total return of the enhanced algorithm (with buybacks) and subtract the total return of the sd8 ATH-only baseline on the same price path and starting capital.
- This produces a single end-to-end alpha metric.

2) Accumulated profit accounting

- Track realized profits as they occur (increment realized alpha when lots are unwound and cash is credited).
- Track unrealized potential as the sum of (expected_sell_price - buy_price) × qty for each lot still on the stack.
- The estimated total alpha = realized + unrealized (upper bound if all lots unwind at expected prices).

Use both: baseline comparison is the economic ground-truth for full-range experiments; accumulated accounting is essential for internal validation and debugging.

## Analytic per-buy alpha (sd8 example)

Let:

- r = rebalance_size (decimal). For sd8, r ≈ 0.0905.
- s = profit_sharing fraction (decimal), e.g. s=0.5 for 50%.
- H = holdings at the anchor price P_anchor.

The algorithm's mechanics:

- Buy price: P_buy = P_anchor / (1 + r)
- Buy quantity: Q = r × H × s (rounded to integer)
- Per-share gross profit when sold at the anchor: ΔP = P_anchor − P_buy = P_anchor × (r/(1+r))

Portfolio-relative alpha from one buy-sell cycle (fraction of portfolio value H×P_anchor):

\[
\text{alpha}_{per\_buy} = \frac{\Delta P \times Q}{H \times P_{anchor}} = \frac{r^{2} s}{1 + r}
\]

Example (sd8): r = 0.0905, s = 0.5 →

- r^2 = 0.00819025
- alpha_per_buy ≈ (0.00819025 × 0.5) / 1.0905 ≈ 0.00375 = 0.375% of starting portfolio value per buy

This derivation explains the rule-of-thumb of roughly 0.3% alpha per buy used in tests and documentation.

## When can alpha be negative?

- Realized alpha (cash) from an unwind is non-negative by construction — sells unwind buys at higher anchors.
- Negative net alpha across a range happens when the strategy buys heavily during a drawdown and the price fails to recover by the end of the measured range, leaving the portfolio with net unrealized losses that overwhelm realized gains.

## Recommended tracking fields (summary payload)

- `volatility_alpha_baseline` (float): final_return(enhanced) − final_return(ath_only)
- `volatility_alpha_realized` (float): cumulative realized profit credited to bank
- `volatility_alpha_unrealized` (float): current potential profit on stack = Σ(expected_sell_price − buy_price)×qty
- `volatility_alpha_estimated_total` (float): realized + unrealized

Additional diagnostics to store per lot:
- `buy_date`, `buy_price`, `qty`, `expected_sell_price` (for FIFO accounting and transparent provenance)

## Presentation and interpretation

- Always show realized and unrealized components separately in charts and tables.
- For long-range economic conclusions, prefer the baseline comparison; for implementation correctness and unit tests, validate the per-buy analytic contribution and the accumulated accounting.

## Implementation notes (engine perspective)

- Maintain a FIFO `buyback_stack` of lots (buy_date, buy_price, qty, expected_sell_price).
- On SELL that unwinds lots:
  - Pop FIFO lots, compute realized profit per lot, increment `volatility_alpha_realized` and record the transaction.
- On report/visualization:
  - Compute `volatility_alpha_unrealized` from remaining lots.
  - Display `volatility_alpha_estimated_total` as an upper-bound and label it as "potential".

---

## Suggested quick checks for unit tests

- Per-buy analytic check: assert that each buy contributes at least `r^2 * s / (1+r)` to the estimated total (within rounding tolerance).
- End-to-end check: `volatility_alpha_baseline` ≈ `volatility_alpha_estimated_total / start_value` (they may differ due to rounding and partial unwinds; expect similar sign and magnitude).

---

(See `theory/PORTFOLIO_VISION.md` for broader portfolio-level context.)
