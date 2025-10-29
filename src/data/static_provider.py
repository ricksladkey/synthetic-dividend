"""Static asset provider for offline testing and CI.

Loads historical price data from committed CSV files in testdata/ directory.
Enables tests to run without network access by using pre-downloaded snapshots.
"""

import os
from datetime import date

import pandas as pd

from src.data.asset_provider import AssetProvider


class StaticAssetProvider(AssetProvider):
    """Static asset provider for offline testing.

    Loads OHLC data from CSV files stored in testdata/ directory.
    Each ticker has its own CSV file: testdata/{ticker}.csv

    CSV Format:
        Date,Open,High,Low,Close,Adj Close,Volume
        2020-01-02,324.87,326.11,324.52,325.34,325.34,50000000
        ...

    This provider enables:
    - CI testing without network access
    - Deterministic tests with known historical data
    - Fast test execution (no network I/O)

    Example:
        >>> # Register static provider with high priority
        >>> AssetRegistry.register("SPY", StaticAssetProvider, priority=0)
        >>> # Now Asset("SPY") will use committed testdata/SPY.csv
        >>> asset = Asset("SPY")
        >>> prices = asset.get_prices(date(2020, 1, 2), date(2020, 12, 31))
    """

    def __init__(self, ticker: str, cache_dir: str = "cache") -> None:
        """Initialize static provider.

        Args:
            ticker: Stock symbol (e.g., "SPY", "NVDA")
            cache_dir: Ignored (static data doesn't use cache)
        """
        super().__init__(ticker, cache_dir)

        # Find testdata directory relative to this file
        src_dir = os.path.dirname(os.path.dirname(__file__))
        self.testdata_dir = os.path.join(src_dir, "..", "testdata")
        self.csv_path = os.path.join(self.testdata_dir, f"{self.ticker}.csv")

    def get_prices(self, start_date: date, end_date: date) -> pd.DataFrame:
        """Get OHLC price data from static CSV file.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            DataFrame with OHLC columns, date-indexed
            Empty DataFrame if file doesn't exist or no data in range
        """
        # Check if static data file exists
        if not os.path.exists(self.csv_path):
            # Return empty DataFrame - fall back to other providers
            return pd.DataFrame(columns=["Open", "High", "Low", "Close"])

        # Load CSV file
        df = pd.read_csv(self.csv_path, index_col="Date", parse_dates=True)

        # Filter to requested date range
        mask = (df.index >= pd.Timestamp(start_date)) & (df.index <= pd.Timestamp(end_date))
        result = df.loc[mask, ["Open", "High", "Low", "Close"]].copy()

        return result

    def get_dividends(self, start_date: date, end_date: date) -> pd.Series:
        """Get dividend history from static CSV file.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            Series with dividend amounts indexed by ex-dividend date
            Empty Series if no dividend file exists
        """
        # Check for dividend file
        div_path = os.path.join(self.testdata_dir, f"{self.ticker}_dividends.csv")

        if not os.path.exists(div_path):
            return pd.Series(dtype=float)

        # Load dividend CSV
        df = pd.read_csv(div_path, index_col="Date", parse_dates=True)

        # Filter to requested date range
        mask = (df.index >= pd.Timestamp(start_date)) & (df.index <= pd.Timestamp(end_date))
        result = df.loc[mask, "Dividend"]

        return result

    def clear_cache(self) -> None:
        """No-op for static provider (no cache to clear)."""
        pass
