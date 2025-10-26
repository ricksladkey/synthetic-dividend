# Examples

Example scripts and demonstrations for the Synthetic Dividend project.

## Contents

- **`demo_dividends.py`** - Real dividend income demo with AAPL backtest
  - Shows how dividend payments are automatically credited to bank
  - Demonstrates integration of real + synthetic income
  - Example output and metrics

## Running Examples

### Dividend Integration Demo
```bash
python examples/demo_dividends.py
```

This demo fetches real AAPL price and dividend data for 2024, runs a backtest with the synthetic dividend algorithm, and shows how real dividends improve coverage ratios.

## Quick Links

- [Main README](../README.md)
- [Full Examples Guide](../docs/EXAMPLES.md)
- [Theory Documentation](../theory/README.md)
- [Installation](../INSTALLATION.md)

## Adding New Examples

When adding new examples:
1. Create a new Python file in this directory
2. Add clear docstring explaining what it demonstrates
3. Update this README with description and usage
4. Add to [docs/EXAMPLES.md](../docs/EXAMPLES.md) if it's a key use case
