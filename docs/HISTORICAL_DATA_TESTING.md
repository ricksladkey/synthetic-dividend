# Historical Data for Offline Testing (Issue #9)

## Overview

This document explains the approach for supporting historical data and tests without network access, addressing **Issue #9** with an immediate focus on **CI testing**.

## Problem Statement

Previously, tests required network access to fetch data from Yahoo Finance via `yfinance`. This caused several issues:

1. **CI Failures**: Tests fail when network is unavailable or rate-limited
2. **Slow Tests**: Network I/O adds significant overhead
3. **Non-deterministic**: Remote data can change, causing test flakiness
4. **Privacy**: May expose test activity to external services

## Solution Architecture

We've implemented a **provider-based architecture** that supports multiple data sources with priority-based fallback:

```
Priority 0: StaticAssetProvider (committed CSV files in testdata/)
Priority 1: CashAssetProvider (for USD only)
Priority 9: YahooAssetProvider (live network data)
```

### Key Components

#### 1. StaticAssetProvider (`src/data/static_provider.py`)

A new asset provider that loads historical price data from committed CSV files:

```python
from src.data.asset import Asset
from src.data.asset_provider import AssetRegistry
from src.data.static_provider import StaticAssetProvider

# Register static provider with high priority
AssetRegistry.register("SPY", StaticAssetProvider, priority=0)

# Now Asset("SPY") uses testdata/SPY.csv instead of network
asset = Asset("SPY")
prices = asset.get_prices(date(2020, 1, 2), date(2020, 12, 31))
```

**Features:**
- Loads from `testdata/{TICKER}.csv`
- Returns empty DataFrame if file doesn't exist (allows fallback)
- Supports dividend files: `testdata/{TICKER}_dividends.csv`
- No network access required
- Deterministic results

#### 2. Test Data Directory (`testdata/`)

Contains committed historical price snapshots for key test assets:

```
testdata/
├── README.md # Documentation
├── SPY.csv # S&P 500 ETF (2020-2024)
└── (more to be added)
```

CSV format matches Yahoo Finance export:
```csv
Date,Open,High,Low,Close,Adj Close,Volume
2020-01-02,323.94,326.89,323.62,325.34,318.77,50128300
...
```

#### 3. CI Auto-Configuration (`tests/conftest.py`)

Pytest fixture automatically registers StaticAssetProvider in CI environments:

```python
@pytest.fixture(scope="session", autouse=True)
def setup_static_provider_for_ci():
 """Auto-register StaticAssetProvider when running in CI."""
 if os.getenv("CI") == "true":
 AssetRegistry.register("*", StaticAssetProvider, priority=0)
```

This runs automatically - **no test code changes needed!**

## Usage Patterns

### Pattern 1: CI Testing (Automatic)

Tests automatically use static data in CI:

```python
def test_backtest():
 asset = Asset("SPY") # Uses testdata/SPY.csv in CI
 prices = asset.get_prices(date(2020, 1, 2), date(2020, 12, 31))
 # Test runs without network access
```

### Pattern 2: Local Development (Network Available)

Developers get fresh data from Yahoo Finance:

```python
def test_backtest():
 asset = Asset("SPY") # Uses YahooAssetProvider locally
 prices = asset.get_prices(date(2020, 1, 2), date(2020, 12, 31))
 # Gets live data, cached to cache/SPY.pkl
```

### Pattern 3: Explicit Static Data (Testing)

Force static data in specific tests:

```python
@pytest.fixture(autouse=True)
def use_static_data():
 AssetRegistry.register("SPY", StaticAssetProvider, priority=0)
 yield
 # cleanup...

def test_deterministic_behavior():
 asset = Asset("SPY") # Always uses testdata/SPY.csv
 prices = asset.get_prices(date(2020, 1, 2), date(2020, 12, 31))
 # Guaranteed same results every run
```

### Pattern 4: Mock Data (Unit Tests)

Use MockAssetProvider for synthetic test scenarios:

```python
def test_algorithm_logic():
 asset = Asset("MOCK-FLAT-100") # Flat $100 prices
 prices = asset.get_prices(date(2024, 1, 1), date(2024, 12, 31))
 # Perfect for testing edge cases
```

## Adding New Test Data

To add historical data for a new ticker:

1. **Download from Yahoo Finance:**
 ```
 https://finance.yahoo.com/quote/NVDA/history?period1=1577934000&period2=1735689600
 ```

2. **Save as CSV:**
 ```bash
 # Download and save to testdata/NVDA.csv
 curl "https://query1.finance.yahoo.com/v7/finance/download/NVDA?..." \
 -o testdata/NVDA.csv
 ```

3. **Commit to repository:**
 ```bash
 git add testdata/NVDA.csv
 git commit -m "Add NVDA test data (2020-2024)"
 ```

4. **Use in tests:**
 ```python
 asset = Asset("NVDA") # Now works offline in CI
 ```

## Design Principles

This implementation follows several key principles:

### 1. Minimal Code Changes

The provider architecture was **already present** in the codebase. We simply added a new provider - no changes to existing backtest code needed.

### 2. Backwards Compatible

Existing tests continue to work without modification:
- Local development: Uses network (YahooAssetProvider)
- CI environment: Uses static data (StaticAssetProvider)
- Both use same `Asset("SPY")` API

### 3. Fail Gracefully

StaticAssetProvider returns empty DataFrame if file missing:
```python
prices = asset.get_prices(...) # Returns empty if no testdata/TICKER.csv
if prices.empty:
 # Fall back to YahooAssetProvider automatically
```

### 4. Easy to Extend

Adding new test assets is straightforward:
1. Download CSV from Yahoo Finance
2. Save to `testdata/{TICKER}.csv`
3. Commit and push

### 5. Transparent Operation

Developers don't need to think about data sources:
- Tests "just work" in CI without network
- Local development gets fresh data as before
- Provider selection is automatic based on environment

## Benefits

### For CI/CD

- [OK] Tests run without network access
- [OK] No rate limiting or API failures
- [OK] Faster test execution (no network I/O)
- [OK] Deterministic results
- [OK] No external service dependencies

### For Developers

- [OK] Local development unchanged
- [OK] Can force static data for reproducibility
- [OK] Easy to add new test assets
- [OK] No special test setup needed

### For Testing

- [OK] Deterministic test data
- [OK] Known price ranges for assertions
- [OK] Can test historical scenarios exactly
- [OK] Fast test iteration

## Future Extensions

This foundation enables several future improvements:

### 1. More Test Assets

Add data for commonly tested tickers:
- `testdata/NVDA.csv` - Tech growth stock
- `testdata/VOO.csv` - Vanguard S&P 500
- `testdata/BTC-USD.csv` - Cryptocurrency
- `testdata/GLD.csv` - Gold commodity

### 2. Dividend Data

Add dividend files for income testing:
- `testdata/AAPL_dividends.csv`
- `testdata/VYM_dividends.csv`

### 3. Historical Scenarios

Create test datasets for specific market conditions:
- `testdata/SPY_2022_bear.csv` - Bear market
- `testdata/SPY_2020_crash.csv` - COVID crash
- `testdata/NVDA_2023_bull.csv` - Bull run

### 4. Test Data Management

Tools to maintain test data:
- Script to update test data from Yahoo Finance
- Validation to ensure data quality
- Documentation of which scenarios each file covers

### 5. Compressed Storage

For larger datasets, use compression:
- `testdata/SPY.csv.gz` - Compressed CSV
- Update StaticAssetProvider to read .gz files

## Testing the Implementation

### Verify Static Provider Works

```bash
# Run demo script
python demo_static_provider.py

# Should output:
# [OK] StaticAssetProvider loaded 111 rows for SPY
# ...
# [OK] StaticAssetProvider working correctly!
```

### Run Static Provider Tests

```bash
# Test the provider itself
pytest tests/test_static_provider.py -v

# Should see:
# test_loads_spy_data PASSED
# test_filters_date_range PASSED
# test_no_network_required PASSED
# ...
```

### Simulate CI Environment

```bash
# Set CI flag to activate static provider
export CI=true
pytest tests/ -v

# Tests should run using testdata/ files
```

## Conclusion

This implementation provides a **minimal, elegant solution** to Issue #9:

- [OK] Demonstrates tech for historical data without network
- [OK] Enables CI testing without internet access
- [OK] Maintains backwards compatibility
- [OK] Easy to extend with more test data
- [OK] Follows existing code patterns

The foundation is in place - adding more test assets is now straightforward and mechanical.
