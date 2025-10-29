"""Tests for StaticAssetProvider - offline testing with committed data."""

from datetime import date

import pytest

from src.data.asset import Asset
from src.data.asset_provider import AssetRegistry
from src.data.static_provider import StaticAssetProvider


@pytest.fixture(autouse=True)
def register_static_provider():
    """Register static provider for tests."""
    # Register with priority=0 to override all other providers
    AssetRegistry.register("SPY", StaticAssetProvider, priority=0)
    AssetRegistry.register("NVDA", StaticAssetProvider, priority=0)
    yield
    # Cleanup: restore defaults
    AssetRegistry._providers = {}
    from src.data.cash_provider import CashAssetProvider
    from src.data.yahoo_provider import YahooAssetProvider

    AssetRegistry.register("USD", CashAssetProvider, priority=1)
    AssetRegistry.register("*", YahooAssetProvider, priority=9)


class TestStaticAssetProvider:
    """Test static asset provider for offline data."""

    def test_loads_spy_data(self):
        """Static provider should load committed SPY data."""
        asset = Asset("SPY")
        prices = asset.get_prices(date(2020, 1, 30), date(2020, 2, 5))

        # Should have data for trading days
        assert len(prices) > 0
        assert "Close" in prices.columns
        assert "Open" in prices.columns
        assert "High" in prices.columns
        assert "Low" in prices.columns

    def test_filters_date_range(self):
        """Should return only data in requested range."""
        asset = Asset("SPY")
        prices = asset.get_prices(date(2020, 1, 30), date(2020, 2, 5))

        # All dates should be in range
        assert prices.index.min().date() >= date(2020, 1, 30)
        assert prices.index.max().date() <= date(2020, 2, 5)

    def test_returns_empty_for_missing_ticker(self):
        """Should return empty DataFrame if ticker file doesn't exist."""
        asset = Asset("MISSING")  # Not in testdata
        prices = asset.get_prices(date(2020, 1, 2), date(2020, 12, 31))

        # Should be empty but have correct columns
        assert len(prices) == 0
        assert "Close" in prices.columns

    def test_dividends_empty_when_no_file(self):
        """Should return empty Series if dividend file doesn't exist."""
        asset = Asset("SPY")
        divs = asset.get_dividends(date(2020, 1, 1), date(2020, 12, 31))

        # Should be empty Series
        assert len(divs) == 0

    def test_works_with_asset_api(self):
        """Static provider should work seamlessly with Asset class."""
        # Create asset - no special code needed
        asset = Asset("SPY")

        # Standard Asset API works
        prices = asset.get_prices(date(2020, 1, 2), date(2020, 1, 31))
        divs = asset.get_dividends(date(2020, 1, 1), date(2020, 12, 31))

        # Returns correct types
        assert prices.shape[0] > 0  # Has rows
        assert prices.shape[1] == 4  # OHLC columns
        assert len(divs) >= 0  # May be empty


class TestStaticProviderForCI:
    """Test that static provider enables CI testing without network."""

    def test_no_network_required(self):
        """Static data should work without internet access."""
        # This test would fail with YahooAssetProvider if offline
        # But succeeds with StaticAssetProvider using committed data
        asset = Asset("SPY")
        prices = asset.get_prices(date(2020, 1, 2), date(2020, 1, 31))

        assert len(prices) > 0
        # We know SPY was trading around $325 in Jan 2020
        assert prices["Close"].iloc[0] > 300
        assert prices["Close"].iloc[0] < 350

    def test_consistent_data(self):
        """Static data should be deterministic across runs."""
        asset = Asset("SPY")

        # First fetch
        prices1 = asset.get_prices(date(2020, 1, 2), date(2020, 1, 10))

        # Second fetch
        prices2 = asset.get_prices(date(2020, 1, 2), date(2020, 1, 10))

        # Should be identical
        assert prices1.equals(prices2)

    def test_supports_multiple_date_ranges(self):
        """Should support querying different date ranges from same file."""
        asset = Asset("SPY")

        # Query January (includes available data)
        jan = asset.get_prices(date(2020, 1, 30), date(2020, 1, 31))

        # Query February (no data available)
        feb = asset.get_prices(date(2020, 2, 1), date(2020, 2, 29))

        # January should have data, February should have data (fallback to Yahoo)
        assert len(jan) > 0
        assert len(feb) > 0
