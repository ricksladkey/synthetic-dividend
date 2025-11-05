import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

# Ensure project imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.backtest import SyntheticDividendAlgorithm, run_portfolio_backtest  # noqa: E402

# Build the positive_alpha_recovery price series
prices = [100.0, 110.0, 101.0, 110.0, 120.0]
start_date = date(2024, 1, 1)
dates = [start_date + timedelta(days=i) for i in range(len(prices))]
df = pd.DataFrame(
    {
        "Date": dates,
        "Open": prices,
        "High": prices,
        "Low": prices,
        "Close": prices,
        "Volume": [1000000] * len(prices),
    }
)
df.set_index("Date", inplace=True)

# Mock the fetcher
from unittest.mock import patch

import src.data.fetcher as fetcher_module

original_get_history = fetcher_module.HistoryFetcher.get_history


def mock_get_history(self, ticker, start_date, end_date):
    if ticker == "SYNTHETIC":
        return df
    return original_get_history(self, ticker, start_date, end_date)


allocations = {"SYNTHETIC": 1.0}
initial_investment = 1000 * df.iloc[0]["Close"]

with patch.object(fetcher_module.HistoryFetcher, "get_history", mock_get_history):
    ath_txns, ath_portfolio_summary = run_portfolio_backtest(
        allocations=allocations,
        start_date=df.index[0],
        end_date=df.index[-1],
        portfolio_algo="per-asset:sd-ath-only-9.05,50",
        initial_investment=initial_investment,
    )

    enhanced_txns, enhanced_portfolio_summary = run_portfolio_backtest(
        allocations=allocations,
        start_date=df.index[0],
        end_date=df.index[-1],
        portfolio_algo="per-asset:sd-9.05,50",
        initial_investment=initial_investment,
    )

# Map to single-ticker format for compatibility
from src.models.backtest import _map_portfolio_to_single_ticker_summary

ath_summary = _map_portfolio_to_single_ticker_summary(
    portfolio_summary=ath_portfolio_summary,
    ticker="SYNTHETIC",
    df_indexed=df,
    start_date=df.index[0],
    end_date=df.index[-1],
    algo_obj=None,
    transactions=ath_txns,
)

enhanced_summary = _map_portfolio_to_single_ticker_summary(
    portfolio_summary=enhanced_portfolio_summary,
    ticker="SYNTHETIC",
    df_indexed=df,
    start_date=df.index[0],
    end_date=df.index[-1],
    algo_obj=None,
    transactions=enhanced_txns,
)

print("ATH transactions:")
for t in ath_txns:
    print(t)
print("ATH summary:", ath_summary)

print("\nEnhanced transactions:")
for t in enhanced_txns:
    print(t)
print("Enhanced summary:", enhanced_summary)
