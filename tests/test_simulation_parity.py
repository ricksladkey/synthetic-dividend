"""Tests to verify parity between simulation.py and backtest.py implementations."""

import pytest
from datetime import date
from typing import Dict, Any, List

from src.models.backtest import run_portfolio_backtest
from src.models.simulation import run_portfolio_simulation
from src.models.model_types import Transaction


def compare_summaries(summary1: Dict[str, Any], summary2: Dict[str, Any], tolerance: float = 1e-10) -> None:
    """Compare two backtest summaries for equality within tolerance."""
    # Compare key financial metrics
    key_metrics = [
        'total_final_value',
        'final_bank',
        'final_asset_value',
        'total_return',
        'annualized_return',
        'initial_investment',
        'total_withdrawn',
        'withdrawal_count',
        'cash_interest_earned',
        'opportunity_cost',
        'transaction_count',
        'skipped_count',
    ]

    for metric in key_metrics:
        if metric in summary1 and metric in summary2:
            val1 = summary1[metric]
            val2 = summary2[metric]
            assert abs(val1 - val2) < tolerance, f"{metric}: {val1} != {val2}"

    # Compare daily values if present
    if 'daily_values' in summary1 and 'daily_values' in summary2:
        daily1 = summary1['daily_values']
        daily2 = summary2['daily_values']
        assert len(daily1) == len(daily2), f"Daily values length: {len(daily1)} != {len(daily2)}"

        for date_key in daily1:
            if date_key in daily2:
                assert abs(daily1[date_key] - daily2[date_key]) < tolerance, \
                    f"Daily value {date_key}: {daily1[date_key]} != {daily2[date_key]}"


def compare_transactions(txns1: List[Transaction], txns2: List[Transaction]) -> None:
    """Compare transaction lists for equality."""
    assert len(txns1) == len(txns2), f"Transaction count: {len(txns1)} != {len(txns2)}"

    for i, (tx1, tx2) in enumerate(zip(txns1, txns2)):
        assert tx1.transaction_date == tx2.transaction_date, f"Tx {i} date: {tx1.transaction_date} != {tx2.transaction_date}"
        assert tx1.action == tx2.action, f"Tx {i} action: {tx1.action} != {tx2.action}"
        assert tx1.qty == tx2.qty, f"Tx {i} qty: {tx1.qty} != {tx2.qty}"
        assert abs(tx1.price - tx2.price) < 1e-6, f"Tx {i} price: {tx1.price} != {tx2.price}"
        assert tx1.ticker == tx2.ticker, f"Tx {i} ticker: {tx1.ticker} != {tx2.ticker}"


class TestSimulationParity:
    """Test parity between simulation and backtest implementations."""

    def test_buy_and_hold_single_asset(self):
        """Test simple buy-and-hold with single asset."""
        allocations = {'NVDA': 1.0}
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        initial_investment = 10000.0

        # Run both implementations
        txns_backtest, summary_backtest = run_portfolio_backtest(
            allocations=allocations,
            start_date=start_date,
            end_date=end_date,
            portfolio_algo='per-asset:buy-and-hold',
            initial_investment=initial_investment,
        )

        txns_sim, summary_sim = run_portfolio_simulation(
            allocations=allocations,
            start_date=start_date,
            end_date=end_date,
            portfolio_algo='per-asset:buy-and-hold',
            initial_investment=initial_investment,
        )

        # Compare results
        compare_summaries(summary_backtest, summary_sim)
        compare_transactions(txns_backtest, txns_sim)

    def test_buy_and_hold_multi_asset(self):
        """Test buy-and-hold with multiple assets."""
        allocations = {'NVDA': 0.6, 'AAPL': 0.4}
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        initial_investment = 10000.0

        # Run both implementations
        txns_backtest, summary_backtest = run_portfolio_backtest(
            allocations=allocations,
            start_date=start_date,
            end_date=end_date,
            portfolio_algo='per-asset:buy-and-hold',
            initial_investment=initial_investment,
        )

        txns_sim, summary_sim = run_portfolio_simulation(
            allocations=allocations,
            start_date=start_date,
            end_date=end_date,
            portfolio_algo='per-asset:buy-and-hold',
            initial_investment=initial_investment,
        )

        # Compare results
        compare_summaries(summary_backtest, summary_sim)
        compare_transactions(txns_backtest, txns_sim)

    def test_with_withdrawals(self):
        """Test with periodic withdrawals."""
        allocations = {'NVDA': 1.0}
        start_date = date(2024, 1, 1)
        end_date = date(2024, 3, 31)  # 3 months for multiple withdrawals
        initial_investment = 100000.0
        withdrawal_rate_pct = 4.0  # 4% annual withdrawal

        # Run both implementations
        txns_backtest, summary_backtest = run_portfolio_backtest(
            allocations=allocations,
            start_date=start_date,
            end_date=end_date,
            portfolio_algo='per-asset:buy-and-hold',
            initial_investment=initial_investment,
            withdrawal_rate_pct=withdrawal_rate_pct,
        )

        txns_sim, summary_sim = run_portfolio_simulation(
            allocations=allocations,
            start_date=start_date,
            end_date=end_date,
            portfolio_algo='per-asset:buy-and-hold',
            initial_investment=initial_investment,
            withdrawal_rate_pct=withdrawal_rate_pct,
        )

        # Compare results
        compare_summaries(summary_backtest, summary_sim)
        compare_transactions(txns_backtest, txns_sim)

    def test_with_reference_rate(self):
        """Test with reference rate for opportunity cost."""
        allocations = {'NVDA': 1.0}
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        initial_investment = 10000.0
        reference_rate_ticker = 'SPY'

        # Run both implementations
        txns_backtest, summary_backtest = run_portfolio_backtest(
            allocations=allocations,
            start_date=start_date,
            end_date=end_date,
            portfolio_algo='per-asset:buy-and-hold',
            initial_investment=initial_investment,
            reference_rate_ticker=reference_rate_ticker,
        )

        txns_sim, summary_sim = run_portfolio_simulation(
            allocations=allocations,
            start_date=start_date,
            end_date=end_date,
            portfolio_algo='per-asset:buy-and-hold',
            initial_investment=initial_investment,
            reference_rate_ticker=reference_rate_ticker,
        )

        # Compare results
        compare_summaries(summary_backtest, summary_sim)
        compare_transactions(txns_backtest, txns_sim)

    def test_with_risk_free_rate(self):
        """Test with risk-free rate for cash interest."""
        allocations = {'NVDA': 1.0}
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        initial_investment = 10000.0
        risk_free_rate_ticker = 'BIL'

        # Run both implementations
        txns_backtest, summary_backtest = run_portfolio_backtest(
            allocations=allocations,
            start_date=start_date,
            end_date=end_date,
            portfolio_algo='per-asset:buy-and-hold',
            initial_investment=initial_investment,
            risk_free_rate_ticker=risk_free_rate_ticker,
        )

        txns_sim, summary_sim = run_portfolio_simulation(
            allocations=allocations,
            start_date=start_date,
            end_date=end_date,
            portfolio_algo='per-asset:buy-and-hold',
            initial_investment=initial_investment,
            risk_free_rate_ticker=risk_free_rate_ticker,
        )

        # Compare results
        compare_summaries(summary_backtest, summary_sim)
        compare_transactions(txns_backtest, txns_sim)

    def test_with_negative_bank(self):
        """Test scenario that creates negative bank balance."""
        allocations = {'NVDA': 1.0}
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        initial_investment = 10000.0

        # Use synthetic dividend algorithm which can create leverage
        txns_backtest, summary_backtest = run_portfolio_backtest(
            allocations=allocations,
            start_date=start_date,
            end_date=end_date,
            portfolio_algo='per-asset:sd8',
            initial_investment=initial_investment,
            allow_margin=True,
        )

        txns_sim, summary_sim = run_portfolio_simulation(
            allocations=allocations,
            start_date=start_date,
            end_date=end_date,
            portfolio_algo='per-asset:sd8',
            initial_investment=initial_investment,
            allow_margin=True,
        )

        # Compare results
        compare_summaries(summary_backtest, summary_sim)
        compare_transactions(txns_backtest, txns_sim)

    def test_with_inflation(self):
        """Test with inflation adjustment."""
        allocations = {'NVDA': 1.0}
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        initial_investment = 10000.0
        inflation_rate_ticker = 'CPI'

        # Run both implementations
        txns_backtest, summary_backtest = run_portfolio_backtest(
            allocations=allocations,
            start_date=start_date,
            end_date=end_date,
            portfolio_algo='per-asset:buy-and-hold',
            initial_investment=initial_investment,
            inflation_rate_ticker=inflation_rate_ticker,
        )

        txns_sim, summary_sim = run_portfolio_simulation(
            allocations=allocations,
            start_date=start_date,
            end_date=end_date,
            portfolio_algo='per-asset:buy-and-hold',
            initial_investment=initial_investment,
            inflation_rate_ticker=inflation_rate_ticker,
        )

        # Compare results
        compare_summaries(summary_backtest, summary_sim)
        compare_transactions(txns_backtest, txns_sim)

    def test_skip_mode(self):
        """Test strict mode where insufficient cash skips transactions."""
        allocations = {'NVDA': 1.0}
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        initial_investment = 1000.0  # Small amount to force skips

        # Use synthetic dividend algorithm which can create leverage
        txns_backtest, summary_backtest = run_portfolio_backtest(
            allocations=allocations,
            start_date=start_date,
            end_date=end_date,
            portfolio_algo='per-asset:sd8',
            initial_investment=initial_investment,
            allow_margin=False,  # Strict mode
        )

        txns_sim, summary_sim = run_portfolio_simulation(
            allocations=allocations,
            start_date=start_date,
            end_date=end_date,
            portfolio_algo='per-asset:sd8',
            initial_investment=initial_investment,
            allow_margin=False,  # Strict mode
        )

        # Compare results
        compare_summaries(summary_backtest, summary_sim)
        compare_transactions(txns_backtest, txns_sim)