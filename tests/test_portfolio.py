"""
Test suite for Portfolio model.

Tests portfolio-level aggregation and multi-ticker management.
"""

from datetime import date

import pytest

from src.models.portfolio import Portfolio


class TestPortfolio:
    """Test the Portfolio model."""

    def test_create_empty_portfolio(self):
        """Can create an empty portfolio."""
        portfolio = Portfolio()

        assert len(portfolio.holdings) == 0
        assert portfolio.get_all_tickers() == []

    def test_add_holding(self):
        """Can add a holding to portfolio."""
        portfolio = Portfolio()

        holding = portfolio.add_holding("NVDA")

        assert holding.ticker == "NVDA"
        assert portfolio.has_holding("NVDA")
        assert len(portfolio.holdings) == 1

    def test_cannot_add_duplicate_ticker(self):
        """Cannot add the same ticker twice."""
        portfolio = Portfolio()
        portfolio.add_holding("NVDA")

        with pytest.raises(ValueError, match="already exists"):
            portfolio.add_holding("NVDA")

    def test_buy_creates_holding_automatically(self):
        """Buying a new ticker creates holding automatically."""
        portfolio = Portfolio()

        portfolio.buy(
            ticker="NVDA", shares=100, purchase_date=date(2024, 1, 1), purchase_price=50.0
        )

        assert portfolio.has_holding("NVDA")
        assert portfolio.total_shares("NVDA") == 100

    def test_buy_multiple_tickers(self):
        """Can buy shares of multiple tickers."""
        portfolio = Portfolio()

        portfolio.buy("NVDA", shares=100, purchase_date=date(2024, 1, 1), purchase_price=50.0)
        portfolio.buy("VOO", shares=50, purchase_date=date(2024, 1, 1), purchase_price=400.0)
        portfolio.buy("GLD", shares=200, purchase_date=date(2024, 1, 1), purchase_price=180.0)

        assert len(portfolio.holdings) == 3
        assert portfolio.total_shares("NVDA") == 100
        assert portfolio.total_shares("VOO") == 50
        assert portfolio.total_shares("GLD") == 200

    def test_sell_shares(self):
        """Can sell shares of a ticker."""
        portfolio = Portfolio()

        portfolio.buy("NVDA", shares=100, purchase_date=date(2024, 1, 1), purchase_price=50.0)
        portfolio.sell("NVDA", shares=40, sale_date=date(2024, 6, 1), sale_price=75.0)

        assert portfolio.total_shares("NVDA") == 60

    def test_sell_nonexistent_ticker_fails(self):
        """Cannot sell shares of ticker not in portfolio."""
        portfolio = Portfolio()

        with pytest.raises(ValueError, match="not found in portfolio"):
            portfolio.sell("NVDA", shares=100, sale_date=date(2024, 6, 1), sale_price=75.0)

    def test_total_shares_all_tickers(self):
        """Can get total shares across all tickers."""
        portfolio = Portfolio()

        portfolio.buy("NVDA", shares=100, purchase_date=date(2024, 1, 1), purchase_price=50.0)
        portfolio.buy("VOO", shares=50, purchase_date=date(2024, 1, 1), purchase_price=400.0)

        # Note: total_shares() without ticker doesn't make sense for different tickers
        # But we're summing share counts across tickers
        assert portfolio.total_shares() == 150

    def test_total_value_single_ticker(self):
        """Calculate total value for single ticker."""
        portfolio = Portfolio()

        portfolio.buy("NVDA", shares=100, purchase_date=date(2024, 1, 1), purchase_price=50.0)

        prices = {"NVDA": 75.0}
        assert portfolio.total_value(prices) == 7500.0

    def test_total_value_multiple_tickers(self):
        """Calculate total value for multiple tickers."""
        portfolio = Portfolio()

        portfolio.buy("NVDA", shares=100, purchase_date=date(2024, 1, 1), purchase_price=50.0)
        portfolio.buy("VOO", shares=50, purchase_date=date(2024, 1, 1), purchase_price=400.0)
        portfolio.buy("GLD", shares=200, purchase_date=date(2024, 1, 1), purchase_price=180.0)

        prices = {
            "NVDA": 75.0,  # 100 × 75 = 7,500
            "VOO": 450.0,  # 50 × 450 = 22,500
            "GLD": 190.0,  # 200 × 190 = 38,000
        }

        # Total: 7,500 + 22,500 + 38,000 = 68,000
        assert portfolio.total_value(prices) == 68000.0

    def test_total_value_missing_price_fails(self):
        """total_value requires prices for all tickers."""
        portfolio = Portfolio()

        portfolio.buy("NVDA", shares=100, purchase_date=date(2024, 1, 1), purchase_price=50.0)
        portfolio.buy("VOO", shares=50, purchase_date=date(2024, 1, 1), purchase_price=400.0)

        prices = {"NVDA": 75.0}  # Missing VOO price

        with pytest.raises(KeyError, match="Price not provided for ticker: VOO"):
            portfolio.total_value(prices)

    def test_total_cost_basis(self):
        """Calculate total cost basis."""
        portfolio = Portfolio()

        portfolio.buy("NVDA", shares=100, purchase_date=date(2024, 1, 1), purchase_price=50.0)
        portfolio.buy("VOO", shares=50, purchase_date=date(2024, 1, 1), purchase_price=400.0)

        # Cost: (100 × 50) + (50 × 400) = 5,000 + 20,000 = 25,000
        assert portfolio.total_cost_basis() == 25000.0

    def test_total_cost_basis_single_ticker(self):
        """Calculate cost basis for specific ticker."""
        portfolio = Portfolio()

        portfolio.buy("NVDA", shares=100, purchase_date=date(2024, 1, 1), purchase_price=50.0)
        portfolio.buy("VOO", shares=50, purchase_date=date(2024, 1, 1), purchase_price=400.0)

        assert portfolio.total_cost_basis("NVDA") == 5000.0
        assert portfolio.total_cost_basis("VOO") == 20000.0

    def test_unrealized_gain_loss(self):
        """Calculate unrealized P/L."""
        portfolio = Portfolio()

        portfolio.buy("NVDA", shares=100, purchase_date=date(2024, 1, 1), purchase_price=50.0)
        portfolio.buy("VOO", shares=50, purchase_date=date(2024, 1, 1), purchase_price=400.0)

        prices = {
            "NVDA": 75.0,  # Cost: 5,000, Value: 7,500, Gain: 2,500
            "VOO": 450.0,  # Cost: 20,000, Value: 22,500, Gain: 2,500
        }

        # Total unrealized gain: 2,500 + 2,500 = 5,000
        assert portfolio.total_unrealized_gain_loss(prices) == 5000.0

    def test_realized_gain_loss(self):
        """Calculate realized P/L."""
        portfolio = Portfolio()

        portfolio.buy("NVDA", shares=100, purchase_date=date(2024, 1, 1), purchase_price=50.0)
        portfolio.sell("NVDA", shares=100, sale_date=date(2024, 6, 1), sale_price=75.0)

        # Bought at 50, sold at 75: 100 × (75 - 50) = 2,500
        assert portfolio.total_realized_gain_loss() == 2500.0

    def test_realized_gain_loss_single_ticker(self):
        """Calculate realized P/L for specific ticker."""
        portfolio = Portfolio()

        portfolio.buy("NVDA", shares=100, purchase_date=date(2024, 1, 1), purchase_price=50.0)
        portfolio.buy("VOO", shares=50, purchase_date=date(2024, 1, 1), purchase_price=400.0)

        portfolio.sell("NVDA", shares=100, sale_date=date(2024, 6, 1), sale_price=75.0)

        assert portfolio.total_realized_gain_loss("NVDA") == 2500.0
        assert portfolio.total_realized_gain_loss("VOO") == 0.0

    def test_total_gain_loss(self):
        """Calculate total P/L (realized + unrealized)."""
        portfolio = Portfolio()

        # Buy 200 NVDA
        portfolio.buy("NVDA", shares=200, purchase_date=date(2024, 1, 1), purchase_price=50.0)

        # Sell 100 at 75 (realized gain: $2,500)
        portfolio.sell("NVDA", shares=100, sale_date=date(2024, 6, 1), sale_price=75.0)

        # Remaining 100 worth $80 (unrealized gain: $3,000)
        prices = {"NVDA": 80.0}

        # Total: 2,500 + 3,000 = 5,500
        assert portfolio.total_gain_loss(prices) == 5500.0

    def test_allocations_equal_value(self):
        """Calculate portfolio allocations."""
        portfolio = Portfolio()

        # Create 50/50 portfolio by value
        portfolio.buy("NVDA", shares=100, purchase_date=date(2024, 1, 1), purchase_price=50.0)
        portfolio.buy("VOO", shares=100, purchase_date=date(2024, 1, 1), purchase_price=50.0)

        prices = {"NVDA": 50.0, "VOO": 50.0}  # Value: 5,000  # Value: 5,000

        allocations = portfolio.allocations(prices)

        assert allocations["NVDA"] == 0.5
        assert allocations["VOO"] == 0.5

    def test_allocations_unequal_value(self):
        """Calculate allocations with different values."""
        portfolio = Portfolio()

        portfolio.buy("NVDA", shares=100, purchase_date=date(2024, 1, 1), purchase_price=50.0)
        portfolio.buy("VOO", shares=50, purchase_date=date(2024, 1, 1), purchase_price=400.0)

        prices = {"NVDA": 75.0, "VOO": 450.0}  # Value: 7,500  # Value: 22,500
        # Total: 30,000
        # NVDA: 7,500 / 30,000 = 0.25
        # VOO: 22,500 / 30,000 = 0.75

        allocations = portfolio.allocations(prices)

        assert allocations["NVDA"] == 0.25
        assert allocations["VOO"] == 0.75

    def test_get_positions(self):
        """Get detailed position information."""
        portfolio = Portfolio()

        portfolio.buy("NVDA", shares=100, purchase_date=date(2024, 1, 1), purchase_price=50.0)
        portfolio.buy("VOO", shares=50, purchase_date=date(2024, 1, 1), purchase_price=400.0)

        prices = {"NVDA": 75.0, "VOO": 450.0}

        positions = portfolio.get_positions(prices)

        # Should be sorted by value (VOO first with 22,500)
        assert len(positions) == 2
        assert positions[0]["ticker"] == "VOO"
        assert positions[0]["shares"] == 50
        assert positions[0]["value"] == 22500.0
        assert positions[0]["unrealized_pl"] == 2500.0

        assert positions[1]["ticker"] == "NVDA"
        assert positions[1]["shares"] == 100
        assert positions[1]["value"] == 7500.0

    def test_get_positions_excludes_empty(self):
        """get_positions excludes tickers with 0 shares."""
        portfolio = Portfolio()

        portfolio.buy("NVDA", shares=100, purchase_date=date(2024, 1, 1), purchase_price=50.0)
        portfolio.sell("NVDA", shares=100, sale_date=date(2024, 6, 1), sale_price=75.0)

        portfolio.buy("VOO", shares=50, purchase_date=date(2024, 1, 1), purchase_price=400.0)

        prices = {"NVDA": 80.0, "VOO": 450.0}

        positions = portfolio.get_positions(prices)

        # Should only include VOO (NVDA has 0 shares)
        assert len(positions) == 1
        assert positions[0]["ticker"] == "VOO"

    def test_portfolio_summary(self):
        """Get comprehensive portfolio summary."""
        portfolio = Portfolio()

        portfolio.buy("NVDA", shares=200, purchase_date=date(2024, 1, 1), purchase_price=50.0)
        portfolio.buy("VOO", shares=50, purchase_date=date(2024, 1, 1), purchase_price=400.0)

        # Sell half of NVDA
        portfolio.sell("NVDA", shares=100, sale_date=date(2024, 6, 1), sale_price=75.0)

        prices = {"NVDA": 80.0, "VOO": 450.0}  # 100 shares @ 80 = 8,000  # 50 shares @ 450 = 22,500

        summary = portfolio.portfolio_summary(prices)

        assert summary["total_tickers"] == 2
        assert summary["active_positions"] == 2
        assert summary["total_value"] == 30500.0  # 8,000 + 22,500
        assert summary["total_cost_basis"] == 25000.0  # (100 × 50) + (50 × 400)
        assert summary["realized_gain_loss"] == 2500.0  # Sold 100 @ 75 (bought @ 50)
        assert summary["unrealized_gain_loss"] == 5500.0  # NVDA +3000, VOO +2500
        assert summary["total_gain_loss"] == 8000.0  # 2500 + 5500
        assert summary["allocations"]["NVDA"] == pytest.approx(8000.0 / 30500.0)
        assert summary["allocations"]["VOO"] == pytest.approx(22500.0 / 30500.0)

    def test_complex_multi_ticker_scenario(self):
        """Test realistic multi-ticker portfolio scenario."""
        portfolio = Portfolio()

        # Build a 3-ticker portfolio
        portfolio.buy("NVDA", shares=100, purchase_date=date(2023, 1, 1), purchase_price=50.0)
        portfolio.buy("VOO", shares=50, purchase_date=date(2023, 1, 1), purchase_price=400.0)
        portfolio.buy("GLD", shares=200, purchase_date=date(2023, 1, 1), purchase_price=180.0)

        # Add more to NVDA
        portfolio.buy("NVDA", shares=50, purchase_date=date(2023, 6, 1), purchase_price=60.0)

        # Take profits on some NVDA
        portfolio.sell("NVDA", shares=75, sale_date=date(2024, 1, 1), sale_price=80.0)

        # Current prices
        prices = {"NVDA": 90.0, "VOO": 450.0, "GLD": 200.0}

        # Verify state
        assert portfolio.total_shares("NVDA") == 75  # 100 + 50 - 75
        assert portfolio.total_shares("VOO") == 50
        assert portfolio.total_shares("GLD") == 200

        # Total value: (75 × 90) + (50 × 450) + (200 × 200) = 6750 + 22500 + 40000 = 69250
        assert portfolio.total_value(prices) == 69250.0

        # Verify realized gains (sold 75 NVDA: first 100 @ 50, then partial from second lot @ 60)
        realized = portfolio.total_realized_gain_loss()
        assert realized > 0  # Made profit

        # Portfolio should have positive total return
        summary = portfolio.portfolio_summary(prices)
        assert summary["total_return_pct"] > 0
