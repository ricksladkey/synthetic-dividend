# Test Data Directory

This directory contains historical price data snapshots for offline testing and CI.

## Purpose

- **CI Testing**: Enable tests to run without network access
- **Deterministic Tests**: Known data produces predictable results
- **Fast Execution**: No network I/O delays

## Data Format

Each ticker has its own CSV file: `{TICKER}.csv`

CSV format matches Yahoo Finance export:
```
Date,Open,High,Low,Close,Adj Close,Volume
2020-01-02,323.94,326.89,323.62,325.34,318.77,50128300
...
```

Dividend files (optional): `{TICKER}_dividends.csv`
```
Date,Dividend
2020-03-20,1.32
...
```

## Data Integrity

⚠️ **Important**: Files in this directory are committed test data and should never be modified by the application. The `StaticAssetProvider` only reads from these files - it does not write to them. If you find these files being modified during testing, this indicates a bug in the caching logic.

## Available Data

- **SPY.csv**: S&P 500 ETF (2020-2024) - Primary test asset

## Usage

The `StaticAssetProvider` automatically loads data from this directory when available.

```python
from src.data.asset import Asset
from src.data.asset_provider import AssetRegistry
from src.data.static_provider import StaticAssetProvider

# Register static provider with high priority (lower number = higher priority)
AssetRegistry.register("SPY", StaticAssetProvider, priority=0)

# Now Asset("SPY") uses committed testdata/SPY.csv instead of network
asset = Asset("SPY")
prices = asset.get_prices(date(2020, 1, 2), date(2020, 12, 31))
```

## Adding New Test Data

To add data for a new ticker:

1. Download historical data as CSV from Yahoo Finance
2. Save as `testdata/{TICKER}.csv`
3. Keep file size reasonable (few years max)
4. Commit to repository

Example download URL:
```
https://finance.yahoo.com/quote/SPY/history?period1=1577934000&period2=1735689600
```

## CI Configuration

Tests automatically use static data when `testdata/{TICKER}.csv` exists.
No special configuration needed - the provider system handles fallback automatically.
