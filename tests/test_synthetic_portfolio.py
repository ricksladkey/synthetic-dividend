"""
Tests for SyntheticPortfolio - the multi-asset synthetic dividend portfolio.
"""

import pytest

from src.models.synthetic_portfolio import SyntheticAsset, SyntheticPortfolio


class TestSyntheticPortfolio:
    """Test the synthetic portfolio functionality."""

    def test_portfolio_creation(self):
        """Test basic portfolio creation."""
        portfolio = SyntheticPortfolio(cash=100_000, name="Test Portfolio")

        assert portfolio.name == "Test Portfolio"
        assert portfolio.bank == 100_000
        assert portfolio.initial_capital == 100_000
        assert len(portfolio.assets) == 0
        assert portfolio.rebalancing_mode == "nav_opportunistic"

    def test_add_asset(self):
        """Test adding assets to portfolio."""
        portfolio = SyntheticPortfolio(cash=100_000)

        # Add first asset
        portfolio.add_asset("NVDA", shares=100, price=450.0, strategy="sd8")
        assert "NVDA" in portfolio.assets
        assert portfolio.assets["NVDA"].holdings == 100
        assert portfolio.assets["NVDA"].nav == 450.0
        assert portfolio.bank == 100_000 - (100 * 450.0)  # $55,000 remaining

        # Add second asset
        portfolio.add_asset("SPY", shares=50, price=400.0, strategy="sd10")
        assert "SPY" in portfolio.assets
        assert portfolio.assets["SPY"].holdings == 50
        assert portfolio.assets["SPY"].nav == 400.0
        assert portfolio.bank == 55_000 - (50 * 400.0)  # $35,000 remaining

    def test_add_duplicate_asset_fails(self):
        """Test that adding duplicate assets fails."""
        portfolio = SyntheticPortfolio(cash=100_000)
        portfolio.add_asset("NVDA", shares=100, price=450.0)

        with pytest.raises(ValueError, match="Asset NVDA already exists"):
            portfolio.add_asset("NVDA", shares=50, price=400.0)

    def test_get_holdings(self):
        """Test getting current holdings."""
        portfolio = SyntheticPortfolio(cash=100_000)
        portfolio.add_asset("NVDA", shares=100, price=450.0)
        portfolio.add_asset("SPY", shares=50, price=400.0)

        holdings = portfolio.get_holdings()
        assert holdings == {"NVDA": 100, "SPY": 50}

    def test_get_total_value(self):
        """Test calculating total portfolio value."""
        portfolio = SyntheticPortfolio(cash=100_000)  # Start with more cash
        portfolio.add_asset("NVDA", shares=100, price=450.0)  # $45,000 invested
        portfolio.add_asset("SPY", shares=50, price=400.0)  # $20,000 invested
        # Bank should be 100,000 - 45,000 - 20,000 = $35,000 remaining

        current_prices = {"NVDA": 500.0, "SPY": 420.0}
        total_value = portfolio.get_total_value(current_prices)

        expected = 35_000 + (100 * 500.0) + (50 * 420.0)  # 35k + 50k + 21k = 106k
        assert total_value == expected

    def test_deposit_and_withdraw(self):
        """Test cash management."""
        portfolio = SyntheticPortfolio(cash=50_000)

        # Deposit
        portfolio.deposit(25_000)
        assert portfolio.bank == 75_000

        # Withdraw successful
        success = portfolio.withdraw(30_000)
        assert success is True
        assert portfolio.bank == 45_000

        # Withdraw too much
        success = portfolio.withdraw(50_000)
        assert success is False
        assert portfolio.bank == 45_000  # Unchanged

    def test_nav_calculations(self):
        """Test NAV-related calculations."""
        asset = SyntheticAsset(ticker="NVDA", holdings=100, nav=450.0)

        # Market value
        assert asset.market_value(500.0) == 50_000.0

        # NAV value
        assert asset.nav_value() == 45_000.0

        # NAV premium (price > NAV)
        assert asset.nav_premium(500.0) == (500.0 - 450.0) / 450.0  # 11.11%

        # NAV discount (price < NAV)
        assert asset.nav_premium(400.0) == (400.0 - 450.0) / 450.0  # -11.11%

    def test_nav_updates(self):
        """Test NAV updates to all-time highs."""
        asset = SyntheticAsset(ticker="NVDA", nav=450.0)

        # Lower price shouldn't change NAV
        asset.update_nav(400.0)
        assert asset.nav == 450.0

        # Higher price should update NAV
        asset.update_nav(475.0)
        assert asset.nav == 475.0

        # Even higher
        asset.update_nav(500.0)
        assert asset.nav == 500.0

    def test_portfolio_summary(self):
        """Test portfolio summary generation."""
        portfolio = SyntheticPortfolio(cash=100_000, name="Test Portfolio")
        portfolio.add_asset("NVDA", shares=100, price=450.0)

        summary = portfolio.summary()

        assert summary["name"] == "Test Portfolio"
        assert summary["bank_balance"] == 100_000 - (100 * 450.0)
        assert summary["assets"] == 1
        assert summary["transactions"] == 1  # Initial buy
        assert summary["rebalancing_mode"] == "nav_opportunistic"

    def test_string_representations(self):
        """Test string representations."""
        portfolio = SyntheticPortfolio(cash=100_000, name="Test Portfolio")

        # Empty portfolio
        assert "Test Portfolio" in str(portfolio)
        assert "$100,000" in str(portfolio)

        # With assets (would need to add snapshot logic)
        portfolio.add_asset("NVDA", shares=100, price=450.0)
        assert "SyntheticPortfolio" in repr(portfolio)
        assert "Test Portfolio" in repr(portfolio)
