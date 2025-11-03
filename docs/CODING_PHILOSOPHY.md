# Coding Philosophy

This document outlines the core principles guiding code quality and maintainability in this project.

## Meta-Principle: Don't Hide Your Light Under a Bushel

**Principle**: When you have strong opinions backed by technical reasoning, state them clearly and pointedly.

**Why**:
- **Clarity beats politeness**: "This is wrong" > "Perhaps we might consider..."
- **Efficiency**: Direct feedback saves time and avoids misunderstandings
- **Technical leadership**: Strong opinions, weakly held—advocate clearly, update freely
- **Respect through honesty**: Pointed remarks show you care enough to be direct

**Practice**:
- Say "This approach is fundamentally flawed because..." not "Maybe this could be improved"
- Recommend the best solution directly: "Option 1 is clearly superior for these three reasons"
- Don't soften technical critique with hedging language
- Back strong statements with concrete technical reasoning
- But remain open to counter-arguments with better reasoning

**Example**:
```python
# GOOD (pointed, clear)
# This is a terrible design. The lot selection logic doesn't belong here
# because tax consequences are orthogonal to symmetry tracking.
# Remove this entire method.

# AVOID (wishy-washy)
# Perhaps we might consider whether this method is needed, as it seems
# like maybe there could be some potential concerns about...
```

**Caveat**: Be direct about **code and architecture**, not people. Critique the work, not the worker.

---

## Meta-Principle: Document Insights While Everything Is Fresh

**Principle**: Write conclusions, insights, and experimental results immediately after discovery, while context is still vivid in your mind.

**Why**:
- **Context evaporates**: Technical details fade within hours; assumptions you "just know" become mysteries
- **Future you is a stranger**: What's obvious now will be obscure in a week
- **Experiments have half-lives**: Without documentation, research decays into "we tried something once"
- **Compounding knowledge**: Today's insights inform tomorrow's experiments, but only if captured

**Practice**:
- After running experiments: Write summary markdown **immediately** with findings, surprises, and implications
- Create lab notebooks: Document hypothesis, methodology, results, and next questions
- Capture the "why": Don't just log what happened, explain why it matters
- Record failures: Negative results are valuable; document what didn't work and why
- Include reproduction steps: Future experiments should build on, not rediscover, past work

**Structure for Experiment Documentation**:
```markdown
# Experiment: [Name]
**Date**: [ISO date]
**Hypothesis**: [What you expected to find]
**Methodology**: [How you tested it]
**Results**: [What actually happened - data, charts, numbers]
**Insights**: [What this means, surprises, implications]
**Next Steps**: [Questions raised, follow-up experiments]
```

**Example**:
After running portfolio volatility alpha experiment, don't just commit the code—write:
- What the +39% volatility alpha means economically
- Why ATH-only underperformed buy-and-hold by 208%
- Which assets contributed most and why
- How this changes our understanding of the strategy
- What parameters should be tested next

**Caveat**: Balance thoroughness with momentum. 5 minutes of documentation now saves 5 hours of archaeology later.

---

## Meta-Principle: Abstraction Level Determines Naming

**Principle**: Variable and parameter names should match the abstraction level of the code they appear in. Use the most abstract term appropriate for that architectural layer.

**Why**:
- **Architectural clarity**: High-level code should read at a high level of abstraction
- **Pythonic interoperability**: When in the Python ecosystem, use established conventions from that ecosystem
- **Glue code flexibility**: Interface layers are free to use implementation-specific names
- **Cognitive load reduction**: Don't force readers to context-switch between abstraction levels

**The Abstraction Hierarchy** (from most abstract to most specific):
1. **Domain concepts**: `price`, `quantity`, `transaction`, `balance`
2. **Data architecture**: `row`, `record`, `series`, `dataset`
3. **Implementation specifics**: `DataFrame`, `ndarray`, `dict`, `list`

**Rules**:
1. **High-level business logic**: Use domain concepts exclusively
   - ✓ `process_transaction(price: float, quantity: int)`
   - ✗ `process_transaction(df_row: pd.Series, qty: int)`

2. **Mid-level architecture**: Use data structure abstractions
   - ✓ `def calculate_returns(price_series: pd.Series) -> pd.Series`
   - ✓ `def fetch_market_data(ticker: str) -> pd.DataFrame`  (pandas is THE Python standard)
   - ✗ `def calculate_returns(price_list: List[float])`  (too specific for this level)

3. **Pythonic naming**: When a concept has an established Python/pandas convention, use it
   - ✓ `df` for DataFrame in local scopes (pandas convention)
   - ✓ `Series` for time series data (pandas standard)
   - ✗ `data_row` when `Series` is the Pythonic term everyone understands

4. **Glue code is free**: Interface/adapter code can be implementation-specific
   - ✓ `def convert_df_to_records(df: pd.DataFrame) -> List[Dict]`
   - ✓ `def pandas_series_to_numpy(series: pd.Series) -> np.ndarray`

**Naming Priority** (choose the first applicable):
1. **Domain term** (if concept exists in business logic): `price`, `order`, `account`
2. **Abstract data term** (if structural concept): `row`, `record`, `series`, `table`
3. **Pythonic term** (if ecosystem standard): `DataFrame`, `Series`, `dict`, `list`
4. **Implementation term** (only in glue/low-level code): `np.ndarray`, `pd.Index`

**Examples**:

```python
# GOOD: Domain-level abstraction
def calculate_portfolio_value(
    holdings: int,
    price: float,
    cash_balance: float
) -> float:
    """High-level business logic uses domain concepts."""
    return holdings * price + cash_balance

# GOOD: Data architecture abstraction
def run_algorithm_backtest(
    price_data: pd.DataFrame,  # "price_data" is more abstract than "df"
    ticker: str,
    initial_qty: int,
    reference_series: Optional[pd.Series] = None  # "series" is the data architecture term
) -> Tuple[List[Transaction], Dict[str, Any]]:
    """Mid-level uses data abstractions + Pythonic conventions."""
    pass

# AVOID: Mixed abstraction levels
def run_algorithm_backtest(
    reference_asset_df: Optional[pd.DataFrame] = None  # ❌ "asset" is domain, "df" is implementation
):
    """Mixing "asset" (domain) with "df" (pandas-specific) confuses the abstraction."""
    pass

# GOOD: Corrected
def run_algorithm_backtest(
    reference_data: Optional[pd.DataFrame] = None  # ✓ "data" is appropriately abstract
):
    """Or even better: reference_series if it's 1D time series data."""
    pass

# GOOD: Low-level glue code can be specific
def _extract_close_prices_as_array(df: pd.DataFrame) -> np.ndarray:
    """Implementation-specific helper is fine at this layer."""
    return df['Close'].values

# GOOD: Pythonic convention for local scope
def process_data(price_data: pd.DataFrame) -> pd.Series:
    df = price_data  # Local rename to idiomatic 'df' is fine
    return df['Close'].pct_change()
```

**Database Analogy**:
Database architects call it a "row" because that's the abstract concept. Pandas calls it a `Series` because that's the Pythonic term for a 1D labeled array. Both are correct at their abstraction levels:
- Database layer: `row: DatabaseRow` ← domain abstraction
- Pandas layer: `series: pd.Series` ← Pythonic ecosystem term
- Glue layer: `df_row: pd.Series` ← explicit type bridge

**When in doubt**:
- If you're writing business logic → use domain terms
- If you're writing data processing → use Pythonic terms
- If you're writing adapters → be explicit about types
- If your parameter name has multiple words and one is an implementation detail → you've mixed abstraction levels

**Caveat**: "The most abstract word is the best, the first one after 'Noun'!" — but not so abstract it becomes meaningless. `data` is better than `reference_asset_df`, but `price_series` is better than `data` if it's specifically price data.

---

## Meta-Principle: Code You Can Maintain Without AI

**The Assembly Language Analogy**:

C++ programmers rarely look at assembly—until there's a problem. Then it becomes foreign territory, hard to navigate. AI-generated code is the same: if you can't read and understand it, you've lost control of your own project.

**Principle**: Write code in a style you can understand and maintain years later, without depending on the tool that generated it.

**Why**:
- **Maintainability decay**: Code you can't explain becomes technical debt
- **Dependency risk**: Relying on AI to maintain your codebase is fragile—tools change, access ends, context is lost
- **Understanding compounds**: Deep code comprehension enables better architecture decisions over time
- **Debugging requires mastery**: When things break at 2am, you need to understand every line

**AI as Colleague, Not Autopilot**:

The goal is **sustainable collaboration**—AI accelerates work you understand, it doesn't replace understanding.

**Good uses** (delegate the busywork):
- ✅ Boilerplate generation (test scaffolding, type hints, docstrings)
- ✅ Repetitive edits across multiple files
- ✅ Documentation formatting and consistency
- ✅ Implementing well-specified algorithms you've designed
- ✅ Converting between data formats you understand

**Bad uses** (don't delegate architecture):
- ❌ Designing core algorithms without understanding the approach
- ❌ Accepting abstractions you can't explain
- ❌ Implementing business logic without grasping the why
- ❌ "Fix this bug" without understanding the root cause
- ❌ Any code you wouldn't confidently review and approve yourself

**Bare-Bones Over Clever**:

Prefer simple, obvious code over "elegant" abstractions you don't fully understand. Your future self (and any maintainer) will thank you.

```python
# GOOD: Straightforward, maintainable
def calculate_profit(sell_price: float, buy_price: float, qty: int) -> float:
    """Calculate profit from a trade."""
    return (sell_price - buy_price) * qty

# AVOID: Clever but opaque (even if "more Pythonic")
from functools import reduce
import operator
calculate_profit = lambda s, b, q: reduce(operator.mul, [operator.sub(s, b), q])
```

The first version is longer but **you can debug it at 2am without Stack Overflow**. The second requires remembering functional programming patterns and operator precedence.

**The Maintenance Test**:

Before accepting any code (AI-generated or otherwise), ask yourself:

1. **Can I explain what this does to a colleague?** If not, you don't understand it well enough to maintain it.
2. **Could I debug this at 2am without the AI?** The tool won't be there when production breaks.
3. **Will I understand this in 6 months?** Context fades fast—code must be self-documenting.
4. **Is this the simplest solution that works?** Complexity is a liability, not an asset.

If any answer is "no", simplify or reject it.

**Real-World Horror Story**:

Developer builds a complex system with heavy AI assistance. Six months later, a critical bug appears. The original developer can't explain how the code works—they just know it did work. The AI doesn't have context from six months ago. The codebase becomes unmaintainable archaeology instead of living software.

**Prevention**: Own your code conceptually. AI should amplify your understanding, not replace it.

**Practical Guidelines**:

- **Before writing code**: Understand the problem and sketch the solution yourself
- **While using AI**: Review every line generated; if you wouldn't write it yourself, reject it
- **After generation**: Explain the code out loud; if you stumble, the code is too complex
- **During debugging**: If you're lost in your own codebase, you've lost control—simplify

**Caveat**: This doesn't mean avoiding AI—it means using AI **as a force multiplier for work you understand**, not a replacement for understanding. The assembly language analogy isn't "don't use compilers"—it's "understand what your compiler is doing."

Good engineers use abstractions (compilers, frameworks, AI) but maintain conceptual mastery of what's happening underneath. When abstractions leak or fail, understanding is your only defense.

---

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


### 7. Test-Driven Trust

**Principle**: Tests are not just verification—they are the foundation of confidence in our calculations and logic.

**Philosophy**: "Tests are like magic. They keep us distrusting calculations that could be wrong and we wouldn't notice."

**Why Tests are Essential**:
- **Catch Silent Bugs**: Calculations can be subtly wrong without obviously breaking
- **Document Expected Behavior**: Tests are executable specifications
- **Enable Refactoring**: Comprehensive tests let you change code fearlessly
- **Prevent Regression**: Once fixed, bugs stay fixed
- **Expose Edge Cases**: Unusual inputs that you wouldn't think to manually test

**Real Example from This Codebase**:
The buyback stack tests exposed a fundamental misunderstanding about volatility harvesting:
- **Original Assumption**: Enhanced and ATH-only should have equal shares after V-shape recovery
- **Test Failure**: Enhanced consistently had MORE shares (7337 vs 7221)
- **Investigation**: Not a bug—this IS volatility alpha! Enhanced buys low, sells high, retains more shares
- **Fix**: Changed test assertions from `==` to `>=` to verify correct economic behavior

Without tests, we might have "fixed" the algorithm to match wrong expectations, destroying the volatility harvesting feature!

**Testing Best Practices**:
```python
# GOOD: Test verifies economic invariants
def test_v_shape_symmetric(self):
    """Enhanced accumulates shares during dip, retains MORE after recovery."""
    sd_full, ath_only, stack_qty, stack_empty = run_test_comparison(
        price_path=[...],  # 100→200→100→200
        rebalance_pct=10.0,
        profit_sharing_pct=50.0
    )
    
    # Enhanced MUST have more shares (volatility harvesting)
    assert sd_full >= ath_only, \
        f"Enhanced should retain more: SD={sd_full}, ATH={ath_only}"
    
    # Stack quantity accounts for extra shares
    share_diff = sd_full - ath_only
    assert stack_qty == share_diff, \
        f"Stack ({stack_qty}) should equal difference ({share_diff})"
```

**What to Test**:
- **Happy Path**: Normal expected behavior
- **Edge Cases**: Zero quantities, empty datasets, boundary values
- **Economic Invariants**: Relationships that MUST hold (alpha ≥ 0, stack integrity)
- **Error Conditions**: Invalid inputs should raise appropriate exceptions
- **Regression**: Once you fix a bug, add a test so it never returns

**Test Organization**:
```python
class TestBuybackStackVShape:
    """Test V-shape price patterns (100→200→100→200).
    
    Expected behavior:
    - Enhanced buys during dip, sells during recovery
    - Retains MORE shares than ATH-only (volatility harvesting)
    - Buyback stack tracks the share difference
    """
    
    def test_symmetric_recovery(self): ...
    def test_exceeds_previous_ath(self): ...
    def test_multiple_cycles(self): ...
```

**Trust Through Testing**:
- Don't trust your calculations—**verify them with tests**
- Don't assume edge cases work—**test them explicitly**
- Don't believe the algorithm is correct—**prove it with comprehensive tests**

Tests transform hope into certainty. They're the difference between "I think this works" and "I know this works."


## Code Review Checklist

Before committing code, verify:

- [ ] **Types**: All functions have complete type annotations
- [ ] **Docstrings**: Public functions have Google/NumPy style docstrings
- [ ] **Comments**: Complex logic explained with terse, accurate comments
- [ ] **Length**: Functions are short (5-30 lines typical, max ~50)
- [ ] **Purity**: Functions prefer explicit parameters over hidden state
- [ ] **Side Effects**: Mutations are minimized and clearly documented
- [ ] **Tests**: New functions have unit tests covering happy path, edge cases, and invariants
- [ ] **Test Coverage**: Tests verify expected behavior, not just "it doesn't crash"
- [ ] **Naming**: Variable/function names are descriptive and unambiguous


## Rationale

These principles emerged from real-world experience with large codebases:

1. **Functional style** reduces bugs by minimizing state-related errors
2. **Static typing** catches errors at compile-time instead of production
3. **Short functions** reduce cognitive load and improve maintainability
4. **Dense comments** preserve intent for future maintainers (including yourself)
5. **Immutability** prevents entire classes of concurrency and mutation bugs
6. **Comprehensive tests** catch silent calculation errors that you'd never notice otherwise

The goal is **code that is easy to understand, modify, and verify correctness**. These practices have proven effective across thousands of production systems.

**Special Note on Testing**: In financial/mathematical code, silent errors are the most dangerous. A bug that crashes is obvious; a bug that produces slightly wrong numbers can go undetected for years. Tests are your only defense against this—they transform uncertain calculations into verified facts.


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

## Related Documentation

For information about the investment strategy and financial theory behind the Synthetic Dividend algorithm, see [INVESTING_THEORY.md](INVESTING_THEORY.md).

---

**Last Updated**: October 2025
**Contributors**: Project maintainers and code reviewers
