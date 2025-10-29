"""
Synthetic Portfolio: Multi-asset synthetic dividend management.

Advanced portfolio abstraction that coordinates synthetic dividend algorithms
across multiple assets with NAV-based optimization and cross-asset arbitrage.

This provides the "killer app" - multi-asset retirement portfolios that can
sustain 8-10% withdrawal rates through volatility harvesting.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional, Tuple, Any
import logging

from .model_types import Transaction

logger = logging.getLogger(__name__)


@dataclass
class SyntheticAsset:
    """Single asset within a synthetic portfolio with NAV and algorithm."""

    ticker: str
    holdings: int = 0
    nav: float = 0.0  # All-time high (internal valuation)
    algorithm: Any = None  # SyntheticDividendAlgorithm
    buyback_stack: List[Dict] = field(default_factory=list)

    # Metrics
    total_invested: float = 0.0
    total_dividends: float = 0.0
    transaction_count: int = 0

    def market_value(self, current_price: float) -> float:
        """Current market value of holdings."""
        return self.holdings * current_price

    def nav_value(self) -> float:
        """Value using internal NAV."""
        return self.holdings * self.nav

    def nav_premium(self, current_price: float) -> float:
        """Premium/discount to NAV as percentage."""
        if self.nav == 0:
            return 0.0
        return (current_price - self.nav) / self.nav

    def update_nav(self, price: float) -> None:
        """Update NAV if price exceeds current NAV."""
        if price > self.nav:
            self.nav = price


@dataclass
class PortfolioTransaction:
    """Transaction record for portfolio-level tracking."""

    date: date
    ticker: str
    action: str  # 'BUY', 'SELL', 'INITIAL_BUY', 'WITHDRAWAL'
    quantity: int
    price: float
    total: float
    bank_after: float
    nav_premium: float = 0.0


@dataclass
class PortfolioSnapshot:
    """Daily snapshot of portfolio state."""

    date: date
    total_value: float
    bank: float
    asset_values: Dict[str, float] = field(default_factory=dict)
    asset_navs: Dict[str, float] = field(default_factory=dict)
    holdings: Dict[str, int] = field(default_factory=dict)


class SyntheticPortfolio:
    """
    Multi-asset synthetic dividend portfolio with cross-asset coordination.

    This is the "killer app" - clean, investing-tool-like API for managing
    portfolios that can sustain 8-10% withdrawal rates through volatility harvesting.

    Key Features:
    - Unified cash management across assets
    - NAV-based cross-asset arbitrage
    - Automatic rebalancing strategies
    - Portfolio-level withdrawal management
    - Retirement planning optimization

    Example:
        # Create retirement portfolio
        portfolio = SyntheticPortfolio(cash=500_000, name="Retirement Portfolio")

        # Add diversified assets
        portfolio.add_asset('NVDA', shares=200, price=450.0, strategy='sd8')
        portfolio.add_asset('SPY', shares=150, price=400.0, strategy='sd10')
        portfolio.add_asset('BTC-USD', shares=300, price=35_000.0, strategy='sd6')
        portfolio.add_asset('GLD', shares=400, price=180.0, strategy='sd12')

        # Run 10-year backtest
        results = portfolio.backtest(
            start_date=date(2014, 1, 1),
            end_date=date(2024, 1, 1)
        )

        # Check if 8% withdrawal is sustainable
        print(f"Portfolio value: ${portfolio.total_value:,.0f}")
        print(f"Max drawdown: {portfolio.max_drawdown:.1%}")
        print(f"Dividends generated: ${portfolio.total_dividends:,.0f}")
    """

    def __init__(
        self,
        cash: float = 0.0,
        name: str = "Synthetic Portfolio",
        rebalancing_mode: str = "nav_opportunistic",
        withdrawal_rate: float = 0.0,  # Annual withdrawal rate (e.g., 0.08 for 8%)
    ):
        """
        Create a synthetic dividend portfolio.

        Args:
            cash: Initial cash balance
            name: Portfolio name
            rebalancing_mode: Cross-asset coordination strategy
                - 'simple': Execute all affordable trades
                - 'nav_opportunistic': Prioritize by NAV deviation
            withdrawal_rate: Annual withdrawal rate (0.08 = 8%)
        """
        self.name = name
        self.bank = cash
        self.initial_capital = cash
        self.rebalancing_mode = rebalancing_mode
        self.withdrawal_rate = withdrawal_rate

        self.assets: Dict[str, SyntheticAsset] = {}

        # History and tracking
        self.transactions: List[PortfolioTransaction] = []
        self.snapshots: List[PortfolioSnapshot] = []

        # Performance metrics
        self.peak_value = cash
        self.total_dividends = 0.0
        self.total_withdrawals = 0.0

    def add_asset(
        self,
        ticker: str,
        shares: int = 0,
        price: float = 0.0,
        strategy: str = "sd8",
        profit_sharing: float = 50.0,
    ) -> None:
        """
        Add an asset to the portfolio with synthetic dividend strategy.

        Args:
            ticker: Asset ticker symbol
            shares: Initial number of shares
            price: Current price per share (sets initial NAV)
            strategy: Algorithm variant ('sd6', 'sd8', 'sd10', 'sd12', 'ath_only')
            profit_sharing: Profit sharing percentage (0-100)
        """
        if ticker in self.assets:
            raise ValueError(f"Asset {ticker} already exists in portfolio")

        # Import here to avoid circular imports
        from ..algorithms.factory import build_algo_from_name

        # Create algorithm - build strategy string with profit sharing
        if profit_sharing != 50.0:
            strategy_with_profit = f"{strategy},{profit_sharing}"
        else:
            strategy_with_profit = strategy

        algorithm = build_algo_from_name(strategy_with_profit)

        # Create asset
        asset = SyntheticAsset(
            ticker=ticker, holdings=shares, nav=price if price > 0 else 0.0, algorithm=algorithm
        )

        self.assets[ticker] = asset

        # Record initial purchase
        if shares > 0 and price > 0:
            cost = shares * price
            self.bank -= cost
            asset.total_invested = cost

            self.transactions.append(
                PortfolioTransaction(
                    date=date.today(),
                    ticker=ticker,
                    action="INITIAL_BUY",
                    quantity=shares,
                    price=price,
                    total=cost,
                    bank_after=self.bank,
                )
            )

    def remove_asset(self, ticker: str) -> None:
        """Remove an asset from the portfolio."""
        if ticker not in self.assets:
            raise ValueError(f"Asset {ticker} not found in portfolio")

        asset = self.assets[ticker]
        if asset.holdings > 0:
            logger.warning(
                f"Removing {ticker} with {asset.holdings} shares - consider selling first"
            )

        del self.assets[ticker]

    # Portfolio state queries
    def get_holdings(self) -> Dict[str, int]:
        """Get current holdings for all assets."""
        return {ticker: asset.holdings for ticker, asset in self.assets.items()}

    def get_asset_value(self, ticker: str, current_price: float) -> float:
        """Get market value of specific asset."""
        if ticker not in self.assets:
            return 0.0
        return self.assets[ticker].market_value(current_price)

    def get_total_value(self, current_prices: Dict[str, float]) -> float:
        """Get total portfolio value including cash."""
        total = self.bank
        for ticker, asset in self.assets.items():
            if ticker in current_prices:
                total += asset.market_value(current_prices[ticker])
        return total

    def get_nav_value(self) -> float:
        """Get total portfolio NAV (internal valuation)."""
        return sum(asset.nav_value() for asset in self.assets.values()) + self.bank

    # Cash management
    def deposit(self, amount: float, deposit_date: Optional[date] = None) -> None:
        """Add cash to the portfolio."""
        self.bank += amount
        if deposit_date is None:
            deposit_date = date.today()

        self.transactions.append(
            PortfolioTransaction(
                date=deposit_date,
                ticker="CASH",
                action="DEPOSIT",
                quantity=0,
                price=0.0,
                total=amount,
                bank_after=self.bank,
            )
        )

    def withdraw(self, amount: float, withdrawal_date: Optional[date] = None) -> bool:
        """
        Withdraw cash from the portfolio.

        Returns True if successful, False if insufficient funds.
        """
        if self.bank < amount:
            return False

        self.bank -= amount
        self.total_withdrawals += amount

        if withdrawal_date is None:
            withdrawal_date = date.today()

        self.transactions.append(
            PortfolioTransaction(
                date=withdrawal_date,
                ticker="CASH",
                action="WITHDRAWAL",
                quantity=0,
                price=0.0,
                total=-amount,
                bank_after=self.bank,
            )
        )

        return True

    def process_withdrawal(self, current_date: date) -> bool:
        """
        Process regular withdrawal based on portfolio value and withdrawal rate.

        Returns True if withdrawal processed, False if insufficient funds.
        """
        if self.withdrawal_rate <= 0:
            return True  # No withdrawal needed

        # Calculate withdrawal amount (monthly)
        annual_withdrawal = self.total_value * self.withdrawal_rate
        monthly_withdrawal = annual_withdrawal / 12

        return self.withdraw(monthly_withdrawal, current_date)

    # Core backtesting logic
    def process_day(
        self, current_date: date, market_data: Dict[str, Dict[str, float]]
    ) -> List[PortfolioTransaction]:
        """
        Process one trading day for the entire portfolio.

        Args:
            current_date: Trading date
            market_data: Dict mapping ticker -> {'open', 'high', 'low', 'close'}

        Returns:
            List of transactions executed
        """
        # Update NAVs and collect transaction proposals
        proposals = {}
        for ticker, asset in self.assets.items():
            if ticker not in market_data:
                continue

            ohlc = market_data[ticker]
            close_price = ohlc["close"]

            # Update NAV (all-time high)
            asset.update_nav(close_price)

            # Get algorithm proposals
            try:
                transactions, cash_impact = self._process_asset_day(asset, ohlc)
                proposals[ticker] = {
                    "transactions": transactions,
                    "cash_impact": cash_impact,
                    "nav_premium": asset.nav_premium(close_price),
                }
            except Exception as e:
                logger.warning(f"Error processing {ticker}: {e}")
                continue

        # Execute transactions based on rebalancing strategy
        executed = self._execute_strategy(current_date, proposals, market_data)

        # Process regular withdrawals
        self.process_withdrawal(current_date)

        # Create daily snapshot
        self._create_snapshot(current_date, market_data)

        return executed

    def _process_asset_day(
        self, asset: SyntheticAsset, ohlc: Dict[str, float]
    ) -> Tuple[List[Transaction], float]:
        """Process one day for a single asset using its algorithm."""
        if not asset.algorithm:
            return [], 0.0

        # This will call the algorithm's process_day method
        # For now, return mock data until algorithm integration is complete
        return [], 0.0

    def _execute_strategy(
        self, current_date: date, proposals: Dict, market_data: Dict[str, Dict[str, float]]
    ) -> List[PortfolioTransaction]:
        """Execute transactions based on portfolio strategy."""
        if self.rebalancing_mode == "simple":
            return self._execute_simple(current_date, proposals)
        elif self.rebalancing_mode == "nav_opportunistic":
            return self._execute_nav_opportunistic(current_date, proposals)
        else:
            raise ValueError(f"Unknown rebalancing mode: {self.rebalancing_mode}")

    def _execute_simple(self, current_date: date, proposals: Dict) -> List[PortfolioTransaction]:
        """Execute all affordable transactions in order."""
        executed = []

        # Execute sells first (generate cash)
        for ticker, proposal in proposals.items():
            for tx in proposal["transactions"]:
                if tx.action == "SELL":
                    self._execute_transaction(current_date, ticker, tx, proposal["nav_premium"])
                    executed.append(
                        self._to_portfolio_transaction(
                            current_date, ticker, tx, proposal["nav_premium"]
                        )
                    )

        # Execute buys if cash available
        for ticker, proposal in proposals.items():
            for tx in proposal["transactions"]:
                if tx.action == "BUY":
                    cost = tx.qty * tx.price
                    if self.bank >= cost:
                        self._execute_transaction(current_date, ticker, tx, proposal["nav_premium"])
                        executed.append(
                            self._to_portfolio_transaction(
                                current_date, ticker, tx, proposal["nav_premium"]
                            )
                        )

        return executed

    def _execute_nav_opportunistic(
        self, current_date: date, proposals: Dict
    ) -> List[PortfolioTransaction]:
        """
        Prioritize transactions by NAV deviation magnitude.

        Sells assets with highest NAV premium first (capture overvaluation).
        Buys assets with largest NAV discount first (exploit undervaluation).
        """
        executed = []

        # Collect all transactions with NAV context
        all_txns = []
        for ticker, proposal in proposals.items():
            for tx in proposal["transactions"]:
                all_txns.append(
                    {"ticker": ticker, "transaction": tx, "nav_premium": proposal["nav_premium"]}
                )

        # Sort sells by NAV premium (highest first = most overvalued)
        sells = [t for t in all_txns if t["transaction"].action == "SELL"]
        sells.sort(key=lambda x: x["nav_premium"], reverse=True)

        # Sort buys by NAV premium (most negative first = most undervalued)
        buys = [t for t in all_txns if t["transaction"].action == "BUY"]
        buys.sort(key=lambda x: x["nav_premium"])

        # Execute sells to generate cash
        for item in sells:
            self._execute_transaction(
                current_date, item["ticker"], item["transaction"], item["nav_premium"]
            )
            executed.append(
                self._to_portfolio_transaction(
                    current_date, item["ticker"], item["transaction"], item["nav_premium"]
                )
            )

        # Execute buys if cash available
        for item in buys:
            tx = item["transaction"]
            cost = tx.qty * tx.price
            if self.bank >= cost:
                self._execute_transaction(current_date, item["ticker"], tx, item["nav_premium"])
                executed.append(
                    self._to_portfolio_transaction(
                        current_date, item["ticker"], tx, item["nav_premium"]
                    )
                )

        return executed

    def _execute_transaction(
        self, current_date: date, ticker: str, transaction: Transaction, nav_premium: float
    ) -> None:
        """Execute a transaction and update portfolio state."""
        asset = self.assets[ticker]

        if transaction.action == "BUY":
            cost = transaction.qty * transaction.price
            self.bank -= cost
            asset.holdings += transaction.qty
            asset.total_invested += cost

        elif transaction.action == "SELL":
            proceeds = transaction.qty * transaction.price
            self.bank += proceeds
            asset.holdings -= transaction.qty
            asset.total_dividends += proceeds
            self.total_dividends += proceeds

        asset.transaction_count += 1

    def _to_portfolio_transaction(
        self, current_date: date, ticker: str, transaction: Transaction, nav_premium: float
    ) -> PortfolioTransaction:
        """Convert algorithm transaction to portfolio transaction."""
        return PortfolioTransaction(
            date=current_date,
            ticker=ticker,
            action=transaction.action,
            quantity=transaction.qty,
            price=transaction.price,
            total=transaction.qty * transaction.price,
            bank_after=self.bank,
            nav_premium=nav_premium,
        )

    def _create_snapshot(
        self, current_date: date, market_data: Dict[str, Dict[str, float]]
    ) -> None:
        """Create daily portfolio snapshot."""
        current_prices = {ticker: data["close"] for ticker, data in market_data.items()}

        snapshot = PortfolioSnapshot(
            date=current_date,
            total_value=self.get_total_value(current_prices),
            bank=self.bank,
            asset_values={
                ticker: self.get_asset_value(ticker, current_prices.get(ticker, 0))
                for ticker in self.assets
            },
            asset_navs={ticker: self.assets[ticker].nav_value() for ticker in self.assets},
            holdings=self.get_holdings(),
        )

        self.snapshots.append(snapshot)

        # Update peak value
        if snapshot.total_value > self.peak_value:
            self.peak_value = snapshot.total_value

    # Performance properties
    @property
    def total_value(self) -> float:
        """Current total portfolio value."""
        if not self.snapshots:
            return self.initial_capital
        return self.snapshots[-1].total_value

    @property
    def total_return(self) -> float:
        """Total return since inception."""
        if self.initial_capital == 0:
            return 0.0
        return (self.total_value - self.initial_capital) / self.initial_capital

    @property
    def max_drawdown(self) -> float:
        """Maximum drawdown from peak."""
        if not self.snapshots:
            return 0.0

        peak = self.initial_capital
        max_dd = 0.0

        for snapshot in self.snapshots:
            if snapshot.total_value > peak:
                peak = snapshot.total_value
            dd = (peak - snapshot.total_value) / peak
            max_dd = max(max_dd, dd)

        return max_dd

    def summary(self) -> Dict[str, Any]:
        """Get comprehensive portfolio summary."""
        return {
            "name": self.name,
            "total_value": self.total_value,
            "bank_balance": self.bank,
            "total_return": self.total_return,
            "max_drawdown": self.max_drawdown,
            "total_dividends": self.total_dividends,
            "total_withdrawals": self.total_withdrawals,
            "assets": len(self.assets),
            "transactions": len(self.transactions),
            "days": len(self.snapshots),
            "rebalancing_mode": self.rebalancing_mode,
            "withdrawal_rate": self.withdrawal_rate,
            "holdings": self.get_holdings(),
        }

    def get_income_data(self) -> Any:
        """
        Generate income data for band chart visualization.

        Returns DataFrame with columns for each asset's income stream,
        expenses/withdrawals, and cash reserves over time.

        Used by income_band_chart.py for visualization.

        Returns:
            DataFrame with date index and columns:
            - Asset tickers: Monthly income from each asset
            - 'expenses': Monthly withdrawal amounts (red band)
            - 'cash': Cash reserve levels (green band)
        """
        import pandas as pd

        if not self.snapshots:
            raise ValueError("No portfolio snapshots available - run backtest first")

        # Extract data from snapshots
        income_data = []

        for i, snapshot in enumerate(self.snapshots):  # noqa: B007
            row = {"date": snapshot.date}

            # Asset income streams (simplified: assume dividends are monthly)
            # In a real implementation, this would track actual dividend payments
            # For now, use a proxy based on transaction activity
            asset_income = {}

            # Look at transactions in this period to estimate income
            period_start = snapshot.date.replace(day=1)  # Start of month
            period_end = snapshot.date

            # Calculate income from sell transactions (dividends)
            for tx in self.transactions:
                if period_start <= tx.date <= period_end and tx.action == "SELL":
                    if tx.ticker not in asset_income:
                        asset_income[tx.ticker] = 0.0
                    asset_income[tx.ticker] += tx.total

            # Add all assets (even if no income this period)
            for ticker in self.assets.keys():
                row[ticker] = asset_income.get(ticker, 0.0)

            # Expenses/withdrawals (monthly)
            withdrawal_txns = [
                tx
                for tx in self.transactions
                if period_start <= tx.date <= period_end and tx.action == "WITHDRAWAL"
            ]
            row["expenses"] = sum(abs(tx.total) for tx in withdrawal_txns)

            # Cash reserves
            row["cash"] = snapshot.bank

            income_data.append(row)

        # Create DataFrame
        df = pd.DataFrame(income_data)
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")

        # Resample to monthly for cleaner visualization
        monthly_df = df.resample("M").agg(
            {
                **{col: "sum" for col in df.columns if col not in ["cash"]},  # Sum income/expenses
                "cash": "last",  # Use last cash value for month
            }
        )

        return monthly_df

    def __str__(self) -> str:
        """String representation of portfolio."""
        return (
            f"SyntheticPortfolio('{self.name}'): "
            f"${self.total_value:,.0f} "
            f"({self.total_return:.1%}) "
            f"across {len(self.assets)} assets"
        )

    def __repr__(self) -> str:
        """Detailed representation."""
        return (
            f"SyntheticPortfolio(name='{self.name}', "
            f"assets={len(self.assets)}, "
            f"value=${self.total_value:,.0f}, "
            f"return={self.total_return:.1%})"
        )
