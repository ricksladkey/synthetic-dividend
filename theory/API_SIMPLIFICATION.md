# API Simplification Analysis

**Status**: INVESTIGATION  
**Date**: October 27, 2025

## Current State: What We Have

### 1. Yahoo Finance Layer (`src/data/fetcher.py`, 347 lines)

**HistoryFetcher class** - Complex caching mechanism:

```python
class HistoryFetcher:
    def __init__(self, cache_dir: Optional[str] = None)
    def get_history(ticker, start_date, end_date) -> pd.DataFrame  # OHLC
    def get_dividends(ticker, start_date, end_date) -> pd.Series   # Dividends
    def get_multiple_histories(tickers, start, end) -> Dict[str, DataFrame]
    def get_multiple_dividends(tickers, start, end) -> Dict[str, Series]
    
    # Internal implementation (hacky):
    def _cache_path(ticker) -> str
    def _dividend_cache_path(ticker) -> str
    def _load_cache(ticker) -> Optional[DataFrame]
    def _save_cache(ticker, df)
    def _load_dividend_cache(ticker) -> Optional[Series]
    def _save_dividend_cache(ticker, series)
    def _download(ticker, start, end) -> DataFrame
    def _download_dividends(ticker) -> Series
```

**Issues**:
- Pickle-based persistence (binary, opaque, version-sensitive)
- Cache extension logic (complex merge/dedup dance)
- Separate caching for OHLC vs dividends
- yfinance quirks baked in (1-day buffers, date handling)
- Optional dependency handling (yf may be None)
- Silent failure modes (empty DataFrames vs exceptions)

### 2. Stock Model (`src/models/stock.py`, 39 lines)

**Stock dataclass** - Mutable position tracking:

```python
@dataclass
class Stock:
    ticker: str
    quantity: int = 0
    
    def get_ticker() -> str
    def get_quantity() -> int
    def calculate_investment_value(current_price) -> float
    def value_series(price_series) -> Series
    def buy(amount: int)
    def sell(amount: int)
    def to_dict() -> dict
    def __str__() -> str
```

**Issues**:
- Mutable state (quantity changes in place)
- Redundant accessors (get_ticker, get_quantity)
- Type coercion everywhere (int(self.quantity))
- Limited responsibility (just ticker + quantity)
- Doesn't fit our new architecture (Holding/Portfolio/Account)

### 3. Current Usage Pattern

**In backtest engine** (`src/models/backtest.py`):

```python
# User must:
1. Create HistoryFetcher()
2. Call get_history(ticker, start, end) -> DataFrame
3. Call get_dividends(ticker, start, end) -> Series
4. Pass both to run_portfolio_backtest()
5. Handle empty DataFrames, cache invalidation, etc.
```

**In GUI** (`src/gui/layout.py`):

```python
self.fetcher = HistoryFetcher()
# Later:
df = self.fetcher.get_history(ticker, start, end)
divs = self.fetcher.get_dividends(ticker, start, end)
```

## What We Actually Need

### Asset Data API (Conceptual):

For algorithmic backtesting, we need:

1. **Price history** (OHLC) - daily bars for range
2. **Dividend history** - ex-dates and amounts for range
3. **Caching** - don't re-download on every run
4. **Multi-asset** - fetch multiple tickers efficiently

That's it. No complex merging, no pickle files, no quirks leaking out.

### Position Tracking (Conceptual):

We already have the right model:
- **Transaction** - immutable record of what happened
- **Holding** - collection of transactions, lot tracking
- **Portfolio** - collection of holdings
- **Account** - portfolio + debt

**Stock.py is obsolete** - it predates our Transaction/Holding architecture.

## Design Goals

### For Asset API:

1. **Simple interface**: `asset.get_prices(start, end)`, `asset.get_dividends(start, end)`
2. **Clean persistence**: JSON or CSV (human-readable), not pickle
3. **Explicit errors**: Don't silently return empty DataFrames
4. **No leaky abstractions**: yfinance quirks hidden inside implementation
5. **Single responsibility**: One cache per ticker, handles both OHLC + dividends

### For Position Model:

1. **Use what we have**: Transaction/Holding/Portfolio/Account
2. **Remove Stock.py**: Doesn't fit our architecture
3. **Immutable operations**: Transactions are records, not state changes

## Proposed Simplification

### Option A: Minimal Asset Class

```python
class Asset:
    """Single ticker, handles both prices and dividends."""
    
    def __init__(self, ticker: str, cache_dir: str = "cache"):
        self.ticker = ticker
        self.cache_path = f"{cache_dir}/{ticker}.json"
    
    def get_prices(self, start: date, end: date) -> pd.DataFrame:
        """OHLC data for range. Downloads if needed, extends cache."""
        # Load cache (JSON)
        # Check range coverage
        # Download missing data
        # Update cache
        # Return requested range
    
    def get_dividends(self, start: date, end: date) -> pd.Series:
        """Dividend/interest history. Downloads once, caches forever."""
        # Same cache file has both OHLC + dividends
        # Dividends rarely change (historical), so clone-once strategy works
```

**Benefits**:
- One class, one ticker, one cache file
- JSON format (human-readable, version-stable)
- Prices and dividends together (conceptually correct)
- No yfinance leakage (buffers/quirks internal)

### Option B: Keep HistoryFetcher, Fix Persistence

```python
class HistoryFetcher:
    """Multi-ticker fetcher with clean JSON caching."""
    
    def get_asset_data(self, ticker: str, start: date, end: date) -> AssetData:
        """Returns OHLC + dividends in one call."""
        # Load from {ticker}.json (not .pkl)
        # Extend if needed
        # Return structured data
```

**Benefits**:
- Less code churn (keep existing API)
- Fix persistence layer (JSON not pickle)
- Combine OHLC + dividends fetch

## Design Decisions ✅

### 1. Dual Caching Strategy

**Pickle for speed** (internal, backtest performance):
- Fast serialization/deserialization
- Preserves DataFrame dtypes perfectly
- Used by algorithm execution

**CSV for transparency** (human inspection, Excel):
- Plain text, version control friendly
- Excel/LibreOffice can open directly
- Auditable, debuggable
- Export on cache write

**Implementation**:
```python
# Save cache:
df.to_pickle(f"{ticker}.pkl")     # Fast internal format
df.to_csv(f"{ticker}.csv")        # Human-readable export

# Load cache (prefer fast):
df = pd.read_pickle(f"{ticker}.pkl")
```

**Philosophy**: "Computers are fast, so tolerate the overhead for dual format."

### 2. Simple Download Strategy

**Current (complex)**:
- Check if range covered
- Download left extension if start < cache_min
- Download right extension if end > cache_max
- Merge, deduplicate, save

**New (simple)**:
- Cache miss or range not covered? **Download full range requested**
- Don't try to be clever with extensions
- Cache is just memoization, not incremental database

**Rationale**: Computers are fast. Downloading 5 years vs extending 1 month takes same time.

### 3. Interface Design

**One Asset per ticker** (clean encapsulation):

```python
class Asset:
    def __init__(self, ticker: str, cache_dir: str = "cache")
    
    def get_prices(self, start: date, end: date) -> pd.DataFrame:
        """OHLC data. Fast path: pickle cache. Miss: download, save both formats."""
    
    def get_dividends(self, start: date, end: date) -> pd.Series:
        """Dividend/interest history. Same cache file, different columns."""
    
    def clear_cache(self):
        """Remove both .pkl and .csv cache files."""
```

**Benefits**:
- One ticker = one Asset instance
- Prices + dividends together (conceptually correct)
- Cache files: `{ticker}.pkl` (fast) + `{ticker}.csv` (readable)

### 4. Stock.py Fate

**REMOVE** - obsolete, replaced by:
- `Transaction` - immutable buy/sell record
- `Holding` - lot tracking, FIFO/LIFO
- `Portfolio` - collection of holdings
- `Account` - portfolio + debt

Stock.py was pre-architecture. We've moved beyond it.

### 5. Error Handling

**Explicit exceptions** (fail fast):
- `ticker not found` → raise ValueError (don't return empty DataFrame)
- `yfinance unavailable` → raise RuntimeError at __init__ time
- `cache corrupt` → log warning, re-download, don't silently fail

**Philosophy**: Silent failures hide bugs. Explicit errors surface problems.

## Implementation Plan

### Phase 1: New Asset Class ✅

Create `src/data/asset.py`:

```python
class Asset:
    """Single ticker data provider with dual-format caching.
    
    Cache files:
    - {ticker}.pkl - Fast binary format for backtests
    - {ticker}.csv - Human-readable for Excel/inspection
    
    Both files written on cache save, pickle preferred for reads.
    """
    
    def __init__(self, ticker: str, cache_dir: str = "cache"):
        self.ticker = ticker.upper()
        self.cache_dir = cache_dir
        self.pkl_path = f"{cache_dir}/{self.ticker}.pkl"
        self.csv_path = f"{cache_dir}/{self.ticker}.csv"
        
        # Fail fast if yfinance not available
        if yf is None:
            raise RuntimeError("yfinance not installed")
    
    def get_prices(self, start: date, end: date) -> pd.DataFrame:
        """OHLC data for date range.
        
        Strategy:
        1. Try load from pickle cache
        2. If miss or incomplete: download full range
        3. Save both pkl + csv
        4. Return requested range
        """
        cached = self._load_pickle_cache()
        
        if self._cache_covers_range(cached, start, end):
            return self._filter_range(cached, start, end)
        
        # Cache miss or incomplete: download full range
        df = self._download_ohlc(start, end)
        self._save_dual_cache(df)
        return df
    
    def get_dividends(self, start: date, end: date) -> pd.Series:
        """Dividend/interest history.
        
        Strategy: Download complete dividend history once, cache forever.
        Dividends are immutable (historical) so no incremental updates needed.
        """
        cached_divs = self._load_dividend_cache()
        
        if cached_divs is not None:
            return self._filter_dividends(cached_divs, start, end)
        
        # Download complete dividend history
        divs = self._download_dividends()
        self._save_dividend_cache(divs)
        return self._filter_dividends(divs, start, end)
    
    def _save_dual_cache(self, df: pd.DataFrame):
        """Save both pickle (fast) and CSV (readable)."""
        df.to_pickle(self.pkl_path)
        df.to_csv(self.csv_path)
    
    def _load_pickle_cache(self) -> Optional[pd.DataFrame]:
        """Load from fast pickle cache."""
        if os.path.exists(self.pkl_path):
            return pd.read_pickle(self.pkl_path)
        return None
```

### Phase 2: Migrate HistoryFetcher Usages

**Backtest engine** - becomes simpler:
```python
# OLD:
fetcher = HistoryFetcher()
df = fetcher.get_history(ticker, start, end)
divs = fetcher.get_dividends(ticker, start, end)

# NEW:
asset = Asset(ticker)
df = asset.get_prices(start, end)
divs = asset.get_dividends(start, end)
```

**Multi-ticker support** - explicit loop:
```python
# OLD:
fetcher.get_multiple_histories([tickers], start, end)

# NEW:
data = {ticker: Asset(ticker).get_prices(start, end) for ticker in tickers}
```

### Phase 3: Remove Stock.py

- Delete `src/models/stock.py`
- Update imports to use Portfolio/Holding
- Remove any Stock references in tests/examples

### Phase 4: Keep HistoryFetcher as Compatibility Shim (Optional)

```python
class HistoryFetcher:
    """Legacy compatibility wrapper around Asset class."""
    
    def get_history(self, ticker, start, end):
        return Asset(ticker, self.cache_dir).get_prices(start, end)
    
    def get_dividends(self, ticker, start, end):
        return Asset(ticker, self.cache_dir).get_dividends(start, end)
```

Allows gradual migration without breaking existing code.

## Next Steps

1. ✅ **Design decisions documented** (this file)
2. **Create `src/data/asset.py`** - Clean Asset class with dual caching
3. **Test dual caching** - Verify pkl + csv both written/readable
4. **Migrate one usage** - Update backtest.py to use Asset
5. **Validate performance** - Confirm dual caching doesn't slow backtests
6. **Remove Stock.py** - Clean up obsolete model
7. **Update documentation** - Reflect new Asset API

---

**Insight**: The complexity comes from trying to be too clever with caching. "Download what you need" is simpler than "extend cache left/right with merge/dedup logic".

**Philosophy**: The right abstraction is **Asset** (one ticker, everything about it). Current design splits OHLC/dividends/caching across too many concerns.
