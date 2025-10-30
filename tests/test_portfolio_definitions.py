"""Tests for portfolio name parsing and definitions."""

import pytest

from src.algorithms.portfolio_definitions import parse_portfolio_name


def test_classic_portfolio_default():
    """Test classic 60/40 portfolio with default allocations."""
    allocations = parse_portfolio_name("classic")
    assert allocations == {"VOO": 0.6, "BIL": 0.4}
    assert sum(allocations.values()) == pytest.approx(1.0)


def test_classic_portfolio_custom():
    """Test classic portfolio with custom allocations."""
    allocations = parse_portfolio_name("classic-70,30")
    assert allocations == {"VOO": 0.7, "BIL": 0.3}
    assert sum(allocations.values()) == pytest.approx(1.0)

    allocations = parse_portfolio_name("classic-80,20")
    assert allocations == {"VOO": 0.8, "BIL": 0.2}
    assert sum(allocations.values()) == pytest.approx(1.0)


def test_classic_plus_crypto_default():
    """Test classic+crypto portfolio with default allocations."""
    allocations = parse_portfolio_name("classic-plus-crypto")
    assert allocations == {"VOO": 0.6, "BIL": 0.3, "BTC-USD": 0.1}
    assert sum(allocations.values()) == pytest.approx(1.0)


def test_classic_plus_crypto_custom():
    """Test classic+crypto portfolio with custom allocations."""
    allocations = parse_portfolio_name("classic-plus-crypto-60,30,10")
    assert allocations == {"VOO": 0.6, "BIL": 0.3, "BTC-USD": 0.1}
    assert sum(allocations.values()) == pytest.approx(1.0)

    allocations = parse_portfolio_name("classic-plus-crypto-50,30,20")
    assert allocations == {"VOO": 0.5, "BIL": 0.3, "BTC-USD": 0.2}
    assert sum(allocations.values()) == pytest.approx(1.0)


def test_buffet_portfolio_default():
    """Test Buffett 90/10 portfolio with default allocations."""
    allocations = parse_portfolio_name("buffet")
    assert allocations == {"VOO": 0.9, "BIL": 0.1}
    assert sum(allocations.values()) == pytest.approx(1.0)

    # Test alternate spelling
    allocations = parse_portfolio_name("buffett")
    assert allocations == {"VOO": 0.9, "BIL": 0.1}


def test_buffet_portfolio_custom():
    """Test Buffett portfolio with custom allocations."""
    allocations = parse_portfolio_name("buffet-95,5")
    assert allocations == {"VOO": 0.95, "BIL": 0.05}
    assert sum(allocations.values()) == pytest.approx(1.0)

    # Test alternate spelling
    allocations = parse_portfolio_name("buffett-85,15")
    assert allocations == {"VOO": 0.85, "BIL": 0.15}
    assert sum(allocations.values()) == pytest.approx(1.0)


def test_all_weather_portfolio():
    """Test Ray Dalio's All-Weather portfolio."""
    allocations = parse_portfolio_name("all-weather")
    assert "VOO" in allocations
    assert "TLT" in allocations
    assert "IEF" in allocations
    assert "GLD" in allocations
    assert "DBC" in allocations
    assert "BIL" in allocations
    assert sum(allocations.values()) == pytest.approx(1.0)


def test_three_fund_portfolio():
    """Test Bogleheads three-fund portfolio."""
    allocations = parse_portfolio_name("three-fund")
    assert allocations == {"VTI": 0.4, "VXUS": 0.3, "BND": 0.3}
    assert sum(allocations.values()) == pytest.approx(1.0)


def test_golden_butterfly_portfolio():
    """Test Tyler's Golden Butterfly portfolio."""
    allocations = parse_portfolio_name("golden-butterfly")
    assert len(allocations) == 5
    assert all(v == 0.2 for v in allocations.values())
    assert sum(allocations.values()) == pytest.approx(1.0)


def test_tech_growth_default():
    """Test tech growth portfolio with default allocations."""
    allocations = parse_portfolio_name("tech-growth")
    assert allocations == {"QQQ": 0.6, "VOO": 0.4}
    assert sum(allocations.values()) == pytest.approx(1.0)


def test_tech_growth_custom():
    """Test tech growth portfolio with custom allocations."""
    allocations = parse_portfolio_name("tech-growth-70,30")
    assert allocations == {"QQQ": 0.7, "VOO": 0.3}
    assert sum(allocations.values()) == pytest.approx(1.0)


def test_high_growth_portfolio():
    """Test high-growth portfolio."""
    allocations = parse_portfolio_name("high-growth")
    assert "NVDA" in allocations
    assert "QQQ" in allocations
    assert "VOO" in allocations
    assert sum(allocations.values()) == pytest.approx(1.0)


def test_crypto_heavy_portfolio():
    """Test crypto-heavy portfolio."""
    allocations = parse_portfolio_name("crypto-heavy")
    assert "BTC-USD" in allocations
    assert "ETH-USD" in allocations
    assert "VOO" in allocations
    assert "BIL" in allocations
    assert sum(allocations.values()) == pytest.approx(1.0)


def test_invalid_portfolio_name():
    """Test that invalid portfolio names raise ValueError."""
    with pytest.raises(ValueError, match="Unrecognized portfolio name"):
        parse_portfolio_name("invalid-portfolio-name")

    with pytest.raises(ValueError, match="Unrecognized portfolio name"):
        parse_portfolio_name("nonexistent")


def test_whitespace_handling():
    """Test that whitespace is properly handled."""
    allocations1 = parse_portfolio_name("classic")
    allocations2 = parse_portfolio_name("  classic  ")
    assert allocations1 == allocations2


def test_decimal_parameters():
    """Test that decimal parameters are supported."""
    allocations = parse_portfolio_name("classic-67.5,32.5")
    assert allocations == {"VOO": 0.675, "BIL": 0.325}
    assert sum(allocations.values()) == pytest.approx(1.0)


if __name__ == "__main__":
    # Run tests with output
    pytest.main([__file__, "-v"])
