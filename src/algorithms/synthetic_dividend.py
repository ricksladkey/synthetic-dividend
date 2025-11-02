"""Synthetic dividend algorithm: volatility harvesting strategy."""

from datetime import date
from typing import Any, Dict, List, Optional

import pandas as pd

from src.algorithms.base import AlgorithmBase
from src.models.backtest_utils import calculate_synthetic_dividend_orders
from src.models.market import Market, Order, OrderAction, OrderType
from src.models.model_types import Transaction


class SyntheticDividendAlgorithm(AlgorithmBase):
    """Volatility harvesting algorithm that generates synthetic dividends.

    This algorithm exploits mean reversion by systematically buying on dips and
    selling on rises within a symmetrically-spaced bracket system. It operates as
    a volatility-harvesting strategy that generates cash flow ("synthetic dividends")
    from price oscillations.

    WHAT THIS IS NOT:
    =================
    NO derivatives required - just spot asset + limit orders:
        ❌ No options (covered calls, puts, spreads)
        ❌ No futures, swaps, or VIX products
        ❌ No leverage or margin
        ✅ Direct ownership only - buy low, sell high systematically

    Key differentiator: We extract volatility returns without options decay,
    counterparty risk, or complex derivatives pricing. Just rebalancing.

    CRITICAL PREREQUISITE:
    ======================
    ⚠️  ASSUMPTION: Asset will eventually recover from drawdowns and make new ATHs.

    The algorithm buys systematically during declines. This is profitable ONLY if
    the asset recovers. If the investment thesis breaks (permanent decline), those
    buyback purchases amplify losses.

    Example of BROKEN thesis: Moderna (MRNA) - down 92% from peak, COVID demand gone
    Example of VALID thesis: NVIDIA (NVDA) - multiple 40-50% drawdowns, always recovered

    Before using this algorithm, confirm:
        1. Asset has secular growth potential (not speculative)
        2. Will likely make new ATHs within 2-5 years
        3. You'd hold through a 50% drawdown (high conviction)

    Only apply to assets where you're confident about eventual ATH recovery.
    This algorithm amplifies conviction - use only on high-quality holdings.

    PSEUDO-CODE OVERVIEW:
    =====================

    Core Principle: "Treat volatility as a harvestable asset class"

    Given:
        - A volatile growth asset (NVDA, BTC, ETH, etc.)
        - Rebalance trigger 'r' (e.g., 9.15% = one bracket)
        - Profit sharing 's' (e.g., 50% = half position size)

    On Initial Purchase:
        anchor_price ← initial_price
        all_time_high ← initial_price
        buyback_stack ← empty

        Place symmetric limit orders:
            buy_price  ← anchor / (1 + r)      # One bracket below
            sell_price ← anchor × (1 + r)      # One bracket above
            buy_qty    ← holdings × r × s
            sell_qty   ← holdings × r × s / (1 + r)  # Geometric symmetry

    Each Trading Day:
        # Update all-time high
        if today.high > all_time_high:
            all_time_high ← today.high

        # Check if price crossed any brackets (could cross multiple in one day)
        while orders triggered by today's OHLC range:

            if BUY order triggered:
                # Price dropped - buy the dip
                shares_bought ← execute_buy_at(buy_price)
                holdings ← holdings + shares_bought
                buyback_stack.push(shares_bought)

                # Measure volatility alpha (profit from mean reversion)
                profit ← (last_sell_price - buy_price) × shares_bought
                volatility_alpha ← profit / portfolio_value

                # Reset anchor to new transaction price
                anchor_price ← buy_price

            if SELL order triggered:
                # Price rose - take profits
                shares_sold ← execute_sell_at(sell_price)
                holdings ← holdings - shares_sold

                if buyback_enabled:
                    # Track unwinding of buyback stack (diagnostic)
                    buyback_stack.pop(min(shares_sold, stack_size))

                # Reset anchor to new transaction price
                anchor_price ← sell_price

            # Place fresh orders from new anchor point
            cancel_all_old_orders()
            calculate_and_place_new_symmetric_orders(anchor_price)

            # Anti-chatter: new orders can't execute same day
            new_orders.earliest_execution ← tomorrow

    Result: Volatility Alpha
        Each buy-low/sell-high cycle extracts value from price oscillations.
        Formula (theoretical minimum): α ≈ (trigger%)² / 2 × cycle_count
        Reality: Actual alpha is 1.1x to 10.6x this formula due to gaps!

    KEY INSIGHTS FROM THEORY:
    =========================

    1. Dividend Illusion:
       "There's no free money - every withdrawal has opportunity cost"
       → We acknowledge this and measure opportunity cost vs buy-and-hold

    2. Time Machine Effect:
       "Profit sharing creates non-linear time dilation"
       → 50% profit sharing = 2x time to reach goals
       → Trade current income for future growth, or vice versa

    3. Volatility as Asset Class:
       "Traditional finance: volatility = risk to minimize"
       "Our view: volatility = harvestable value"
       → Four sources: price path, drawdown recycling, compounding, gap arbitrage
       → Empirical validation: +1% to +198% alpha over 3 years

    4. Geometric Symmetry:
       "Why divide sell qty by (1 + r)?"
       → Ensures exact price unwinding: buy at P/(1+r), sell at P×(1+r)
       → Stack (LIFO) requires equal dollar amounts, not equal shares
       → Example: Buy 10 shares @ $91, sell 9.2 shares @ $100 → same $910

    5. Multi-Bracket Gaps:
       "Price can jump multiple brackets in one day"
       → Each bracket crossing = separate stack entry
       → Iterate until no more triggers (max 20 iterations/day)
       → Preserves exact symmetry for profit calculation

    OPERATING MODES:
    ================

    Full Mode (buyback_enabled=True):
        - Places both BUY and SELL orders
        - Maintains buyback stack for tracking
        - Generates volatility alpha from mean reversion
        - Use for: actual income generation

    ATH-Only Mode (buyback_enabled=False):
        - Places only SELL orders at new all-time highs
        - No buyback stack needed
        - Baseline for measuring volatility alpha
        - Use for: performance comparison

    ATH-Sell Mode (sell_at_new_ath=True):
        - Places BUY orders on dips (builds stack)
        - Only SELLS when price exceeds previous ATH
        - Maximizes compounding during recoveries
        - Use for: accumulation phase with minimal selling

    MATHEMATICAL FOUNDATION:
    ========================

    Bracket Spacing (Geometric):
        buy_price  = anchor / (1 + r)
        sell_price = anchor × (1 + r)

    Trade Sizing (Profit Sharing):
        buy_qty  = holdings × r × s
        sell_qty = holdings × r × s / (1 + r)

    Where:
        r = rebalance_size (bracket spacing, e.g., 0.0915 for SD8)
        s = profit_sharing (extraction ratio, e.g., 0.5 for 50%)

    Volatility Alpha Calculation:
        profit = (sell_price - buy_price) × shares_in_cycle
        alpha  = profit / portfolio_value × 100

    Theoretical Minimum (from VOLATILITY_ALPHA_THESIS.md):
        alpha_per_cycle ≈ (r)² / 2
        total_alpha     ≈ cycle_count × (r)² / 2

    Reality Check (from empirical validation):
        GLD (16% vol):  1.1x formula  → predictable
        BTC (40% vol):  1.9x formula  → moderate gaps
        MSTR (90% vol): 2.1x formula  → extreme frequency
        NVDA (52% vol): 5.7x formula  → explosive growth gaps! 🚀
        PLTR (68% vol): 10.6x formula → explosive growth gaps! 🚀

    PARAMETERS:
    ===========
        rebalance_size: Bracket spacing as decimal (e.g., 0.0915 = 9.15% brackets)
        profit_sharing: Trade size as fraction of rebalance (e.g., 0.5 = 50%)
        buyback_enabled: True for full algorithm, False for ATH-only baseline
        sell_at_new_ath: True for ATH-sell variant (only sell at new ATHs)

    EXAMPLES:
    =========

    # Full volatility harvesting (standard)
    algo = SyntheticDividendAlgorithm(
        rebalance_size=0.0915,  # SD8: 9.15% brackets
        profit_sharing=0.5,      # 50% extraction
        buyback_enabled=True
    )

    # ATH-only baseline (for comparison)
    baseline = SyntheticDividendAlgorithm(
        rebalance_size=0.0915,
        profit_sharing=0.5,
        buyback_enabled=False    # Only sells at ATHs
    )

    # ATH-sell variant (accumulation mode)
    accumulator = SyntheticDividendAlgorithm(
        rebalance_size=0.0915,
        profit_sharing=0.5,
        sell_at_new_ath=True     # Only sells at new ATHs
    )

    PERFORMANCE EXPECTATIONS (from experiments/volatility-alpha-validation/):
    ==========================================================================

    Asset     | Vol  | Algo | Period | Expected Alpha (3yr)
    ----------|------|------|--------|--------------------
    GLD       | 16%  | SD16 | Stable | ~1%   (minimal)
    VOO       | 20%  | SD16 | Stable | ~3%   (low)
    BTC-USD   | 40%  | SD8  | Crypto | ~27%  (moderate)
    ETH-USD   | 54%  | SD6  | Crypto | ~46%  (strong)
    NVDA      | 52%  | SD6  | Growth | ~77%  (explosive!) 🚀
    PLTR      | 68%  | SD6  | Growth | ~198% (extraordinary!) 🚀🚀

    Rule of Thumb:
        - Higher volatility → more cycles → more alpha
        - Explosive growth → large gaps → MASSIVE alpha boost
        - Formula gives conservative minimum, reality often exceeds it

    SEE ALSO:
    =========
    - theory/01-core-concepts.md - Economic foundations
    - theory/02-algorithm-variants.md - Mode comparisons
    - theory/VOLATILITY_ALPHA_THESIS.md - Complete mathematical treatment
    - experiments/volatility-alpha-validation/ - Empirical validation data
    """

    # Maximum iterations for multi-bracket gap handling per day
    # In extreme volatility (e.g., 20% gap = ~2 brackets), we need multiple iterations
    # to create separate stack entries for exact symmetry. Limit prevents infinite loops.
    MAX_ITERATIONS_PER_DAY = 20

    def __init__(
        self,
        rebalance_size: float = 0.0,
        profit_sharing: float = 0.0,
        buyback_enabled: bool = True,
        bracket_seed: Optional[float] = None,
        sell_at_new_ath: bool = False,
        params: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize algorithm with strategy parameters.

        Args:
            rebalance_size: Bracket spacing as decimal (e.g., 0.0915 for 9.15%)
            profit_sharing: Trade size as fraction (e.g., 0.5 for 50%)
            buyback_enabled: True for full mode, False for ATH-only
            bracket_seed: Optional seed price to align bracket positions (e.g., 100.0)
            params: Optional dict for base class compatibility (can include 'bracket_seed')
            sell_at_new_ath: True for ATH-sell variant (sell only at new ATHs)
            params: Optional dict for base class compatibility
        """
        super().__init__(params)

        # Strategy parameters (stored as mathematical decimals, not percentages)
        self.rebalance_size: float = float(rebalance_size)
        self.profit_sharing: float = float(profit_sharing)
        self.buyback_enabled: bool = buyback_enabled
        # Allow bracket_seed from params dict if not explicitly provided
        self.bracket_seed: Optional[float] = bracket_seed
        if self.bracket_seed is None and params:
            seed_value = params.get("bracket_seed")
            # Validate that seed is numeric if provided via params
            if seed_value is not None:
                try:
                    self.bracket_seed = float(seed_value)
                except (TypeError, ValueError):
                    # Invalid seed value, ignore it
                    pass
        self.sell_at_new_ath: bool = sell_at_new_ath

        # Performance tracking: cumulative alpha from volatility harvesting
        self.total_volatility_alpha: float = 0.0

        # ATH tracking for sell conditions
        self.all_time_high: float = 0.0

        # Buyback stack: simple count of shares purchased for volatility harvesting
        # We don't track individual lots since tax consequences (LTCG) don't matter here
        # Just need to know how many shares are in the stack for symmetry tracking
        self.buyback_stack_count: int = 0

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

    def place_orders(
        self, holdings: int, current_price: float, placed_date: Optional[date] = None
    ) -> None:
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
            placed_date: Date order is placed (for anti-chatter logic)
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
            bracket_seed=self.bracket_seed,
        )

        if self.buyback_enabled:
            # Full mode: place both buy and sell orders for volatility harvesting
            if orders["next_buy_qty"] > 0:
                buy_order = Order(
                    action=OrderAction.BUY,
                    quantity=int(orders["next_buy_qty"]),
                    order_type=OrderType.LIMIT,
                    limit_price=orders["next_buy_price"],
                    notes="Buying back",
                    placed_date=placed_date,
                )
                self.market.place_order(buy_order)

            if orders["next_sell_qty"] > 0:
                # ATH-sell variant: only sell if price exceeds all-time high
                if self.sell_at_new_ath:
                    # Only place sell order if current price exceeds all-time high
                    if current_price > self.all_time_high:
                        sell_order = Order(
                            action=OrderAction.SELL,
                            quantity=int(orders["next_sell_qty"]),
                            order_type=OrderType.LIMIT,
                            limit_price=orders["next_sell_price"],
                            notes=f"ATH-sell at new ATH ${self.all_time_high:.2f}",
                            placed_date=placed_date,
                        )
                        self.market.place_order(sell_order)
                else:
                    # Standard sell logic
                    sell_order = Order(
                        action=OrderAction.SELL,
                        quantity=int(orders["next_sell_qty"]),
                        order_type=OrderType.LIMIT,
                        limit_price=orders["next_sell_price"],
                        notes="Taking profits",
                        placed_date=placed_date,
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
                    notes=f"ATH-only sell, ATH=${self.ath_price:.2f}",
                    placed_date=placed_date,
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
        # Initialize ATH tracking
        self.all_time_high = current_price

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
            entries for exact geometric symmetry. Each iteration represents one
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
        transactions: List[Transaction] = []

        # ATH tracking for sell conditions (used by ATH-sell variant)
        high = price_row.get("High")
        if high is not None:
            high_val = high.item() if hasattr(high, "item") else float(high)
            if high_val > self.all_time_high:
                self.all_time_high = high_val

        # ATH-only mode: track all-time high for baseline comparison
        if not self.buyback_enabled:
            high = price_row.get("High")
            if high is not None:
                high_val = high.item() if hasattr(high, "item") else float(high)
                if high_val > self.ath_price:
                    self.ath_price = high_val

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
                        # Add to buyback stack count for symmetry tracking
                        self.buyback_stack_count += txn.qty

                        # Accumulate volatility alpha (profit from mean reversion)
                        alpha = self._calculate_volatility_alpha(holdings, fill_price, txn.qty)
                        self.total_volatility_alpha += alpha

                    # Update position
                    holdings += txn.qty

                elif txn.action == "SELL":
                    if self.buyback_enabled:
                        # Track buyback stack unwinding (diagnostic only)
                        # Can only unwind shares that are actually in the stack
                        shares_to_unwind = min(txn.qty, self.buyback_stack_count)
                        self.buyback_stack_count -= shares_to_unwind

                    # Update position
                    holdings -= txn.qty

                # Place fresh orders based on new position and fill price
                # Pass current date so orders don't execute on same day (anti-chatter)
                self.place_orders(holdings, fill_price, placed_date=date_)

            # Accumulate all transactions for this day
            transactions.extend(executed)

        return transactions

    def on_end_holding(self) -> None:
        """Print summary statistics after backtest completes.

        Outputs performance metrics and final state for analysis.
        """
        if self.buyback_enabled:
            if self.sell_at_new_ath:
                print(
                    f"ATH-Sell Algorithm total volatility alpha: {self.total_volatility_alpha:.2f}%"
                )
                print(f"  Final ATH: ${self.all_time_high:.2f}")
            else:
                print(
                    f"Synthetic Dividend Algorithm total volatility alpha: {self.total_volatility_alpha:.2f}%"
                )
            # Report buyback stack status (unwound shares indicate complete cycles)
            if self.buyback_stack_count > 0:
                print(f"  Buyback stack: {self.buyback_stack_count} shares not yet unwound")
            else:
                print("  Buyback stack: empty (all shares unwound)")
        else:
            print(f"ATH-only algorithm: final ATH = ${self.ath_price:.2f}")
