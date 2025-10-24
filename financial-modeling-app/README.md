# Synthetic Dividend Algorithm

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A sophisticated **rules-based investment strategy** that systematically generates cash flow from growth stocks while maintaining long-term compound exposure. The algorithm creates "synthetic dividends" through strategic profit-taking at all-time highs, solving the universal problem of generating distributions from growth portfolios without sacrificing appreciation potential.

## 🎯 What Problem Does This Solve?

Traditional growth portfolios face a fundamental dilemma:
- **Dividends alone** provide insufficient cash flow (typically 1-2% yields)
- **Forced selling** creates timing risk and tax inefficiencies
- **Rebalancing to fixed income** sacrifices growth potential

**The Synthetic Dividend Solution**:
- ✅ **Rules-based profit-taking** only at all-time highs (selling strength, never weakness)
- ✅ **Predictable cash generation** through formula-driven rebalancing
- ✅ **Growth preservation** via configurable profit-sharing ratios
- ✅ **No market timing required** - only unknown is WHEN ATHs occur, not IF

## 🚀 Key Features

### Core Algorithm
- **Automated rebalancing** triggered by price movements exceeding configurable thresholds (5-25%)
- **Profit sharing ratios** from -100% to >100% for flexible position sizing
- **Buyback stack tracking** with FIFO unwinding for tax-efficient cost basis management
- **Bank balance tracking** for cash flow analysis and liquidity planning
- **Financial adjustments** using actual asset returns (VOO/BIL) for realistic opportunity cost calculations

### Analysis & Backtesting
- **Historical backtesting** with real market data via yfinance
- **Batch comparison** of multiple strategies across different parameters
- **Performance metrics**: Total return, Sharpe ratio, max drawdown, transaction counts
- **Visualization** with matplotlib-based charts and performance tables
- **Comprehensive test suite** with 20 unit tests covering edge cases

### Command-Line Interface
```bash
# Run single strategy backtest
python -m src.run_model NVDA 2024-01-01 2025-01-01 sd-7.5,50 --qty 10000

# Compare multiple strategies
python -m src.compare.batch_comparison NVDA 2024-01-01 2025-01-01 results.csv

# Interactive GUI (Tkinter-based)
python src/main.py
```

## 📊 Example Results (NVDA 10/22/2024 - 10/22/2025)

| Strategy | Return | Max Drawdown | Transactions | Bank Avg |
|----------|--------|--------------|--------------|----------|
| Buy-and-Hold | 29.05% | -27.50% | 0 | $0 |
| SD 7.5,50 | **31.41%** | -25.84% | 67 | -$77.6K |
| SD 7.5,100 | 34.14% | -23.72% | 67 | -$262.2K |
| SD 25,50 | 30.14% | -27.03% | 23 | -$54.8K |

The algorithm **outperforms buy-and-hold** while providing systematic cash flow and reduced drawdowns.

## 🏗️ Project Structure

```
financial-modeling-app/
├── src/
│   ├── main.py                    # GUI entry point
│   ├── run_model.py              # CLI for single backtests
│   ├── data/
│   │   └── fetcher.py            # Yahoo Finance data retrieval
│   ├── models/
│   │   ├── stock.py              # Core stock model with rebalancing
│   │   └── backtest.py           # Backtesting engine
│   ├── compare/
│   │   ├── batch_comparison.py   # Multi-strategy comparison
│   │   ├── plotter.py            # Visualization
│   │   ├── runner.py             # Parallel backtest execution
│   │   └── table.py              # Results formatting
│   ├── gui/
│   │   └── layout.py             # Tkinter GUI layout
│   └── utils/
│       └── date_utils.py         # Date parsing utilities
├── tests/
│   ├── test_buyback_stack.py     # FIFO unwinding tests
│   └── test_synthetic_dividend.py # Core algorithm tests
├── CODING_PHILOSOPHY.md          # Code quality guidelines
├── INVESTING_THEORY.md           # Strategy theory and analysis
├── TODO.md                       # Development roadmap
├── requirements.txt              # Production dependencies
└── requirements-dev.txt          # Development tools
```

## 🛠️ Setup Instructions

### Prerequisites
- Python 3.11 or higher
- pip package manager
- Virtual environment (recommended)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/ricksladkey/synthetic-dividend.git
   cd synthetic-dividend/financial-modeling-app
   ```

2. **Create and activate virtual environment**:
   ```bash
   # Windows PowerShell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   
   # Linux/Mac
   python -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   
   # For development (includes testing/linting tools)
   pip install -r requirements-dev.txt
   ```

4. **Run tests** (optional):
   ```bash
   pytest tests/ -v
   ```

## 📖 Quick Start Guide

### Run a Single Backtest

```bash
python -m src.run_model NVDA 2024-01-01 2025-01-01 sd-7.5,50 \
    --qty 10000 \
    --reference-asset VOO \
    --risk-free-asset BIL
```

**Output**: Detailed performance metrics, transaction history, and bank balance statistics.

### Compare Multiple Strategies

```bash
python -m src.compare.batch_comparison NVDA 2024-01-01 2025-01-01 results.csv
```

**Output**: CSV file with comparative performance metrics and optional matplotlib charts.

### Launch GUI

```bash
python src/main.py
```

**Features**: Interactive data entry, strategy selection, and visual results display.

## 🎓 Strategy Configuration

### Rebalancing Triggers
- **5-7.5%**: Aggressive volatility harvesting, higher transaction costs
- **9.05%**: Balanced approach (default in many examples)
- **15-25%**: Conservative trading, lower transaction frequency

### Profit Sharing Ratios
- **-25% to 0%**: Accumulation mode - buy more on strength
- **25-50%**: Balanced growth and distributions
- **50%**: Sweet spot - maintains position growth while generating cash
- **75-100%**: Maximum distributions, position plateaus
- **>100%**: De-risking mode - systematically reduce position

See [INVESTING_THEORY.md](INVESTING_THEORY.md) for detailed analysis of these parameters.

## 🧪 Testing & Code Quality

This project maintains high code quality standards:

- ✅ **pytest** test suite with 20 tests (14 passing, 6 xfail with documented bugs)
- ✅ **mypy** type checking (100% clean)
- ✅ **flake8** linting (0 warnings)
- ✅ **black** code formatting (100 char line length)
- ✅ **isort** import organization

See [CODING_PHILOSOPHY.md](CODING_PHILOSOPHY.md) for development guidelines.

## 📚 Documentation

- **[INVESTING_THEORY.md](INVESTING_THEORY.md)** - Comprehensive explanation of the investment strategy, profit-sharing theory, and financial adjustments
- **[CODING_PHILOSOPHY.md](CODING_PHILOSOPHY.md)** - Code quality standards, functional programming principles, and development practices
- **[TODO.md](TODO.md)** - Development roadmap and planned features

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Follow the code quality guidelines in CODING_PHILOSOPHY.md
4. Run tests and linting (`pytest`, `mypy`, `flake8`, `black`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Market data provided by [yfinance](https://github.com/ranaroussi/yfinance)
- Inspired by the need for systematic cash flow from growth portfolios
- Built with Python, NumPy, Pandas, and Matplotlib

## 📧 Contact

Rick Sladkey - [@ricksladkey](https://github.com/ricksladkey)

Project Link: [https://github.com/ricksladkey/synthetic-dividend](https://github.com/ricksladkey/synthetic-dividend)

---

**Disclaimer**: This software is for educational and research purposes only. Past performance does not guarantee future results. Always consult with a qualified financial advisor before making investment decisions.