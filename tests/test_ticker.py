"""Tests for ticker data retrieval functionality."""

import pytest
import pandas as pd
from datetime import date
from unittest.mock import Mock, patch
from src.synthetic_dividend_tool import run_ticker


class TestTickerFunctionality:
    """Test the ticker data retrieval and aggregation functionality."""

    @pytest.fixture
    def mock_asset(self):
        """Create a mock Asset with sample price data."""
        # Create sample daily data for testing
        dates = pd.date_range('2024-01-01', '2024-01-31', freq='D')
        data = {
            'Open': [100 + i * 0.5 for i in range(len(dates))],
            'High': [102 + i * 0.5 for i in range(len(dates))],
            'Low': [98 + i * 0.5 for i in range(len(dates))],
            'Close': [101 + i * 0.5 for i in range(len(dates))],
            'Volume': [1000000 + i * 10000 for i in range(len(dates))]
        }
        df = pd.DataFrame(data, index=dates)
        return df

    def test_ticker_daily_aggregation(self, mock_asset, capsys):
        """Test daily ticker data retrieval (no aggregation needed)."""
        # Mock the Asset class
        with patch('src.data.asset.Asset') as mock_asset_class:
            mock_instance = Mock()
            mock_instance.get_prices.return_value = mock_asset
            mock_asset_class.return_value = mock_instance

            # Create mock args
            args = Mock()
            args.ticker = 'TEST'
            args.start = '2024-01-01'
            args.end = '2024-01-31'
            args.interval = 'daily'
            args.output = None

            # Run the function
            result = run_ticker(args)

            # Check result
            assert result == 0

            # Check output
            captured = capsys.readouterr()
            output_lines = captured.out.strip().split('\n')

            # Should have header + 31 data rows
            assert len(output_lines) == 32  # header + 31 days

            # Check header (strip carriage returns)
            assert output_lines[0].rstrip('\r') == 'Date,Ticker,O,C,L,H'

            # Check first data row
            first_row = [field.rstrip('\r') for field in output_lines[1].split(',')]
            assert first_row[0] == '2024-01-01'
            assert first_row[1] == 'TEST'
            assert first_row[2] == '100.0'  # Open
            assert first_row[3] == '101.0'  # Close
            assert first_row[4] == '98.0'   # Low
            assert first_row[5] == '102.0'  # High

    def test_ticker_weekly_aggregation(self, mock_asset, capsys):
        """Test weekly ticker data aggregation."""
        with patch('src.data.asset.Asset') as mock_asset_class:
            mock_instance = Mock()
            mock_instance.get_prices.return_value = mock_asset
            mock_asset_class.return_value = mock_instance

            args = Mock()
            args.ticker = 'TEST'
            args.start = '2024-01-01'
            args.end = '2024-01-31'
            args.interval = 'weekly'
            args.output = None

            result = run_ticker(args)
            assert result == 0

            captured = capsys.readouterr()
            output_lines = captured.out.strip().split('\n')

            # Should have header + weekly aggregated rows
            assert len(output_lines) >= 6  # header + at least 5 weeks

            # Check header
            assert output_lines[0].rstrip('\r') == 'Date,Ticker,O,C,L,H'

    def test_ticker_monthly_aggregation(self, mock_asset, capsys):
        """Test monthly ticker data aggregation."""
        with patch('src.data.asset.Asset') as mock_asset_class:
            mock_instance = Mock()
            mock_instance.get_prices.return_value = mock_asset
            mock_asset_class.return_value = mock_instance

            args = Mock()
            args.ticker = 'TEST'
            args.start = '2024-01-01'
            args.end = '2024-01-31'
            args.interval = 'monthly'
            args.output = None

            result = run_ticker(args)
            assert result == 0

            captured = capsys.readouterr()
            output_lines = captured.out.strip().split('\n')

            # Should have header + 1 monthly row (all data is in January)
            assert len(output_lines) == 2

            # Check header
            assert output_lines[0].rstrip('\r') == 'Date,Ticker,O,C,L,H'

    def test_ticker_empty_data(self, capsys):
        """Test handling of empty data."""
        with patch('src.data.asset.Asset') as mock_asset_class:
            mock_instance = Mock()
            mock_instance.get_prices.return_value = pd.DataFrame()  # Empty DataFrame
            mock_asset_class.return_value = mock_instance

            args = Mock()
            args.ticker = 'EMPTY'
            args.start = '2024-01-01'
            args.end = '2024-01-31'
            args.interval = 'daily'
            args.output = None

            result = run_ticker(args)
            assert result == 1

            captured = capsys.readouterr()
            assert "No data found" in captured.out

    def test_ticker_invalid_date_format(self, capsys):
        """Test handling of invalid date formats."""
        args = Mock()
        args.ticker = 'TEST'
        args.start = 'invalid-date'
        args.end = '2024-01-31'
        args.interval = 'daily'
        args.output = None

        result = run_ticker(args)
        assert result == 1

        captured = capsys.readouterr()
        assert "Error retrieving ticker data" in captured.out

    @patch('builtins.open')
    @patch('pandas.DataFrame.to_csv')
    def test_ticker_output_to_file(self, mock_to_csv, mock_open, mock_asset):
        """Test outputting ticker data to a file."""
        with patch('src.data.asset.Asset') as mock_asset_class:
            mock_instance = Mock()
            mock_instance.get_prices.return_value = mock_asset
            mock_asset_class.return_value = mock_instance

            args = Mock()
            args.ticker = 'TEST'
            args.start = '2024-01-01'
            args.end = '2024-01-31'
            args.interval = 'daily'
            args.output = 'output.csv'

            result = run_ticker(args)
            assert result == 0

            # Verify to_csv was called
            mock_to_csv.assert_called_once()

    def test_ticker_invalid_interval(self, mock_asset):
        """Test handling of invalid interval."""
        with patch('src.data.asset.Asset') as mock_asset_class:
            mock_instance = Mock()
            mock_instance.get_prices.return_value = mock_asset
            mock_asset_class.return_value = mock_instance

            args = Mock()
            args.ticker = 'TEST'
            args.start = '2024-01-01'
            args.end = '2024-01-31'
            args.interval = 'invalid'  # This should be caught by argparse, but test anyway
            args.output = None

            # Since argparse handles the choices, this shouldn't reach our function
            # But if it does, it should handle gracefully
            result = run_ticker(args)
            # The function now validates interval, so it should return 1 for invalid interval
            assert result == 1