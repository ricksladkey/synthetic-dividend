"""Demonstrate the impact of cash earning returns on multi-year retirement scenarios.

This script compares simple_mode=True (cash earns 0%) vs simple_mode=False (cash earns VOO)
over longer time periods to show the compounding effect.
"""

from datetime import date
from src.data.fetcher import HistoryFetcher
from src.algorithms.factory import build_algo_from_name
from src.models.retirement_backtest import run_retirement_backtest


def compare_multi_year_scenarios():
    """Compare cash strategies over multi-year periods to show compounding impact."""
    
    print("=" * 80)
    print("MULTI-YEAR CASH RETURNS IMPACT")
    print("=" * 80)
    print("\nComparing simple_mode=True (cash earns 0%) vs simple_mode=False (cash in VOO)")
    print("Over longer time periods, the compounding effect becomes dramatic!\n")
    
    scenarios = [
        {
            'name': 'NVDA 2020-2023 (4 years)',
            'ticker': 'NVDA',
            'start': date(2020, 1, 1),
            'end': date(2023, 12, 31),
            'algo': 'sd-9.05,50.0',
            'withdrawal': 0.05,
            'qty': 10000
        },
        {
            'name': 'VOO 2015-2019 (5 years)', 
            'ticker': 'VOO',
            'start': date(2015, 1, 1),
            'end': date(2019, 12, 31),
            'algo': 'sd-9.05,50.0',
            'withdrawal': 0.05,
            'qty': 1000
        },
        {
            'name': 'SPY 2010-2019 (10 years)',
            'ticker': 'SPY',
            'start': date(2010, 1, 1),
            'end': date(2019, 12, 31),
            'algo': 'sd-9.05,50.0',
            'withdrawal': 0.04,
            'qty': 1000
        },
    ]
    
    fetcher = HistoryFetcher()
    
    for scenario in scenarios:
        print("\n" + "=" * 80)
        print(f"SCENARIO: {scenario['name']}")
        print("=" * 80)
        
        # Fetch main asset data
        df = fetcher.get_history(scenario['ticker'], scenario['start'], scenario['end'])
        
        # Fetch VOO data for cash returns (same period)
        voo_df = fetcher.get_history('VOO', scenario['start'], scenario['end'])
        
        # Calculate initial value
        start_price = df.iloc[0]['Close'].item()
        end_price = df.iloc[-1]['Close'].item()
        initial_value = scenario['qty'] * start_price
        
        print(f"\nAsset: {scenario['ticker']}")
        print(f"Period: {scenario['start']} to {scenario['end']}")
        print(f"Initial value: ${initial_value:,.0f}")
        print(f"Price: ${start_price:.2f} → ${end_price:.2f} ({(end_price/start_price - 1)*100:+.1f}%)")
        print(f"Algorithm: {scenario['algo']}")
        print(f"Withdrawal: {scenario['withdrawal']*100:.0f}% annually")
        
        # Scenario 1: Cash earns 0% (simple_mode=True)
        print("\n" + "-" * 80)
        print("SIMPLE MODE (Cash earns 0%):")
        print("-" * 80)
        
        algo1 = build_algo_from_name(scenario['algo'])
        _, summary1 = run_retirement_backtest(
            df, scenario['ticker'], scenario['qty'], 
            scenario['start'], scenario['end'], algo1,
            annual_withdrawal_rate=scenario['withdrawal'],
            withdrawal_frequency='monthly',
            cpi_adjust=True,
            simple_mode=True  # Cash earns 0%
        )
        
        print(f"Final value: ${summary1['total']:,.0f}")
        print(f"  Holdings: {summary1['holdings']:,} shares × ${end_price:.2f} = ${summary1['holdings'] * end_price:,.0f}")
        print(f"  Bank: ${summary1['bank']:,.0f}")
        print(f"Total withdrawn: ${summary1['total_withdrawn']:,.0f}")
        net1 = summary1['total'] + summary1['total_withdrawn'] - initial_value
        print(f"Net result: ${net1:+,.0f} ({net1/initial_value*100:+.1f}%)")
        
        # Scenario 2: Cash earns VOO returns (simple_mode=False)
        print("\n" + "-" * 80)
        print("REALISTIC MODE (Cash earns VOO returns):")
        print("-" * 80)
        
        algo2 = build_algo_from_name(scenario['algo'])
        _, summary2 = run_retirement_backtest(
            df, scenario['ticker'], scenario['qty'],
            scenario['start'], scenario['end'], algo2,
            annual_withdrawal_rate=scenario['withdrawal'],
            withdrawal_frequency='monthly',
            cpi_adjust=True,
            simple_mode=False,  # Enable costs/gains
            risk_free_data=voo_df,  # Cash earns VOO returns
            risk_free_asset_ticker='VOO'
        )
        
        print(f"Final value: ${summary2['total']:,.0f}")
        print(f"  Holdings: {summary2['holdings']:,} shares × ${end_price:.2f} = ${summary2['holdings'] * end_price:,.0f}")
        print(f"  Bank: ${summary2['bank']:,.0f} (includes compounded gains)")
        print(f"Risk-free gains accumulated: ${summary2.get('risk_free_gains', 0):,.0f}")
        print(f"Total withdrawn: ${summary2['total_withdrawn']:,.0f}")
        net2 = summary2['total'] + summary2['total_withdrawn'] - initial_value
        print(f"Net result: ${net2:+,.0f} ({net2/initial_value*100:+.1f}%)")
        
        # Compare
        improvement = net2 - net1
        improvement_pct = (improvement / abs(net1)) * 100 if net1 != 0 else 0
        bank_diff = summary2['bank'] - summary1['bank']
        
        print("\n" + "-" * 80)
        print("IMPACT OF CASH EARNING VOO RETURNS:")
        print("-" * 80)
        print(f"Improvement: ${improvement:+,.0f} ({improvement_pct:+.1f}%)")
        print(f"Bank difference: ${bank_diff:+,.0f}")
        print(f"Years: {summary2['years']:.1f}")
        if summary2['years'] > 0:
            print(f"Annualized bank growth from VOO: {(bank_diff / summary1['bank']) / summary2['years'] * 100:.2f}%/year" 
                  if summary1['bank'] > 0 else "N/A")
        
        print("\n" + "=" * 80)
    
    print("\n\n" + "=" * 80)
    print("KEY INSIGHTS")
    print("=" * 80)
    print("""
1. **Compounding Matters**: Over multiple years, daily compounding of cash returns
   creates significant improvements compared to 1-year tests.

2. **Cash Isn't Dead Weight**: SD8 builds substantial cash reserves through 
   volatility harvesting. With simple_mode=False, this cash earns market returns.

3. **True 2-Asset Portfolio**: This is effectively a dynamic allocation between
   the main asset and VOO, with the allocation determined by harvested volatility alpha.

4. **Realistic vs Unrealistic**: 
   - simple_mode=True: Unrealistic (cash earns 0%, borrowing is free)
   - simple_mode=False: Realistic (cash earns returns, borrowing has cost)

5. **Multi-Year Impact**: The longer the time period, the more dramatic the
   compounding effect becomes. 10-year scenarios should show massive improvements.
""")
    print("=" * 80)


if __name__ == '__main__':
    compare_multi_year_scenarios()
