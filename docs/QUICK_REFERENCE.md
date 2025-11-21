# Quick Reference Card

**Last Updated**: October 25, 2025
**Status**: [OK] All systems operational (39/39 tests passing)

---

## Core Concepts (30-second refresh)

**Volatility Alpha**: `algorithm_return - buy_and_hold_return`
**Rebalance Trigger**: sd8 = 9.05% (8th root of 2)
**Profit Sharing**: 50% = balanced (sell half of profit, keep half)
**Bracket Position**: 1.0 × (1.0905)^n for sd8

---

## Key Parameters

### Backtest Engine
```python
run_algorithm_backtest(
 df=price_data, # OHLC DataFrame
 ticker="NVDA", # Symbol
 initial_qty=1000, # Shares to start
 start_date=date(2020, 1, 1), # Begin
 end_date=date(2024, 1, 1), # End
 algo=SyntheticDividendAlgorithm(
 rebalance_size_pct=9.05, # sd8 trigger
 profit_sharing_pct=50.0, # 50% balanced
 buyback_enabled=True, # Full vs ATH-only
 ),
 # Optional enhancements
 normalize_prices=False, # Deterministic brackets
 withdrawal_rate_pct=0.0, # 4% = retirement
 withdrawal_frequency_days=30, # Monthly
 simple_mode=False, # Clean testing
)
```

### Order Calculator GUI
```bash
sd-calc-orders-gui
```

**Features**:
- Interactive GUI with persistent defaults per ticker
- Dropdown of all previously calculated tickers
- Current price defaults to last transaction price
- Accepts currency symbols and commas in price inputs ($1,234.56)
- Logarithmic price chart with bracket annotations
- Bracket seed supports 'none'/'nil' for no seed alignment

### Order Calculator (CLI)
```bash
sd-calc-orders \
 --ticker NVDA \
 --holdings 1000 \
 --last-price 120.50 \
 --current-price 125.30 \
 --sdn 8 \
 --profit 50
```

---

## Return Metrics (What to Look At)

**Primary Metrics** (these matter most):
- `total_return` - Overall gain/loss
- `volatility_alpha` - Excess return vs buy-and-hold
- `annualized` - Yearly equivalent return

**Secondary Metrics** (context):
- `holdings` - Final share count
- `bank` - Cash position
- `opportunity_cost` - Borrowing cost
- `risk_free_gains` - Cash interest

**Withdrawal Metrics**:
- `total_withdrawn` - Total cash withdrawn
- `shares_sold_for_withdrawals` - Forced selling count

---

## 🧪 Testing Commands

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_price_normalization.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run single test
pytest tests/test_withdrawal_policy.py::test_withdrawal_from_bank_balance -v
```

---

## Theory Documents (Where to Find Answers)

| Question | Document |
|----------|----------|
| Why does this work? | INVESTING_THEORY.md |
| What is volatility alpha? | VOLATILITY_ALPHA_THESIS.md |
| How do we measure returns? | RETURN_METRICS_ANALYSIS.md |
| Why opportunity cost? | INITIAL_CAPITAL_THEORY.md |
| How do brackets work? | PRICE_NORMALIZATION.md |
| How do withdrawals work? | WITHDRAWAL_POLICY.md |
| What's the vision? | PORTFOLIO_VISION.md |
| Coding guidelines? | CODING_PHILOSOPHY.md |

**Quick Theory Refresh**:
```bash
cat theory/INVESTING_THEORY.md theory/VOLATILITY_ALPHA_THESIS.md | less
```

---

## 🐛 Debugging Checklist

**If tests fail**:
1. Read error message carefully
2. Check if theory still matches implementation
3. Look at last passing commit
4. Run single failing test with `-v -s`
5. Add debug prints to isolate issue

**If results seem wrong**:
1. Check: Are you using simple_mode for testing?
2. Check: Is normalize_prices affecting comparison?
3. Check: Are withdrawals enabled unintentionally?
4. Check: Is opportunity cost being double-counted?

**If behavior changed**:
1. Did theory document update?
2. Did test assertions change?
3. Did new parameter get added?
4. Check git diff for recent changes

---

## Code Style Guide

**Variable Naming**:
- `rebalance_size` = decimal (0.0905)
- `rebalance_size_pct` = percentage (9.05)
- `_pct` suffix = percentage value
- `_df` suffix = DataFrame
- `_total` suffix = cumulative sum

**Function Naming**:
- `calculate_*` = pure function, no side effects
- `run_*` = executes process, returns results
- `format_*` = transforms data for display

**Test Naming**:
- `test_<behavior>_<scenario>` format
- Descriptive names (not test_001)
- Group related tests in classes

---

## Common Tasks

### Add a New Feature
1. Write theory document first
2. Write failing test
3. Implement feature
4. Make test pass
5. Update theory/README.md
6. Update CHECKPOINT.md

### Fix a Bug
1. Write test that reproduces bug
2. Fix implementation
3. Verify test passes
4. Check if theory needs update
5. Document in commit message

### Verify Theory Sync
1. Read CHECKPOINT.md
2. Spot-check key formulas in code
3. Run all tests
4. Review recent git commits

---

## 🔍 File Organization

```
src/
├── models/backtest.py # Core engine (423 lines, 78% covered)
├── tools/order_calculator.py # Manual trading tool (CLI)
├── tools/order_calculator_gui.py # Manual trading tool (GUI)
└── research/
 ├── strategy_comparison.py # Multi-strategy experiments
 └── volatility_alpha.py # Alpha validation

tests/
├── test_buyback_stack.py # 11 tests - core algorithm
├── test_synthetic_dividend.py # 8 tests - symmetry
├── test_volatility_alpha_*.py # 13 tests - alpha generation
├── test_price_normalization.py # 5 tests - deterministic brackets
└── test_withdrawal_policy.py # 3 tests - orthogonal design

theory/
├── README.md # Index
├── INVESTING_THEORY.md # Why
├── VOLATILITY_ALPHA_THESIS.md # Math
├── PRICE_NORMALIZATION.md # Brackets
├── WITHDRAWAL_POLICY.md # Withdrawals
└── ... (8 total documents)
```

---

## 🎓 Key Formulas (Quick Reference)

**Rebalance Trigger**:
```
trigger = (2^(1/N) - 1) × 100
sd4 = 18.92%
sd6 = 12.25%
sd8 = 9.05%
sd16 = 4.43%
```

**Buy/Sell Prices**:
```
buy_price = last_price / (1 + trigger)
sell_price = last_price × (1 + trigger)
```

**Bracket Number**:
```
n = log(price) / log(1 + trigger)
normalized_price = 1.0 × (1 + trigger)^round(n)
```

**Volatility Alpha**:
```
alpha = (final_value_algo - start_value) / start_value
 - (final_value_buyhold - start_value) / start_value
```

---

## TIP: Design Principles (Remember These)

1. **Orthogonality**: Features should be independent (withdrawals ≠ strategy)
2. **Test Behavior**: Test economic outcomes, not implementation details
3. **Theory First**: Document conceptual model before coding
4. **Fail Fast**: Clear error messages at validation time
5. **Empirical**: Experiments validate theory, not the reverse

---

## ⚡ Performance Notes

**Typical Backtest**: 1-5 seconds for 4 years daily data
**Test Suite**: ~5 seconds for all 39 tests
**Memory**: Minimal (<100MB for typical backtest)
**Bottleneck**: DataFrame operations (already optimized)

**Not optimized for**: Real-time trading, high-frequency data

---

## Success Criteria

**Feature is Complete When**:
- [ ] Theory document written
- [ ] Implementation matches theory
- [ ] Unit tests pass
- [ ] No regressions in existing tests
- [ ] CHECKPOINT.md updated
- [ ] theory/README.md updated

---

**Keep This Handy**: Bookmark this file for quick reference at start of each session.
