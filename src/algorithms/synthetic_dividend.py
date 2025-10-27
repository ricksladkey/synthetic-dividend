"""Synthetic dividend algorithm: volatility harvesting strategy."""

from datetime import date
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from src.algorithms.base import AlgorithmBase
from src.models.types import Transaction
from src.models.backtest_utils import calculate_synthetic_dividend_orders
from src.models.market import Market, Order, OrderAction, OrderType


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
    
    # Maximum iterations for multi-bracket gap handling per day
    # Prevents infinite loops while allowing extreme volatility (e.g., 20 brackets)
    MAX_ITERATIONS_PER_DAY = 20

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

        # Market for order execution
        self.market: Market = Market()
        
        # Last transaction price (for order calculations)
        self.last_transaction_price: float = 0.0

    @staticmethod
    def _extract_fill_price(transaction: Transaction) -> float:
        """Extract fill price from transaction notes.
        
        Args:
            transaction: Transaction with notes containing "filled=$XX.XX"
            
        Returns:
            Fill price as float
        """
        fill_price_str = transaction.notes.split("filled=$")[1].split()[0]
        return float(fill_price_str)
    
    def _calculate_volatility_alpha(self, holdings: int, fill_price: float, quantity: int) -> float:
        """Calculate volatility alpha from a buy transaction.
        
        Args:
            holdings: Current holdings before this buy
            fill_price: Price at which shares were bought
            quantity: Number of shares bought
            
        Returns:
            Alpha as percentage
        """
        current_value = holdings * fill_price
        profit = (self.last_transaction_price - fill_price) * quantity
        return (profit / current_value) * 100 if current_value != 0 else 0.0
    
    def _unwind_buyback_stack(self, sell_quantity: int) -> None:
        """Unwind buyback stack in FIFO order.
        
        Args:
            sell_quantity: Number of shares being sold
        """
        remaining = sell_quantity
        while remaining > 0 and self.buyback_stack:
            buy_price, buy_qty = self.buyback_stack[0]
            to_unwind = min(remaining, buy_qty)
            
            if to_unwind == buy_qty:
                self.buyback_stack.pop(0)
            else:
                self.buyback_stack[0] = (buy_price, buy_qty - to_unwind)
            
            remaining -= to_unwind

    def place_orders(self, holdings: int, current_price: float) -> None:
        """Calculate and place buy/sell orders with the market.

        Clears existing orders and places new symmetric orders based on
        current holdings and price.
        
        In buyback mode: place both buy and sell orders
        In ATH-only mode: only place sell orders (no buybacks)
        """
        # Clear any pending orders (they're all based on old price/holdings)
        self.market.clear_orders()
        
        # Update transaction anchor
        self.last_transaction_price = current_price

        # Calculate symmetric buy/sell orders
        orders = calculate_synthetic_dividend_orders(
            holdings=holdings,
            last_transaction_price=current_price,
            rebalance_size=self.rebalance_size,
            profit_sharing=self.profit_sharing,
        )

        # In buyback mode: place both buy and sell orders
        if self.buyback_enabled:
            # Place buy order (if quantity > 0)
            if orders["next_buy_qty"] > 0:
                buy_order = Order(
                    action=OrderAction.BUY,
                    quantity=int(orders["next_buy_qty"]),
                    order_type=OrderType.LIMIT,
                    limit_price=orders["next_buy_price"],
                    notes="Buying back"
                )
                self.market.place_order(buy_order)
            
            # Place sell order (if quantity > 0)
            if orders["next_sell_qty"] > 0:
                sell_order = Order(
                    action=OrderAction.SELL,
                    quantity=int(orders["next_sell_qty"]),
                    order_type=OrderType.LIMIT,
                    limit_price=orders["next_sell_price"],
                    notes="Taking profits"
                )
                self.market.place_order(sell_order)
        
        # In ATH-only mode: only place sell orders
        else:
            # Only place sell order (no buybacks in ATH-only mode)
            if orders["next_sell_qty"] > 0:
                sell_order = Order(
                    action=OrderAction.SELL,
                    quantity=int(orders["next_sell_qty"]),
                    order_type=OrderType.LIMIT,
                    limit_price=orders["next_sell_price"],
                    notes=f"ATH-only sell, ATH=${self.ath_price:.2f}"
                )
                self.market.place_order(sell_order)

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
        """Evaluate day's price action and execute triggered orders.

        The Market handles trigger detection and execution mechanics.
        We iterate to handle multi-bracket gaps: after each execution,
        update holdings and check if new orders trigger.
        """
        from src.models.backtest_utils import _get_price_scalar_from_row
        
        transactions: List[Transaction] = []
        
        # ATH-only mode: update ATH price
        if not self.buyback_enabled:
            high = _get_price_scalar_from_row(price_row, "High")
            if high is not None and high > self.ath_price:
                self.ath_price = high
        
        # Iterate to handle multi-bracket gaps
        for iteration in range(1, self.MAX_ITERATIONS_PER_DAY + 1):
            # Let the market evaluate current orders against this day's price
            executed = self.market.evaluate_day(date_, price_row, max_iterations=1)
            
            if not executed:
                # No orders triggered
                break
            
            # Process each executed transaction
            for txn in executed:
                # Extract fill price from transaction notes
                fill_price = self._extract_fill_price(txn)
                
                if txn.action == "BUY":
                    # Add to buyback stack (for FIFO unwinding)
                    if self.buyback_enabled:
                        self.buyback_stack.append((fill_price, txn.qty))
                        
                        # Calculate and accumulate volatility alpha
                        alpha = self._calculate_volatility_alpha(holdings, fill_price, txn.qty)
                        self.total_volatility_alpha += alpha
                    
                    # Update holdings
                    holdings += txn.qty
                    
                elif txn.action == "SELL":
                    # Unwind buyback stack FIFO (if in full mode)
                    if self.buyback_enabled:
                        self._unwind_buyback_stack(txn.qty)
                    
                    # Update holdings
                    holdings -= txn.qty
                
                # Place new orders based on updated holdings and fill price
                self.place_orders(holdings, fill_price)
            
            # Add executed transactions to our list
            transactions.extend(executed)
        
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
