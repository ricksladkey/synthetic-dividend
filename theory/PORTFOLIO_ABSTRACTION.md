# Portfolio Abstraction Design

## Vision

A **true self-contained portfolio abstraction** that manages multiple assets using the Synthetic Dividend algorithm with NAV-based coordination, automatic rebalancing, and consolidated reporting.

## Core Principles

1. **Asset Independence:** Each asset has its own NAV, buyback stack, and algorithm parameters
2. **Portfolio Coordination:** Cross-asset decisions (rebalancing, cash allocation) happen at portfolio level
3. **Unified Cash Management:** Single bank account shared across all assets
4. **NAV-Based Optimization:** Portfolio-level decisions driven by NAV premiums/discounts across assets
5. **Self-Contained:** Portfolio manages its own state, history, and performance metrics

## Architecture

```
Portfolio
├── Assets: List[Asset]
│   ├── Asset (NVDA)
│   │   ├── Ticker: "NVDA"
│   │   ├── Holdings: int
│   │   ├── NAV (ATH): float
│   │   ├── Algorithm: SyntheticDividendAlgorithm
│   │   └── BuybackStack: List[BuybackLot]
│   │
│   ├── Asset (BTC-USD)
│   │   ├── Ticker: "BTC-USD"
│   │   ├── Holdings: int
│   │   ├── NAV (ATH): float
│   │   ├── Algorithm: SyntheticDividendAlgorithm
│   │   └── BuybackStack: List[BuybackLot]
│   └── ...
│
├── Bank: float (shared cash pool)
├── PortfolioNAV: float (sum of asset NAVs)
├── RebalancingEngine: PortfolioRebalancer
├── TransactionHistory: List[PortfolioTransaction]
└── PerformanceMetrics: PortfolioMetrics
```

## Asset Class

```python
@dataclass
class Asset:
    """Single asset within portfolio."""
    
    ticker: str
    asset_class: str  # 'growth_stocks', 'crypto', 'commodities', 'indices'
    holdings: int
    nav: float  # Internal NAV (ATH)
    algorithm: SyntheticDividendAlgorithm
    buyback_stack: List[BuybackLot]
    
    # Asset-specific metrics
    total_dividends_generated: float = 0.0
    total_invested: float = 0.0
    transaction_count: int = 0
    
    def get_market_value(self, current_price: float) -> float:
        """Current market value of holdings."""
        return self.holdings * current_price
    
    def get_nav_value(self) -> float:
        """Value using internal NAV."""
        return self.holdings * self.nav
    
    def get_nav_premium(self, current_price: float) -> float:
        """Calculate premium/discount to NAV (%)."""
        if self.nav == 0:
            return 0.0
        return (current_price - self.nav) / self.nav
    
    def process_day(
        self,
        date: date,
        ohlc: Dict[str, float],
        available_cash: float
    ) -> Tuple[List[Transaction], float]:
        """
        Process one trading day for this asset.
        
        Returns:
            (transactions, cash_required)
            
        cash_required can be negative (cash generated from sells)
        """
        transactions = self.algorithm.on_day(
            date=date,
            open_price=ohlc['open'],
            high=ohlc['high'],
            low=ohlc['low'],
            close=ohlc['close'],
            holdings=self.holdings,
            bank=available_cash
        )
        
        # Calculate net cash impact
        cash_required = 0.0
        for tx in transactions:
            if tx.action == 'BUY':
                cash_required += tx.qty * tx.price
            elif tx.action == 'SELL':
                cash_required -= tx.qty * tx.price
        
        return transactions, cash_required
```

## Portfolio Class

```python
class Portfolio:
    """
    Self-contained portfolio managing multiple assets with synthetic dividend algorithm.
    """
    
    def __init__(
        self,
        initial_cash: float,
        rebalancing_mode: str = 'nav_opportunistic',
        withdrawal_policy: Optional[WithdrawalPolicy] = None
    ):
        self.assets: Dict[str, Asset] = {}
        self.bank: float = initial_cash
        self.initial_capital: float = initial_cash
        
        self.rebalancing_mode = rebalancing_mode
        self.withdrawal_policy = withdrawal_policy
        
        self.transaction_history: List[PortfolioTransaction] = []
        self.daily_snapshots: List[PortfolioSnapshot] = []
        
        # Portfolio-level metrics
        self.peak_portfolio_value: float = initial_cash
        self.total_dividends_generated: float = 0.0
        self.total_withdrawals: float = 0.0
    
    def add_asset(
        self,
        ticker: str,
        asset_class: str,
        initial_qty: int,
        initial_price: float,
        sd_n: int = 8,
        profit_sharing_pct: float = 50.0,
        buyback_enabled: bool = True
    ) -> None:
        """Add asset to portfolio with initial position."""
        
        # Create algorithm for this asset
        algo = SyntheticDividendAlgorithm(
            rebalance_size_pct=calculate_trigger(sd_n),
            profit_sharing_pct=profit_sharing_pct,
            buyback_enabled=buyback_enabled
        )
        
        # Create asset
        asset = Asset(
            ticker=ticker,
            asset_class=asset_class,
            holdings=initial_qty,
            nav=initial_price,
            algorithm=algo,
            buyback_stack=[]
        )
        
        self.assets[ticker] = asset
        
        # Deduct initial purchase from bank
        initial_cost = initial_qty * initial_price
        self.bank -= initial_cost
        
        # Record transaction
        self.transaction_history.append(
            PortfolioTransaction(
                date=date.today(),
                ticker=ticker,
                action='INITIAL_BUY',
                qty=initial_qty,
                price=initial_price,
                total=initial_cost,
                bank_after=self.bank
            )
        )
    
    def process_day(
        self,
        current_date: date,
        market_data: Dict[str, Dict[str, float]]
    ) -> PortfolioDayResult:
        """
        Process one trading day for entire portfolio.
        
        Args:
            current_date: Trading date
            market_data: Dict mapping ticker → OHLC dict
            
        Returns:
            PortfolioDayResult with all transactions and metrics
        """
        
        day_transactions = []
        
        # Phase 1: Collect potential transactions from all assets
        asset_proposals = {}
        for ticker, asset in self.assets.items():
            if ticker not in market_data:
                continue
                
            txns, cash_impact = asset.process_day(
                date=current_date,
                ohlc=market_data[ticker],
                available_cash=self.bank
            )
            
            asset_proposals[ticker] = {
                'transactions': txns,
                'cash_impact': cash_impact,
                'nav_premium': asset.get_nav_premium(market_data[ticker]['close'])
            }
        
        # Phase 2: Prioritize and execute based on portfolio strategy
        executed = self._execute_portfolio_strategy(
            current_date,
            asset_proposals,
            market_data
        )
        
        # Phase 3: Handle withdrawals if policy exists
        if self.withdrawal_policy:
            withdrawal_txns = self._process_withdrawals(current_date)
            executed.extend(withdrawal_txns)
        
        # Phase 4: Record snapshot
        snapshot = self._create_snapshot(current_date, market_data)
        self.daily_snapshots.append(snapshot)
        
        return PortfolioDayResult(
            date=current_date,
            transactions=executed,
            snapshot=snapshot
        )
    
    def _execute_portfolio_strategy(
        self,
        current_date: date,
        asset_proposals: Dict[str, Dict],
        market_data: Dict[str, Dict[str, float]]
    ) -> List[PortfolioTransaction]:
        """
        Execute transactions based on portfolio-level strategy.
        
        Strategies:
        - 'simple': Execute all affordable transactions
        - 'nav_opportunistic': Prioritize largest NAV deviations
        - 'rebalancing': Maintain target allocations
        """
        
        if self.rebalancing_mode == 'simple':
            return self._execute_simple(current_date, asset_proposals)
        
        elif self.rebalancing_mode == 'nav_opportunistic':
            return self._execute_nav_opportunistic(current_date, asset_proposals)
        
        elif self.rebalancing_mode == 'rebalancing':
            return self._execute_rebalancing(current_date, asset_proposals, market_data)
        
        else:
            raise ValueError(f"Unknown rebalancing mode: {self.rebalancing_mode}")
    
    def _execute_simple(
        self,
        current_date: date,
        asset_proposals: Dict[str, Dict]
    ) -> List[PortfolioTransaction]:
        """Execute all transactions in order (sells first, then buys)."""
        
        executed = []
        
        # Execute all sells first (generate cash)
        for ticker, proposal in asset_proposals.items():
            for tx in proposal['transactions']:
                if tx.action == 'SELL':
                    self._execute_transaction(current_date, ticker, tx)
                    executed.append(self._to_portfolio_transaction(current_date, ticker, tx))
        
        # Execute buys if cash available
        for ticker, proposal in asset_proposals.items():
            for tx in proposal['transactions']:
                if tx.action == 'BUY':
                    cost = tx.qty * tx.price
                    if self.bank >= cost:
                        self._execute_transaction(current_date, ticker, tx)
                        executed.append(self._to_portfolio_transaction(current_date, ticker, tx))
                    else:
                        # Skip buy - insufficient cash
                        executed.append(self._create_skip_transaction(current_date, ticker, tx))
        
        return executed
    
    def _execute_nav_opportunistic(
        self,
        current_date: date,
        asset_proposals: Dict[str, Dict]
    ) -> List[PortfolioTransaction]:
        """
        Prioritize transactions by NAV deviation magnitude.
        
        Logic:
        - Sells from assets with highest NAV premium (most overvalued)
        - Buys for assets with largest NAV discount (most undervalued)
        """
        
        executed = []
        
        # Collect all transactions with NAV deviation
        all_txns = []
        for ticker, proposal in asset_proposals.items():
            for tx in proposal['transactions']:
                all_txns.append({
                    'ticker': ticker,
                    'transaction': tx,
                    'nav_premium': proposal['nav_premium']
                })
        
        # Sort by NAV deviation (sells from high premium first, buys from low premium last)
        # For sells: Higher premium = higher priority (capture overvaluation)
        # For buys: Lower premium (more negative = larger discount) = higher priority
        
        sells = [t for t in all_txns if t['transaction'].action == 'SELL']
        buys = [t for t in all_txns if t['transaction'].action == 'BUY']
        
        sells.sort(key=lambda x: x['nav_premium'], reverse=True)
        buys.sort(key=lambda x: x['nav_premium'])  # Most negative first
        
        # Execute sells first
        for item in sells:
            self._execute_transaction(current_date, item['ticker'], item['transaction'])
            executed.append(self._to_portfolio_transaction(
                current_date, item['ticker'], item['transaction']
            ))
        
        # Execute buys if cash available
        for item in buys:
            tx = item['transaction']
            cost = tx.qty * tx.price
            if self.bank >= cost:
                self._execute_transaction(current_date, item['ticker'], tx)
                executed.append(self._to_portfolio_transaction(current_date, item['ticker'], tx))
            else:
                executed.append(self._create_skip_transaction(current_date, item['ticker'], tx))
        
        return executed
    
    def _execute_transaction(
        self,
        current_date: date,
        ticker: str,
        transaction: Transaction
    ) -> None:
        """Execute transaction and update portfolio state."""
        
        asset = self.assets[ticker]
        
        if transaction.action == 'BUY':
            cost = transaction.qty * transaction.price
            self.bank -= cost
            asset.holdings += transaction.qty
            asset.total_invested += cost
            
        elif transaction.action == 'SELL':
            proceeds = transaction.qty * transaction.price
            self.bank += proceeds
            asset.holdings -= transaction.qty
            asset.total_dividends_generated += proceeds
            self.total_dividends_generated += proceeds
        
        asset.transaction_count += 1
    
    def get_portfolio_nav(self) -> float:
        """Calculate total portfolio NAV (sum of asset NAVs)."""
        return sum(asset.get_nav_value() for asset in self.assets.values())
    
    def get_portfolio_market_value(self, market_data: Dict[str, float]) -> float:
        """Calculate total portfolio market value."""
        total = self.bank
        for ticker, asset in self.assets.items():
            if ticker in market_data:
                total += asset.get_market_value(market_data[ticker])
        return total
    
    def get_portfolio_performance(self) -> PortfolioPerformance:
        """Calculate portfolio-level performance metrics."""
        
        if not self.daily_snapshots:
            return PortfolioPerformance()
        
        latest = self.daily_snapshots[-1]
        
        total_return = (latest.total_value - self.initial_capital) / self.initial_capital
        
        # Calculate max drawdown
        peak = self.initial_capital
        max_dd = 0.0
        for snapshot in self.daily_snapshots:
            if snapshot.total_value > peak:
                peak = snapshot.total_value
            dd = (peak - snapshot.total_value) / peak
            if dd > max_dd:
                max_dd = dd
        
        return PortfolioPerformance(
            total_return=total_return,
            total_value=latest.total_value,
            bank_balance=self.bank,
            max_drawdown=max_dd,
            total_dividends=self.total_dividends_generated,
            total_withdrawals=self.total_withdrawals,
            sharpe_ratio=self._calculate_sharpe()
        )
```

## Data Structures

```python
@dataclass
class PortfolioTransaction:
    """Single transaction in portfolio context."""
    date: date
    ticker: str
    action: str  # 'BUY', 'SELL', 'INITIAL_BUY', 'WITHDRAWAL', 'SKIP_BUY'
    qty: int
    price: float
    total: float  # Total cash impact
    bank_after: float
    nav_premium: float = 0.0  # NAV premium at time of transaction

@dataclass
class PortfolioSnapshot:
    """Daily snapshot of portfolio state."""
    date: date
    total_value: float
    bank: float
    asset_values: Dict[str, float]  # ticker → market value
    asset_navs: Dict[str, float]    # ticker → NAV value
    holdings: Dict[str, int]        # ticker → shares
    nav_premiums: Dict[str, float]  # ticker → premium %

@dataclass
class PortfolioDayResult:
    """Result of processing one day."""
    date: date
    transactions: List[PortfolioTransaction]
    snapshot: PortfolioSnapshot

@dataclass
class PortfolioPerformance:
    """Portfolio-level performance metrics."""
    total_return: float
    total_value: float
    bank_balance: float
    max_drawdown: float
    total_dividends: float
    total_withdrawals: float
    sharpe_ratio: float
```

## Rebalancing Strategies

### 1. Simple (No Coordination)

Each asset trades independently based on its own algorithm. No cross-asset coordination.

**Pros:** Simple, asset isolation
**Cons:** May deplete cash buying one asset while missing opportunities in others

### 2. NAV Opportunistic

Prioritize transactions by NAV deviation magnitude:
- Sell most overvalued assets first (highest NAV premium)
- Buy most undervalued assets first (largest NAV discount)

**Pros:** Automatically rebalances toward value, captures largest opportunities
**Cons:** May starve less-extreme opportunities

### 3. Target Allocation Rebalancing

Maintain target allocation percentages:
```python
target_allocations = {
    'NVDA': 0.25,
    'BTC-USD': 0.25,
    'SPY': 0.25,
    'GLD': 0.25
}
```

When asset drifts from target, rebalance back.

**Pros:** Maintains diversification, automatically sells winners/buys losers
**Cons:** May override algorithm signals

### 4. Hybrid: NAV-Constrained Allocation

Use NAV signals within allocation bands:
```python
allocation_bands = {
    'NVDA': (0.20, 0.30),  # Min 20%, max 30%
    'BTC-USD': (0.20, 0.30),
    'SPY': (0.20, 0.30),
    'GLD': (0.20, 0.30)
}
```

- Allow NAV-driven trading within bands
- Rebalance if allocation exceeds band
- Best of both worlds

## Usage Example

```python
# Create portfolio
portfolio = Portfolio(
    initial_cash=400_000,
    rebalancing_mode='nav_opportunistic'
)

# Add assets
portfolio.add_asset('NVDA', 'growth_stocks', 1000, 100.0, sd_n=8)
portfolio.add_asset('BTC-USD', 'crypto', 1000, 50.0, sd_n=8)
portfolio.add_asset('SPY', 'indices', 1000, 500.0, sd_n=12)
portfolio.add_asset('GLD', 'commodities', 1000, 200.0, sd_n=12)

# Run backtest
for date in date_range:
    market_data = fetch_market_data(date)
    result = portfolio.process_day(date, market_data)
    
    print(f"{date}: {len(result.transactions)} transactions, "
          f"portfolio value: ${result.snapshot.total_value:,.0f}")

# Get performance
perf = portfolio.get_portfolio_performance()
print(f"Total return: {perf.total_return:.2%}")
print(f"Dividends generated: ${perf.total_dividends:,.0f}")
print(f"Max drawdown: {perf.max_drawdown:.2%}")
```

## Advanced Features

### Cross-Asset NAV Arbitrage

When one asset is at high premium and another at deep discount:

```python
def check_arbitrage_opportunity(self) -> Optional[ArbitrageOpportunity]:
    """
    Find arbitrage: sell asset with high NAV premium,
    buy asset with large NAV discount.
    """
    premiums = {
        ticker: asset.get_nav_premium(market_price)
        for ticker, asset in self.assets.items()
    }
    
    max_premium_ticker = max(premiums, key=premiums.get)
    min_premium_ticker = min(premiums, key=premiums.get)
    
    spread = premiums[max_premium_ticker] - premiums[min_premium_ticker]
    
    if spread > 0.15:  # 15% spread threshold
        return ArbitrageOpportunity(
            sell_ticker=max_premium_ticker,
            buy_ticker=min_premium_ticker,
            spread=spread
        )
    
    return None
```

### Portfolio-Level Withdrawal Management

```python
class WithdrawalPolicy:
    """Manage portfolio-level withdrawals."""
    
    def __init__(
        self,
        monthly_amount: float,
        coverage_ratio_min: float = 1.0
    ):
        self.monthly_amount = monthly_amount
        self.coverage_ratio_min = coverage_ratio_min
    
    def calculate_withdrawal(
        self,
        portfolio: Portfolio,
        current_date: date
    ) -> Optional[float]:
        """
        Calculate withdrawal amount.
        
        Only withdraw if coverage ratio > minimum.
        """
        if current_date.day != 1:
            return None  # Only withdraw on first of month
        
        coverage = portfolio.total_dividends_generated / (
            self.monthly_amount * (current_date.year * 12 + current_date.month)
        )
        
        if coverage >= self.coverage_ratio_min:
            return min(self.monthly_amount, portfolio.bank)
        
        return 0.0  # Skip withdrawal if coverage insufficient
```

### Dynamic SD_N Adjustment

```python
def optimize_sd_n_by_gap_frequency(self, ticker: str) -> int:
    """
    Adjust sd_n based on observed gap frequency for this asset.
    
    More gaps → tighter trigger (higher sd_n) to capture more bonus.
    """
    asset = self.assets[ticker]
    
    # Analyze recent gap frequency
    gaps = self._count_recent_gaps(ticker, days=90)
    gap_frequency = gaps / 90
    
    if gap_frequency > 0.15:  # >15% of days have gaps
        return 12  # Tight trigger for high-gap assets
    elif gap_frequency > 0.05:
        return 8
    else:
        return 6  # Wider trigger for smooth assets
```

## Benefits of Portfolio Abstraction

1. **Unified Cash Management:** Single bank shared across assets
2. **Cross-Asset Optimization:** Can prioritize best opportunities
3. **Automatic Rebalancing:** NAV-driven allocation adjustments
4. **Consolidated Reporting:** Portfolio-level metrics
5. **Withdrawal Management:** Coordinated income generation
6. **Risk Management:** Portfolio-level drawdown monitoring
7. **Tax Optimization:** Can choose which asset to sell for withdrawals

## Next Steps

1. **Implement base Portfolio class**
2. **Test with 2-asset portfolio** (NVDA + SPY)
3. **Add NAV opportunistic strategy**
4. **Backtest against simple strategy**
5. **Add withdrawal policy**
6. **Scale to 10+ asset portfolio**
7. **Performance comparison vs individual asset strategies**

## Open Questions

1. Should portfolio maintain its own "portfolio NAV" or just sum asset NAVs?
2. How to handle cash allocation when multiple assets want to buy simultaneously?
3. Should we add transaction costs at portfolio level?
4. How to visualize portfolio-level NAV dynamics?
5. Should rebalancing be time-based (monthly) or signal-based (allocation drift)?

