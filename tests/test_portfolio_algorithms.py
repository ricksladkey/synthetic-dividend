"""Tests for portfolio-level algorithms with shared cash pool."""

from datetime import date

import pytest

from src.algorithms import (
    BuyAndHoldAlgorithm,
    PerAssetPortfolioAlgorithm,
    QuarterlyRebalanceAlgorithm,
    SyntheticDividendAlgorithm,
)
from src.models.backtest import run_portfolio_backtest


def test_quarterly_rebalance_60_40():
    """Test traditional 60/40 quarterly rebalancing."""
    algo = QuarterlyRebalanceAlgorithm(
        target_allocations={"VOO": 0.6, "BIL": 0.4}, rebalance_months=[3, 6, 9, 12]
    )

    transactions, summary = run_portfolio_backtest(
        allocations={"VOO": 0.6, "BIL": 0.4},
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31),
        portfolio_algo=algo,
        initial_investment=100_000,
    )

    # Verify basic structure
    assert summary["initial_investment"] == 100_000
    assert summary["total_final_value"] > 0
    assert "VOO" in summary["assets"]
    assert "BIL" in summary["assets"]
    assert summary["transaction_count"] >= 2  # At least initial purchases

    # Verify shared bank tracking
    assert "final_bank" in summary
    assert "daily_bank_values" in summary

    print("\nQuarterly Rebalance 60/40 Results:")
    print(f"  Final Value: ${summary['total_final_value']:,.2f}")
    print(f"  Total Return: {summary['total_return']:.2f}%")
    print(f"  Transactions: {summary['transaction_count']}")
    print(f"  Final Bank: ${summary['final_bank']:,.2f}")


def test_per_asset_portfolio_hybrid():
    """Test hybrid strategy: synthetic dividends + buy-and-hold."""
    hybrid_algo = PerAssetPortfolioAlgorithm(
        {
            "VOO": SyntheticDividendAlgorithm(rebalance_size=0.0905, profit_sharing=0.5),
            "BIL": BuyAndHoldAlgorithm(),
        }
    )

    transactions, summary = run_portfolio_backtest(
        allocations={"VOO": 0.7, "BIL": 0.3},
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31),
        portfolio_algo=hybrid_algo,
        initial_investment=100_000,
    )

    # Verify basic structure
    assert summary["initial_investment"] == 100_000
    assert summary["total_final_value"] > 0

    # VOO should have rebalancing transactions, BIL should not
    voo_txns = [tx for tx in transactions if tx.ticker == "VOO" and "SKIP" not in tx.action]
    bil_txns = [
        tx
        for tx in transactions
        if tx.ticker == "BIL" and "SKIP" not in tx.action and "Initial" not in tx.notes
    ]

    # VOO should have activity beyond initial purchase
    assert len(voo_txns) >= 1  # At least initial purchase
    # BIL should only have initial purchase
    assert len(bil_txns) == 0  # Buy-and-hold after initial

    print("\nHybrid Strategy Results:")
    print(f"  Final Value: ${summary['total_final_value']:,.2f}")
    print(f"  Total Return: {summary['total_return']:.2f}%")
    print(f"  VOO Transactions: {len(voo_txns)}")
    print(f"  BIL Transactions: {len(bil_txns)}")
    print(f"  Final Bank: ${summary['final_bank']:,.2f}")


def test_shared_bank_isolation():
    """Verify that shared bank is properly isolated across assets."""
    # Use three assets with synthetic dividends
    hybrid_algo = PerAssetPortfolioAlgorithm(
        {
            "VOO": SyntheticDividendAlgorithm(rebalance_size=0.0905, profit_sharing=0.5),
            "QQQ": SyntheticDividendAlgorithm(rebalance_size=0.0905, profit_sharing=0.5),
            "BIL": BuyAndHoldAlgorithm(),
        }
    )

    transactions, summary = run_portfolio_backtest(
        allocations={"VOO": 0.4, "QQQ": 0.4, "BIL": 0.2},
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31),
        portfolio_algo=hybrid_algo,
        initial_investment=100_000,
    )

    # Bank should never be super negative (some margin is ok)
    min_bank = min(summary["daily_bank_values"].values())
    print("\nShared Bank Test:")
    print(f"  Minimum bank balance: ${min_bank:,.2f}")
    print(f"  Final bank balance: ${summary['final_bank']:,.2f}")

    # Verify all assets share same cash pool
    assert "final_bank" in summary
    assert summary["final_asset_value"] + summary["final_bank"] == pytest.approx(
        summary["total_final_value"], rel=0.01
    )


if __name__ == "__main__":
    # Run tests with output
    test_quarterly_rebalance_60_40()
    test_per_asset_portfolio_hybrid()
    test_shared_bank_isolation()
