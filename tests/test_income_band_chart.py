"""
Test: Income Band Chart Visualization

Tests the income band chart functionality to ensure it works correctly
with synthetic portfolio data.
"""

import os

# Add src to path for imports
import sys
import tempfile
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from visualization.income_band_chart import (  # noqa: E402
    create_sample_income_data,
    get_asset_color,
    plot_income_bands,
)


class TestIncomeBandChart:
    """Test the income band chart functionality."""

    def test_get_asset_color(self):
        """Test asset color assignment."""
        assert get_asset_color("NVDA") == "#1f77b4"  # Blue for NVDA
        assert get_asset_color("SPY") == "#74c476"  # Green for SPY
        assert get_asset_color("expenses") == "#d62728"  # Red for expenses
        assert get_asset_color("cash") == "#2ca02c"  # Green for cash
        assert get_asset_color("UNKNOWN") == "#7f7f7f"  # Default gray

    def test_create_sample_income_data(self):
        """Test sample data creation."""
        df = create_sample_income_data()

        # Check structure
        assert isinstance(df, pd.DataFrame)
        assert isinstance(df.index, pd.DatetimeIndex)

        # Check required columns exist
        required_cols = ["NVDA", "SPY", "BTC", "GLD", "expenses", "cash"]
        for col in required_cols:
            assert col in df.columns

        # Check data is non-negative
        assert (df >= 0).all().all()

        # Check expenses are constant (as designed)
        assert df["expenses"].nunique() == 1

    def test_plot_income_bands_basic(self):
        """Test basic band chart plotting."""
        df = create_sample_income_data()

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            output_file = tmp.name

        try:
            result = plot_income_bands(
                income_data=df,
                title="Test Income Bands",
                output_file=output_file,
                show_legend=False,  # Avoid display issues in tests
            )

            assert result == output_file
            assert os.path.exists(output_file)
            assert os.path.getsize(output_file) > 0  # File has content

        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_plot_income_bands_display_only(self):
        """Test plotting without saving to file."""
        # Skip in headless environments
        try:
            import matplotlib

            matplotlib.use("Agg")  # Use non-interactive backend
        except ImportError:
            pytest.skip("matplotlib not available")

        df = create_sample_income_data()

        result = plot_income_bands(
            income_data=df, title="Test Display Only", output_file=None, show_legend=False
        )

        assert result == "displayed"

    def test_plot_income_bands_custom_colors(self):
        """Test custom styling options."""
        df = create_sample_income_data()

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            output_file = tmp.name

        try:
            result = plot_income_bands(
                income_data=df,
                title="Custom Styled Chart",
                output_file=output_file,
                figsize=(12, 8),
                alpha=0.5,
                show_legend=True,
            )

            assert result == output_file
            assert os.path.exists(output_file)

        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_empty_dataframe_error(self):
        """Test error handling for empty data."""
        empty_df = pd.DataFrame()

        with pytest.raises(ValueError, match="income_data DataFrame is empty"):
            plot_income_bands(empty_df, "Test")

    def test_invalid_date_index_error(self):
        """Test error handling for non-datetime index."""
        df = pd.DataFrame(
            {"NVDA": [100, 200], "expenses": [50, 50], "cash": [1000, 1000]},
            index=["date1", "date2"],
        )

        with pytest.raises(ValueError, match="Could not convert index to datetime"):
            plot_income_bands(df, "Test")

    def test_demo_functionality(self):
        """Test that the demo function runs without errors."""
        # Skip in headless environments
        try:
            import matplotlib

            matplotlib.use("Agg")  # Use non-interactive backend
        except ImportError:
            pytest.skip("matplotlib not available")

        from visualization.income_band_chart import demo_income_bands  # noqa: E402

        # This should run without throwing exceptions
        # (it will create a demo file)
        demo_income_bands()

        # Check if demo file was created
        demo_file = "demo_income_bands.png"
        if os.path.exists(demo_file):
            assert os.path.getsize(demo_file) > 0
            os.unlink(demo_file)  # Clean up


if __name__ == "__main__":
    pytest.main([__file__])
