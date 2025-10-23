"""Historical price data fetcher with per-ticker disk caching.

Fetches OHLC data from yfinance and caches to local pickle files.
Intelligently extends cache when requested dates exceed cached range.
"""
import os
import pickle
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd

# Optional dependency: gracefully degrade if yfinance unavailable
try:
    import yfinance as yf  # type: ignore
except Exception:
    yf = None


class HistoryFetcher:
    """Fetch and cache historical stock price data per ticker.
    
    Cache strategy:
    - One pickle file per ticker (e.g., NVDA.pkl)
    - Stores OHLC DataFrame with date index
    - Extends cache automatically if requested range exceeds cached dates
    - Returns copy of requested date range
    """

    def __init__(self, cache_dir: Optional[str] = None) -> None:
        """Initialize fetcher with cache directory.
        
        Args:
            cache_dir: Path to cache directory (default: ../cache from this file)
        """
        if cache_dir is None:
            cache_dir = os.path.join(os.path.dirname(__file__), "..", "cache")
        self.cache_dir: str = os.path.abspath(cache_dir)
        os.makedirs(self.cache_dir, exist_ok=True)

    def _cache_path(self, ticker: str) -> str:
        """Return absolute path to cache file for ticker."""
        return os.path.join(self.cache_dir, f"{ticker.upper()}.pkl")

    def _load_cache(self, ticker: str) -> Optional[pd.DataFrame]:
        """Load cached DataFrame for ticker, or None if missing/corrupt."""
        path = self._cache_path(ticker)
        if os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    df: pd.DataFrame = pickle.load(f)
                return df
            except Exception:
                # Corrupt cache file
                return None
        return None

    def _save_cache(self, ticker: str, df: pd.DataFrame) -> None:
        """Persist DataFrame to cache file (pickle format)."""
        path = self._cache_path(ticker)
        try:
            with open(path, "wb") as f:
                pickle.dump(df, f)
        except Exception:
            # Silently ignore save failures (permissions, disk full, etc.)
            pass

    def _download(self, ticker: str, start: date, end: date) -> pd.DataFrame:
        """Download OHLC data from yfinance for date range.
        
        Args:
            ticker: Stock symbol
            start: Start date (inclusive)
            end: End date (inclusive)
            
        Returns:
            DataFrame with OHLC columns, date-indexed (empty if no data)
        """
        if yf is None:
            raise RuntimeError("yfinance not installed or failed to import")
        
        # Add 1-day buffer on each side for yfinance's date handling quirks
        start_dt = datetime.combine(start, datetime.min.time()) - timedelta(days=1)
        end_dt = datetime.combine(end, datetime.min.time()) + timedelta(days=1)
        
        # auto_adjust=False: preserve original unadjusted prices
        df = yf.download(
            ticker,
            start=start_dt.strftime("%Y-%m-%d"),
            end=end_dt.strftime("%Y-%m-%d"),
            progress=False,
            auto_adjust=False,
        )
        
        if df is None or df.empty:
            return pd.DataFrame()
        
        # Keep only OHLC columns (needed for intraday logic in algorithms)
        cols = [c for c in ("Open", "High", "Low", "Close") if c in df.columns]
        if not cols:
            return pd.DataFrame()
        
        # Remove rows with all NaN prices
        df = df[cols].dropna(how="all")
        return df

    def get_history(
        self, 
        ticker: str, 
        start_date: date, 
        end_date: date
    ) -> pd.DataFrame:
        """Fetch OHLC history for ticker in date range, using cache when possible.
        
        Workflow:
        1. Check cache file
        2. If missing/empty: download full range, save cache, return subset
        3. If cached: check if start/end dates are covered
        4. Download missing left/right ranges if needed
        5. Merge, deduplicate, update cache
        6. Return requested date range as copy
        
        Args:
            ticker: Stock symbol
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            
        Returns:
            DataFrame with OHLC columns, date-indexed (empty if no data available)
        """
        ticker = ticker.upper()
        cached = self._load_cache(ticker)
        
        # No cache: download full range
        if cached is None or cached.empty:
            df_new = self._download(ticker, start_date, end_date)
            if df_new.empty:
                return pd.DataFrame()
            self._save_cache(ticker, df_new)
            # Filter to requested range
            mask = (pd.to_datetime(df_new.index).date >= start_date) & \
                   (pd.to_datetime(df_new.index).date <= end_date)
            return df_new.loc[mask].copy()

        # Cache exists: determine if we need additional data
        cached_dates = pd.to_datetime(cached.index).date
        cache_min = min(cached_dates)
        cache_max = max(cached_dates)

        need_download = False
        updated = cached.copy()

        # Extend cache leftward if requested range starts before cached data
        if start_date < cache_min:
            df_left = self._download(ticker, start_date, cache_min - timedelta(days=1))
            if not df_left.empty:
                updated = pd.concat([df_left, updated]).sort_index()
                need_download = True

        # Extend cache rightward if requested range ends after cached data
        if end_date > cache_max:
            df_right = self._download(ticker, cache_max + timedelta(days=1), end_date)
            if not df_right.empty:
                updated = pd.concat([updated, df_right]).sort_index()
                need_download = True

        # Save extended cache (remove duplicate dates from concat)
        if need_download:
            updated = updated[~updated.index.duplicated(keep="first")]
            self._save_cache(ticker, updated)

        # Return only requested date range
        mask = (pd.to_datetime(updated.index).date >= start_date) & \
               (pd.to_datetime(updated.index).date <= end_date)
        return updated.loc[mask].copy()

    def get_multiple_histories(
        self,
        tickers: List[str],
        start_date: date,
        end_date: date
    ) -> Dict[str, pd.DataFrame]:
        """Fetch OHLC history for multiple tickers in parallel (same date range).
        
        This is a convenience wrapper around get_history() that fetches data
        for multiple tickers and returns them as a dictionary. Each ticker
        is fetched independently using the same caching logic.
        
        Args:
            tickers: List of stock symbols to fetch
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            
        Returns:
            Dict mapping ticker symbol to DataFrame (may be empty if no data)
            
        Example:
            >>> fetcher = HistoryFetcher()
            >>> data = fetcher.get_multiple_histories(
            ...     ["NVDA", "VOO", "BIL"],
            ...     date(2024, 1, 1),
            ...     date(2024, 12, 31)
            ... )
            >>> nvda_df = data["NVDA"]
            >>> voo_df = data["VOO"]
        """
        result: Dict[str, pd.DataFrame] = {}
        for ticker in tickers:
            result[ticker] = self.get_history(ticker, start_date, end_date)
        return result
