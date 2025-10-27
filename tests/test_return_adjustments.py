"""Tests for return adjustment calculations."""

import pytest
from datetime import date
from unittest.mock import Mock, patch
import pandas as pd

from src.models.return_adjustments import (
    calculate_adjusted_returns,
    print_adjusted_returns,
    format_adjustment_summary,
    add_adjusted_columns_to_summary,
)


@pytest.fixture
def sample_summary():
    """Sample backtest summary with known values."""
    return {
        'total_return': 0.518,  # 51.8% return
        'start_value': 10000.0,
        'total': 15180.0,  # $5,180 gain
    }


@pytest.fixture
def mock_cpi_prices():
    """Mock CPI price data showing 10% inflation."""
    return pd.DataFrame({
        'Close': [100.0, 110.0],  # 10% increase
        'Date': [date(2024, 1, 1), date(2024, 12, 31)]
    })


@pytest.fixture
def mock_market_prices():
    """Mock market price data showing 40% return."""
    return pd.DataFrame({
        'Close': [100.0, 140.0],  # 40% increase
        'Date': [date(2024, 1, 1), date(2024, 12, 31)]
    })


def test_calculate_nominal_only(sample_summary):
    """Test that nominal return is calculated correctly without adjustments."""
    result = calculate_adjusted_returns(
        sample_summary,
        date(2024, 1, 1),
        date(2024, 12, 31),
        adjust_inflation=False,
        adjust_market=False,
    )
    
    assert result['nominal_return'] == 0.518
    assert result['nominal_dollars'] == 5180.0
    assert result['start_value'] == 10000.0
    assert result['end_value'] == 15180.0
    assert 'real_return' not in result
    assert 'alpha' not in result


@patch('src.data.fetcher.Asset')
def test_calculate_inflation_adjusted(mock_asset_class, sample_summary, mock_cpi_prices):
    """Test inflation-adjusted return calculation."""
    # Setup mock
    mock_asset = Mock()
    mock_asset.get_prices.return_value = mock_cpi_prices
    mock_asset_class.return_value = mock_asset
    
    result = calculate_adjusted_returns(
        sample_summary,
        date(2024, 1, 1),
        date(2024, 12, 31),
        inflation_ticker='CPI',
        adjust_inflation=True,
        adjust_market=False,
    )
    
    # Verify CPI was fetched
    mock_asset_class.assert_called_once_with('CPI')
    mock_asset.get_prices.assert_called_once()
    
    # Check inflation metrics
    assert result['cpi_multiplier'] == 1.1
    assert abs(result['inflation_rate'] - 0.1) < 0.001  # 10%
    
    # Real return: End value / CPI multiplier - start value
    # $15,180 / 1.1 = $13,800
    # $13,800 - $10,000 = $3,800 real gain
    # $3,800 / $10,000 = 38% real return
    assert abs(result['real_return'] - 0.38) < 0.001
    assert abs(result['real_dollars'] - 3800.0) < 1.0
    
    # Purchasing power lost
    assert abs(result['purchasing_power_lost'] - 1380.0) < 1.0  # $5,180 - $3,800


@patch('src.data.fetcher.Asset')
def test_calculate_market_adjusted(mock_asset_class, sample_summary, mock_market_prices):
    """Test market-adjusted return calculation."""
    # Setup mock
    mock_asset = Mock()
    mock_asset.get_prices.return_value = mock_market_prices
    mock_asset_class.return_value = mock_asset
    
    result = calculate_adjusted_returns(
        sample_summary,
        date(2024, 1, 1),
        date(2024, 12, 31),
        market_ticker='VOO',
        adjust_inflation=False,
        adjust_market=True,
    )
    
    # Verify market benchmark was fetched
    mock_asset_class.assert_called_once_with('VOO')
    mock_asset.get_prices.assert_called_once()
    
    # Check market metrics
    assert result['market_return'] == 0.4  # 40%
    assert result['benchmark'] == 'VOO'
    
    # Alpha = your return - market return
    # 51.8% - 40% = 11.8%
    assert abs(result['alpha'] - 0.118) < 0.001
    
    # Alpha dollars = your dollars - (start * market return)
    # $5,180 - ($10,000 * 0.4) = $5,180 - $4,000 = $1,180
    assert abs(result['alpha_dollars'] - 1180.0) < 1.0


@patch('src.data.fetcher.Asset')
def test_calculate_both_adjustments(mock_asset_class, sample_summary, mock_cpi_prices, mock_market_prices):
    """Test calculating both inflation and market adjustments."""
    # Setup mock to return different data for CPI vs VOO
    def mock_asset_factory(ticker):
        mock = Mock()
        if ticker == 'CPI':
            mock.get_prices.return_value = mock_cpi_prices
        else:  # VOO
            mock.get_prices.return_value = mock_market_prices
        return mock
    
    mock_asset_class.side_effect = mock_asset_factory
    
    result = calculate_adjusted_returns(
        sample_summary,
        date(2024, 1, 1),
        date(2024, 12, 31),
        inflation_ticker='CPI',
        market_ticker='VOO',
        adjust_inflation=True,
        adjust_market=True,
    )
    
    # Should have both adjustments
    assert 'real_return' in result
    assert 'alpha' in result
    assert abs(result['real_return'] - 0.38) < 0.001
    assert abs(result['alpha'] - 0.118) < 0.001


def test_format_adjustment_summary():
    """Test summary formatting."""
    adjustments = {
        'nominal_return': 0.518,
        'real_return': 0.382,
        'alpha': 0.118,
    }
    
    summary = format_adjustment_summary(adjustments)
    
    assert "Nominal: +51.80%" in summary
    assert "Real: +38.20%" in summary
    assert "Alpha: +11.80%" in summary


def test_format_adjustment_summary_nominal_only():
    """Test summary formatting with only nominal return."""
    adjustments = {
        'nominal_return': 0.518,
    }
    
    summary = format_adjustment_summary(adjustments)
    
    assert "Nominal: +51.80%" in summary
    assert "Real" not in summary
    assert "Alpha" not in summary


def test_add_adjusted_columns_to_summary():
    """Test adding adjusted columns to summary dict."""
    summary = {
        'total_return': 0.518,
        'start_value': 10000.0,
    }
    
    adjustments = {
        'nominal_return': 0.518,
        'nominal_dollars': 5180.0,
        'real_return': 0.382,
        'real_dollars': 3800.0,
        'inflation_rate': 0.1,
        'cpi_multiplier': 1.1,
        'purchasing_power_lost': 1380.0,
        'alpha': 0.118,
        'alpha_dollars': 1180.0,
        'market_return': 0.4,
        'benchmark': 'VOO',
    }
    
    result = add_adjusted_columns_to_summary(summary, adjustments)
    
    # Original keys preserved
    assert result['total_return'] == 0.518
    assert result['start_value'] == 10000.0
    
    # Adjusted keys added
    assert result['real_return'] == 0.382
    assert result['alpha'] == 0.118
    assert result['market_return'] == 0.4
    assert result['benchmark'] == 'VOO'


def test_print_adjusted_returns_compact(capsys, sample_summary):
    """Test compact output format."""
    adjustments = {
        'nominal_return': 0.518,
        'nominal_dollars': 5180.0,
        'real_return': 0.382,
        'real_dollars': 3800.0,
        'alpha': 0.118,
        'alpha_dollars': 1180.0,
        'benchmark': 'VOO',
    }
    
    print_adjusted_returns(adjustments, verbose=False)
    
    captured = capsys.readouterr()
    output = captured.out
    
    assert "Nominal: +51.80%" in output
    assert "$5,180" in output
    assert "Real: +38.20%" in output
    assert "$3,800" in output
    assert "Alpha: +11.80%" in output
    assert "$1,180" in output
    assert "VOO" in output


def test_print_adjusted_returns_verbose(capsys, sample_summary):
    """Test verbose output format."""
    adjustments = {
        'nominal_return': 0.518,
        'nominal_dollars': 5180.0,
        'real_return': 0.382,
        'real_dollars': 3800.0,
        'inflation_rate': 0.1,
        'cpi_multiplier': 1.1,
        'purchasing_power_lost': 1380.0,
        'alpha': 0.118,
        'alpha_dollars': 1180.0,
        'market_return': 0.4,
        'benchmark': 'VOO',
    }
    
    print_adjusted_returns(adjustments, verbose=True)
    
    captured = capsys.readouterr()
    output = captured.out
    
    assert "RETURN BREAKDOWN" in output
    assert "Nominal Return:" in output
    assert "Inflation-Adjusted Return:" in output
    assert "Market-Adjusted Return" in output
    assert "51.80%" in output
    assert "38.20%" in output
    assert "11.80%" in output
    assert "Purchasing Power Lost:" in output


@patch('src.data.fetcher.Asset')
def test_error_handling_insufficient_data(mock_asset_class, sample_summary):
    """Test error handling when price data is insufficient."""
    # Setup mock to return insufficient data
    mock_asset = Mock()
    mock_asset.get_prices.return_value = pd.DataFrame({
        'Close': [100.0],  # Only one data point
        'Date': [date(2024, 1, 1)]
    })
    mock_asset_class.return_value = mock_asset
    
    result = calculate_adjusted_returns(
        sample_summary,
        date(2024, 1, 1),
        date(2024, 12, 31),
        adjust_inflation=True,
    )
    
    # Should have error info
    assert result['real_return'] is None
    assert 'inflation_error' in result
    assert "Insufficient" in result['inflation_error']


@patch('src.data.fetcher.Asset')
def test_error_handling_asset_fetch_failure(mock_asset_class, sample_summary):
    """Test error handling when asset fetch fails."""
    # Setup mock to raise exception
    mock_asset_class.side_effect = Exception("Network error")
    
    result = calculate_adjusted_returns(
        sample_summary,
        date(2024, 1, 1),
        date(2024, 12, 31),
        adjust_inflation=True,
    )
    
    # Should have error info
    assert result['real_return'] is None
    assert 'inflation_error' in result
    assert "Network error" in result['inflation_error']
