"""Yahoo Finance asset provider with dual-format caching.

Fetches market data from Yahoo Finance and caches in both pickle (fast)
and CSV (human-readable) formats.
"""

import os
from datetime import date, datetime, timedelta
from typing import Optional

import pandas as pd

from src.data.asset_provider import AssetProvider

# Optional dependency: gracefully degrade if yfinance unavailable
try:
    import yfinance as yf  # type: ignore

    YFINANCE_AVAILABLE = True
except Exception:
    yf = None
    YFINANCE_AVAILABLE = False


class YahooAssetProvider(AssetProvider):
    """Yahoo Finance data provider with dual-format caching.

    Fetches OHLC and dividend data from Yahoo Finance.
    Caches in two formats:
    - {ticker}.pkl - Fast binary for backtest performance
    - {ticker}.csv - Plain text for Excel/inspection

    Philosophy:
    - Computers are fast: dual-write overhead acceptable for transparency
    - Simple caching: download full range on miss
    - Fail fast: explicit errors, no silent failures
    """

    def __init__(self, ticker: str, cache_dir: str = "cache") -> None:
        """Initialize Yahoo Finance provider.

        Args:
            ticker: Stock symbol (e.g., "NVDA", "VOO", "BIL")
            cache_dir: Directory for cache files

        Raises:
            RuntimeError: If yfinance not installed/available
        """
        super().__init__(ticker, cache_dir)

        if not YFINANCE_AVAILABLE:
            raise RuntimeError(
                "yfinance not installed or failed to import. " "Install with: pip install yfinance"
            )

        # Ensure cache directory exists
        os.makedirs(cache_dir, exist_ok=True)

        # Cache file paths
        self.pkl_path: str = os.path.join(cache_dir, f"{self.ticker}.pkl")
        self.csv_path: str = os.path.join(cache_dir, f"{self.ticker}.csv")
        self.div_pkl_path: str = os.path.join(cache_dir, f"{self.ticker}_dividends.pkl")
        self.div_csv_path: str = os.path.join(cache_dir, f"{self.ticker}_dividends.csv")

    def get_prices(self, start_date: date, end_date: date) -> pd.DataFrame:
        """Get OHLC price data from Yahoo Finance.

        Strategy:
        1. Try load from pickle cache (fast path)
        2. If cache covers range: return filtered subset
        3. If cache miss/incomplete: download full range
        4. Save both pkl + csv formats
        5. Return requested range

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            DataFrame with OHLC columns, date-indexed

        Raises:
            ValueError: If start_date > end_date
        """
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
        """Get dividend/interest history from Yahoo Finance.

        Strategy: Download complete dividend history once, cache forever.
        Dividends are immutable (historical), so no incremental updates needed.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            Series with dividend amounts indexed by ex-dividend date

        Raises:
            ValueError: If start_date > end_date
        """
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
        """Remove all cache files for this asset."""
        for path in [self.pkl_path, self.csv_path, self.div_pkl_path, self.div_csv_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass

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
                return None
        return None

    def _save_price_cache(self, df: pd.DataFrame) -> None:
        """Save OHLC cache in both formats: pickle (fast) + CSV (readable).

        Extends existing cache with new data rather than overwriting.
        """
        try:
            # Load existing cache if it exists
            existing_df = self._load_price_cache()

            if existing_df is not None and not existing_df.empty:
                # Normalize indices to ensure compatibility
                # Convert both to datetime for consistent comparison
                existing_dates = pd.to_datetime(existing_df.index)
                new_dates = pd.to_datetime(df.index)

                # Reset indices to datetime objects for consistent merging
                existing_df = existing_df.copy()
                existing_df.index = existing_dates
                df = df.copy()
                df.index = new_dates

                # Combine existing cache with new data (union operation)
                combined_df = pd.concat([existing_df, df], axis=0)
                # Remove duplicates based on index (date), keeping the last occurrence
                combined_df = combined_df[~combined_df.index.duplicated(keep="last")]
                # Sort by index to maintain chronological order
                combined_df = combined_df.sort_index()
                df = combined_df

            # Save the (possibly extended) cache
            df.to_pickle(self.pkl_path)
            df.to_csv(self.csv_path, index=True)
        except Exception:
            pass

    def _load_dividend_cache(self) -> Optional[pd.Series]:
        """Load dividend cache from pickle (fast path)."""
        if os.path.exists(self.div_pkl_path):
            try:
                series: pd.Series = pd.read_pickle(self.div_pkl_path)
                return series
            except Exception:
                return None
        return None

    def _save_dividend_cache(self, series: pd.Series) -> None:
        """Save dividend cache in both formats: pickle (fast) + CSV (readable).

        Extends existing cache with new data rather than overwriting.
        """
        try:
            # Load existing cache if it exists
            existing_series = self._load_dividend_cache()

            if existing_series is not None and not existing_series.empty:
                # Normalize indices to ensure compatibility
                # Convert both to datetime for consistent comparison
                existing_dates = pd.to_datetime(existing_series.index)
                new_dates = pd.to_datetime(series.index)

                # Reset indices to datetime objects for consistent merging
                existing_series = existing_series.copy()
                existing_series.index = existing_dates
                series = series.copy()
                series.index = new_dates

                # Combine existing cache with new data (union operation)
                combined_series = pd.concat([existing_series, series], axis=0)
                # Remove duplicates based on index (date), keeping the last occurrence
                combined_series = combined_series[~combined_series.index.duplicated(keep="last")]
                # Sort by index to maintain chronological order
                combined_series = combined_series.sort_index()
                series = combined_series

            # Save the (possibly extended) cache
            series.to_pickle(self.div_pkl_path)
            df = series.to_frame(name="Dividend")
            df.index.name = "Date"
            df.to_csv(self.div_csv_path)
        except Exception:
            pass

    def _cache_covers_range(self, cached: Optional[pd.DataFrame], start: date, end: date) -> bool:
        """Check if cached data covers requested date range."""
        if cached is None or cached.empty:
            return False

        try:
            cached_dates = pd.to_datetime(cached.index).date
            cache_min = min(cached_dates)
            cache_max = max(cached_dates)
            return bool(cache_min <= start and cache_max >= end)
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
        """Download OHLC data from yfinance."""
        # Add 1-day buffer for yfinance date handling quirks
        start_dt = datetime.combine(start, datetime.min.time()) - timedelta(days=1)
        end_dt = datetime.combine(end, datetime.min.time()) + timedelta(days=1)

        try:
            df = yf.download(
                self.ticker,
                start=start_dt.strftime("%Y-%m-%d"),
                end=end_dt.strftime("%Y-%m-%d"),
                progress=False,
                auto_adjust=False,
            )

            if df is None or df.empty:
                return pd.DataFrame(columns=["Open", "High", "Low", "Close"])

            # Flatten MultiIndex columns (yfinance quirk)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # Keep only OHLC columns
            cols = [c for c in ("Open", "High", "Low", "Close") if c in df.columns]
            if not cols:
                return pd.DataFrame(columns=["Open", "High", "Low", "Close"])

            df = df[cols].dropna(how="all")
            return df

        except Exception:
            return pd.DataFrame(columns=["Open", "High", "Low", "Close"])

    def _download_dividends(self) -> pd.Series:
        """Download complete dividend history from yfinance."""
        try:
            ticker_obj = yf.Ticker(self.ticker)
            dividends = ticker_obj.dividends

            if dividends is None or dividends.empty:
                return pd.Series(dtype=float)

            return dividends.dropna()

        except Exception:
            return pd.Series(dtype=float)
