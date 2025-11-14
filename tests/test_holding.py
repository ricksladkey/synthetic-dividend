"""
Test suite for Holding and Transaction models.

Tests the foundational transaction-based position tracking abstraction.
"""

from datetime import date

import pytest

from src.models.holding import Holding, Transaction


class TestTransaction:
    """Test the Transaction model."""

    def test_create_buy_transaction(self):
        """Can create a valid BUY transaction."""
        txn = Transaction(
            transaction_type="BUY",
            shares=100,
            purchase_date=date(2024, 1, 1),
            purchase_price=50.0,
            notes="Initial purchase",
        )

        assert txn.transaction_type == "BUY"
        assert txn.shares == 100
        assert txn.purchase_price == 50.0
        assert txn.is_open
        assert not txn.is_closed

    def test_create_closed_transaction(self):
        """Can create a closed transaction with sale info."""
        txn = Transaction(
            transaction_type="BUY",
            shares=100,
            purchase_date=date(2024, 1, 1),
            purchase_price=50.0,
            sale_date=date(2024, 6, 1),
            sale_price=75.0,
        )

        assert txn.is_closed
        assert not txn.is_open
        assert txn.sale_date == date(2024, 6, 1)
        assert txn.sale_price == 75.0

    def test_invalid_transaction_type(self):
        """Reject invalid transaction types."""
        with pytest.raises(ValueError, match="must be 'BUY' or 'SELL'"):
            Transaction(
                transaction_type="HOLD",
                shares=100,
                purchase_date=date(2024, 1, 1),
                purchase_price=50.0,
            )

    def test_negative_shares_rejected(self):
        """Reject negative share quantities."""
        with pytest.raises(ValueError, match="shares must be positive"):
            Transaction(
                transaction_type="BUY",
                shares=-100,
                purchase_date=date(2024, 1, 1),
                purchase_price=50.0,
            )

    def test_zero_price_rejected(self):
        """Reject zero or negative prices."""
        with pytest.raises(ValueError, match="purchase_price must be positive"):
            Transaction(
                transaction_type="BUY",
                shares=100,
                purchase_date=date(2024, 1, 1),
                purchase_price=0.0,
            )

    def test_partial_sale_info_rejected(self):
        """Reject transactions with only sale_date or only sale_price."""
        with pytest.raises(ValueError, match="sale_date and sale_price must both be set"):
            Transaction(
                transaction_type="BUY",
                shares=100,
                purchase_date=date(2024, 1, 1),
                purchase_price=50.0,
                sale_date=date(2024, 6, 1),
                sale_price=None,  # Missing sale_price
            )

    def test_sale_before_purchase_rejected(self):
        """Reject sale dates before purchase dates."""
        with pytest.raises(ValueError, match="sale_date.*cannot be before purchase_date"):
            Transaction(
                transaction_type="BUY",
                shares=100,
                purchase_date=date(2024, 6, 1),
                purchase_price=50.0,
                sale_date=date(2024, 1, 1),  # Before purchase
                sale_price=75.0,
            )

    def test_close_open_transaction(self):
        """Can close an open transaction."""
        txn = Transaction(
            transaction_type="BUY", shares=100, purchase_date=date(2024, 1, 1), purchase_price=50.0
        )

        assert txn.is_open

        txn.close(sale_date=date(2024, 6, 1), sale_price=75.0)

        assert txn.is_closed
        assert txn.sale_date == date(2024, 6, 1)
        assert txn.sale_price == 75.0

    def test_cannot_close_already_closed(self):
        """Cannot close an already closed transaction."""
        txn = Transaction(
            transaction_type="BUY",
            shares=100,
            purchase_date=date(2024, 1, 1),
            purchase_price=50.0,
            sale_date=date(2024, 6, 1),
            sale_price=75.0,
        )

        with pytest.raises(ValueError, match="already closed"):
            txn.close(sale_date=date(2024, 7, 1), sale_price=80.0)

    def test_market_value_open_position(self):
        """Market value for open positions uses current price."""
        txn = Transaction(
            transaction_type="BUY", shares=100, purchase_date=date(2024, 1, 1), purchase_price=50.0
        )

        assert txn.market_value(current_price=60.0) == 6000.0
        assert txn.market_value(current_price=40.0) == 4000.0

    def test_market_value_closed_position(self):
        """Market value for closed positions is zero."""
        txn = Transaction(
            transaction_type="BUY",
            shares=100,
            purchase_date=date(2024, 1, 1),
            purchase_price=50.0,
            sale_date=date(2024, 6, 1),
            sale_price=75.0,
        )

        assert txn.market_value(current_price=100.0) == 0.0

    def test_realized_gain(self):
        """Calculate realized gain on closed position."""
        txn = Transaction(
            transaction_type="BUY",
            shares=100,
            purchase_date=date(2024, 1, 1),
            purchase_price=50.0,
            sale_date=date(2024, 6, 1),
            sale_price=75.0,
        )

        # Bought at 50, sold at 75: $25 profit per share × 100 shares = $2500
        assert txn.realized_gain_loss() == 2500.0

    def test_realized_loss(self):
        """Calculate realized loss on closed position."""
        txn = Transaction(
            transaction_type="BUY",
            shares=100,
            purchase_date=date(2024, 1, 1),
            purchase_price=50.0,
            sale_date=date(2024, 6, 1),
            sale_price=40.0,
        )

        # Bought at 50, sold at 40: $10 loss per share × 100 shares = -$1000
        assert txn.realized_gain_loss() == -1000.0

    def test_realized_gain_none_when_open(self):
        """Realized gain is None for open positions."""
        txn = Transaction(
            transaction_type="BUY", shares=100, purchase_date=date(2024, 1, 1), purchase_price=50.0
        )

        assert txn.realized_gain_loss() is None

    def test_unrealized_gain(self):
        """Calculate unrealized gain on open position."""
        txn = Transaction(
            transaction_type="BUY", shares=100, purchase_date=date(2024, 1, 1), purchase_price=50.0
        )

        # Cost basis: $5000, Current value at 60: $6000, Gain: $1000
        assert txn.unrealized_gain_loss(current_price=60.0) == 1000.0

    def test_unrealized_loss(self):
        """Calculate unrealized loss on open position."""
        txn = Transaction(
            transaction_type="BUY", shares=100, purchase_date=date(2024, 1, 1), purchase_price=50.0
        )

        # Cost basis: $5000, Current value at 40: $4000, Loss: -$1000
        assert txn.unrealized_gain_loss(current_price=40.0) == -1000.0

    def test_unrealized_gain_none_when_closed(self):
        """Unrealized gain is None for closed positions."""
        txn = Transaction(
            transaction_type="BUY",
            shares=100,
            purchase_date=date(2024, 1, 1),
            purchase_price=50.0,
            sale_date=date(2024, 6, 1),
            sale_price=75.0,
        )

        assert txn.unrealized_gain_loss(current_price=100.0) is None


class TestHolding:
    """Test the Holding model."""

    def test_create_empty_holding(self):
        """Can create an empty holding."""
        holding = Holding(ticker="NVDA")

        assert holding.ticker == "NVDA"
        assert len(holding.transactions) == 0
        assert holding.current_shares() == 0

    def test_add_single_buy(self):
        """Can add a buy transaction."""
        holding = Holding(ticker="NVDA")

        txn = holding.add_buy(
            shares=100,
            purchase_date=date(2024, 1, 1),
            purchase_price=50.0,
            notes="Initial purchase",
        )

        assert len(holding.transactions) == 1
        assert holding.current_shares() == 100
        assert txn.transaction_type == "BUY"
        assert txn.shares == 100

    def test_add_multiple_buys(self):
        """Can add multiple buy transactions."""
        holding = Holding(ticker="NVDA")

        holding.add_buy(shares=100, purchase_date=date(2024, 1, 1), purchase_price=50.0)
        holding.add_buy(shares=50, purchase_date=date(2024, 2, 1), purchase_price=55.0)
        holding.add_buy(shares=75, purchase_date=date(2024, 3, 1), purchase_price=52.0)

        assert len(holding.transactions) == 3
        assert holding.current_shares() == 225

    def test_add_sell_simple(self):
        """Can sell entire position."""
        holding = Holding(ticker="NVDA")
        holding.add_buy(shares=100, purchase_date=date(2024, 1, 1), purchase_price=50.0)

        sell_txns = holding.add_sell(
            shares=100, sale_date=date(2024, 6, 1), sale_price=75.0, notes="Full exit"
        )

        assert holding.current_shares() == 0
        assert len(sell_txns) == 1
        assert sell_txns[0].transaction_type == "SELL"

    def test_add_sell_partial(self):
        """Can sell partial position."""
        holding = Holding(ticker="NVDA")
        holding.add_buy(shares=100, purchase_date=date(2024, 1, 1), purchase_price=50.0)

        holding.add_sell(shares=40, sale_date=date(2024, 6, 1), sale_price=75.0)

        assert holding.current_shares() == 60

    def test_sell_more_than_held_rejected(self):
        """Cannot sell more shares than currently held."""
        holding = Holding(ticker="NVDA")
        holding.add_buy(shares=100, purchase_date=date(2024, 1, 1), purchase_price=50.0)

        with pytest.raises(ValueError, match="Cannot sell 150 shares.*only 100.0 shares held"):
            holding.add_sell(shares=150, sale_date=date(2024, 6, 1), sale_price=75.0)

    def test_fifo_lot_selection(self):
        """FIFO: Sell oldest lots first."""
        holding = Holding(ticker="NVDA")

        # Three buys at different prices
        holding.add_buy(shares=100, purchase_date=date(2024, 1, 1), purchase_price=50.0)
        holding.add_buy(shares=100, purchase_date=date(2024, 2, 1), purchase_price=55.0)
        holding.add_buy(shares=100, purchase_date=date(2024, 3, 1), purchase_price=60.0)

        # Sell 150 shares (should take all of lot 1 and half of lot 2)
        holding.add_sell(shares=150, sale_date=date(2024, 6, 1), sale_price=70.0)

        # Should have 150 shares remaining (50 from lot 2, 100 from lot 3)
        assert holding.current_shares() == 150

        # Verify FIFO: First lot should be fully closed (100 shares)
        # Second lot should be partially closed (50 shares sold, 50 remaining)
        open_lots = holding.get_open_lots()
        closed_lots = holding.get_closed_lots()

        # Two lots closed: lot 1 (100 shares) + partial lot 2 (50 shares)
        assert len(closed_lots) == 2
        assert closed_lots[0].purchase_price == 50.0  # First lot
        assert closed_lots[0].shares == 100
        assert closed_lots[1].purchase_price == 55.0  # Partial second lot
        assert closed_lots[1].shares == 50

        # Remaining open lots: partial lot 2 (50 shares) + lot 3 (100 shares)
        assert len(open_lots) == 2
        assert sum(lot.shares for lot in open_lots) == 150

    def test_market_value(self):
        """Calculate total market value."""
        holding = Holding(ticker="NVDA")

        holding.add_buy(shares=100, purchase_date=date(2024, 1, 1), purchase_price=50.0)
        holding.add_buy(shares=50, purchase_date=date(2024, 2, 1), purchase_price=55.0)

        # 150 shares at current price of $80
        assert holding.market_value(current_price=80.0) == 12000.0

    def test_cost_basis(self):
        """Calculate total cost basis."""
        holding = Holding(ticker="NVDA")

        holding.add_buy(shares=100, purchase_date=date(2024, 1, 1), purchase_price=50.0)
        holding.add_buy(shares=50, purchase_date=date(2024, 2, 1), purchase_price=60.0)

        # Cost basis: (100 × 50) + (50 × 60) = 5000 + 3000 = 8000
        assert holding.cost_basis() == 8000.0

    def test_average_cost_basis(self):
        """Calculate weighted average cost per share."""
        holding = Holding(ticker="NVDA")

        holding.add_buy(shares=100, purchase_date=date(2024, 1, 1), purchase_price=50.0)
        holding.add_buy(shares=50, purchase_date=date(2024, 2, 1), purchase_price=62.0)

        # Total cost: 5000 + 3100 = 8100
        # Total shares: 150
        # Average: 8100 / 150 = 54.0
        assert holding.average_cost_basis() == 54.0

    def test_average_cost_basis_empty(self):
        """Average cost basis is 0 for empty holding."""
        holding = Holding(ticker="NVDA")
        assert holding.average_cost_basis() == 0.0

    def test_unrealized_gain_loss(self):
        """Calculate unrealized P/L on open positions."""
        holding = Holding(ticker="NVDA")

        holding.add_buy(shares=100, purchase_date=date(2024, 1, 1), purchase_price=50.0)

        # Cost basis: $5000, Current value at 60: $6000, Unrealized gain: $1000
        assert holding.unrealized_gain_loss(current_price=60.0) == 1000.0

    def test_realized_gain_loss(self):
        """Calculate realized P/L from closed positions."""
        holding = Holding(ticker="NVDA")

        holding.add_buy(shares=100, purchase_date=date(2024, 1, 1), purchase_price=50.0)
        holding.add_sell(shares=100, sale_date=date(2024, 6, 1), sale_price=75.0)

        # Bought at 50, sold at 75: $25 profit per share × 100 shares = $2500
        assert holding.realized_gain_loss() == 2500.0

    def test_total_gain_loss(self):
        """Calculate total P/L (realized + unrealized)."""
        holding = Holding(ticker="NVDA")

        # Buy 200 shares
        holding.add_buy(shares=200, purchase_date=date(2024, 1, 1), purchase_price=50.0)

        # Sell 100 shares at 75 (realized gain: $2500)
        holding.add_sell(shares=100, sale_date=date(2024, 6, 1), sale_price=75.0)

        # Remaining 100 shares now worth $80 (unrealized gain: $3000)
        # Total: $2500 + $3000 = $5500
        assert holding.total_gain_loss(current_price=80.0) == 5500.0

    def test_transaction_summary(self):
        """Get summary statistics."""
        holding = Holding(ticker="NVDA")

        holding.add_buy(shares=100, purchase_date=date(2024, 1, 1), purchase_price=50.0)
        holding.add_buy(shares=50, purchase_date=date(2024, 2, 1), purchase_price=60.0)
        holding.add_sell(shares=75, sale_date=date(2024, 6, 1), sale_price=70.0)

        summary = holding.transaction_summary()

        assert summary["ticker"] == "NVDA"
        assert summary["current_shares"] == 75
        assert summary["open_lots"] >= 1
        assert summary["closed_lots"] >= 1
        assert summary["sell_transactions"] >= 1

    def test_get_open_lots(self):
        """Can retrieve open lots."""
        holding = Holding(ticker="NVDA")

        holding.add_buy(shares=100, purchase_date=date(2024, 1, 1), purchase_price=50.0)
        holding.add_buy(shares=50, purchase_date=date(2024, 2, 1), purchase_price=60.0)
        holding.add_sell(shares=100, sale_date=date(2024, 6, 1), sale_price=70.0)

        open_lots = holding.get_open_lots()

        # Should have 50 shares remaining (from second buy)
        assert len(open_lots) >= 1
        assert sum(lot.shares for lot in open_lots) == 50

    def test_complex_scenario(self):
        """Test realistic scenario with multiple buys and sells."""
        holding = Holding(ticker="NVDA")

        # Year 1: Accumulation phase
        holding.add_buy(shares=100, purchase_date=date(2023, 1, 1), purchase_price=50.0)
        holding.add_buy(shares=100, purchase_date=date(2023, 3, 1), purchase_price=55.0)
        holding.add_buy(shares=100, purchase_date=date(2023, 6, 1), purchase_price=60.0)

        assert holding.current_shares() == 300

        # Year 2: Take some profits
        holding.add_sell(shares=150, sale_date=date(2024, 1, 1), sale_price=80.0)

        assert holding.current_shares() == 150

        # Verify P/L
        realized = holding.realized_gain_loss()
        # First 100 at 50 → 80 = +$3000
        # Next 50 at 55 → 80 = +$1250
        # Total realized: ~$4250
        assert realized > 4000

        # Current value should be positive (bought at 55-60, current price higher)
        unrealized = holding.unrealized_gain_loss(current_price=90.0)
        assert unrealized > 0
