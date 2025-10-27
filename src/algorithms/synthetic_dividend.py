"""Synthetic dividend algorithm: volatility harvesting strategy."""

from datetime import date
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from src.algorithms.base import AlgorithmBase
from src.models.types import Transaction
from src.models.backtest_utils import calculate_synthetic_dividend_orders, _get_price_scalar_from_row


class SyntheticDividendAlgorithm(AlgorithmBase):
    """Volatility harvesting algorithm that generates synthetic dividends.

    Operates in two modes:
    1. Full (buyback_enabled=True): Buy on dips, sell on rises
    2. ATH-only (buyback_enabled=False): Only sell at new all-time highs

    Parameters:
        rebalance_size_pct: Rebalance threshold (e.g. 9.15 for 9.15%)
        profit_sharing_pct: Portion of rebalance to trade (e.g. 50 for 50%)
        buyback_enabled: True for full algorithm, False for ATH-only

    Examples:
        Full: SyntheticDividendAlgorithm(9.15, 50, buyback_enabled=True)
        ATH-only: SyntheticDividendAlgorithm(9.15, 50, buyback_enabled=False)
    """

    def __init__(
        self,
        rebalance_size_pct: float = 0.0,
        profit_sharing_pct: float = 0.0,
        buyback_enabled: bool = True,
        params: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize algorithm with strategy parameters."""
        super().__init__(params)

        # Convert percentages to decimals
        self.rebalance_size: float = float(rebalance_size_pct) / 100.0
        self.profit_sharing: float = float(profit_sharing_pct) / 100.0
        self.buyback_enabled: bool = buyback_enabled

        # Cumulative alpha from volatility harvesting (full mode only)
        self.total_volatility_alpha: float = 0.0

        # All-time high tracker (ATH-only mode)
        self.ath_price: float = 0.0

        # Buyback stack for FIFO unwinding (full mode only)
        # Each entry: (purchase_price, quantity) for exact lot tracking
        self.buyback_stack: List[Tuple[float, int]] = []

        # State for pending orders
        self.last_transaction_price: float
        self.next_buy_price: float
        self.next_buy_qty: int
        self.next_sell_price: float
        self.next_sell_qty: int

    def place_orders(self, holdings: int, current_price: float) -> None:
        """Calculate and set next buy/sell orders based on current state.

        Updates instance variables with new order prices and quantities.
        """
        # Anchor next orders to this transaction price
        self.last_transaction_price = current_price

        # Calculate symmetric buy/sell orders
        orders = calculate_synthetic_dividend_orders(
            holdings=holdings,
            last_transaction_price=current_price,
            rebalance_size=self.rebalance_size,
            profit_sharing=self.profit_sharing,
        )

        # Update order state
        self.next_buy_price = orders["next_buy_price"]
        self.next_buy_qty = int(orders["next_buy_qty"])
        self.next_sell_price = orders["next_sell_price"]
        self.next_sell_qty = int(orders["next_sell_qty"])

        # Edge case: Skip orders with zero quantity (e.g., 0% profit sharing)
        # This prevents creating empty lots in the buyback stack
        if self.next_buy_qty == 0 and self.next_sell_qty == 0:
            return

        # Debug output (disabled by default for cleaner logs)
        # Uncomment for detailed order placement debugging
        # if self.buyback_enabled:
        #     print(f"Placing orders for last transaction price: ${self.last_transaction_price}")
        #     print(
        #         f"  Next BUY: {self.next_buy_qty} @ ${self.next_buy_price:.2f} = ${self.next_buy_price * self.next_buy_qty:.2f}"
        #     )
        #     print(
        #         f"  Next SELL: {self.next_sell_qty} @ ${self.next_sell_price:.2f} = ${self.next_sell_price * self.next_sell_qty:.2f}"
        #     )
        # else:
        #     print(f"ATH-only: New ATH at ${current_price:.2f}, placing sell order:")
        #     print(
        #         f"  Next SELL: {self.next_sell_qty} @ ${self.next_sell_price:.2f} = ${self.next_sell_price * self.next_sell_qty:.2f}"
        #     )

    def on_new_holdings(self, holdings: int, current_price: float) -> None:
        """Initialize algorithm state after initial purchase."""
        # ATH-only mode: seed with initial price as baseline
        if not self.buyback_enabled:
            self.ath_price = current_price

        # Calculate first set of orders
        self.place_orders(holdings, current_price)

    def on_day(
        self, date_: date, price_row: pd.Series, holdings: int, bank: float, history: pd.DataFrame
    ) -> List[Transaction]:
        """Evaluate day's price action and execute ALL triggered orders.

        CRITICAL FIX: Loops to process multiple bracket crossings on same day.
        Example: 20% gap with 9% brackets triggers 2 sells instead of 1.

        Logic:
        - ATH-only mode: Sell at all triggered price levels
        - Full mode: Buy on dips, sell on rises - loop until no more triggers
        - Orders placed as limit orders; actual price may differ due to gaps
        """
        transactions: List[Transaction] = []
        
        try:
            # Extract OHLC prices as scalars
            open_price: Optional[float] = _get_price_scalar_from_row(price_row, "Open")
            high: Optional[float] = _get_price_scalar_from_row(price_row, "High")
            low: Optional[float] = _get_price_scalar_from_row(price_row, "Low")

            # Require high/low to evaluate orders
            if low is None or high is None:
                return transactions

            # Debug output (disabled by default)
            if False:
                low_s = f"{low:.2f}"
                high_s = f"{high:.2f}"
                print(f"Evaluating orders on {date_.isoformat()}: Low=${low_s}, High=${high_s}")

            # ATH-only mode: sell at ALL triggered levels
            if not self.buyback_enabled:
                # Loop to process multiple sells if gap crosses multiple brackets
                max_iterations = 20  # Safety limit to prevent infinite loops
                iteration = 0
                
                while iteration < max_iterations:
                    iteration += 1
                    
                    if high > self.ath_price:
                        # Record new ATH
                        self.ath_price = high

                        # Check if sell threshold reached
                        if high >= self.next_sell_price and self.next_sell_qty > 0:
                            # Use open if market gapped up, else use limit price
                            actual_price = (
                                max(self.next_sell_price, open_price)
                                if open_price is not None
                                else self.next_sell_price
                            )
                            notes = f"ATH-only sell #{iteration}: limit price = {self.next_sell_price:.2f}, actual price = {actual_price:.2f}, new ATH = {self.ath_price:.2f}"
                            transaction = Transaction(
                                action="SELL", qty=self.next_sell_qty, notes=notes
                            )
                            transactions.append(transaction)

                            # Update orders and holdings for next potential sell
                            holdings -= self.next_sell_qty
                            self.place_orders(holdings, self.next_sell_price)
                            
                            # Continue loop to check if high triggers another sell
                        else:
                            # No more sells triggered
                            break
                    else:
                        # Price didn't exceed ATH
                        break
                
                return transactions

            # Full mode: loop to process ALL triggered orders (buys and sells)
            max_iterations = 20  # Safety limit
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                transaction_executed = False

                # Buy trigger: price dropped to or below buy threshold
                if low <= self.next_buy_price and self.next_buy_qty > 0:
                    # Fill at open if market gapped down, else at limit price
                    actual_price = (
                        min(self.next_buy_price, open_price)
                        if open_price is not None
                        else self.next_buy_price
                    )

                    # Push buyback to stack for FIFO unwinding
                    self.buyback_stack.append((actual_price, self.next_buy_qty))

                    # Calculate alpha: profit from buying back cheaper shares
                    current_value = holdings * actual_price
                    profit = (self.last_transaction_price - actual_price) * self.next_buy_qty
                    alpha = (profit / current_value) * 100 if current_value != 0 else 0.0
                    self.total_volatility_alpha += alpha

                    notes = f"Buying back #{iteration}: limit price = {self.next_buy_price:.2f}, actual price = {actual_price:.2f}"
                    transaction = Transaction(action="BUY", qty=self.next_buy_qty, notes=notes)
                    transactions.append(transaction)

                    # Update holdings and orders for next potential buy
                    holdings += self.next_buy_qty
                    self.place_orders(holdings, self.next_buy_price)
                    transaction_executed = True

                # Sell trigger: price rose to or above sell threshold
                if high >= self.next_sell_price and self.next_sell_qty > 0:
                    # Fill at open if market gapped up, else at limit price
                    actual_price = (
                        max(self.next_sell_price, open_price)
                        if open_price is not None
                        else self.next_sell_price
                    )

                    # Unwind buyback stack FIFO before selling initial shares
                    sell_qty_remaining = self.next_sell_qty
                    unwound_from_stack = 0

                    while sell_qty_remaining > 0 and self.buyback_stack:
                        buy_price, buy_qty = self.buyback_stack[0]
                        to_unwind = min(sell_qty_remaining, buy_qty)

                        # This lot is now fully or partially unwound
                        if to_unwind == buy_qty:
                            # Fully unwound - remove from stack
                            self.buyback_stack.pop(0)
                        else:
                            # Partially unwound - update remaining quantity
                            self.buyback_stack[0] = (buy_price, buy_qty - to_unwind)

                        unwound_from_stack += to_unwind
                        sell_qty_remaining -= to_unwind

                    # Note about what we unwound
                    if unwound_from_stack > 0:
                        notes = f"Taking profits #{iteration}: limit price = {self.next_sell_price:.2f}, actual price = {actual_price:.2f} (unwound {unwound_from_stack} from buyback stack)"
                    else:
                        notes = f"Taking profits #{iteration}: limit price = {self.next_sell_price:.2f}, actual price = {actual_price:.2f}"

                    transaction = Transaction(action="SELL", qty=self.next_sell_qty, notes=notes)
                    transactions.append(transaction)

                    # Update holdings and orders for next potential sell
                    holdings -= self.next_sell_qty
                    self.place_orders(holdings, self.next_sell_price)
                    transaction_executed = True

                # If no transaction was executed this iteration, we're done
                if not transaction_executed:
                    break

        except Exception:
            # Silently ignore errors (e.g., missing price data)
            pass
        
        return transactions

    def on_end_holding(self) -> None:
        """Print summary statistics after backtest completes."""
        if self.buyback_enabled:
            print(
                f"Synthetic Dividend Algorithm total volatility alpha: {self.total_volatility_alpha:.2f}%"
            )
            # Show buyback stack status
            if self.buyback_stack:
                total_stack_qty = sum(qty for _, qty in self.buyback_stack)
                print(
                    f"  Buyback stack: {len(self.buyback_stack)} lots with {total_stack_qty} total shares not yet unwound"
                )
            else:
                print("  Buyback stack: empty (all lots unwound)")
        else:
            print(f"ATH-only algorithm: final ATH = ${self.ath_price:.2f}")
