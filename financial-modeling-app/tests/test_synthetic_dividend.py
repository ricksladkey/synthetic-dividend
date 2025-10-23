"""Unit tests for synthetic dividend algorithm."""
import pytest
from src.models.backtest import calculate_synthetic_dividend_orders


class TestPlaceOrdersSymmetry:
    """Test the symmetry property: buy_qty at current bracket == sell_qty at next bracket up."""
    
    def test_symmetry_single_step(self):
        """Test that buying at lower bracket gives same qty as selling from current bracket."""
        holdings = 1000
        price = 100.0
        rebalance_size = 0.0905  # 9.05%
        profit_sharing = 0.5  # 50%
        
        # Calculate orders at current price
        current_orders = calculate_synthetic_dividend_orders(
            holdings=holdings,
            last_transaction_price=price,
            rebalance_size=rebalance_size,
            profit_sharing=profit_sharing
        )
        
        # Now calculate orders at the buy price (one bracket down)
        # After buying next_buy_qty shares, we'd have (holdings + next_buy_qty) shares
        new_holdings = holdings + current_orders["next_buy_qty"]
        lower_orders = calculate_synthetic_dividend_orders(
            holdings=new_holdings,
            last_transaction_price=current_orders["next_buy_price"],
            rebalance_size=rebalance_size,
            profit_sharing=profit_sharing
        )
        
        # The sell quantity from the lower bracket should be close to the buy quantity from current bracket
        # Note: Perfect symmetry is impossible with integer rounding when holdings change
        # We accept a difference of up to 6% of the buy quantity (minimum 3 shares) as acceptable rounding error
        diff = abs(lower_orders["next_sell_qty"] - current_orders["next_buy_qty"])
        max_acceptable_diff = max(3, int(current_orders["next_buy_qty"] * 0.06))
        assert diff <= max_acceptable_diff, (
            f"Symmetry broken beyond acceptable rounding: bought {current_orders['next_buy_qty']} shares, "
            f"would sell {lower_orders['next_sell_qty']} shares back (diff={diff}, max_acceptable={max_acceptable_diff})"
        )
    
    def test_symmetry_upward_step(self):
        """Test that selling at upper bracket matches what we'd buy back at current bracket."""
        holdings = 1000
        price = 100.0
        rebalance_size = 0.0905
        profit_sharing = 0.5
        
        # Calculate orders at current price
        current_orders = calculate_synthetic_dividend_orders(
            holdings=holdings,
            last_transaction_price=price,
            rebalance_size=rebalance_size,
            profit_sharing=profit_sharing
        )
        
        # After selling next_sell_qty shares, we'd have (holdings - next_sell_qty) shares
        new_holdings = holdings - current_orders["next_sell_qty"]
        upper_orders = calculate_synthetic_dividend_orders(
            holdings=new_holdings,
            last_transaction_price=current_orders["next_sell_price"],
            rebalance_size=rebalance_size,
            profit_sharing=profit_sharing
        )
        
        # The buy quantity from the upper bracket should be close to the sell quantity from current bracket
        # Note: Perfect symmetry is impossible with integer rounding when holdings change
        diff = abs(upper_orders["next_buy_qty"] - current_orders["next_sell_qty"])
        max_acceptable_diff = max(3, int(current_orders["next_sell_qty"] * 0.06))
        assert diff <= max_acceptable_diff, (
            f"Symmetry broken beyond acceptable rounding: sold {current_orders['next_sell_qty']} shares, "
            f"would buy back {upper_orders['next_buy_qty']} shares (diff={diff}, max_acceptable={max_acceptable_diff})"
        )
    
    @pytest.mark.parametrize("holdings,price,rebalance,profit", [
        (1000, 100.0, 0.0905, 0.5),
        (1000, 150.0, 0.0905, 0.5),
        (500, 100.0, 0.0905, 0.5),
        (1000, 100.0, 0.10, 0.5),
        (1000, 100.0, 0.0905, 0.6),
        (2000, 200.0, 0.05, 0.4),
    ])
    def test_symmetry_multiple_scenarios(self, holdings, price, rebalance, profit):
        """Test symmetry across various parameter combinations."""
        current_orders = calculate_synthetic_dividend_orders(
            holdings=holdings,
            last_transaction_price=price,
            rebalance_size=rebalance,
            profit_sharing=profit
        )
        
        # Test downward symmetry (buy at lower, sell back at current)
        new_holdings_down = holdings + current_orders["next_buy_qty"]
        lower_orders = calculate_synthetic_dividend_orders(
            holdings=new_holdings_down,
            last_transaction_price=current_orders["next_buy_price"],
            rebalance_size=rebalance,
            profit_sharing=profit
        )
        
        # Accept small rounding differences (up to 6% of quantity, minimum 3 shares)
        diff_down = abs(lower_orders["next_sell_qty"] - current_orders["next_buy_qty"])
        max_diff_down = max(3, int(current_orders["next_buy_qty"] * 0.06))
        assert diff_down <= max_diff_down, (
            f"Downward symmetry broken beyond acceptable rounding for params: holdings={holdings}, price={price}, "
            f"rebalance={rebalance}, profit={profit} (diff={diff_down}, max={max_diff_down})"
        )

        # Test upward symmetry (sell at upper, buy back at current)
        new_holdings_up = holdings - current_orders["next_sell_qty"]
        upper_orders = calculate_synthetic_dividend_orders(
            holdings=new_holdings_up,
            last_transaction_price=current_orders["next_sell_price"],
            rebalance_size=rebalance,
            profit_sharing=profit
        )

        diff_up = abs(upper_orders["next_buy_qty"] - current_orders["next_sell_qty"])
        max_diff_up = max(3, int(current_orders["next_sell_qty"] * 0.06))
        assert diff_up <= max_diff_up, (
            f"Upward symmetry broken beyond acceptable rounding for params: holdings={holdings}, price={price}, "
            f"rebalance={rebalance}, profit={profit} (diff={diff_up}, max={max_diff_up})"
        )

    def test_order_calculations_basic(self):
        """Test basic order calculation correctness."""
        holdings = 1000
        price = 100.0
        rebalance_size = 0.0905  # 9.05%
        profit_sharing = 0.5  # 50%
        
        orders = calculate_synthetic_dividend_orders(
            holdings=holdings,
            last_transaction_price=price,
            rebalance_size=rebalance_size,
            profit_sharing=profit_sharing
        )
        
        # Buy price should be lower than current
        assert orders["next_buy_price"] < price
        assert orders["next_buy_price"] == pytest.approx(price / (1 + rebalance_size))
        
        # Sell price should be higher than current
        assert orders["next_sell_price"] > price
        assert orders["next_sell_price"] == pytest.approx(price * (1 + rebalance_size))
        
        # Quantities should be positive
        assert orders["next_buy_qty"] > 0
        assert orders["next_sell_qty"] > 0
