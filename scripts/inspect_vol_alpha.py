from datetime import date, timedelta
import pandas as pd
from pathlib import Path
import sys
# Ensure project imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.backtest import SyntheticDividendAlgorithm, run_algorithm_backtest

# Build the positive_alpha_recovery price series
prices = [100.0, 110.0, 101.0, 110.0, 120.0]
start_date = date(2024,1,1)
dates = [start_date + timedelta(days=i) for i in range(len(prices))]
df = pd.DataFrame({'Date': dates, 'Open': prices, 'High': prices, 'Low': prices, 'Close': prices, 'Volume': [1000000]*len(prices)})
df.set_index('Date', inplace=True)

ath_algo = SyntheticDividendAlgorithm(rebalance_size=0.0905, profit_sharing=0.5, buyback_enabled=False)
enhanced_algo = SyntheticDividendAlgorithm(rebalance_size=0.0905, profit_sharing=0.5, buyback_enabled=True)

ath_txns, ath_summary = run_algorithm_backtest(df=df, ticker='SYNTHETIC', initial_qty=1000, algo=ath_algo, start_date=df.index[0], end_date=df.index[-1])
enhanced_txns, enhanced_summary = run_algorithm_backtest(df=df, ticker='SYNTHETIC', initial_qty=1000, algo=enhanced_algo, start_date=df.index[0], end_date=df.index[-1])

print('ATH transactions:')
for t in ath_txns:
    print(t)
print('ATH summary:', ath_summary)

print('\nEnhanced transactions:')
for t in enhanced_txns:
    print(t)
print('Enhanced summary:', enhanced_summary)
