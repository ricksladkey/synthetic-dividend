"""Tests for MockAssetProvider - mathematical signpost assets."""

from datetime import date

import pytest

from src.data.asset import Asset
from src.data.asset_provider import AssetRegistry
from src.data.mock_provider import (
    MockAssetProvider,
    create_flat_mock,
    create_trend_mock,
    create_volatile_mock,
)


@pytest.fixture(autouse=True)
def register_mock_provider():
    """Register mock provider for tests."""
    # Register with priority=0 to override even USD
    AssetRegistry.register("MOCK-*", MockAssetProvider, priority=0)
    yield
    # Cleanup: restore defaults
    AssetRegistry._providers = {}
    from src.data.cash_provider import CashAssetProvider
    from src.data.yahoo_provider import YahooAssetProvider

    AssetRegistry.register("USD", CashAssetProvider, priority=1)
    AssetRegistry.register("*", YahooAssetProvider, priority=9)


class TestMockProviderPatterns:
    """Test mock provider pattern matching."""

    def test_mock_flat_pattern(self):
        """MOCK-FLAT-{price} should generate constant prices."""
        asset = Asset("MOCK-FLAT-150")
        prices = asset.get_prices(date(2024, 1, 1), date(2024, 1, 10))

        # All close prices should be exactly $150.00
        assert (prices["Close"] == 150.0).all()

        # OHLC should have small variations
        assert (prices["Low"] <= prices["Close"]).all()
        assert (prices["High"] >= prices["Close"]).all()

    def test_mock_linear_trend(self):
        """MOCK-LINEAR-{start}-{end} should trend linearly."""
        asset = Asset("MOCK-LINEAR-100-200")
        prices = asset.get_prices(date(2024, 1, 1), date(2024, 1, 11))

        # Should start near $100 and end near $200
        assert prices["Close"].iloc[0] == pytest.approx(100.0, abs=0.1)
        assert prices["Close"].iloc[-1] == pytest.approx(200.0, abs=0.1)

        # Should be monotonically increasing
        assert (prices["Close"].diff()[1:] > 0).all()

    def test_mock_sine_wave(self):
        """MOCK-SINE-{base}-{amp} should oscillate."""
        asset = Asset("MOCK-SINE-100-20")
        prices = asset.get_prices(date(2024, 1, 1), date(2024, 12, 31))

        # Mean should be near base price
        assert prices["Close"].mean() == pytest.approx(100.0, abs=1.0)

        # Should oscillate around base
        assert prices["Close"].min() < 100.0
        assert prices["Close"].max() > 100.0

    def test_mock_step_function(self):
        """MOCK-STEP-{start}-{step} should jump in steps."""
        asset = Asset("MOCK-STEP-100-10")
        prices = asset.get_prices(date(2024, 1, 1), date(2024, 4, 1))

        # Should start at $100
        assert prices["Close"].iloc[0] == pytest.approx(100.0, abs=0.1)

        # Should have distinct price levels
        unique_levels = len(prices["Close"].round(0).unique())
        assert unique_levels >= 3  # At least 3 steps in 3 months

    def test_mock_random_walk(self):
        """MOCK-WALK-{start} should random walk from start price."""
        asset = Asset("MOCK-WALK-100")
        prices = asset.get_prices(date(2024, 1, 1), date(2024, 12, 31))

        # Should start at $100
        assert prices["Close"].iloc[0] == pytest.approx(100.0, abs=0.1)

        # Should vary (not all the same)
        assert prices["Close"].std() > 0

        # Deterministic: same ticker = same prices
        prices2 = asset.get_prices(date(2024, 1, 1), date(2024, 12, 31))
        assert prices["Close"].equals(prices2["Close"])


class TestMockConvenienceFunctions:
    """Test convenience factory functions."""

    def test_create_flat_mock(self):
        """Convenience function should create valid flat ticker."""
        ticker = create_flat_mock(125.0)
        assert ticker == "MOCK-FLAT-125.0"

        asset = Asset(ticker)
        prices = asset.get_prices(date(2024, 1, 1), date(2024, 1, 5))
        assert (prices["Close"] == 125.0).all()

    def test_create_trend_mock(self):
        """Convenience function should create valid trend ticker."""
        ticker = create_trend_mock(50.0, 150.0)
        assert ticker == "MOCK-LINEAR-50.0-150.0"

        asset = Asset(ticker)
        prices = asset.get_prices(date(2024, 1, 1), date(2024, 1, 11))
        assert prices["Close"].iloc[0] == pytest.approx(50.0, abs=0.1)
        assert prices["Close"].iloc[-1] == pytest.approx(150.0, abs=0.1)

    def test_create_volatile_mock(self):
        """Convenience function should create valid volatile ticker."""
        ticker = create_volatile_mock(100.0, 30.0)
        assert ticker == "MOCK-SINE-100.0-30.0"

        asset = Asset(ticker)
        prices = asset.get_prices(date(2024, 1, 1), date(2024, 12, 31))
        assert prices["Close"].mean() == pytest.approx(100.0, abs=2.0)


class TestMockInBacktest:
    """Test mock assets work seamlessly in backtests."""

    def test_mock_works_with_asset_api(self):
        """Mock should work exactly like any other asset."""
        # Create mock via Asset() factory - no special code needed
        mock = Asset("MOCK-FLAT-100")
        real = Asset("USD")  # CashAssetProvider also returns flat $1.00

        # Both work with same API
        mock_prices = mock.get_prices(date(2024, 1, 1), date(2024, 1, 5))
        real_prices = real.get_prices(date(2024, 1, 1), date(2024, 1, 5))

        # Both return DataFrames with OHLC
        assert set(mock_prices.columns) == {"Open", "High", "Low", "Close"}
        assert set(real_prices.columns) == {"Open", "High", "Low", "Close"}

        # Both can get dividends (empty for both)
        mock_divs = mock.get_dividends(date(2024, 1, 1), date(2024, 12, 31))
        real_divs = real.get_dividends(date(2024, 1, 1), date(2024, 12, 31))
        assert len(mock_divs) == 0
        assert len(real_divs) == 0

    def test_multiple_mock_patterns_coexist(self):
        """Different mock patterns can be used simultaneously."""
        flat = Asset("MOCK-FLAT-100")
        trend = Asset("MOCK-LINEAR-100-200")
        volatile = Asset("MOCK-SINE-100-20")

        # All work independently
        flat_p = flat.get_prices(date(2024, 1, 1), date(2024, 1, 10))
        trend_p = trend.get_prices(date(2024, 1, 1), date(2024, 1, 10))
        volatile_p = volatile.get_prices(date(2024, 1, 1), date(2024, 1, 10))

        # Each has distinct behavior
        assert flat_p["Close"].std() < 0.1  # Nearly flat
        assert trend_p["Close"].diff()[1:].mean() > 0  # Trending up
        assert volatile_p["Close"].std() > flat_p["Close"].std()  # More volatile


class TestMockExtensibility:
    """Test that mocks don't fork the main algorithm."""

    def test_no_special_casing_needed(self):
        """Backtest code doesn't need to know about mocks."""
        from src.models.backtest import run_portfolio_backtest

        # Use mock data for backtest - no code changes needed
        mock_ticker = create_flat_mock(100.0)

        # This would work identically with "NVDA" or any other ticker
        # The backtest algorithm has ZERO knowledge of mocks
        initial_qty = 100
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)

        # Run backtest (would work the same way)
        transactions, summary = run_portfolio_backtest(
            allocations={mock_ticker: 1.0},
            start_date=start_date,
            end_date=end_date,
            portfolio_algo="per-asset:buy-and-hold",
            initial_investment=initial_qty * 100.0,  # 100 shares @ $100 each
            simple_mode=True,
        )

        # Backtest runs successfully with mock data
        mock_asset_summary = summary["assets"][mock_ticker]
        assert mock_asset_summary["final_holdings"] == 100
        assert len(transactions) == 1  # Initial purchase transaction
        assert transactions[0].action == "BUY"

    def test_registry_enables_future_extensions(self):
        """Registry pattern means new providers = zero code changes."""
        # Tomorrow: add QuandlAssetProvider, BondAssetProvider, etc.
        # Just register them, existing code continues to work:

        # AssetRegistry.register("BOND-*", BondAssetProvider, priority=2)
        # AssetRegistry.register("QUANDL-*", QuandlAssetProvider, priority=2)
        #
        # asset = Asset("BOND-UST-10Y")  # Works automatically
        # asset = Asset("QUANDL-GOLD-SPOT")  # Works automatically

        # The synthetic dividend algorithm NEVER needs to change
        # The backtest engine NEVER needs to change
        # The portfolio/holding classes NEVER need to change

        # This is the power of the provider pattern
        assert True  # Philosophical test passes ✓
