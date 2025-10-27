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

    This algorithm exploits mean reversion by systematically buying on dips and 
    selling on rises within a symmetrically-spaced bracket system. It operates as 
    a volatility-harvesting strategy that generates cash flow ("synthetic dividends") 
    from price oscillations.

    Operating Modes:
        Full (buyback_enabled=True): 
            Complete volatility harvesting with symmetric buy/sell brackets.
            Maintains a buyback stack for FIFO lot tracking and profit calculation.
        
        ATH-only (buyback_enabled=False): 
            Baseline comparison mode that only sells at new all-time highs.
            No buybacks, no stack management - pure upside capture only.

    Parameters:
        rebalance_size: Bracket spacing as decimal (e.g., 0.0915 = 9.15% brackets)
        profit_sharing: Trade size as fraction of rebalance (e.g., 0.5 = 50%)
        buyback_enabled: True for full algorithm, False for ATH-only baseline

    Mathematical Foundation:
        The algorithm places symmetric limit orders at prices:
            Buy:  P_current / (1 + r)
            Sell: P_current × (1 + r)
        
        Where r = rebalance_size ensures geometric symmetry for exact FIFO unwinding.

    Examples:
        Full: SyntheticDividendAlgorithm(0.0915, 0.5, buyback_enabled=True)
        ATH-only: SyntheticDividendAlgorithm(0.0915, 0.5, buyback_enabled=False)
    """
    
    # Maximum iterations for multi-bracket gap handling per day
    # In extreme volatility (e.g., 20% gap = ~2 brackets), we need multiple iterations
    # to create separate FIFO stack entries for exact symmetry. Limit prevents infinite loops.
    MAX_ITERATIONS_PER_DAY = 20

    def __init__(
        self,
        rebalance_size: float = 0.0,
        profit_sharing: float = 0.0,
        buyback_enabled: bool = True,
        lot_selection: str = "LIFO",
        params: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize algorithm with strategy parameters.
        
        Args:
            rebalance_size: Bracket spacing as decimal (e.g., 0.0915 for 9.15%)
            profit_sharing: Trade size as fraction (e.g., 0.5 for 50%)
            buyback_enabled: True for full mode, False for ATH-only
            lot_selection: Lot selection method ('FIFO', 'LIFO') - default LIFO
            params: Optional dict for base class compatibility
        """
        super().__init__(params)

        # Strategy parameters (stored as mathematical decimals, not percentages)
        self.rebalance_size: float = float(rebalance_size)
        self.profit_sharing: float = float(profit_sharing)
        self.buyback_enabled: bool = buyback_enabled
        self.lot_selection: str = lot_selection

        # Performance tracking: cumulative alpha from volatility harvesting
        self.total_volatility_alpha: float = 0.0

        # ATH-only mode: track all-time high for baseline comparison
        self.ath_price: float = 0.0

        # FIFO lot tracking for exact profit calculation
        # Each entry: (purchase_price, quantity) representing one buy transaction
        # Unwound in FIFO order on sells to maintain symmetry
        self.buyback_stack: List[Tuple[float, int]] = []

        # Market interface: handles order placement, triggering, and execution
        self.market: Market = Market()
        
        # Transaction price anchor: updated after each fill for symmetric order placement
        self.last_transaction_price: float = 0.0

    @staticmethod
    def _extract_fill_price(transaction: Transaction) -> float:
        """Extract fill price from transaction notes.
        
        Transaction notes format: "...filled=$XX.XX..."
        This parsing maintains separation between transaction data and execution details.
        
        Args:
            transaction: Transaction with notes containing fill price
            
        Returns:
            Fill price as float
        """
        fill_price_str = transaction.notes.split("filled=$")[1].split()[0]
        return float(fill_price_str)
    
    def _calculate_volatility_alpha(self, holdings: int, fill_price: float, quantity: int) -> float:
        """Calculate volatility alpha from a buy transaction.
        
        Volatility alpha measures the profit from mean reversion as a percentage
        of current portfolio value. It represents the "free money" extracted from
        price oscillations.
        
        Formula: alpha = (P_last - P_fill) × qty / (holdings × P_fill) × 100
        
        Args:
            holdings: Current holdings before this buy
            fill_price: Price at which shares were bought
            quantity: Number of shares bought
            
        Returns:
            Alpha as percentage of portfolio value
        """
        current_value = holdings * fill_price
        profit = (self.last_transaction_price - fill_price) * quantity
        return (profit / current_value) * 100 if current_value != 0 else 0.0
    
    def _unwind_buyback_stack(self, sell_quantity: int) -> None:
        """Unwind buyback stack using configured lot selection method.
        
        FIFO (First-In-First-Out) unwinding:
        - Sells oldest purchases first (default for buy-and-hold parity)
        - Multi-bracket gaps unwind one bracket at a time
        - Exact lot tracking and symmetric profit calculation
        
        LIFO (Last-In-First-Out) unwinding:
        - Sells newest purchases first (tax-efficient in some jurisdictions)
        - Potentially different profit characteristics
        - Still maintains exact lot tracking
        
        Args:
            sell_quantity: Number of shares being sold
        """
        remaining = sell_quantity
        
        # Select unwinding direction based on lot_selection
        if self.lot_selection == "LIFO":
            # LIFO: Process from end of stack (newest first)
            while remaining > 0 and self.buyback_stack:
                buy_price, buy_qty = self.buyback_stack[-1]
                to_unwind = min(remaining, buy_qty)
                
                if to_unwind == buy_qty:
                    # Fully consumed this lot
                    self.buyback_stack.pop()
                else:
                    # Partially consumed - update remaining quantity
                    self.buyback_stack[-1] = (buy_price, buy_qty - to_unwind)
                
                remaining -= to_unwind
        else:
            # FIFO: Process from beginning of stack (oldest first)
            while remaining > 0 and self.buyback_stack:
                buy_price, buy_qty = self.buyback_stack[0]
                to_unwind = min(remaining, buy_qty)
                
                if to_unwind == buy_qty:
                    # Fully consumed this lot
                    self.buyback_stack.pop(0)
                else:
                    # Partially consumed - update remaining quantity
                    self.buyback_stack[0] = (buy_price, buy_qty - to_unwind)
                
                remaining -= to_unwind

    def place_orders(self, holdings: int, current_price: float) -> None:
        """Calculate and place symmetric buy/sell orders with the market.

        This is the core strategy logic: place limit orders at geometrically
        symmetric prices around the current anchor point. The Market abstraction
        handles execution mechanics.
        
        Order Placement Strategy:
            Buy:  P / (1 + r) with quantity r × H × s
            Sell: P × (1 + r) with quantity r × H × s / (1 + r)
        
        Where:
            P = current_price (anchor after each fill)
            r = rebalance_size (bracket spacing)
            H = holdings (current position)
            s = profit_sharing (trade size fraction)
        
        Mode Differences:
            Full mode: Places both buy and sell orders (volatility harvesting)
            ATH-only: Places only sell orders (baseline for comparison)
        
        Args:
            holdings: Current share count
            current_price: Price anchor for order calculation
        """
        # Clear stale orders - all previous orders are invalidated after a fill
        self.market.clear_orders()
        
        # Update anchor point for symmetric bracket placement
        self.last_transaction_price = current_price

        # Calculate symmetric buy/sell order parameters
        orders = calculate_synthetic_dividend_orders(
            holdings=holdings,
            last_transaction_price=current_price,
            rebalance_size=self.rebalance_size,
            profit_sharing=self.profit_sharing,
        )

        if self.buyback_enabled:
            # Full mode: place both buy and sell orders for volatility harvesting
            if orders["next_buy_qty"] > 0:
                buy_order = Order(
                    action=OrderAction.BUY,
                    quantity=int(orders["next_buy_qty"]),
                    order_type=OrderType.LIMIT,
                    limit_price=orders["next_buy_price"],
                    notes="Buying back"
                )
                self.market.place_order(buy_order)
            
            if orders["next_sell_qty"] > 0:
                sell_order = Order(
                    action=OrderAction.SELL,
                    quantity=int(orders["next_sell_qty"]),
                    order_type=OrderType.LIMIT,
                    limit_price=orders["next_sell_price"],
                    notes="Taking profits"
                )
                self.market.place_order(sell_order)
        else:
            # ATH-only mode: only sell at new highs (no buybacks)
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
        """Initialize algorithm state after initial purchase.
        
        Called once at backtest start to set up initial conditions and place
        the first set of orders.
        
        Args:
            holdings: Initial share quantity
            current_price: Initial purchase price
        """
        # ATH-only mode: seed with initial price as baseline
        if not self.buyback_enabled:
            self.ath_price = current_price

        # Place initial symmetric orders
        self.place_orders(holdings, current_price)

    def on_day(
        self, date_: date, price_row: pd.Series, holdings: int, bank: float, history: pd.DataFrame
    ) -> List[Transaction]:
        """Evaluate day's price action and execute triggered orders.

        Core execution loop that:
        1. Checks for order triggers against OHLC data
        2. Executes fills and updates internal state
        3. Places new orders based on updated position
        4. Iterates to handle multi-bracket gaps
        
        Multi-bracket Gap Handling:
            When price gaps 2+ brackets, we iterate to create separate stack
            entries for exact FIFO symmetry. Each iteration represents one
            bracket crossing, ensuring accurate lot tracking.
        
        Example (gap down 2 brackets):
            Iteration 1: Buy at $91.62 → add stack entry → place new orders
            Iteration 2: Buy at $83.94 → add stack entry → place new orders
            Result: Two separate lots for symmetric unwinding
        
        Args:
            date_: Current date
            price_row: OHLC price data for the day
            holdings: Current share count
            bank: Available cash (unused in this algorithm)
            history: Historical price data (unused in this algorithm)
            
        Returns:
            List of executed transactions for this day
        """
        from src.models.backtest_utils import _get_price_scalar_from_row
        
        transactions: List[Transaction] = []
        
        # ATH-only mode: track all-time high for baseline comparison
        if not self.buyback_enabled:
            high = _get_price_scalar_from_row(price_row, "High")
            if high is not None and high > self.ath_price:
                self.ath_price = high
        
        # Iterate to handle multi-bracket gaps (each iteration = one bracket crossing)
        for iteration in range(1, self.MAX_ITERATIONS_PER_DAY + 1):
            # Let market evaluate orders against this day's price action
            executed = self.market.evaluate_day(date_, price_row, max_iterations=1)
            
            if not executed:
                # No orders triggered - we're done for today
                break
            
            # Process each executed transaction
            for txn in executed:
                fill_price = self._extract_fill_price(txn)
                
                if txn.action == "BUY":
                    if self.buyback_enabled:
                        # Add to FIFO stack for exact lot tracking
                        self.buyback_stack.append((fill_price, txn.qty))
                        
                        # Accumulate volatility alpha (profit from mean reversion)
                        alpha = self._calculate_volatility_alpha(holdings, fill_price, txn.qty)
                        self.total_volatility_alpha += alpha
                    
                    # Update position
                    holdings += txn.qty
                    
                elif txn.action == "SELL":
                    if self.buyback_enabled:
                        # Unwind FIFO stack to maintain symmetry
                        self._unwind_buyback_stack(txn.qty)
                    
                    # Update position
                    holdings -= txn.qty
                
                # Place fresh orders based on new position and fill price
                self.place_orders(holdings, fill_price)
            
            # Accumulate all transactions for this day
            transactions.extend(executed)
        
        return transactions

    def on_end_holding(self) -> None:
        """Print summary statistics after backtest completes.
        
        Outputs performance metrics and final state for analysis.
        """
        if self.buyback_enabled:
            print(
                f"Synthetic Dividend Algorithm total volatility alpha: {self.total_volatility_alpha:.2f}%"
            )
            # Report buyback stack status (unwound lots indicate complete cycles)
            if self.buyback_stack:
                total_stack_qty = sum(qty for _, qty in self.buyback_stack)
                print(
                    f"  Buyback stack: {len(self.buyback_stack)} lots with {total_stack_qty} total shares not yet unwound"
                )
            else:
                print("  Buyback stack: empty (all lots unwound)")
        else:
            print(f"ATH-only algorithm: final ATH = ${self.ath_price:.2f}")
