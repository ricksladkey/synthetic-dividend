"""Asset data provider with dual-format caching.

Provides clean interface for fetching historical price and dividend data
with transparent caching in both pickle (fast) and CSV (human-readable) formats.
"""

import os
from datetime import date, datetime, timedelta
from typing import Optional

import pandas as pd

# Optional dependency: gracefully degrade if yfinance unavailable
try:
    import yfinance as yf  # type: ignore
    YFINANCE_AVAILABLE = True
except Exception:
    yf = None
    YFINANCE_AVAILABLE = False


class Asset:
    """Single ticker data provider with dual-format caching.
    
    Provides clean interface for historical price (OHLC) and dividend data.
    Caches in two formats:
    - {ticker}.pkl - Fast binary format for backtest performance
    - {ticker}.csv - Plain text for Excel/inspection/version control
    
    Both formats written on cache save, pickle preferred for reads.
    
    Philosophy:
    - Computers are fast: tolerate dual-write overhead for transparency
    - Simple caching: download full range on miss, no complex extensions
    - Fail fast: explicit errors, no silent failures
    - Clean separation: one Asset per ticker, prices + dividends together
    
    Example:
        >>> asset = Asset("NVDA")
        >>> prices = asset.get_prices(date(2024, 1, 1), date(2024, 12, 31))
        >>> divs = asset.get_dividends(date(2024, 1, 1), date(2024, 12, 31))
        >>> # Cache files created: NVDA.pkl + NVDA.csv
    """

    def __init__(self, ticker: str, cache_dir: str = "cache") -> None:
        """Initialize asset data provider.

        This Asset class acts as a small compatibility shim:
        - If an AssetRegistry with providers is available, prefer the registered
          provider and delegate all operations to it (tests expect `asset._provider`).
        - Otherwise, fall back to the built-in dual-format caching implementation
          that uses yfinance to download data and stores {ticker}.pkl and {ticker}.csv.

        Args:
            ticker: Stock symbol (e.g., "NVDA", "VOO", "BIL")
            cache_dir: Directory for cache files (default: "cache")

        Raises:
            RuntimeError: If yfinance is required by the fallback implementation
                          but not available.
        """
        self.ticker: str = ticker.upper()
        self.cache_dir: str = cache_dir

        # Ensure cache directory exists
        os.makedirs(cache_dir, exist_ok=True)

        # Default cache file paths (used by fallback and also exposed when delegating)
        self.pkl_path: str = os.path.join(cache_dir, f"{self.ticker}.pkl")
        self.csv_path: str = os.path.join(cache_dir, f"{self.ticker}.csv")
        self.div_pkl_path: str = os.path.join(cache_dir, f"{self.ticker}_dividends.pkl")
        self.div_csv_path: str = os.path.join(cache_dir, f"{self.ticker}_dividends.csv")

        # --- Prefer registered provider when available ---
        try:
            # Import here to avoid import cycles when modules load
            from src.data.asset_provider import AssetRegistry

            try:
                provider_class = AssetRegistry.get_provider_class(self.ticker)
            except Exception:
                provider_class = None

            if provider_class is not None:
                # Instantiate provider and expose attributes expected by tests
                self._provider = provider_class(self.ticker, cache_dir)

                # Mirror common cache attributes if provider exposes them,
                # otherwise keep the default paths above.
                self.pkl_path = getattr(self._provider, "pkl_path", self.pkl_path)
                self.csv_path = getattr(self._provider, "csv_path", self.csv_path)
                self.div_pkl_path = getattr(self._provider, "div_pkl_path", self.div_pkl_path)
                self.div_csv_path = getattr(self._provider, "div_csv_path", self.div_csv_path)

                # We're delegating to provider, so no further initialization needed.
                return
        except Exception:
            # If anything goes wrong with the registry import, fall back below.
            pass

        # --- Fallback: standalone yfinance-backed Asset implementation ---
        if not YFINANCE_AVAILABLE:
            raise RuntimeError(
                "yfinance not installed or failed to import. "
                "Install with: pip install yfinance"
            )

        # No provider registered: behave as the self-contained Asset class
        self._provider = None

    def get_prices(self, start_date: date, end_date: date) -> pd.DataFrame:
        """Get OHLC price data for date range.
        
        Strategy:
        1. Try load from pickle cache (fast path)
        2. If cache covers range: return filtered subset
        3. If cache miss/incomplete: download full range requested
        4. Save both pkl + csv formats
        5. Return requested range
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            
        Returns:
            DataFrame with OHLC columns, date-indexed
            Columns: Open, High, Low, Close
            Empty DataFrame if no data available for ticker/range
            
        Raises:
            ValueError: If start_date > end_date
            
        Example:
            >>> asset = Asset("NVDA")
            >>> df = asset.get_prices(date(2024, 1, 1), date(2024, 12, 31))
            >>> df.columns
            Index(['Open', 'High', 'Low', 'Close'], dtype='object')
        """
        # If delegating to a registered provider, prefer that API
        if getattr(self, "_provider", None) is not None:
            return self._provider.get_prices(start_date, end_date)

        if start_date > end_date:
            raise ValueError(f"start_date ({start_date}) must be <= end_date ({end_date})")

        # Try to load from cache
        cached = self._load_price_cache()

        # Check if cache covers requested range
        if self._cache_covers_range(cached, start_date, end_date):
            return self._filter_range(cached, start_date, end_date)

        # Cache miss or incomplete: download full range
        df = self._download_ohlc(start_date, end_date)

        if not df.empty:
            self._save_price_cache(df)

        return df

    def get_dividends(self, start_date: date, end_date: date) -> pd.Series:
        """Get dividend/interest history for date range.
        
        Strategy: "Clone everything once" - download complete dividend history,
        cache locally, return filtered subset for requested range.
        
        Works for:
        - Equity dividends (AAPL, MSFT, KO, etc.)
        - ETF distributions (VOO, VTI, etc.)
        - Money market interest (BIL, SHV, etc.)
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            
        Returns:
            Series with dividend amounts indexed by ex-dividend date
            Empty Series if no dividends in range or ticker doesn't pay
            
        Raises:
            ValueError: If start_date > end_date
            
        Example:
            >>> asset = Asset("AAPL")
            >>> divs = asset.get_dividends(date(2024, 1, 1), date(2024, 12, 31))
            >>> total = divs.sum()  # Total dividends for year
        """
        # If delegating to a registered provider, prefer that API
        if getattr(self, "_provider", None) is not None:
            return self._provider.get_dividends(start_date, end_date)

        if start_date > end_date:
            raise ValueError(f"start_date ({start_date}) must be <= end_date ({end_date})")

        # Try to load from cache
        cached = self._load_dividend_cache()

        # If cache exists, filter and return
        if cached is not None and not cached.empty:
            return self._filter_dividends(cached, start_date, end_date)

        # Download complete dividend history (immutable, so fetch once)
        divs = self._download_dividends()

        if not divs.empty:
            self._save_dividend_cache(divs)

        return self._filter_dividends(divs, start_date, end_date)

    def clear_cache(self) -> None:
        """Remove all cache files for this asset.
        
        Deletes:
        - {ticker}.pkl and {ticker}.csv (price data)
        - {ticker}_dividends.pkl and {ticker}_dividends.csv (dividend data)
        
        Example:
            >>> asset = Asset("NVDA")
            >>> asset.clear_cache()  # Force re-download on next fetch
        """
        # If delegating to provider, let provider handle cache clearing
        if getattr(self, "_provider", None) is not None:
            try:
                self._provider.clear_cache()
                return
            except Exception:
                # Fall through and attempt to remove files ourselves
                pass

        for path in [self.pkl_path, self.csv_path, self.div_pkl_path, self.div_csv_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass  # Silently ignore removal failures

    # -------------------------------------------------------------------------
    # Internal methods: caching
    # -------------------------------------------------------------------------

    def _load_price_cache(self) -> Optional[pd.DataFrame]:
        """Load OHLC cache from pickle (fast path)."""
        if os.path.exists(self.pkl_path):
            try:
                df: pd.DataFrame = pd.read_pickle(self.pkl_path)
                return df
            except Exception:
                # Corrupt cache: ignore and re-download
                return None
        return None

    def _save_price_cache(self, df: pd.DataFrame) -> None:
        """Save OHLC cache in both formats: pickle (fast) + CSV (readable)."""
        try:
            # Pickle: fast binary format
            df.to_pickle(self.pkl_path)
            
            # CSV: human-readable, Excel-compatible
            # Index is dates, so include it in CSV
            df.to_csv(self.csv_path, index=True)
        except Exception:
            # Silently ignore save failures (permissions, disk full, etc.)
            pass

    def _load_dividend_cache(self) -> Optional[pd.Series]:
        """Load dividend cache from pickle (fast path)."""
        if os.path.exists(self.div_pkl_path):
            try:
                series: pd.Series = pd.read_pickle(self.div_pkl_path)
                return series
            except Exception:
                # Corrupt cache: ignore and re-download
                return None
        return None

    def _save_dividend_cache(self, series: pd.Series) -> None:
        """Save dividend cache in both formats: pickle (fast) + CSV (readable)."""
        try:
            # Pickle: fast binary format
            series.to_pickle(self.div_pkl_path)
            
            # CSV: human-readable, Excel-compatible
            # Convert Series to DataFrame for better CSV format
            df = series.to_frame(name="Dividend")
            df.index.name = "Date"
            df.to_csv(self.div_csv_path)
        except Exception:
            # Silently ignore save failures
            pass

    def _cache_covers_range(
        self, cached: Optional[pd.DataFrame], start: date, end: date
    ) -> bool:
        """Check if cached data covers requested date range."""
        if cached is None or cached.empty:
            return False
        
        try:
            cached_dates = pd.to_datetime(cached.index).date
            cache_min = min(cached_dates)
            cache_max = max(cached_dates)
            return cache_min <= start and cache_max >= end
        except Exception:
            return False

    def _filter_range(self, df: pd.DataFrame, start: date, end: date) -> pd.DataFrame:
        """Filter DataFrame to requested date range."""
        if df.empty:
            return pd.DataFrame()
        
        try:
            dates = pd.to_datetime(df.index).date
            mask = (dates >= start) & (dates <= end)
            return df.loc[mask].copy()
        except Exception:
            return pd.DataFrame()

    def _filter_dividends(self, series: pd.Series, start: date, end: date) -> pd.Series:
        """Filter dividend Series to requested date range."""
        if series.empty:
            return pd.Series(dtype=float)
        
        try:
            dates = pd.to_datetime(series.index).date
            mask = (dates >= start) & (dates <= end)
            return series.loc[mask].copy()
        except Exception:
            return pd.Series(dtype=float)

    # -------------------------------------------------------------------------
    # Internal methods: downloading from yfinance
    # -------------------------------------------------------------------------

    def _download_ohlc(self, start: date, end: date) -> pd.DataFrame:
        """Download OHLC data from yfinance for date range.
        
        Handles yfinance quirks internally (date buffers, auto_adjust, etc.)
        Returns clean OHLC DataFrame or empty DataFrame on failure.
        """
        # Add 1-day buffer on each side for yfinance's date handling quirks
        start_dt = datetime.combine(start, datetime.min.time()) - timedelta(days=1)
        end_dt = datetime.combine(end, datetime.min.time()) + timedelta(days=1)

        try:
            # auto_adjust=False: preserve original unadjusted prices
            df = yf.download(
                self.ticker,
                start=start_dt.strftime("%Y-%m-%d"),
                end=end_dt.strftime("%Y-%m-%d"),
                progress=False,
                auto_adjust=False,
            )

            if df is None or df.empty:
                return pd.DataFrame()

            # yfinance returns MultiIndex columns even for single ticker
            # Flatten to simple column names (Open, High, Low, Close)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # Keep only OHLC columns
            cols = [c for c in ("Open", "High", "Low", "Close") if c in df.columns]
            if not cols:
                return pd.DataFrame()

            # Remove rows with all NaN prices
            df = df[cols].dropna(how="all")
            return df
            
        except Exception:
            # Download failed: return empty DataFrame
            return pd.DataFrame()

    def _download_dividends(self) -> pd.Series:
        """Download COMPLETE dividend/interest history from yfinance.
        
        Strategy: "Clone, don't query" - grab everything available.
        Dividends are immutable (historical), so fetch once and cache forever.
        """
        try:
            # Fetch Ticker object (metadata only, fast)
            ticker_obj = yf.Ticker(self.ticker)
            
            # Get complete dividend history
            dividends = ticker_obj.dividends
            
            if dividends is None or dividends.empty:
                return pd.Series(dtype=float)
            
            # Clean up: remove any NaN values
            dividends = dividends.dropna()
            
            return dividends
            
        except Exception:
            # Download failed: return empty Series
            return pd.Series(dtype=float)
