# Price Data Cache

This directory contains cached historical price data from Yahoo Finance.

## Purpose

- **Offline Operation**: Run backtests without hitting Yahoo Finance API
- **Rate Limit Avoidance**: Avoid 403 errors and rate limiting
- **Faster Testing**: Instant data access from cache
- **CI/CD**: Tests run reliably without external dependencies

## Cache Files

For each ticker (e.g., `NVDA`):
- `NVDA.pkl` - Binary pickle format (fast loading)
- `NVDA.csv` - Human-readable CSV format
- `NVDA_dividends.pkl` - Dividend/distribution history
- `NVDA_dividends.csv` - Dividend CSV

## Populating the Cache

### Option 1: Run Population Script (Recommended)

When you have reliable Yahoo Finance access:

```bash
# Populate with 5 years of data for all common tickers
python scripts/populate_cache.py

# Populate with 10 years
python scripts/populate_cache.py --years 10

# Populate specific tickers only
python scripts/populate_cache.py --tickers NVDA BTC-USD SPY

# List all default tickers
python scripts/populate_cache.py --list
```

### Option 2: Manual Population

The cache is populated automatically when you run backtests. The first run will fetch from Yahoo and cache for future use.

### Option 3: Pre-Populated Cache (Future)

We plan to provide a downloadable pre-populated cache archive for common tickers.

## Common Tickers

The population script includes 22 commonly used tickers:

**Growth Stocks**: NVDA, MSTR, PLTR, SHOP, GOOG
**Small Cap**: SOUN, APP
**Crypto**: BTC-USD, ETH-USD
**Index ETFs**: SPY, VOO, QQQ, DIA, IWM
**Commodities**: GLD, GLDM, SLV
**Risk-Free**: BIL, ^IRX
**Sectors**: XLK, XLF, XLE

## How It Works

The `YahooAssetProvider` automatically:

1. Checks if cache exists and covers requested date range
2. If yes: returns filtered data from cache (fast!)
3. If no: downloads from Yahoo and saves to cache
4. Next request: uses cache (offline!)

## Troubleshooting

**Yahoo Finance Rate Limits**:
- Yahoo may temporarily block requests (403 errors)
- Wait a few minutes and try again
- Use VPN if persistent issues
- Consider running population script overnight

**Missing Data**:
- Some tickers may not have full 5-year history
- IPO dates vary (e.g., SOUN listed in 2022)
- Crypto data availability varies by exchange

**Cache Invalidation**:
- Delete `.pkl` and `.csv` files to force re-download
- Cache automatically updates if requested range exceeds cached range

## Notes

- Cache is gitignored (too large for repo)
- Test data in `testdata/` is committed (small, specific test cases)
- Cache grows over time as new tickers are requested
- Typical cache size: ~5-10 MB per ticker for 5 years

## Future Improvements

- [ ] Provide downloadable pre-populated cache archive
- [ ] Automatic cache refresh for recent data
- [ ] Cache compression for storage efficiency
- [ ] Multi-source support (Alpha Vantage, Polygon, etc.)

## Getting Pre-Populated Cache (Workaround for Rate Limits)

If you're experiencing Yahoo Finance rate limits, here are alternatives:

### Option A: Run Script During Off-Peak Hours
Yahoo rate limits are less strict during off-peak hours (late night, weekends):
```bash
python scripts/populate_cache.py --years 5
```

### Option B: Populate Incrementally
Cache a few tickers at a time to avoid rate limits:
```bash
python scripts/populate_cache.py --tickers NVDA SPY
# Wait a few minutes...
python scripts/populate_cache.py --tickers BTC-USD GLDM
# Wait a few minutes...
python scripts/populate_cache.py --tickers VOO QQQ
```

### Option C: Share Cache Between Machines
Copy the `cache/` directory from a machine with good Yahoo access:
```bash
# On machine with good access:
tar czf cache-backup.tar.gz cache/*.pkl cache/*.csv

# Transfer and extract on target machine:
tar xzf cache-backup.tar.gz
```

### Option D: Use Test Data
For quick testing, use the smaller test data in `testdata/`:
```python
df = pd.read_csv("testdata/NVDA.csv", index_col=0, parse_dates=True)
```
