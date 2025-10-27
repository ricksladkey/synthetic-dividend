"""
Portfolio: A collection of holdings across multiple tickers.

A Portfolio aggregates multiple Holdings to provide portfolio-level analysis.
This is the second foundational building block for multi-asset management.

Design Philosophy:
- Portfolio is just a container of Holdings
- All state derives from underlying transaction history
- Clean separation: Holding = single ticker, Portfolio = multiple tickers
- Beautiful compositional design
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional, Tuple
from src.models.holding import Holding, Transaction


@dataclass
class Portfolio:
    """
    A collection of holdings across multiple tickers.
    
    A Portfolio is simply a dictionary of {ticker: Holding}, plus methods
    for portfolio-level aggregation and analysis.
    
    Design Principles:
    - Holdings are independent (no cross-ticker logic here)
    - Portfolio value = sum of all holdings' values
    - Transaction history preserved per ticker
    - Cash/bank balance managed separately (not part of this abstraction)
    
    Example:
        >>> portfolio = Portfolio()
        >>> portfolio.add_holding("NVDA")
        >>> portfolio.buy("NVDA", shares=100, date=date(2024, 1, 1), price=50.0)
        >>> portfolio.add_holding("VOO")
        >>> portfolio.buy("VOO", shares=50, date=date(2024, 1, 1), price=400.0)
        >>> portfolio.total_value(prices={"NVDA": 75.0, "VOO": 450.0})
        >>> # (100 × 75) + (50 × 450) = 7500 + 22500 = 30000
    """
    
    holdings: Dict[str, Holding] = field(default_factory=dict)
    
    def add_holding(self, ticker: str) -> Holding:
        """
        Add a new ticker to the portfolio.
        
        Args:
            ticker: Stock symbol
            
        Returns:
            The created Holding
            
        Raises:
            ValueError: If ticker already exists
        """
        if ticker in self.holdings:
            raise ValueError(f"Ticker {ticker} already exists in portfolio")
        
        holding = Holding(ticker=ticker)
        self.holdings[ticker] = holding
        return holding
    
    def get_holding(self, ticker: str) -> Optional[Holding]:
        """
        Get holding for a specific ticker.
        
        Args:
            ticker: Stock symbol
            
        Returns:
            Holding if exists, None otherwise
        """
        return self.holdings.get(ticker)
    
    def has_holding(self, ticker: str) -> bool:
        """Check if portfolio contains a specific ticker."""
        return ticker in self.holdings
    
    def buy(
        self,
        ticker: str,
        shares: int,
        purchase_date: date,
        purchase_price: float,
        notes: str = ""
    ) -> Transaction:
        """
        Buy shares of a ticker.
        
        If ticker doesn't exist in portfolio, it will be added automatically.
        
        Args:
            ticker: Stock symbol
            shares: Number of shares
            purchase_date: Date of purchase
            purchase_price: Price per share
            notes: Optional explanation
            
        Returns:
            The created Transaction
        """
        if ticker not in self.holdings:
            self.add_holding(ticker)
        
        return self.holdings[ticker].add_buy(
            shares=shares,
            purchase_date=purchase_date,
            purchase_price=purchase_price,
            notes=notes
        )
    
    def sell(
        self,
        ticker: str,
        shares: int,
        sale_date: date,
        sale_price: float,
        notes: str = "",
        lot_selection: str = "FIFO"
    ) -> List[Transaction]:
        """
        Sell shares of a ticker.
        
        Args:
            ticker: Stock symbol
            shares: Number of shares to sell
            sale_date: Date of sale
            sale_price: Price per share
            notes: Optional explanation
            lot_selection: Lot selection method ('FIFO', 'LIFO', etc.)
            
        Returns:
            List of created SELL transactions
            
        Raises:
            ValueError: If ticker doesn't exist or insufficient shares
        """
        if ticker not in self.holdings:
            raise ValueError(f"Ticker {ticker} not found in portfolio")
        
        return self.holdings[ticker].add_sell(
            shares=shares,
            sale_date=sale_date,
            sale_price=sale_price,
            notes=notes,
            lot_selection=lot_selection
        )
    
    def total_shares(self, ticker: Optional[str] = None) -> int:
        """
        Get total shares held.
        
        Args:
            ticker: If specified, return shares for that ticker only.
                   If None, return total across all tickers.
        
        Returns:
            Number of shares
        """
        if ticker is not None:
            holding = self.holdings.get(ticker)
            return holding.current_shares() if holding else 0
        
        return sum(
            holding.current_shares()
            for holding in self.holdings.values()
        )
    
    def total_value(self, prices: Dict[str, float]) -> float:
        """
        Calculate total portfolio market value.
        
        Args:
            prices: Dictionary mapping ticker → current price
            
        Returns:
            Total market value across all holdings
            
        Raises:
            KeyError: If a ticker in portfolio is missing from prices dict
        """
        total = 0.0
        for ticker, holding in self.holdings.items():
            if ticker not in prices:
                raise KeyError(f"Price not provided for ticker: {ticker}")
            total += holding.market_value(prices[ticker])
        return total
    
    def total_cost_basis(self, ticker: Optional[str] = None) -> float:
        """
        Calculate total cost basis.
        
        Args:
            ticker: If specified, return cost basis for that ticker only.
                   If None, return total across all tickers.
        
        Returns:
            Total cost basis in dollars
        """
        if ticker is not None:
            holding = self.holdings.get(ticker)
            return holding.cost_basis() if holding else 0.0
        
        return sum(
            holding.cost_basis()
            for holding in self.holdings.values()
        )
    
    def total_unrealized_gain_loss(self, prices: Dict[str, float]) -> float:
        """
        Calculate total unrealized P/L across all holdings.
        
        Args:
            prices: Dictionary mapping ticker → current price
            
        Returns:
            Total unrealized P/L
        """
        total = 0.0
        for ticker, holding in self.holdings.items():
            if ticker not in prices:
                raise KeyError(f"Price not provided for ticker: {ticker}")
            total += holding.unrealized_gain_loss(prices[ticker])
        return total
    
    def total_realized_gain_loss(self, ticker: Optional[str] = None) -> float:
        """
        Calculate total realized P/L.
        
        Args:
            ticker: If specified, return realized P/L for that ticker only.
                   If None, return total across all tickers.
        
        Returns:
            Total realized P/L
        """
        if ticker is not None:
            holding = self.holdings.get(ticker)
            return holding.realized_gain_loss() if holding else 0.0
        
        return sum(
            holding.realized_gain_loss()
            for holding in self.holdings.values()
        )
    
    def total_gain_loss(self, prices: Dict[str, float]) -> float:
        """
        Calculate total P/L (realized + unrealized).
        
        Args:
            prices: Dictionary mapping ticker → current price
            
        Returns:
            Total P/L across all holdings
        """
        return self.total_realized_gain_loss() + self.total_unrealized_gain_loss(prices)
    
    def allocations(self, prices: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate current portfolio allocations by ticker.
        
        Args:
            prices: Dictionary mapping ticker → current price
            
        Returns:
            Dictionary mapping ticker → percentage (0.0 to 1.0)
        """
        total = self.total_value(prices)
        if total == 0:
            return {ticker: 0.0 for ticker in self.holdings.keys()}
        
        return {
            ticker: holding.market_value(prices[ticker]) / total
            for ticker, holding in self.holdings.items()
        }
    
    def get_all_tickers(self) -> List[str]:
        """
        Get list of all tickers in portfolio.
        
        Returns:
            List of ticker symbols
        """
        return list(self.holdings.keys())
    
    def get_positions(self, prices: Dict[str, float]) -> List[Dict]:
        """
        Get detailed position information for all holdings.
        
        Args:
            prices: Dictionary mapping ticker → current price
            
        Returns:
            List of position dictionaries with ticker, shares, value, etc.
        """
        positions = []
        for ticker, holding in self.holdings.items():
            if ticker not in prices:
                raise KeyError(f"Price not provided for ticker: {ticker}")
            
            shares = holding.current_shares()
            if shares == 0:
                continue  # Skip empty positions
            
            price = prices[ticker]
            value = holding.market_value(price)
            cost_basis = holding.cost_basis()
            unrealized_pl = holding.unrealized_gain_loss(price)
            
            positions.append({
                'ticker': ticker,
                'shares': shares,
                'price': price,
                'value': value,
                'cost_basis': cost_basis,
                'unrealized_pl': unrealized_pl,
                'unrealized_pl_pct': (unrealized_pl / cost_basis * 100) if cost_basis > 0 else 0.0,
                'average_cost': holding.average_cost_basis()
            })
        
        return sorted(positions, key=lambda p: p['value'], reverse=True)
    
    def portfolio_summary(self, prices: Dict[str, float]) -> dict:
        """
        Get comprehensive portfolio summary.
        
        Args:
            prices: Dictionary mapping ticker → current price
            
        Returns:
            Dictionary with portfolio-level statistics
        """
        total_value = self.total_value(prices)
        total_cost = self.total_cost_basis()
        realized_pl = self.total_realized_gain_loss()
        unrealized_pl = self.total_unrealized_gain_loss(prices)
        total_pl = realized_pl + unrealized_pl
        
        return {
            'total_tickers': len(self.holdings),
            'active_positions': sum(1 for h in self.holdings.values() if h.current_shares() > 0),
            'total_value': total_value,
            'total_cost_basis': total_cost,
            'realized_gain_loss': realized_pl,
            'unrealized_gain_loss': unrealized_pl,
            'total_gain_loss': total_pl,
            'total_return_pct': (total_pl / total_cost * 100) if total_cost > 0 else 0.0,
            'allocations': self.allocations(prices)
        }
    
    def __str__(self) -> str:
        """Human-readable portfolio summary."""
        active = sum(1 for h in self.holdings.values() if h.current_shares() > 0)
        return f"Portfolio: {active} active positions across {len(self.holdings)} tickers"
    
    def __repr__(self) -> str:
        return f"Portfolio(holdings={len(self.holdings)})"
