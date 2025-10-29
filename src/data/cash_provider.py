"""Cash asset provider for USD and other currency symbols.

Provides flat $1.00 prices for cash holdings. Enables cash to be treated
as just another asset in the portfolio without special casing.
"""

from datetime import date
import pandas as pd

from src.data.asset_provider import AssetProvider


class CashAssetProvider(AssetProvider):
    """Asset provider for cash (USD, etc.).

    Returns flat $1.00 prices for all dates. No volatility, no dividends.
    Enables cash to work everywhere a ticker works.

    Example:
        >>> cash = CashAssetProvider("USD")
        >>> prices = cash.get_prices(date(2024, 1, 1), date(2024, 1, 5))
        >>> prices["Close"].unique()
        array([1.0])
    """

    def get_prices(self, start_date: date, end_date: date) -> pd.DataFrame:
        """Return flat $1.00 prices for all dates in range.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            DataFrame with OHLC all at $1.00
        """
        if start_date > end_date:
            raise ValueError(f"start_date ({start_date}) must be <= end_date ({end_date})")

        # Generate daily date range (business days not needed - cash is 24/7)
        dates = pd.date_range(start=start_date, end=end_date, freq="D")

        # All prices are exactly $1.00
        return pd.DataFrame(
            {
                "Open": 1.0,
                "High": 1.0,
                "Low": 1.0,
                "Close": 1.0,
            },
            index=dates,
        )

    def get_dividends(self, start_date: date, end_date: date) -> pd.Series:
        """Cash doesn't pay dividends.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            Empty Series (cash has no dividend payments)
        """
        if start_date > end_date:
            raise ValueError(f"start_date ({start_date}) must be <= end_date ({end_date})")

        return pd.Series(dtype=float)
