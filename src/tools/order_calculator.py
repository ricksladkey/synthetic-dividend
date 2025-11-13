"""Order Calculator - Calculate exact limit orders for manual trading.

This tool calculates the precise buy and sell limit orders you need to place
based on your last transaction price and current holdings.

Usage:
    python -m src.tools.order_calculator --ticker NVDA --holdings 1000 --last-price 120.50 --current-price 125.30 --sdn 8 --profit 50

Output:
    - Next BUY limit price and quantity
    - Next SELL limit price and quantity
    - Bracket position information (normalized to standard positions)
    - Ready to copy/paste into your broker
"""

import argparse
import math
from typing import Optional, Tuple

from src.models.backtest import calculate_synthetic_dividend_orders


def calculate_orders_for_manual_entry(
    ticker: str,
    holdings: float,
    last_transaction_price: float,
    current_price: float,
    sdn: int,
    profit_sharing_pct: float,
    bracket_seed: Optional[float] = None,
) -> Tuple[float, float, float, float]:
    """Calculate buy/sell orders for manual placement.

    Args:
        ticker: Asset ticker symbol (for display)
        holdings: Current share count
        last_transaction_price: Price of last buy/sell transaction
        current_price: Current market price
        sdn: Rebalancing frequency (sd4, sd6, sd8, etc.)
        profit_sharing_pct: Profit sharing percentage (0-100)
        bracket_seed: Optional seed price to align bracket positions (e.g., 100.0)

    Returns:
        Tuple of (buy_price, buy_qty, sell_price, sell_qty)
    """
    # Calculate rebalance threshold from sdN format
    # Formula: 2^(1/N) - 1
    rebalance_size = (2.0 ** (1.0 / float(sdn))) - 1.0
    profit_sharing = profit_sharing_pct / 100.0

    # Calculate orders
    orders = calculate_synthetic_dividend_orders(
        holdings=holdings,
        last_transaction_price=last_transaction_price,
        rebalance_size=rebalance_size,
        profit_sharing=profit_sharing,
        bracket_seed=bracket_seed,
    )

    return (
        orders["next_buy_price"],
        orders["next_buy_qty"],
        orders["next_sell_price"],
        orders["next_sell_qty"],
    )


def format_order_display(
    ticker: str,
    holdings: float,
    last_price: float,
    current_price: float,
    buy_price: float,
    buy_qty: float,
    sell_price: float,
    sell_qty: float,
    sdn: int,
    profit_pct: float,
    bracket_seed: Optional[float] = None,
) -> str:
    """Format order information for easy copy/paste.

    Returns:
        Formatted string with order details
    """
    # Calculate price changes
    price_change = current_price - last_price
    price_change_pct = (price_change / last_price * 100) if last_price > 0 else 0

    # Calculate distances to triggers
    buy_trigger_pct = (last_price - buy_price) / last_price * 100
    sell_trigger_pct = (sell_price - last_price) / last_price * 100

    # Distance from current price to triggers
    to_buy_pct = (current_price - buy_price) / current_price * 100
    to_sell_pct = (sell_price - current_price) / current_price * 100

    rebalance_pct = ((2.0 ** (1.0 / float(sdn))) - 1.0) * 100

    # Calculate bracket positions (normalized to base 1.0)
    trigger_decimal = rebalance_pct / 100.0

    # Current bracket (based on last transaction price)
    current_bracket_n = math.log(last_price) / math.log(1 + trigger_decimal)
    current_bracket_normalized = math.pow(1 + trigger_decimal, round(current_bracket_n))

    # Buy bracket (one step down)
    buy_bracket_n = math.log(buy_price) / math.log(1 + trigger_decimal)
    buy_bracket_normalized = math.pow(1 + trigger_decimal, round(buy_bracket_n))

    # Sell bracket (one step up)
    sell_bracket_n = math.log(sell_price) / math.log(1 + trigger_decimal)
    sell_bracket_normalized = math.pow(1 + trigger_decimal, round(sell_bracket_n))

    # Build seed information text if seed is provided
    seed_info = ""
    if bracket_seed is not None and bracket_seed > 0:
        seed_bracket_n = math.log(bracket_seed) / math.log(1 + trigger_decimal)
        seed_info = f"\n  Bracket Seed:          ${bracket_seed:.2f}  (bracket n={round(seed_bracket_n)}, aligns all positions)"

    # Format box lines with proper alignment
    content_width = 67  # For lines between | |

    empty_line = f"  |{'':<{content_width}}|"
    buy_price_line = f"  |{f'  Price:     ${buy_price:.2f}':<{content_width}}|"
    buy_qty_line = f"  |{f'  Quantity:  {buy_qty:,.2f} shares':<{content_width}}|"
    buy_total_line = f"  |{f'  Total:     ${buy_price * buy_qty:,.2f}':<{content_width}}|"
    buy_trigger_line = (
        f"  |{f'  Trigger:   {buy_trigger_pct:.2f}% below last transaction':<{content_width}}|"
    )
    buy_distance_line = (
        f"  |{f'  Distance:  {to_buy_pct:.2f}% below current price':<{content_width}}|"
    )

    sell_price_line = f"  |{f'  Price:     ${sell_price:.2f}':<{content_width}}|"
    sell_qty_line = f"  |{f'  Quantity:  {sell_qty:,.2f} shares':<{content_width}}|"
    sell_total_line = f"  |{f'  Total:     ${sell_price * sell_qty:,.2f}':<{content_width}}|"
    sell_trigger_line = (
        f"  |{f'  Trigger:   {sell_trigger_pct:.2f}% above last transaction':<{content_width}}|"
    )
    sell_distance_line = (
        f"  |{f'  Distance:  {to_sell_pct:.2f}% above current price':<{content_width}}|"
    )

    output = f"""
+==============================================================================+
|                       SYNTHETIC DIVIDEND ORDER CALCULATOR                     |
+==============================================================================+

* CURRENT POSITION - {ticker}
==============================================================================
  Holdings:              {holdings:,.2f} shares
  Last Transaction:      ${last_price:.2f}  (bracket n={round(current_bracket_n)}, normalized=${current_bracket_normalized:.2f}){seed_info}
  Current Price:         ${current_price:.2f}
  Price Change:          ${price_change:+.2f} ({price_change_pct:+.2f}%)

  Strategy:              sd{sdn} ({rebalance_pct:.2f}% rebalance, {profit_pct:.0f}% profit sharing)

* BRACKET POSITIONS
==============================================================================
  Your position is on bracket n={round(current_bracket_n)}

  Standard bracket ladder for sd{sdn} (normalized to 1.0):
    Bracket n={round(buy_bracket_n):4} -> ${buy_bracket_normalized:8.2f} [BUY TARGET]
    Bracket n={round(current_bracket_n):4} -> ${current_bracket_normalized:8.2f} [YOUR POSITION]
    Bracket n={round(sell_bracket_n):4} -> ${sell_bracket_normalized:8.2f} [SELL TARGET]

  * All backtests using sd{sdn} will hit these same bracket positions,
    making your strategy deterministic and comparable.

* LIMIT ORDERS TO PLACE
==============================================================================

  +-- BUY LIMIT ORDER ------------------------------------------------+
{empty_line}
{buy_price_line}
{buy_qty_line}
{buy_total_line}
{empty_line}
{buy_trigger_line}
{buy_distance_line}
{empty_line}
  +-------------------------------------------------------------------+

  +-- SELL LIMIT ORDER -----------------------------------------------+
{empty_line}
{sell_price_line}
{sell_qty_line}
{sell_total_line}
{empty_line}
{sell_trigger_line}
{sell_distance_line}
{empty_line}
  +-------------------------------------------------------------------+

* BROKER ENTRY (Copy/Paste)
==============================================================================

  BUY  {ticker:5} {buy_qty:8.2f} @ ${buy_price:.2f}  (LIMIT GTC)
  SELL {ticker:5} {sell_qty:8.2f} @ ${sell_price:.2f}  (LIMIT GTC)

==============================================================================
* TIP: Set both orders as "Good Till Canceled" (GTC) limit orders
       Cancel and replace when either executes
==============================================================================
"""
    return output


def main():
    """Main entry point for order calculator."""
    parser = argparse.ArgumentParser(
        description="Calculate limit orders for synthetic dividend manual trading",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic calculation
  python -m src.tools.order_calculator --ticker NVDA --holdings 1000 --last-price 120.50 --current-price 125.30 --sdn 8 --profit 50

  # With bracket seed for aligned positions
  python -m src.tools.order_calculator --ticker NVDA --holdings 1000 --last-price 120.50 --current-price 125.30 --sdn 8 --profit 50 --bracket-seed 100.0

  # Different strategy
  python -m src.tools.order_calculator --ticker BTC-USD --holdings 0.5 --last-price 45000 --current-price 46500 --sdn 4 --profit 75

  # Quick recalculation after a trade
  python -m src.tools.order_calculator --ticker MSTR --holdings 250 --last-price 380.50 --current-price 385.20 --sdn 6 --profit 50
        """,
    )

    parser.add_argument("--ticker", required=True, help="Asset ticker symbol (e.g., NVDA, BTC-USD)")
    parser.add_argument(
        "--holdings", type=float, required=True, help="Current number of shares/units"
    )
    parser.add_argument(
        "--last-price", type=float, required=True, help="Price of last transaction (buy or sell)"
    )
    parser.add_argument(
        "--current-price", type=float, required=True, help="Current market price (for reference)"
    )
    parser.add_argument(
        "--sdn", type=int, required=True, help="Rebalancing frequency (4, 6, 8, 10, 12, 16)"
    )
    parser.add_argument(
        "--profit", type=float, required=True, help="Profit sharing percentage (0-100)"
    )
    parser.add_argument(
        "--bracket-seed",
        type=float,
        default=None,
        help="Optional seed price to align bracket positions (e.g., 100.0). "
        "When provided, all bracket calculations align to a common ladder based on this seed.",
    )

    args = parser.parse_args()

    # Validate inputs
    if args.holdings <= 0:
        parser.error("Holdings must be positive")
    if args.last_price <= 0:
        parser.error("Last price must be positive")
    if args.current_price <= 0:
        parser.error("Current price must be positive")
    if args.sdn < 2 or args.sdn > 20:
        parser.error("sdN must be between 2 and 20 (typically 4-16)")
    if args.profit < 0 or args.profit > 200:
        parser.error("Profit sharing must be between 0 and 200%")

    # Calculate orders
    buy_price, buy_qty, sell_price, sell_qty = calculate_orders_for_manual_entry(
        ticker=args.ticker,
        holdings=args.holdings,
        last_transaction_price=args.last_price,
        current_price=args.current_price,
        sdn=args.sdn,
        profit_sharing_pct=args.profit,
        bracket_seed=args.bracket_seed,
    )

    # Display formatted output
    output = format_order_display(
        ticker=args.ticker,
        holdings=args.holdings,
        last_price=args.last_price,
        current_price=args.current_price,
        buy_price=buy_price,
        buy_qty=buy_qty,
        sell_price=sell_price,
        sell_qty=sell_qty,
        sdn=args.sdn,
        profit_pct=args.profit,
        bracket_seed=args.bracket_seed,
    )

    print(output)


if __name__ == "__main__":
    main()
