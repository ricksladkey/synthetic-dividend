"""Quick test of dividend fetching functionality."""
from datetime import date
from src.data.fetcher import HistoryFetcher

fetcher = HistoryFetcher()

# Test with AAPL (pays dividends)
print('Testing AAPL dividends...')
aapl_divs = fetcher.get_dividends('AAPL', date(2024, 1, 1), date(2024, 12, 31))
print(f'AAPL 2024 dividend payments: {len(aapl_divs)}')
total = aapl_divs.sum()
print(f'Total dividends: ${total:.4f} per share')
if not aapl_divs.empty:
    for dt, amt in aapl_divs.items():
        date_str = dt.strftime('%Y-%m-%d')
        print(f'  {date_str}: ${amt:.4f}')
print()

# Test with BIL (money market ETF - pays interest)
print('Testing BIL interest payments...')
bil_divs = fetcher.get_dividends('BIL', date(2024, 1, 1), date(2024, 12, 31))
print(f'BIL 2024 interest payments: {len(bil_divs)}')
total = bil_divs.sum()
print(f'Total interest: ${total:.4f} per share')
print(f'First payment: ${bil_divs.iloc[0]:.4f}')
print(f'Last payment: ${bil_divs.iloc[-1]:.4f}')
print()

# Test with NVDA (now pays dividends!)
print('Testing NVDA...')
nvda_divs = fetcher.get_dividends('NVDA', date(2024, 1, 1), date(2024, 12, 31))
print(f'NVDA 2024 dividend payments: {len(nvda_divs)}')
if not nvda_divs.empty:
    total = nvda_divs.sum()
    print(f'Total dividends: ${total:.4f} per share')
    for dt, amt in nvda_divs.items():
        date_str = dt.strftime('%Y-%m-%d')
        print(f'  {date_str}: ${amt:.4f}')
