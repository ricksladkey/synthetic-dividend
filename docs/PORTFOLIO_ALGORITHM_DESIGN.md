# Portfolio Algorithm Architecture Design

**Date**: 2025-10-29
**Status**: Design phase - not yet implemented
**Goal**: Support both per-asset and portfolio-level rebalancing with shared cash pool

---

## Problem Statement

Current architecture only supports per-asset algorithms (synthetic dividends). Need to support:

1. **Per-asset strategies** (existing): Each asset rebalances independently with shared cash
   - Example: `sd8` on NVDA, `sd4` on BTC, buy-and-hold on VOO
   - Shared cash pool ("sweeps account") - if one asset runs out, all do

2. **Portfolio-level strategies** (new): Rebalance based on portfolio allocations
   - Example: 60/40 quarterly rebalancing (VOO/BIL)
   - Requires seeing all asset prices and current allocations

3. **Hybrid strategies**: Mix both approaches in same portfolio
   - Example: Synthetic dividends on growth stocks, buy-and-hold on bonds

---

## Design Principles

### Minimal API Surface

> "Everything is up for grabs unless we restrict it"

**Public API** (what algorithm implementers see):
- `on_portfolio_day()` - portfolio algorithms implement this
- `on_day()` - per-asset algorithms implement this (existing)
- That's it. No helpers, no utilities, no frameworks.

**Private internals** (backtest engine only):
- Transaction execution
- Bank balance tracking
- Date iteration
- These are NOT exposed to algorithms

### Thin Abstractions

> "The thinnest of abstractions"

**Don't create**:
- `PortfolioState` class with methods
- `AssetState` class with methods
- Helper utilities
- Configuration objects
- Builder patterns

**Do create**:
- Simple dataclasses with public fields (data holders only)
- Two abstract base classes with single required method each
- That's all

---

## Core Architecture

### Data Structures (pure data, no behavior)

```python
@dataclass
class AssetState:
    """Snapshot of single asset position. Pure data."""
    ticker: str
    holdings: int  # Share count
    price: float   # Current price
```

That's it. No `market_value()` method. Algorithm does: `state.holdings * state.price`.

### Algorithm Interfaces

**Portfolio-level algorithm** (new):
```python
class PortfolioAlgorithmBase(ABC):
    """Makes decisions across entire portfolio."""

    @abstractmethod
    def on_portfolio_day(
        self,
        date_: date,
        assets: Dict[str, AssetState],      # All asset positions
        bank: float,                        # Shared cash pool
        prices: Dict[str, pd.Series],       # Today's OHLC per asset
        history: Dict[str, pd.DataFrame],   # Historical OHLC per asset
    ) -> Dict[str, List[Transaction]]:
        """Return transactions keyed by ticker."""
        pass
```

**Per-asset algorithm** (existing, unchanged):
```python
class AlgorithmBase(ABC):
    """Makes decisions for single asset."""

    @abstractmethod
    def on_day(
        self,
        date_: date,
        price_row: pd.Series,     # Today's OHLC
        holdings: int,            # Current shares
        bank: float,              # Shared cash (read-only view)
        history: pd.DataFrame,    # Historical OHLC
    ) -> List[Transaction]:
        """Return transactions for this asset."""
        pass
```

### Adapter Algorithm (connects the two layers)

```python
class PerAssetPortfolioAlgorithm(PortfolioAlgorithmBase):
    """Runs per-asset algorithms in portfolio context."""

    def __init__(self, strategies: Dict[str, AlgorithmBase]):
        self.strategies = strategies

    def on_portfolio_day(self, date_, assets, bank, prices, history):
        transactions = {}
        for ticker, algo in self.strategies.items():
            txns = algo.on_day(
                date_,
                prices[ticker],
                assets[ticker].holdings,
                bank,
                history[ticker]
            )
            transactions[ticker] = txns
        return transactions
```

This is the **only** glue code needed. Everything else is algorithms.

---

## Implementation Strategy

### Step 1: Add PortfolioAlgorithmBase

Create `src/algorithms/portfolio_base.py`:
```python
from abc import ABC, abstractmethod
from datetime import date
from typing import Dict, List
import pandas as pd
from src.models.model_types import Transaction, AssetState

class PortfolioAlgorithmBase(ABC):
    @abstractmethod
    def on_portfolio_day(
        self,
        date_: date,
        assets: Dict[str, AssetState],
        bank: float,
        prices: Dict[str, pd.Series],
        history: Dict[str, pd.DataFrame],
    ) -> Dict[str, List[Transaction]]:
        pass
```

Add `AssetState` to `src/models/model_types.py`:
```python
@dataclass
class AssetState:
    ticker: str
    holdings: int
    price: float
```

### Step 2: Update portfolio backtest runner

Modify `run_portfolio_backtest()` to:
1. Accept `PortfolioAlgorithmBase` instead of individual `algo` param
2. Call `portfolio_algo.on_portfolio_day()` each day
3. Execute returned transactions against shared bank

Pseudo-code:
```python
def run_portfolio_backtest(
    allocations: Dict[str, float],
    start_date: date,
    end_date: date,
    portfolio_algo: PortfolioAlgorithmBase,  # Changed!
    initial_investment: float = 1_000_000.0,
):
    shared_bank = initial_investment
    holdings = {}  # Dict[str, int]

    # Initial purchase
    for ticker, pct in allocations.items():
        first_price = price_data[ticker].iloc[0]['Close']
        qty = int((initial_investment * pct) / first_price)
        holdings[ticker] = qty
        shared_bank -= qty * first_price

    # Daily loop
    for current_date in trading_dates:
        # Build asset states
        assets = {
            ticker: AssetState(
                ticker=ticker,
                holdings=holdings[ticker],
                price=price_data[ticker].loc[current_date, 'Close']
            )
            for ticker in allocations.keys()
        }

        # Get today's prices
        prices = {
            ticker: price_data[ticker].loc[current_date]
            for ticker in allocations.keys()
        }

        # Ask algorithm for transactions
        txns_by_ticker = portfolio_algo.on_portfolio_day(
            current_date,
            assets,
            shared_bank,
            prices,
            history_data
        )

        # Execute transactions (update holdings and shared_bank)
        for ticker, txns in txns_by_ticker.items():
            for tx in txns:
                if tx.action == "BUY":
                    cost = tx.qty * tx.price
                    if shared_bank >= cost or allow_margin:
                        holdings[ticker] += tx.qty
                        shared_bank -= cost
                elif tx.action == "SELL":
                    holdings[ticker] -= tx.qty
                    shared_bank += tx.qty * tx.price
```

### Step 3: Implement example algorithms

**Traditional quarterly rebalancing**:
```python
class QuarterlyRebalanceAlgorithm(PortfolioAlgorithmBase):
    def __init__(self, targets: Dict[str, float]):
        self.targets = targets
        self.last_rebalance = None

    def on_portfolio_day(self, date_, assets, bank, prices, history):
        # Check if rebalance due
        if date_.month not in [3, 6, 9, 12]:
            return {}
        if self.last_rebalance and (date_ - self.last_rebalance).days < 80:
            return {}

        # Calculate total portfolio value
        total = bank + sum(a.holdings * a.price for a in assets.values())

        # Generate rebalancing trades
        transactions = {}
        for ticker, target_pct in self.targets.items():
            current_val = assets[ticker].holdings * assets[ticker].price
            target_val = total * target_pct
            diff = target_val - current_val

            if abs(diff) > 100:  # Threshold
                qty = int(abs(diff) / assets[ticker].price)
                action = "BUY" if diff > 0 else "SELL"
                transactions[ticker] = [Transaction(
                    transaction_date=date_,
                    action=action,
                    qty=qty,
                    price=assets[ticker].price,
                    ticker=ticker,
                    notes=f"Quarterly rebalance"
                )]

        self.last_rebalance = date_
        return transactions
```

**Hybrid strategy** (uses existing algorithms):
```python
# Usage:
hybrid = PerAssetPortfolioAlgorithm({
    'NVDA': SyntheticDividendAlgorithm(0.0905, 50.0),
    'BTC-USD': SyntheticDividendAlgorithm(0.1892, 50.0),
    'VOO': BuyAndHoldAlgorithm(),
})

results = run_portfolio_backtest(
    allocations={'NVDA': 0.3, 'BTC-USD': 0.2, 'VOO': 0.5},
    start_date=date(2023, 1, 1),
    end_date=date(2024, 12, 31),
    portfolio_algo=hybrid
)
```

---

## What This Design Does NOT Include

- No `PortfolioState` helper class with methods
- No `calculate_allocations()` utility
- No `RebalanceStrategy` configuration objects
- No builder pattern for algorithms
- No algorithm registry or factory beyond existing `build_algo_from_name()`
- No event system or callbacks beyond the two required methods
- No middleware or plugins
- No abstract `execute()` method on algorithms

**Why not?** Each of these adds API surface. Algorithms can implement their own helpers if needed.

---

## Migration Path

**Existing code keeps working**:
- Single-asset backtests unchanged: `run_algorithm_backtest()` stays as-is
- Per-asset algorithms unchanged: `AlgorithmBase.on_day()` stays as-is

**New capabilities**:
- Portfolio backtests gain `portfolio_algo` parameter
- Old way still works via `PerAssetPortfolioAlgorithm` adapter

**Deprecation strategy**:
- Keep `simulate_portfolio()` wrapper for backward compat
- Add deprecation warning pointing to `run_portfolio_backtest()`

---

## Open Questions

1. **Withdrawals**: Should withdrawals be portfolio-level or per-asset?
   - Lean toward: Portfolio-level, happens before `on_portfolio_day()`

2. **Dividends**: How to handle in portfolio context?
   - Lean toward: Credit to shared bank automatically, not exposed to algorithm

3. **Margin handling**: Should algorithms see negative bank?
   - Lean toward: Yes, let algorithm decide if it matters

4. **Transaction validation**: Who checks if BUY is affordable?
   - Lean toward: Backtest engine (like today), not algorithm responsibility

---

## Next Steps

1. Add `PortfolioAlgorithmBase` class
2. Add `AssetState` dataclass
3. Modify `run_portfolio_backtest()` to use new interface
4. Implement `PerAssetPortfolioAlgorithm` adapter
5. Implement `QuarterlyRebalanceAlgorithm` as proof-of-concept
6. Write tests for portfolio-level rebalancing
7. Update CLI to support new algorithm type

---

## Success Criteria

**This design succeeds if:**
1. Traditional 60/40 quarterly rebalancing can be implemented in <50 lines
2. Hybrid strategies (per-asset + buy-and-hold) require zero new code
3. Algorithm implementers only need to understand 1-2 methods
4. No "framework" emerges - just data and one decision point

**This design fails if:**
- Need to read >2 files to understand how to write an algorithm
- "Helper" utilities start proliferating
- Configuration objects multiply
- Can't explain the design in 5 minutes
