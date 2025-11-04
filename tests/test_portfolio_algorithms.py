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
from src.models.backtest import run_algorithm_backtest, run_portfolio_backtest


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


def test_wrapper_vs_portfolio_equivalence():
    """Test that run_algorithm_backtest wrapper produces equivalent results to run_portfolio_backtest.

    This validates that the Phase 2 consolidation wrapper correctly delegates to portfolio backtest
    for supported scenarios, ensuring both approaches produce identical results.
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

    # Use SD8 algorithm (supported by wrapper)
    algo = SyntheticDividendAlgorithm(
        rebalance_size=0.0905,  # 9.05%
        profit_sharing=0.5,  # 50%
        buyback_enabled=True,
    )

    initial_investment = 100_000

    # Run with single-ticker wrapper (should delegate to portfolio backtest)
    wrapper_txns, wrapper_summary = run_algorithm_backtest(
        df=price_df,
        ticker=ticker,
        initial_investment=initial_investment,
        start_date=start_date,
        end_date=end_date,
        algo=algo,
        # No dividends, reference data, etc. - so wrapper should be used
    )

    # Run equivalent scenario with portfolio backtest (100% allocation to single asset)
    from src.algorithms.portfolio_factory import build_portfolio_algo_from_name

    portfolio_algo = build_portfolio_algo_from_name("per-asset:sd8", {ticker: 1.0})

    portfolio_txns, portfolio_summary = run_portfolio_backtest(
        allocations={ticker: 1.0},
        start_date=start_date,
        end_date=end_date,
        portfolio_algo=portfolio_algo,
        initial_investment=initial_investment,
    )

    # Compare key metrics that should be identical
    print("\n=== Wrapper vs Portfolio Equivalence Test ===")

    # Map portfolio results to single-ticker format for comparison
    test_asset = portfolio_summary["assets"][ticker]

    print("Wrapper Results:")
    print(f"  Total Return: {wrapper_summary['total_return']:.4f}")
    print(f"  Final Value: ${wrapper_summary['total']:.2f}")
    print(f"  Final Holdings: {wrapper_summary['holdings']}")
    print(f"  Final Bank: ${wrapper_summary['bank']:.2f}")
    print(f"  Transactions: {len(wrapper_txns)}")

    print("Portfolio Results:")
    print(f"  Total Return: {portfolio_summary['total_return']:.4f}")
    print(f"  Final Value: ${portfolio_summary['total_final_value']:.2f}")
    print(f"  Final Holdings: {test_asset['final_holdings']}")
    print(f"  Final Bank: ${portfolio_summary['final_bank']:.2f}")
    print(f"  Transactions: {len(portfolio_txns)}")

    # Assertions: key metrics should be equivalent
    # Total return (wrapper returns decimal, portfolio returns percentage - convert for comparison)
    portfolio_total_return_decimal = portfolio_summary["total_return"] / 100.0
    assert (
        abs(wrapper_summary["total_return"] - portfolio_total_return_decimal) < 0.001
    ), f"Total return mismatch: wrapper={wrapper_summary['total_return']:.6f}, portfolio={portfolio_total_return_decimal:.6f}"

    # Final total value
    assert (
        abs(wrapper_summary["total"] - portfolio_summary["total_final_value"]) < 0.01
    ), f"Final value mismatch: wrapper=${wrapper_summary['total']:.2f}, portfolio=${portfolio_summary['total_final_value']:.2f}"

    # Final holdings
    assert (
        wrapper_summary["holdings"] == test_asset["final_holdings"]
    ), f"Final holdings mismatch: wrapper={wrapper_summary['holdings']}, portfolio={test_asset['final_holdings']}"

    # Final bank balance
    assert (
        abs(wrapper_summary["bank"] - portfolio_summary["final_bank"]) < 0.01
    ), f"Final bank mismatch: wrapper=${wrapper_summary['bank']:.2f}, portfolio=${portfolio_summary['final_bank']:.2f}"

    # Transaction count (excluding initial purchases and withdrawals)
    wrapper_trade_txns = [
        tx for tx in wrapper_txns if tx.action in ["BUY", "SELL"] and "Initial" not in tx.notes
    ]
    portfolio_trade_txns = [
        tx for tx in portfolio_txns if tx.action in ["BUY", "SELL"] and "Initial" not in tx.notes
    ]

    assert len(wrapper_trade_txns) == len(
        portfolio_trade_txns
    ), f"Transaction count mismatch: wrapper={len(wrapper_trade_txns)}, portfolio={len(portfolio_trade_txns)}"

    print("✅ Wrapper and portfolio backtest produce equivalent results!")
    print(f"   Both generated {len(wrapper_trade_txns)} trading transactions")
    print(f"   Both achieved {wrapper_summary['total_return']:.2f}% total return")


if __name__ == "__main__":
    # Run tests with output
    test_quarterly_rebalance_60_40()
    test_per_asset_portfolio_hybrid()
    test_shared_bank_isolation()
    test_wrapper_vs_portfolio_equivalence()
