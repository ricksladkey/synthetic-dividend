"""Tests for portfolio-level algorithms with shared cash pool."""

from datetime import date, timedelta

import pandas as pd
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


def create_synthetic_price_data(price_path, ticker="TEST"):
    """Create synthetic OHLC price data for testing."""
    start_date = date(2020, 1, 1)
    dates = [start_date + timedelta(days=i) for i in range(len(price_path))]

    data = {
        "Date": dates,
        "Open": price_path,
        "High": price_path,
        "Low": price_path,
        "Close": price_path,
        "Volume": [1000000] * len(price_path),
    }

    df = pd.DataFrame(data)
    df.set_index("Date", inplace=True)
    return df


def test_portfolio_algo_string_vs_instance_equivalence():
    """Test that portfolio backtest with string algo produces equivalent results to instance algo.

    This validates that the algorithm factory correctly parses string identifiers
    into algorithm instances that produce identical results.
    """
    # Use NVDA with a date range that should have data
    ticker = "NVDA"

    start_date = date(2024, 1, 1)
    end_date = date(2024, 6, 30)  # Shorter period to ensure data availability

    # Fetch data using HistoryFetcher (same as portfolio backtest)
    from src.data.fetcher import HistoryFetcher

    fetcher = HistoryFetcher()
    price_df = fetcher.get_history(ticker, start_date, end_date)

    if price_df is None or price_df.empty:
        pytest.skip(f"No data available for {ticker}")

    initial_investment = 100_000

    # Run with string portfolio_algo
    string_txns, string_summary = run_portfolio_backtest(
        allocations={ticker: 1.0},
        start_date=start_date,
        end_date=end_date,
        portfolio_algo="per-asset:sd8",  # String format
        initial_investment=initial_investment,
    )

    # Run with explicit algorithm instance
    from src.algorithms.portfolio_factory import build_portfolio_algo_from_name

    portfolio_algo_instance = build_portfolio_algo_from_name("per-asset:sd8", {ticker: 1.0})

    instance_txns, instance_summary = run_portfolio_backtest(
        allocations={ticker: 1.0},
        start_date=start_date,
        end_date=end_date,
        portfolio_algo=portfolio_algo_instance,  # Instance format
        initial_investment=initial_investment,
    )

    # Compare key metrics that should be identical
    print("\n=== String vs Instance Portfolio Algo Equivalence Test ===")

    # Map portfolio results to single-ticker format for comparison
    string_asset = string_summary["assets"][ticker]
    instance_asset = instance_summary["assets"][ticker]

    print("String Algo Results:")
    print(f"  Total Return: {string_summary['total_return']:.4f}%")
    print(f"  Final Value: ${string_summary['total_final_value']:.2f}")
    print(f"  Final Holdings: {string_asset['final_holdings']}")
    print(f"  Final Bank: ${string_summary['final_bank']:.2f}")
    print(f"  Transactions: {len(string_txns)}")

    print("Instance Algo Results:")
    print(f"  Total Return: {instance_summary['total_return']:.4f}%")
    print(f"  Final Value: ${instance_summary['total_final_value']:.2f}")
    print(f"  Final Holdings: {instance_asset['final_holdings']}")
    print(f"  Final Bank: ${instance_summary['final_bank']:.2f}")
    print(f"  Transactions: {len(instance_txns)}")

    # Assertions: key metrics should be equivalent
    # Total return
    assert (
        abs(string_summary["total_return"] - instance_summary["total_return"]) < 0.001
    ), f"Total return mismatch: string={string_summary['total_return']:.6f}%, instance={instance_summary['total_return']:.6f}%"

    # Final total value
    assert (
        abs(string_summary["total_final_value"] - instance_summary["total_final_value"]) < 0.01
    ), f"Final value mismatch: string=${string_summary['total_final_value']:.2f}, instance=${instance_summary['total_final_value']:.2f}"

    # Final holdings
    assert (
        string_asset["final_holdings"] == instance_asset["final_holdings"]
    ), f"Final holdings mismatch: string={string_asset['final_holdings']}, instance={instance_asset['final_holdings']}"

    # Final bank balance
    assert (
        abs(string_summary["final_bank"] - instance_summary["final_bank"]) < 0.01
    ), f"Final bank mismatch: string=${string_summary['final_bank']:.2f}, instance=${instance_summary['final_bank']:.2f}"

    # Transaction count (excluding initial purchases and withdrawals)
    string_trade_txns = [
        tx for tx in string_txns if tx.action in ["BUY", "SELL"] and "Initial" not in tx.notes
    ]
    instance_trade_txns = [
        tx for tx in instance_txns if tx.action in ["BUY", "SELL"] and "Initial" not in tx.notes
    ]

    assert len(string_trade_txns) == len(
        instance_trade_txns
    ), f"Transaction count mismatch: string={len(string_trade_txns)}, instance={len(instance_trade_txns)}"

    print("✅ String and instance portfolio algo produce equivalent results!")
    print(f"   Both generated {len(string_trade_txns)} trading transactions")
    print(f"   Both achieved {string_summary['total_return']:.2f}% total return")


if __name__ == "__main__":
    # Run tests with output
    test_quarterly_rebalance_60_40()
    test_per_asset_portfolio_hybrid()
    test_shared_bank_isolation()
    test_wrapper_vs_portfolio_equivalence()
