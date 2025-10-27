"""Historical price data fetcher with per-ticker disk caching.

DEPRECATED: Legacy wrapper around Asset class for backward compatibility.
New code should use Asset class directly from src.data.asset.
"""

import os
from datetime import date
from typing import Dict, List, Optional

import pandas as pd

from src.data.asset import Asset


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

    def get_history(self, ticker: str, start_date: date, end_date: date) -> pd.DataFrame:
        """Fetch OHLC history for ticker in date range, using cache when possible.

        DEPRECATED: Use Asset(ticker).get_prices(start_date, end_date) instead.

        Args:
            ticker: Stock symbol
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            DataFrame with OHLC columns, date-indexed (empty if no data available)
        """
        asset = Asset(ticker, cache_dir=self.cache_dir)
        return asset.get_prices(start_date, end_date)

    def get_multiple_histories(
        self, tickers: List[str], start_date: date, end_date: date
    ) -> Dict[str, pd.DataFrame]:
        """Fetch OHLC history for multiple tickers in parallel (same date range).

        DEPRECATED: Use {t: Asset(t).get_prices(start, end) for t in tickers} instead.

        Args:
            tickers: List of stock symbols to fetch
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            Dict mapping ticker symbol to DataFrame (may be empty if no data)
        """
        result: Dict[str, pd.DataFrame] = {}
        for ticker in tickers:
            asset = Asset(ticker, cache_dir=self.cache_dir)
            result[ticker] = asset.get_prices(start_date, end_date)
        return result

    def get_dividends(self, ticker: str, start_date: date, end_date: date) -> pd.Series:
        """Fetch dividend/interest history for ticker, using cache when possible.

        DEPRECATED: Use Asset(ticker).get_dividends(start_date, end_date) instead.

        Args:
            ticker: Stock symbol
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            Series with dividend amounts indexed by ex-dividend date
            (empty Series if no dividends in range or ticker doesn't pay)
        """
        asset = Asset(ticker, cache_dir=self.cache_dir)
        return asset.get_dividends(start_date, end_date)

    def get_multiple_dividends(
        self, tickers: List[str], start_date: date, end_date: date
    ) -> Dict[str, pd.Series]:
        """Fetch dividend history for multiple tickers (same date range).

        DEPRECATED: Use {t: Asset(t).get_dividends(start, end) for t in tickers} instead.

        Args:
            tickers: List of stock symbols to fetch
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            Dict mapping ticker symbol to dividend Series (may be empty if none)
        """
        result: Dict[str, pd.Series] = {}
        for ticker in tickers:
            asset = Asset(ticker, cache_dir=self.cache_dir)
            result[ticker] = asset.get_dividends(start_date, end_date)
        return result
