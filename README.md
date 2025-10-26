<div align="center">

# 💰 Synthetic Dividend Algorithm

### *Transform Volatility Into Cash Flow*

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![| 💰 **[INCOME_GENERATION.md### ✅ Completed (Phase 1-2)
- [x] Core synthetic dividend algorithm with buyback stack
- [x] Optimal rebalancing parameter research (48 backtests)
- [x] Volatility alpha discovery and measurement
- [x] CLI tools for backtesting and batch analysis
- [x] Comprehensive test suite with 48 tests (100% passing)
- [x] Withdrawal policy implementation (orthogonal to strategy)
- [x] Dual bank management modes (simple vs strict)
- [x] Price normalization for deterministic backtests
- [x] Income generation framework and theory documentation
- [x] Income smoothing theory (irregular → regular transformation)
- [x] Dividend/interest income tracking (real + synthetic dividends)
- [x] Volatility alpha analyzer tool (auto-suggest SD parameters)

### 🔄 In Progress (Phase 3)ME_GENERATION.md)** | How volatility becomes cash flow - the core income mechanism, practical implementation guide |
| 🔄 **[INCOME_SMOOTHING.md](theory/INCOME_SMOOTHING.md)** | Irregular → regular payment transformation, sequence-of-returns protection, never sell at loss principle |
| 🏦 **[WITHDRAWAL_POLICY.md](theory/WITHDRAWAL_POLICY.md)** | Orthogonal withdrawal dimension, bank-first approach, 4% rule with CPI adjustment |
| 💻 **[CODING_PHILOSOPHY.md](theory/CODING_PHILOSOPHY.md)** | Code quality standards, functional programming principles, and development best practices |
| 📚 **[theory/README.md](theory/README.md)** | Complete theoretical framework overview and system prompt usage guide |
| 🤝 **[CONTRIBUTORS.md](CONTRIBUTORS.md)** | Who built this and how - the human-AI collaboration story |
| 🚀 **[CODING_ASSISTANCE_MANIFESTO.md](CODING_ASSISTANCE_MANIFESTO.md)** | ⭐ Lessons on AI-assisted development, the "pays for itself" productivity gain |
| 📋 **[TODO.md](TODO.md)** | Development roadmap, completed features, and future plans |

[![Tests](https://img.shields.io/badge/tests-48%20passing-brightgreen.svg)](./tests)

**A rules-based investment strategy that systematically generates cash flow from growth stocks while preserving compound growth potential.**

[🚀 Quick Start](#-quick-start-guide) • [📊 Research Findings](#-research-findings) • [� Examples](EXAMPLES.md) • [�📖 Documentation](#-documentation) • [🤝 Contributing](#-contributing)

---

</div>

## 💡 The Innovation

The Synthetic Dividend Algorithm solves a fundamental problem in portfolio management: **How do you generate cash flow from growth stocks without sacrificing long-term returns?**

Traditional approaches fail:
- 🔴 **Dividend stocks** - Low yields (1-2%), slower growth
- 🔴 **Forced selling** - Sequence-of-returns risk, tax inefficiency  
- 🔴 **Bonds/Fixed income** - Sacrifice growth potential

**Our solution**:
- ✅ **Strategic profit-taking** - Only sell at all-time highs (never weakness)
- ✅ **Volatility harvesting** - Buybacks during dips amplify returns
- ✅ **Income smoothing** - Convert irregular volatility profits into regular income
- ✅ **Sequence-of-returns protection** - Bank buffer avoids forced sales in bear markets
- ✅ **Configurable distributions** - Flexible profit-sharing ratios (0-100%+)
- ✅ **Rules-based execution** - No market timing, just mathematics

> 💎 **Key Insight**: Irregular payments (from market volatility) → Regular income (for lifestyle needs) through temporal buffering.

## 🔬 How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│  Stock Price Over Time                                          │
│                                                                 │
│   ATH! 💰 SELL                                                  │
│    ↑                            ATH! 💰 SELL                    │
│    │        ↗ BUY 📈              ↑                             │
│    │      ↙ (dip)                 │      ↗ BUY 📈              │
│    │    ↗                         │    ↙ (dip)                 │
│    │  ↙                           │  ↗                         │
│    ↗                              ↗                            │
│                                                                 │
│  Two Revenue Sources:                                           │
│  1️⃣ Primary Dividends: Sell fractions at new all-time highs   │
│  2️⃣ Secondary Dividends: Buy low, sell high during volatility │
└─────────────────────────────────────────────────────────────────┘
```

**The Algorithm in 3 Steps:**

1. **🎯 Set Rebalancing Threshold** - Choose trigger (e.g., 9.05% = 8th root of 2)
2. **💰 Configure Profit Sharing** - Decide cash vs. growth (e.g., 50% = balanced)
3. **⚙️ Let Mathematics Work** - Automatic execution at all-time highs + buybacks

**Example**: With 9.05% threshold and 50% profit sharing:
- Price rises 9.05% to new ATH → Sell 50% of the profit
- Price falls 8.3% from last transaction → Buy back shares
- Net result: Cash flow + increased share count from volatility

## 📊 Research Findings

### Phase 1: Optimal Rebalancing Parameters (1-Year Backtest)

We tested **48 configurations** across 12 assets (Oct 2023 - Oct 2024):

| Asset Class | Best Performer | Rebalancing | 1-Year Return | Transactions |
|-------------|----------------|-------------|---------------|--------------|
| 🚀 **Crypto** | BTC-USD | sd4 (18.92%) | 152.18% | 32 |
| 💻 **Tech Growth** | NVDA | sd8 (9.05%) | 174.59% | 38 |
| 📈 **Tech Giants** | GOOG | sd6 (12.25%) | 34.82% | 17 |
| 🥇 **Commodities** | GLD | sd8 (9.05%) | 43.78% | 21 |
| 📊 **Indices** | QQQ | sd10 (7.18%) | 35.67% | 28 |

**Key Findings**:
- ✅ Higher volatility assets benefit from **tighter triggers** (sd4-sd8)
- ✅ Lower volatility assets prefer **wider triggers** (sd10-sd16)
- ✅ Optimal threshold correlates with asset volatility profile

### Volatility Alpha Discovery

**Groundbreaking insight**: Buyback-enhanced strategies can generate **extra returns beyond ATH-only selling**.

**Example - NVDA (Oct 2023 - Oct 2024)**:
```
Enhanced Strategy (sd8 + buybacks):  174.59% return, 38 transactions
ATH-Only (sd8, no buybacks):         165.00% return, 14 transactions
────────────────────────────────────────────────────────────────
Volatility Alpha:                     +9.59% extra profit
Alpha Per Transaction:                +0.25% per buyback cycle
```

**The "Volatility Alpha" Thesis**: 
> Buybacks during drawdowns create "secondary synthetic dividends" by rewinding the clock on previous sales, enabling resales at higher prices. This transforms volatility from risk into opportunity.

📄 **[Read the full thesis →](VOLATILITY_ALPHA_THESIS.md)**

## 🚀 Key Features

<table>
<tr>
<td width="50%">

### 🎯 Core Algorithm
- ⚡ **Automated rebalancing** via exponential thresholds (2^(1/N) scaling)
- 💸 **Flexible profit sharing** (-100% to >100% for any strategy)
- 📚 **FIFO buyback stack** for tax-efficient cost basis tracking
- 💰 **Bank balance tracking** for cash flow analysis
- 💵 **Real dividend/interest income** (AAPL, BIL, etc.) credited to bank
- 🏦 **Dual bank modes** (simple: allow margin, strict: never negative)
- � **Withdrawal policy** (4% rule with CPI adjustment, orthogonal to strategy)
- 📊 **Financial adjustments** using real market benchmarks (VOO/BIL)

</td>
<td width="50%">

### 🔬 Research Tools
- 📈 **Historical backtesting** with yfinance market data
- 📥 **Dividend/interest tracking** (cached locally for fast access)
- 🔄 **Batch comparison** across multiple parameters
- 📉 **Performance metrics** (Sharpe, drawdown, alpha, coverage ratio)
- 🎨 **Visualization** with matplotlib charts
- ✅ **48-test suite** covering edge cases, margin modes, withdrawals, dividends

</td>
</tr>
</table>

### 💻 Command-Line Interface

```bash
# Recommended: Volatility Alpha Analyzer (auto-suggests SD parameter)
analyze-volatility-alpha.bat GLD 10/26/2024 10/26/2025
analyze-volatility-alpha.bat NVDA 10/23/2023 10/23/2024

# Single backtest with detailed output
python -m src.run_model NVDA 10/23/2023 10/23/2024 sd8 --qty 10000

# Batch research across 12 assets, 4 rebalancing triggers
python -m src.research.optimal_rebalancing --comprehensive --output results.csv

# Dividend tracking demo
python demo_dividends.py
```

**💡 New Feature**: The **Volatility Alpha Analyzer** automatically:
1. Calculates historical volatility
2. Suggests optimal SD parameter (e.g., SD16 for low-vol GLD, SD6 for high-vol NVDA)
3. Compares full strategy vs ATH-only
4. Reports volatility alpha (secondary synthetic dividends)

See [**EXAMPLES.md**](EXAMPLES.md) for comprehensive usage guide!

## 🎯 Live Example: NVDA Bull Run (Oct 2024 - Oct 2025)

| Strategy | Total Return | Max Drawdown | Transactions | Cash Generated |
|----------|--------------|--------------|--------------|----------------|
| 💤 Buy-and-Hold | 29.05% | -27.50% | 0 | $0 |
| 💰 **SD 7.5,50** | **31.41%** ⬆️ | -25.84% ✅ | 67 | $77.6K |
| 💸 SD 7.5,100 | 34.14% ⬆️ | -23.72% ✅ | 67 | $262.2K |
| 🎯 SD 25,50 | 30.14% ⬆️ | -27.03% ✅ | 23 | $54.8K |

**Key Takeaways**:
- ✅ **Outperforms buy-and-hold** by 2.36% while generating $77K cash
- ✅ **Reduced drawdown** from -27.5% to -25.84% (smoother ride)
- ✅ **Systematic distributions** without sacrificing growth
- ⚡ **67 transactions** automated by rules, zero emotional decisions

## 🏗️ Project Structure

```
synthetic-dividend/
├── 📊 src/
│   ├── main.py                         # GUI entry point
│   ├── run_model.py                    # CLI for single backtests
│   │
│   ├── 📡 data/
│   │   └── fetcher.py                  # Yahoo Finance integration
│   │
│   ├── 🧮 models/
│   │   ├── stock.py                    # Position tracking & P/L
│   │   └── backtest.py                 # Algorithm engine (800+ lines)
│   │
│   ├── 🔬 research/
│   │   ├── optimal_rebalancing.py      # Phase 1: Parameter optimization
│   │   └── volatility_alpha.py         # Phase 1b: Enhanced vs ATH-only
│   │
│   ├── 🛠️ tools/
│   │   └── order_calculator.py         # Manual trading order calculator
│   │
│   ├── 📊 compare/
│   │   ├── batch_comparison.py         # Multi-strategy analysis
│   │   ├── plotter.py                  # Matplotlib visualizations
│   │   ├── runner.py                   # Parallel execution
│   │   └── table.py                    # Results formatting
│   │
│   ├── 🖥️ gui/
│   │   └── layout.py                   # Tkinter interface
│   │
│   └── 🛠️ utils/
│       └── date_utils.py               # Date parsing utilities
│
├── 🧪 tests/
│   ├── test_buyback_stack.py           # FIFO unwinding validation
│   ├── test_synthetic_dividend.py      # Core algorithm tests
│   └── test_volatility_alpha_synthetic.py  # Synthetic data tests
│
├── 📚 Documentation/
│   ├── README.md                       # You are here! 👋
│   ├── CODING_PHILOSOPHY.md            # Code quality standards
│   ├── INVESTING_THEORY.md             # Strategy deep dive
│   ├── VOLATILITY_ALPHA_THESIS.md      # Buyback enhancement theory
│   └── TODO.md                         # Development roadmap
│
└── ⚙️ Configuration/
    ├── requirements.txt                # Production dependencies
    └── requirements-dev.txt            # Development tools (pytest, mypy, black)
```

## � Quick Start Guide

### 🎬 Installation

```bash
# 1. Clone the repository
git clone https://github.com/ricksladkey/synthetic-dividend.git
cd synthetic-dividend

# 2. Create virtual environment (Windows PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Verify installation (optional)
python -m pytest tests/ -v
```

<details>
<summary>🐧 <b>Linux/Mac Installation</b></summary>

```bash
# Step 2 for Linux/Mac
python -m venv .venv
source .venv/bin/activate

# Steps 3-4 are identical
```
</details>

### � Your First Backtest

**Run NVDA with optimal settings (sd8, 50% profit sharing):**

```bash
python -m src.run_model NVDA 10/23/2023 10/23/2024 sd8 --qty 10000
```

**Output**:
```
📊 Backtest Results: NVDA (2023-10-23 to 2024-10-23)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Strategy: sd8 (9.05% trigger, 50% profit sharing)
Initial Investment: $450,500.00 (10,000 shares @ $45.05)

💰 Final Results:
   Holdings: 4,246 shares @ $119.62 = $507,865.52
   Bank: $729,433.76
   Total: $1,237,299.28
   
📈 Performance:
   Total Return: 174.59%
   Transactions: 38
   Volatility Alpha: 9.59% vs ATH-only

✅ OUTPERFORMED buy-and-hold by 25.46%!
```

### 🧮 Calculate Orders for Manual Trading

**For live trading**: Calculate exact limit orders to place in your broker:

```bash
# Calculate buy/sell orders based on current position
python -m src.tools.order_calculator \
    --ticker NVDA \
    --holdings 1000 \
    --last-price 120.50 \
    --current-price 125.30 \
    --sdn 8 \
    --profit 50
```

**Output** (ready to copy/paste into your broker):
```
╔══════════════════════════════════════════════════════════════╗
║           SYNTHETIC DIVIDEND ORDER CALCULATOR                ║
╚══════════════════════════════════════════════════════════════╝

📊 CURRENT POSITION - NVDA
  Holdings:         1,000 shares
  Last Transaction: $120.50
  Current Price:    $125.30
  
🎯 LIMIT ORDERS TO PLACE

  BUY  NVDA     45 @ $110.50  (LIMIT GTC)
  SELL NVDA     41 @ $131.41  (LIMIT GTC)

💡 TIP: Set both orders as GTC, cancel and replace when either executes
```

**Quick shortcut** (Windows):
```bash
.\calc-orders.bat NVDA 1000 120.50 125.30 8 50
```

### 🔬 Run Research Analysis

**Phase 1: Find optimal rebalancing for all assets:**

```bash
# Quick test (1 asset, 4 triggers, ~2 min)
python -m src.research.optimal_rebalancing --ticker NVDA --quick

# Comprehensive (12 assets, 4 triggers each = 48 backtests, ~40 min)
python -m src.research.optimal_rebalancing --comprehensive --output results.csv
```

**Phase 1b: Measure volatility alpha:**

```bash
python -m src.research.volatility_alpha --ticker NVDA \
    --start 10/23/2023 --end 10/23/2024 --output volatility_alpha.csv
```

## ⚙️ Strategy Configuration Guide

### 📐 Rebalancing Triggers (sdN format)

The `sdN` format uses **exponential scaling** based on the Nth root of 2:

| Format | Trigger % | Description | Best For |
|--------|-----------|-------------|----------|
| `sd4` | 18.92% | Aggressive | High volatility (BTC, MSTR) |
| `sd6` | 12.25% | Moderate-Aggressive | Growth stocks (GOOG, MSTR) |
| `sd8` | 9.05% | Balanced | Tech stocks (NVDA, PLTR) |
| `sd10` | 7.18% | Moderate-Conservative | Indices (QQQ, SPY) |
| `sd12` | 5.95% | Conservative | Low volatility (GLD, SLV) |
| `sd16` | 4.43% | Very Conservative | Stable assets (DIA) |

**Formula**: `trigger_pct = (2^(1/N) - 1) × 100`

**Choosing your trigger**:
- 🔥 **Higher volatility** → Lower N (sd4-sd6) → Wider triggers
- 📊 **Lower volatility** → Higher N (sd10-sd16) → Tighter triggers
- 🎯 **Sweet spot**: sd8 works well for most growth stocks

### 💰 Profit Sharing Ratios

Controls the balance between **cash flow** and **position growth**:

| Ratio | Strategy | Effect | Use Case |
|-------|----------|--------|----------|
| **-25% to 0%** | 📈 Accumulation | Buy MORE on strength | Building position |
| **25% to 50%** | ⚖️ Balanced | Half cash, half growth | Most investors |
| **50%** | 🎯 **Sweet Spot** | Perfect balance | Recommended default |
| **75% to 100%** | 💸 Distribution | Maximum cash flow | Income focus |
| **>100%** | 🛡️ De-risking | Reduce position | Risk management |

**Example**: `sd8,75` = 9.05% trigger with 75% profit sharing (high distributions)

### 🎨 Custom Configurations

```bash
# Format: sd-<trigger_pct>,<profit_pct>
python -m src.run_model NVDA 10/23/2023 10/23/2024 sd-7.5,50 --qty 10000

# ATH-only mode (no buybacks)
python -m src.run_model NVDA 10/23/2023 10/23/2024 sd-ath-only-9.05,50 --qty 10000
```

📖 **[Deep dive into strategy theory →](INVESTING_THEORY.md)**

## 🧪 Testing & Code Quality

This project maintains **rigorous engineering standards**:

| Tool | Status | Coverage |
|------|--------|----------|
| ✅ **pytest** | 44 tests | Core algorithm, buyback stack, margin modes, withdrawals, edge cases |
| ✅ **mypy** | Type checking | 100% clean, strict mode |
| ✅ **flake8** | Linting | 0 warnings |
| ✅ **black** | Formatting | 100 char lines, consistent style |
| ✅ **isort** | Import sorting | Organized, deterministic |

### 🧬 Test Coverage

```bash
# Run all tests
pytest tests/ -v

# Run specific test suite
pytest tests/test_synthetic_dividend.py -v
pytest tests/test_margin_modes.py -v  # New: Bank management modes

# Run with coverage report
pytest --cov=src tests/
```

**Test Categories**:
- 🔧 **Unit tests**: Algorithm logic, FIFO stack, profit calculations
- 📊 **Integration tests**: Full backtests with synthetic data
- 🎯 **Edge cases**: 0% profit sharing, 100% profit sharing, gap scenarios
- 🏦 **Bank modes**: Margin vs strict mode, withdrawal coverage
- 💵 **Withdrawal policy**: 4% rule, CPI adjustment, bank-first approach

### 📏 Code Quality

```bash
# Type checking
mypy src/

# Linting
flake8 src/ tests/

# Auto-formatting
black src/ tests/
isort src/ tests/
```

📖 **[Read coding philosophy →](CODING_PHILOSOPHY.md)**

## 📚 Documentation

| Document | Description |
|----------|-------------|
| 📖 **[INVESTING_THEORY.md](theory/INVESTING_THEORY.md)** | Comprehensive investment strategy explanation, profit-sharing mathematics, and financial adjustment theory |
| 💎 **[VOLATILITY_ALPHA_THESIS.md](theory/VOLATILITY_ALPHA_THESIS.md)** | How buybacks during drawdowns create extra returns beyond ATH-only selling |
| 💰 **[INCOME_GENERATION.md](theory/INCOME_GENERATION.md)** | How volatility becomes cash flow - the core income mechanism, practical implementation guide |
| � **[INCOME_SMOOTHING.md](theory/INCOME_SMOOTHING.md)** | ⭐ NEW: Irregular → regular payment transformation, sequence-of-returns protection, never sell at loss principle |
| 🏦 **[WITHDRAWAL_POLICY.md](theory/WITHDRAWAL_POLICY.md)** | Orthogonal withdrawal dimension, bank-first approach, 4% rule with CPI adjustment |
| �💻 **[CODING_PHILOSOPHY.md](theory/CODING_PHILOSOPHY.md)** | Code quality standards, functional programming principles, and development best practices |
| 📚 **[theory/README.md](theory/README.md)** | Complete theoretical framework overview and system prompt usage guide |
| 📋 **[TODO.md](TODO.md)** | Development roadmap, completed features, and future plans |
| 🎓 **[EXAMPLES.md](EXAMPLES.md)** | ⭐ **Comprehensive usage guide** - command examples, real-world scenarios, volatility analyzer walkthrough |

## 🗺️ Roadmap

### ✅ Completed (Phase 1-2)
- [x] Core synthetic dividend algorithm with buyback stack
- [x] Optimal rebalancing parameter research (48 backtests)
- [x] Volatility alpha discovery and measurement
- [x] CLI tools for backtesting and batch analysis
- [x] Comprehensive test suite with 44 tests (100% passing)
- [x] Withdrawal policy implementation (orthogonal to strategy)
- [x] Dual bank management modes (simple vs strict)
- [x] Price normalization for deterministic backtests
- [x] Income generation framework and theory documentation
- [x] Income smoothing theory (irregular → regular transformation)

### � In Progress (Phase 3)
- [ ] Multi-asset portfolio experiments (diversification benefits)
- [ ] Sequence-of-returns Monte Carlo validation
- [ ] Coverage ratio optimization research
- [ ] Income calculator tool for retirement planning

### 🔮 Planned (Phase 4+)
- [ ] Portfolio-level optimization (multi-asset allocation)
- [ ] Dynamic withdrawal rate adjustments
- [ ] Tax optimization strategies (lot selection, loss harvesting)
- [ ] Web dashboard for interactive analysis
- [ ] Real-time trading integration (paper trading)

📋 **[See full roadmap →](TODO.md)**

## 🤝 Contributing

Contributions are welcome! This project values **rigorous engineering** and **mathematical precision**.

### How to Contribute

1. 🍴 **Fork the repository**
2. 🌿 **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. 📝 **Follow code quality standards** (see [CODING_PHILOSOPHY.md](CODING_PHILOSOPHY.md))
4. ✅ **Run the full test suite** (`pytest tests/ -v`)
5. 🎨 **Run linting and formatting** (`mypy src/`, `flake8 src/`, `black src/`)
6. 💬 **Commit with descriptive messages** (`git commit -m 'Add amazing feature'`)
7. 📤 **Push to your branch** (`git push origin feature/amazing-feature`)
8. 🔄 **Open a Pull Request** with detailed description

### Areas Where We Need Help

- � **Debug volatility alpha test failures** - Help investigate negative alpha in synthetic scenarios
- 📊 **Statistical analysis** - Add Sharpe ratio, drawdown calculations, significance testing
- 🎨 **Visualizations** - Create interactive dashboards with Plotly or Streamlit
- 📚 **Documentation** - Improve docstrings, add tutorials, create video walkthroughs
- 🧪 **Testing** - Expand test coverage, add integration tests, stress testing

### Code Quality Requirements

All contributions must pass:
- ✅ Type checking with `mypy --strict`
- ✅ Linting with `flake8` (0 warnings)
- ✅ Formatting with `black` (100 char lines)
- ✅ All existing tests (`pytest tests/`)
- ✅ New tests for new features (maintain >80% coverage)

---

## 📜 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

**TL;DR**: Free to use, modify, and distribute. No warranty. Attribution appreciated.

---

## 🙏 Acknowledgments

- 📈 **Market data** provided by [yfinance](https://github.com/ranaroussi/yfinance) (Yahoo Finance API)
- 🐍 **Built with** Python, NumPy, Pandas, and Matplotlib
- 🤖 **Proudly developed in collaboration with AI** - See [CONTRIBUTORS.md](CONTRIBUTORS.md) for the full story
- 💡 **Inspired by** the need for systematic cash flow from growth portfolios
- 🎓 **Mathematical foundation** based on exponential rebalancing theory (2^(1/N) scaling)
- 🔬 **Research methodology** influenced by systematic trading and quantitative finance principles

This project represents a groundbreaking collaboration between human expertise and artificial intelligence, demonstrating the transformative potential of AI-assisted software development. Read the full collaboration story in [CONTRIBUTORS.md](CONTRIBUTORS.md).

Special thanks to the open-source community for excellent tools that made this project possible.

---

## 📧 Contact & Links

**Author**: Rick Sladkey  
**GitHub**: [@ricksladkey](https://github.com/ricksladkey)  
**Project**: [synthetic-dividend](https://github.com/ricksladkey/synthetic-dividend)

### 🔗 Quick Links

- 📖 [Full Documentation](theory/README.md)
- 💎 [Volatility Alpha Thesis](theory/VOLATILITY_ALPHA_THESIS.md)
- 🤝 [Contributors & Collaboration Story](CONTRIBUTORS.md)
- � [AI-Assisted Development Manifesto](CODING_ASSISTANCE_MANIFESTO.md)
- �🐛 [Issue Tracker](https://github.com/ricksladkey/synthetic-dividend/issues)
- 💬 [Discussions](https://github.com/ricksladkey/synthetic-dividend/discussions)

---

<div align="center">

### ⚠️ Important Disclaimer

**This software is for educational and research purposes only.**

- 📚 Not financial advice
- 🔬 No guarantees of future performance
- 💼 Always consult a qualified financial advisor
- ⚖️ Past performance ≠ future results

**Use at your own risk. The authors assume no liability for financial decisions made based on this software.**

**About This Project**: Proudly developed through human-AI collaboration. See [CONTRIBUTORS.md](CONTRIBUTORS.md) for the fascinating story of how this project became a case study in AI-assisted software development.

---

<sub>Made with ❤️, Python, and AI collaboration | © 2024-2025 Rick Sladkey | MIT License</sub>

</div>