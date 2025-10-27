# Asset Provider Coverage Analysis

Analysis of which asset classes work with Yahoo Finance vs. requiring alternative APIs.

## Yahoo Finance Coverage (via yfinance library)

### ✅ WORKS - No Additional API Needed

#### 1. **Mutual Funds** ✅
- **Example**: `VFINX` (Vanguard 500 Index Fund)
- **Status**: WORKS - daily NAV prices available
- **Quirks**: 
  - Volume always 0 (mutual funds trade at NAV, not on exchange)
  - Only one price per day (NAV calculated after market close)
  - Has `Capital Gains` column (mutual fund specific)
- **Dividends**: Available via `.dividends` property
- **Provider**: YahooAssetProvider ✅

#### 2. **Cryptocurrency** ✅
- **Example**: `AVNT-USD`, `BTC-USD`, `ETH-USD`
- **Status**: WORKS - extensive crypto coverage
- **Quirks**:
  - 24/7 trading (weekends have data)
  - Timezone is UTC (+00:00) vs. US Eastern for stocks
  - High volatility in OHLC spreads
- **Dividends**: None (crypto doesn't pay dividends)
- **Provider**: YahooAssetProvider ✅

#### 3. **Market Indexes (Total Return)** ✅
- **Example**: `^SP500TR` (S&P 500 Total Return)
- **Other indexes**: `^GSPC` (S&P 500 Price), `^DJI` (Dow Jones), `^IXIC` (NASDAQ)
- **Status**: WORKS - comprehensive index coverage
- **Note**: TR (Total Return) indexes include dividend reinvestment
- **Quirks**: Cannot trade indexes directly (use ETFs like VOO, SPY instead)
- **Provider**: YahooAssetProvider ✅
- **Use Case**: Benchmark comparison, not tradeable positions

#### 4. **Commodity Futures** ✅
- **Examples**: 
  - `GC=F` (Gold Futures)
  - `CL=F` (Crude Oil)
  - `SI=F` (Silver)
  - `HG=F` (Copper)
  - `NG=F` (Natural Gas)
- **Status**: WORKS - front-month futures contracts
- **Quirks**:
  - Futures roll over (contract expiration issues)
  - Gaps in data when contracts roll
  - Not suitable for long-term backtests without handling rollovers
  - Different trading hours than equities
- **Alternative**: Use commodity ETFs (GLD, USO, SLV) for easier backtesting
- **Provider**: YahooAssetProvider ✅ (with caveats)

#### 5. **OTC Markets** ✅
- **Example**: `BKYI` (BIO-key International - OTC)
- **Status**: WORKS - coverage for major OTC stocks
- **Quirks**:
  - Lower volume, wider spreads
  - Some very small OTC stocks may have gaps
  - Less reliable than exchange-listed stocks
- **Provider**: YahooAssetProvider ✅

#### 6. **ETFs** ✅
- **Examples**: `VOO`, `VTI`, `SPY`, `QQQ`, `GLD`, `BIL`
- **Status**: WORKS PERFECTLY - best asset class for Yahoo Finance
- **Why**: Traded on exchanges, high liquidity, comprehensive data
- **Dividends**: Available (quarterly/monthly distributions)
- **Provider**: YahooAssetProvider ✅

#### 7. **Foreign Stocks (with ADR)** ✅
- **Examples**: `TSM` (Taiwan Semi ADR), `BABA` (Alibaba ADR)
- **Status**: WORKS - ADRs trade on US exchanges
- **Provider**: YahooAssetProvider ✅

#### 8. **Bonds (via ETFs)** ✅
- **Examples**: `TLT` (20+ Year Treasury), `AGG` (Aggregate Bond)
- **Status**: WORKS - bond ETFs widely available
- **Note**: Individual bonds NOT available, use ETFs
- **Provider**: YahooAssetProvider ✅

---

## ❌ REQUIRES ALTERNATIVE APIs

### 1. **Individual Bonds**
- **Examples**: CUSIP-based bonds, US Treasuries (individual securities)
- **Yahoo Status**: NOT AVAILABLE
- **Alternative APIs**:
  - **FINRA/TRACE**: Corporate bond transaction data (requires registration)
  - **TreasuryDirect API**: US government bonds (free, REST API)
  - **Bloomberg API**: Comprehensive bond data (expensive, $$$)
  - **Interactive Brokers API**: Bond prices via brokerage (requires account)
- **Workaround**: Use bond ETFs (TLT, AGG, BND) instead
- **Provider Needed**: `BondAssetProvider` (future enhancement)

### 2. **Foreign Stocks (Direct, Non-ADR)**
- **Examples**: Japanese stocks on TSE, European stocks on LSE/Euronext
- **Yahoo Status**: LIMITED - some work with exchange suffix (e.g., `7203.T` for Toyota)
- **Quirks**: 
  - Inconsistent coverage
  - Currency conversion issues
  - Timezone complexities
- **Alternative APIs**:
  - **Alpha Vantage**: Global stock data (free tier available)
  - **Polygon.io**: Multi-exchange support (free tier available)
  - **IEX Cloud**: International stocks (limited free tier)
- **Workaround**: Use ADRs or country ETFs (EWJ, EWG, etc.)
- **Provider Needed**: Could extend YahooAssetProvider or create `InternationalAssetProvider`

### 3. **Options**
- **Yahoo Status**: PARTIALLY - option chains available but awkward API
- **Issues**: 
  - Expiration handling complex
  - Greeks not provided
  - Historical option prices unreliable
- **Alternative APIs**:
  - **CBOE DataShop**: Official options data (paid)
  - **Interactive Brokers API**: Real-time options via brokerage
  - **Tradier API**: Options market data (REST API, free tier)
  - **TDAmeritrade API**: Options chains (free with account)
- **Provider Needed**: `OptionsAssetProvider` (complex, future enhancement)

### 4. **Real Estate (Direct Properties)**
- **Yahoo Status**: NOT AVAILABLE
- **Alternative APIs**:
  - **Zillow API**: Residential real estate (limited access)
  - **Redfin API**: Property data (scrapers available, no official REST API)
  - **ATTOM Data**: Property analytics (paid)
- **Workaround**: Use REITs (VNQ, SCHH) for real estate exposure
- **Provider Needed**: Not practical for backtesting

### 5. **Private Equity / Unlisted Companies**
- **Yahoo Status**: NOT AVAILABLE (by definition)
- **Alternative**: No public APIs
- **Workaround**: Manual data entry or use publicly-traded PE firms
- **Provider Needed**: `ManualAssetProvider` (user-supplied CSV data)

### 6. **Commodities (Spot Prices, not Futures)**
- **Examples**: Physical gold, silver, oil (spot prices)
- **Yahoo Status**: NOT DIRECTLY - futures available but not true spot
- **Alternative APIs**:
  - **Quandl/Nasdaq Data Link**: Commodity spot prices (free tier)
  - **Metal Prices API**: Precious metals (free)
  - **EIA API**: Oil/gas spot prices (free, government data)
  - **World Bank Commodity Prices**: Historical commodity data (free)
- **Workaround**: Use commodity ETFs (GLD, SLV) or futures (GC=F)
- **Provider Needed**: `CommodityAssetProvider` using Quandl or similar

### 7. **Money Market Funds (some)**
- **Yahoo Status**: MIXED - some work (e.g., `VUSXX`), others don't
- **Alternative**: Most work, but $1.00 stable NAV makes them similar to cash
- **Workaround**: Use `CashAssetProvider` for USD, or BIL (1-3 month T-bill ETF)
- **Provider**: YahooAssetProvider (mostly works) or CashAssetProvider (for simplicity)

---

## Recommended Provider Architecture

```python
# Current (implemented):
AssetRegistry.register("USD", CashAssetProvider, priority=1)
AssetRegistry.register("*", YahooAssetProvider, priority=9)

# Future Extensions:
AssetRegistry.register("*.T", YahooAssetProvider, priority=2)     # Japanese stocks
AssetRegistry.register("*.L", YahooAssetProvider, priority=2)     # London stocks
AssetRegistry.register("CUSTOM-*", ManualAssetProvider, priority=3)  # User-supplied data
AssetRegistry.register("BOND-*", BondAssetProvider, priority=3)   # Individual bonds
AssetRegistry.register("OPT-*", OptionsAssetProvider, priority=3) # Options contracts
```

---

## Summary & Recommendations

### **Use Yahoo Finance (YahooAssetProvider) for:**
✅ US stocks & ETFs (best coverage)
✅ Mutual funds (VFINX works great)
✅ Crypto (BTC-USD, ETH-USD, AVNT-USD)
✅ Market indexes (^SP500TR for benchmarks)
✅ OTC stocks (most work)
✅ ADRs (foreign stocks via US exchanges)
✅ Commodity ETFs (GLD, SLV, USO instead of futures)

### **Avoid or Use Alternatives for:**
❌ Individual bonds → Use Treasury Direct API or bond ETFs
❌ Foreign stocks (direct) → Use ADRs or Alpha Vantage
❌ Options → Use Tradier/TDAmeritrade APIs
❌ Commodity spot prices → Use Quandl or commodity ETFs
❌ Money market funds → Use CashAssetProvider or BIL ETF

### **Best Practice for Your Use Cases:**

1. **Mutual Funds**: ✅ Yahoo works (`VFINX`, `VTSAX`, etc.)
2. **Obscure Crypto**: ✅ Yahoo works (`AVNT-USD`)
3. **S&P 500 TR**: ✅ Yahoo works (`^SP500TR`) - but prefer `VOO` for tradeable backtest
4. **Commodities**: 
   - With ETF: ✅ Yahoo (`GLD`, `SLV`, `DBC`)
   - Spot prices: ❌ Need Quandl/World Bank API
   - Futures: ⚠️ Yahoo works (`GC=F`) but has rollover issues
5. **OTC Markets**: ✅ Yahoo works (major OTC stocks like `BKYI`)

**Recommended**: Stick with Yahoo Finance via YahooAssetProvider for 95% of use cases. It's free, reliable, and covers all major asset classes via ETFs/ADRs.

For niche needs (individual bonds, true commodity spots), add specialized providers when needed via the registry pattern.
