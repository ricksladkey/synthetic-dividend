# Coding Philosophy

This document outlines the core principles guiding code quality and maintainability in this project.

## Core Tenets

### 1. Functional-Style Programming

**Principle**: Prefer pure functions with explicit inputs and outputs over stateful, imperative code.

**Benefits**:
- **Testability**: Pure functions are trivial to test—no mocking, no setup, just input → output
- **Reasoning**: Function behavior is determined solely by arguments, not hidden state
- **Composability**: Pure functions combine naturally into larger operations
- **Parallelization**: Side-effect-free code can be safely parallelized without coordination

**Examples in this codebase**:
```python
# GOOD: Pure function with explicit signature
def calculate_synthetic_dividend_orders(
    holdings: int,
    last_transaction_price: float,
    rebalance_size: float,
    profit_sharing: float
) -> Dict[str, Union[float, int]]:
    """Calculate buy/sell orders from current state."""
    next_buy_price: float = last_transaction_price / (1 + rebalance_size)
    next_buy_qty: int = int(rebalance_size * holdings * profit_sharing + 0.5)
    # ... pure calculation, no side effects
    return { ... }

# AVOID: Functions with hidden state dependencies
def calculate_orders(self):  # Missing explicit parameters
    # Reads from self.last_price, self.holdings, etc.
    # Hard to test, hard to reason about
```

**Practice**:
- Keep functions small (5-30 lines typical)
- Minimize mutable state
- Pass data explicitly via parameters
- Return results explicitly (no out-parameters)
- Avoid global variables and singletons


### 2. Static & Inferable Typing

**Principle**: All functions should have complete, explicit type annotations enabling static analysis.

**Benefits**:
- **IDE Support**: Autocomplete, inline docs, refactoring tools work correctly
- **Error Prevention**: Catch type errors at write-time, not runtime
- **Documentation**: Type signatures are executable documentation
- **Refactoring Safety**: Type checker validates changes across entire codebase

**Requirements**:
- Type all function signatures (parameters and returns)
- Use `typing` module for complex types: `Dict`, `List`, `Tuple`, `Optional`, `Union`, `Callable`
- Annotate instance variables in `__init__` methods
- Use `-> None` for procedures that return nothing

**Examples**:
```python
# GOOD: Complete type annotations
def run_algorithm_backtest(
    df: pd.DataFrame,
    ticker: str,
    initial_qty: int,
    start_date: date,
    end_date: date,
    algo: Optional[Union[AlgorithmBase, Callable]] = None,
    algo_params: Optional[Dict[str, Any]] = None,
) -> Tuple[List[str], Dict[str, Any]]:
    """Execute backtest against historical data."""
    # ...

# AVOID: Missing or partial type annotations
def run_backtest(df, ticker, qty, start, end, algo=None):  # No types
    # Type checker can't help, IDE can't autocomplete
```

**Type Annotation Guidelines**:
- **Primitives**: `int`, `float`, `str`, `bool`
- **Dates**: Use `date` (not `datetime`) for date-only values
- **Optional**: Use `Optional[T]` for nullable values (equivalent to `Union[T, None]`)
- **Collections**: `List[T]`, `Dict[K, V]`, `Tuple[T1, T2, ...]`, `Set[T]`
- **DataFrames**: `pd.DataFrame` (with comments explaining expected structure)
- **Unions**: `Union[TypeA, TypeB]` for multiple possible types
- **Callables**: `Callable[[Arg1Type, Arg2Type], ReturnType]`


### 3. Side-Effect-Free High-Level Operations

**Principle**: Structure code as pipelines of transformations rather than sequences of mutations.

**Pattern**:
```python
# GOOD: Immutable transformations
def process_data(raw_data: pd.DataFrame) -> pd.DataFrame:
    """Transform data through immutable operations."""
    filtered = raw_data[raw_data['price'] > 0]  # New DataFrame
    normalized = filtered.copy()  # Explicit copy
    normalized['price'] = normalized['price'] / normalized['price'].iloc[0]
    return normalized

# AVOID: In-place mutations
def process_data(data):
    data.drop(data[data['price'] <= 0].index, inplace=True)  # Mutates argument
    data['price'] /= data['price'].iloc[0]  # Mutates in-place
    # Function has no return value, operates via side effects
```

**Pandas Guidelines**:
- Prefer `.copy()` over in-place operations
- Use `.loc[mask].copy()` to create filtered views
- Chain operations with explicit intermediate variables for clarity
- Avoid `inplace=True` parameter (deprecated and harder to reason about)


### 4. Short Functions

**Principle**: Functions should be short enough to understand at a glance—typically 5-30 lines.

**Benefits**:
- **Comprehension**: Entire function fits in working memory
- **Testability**: Easier to write focused unit tests
- **Reusability**: Small, focused functions are more reusable
- **Debugging**: Smaller scope reduces cognitive load when debugging

**Guidelines**:
- Extract complex logic into named helper functions
- Use descriptive function names that explain purpose
- If function exceeds ~40 lines, consider extracting subfunctions
- Each function should do one thing well (Single Responsibility Principle)

**Example Refactoring**:
```python
# BEFORE: Long monolithic function
def run_backtest(df, ticker, qty, start, end, algo):
    # 20 lines of validation
    # 30 lines of data preprocessing
    # 50 lines of algorithm execution
    # 20 lines of result formatting
    # Total: 120 lines—too long to understand at once

# AFTER: Extracted into focused functions
def run_backtest(df, ticker, qty, start, end, algo):
    """Orchestrate backtest execution."""
    _validate_inputs(ticker, qty, start, end)
    df_processed = _preprocess_data(df, start, end)
    transactions, metrics = _execute_algorithm(df_processed, qty, algo)
    summary = _format_results(transactions, metrics)
    return transactions, summary

# Each helper is 10-25 lines, focused on one task
```


### 5. Voluminous Terse Accurate Comments

**Principle**: Comments should be dense, precise, and explain **why**, not **what**.

**Comment Types**:

**A. Module Docstrings** (top of file):
```python
"""Historical price data fetcher with per-ticker disk caching.

Fetches OHLC data from yfinance and caches to local pickle files.
Intelligently extends cache when requested dates exceed cached range.
"""
```

**B. Function Docstrings** (Google/NumPy style):
```python
def calculate_orders(holdings: int, price: float) -> Dict[str, Union[float, int]]:
    """Calculate symmetric buy/sell orders from current state.
    
    The formulas ensure perfect symmetry: if you buy Q shares at P_low,
    you can sell exactly Q shares back from P_low at P_current.
    
    Args:
        holdings: Current share count
        price: Last transaction price
        
    Returns:
        Dict with keys: next_buy_price, next_buy_qty, next_sell_price, next_sell_qty
        
    Raises:
        ValueError: If holdings negative or price non-positive
    """
```

**C. Inline Comments** (terse, explanatory):
```python
# Buy at r% below last price
next_buy_price: float = last_transaction_price / (1 + rebalance_size)

# Buy quantity: r * H * s, rounded to nearest integer
next_buy_qty: int = int(rebalance_size * holdings * profit_sharing + 0.5)

# ATH-only mode: seed with initial price as baseline
if not self.buyback_enabled:
    self.ath_price = current_price
```

**D. Complex Logic Comments** (explain "why"):
```python
# Add 1-day buffer on each side for yfinance's date handling quirks
start_dt = datetime.combine(start, datetime.min.time()) - timedelta(days=1)

# Extend cache leftward if requested range starts before cached data
if start_date < cache_min:
    df_left = self._download(ticker, start_date, cache_min - timedelta(days=1))
```

**Comment Guidelines**:
- **Terse**: One-line comments where possible
- **Accurate**: Comments must match code (update both together)
- **Explanatory**: Focus on intent, not mechanics
- **Strategic**: Comment complex algorithms, edge cases, workarounds
- **Avoid**: Don't comment obvious code (`i += 1  # increment i`)


### 6. Immutability Preferences

**Principle**: Prefer immutable data structures and avoid mutation when practical.

**Benefits**:
- **Thread Safety**: Immutable data can be safely shared across threads
- **Debugging**: Values don't change unexpectedly during execution
- **Reasoning**: Fewer possible states → simpler mental model

**Practices**:
```python
# GOOD: Create new objects instead of mutating
def update_holdings(current: int, qty: int) -> int:
    """Calculate new holdings count."""
    return current + qty  # Pure function, no mutation

# AVOID: Mutating passed-in data structures
def update_holdings(holdings_dict, qty):
    holdings_dict['count'] += qty  # Mutates argument
```

**Dataclass Usage**:
```python
from dataclasses import dataclass

@dataclass(frozen=True)  # frozen=True makes immutable
class Transaction:
    """Immutable transaction record."""
    action: str  # 'BUY' or 'SELL'
    qty: int
    price: float
    date: date
```

**When Mutation is Acceptable**:
- Local variables within function scope (not visible to caller)
- Builder patterns during object construction
- Performance-critical loops (with clear comments explaining tradeoff)


## Code Review Checklist

Before committing code, verify:

- [ ] **Types**: All functions have complete type annotations
- [ ] **Docstrings**: Public functions have Google/NumPy style docstrings
- [ ] **Comments**: Complex logic explained with terse, accurate comments
- [ ] **Length**: Functions are short (5-30 lines typical, max ~50)
- [ ] **Purity**: Functions prefer explicit parameters over hidden state
- [ ] **Side Effects**: Mutations are minimized and clearly documented
- [ ] **Tests**: New functions have unit tests (prefer pure functions for testability)
- [ ] **Naming**: Variable/function names are descriptive and unambiguous


## Rationale

These principles emerged from real-world experience with large codebases:

1. **Functional style** reduces bugs by minimizing state-related errors
2. **Static typing** catches errors at compile-time instead of production
3. **Short functions** reduce cognitive load and improve maintainability
4. **Dense comments** preserve intent for future maintainers (including yourself)
5. **Immutability** prevents entire classes of concurrency and mutation bugs

The goal is **code that is easy to understand, modify, and verify correctness**. These practices have proven effective across thousands of production systems.


## Examples From This Codebase

### Pure Function with Complete Types
```python
def calculate_synthetic_dividend_orders(
    holdings: int,
    last_transaction_price: float,
    rebalance_size: float,
    profit_sharing: float
) -> Dict[str, Union[float, int]]:
    """Pure function to calculate synthetic dividend buy/sell orders.
    
    The formulas ensure perfect symmetry: if you buy Q shares at price P_low,
    then from P_low you can sell exactly Q shares back at price P_current.
    """
    next_buy_price: float = last_transaction_price / (1 + rebalance_size)
    next_buy_qty: int = int(rebalance_size * holdings * profit_sharing + 0.5)
    next_sell_price: float = last_transaction_price * (1 + rebalance_size)
    next_sell_qty: int = int(rebalance_size * holdings * profit_sharing / (1 + rebalance_size) + 0.5)
    
    return {
        "next_buy_price": next_buy_price,
        "next_buy_qty": next_buy_qty,
        "next_sell_price": next_sell_price,
        "next_sell_qty": next_sell_qty,
    }
```

**Why This is Good**:
- ✓ Complete type annotations (all params and return)
- ✓ Pure function (no side effects, no hidden state)
- ✓ Short (14 lines of logic)
- ✓ Comprehensive docstring with formula explanation
- ✓ Terse inline comments explaining calculations
- ✓ Explicit intermediate variables with types
- ✓ Immutable return value (dict with explicit structure)


### Abstract Base Class with Type Safety
```python
class AlgorithmBase(ABC):
    """Abstract base class for trading algorithms.

    Subclasses must implement three lifecycle hooks:
    - on_new_holdings: Called after initial purchase
    - on_day: Called each trading day, returns Transaction or None
    - on_end_holding: Called at end of backtest period
    """

    def __init__(self, params: Optional[Dict[str, Any]] = None) -> None:
        """Initialize with optional parameters dict."""
        self.params: Dict[str, Any] = params or {}

    @abstractmethod
    def on_day(
        self, 
        date_: date, 
        price_row: pd.Series, 
        holdings: int, 
        bank: float, 
        history: pd.DataFrame
    ) -> Optional[Transaction]:
        """Process one trading day, optionally return transaction.
        
        Args:
            date_: Current date
            price_row: OHLC prices for current day
            holdings: Current share count
            bank: Current cash balance (may be negative)
            history: All price data up to previous day
            
        Returns:
            Transaction to execute, or None to hold
        """
        pass
```

**Why This is Good**:
- ✓ Complete type annotations on all methods
- ✓ Comprehensive class docstring explaining contract
- ✓ Method docstrings with detailed Args/Returns sections
- ✓ Explicit types for instance variables (`self.params: Dict[str, Any]`)
- ✓ Optional types used correctly (`Optional[Transaction]`)
- ✓ Multi-line signatures for readability


## Tools for Enforcement

### mypy (Static Type Checker)
```bash
# Install
pip install mypy

# Check entire codebase
mypy src/

# Strict mode (recommended)
mypy --strict src/
```

### pylint (Code Quality)
```bash
# Install
pip install pylint

# Check code quality
pylint src/
```

### pytest (Testing)
```bash
# Install
pip install pytest

# Run tests
pytest tests/
```


## Further Reading

- **Clean Code** by Robert C. Martin - Principles of readable code
- **Functional Programming in Python** - Pure functions and immutability
- **PEP 484** - Type Hints specification
- **PEP 8** - Python Style Guide
- **Google Python Style Guide** - Docstring conventions


## Evolution of This Document

This philosophy document should evolve with the codebase. When you discover a pattern that improves code quality, document it here with examples. When you find anti-patterns causing bugs, add them to the "AVOID" sections.

**Last Updated**: October 2025
**Contributors**: Project maintainers and code reviewers


---


## Appendix: Synthetic Dividend Algorithm Design Philosophy

### Profit Sharing Ratio: Strategic Considerations

The **profit sharing ratio** is a critical parameter that controls the balance between profit-taking and long-term growth.

#### The 50% Sweet Spot

**Profit sharing of 50% is a strategic value** that balances immediate profit realization while allowing continued position growth. This ratio ensures:

1. **Half of volatility gains are captured** as cash (bank balance)
2. **Half of the position remains invested** to compound long-term
3. **Over extended periods**, the position fully capitalizes on growth trends
4. **Short-term volatility** provides regular income without sacrificing long-term exposure

In bull markets (like the 1-year NVDA example showing 29% returns), the growth penalty from profit-taking is minimal because the remaining position continues to appreciate substantially.

#### Extended Range: Beyond 0-100%

The algorithm **mathematically supports profit sharing values outside the conventional 0-100% range**, with predictable and useful effects:

**Profit Sharing > 100%**:
- **Systematically reduces position size** as new all-time highs are reached
- Sells more shares than the rebalance would naturally dictate
- Useful for **position exit strategies** or **de-risking** at targets
- Example: 150% profit sharing will steadily convert equity to cash on uptrends

**Profit Sharing < 0% (Negative)**:
- **Steadily increases investment from cash** as asset price rises
- Buys additional shares even when selling would normally occur
- Useful for **dollar-cost averaging** into strength
- Example: -50% profit sharing converts rallies into accumulation opportunities

**Practical Implication**: The algorithm becomes a flexible position-sizing tool where profit sharing controls the **direction and rate** of position changes relative to price movements.

#### Rebalancing Trigger vs. Profit Sharing

**Key Insight**: Varying the **rebalancing trigger** (e.g., 5%, 9.05%, 15%, 25%) has significantly more impact on returns than varying the profit sharing ratio.

**Why?**
- **Rebalancing trigger** determines transaction frequency and volatility harvesting opportunities
- Lower triggers (5-7.5%) → more frequent trades → more alpha from volatility
- Higher triggers (15-25%) → fewer trades → lower transaction costs but less harvesting
- **Profit sharing** primarily affects position trajectory, not opportunity identification

**Empirical Evidence** (from batch comparison results):
- `sd/7.5%/100%` → 34.14% return (67 transactions)
- `sd/7.5%/50%` → 31.41% return (67 transactions)
- `sd/25%/100%` → 33.14% return (23 transactions)
- `sd/25%/50%` → 30.14% return (23 transactions)

Changing rebalance threshold from 7.5% to 25% reduces transaction count by 66% while maintaining similar returns. Changing profit sharing within same rebalance threshold shows smaller impact (~2-3% difference).

**Design Recommendation**: 
1. **Optimize rebalancing trigger first** based on asset volatility and transaction costs
2. **Set profit sharing to 50%** as the balanced default
3. **Adjust profit sharing** only for specific strategic goals (accumulation, de-risking)

### Bank Balance and Opportunity Costs

The algorithm tracks **bank balance statistics** to measure cash management efficiency:

**Metrics Tracked**:
- `bank_min`: Most negative balance (maximum margin used)
- `bank_max`: Highest cash balance
- `bank_avg`: Average cash position over backtest period
- `bank_negative_count`: Number of days with negative balance (borrowing)
- `bank_positive_count`: Number of days with positive balance (cash earning interest)

**Financial Adjustments**:

1. **Opportunity Cost** (when bank < 0):
   - Represents the cost of borrowing to maintain position
   - Calculated using reference return (e.g., S&P 500 TR ~10% annually)
   - Formula: `sum(abs(negative_bank_balance) * daily_reference_rate)`
   - Penalizes strategies that require sustained margin

2. **Risk-Free Gains** (when bank > 0):
   - Represents interest earned on cash reserves
   - Calculated using risk-free rate (e.g., Treasury bills ~4.5% annually)
   - Formula: `sum(positive_bank_balance * daily_risk_free_rate)`
   - Rewards strategies that maintain cash buffers

**Interpretation**: Strategies with large negative bank balances incur opportunity costs (foregone returns from alternative investments). Strategies with large positive balances earn risk-free returns but may sacrifice growth.

**Example**:
- Algorithm with avg bank = -$50,000 over 1 year at 10% reference return
- Opportunity cost ≈ $5,000 (reduces net return by ~0.35% on $1.4M portfolio)

This adjustment provides a more **realistic comparison** between strategies by accounting for the cost of capital.

### Asset-Based Financial Adjustments: The Real-World Model

**Critical Insight**: Fixed annual rates (10% reference, 4.5% risk-free) are **unrealistic** because they assume constant benchmark returns regardless of market conditions. The actual cost/benefit of capital varies with market performance.

**Enhanced Model** (implemented October 2025):

Instead of fixed rates, we now use **actual historical returns** from competing assets:
- **Reference Asset** (default: VOO - Vanguard S&P 500 ETF)
- **Risk-Free Asset** (default: BIL - SPDR 1-3 Month T-Bill ETF)

**Why This Matters**:

1. **Opportunity Cost Isn't a Penalty, It's a Comparison**
   - When bank is negative, we're not "paying interest" to anyone
   - We're measuring: "This capital could have been in VOO instead"
   - If VOO drops 5% that day → our "cost" is negative (we SAVED 5%!)
   - If VOO gains 2% that day → our cost is 2% of borrowed amount
   - This captures **relative performance**, not absolute penalty

2. **Example: Market Downturn Scenario**
   - Strategy A: Aggressive trading, -$200K avg bank
   - Strategy B: Conservative trading, -$50K avg bank
   
   **Old Model** (Fixed 10% rate):
   - Strategy A: -$20K opportunity cost (looks terrible)
   - Strategy B: -$5K opportunity cost (looks better)
   
   **New Model** (VOO actually returned -15% during period):
   - Strategy A: **+$30K** (saved by staying in NVDA, not VOO!)
   - Strategy B: **+$7.5K** (smaller benefit)
   - Strategy A is **better** because it avoided VOO's decline

3. **The Barbell Philosophy: Cash as Stability Mechanism**
   - As the target asset rallies → profit-taking → **cash accumulates**
   - This cash is **"gold"** - a barbell stabilizer for the portfolio
   - Cash earns BIL returns (T-bill equivalent, essentially risk-free)
   - Provides liquidity for distributions without forced selling
   - Protects against having to sell during downturns

4. **Daily Return Calculation**
   - Fetch historical data for VOO and BIL during backtest period
   - Calculate actual daily returns: `(today_price - yesterday_price) / yesterday_price`
   - Apply these actual returns to each day's bank balance
   - Sum across all days for total opportunity cost / risk-free gains

**Realistic Interpretation**:
- **Negative bank** = Capital "borrowed" from potential VOO investment
- **Positive bank** = Cash earning risk-free rate (BIL)
- **Neither is inherently good or bad** - depends on relative performance
- During bull markets: negative bank has higher cost (missing VOO gains)
- During bear markets: negative bank has negative cost (avoiding VOO losses)

**Implementation Example** (NVDA 10/22/2024-10/22/2025):
```
Bank Min: -$262,230 (max margin used)
Bank Avg: -$77,578 (mostly borrowed capital)
Opportunity Cost (VOO): -$8,306
Risk-Free Gains (BIL): +$33
Net Financial Adjustment: +$8,339
```

The **negative opportunity cost** means VOO actually declined during days when we had borrowed capital - we benefited by being in NVDA instead!

### Profit Sharing as Position Sizing: The Complete Strategy Spectrum

**Key Insight**: Profit sharing percentage determines **long-term position trajectory**, not just profit-taking amount.

**The Strategy Spectrum**:

1. **0% Profit Sharing = Buy-and-Hold**
   - Never take profits (never SELL except initial rebalance)
   - Position stays at 100% of initial shares
   - Equivalent to traditional buy-and-hold
   - No bank account needed
   - Maximum growth exposure, zero cash generation

2. **100% Profit Sharing = Constant-Weight Rebalancing**
   - Take full profits on every rebalance
   - Position shrinks toward single maximum share allocation
   - Equivalent to traditional constant-weight portfolio strategy
   - Over 10 years: locks into single maximum exposure (in nominal terms!)
   - Generates maximum cash, sacrifices long-term growth

3. **50% Profit Sharing = Best of Both Worlds**
   - Balanced profit-taking and position maintenance
   - Position can grow over long periods while still generating cash
   - Solves the **universal growth portfolio problem**: generating distributions without sufficient dividends
   - Creates predictable rules-based cash flow
   - Only unknown: **when** ATHs occur, not **whether** they occur

**The 10-Year Perspective**:

Why 50% beats 100% over long horizons:

- **100% Case**: After first ATH, you lock into maximum share count
  - Can never increase position size in nominal terms
  - Inflation erodes real exposure over time
  - Miss compound growth on the position itself
  - Example: Start with 10,000 shares → peak at 11,000 → stay at ~11,000 forever

- **50% Case**: Position can grow steadily
  - Half of gains stay in the position
  - Compound growth on growing share count
  - Still generate meaningful cash distributions
  - Example: Start with 10,000 → 12,000 → 14,000 → 16,000 over years
  - Generates cash while maintaining growth exposure

- **0% Case**: Maximum position growth, zero distributions
  - Full compound growth exposure
  - No cash for new opportunities or living expenses
  - Forced to sell externally if cash needed

**Why This Solves a Universal Problem**:

Traditional growth portfolios face a dilemma:
- **Dividends alone** are never enough for meaningful distributions (~1-2% yields)
- **Forced selling** for cash creates timing risk and tax events
- **Rebalancing to fixed income** sacrifices growth potential

**Synthetic Dividend Solution**:
- **Rules-based**: Profit-taking only at ATHs (strength, not weakness)
- **Predictable**: Formula-driven, no discretionary timing
- **Growth-preserving**: 50% keeps position growing with asset
- **Distribution-generating**: Creates cash flow without external sales
- **Only unknown**: WHEN ATHs occur, not IF they occur (assumes long-term growth)

**Strategic Use Cases**:

- **<0% (e.g., -25%)**: Accumulation mode - actually ADD on strength
  - Use when building position in quality asset
  - Buy more at ATHs instead of selling
  - Negative bank grows (requires external capital source)

- **0-25%**: Growth emphasis with minimal distributions
  - Near buy-and-hold performance
  - Small cash generation for optionality

- **25-50%**: Balanced growth and distributions
  - Sweet spot for most scenarios
  - Meaningful cash flow + position growth

- **50-75%**: Income emphasis with growth participation
  - Higher distributions, slower position growth
  - Good for transitioning to distribution phase

- **75-100%**: Maximum distributions, position maintenance
  - Position plateaus at max exposure
  - Maximum cash generation

- **>100% (e.g., 125%)**: De-risking mode
  - Actively reduce position at ATHs
  - Rotate out of concentrated holdings
  - Build cash reserves for redeployment

**Design Philosophy Summary**:

The Synthetic Dividend algorithm is a **flexible position-sizing tool** disguised as a profit-taking strategy. By adjusting a single parameter (profit sharing percentage), you control the position trajectory from aggressive accumulation (<0%) to maximum de-risking (>100%), while the rebalancing trigger determines transaction frequency and volatility harvesting efficiency.

The 50% default represents the **optimal balance** for most growth-oriented portfolios: maintain long-term compound exposure while generating predictable cash flow for distributions and new opportunities, all governed by simple rules that require no market timing or discretionary decisions.

---

**Last Updated**: October 2025
**Contributors**: Project maintainers and code reviewers
