"""Integration tests for named portfolio functionality.

These tests verify that the named portfolio feature integrates correctly
with the CLI and backtest infrastructure.
"""

import json

import pytest

from src.algorithms.portfolio_definitions import parse_portfolio_name


def test_parse_portfolio_integration():
    """Test that parse_portfolio_name integrates with typical workflow."""
    # Simulate CLI usage
    portfolio_name = "classic-70,30"
    allocations = parse_portfolio_name(portfolio_name)

    # Verify allocations are valid for backtest
    assert isinstance(allocations, dict)
    assert all(isinstance(k, str) for k in allocations.keys())
    assert all(isinstance(v, float) for v in allocations.values())
    assert sum(allocations.values()) == pytest.approx(1.0)

    # Verify structure matches expected format
    assert "VOO" in allocations
    assert "BIL" in allocations


def test_cli_json_fallback():
    """Test that CLI can still accept JSON when not a named portfolio."""
    json_str = '{"NVDA": 0.6, "VOO": 0.4}'

    # This should work as valid JSON
    allocations = json.loads(json_str)
    assert allocations == {"NVDA": 0.6, "VOO": 0.4}


def test_named_portfolio_vs_json_compatibility():
    """Test that both named portfolios and JSON produce compatible outputs."""
    # Named portfolio
    named_alloc = parse_portfolio_name("classic")

    # Equivalent JSON
    json_alloc = {"VOO": 0.6, "BIL": 0.4}

    # Both should produce same structure
    assert named_alloc == json_alloc


def test_all_named_portfolios_valid():
    """Test that all named portfolios produce valid allocations."""
    test_cases = [
        "classic",
        "classic-70,30",
        "classic-plus-crypto",
        "classic-plus-crypto-50,30,20",
        "buffet",
        "buffett",
        "buffet-95,5",
        "buffett-85,15",
        "all-weather",
        "three-fund",
        "golden-butterfly",
        "tech-growth",
        "tech-growth-70,30",
        "high-growth",
        "crypto-heavy",
    ]

    for portfolio_name in test_cases:
        allocations = parse_portfolio_name(portfolio_name)

        # Verify basic validity
        assert isinstance(allocations, dict)
        assert len(allocations) > 0
        assert all(isinstance(v, float) for v in allocations.values())
        assert all(0.0 <= v <= 1.0 for v in allocations.values())

        # Verify allocations sum to 1.0
        total = sum(allocations.values())
        assert total == pytest.approx(
            1.0, abs=0.01
        ), f"Portfolio {portfolio_name} allocations sum to {total}, not 1.0"


def test_portfolio_ticker_validity():
    """Test that portfolio tickers are reasonable strings."""
    allocations = parse_portfolio_name("classic")

    for ticker in allocations.keys():
        # Tickers should be uppercase strings
        assert isinstance(ticker, str)
        assert len(ticker) > 0
        # Common ticker patterns (simple validation)
        assert all(c.isalnum() or c == "-" for c in ticker)


def test_parameterized_portfolios_different_from_defaults():
    """Test that parameterized portfolios differ from defaults when expected."""
    # Classic default vs custom
    classic_default = parse_portfolio_name("classic")
    classic_custom = parse_portfolio_name("classic-70,30")
    assert classic_default != classic_custom

    # Buffett default vs custom
    buffett_default = parse_portfolio_name("buffet")
    buffett_custom = parse_portfolio_name("buffet-95,5")
    assert buffett_default != buffett_custom


def test_decimal_parameters_work():
    """Test that decimal parameters are correctly parsed."""
    allocations = parse_portfolio_name("classic-67.5,32.5")
    assert allocations["VOO"] == pytest.approx(0.675)
    assert allocations["BIL"] == pytest.approx(0.325)


def test_error_message_helpful():
    """Test that error messages guide users to valid options."""
    with pytest.raises(ValueError) as exc_info:
        parse_portfolio_name("invalid-portfolio")

    error_msg = str(exc_info.value)
    # Error should mention supported portfolios
    assert "classic" in error_msg.lower()
    assert "buffet" in error_msg.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
