"""
Unit tests for volatility alpha using synthetic price data.

These tests use carefully constructed price sequences to validate:
1. ATH-only strategy behavior (baseline)
2. Enhanced strategy with buybacks (volatility alpha)
3. Symmetry properties of profit-sharing
4. Gap-up and gradual appreciation scenarios

No external data dependencies - all prices are synthetic and deterministic.
"""

import unittest
from datetime import date, timedelta
import pandas as pd
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.backtest import (
    SyntheticDividendAlgorithm,
    run_algorithm_backtest,
)


def create_synthetic_prices(scenario: str, start_price: float = 100.0) -> pd.DataFrame:
    """
    Create synthetic price data for testing.
    
    All scenarios end at new ATH to satisfy thesis requirements.
    
    Args:
        scenario: Type of price movement
        start_price: Initial price
        
    Returns:
        DataFrame with Date index and OHLC columns
    """
    start_date = date(2024, 1, 1)
    
    if scenario == "gradual_double":
        # Smooth doubling: 100 -> 200 over 100 days
        # No drawdowns, pure ATH progression
        days = 100
        prices = [start_price * (1 + i / days) for i in range(days + 1)]
        
    elif scenario == "gap_up_double":
        # Gap up scenario: 100 -> 100 -> 200 (sudden jump)
        # Simulates overnight gap, no intraday volatility
        days = 50
        prices = [start_price] * days + [start_price * 2.0] * days
        
    elif scenario == "volatile_double":
        # Volatile path to doubling with 50% drawdown in middle
        # 100 -> 150 -> 75 -> 200
        # Tests buyback behavior during drawdown
        segment1 = [start_price * (1 + 0.5 * i / 30) for i in range(30)]  # Up to 150
        segment2 = [150 - 75 * i / 30 for i in range(30)]  # Down to 75
        segment3 = [75 + 125 * i / 40 for i in range(41)]  # Up to 200
        prices = segment1 + segment2 + segment3
        
    elif scenario == "symmetrical_wave":
        # Perfect symmetrical wave: 100 -> 150 -> 100 -> 150
        # Tests symmetry property: buy at X, sell at X should be neutral
        up1 = [start_price * (1 + 0.5 * i / 25) for i in range(25)]  # 100 -> 150
        down1 = [150 - 50 * i / 25 for i in range(25)]  # 150 -> 100
        up2 = [start_price * (1 + 0.5 * i / 25) for i in range(26)]  # 100 -> 150
        prices = up1 + down1 + up2
        
    elif scenario == "multiple_ath":
        # Multiple ATH breaks: 100 -> 120 -> 140 -> 160 -> 180 -> 200
        # Each step is 20% gain, triggers sd8 (9% threshold)
        prices = []
        current = start_price
        for _ in range(6):
            segment = [current * (1 + 0.2 * i / 20) for i in range(20)]
            prices.extend(segment)
            current *= 1.2
        prices.append(current)
        
    elif scenario == "choppy_sideways_then_moon":
        # Sideways chop (90-110) then moon to 200
        # Tests transaction costs in sideways market
        chop_days = 60
        prices = []
        for i in range(chop_days):
            # Oscillate between 90 and 110
            prices.append(start_price + 10 * (i % 2 * 2 - 1))
        # Then moon to 200
        moon_days = 40
        prices.extend([100 + 100 * i / moon_days for i in range(moon_days + 1)])
        
    else:
        raise ValueError(f"Unknown scenario: {scenario}")
    
    # Create DataFrame
    dates = [start_date + timedelta(days=i) for i in range(len(prices))]
    df = pd.DataFrame({
        'Date': dates,
        'Open': prices,
        'High': prices,  # Simplified: no intraday variation
        'Low': prices,
        'Close': prices,
        'Volume': [1000000] * len(prices),  # Constant volume
    })
    df.set_index('Date', inplace=True)
    
    return df


class TestVolatilityAlphaWithSyntheticData(unittest.TestCase):
    """Test volatility alpha calculations with known synthetic price data."""
    
    def test_gradual_double_ath_only(self):
        """Test ATH-only strategy with smooth price doubling (no drawdowns)."""
        df = create_synthetic_prices("gradual_double", start_price=100.0)
        
        # ATH-only with sd8 trigger (9.05%)
        algo = SyntheticDividendAlgorithm(
            rebalance_size_pct=9.05,
            profit_sharing_pct=50.0,
            buyback_enabled=False  # ATH-only
        )
        
        transactions, summary = run_algorithm_backtest(
            df=df,
            ticker="SYNTHETIC",
            initial_qty=1000,
            start_date=df.index[0],
            end_date=df.index[-1],
            algo=algo,
        )
        
        # Assertions
        self.assertGreater(summary['total_return'], 0, "Should have positive return")
        self.assertGreater(len(transactions), 1, "Should have transactions beyond initial BUY")
        
        # With smooth doubling and 9.05% trigger, we expect ~8 sells
        # (2^(1/8) = 1.0905, so 8 steps to double)
        self.assertGreaterEqual(len(transactions), 6, "Should have at least 6 transactions")
        self.assertLessEqual(len(transactions), 10, "Should have at most 10 transactions")
        
        # All transactions should be SELL (ATH-only doesn't buy back)
        # Skip first transaction which is the initial BUY
        for txn in transactions[1:]:
            self.assertIn("SELL", txn, "ATH-only should only SELL")
    
    def test_gradual_double_enhanced_vs_ath(self):
        """Test that enhanced strategy matches ATH-only when there are no drawdowns."""
        df = create_synthetic_prices("gradual_double", start_price=100.0)
        
        # ATH-only
        ath_algo = SyntheticDividendAlgorithm(
            rebalance_size_pct=9.05,
            profit_sharing_pct=50.0,
            buyback_enabled=False
        )
        
        ath_txns, ath_summary = run_algorithm_backtest(
            df=df,
            ticker="SYNTHETIC",
            initial_qty=1000,
            start_date=df.index[0],
            end_date=df.index[-1],
            algo=ath_algo,
        )
        
        # Enhanced (with buybacks)
        enhanced_algo = SyntheticDividendAlgorithm(
            rebalance_size_pct=9.05,
            profit_sharing_pct=50.0,
            buyback_enabled=True
        )
        
        enhanced_txns, enhanced_summary = run_algorithm_backtest(
            df=df,
            ticker="SYNTHETIC",
            initial_qty=1000,
            start_date=df.index[0],
            end_date=df.index[-1],
            algo=enhanced_algo,
        )
        
        # With no drawdowns, enhanced should match ATH-only
        # (no opportunity for buybacks)
        self.assertEqual(len(ath_txns), len(enhanced_txns),
                        "Transaction count should match with no drawdowns")
        self.assertAlmostEqual(ath_summary['total_return'], enhanced_summary['total_return'],
                              places=4, msg="Returns should match with no drawdowns")
        
        # Volatility alpha (Enhanced vs ATH-only) should be ~0
        vol_alpha = enhanced_summary['total_return'] - ath_summary['total_return']
        self.assertAlmostEqual(vol_alpha, 0, places=4,
                              msg="No volatility alpha without drawdowns")
    
    def test_volatile_double_has_positive_volatility_alpha(self):
        """Test that volatile path generates positive volatility alpha."""
        df = create_synthetic_prices("volatile_double", start_price=100.0)
        
        # ATH-only
        ath_algo = SyntheticDividendAlgorithm(
            rebalance_size_pct=9.05,
            profit_sharing_pct=50.0,
            buyback_enabled=False
        )
        
        ath_txns, ath_summary = run_algorithm_backtest(
            df=df,
            ticker="SYNTHETIC",
            initial_qty=1000,
            start_date=df.index[0],
            end_date=df.index[-1],
            algo=ath_algo,
        )
        
        # Enhanced
        enhanced_algo = SyntheticDividendAlgorithm(
            rebalance_size_pct=9.05,
            profit_sharing_pct=50.0,
            buyback_enabled=True
        )
        
        enhanced_txns, enhanced_summary = run_algorithm_backtest(
            df=df,
            ticker="SYNTHETIC",
            initial_qty=1000,
            start_date=df.index[0],
            end_date=df.index[-1],
            algo=enhanced_algo,
        )
        
        # Enhanced should have MORE transactions (buybacks during drawdown)
        self.assertGreater(len(enhanced_txns), len(ath_txns),
                          "Enhanced should have more transactions with volatility")
        
        # Enhanced should have HIGHER return (volatility alpha)
        enhanced_return = enhanced_summary['total_return']
        ath_return = ath_summary['total_return']
        self.assertGreater(enhanced_return, ath_return,
                          "Enhanced should outperform ATH-only with volatility")
        
        # Volatility alpha (Enhanced vs ATH-only) should be positive
        vol_alpha = enhanced_return - ath_return
        self.assertGreater(vol_alpha, 0,
                          "Volatility alpha should be positive")
        
        # Enhanced should have both BUY and SELL transactions
        has_buy = any("BUY" in txn for txn in enhanced_txns)
        has_sell = any("SELL" in txn for txn in enhanced_txns)
        self.assertTrue(has_buy, "Enhanced should have BUY transactions")
        self.assertTrue(has_sell, "Enhanced should have SELL transactions")
    
    def test_symmetrical_wave_buyback_profit(self):
        """Test that buying low and selling high generates profit in symmetrical wave."""
        df = create_synthetic_prices("symmetrical_wave", start_price=100.0)
        
        enhanced_algo = SyntheticDividendAlgorithm(
            rebalance_size_pct=9.05,
            profit_sharing_pct=50.0,
            buyback_enabled=True
        )
        
        enhanced_txns, enhanced_summary = run_algorithm_backtest(
            df=df,
            ticker="SYNTHETIC",
            initial_qty=1000,
            start_date=df.index[0],
            end_date=df.index[-1],
            algo=enhanced_algo,
        )
        
        # Should have positive return despite ending at same level as first peak
        self.assertGreater(enhanced_summary['total_return'], 0,
                          "Should profit from buy-low-sell-high cycles")
        
        # Should have both buy and sell transactions
        buys = [txn for txn in enhanced_txns if "BUY" in txn]
        sells = [txn for txn in enhanced_txns if "SELL" in txn]
        self.assertGreater(len(buys), 0, "Should have buyback transactions")
        self.assertGreater(len(sells), 0, "Should have sell transactions")
    
    def test_gap_up_minimal_transactions(self):
        """Test that gap up scenario generates fewer transactions than volatile path."""
        gap_df = create_synthetic_prices("gap_up_double", start_price=100.0)
        volatile_df = create_synthetic_prices("volatile_double", start_price=100.0)
        
        algo_params = {
            'rebalance_size_pct': 9.05,
            'profit_sharing_pct': 50.0,
            'buyback_enabled': True
        }
        
        # Gap up scenario
        gap_algo = SyntheticDividendAlgorithm(**algo_params)
        gap_txns, gap_summary = run_algorithm_backtest(
            df=gap_df,
            ticker="SYNTHETIC",
            initial_qty=1000,
            start_date=gap_df.index[0],
            end_date=gap_df.index[-1],
            algo=gap_algo,
        )
        
        # Volatile scenario
        volatile_algo = SyntheticDividendAlgorithm(**algo_params)
        volatile_txns, volatile_summary = run_algorithm_backtest(
            df=volatile_df,
            ticker="SYNTHETIC",
            initial_qty=1000,
            start_date=volatile_df.index[0],
            end_date=volatile_df.index[-1],
            algo=volatile_algo,
        )
        
        # Gap up should have fewer transactions
        self.assertLess(len(gap_txns), len(volatile_txns),
                       "Gap up should have fewer transactions than volatile path")
    
    def test_multiple_ath_transaction_count(self):
        """Test that multiple ATH breaks generate expected number of transactions."""
        df = create_synthetic_prices("multiple_ath", start_price=100.0)
        
        # sd8 with 9.05% trigger should trigger on each 20% step
        algo = SyntheticDividendAlgorithm(
            rebalance_size_pct=9.05,
            profit_sharing_pct=50.0,
            buyback_enabled=False  # ATH-only for predictability
        )
        
        transactions, summary = run_algorithm_backtest(
            df=df,
            ticker="SYNTHETIC",
            initial_qty=1000,
            start_date=df.index[0],
            end_date=df.index[-1],
            algo=algo,
        )
        
        # Each 20% step should trigger at least one sell
        # 100 -> 200 is doubling, with 20% steps, expect 4-5 triggers
        self.assertGreaterEqual(len(transactions), 4,
                               "Should have multiple transactions for multiple ATH breaks")
    
    def test_profit_sharing_symmetry(self):
        """Test that 50% profit sharing leaves 50% in holdings."""
        df = create_synthetic_prices("gradual_double", start_price=100.0)
        
        algo = SyntheticDividendAlgorithm(
            rebalance_size_pct=9.05,
            profit_sharing_pct=50.0,  # 50/50 split
            buyback_enabled=False
        )
        
        transactions, summary = run_algorithm_backtest(
            df=df,
            ticker="SYNTHETIC",
            initial_qty=1000,
            start_date=df.index[0],
            end_date=df.index[-1],
            algo=algo,
        )
        
        # Final holdings should be roughly half of initial (due to 50% profit taking)
        # Exact amount depends on trigger points, but should be 40-60% range
        final_holdings = summary['holdings']
        self.assertGreater(final_holdings, 400,
                          "Should retain substantial holdings with 50% profit sharing")
        self.assertLess(final_holdings, 600,
                       "Should have sold substantial holdings with 50% profit sharing")
    
    def test_choppy_then_moon_volatility_alpha(self):
        """Test that choppy sideways market followed by moon shot generates alpha."""
        df = create_synthetic_prices("choppy_sideways_then_moon", start_price=100.0)
        
        # ATH-only
        ath_algo = SyntheticDividendAlgorithm(
            rebalance_size_pct=9.05,
            profit_sharing_pct=50.0,
            buyback_enabled=False
        )
        
        ath_txns, ath_summary = run_algorithm_backtest(
            df=df,
            ticker="SYNTHETIC",
            initial_qty=1000,
            start_date=df.index[0],
            end_date=df.index[-1],
            algo=ath_algo,
        )
        
        # Enhanced
        enhanced_algo = SyntheticDividendAlgorithm(
            rebalance_size_pct=9.05,
            profit_sharing_pct=50.0,
            buyback_enabled=True
        )
        
        enhanced_txns, enhanced_summary = run_algorithm_backtest(
            df=df,
            ticker="SYNTHETIC",
            initial_qty=1000,
            start_date=df.index[0],
            end_date=df.index[-1],
            algo=enhanced_algo,
        )
        
        # ATH-only should have few/no transactions during sideways period
        # Enhanced should profit from oscillations
        self.assertGreaterEqual(len(enhanced_txns), len(ath_txns),
                               "Enhanced should have at least as many transactions")
        
        # Both should capture the moon shot, but enhanced may have slight edge
        # from any profitable cycles during chop
        self.assertGreater(enhanced_summary['total_return'], 0,
                          "Enhanced should profit from final moon shot")


class TestProfitSharingSymmetry(unittest.TestCase):
    """Test mathematical properties of profit sharing."""
    
    def test_zero_profit_sharing_is_buy_and_hold(self):
        """Test that 0% profit sharing behaves like buy-and-hold."""
        df = create_synthetic_prices("gradual_double", start_price=100.0)
        
        algo = SyntheticDividendAlgorithm(
            rebalance_size_pct=9.05,
            profit_sharing_pct=0.0,  # Never sell
            buyback_enabled=True
        )
        
        transactions, summary = run_algorithm_backtest(
            df=df,
            ticker="SYNTHETIC",
            initial_qty=1000,
            start_date=df.index[0],
            end_date=df.index[-1],
            algo=algo,
        )
        
        # Should have no transactions (never sells with 0% profit sharing)
        self.assertEqual(len(transactions), 0,
                        "0% profit sharing should generate no transactions")
        
        # Should have 100% of initial holdings
        self.assertEqual(summary['holdings'], 1000,
                        "Should retain all initial holdings with 0% profit sharing")
        
        # Bank should be empty (never sold anything)
        self.assertEqual(summary['bank'], 0,
                        "Bank should be empty with 0% profit sharing")
    
    def test_hundred_percent_profit_sharing(self):
        """Test that 100% profit sharing sells entire profit portion."""
        df = create_synthetic_prices("gradual_double", start_price=100.0)
        
        algo = SyntheticDividendAlgorithm(
            rebalance_size_pct=9.05,
            profit_sharing_pct=100.0,  # Sell all profit
            buyback_enabled=False
        )
        
        transactions, summary = run_algorithm_backtest(
            df=df,
            ticker="SYNTHETIC",
            initial_qty=1000,
            start_date=df.index[0],
            end_date=df.index[-1],
            algo=algo,
        )
        
        # Should have transactions (selling profits)
        self.assertGreater(len(transactions), 0,
                          "Should have transactions with 100% profit sharing")
        
        # All transactions should be SELL
        for txn in transactions:
            self.assertIn("SELL", txn,
                         "100% profit sharing should only SELL")


if __name__ == '__main__':
    unittest.main()
