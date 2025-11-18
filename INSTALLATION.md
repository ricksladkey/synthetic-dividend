# Installation Guide

## Quick Start

### Prerequisites

- **Python 3.11 or 3.12** (required)
- **pip** (usually comes with Python)
- **Virtual environment** (recommended)

### Basic Installation

```bash
# Clone the repository
git clone https://github.com/ricksladkey/synthetic-dividend.git
cd synthetic-dividend

# Create and activate virtual environment
python -m venv .venv

# Activate on Windows
.\.venv\Scripts\Activate.ps1

# Activate on Unix/Linux/macOS
source .venv/bin/activate

# Install core package in development mode
pip install -e .
```

**After installation**, these commands are available:
- `sd` - Main CLI entry point
- `sd-compare` - Batch strategy comparison
- `sd-research` - Optimal rebalancing research
- `sd-volatility-alpha` - Volatility alpha analysis
- `sd-calc-orders` - Order calculator GUI
- `sd-plotter` - Result visualization

---

## Installation Options

All dependencies are managed through `pyproject.toml` (modern Python standard). Choose the installation that fits your needs:

### 1. Core Package Only

For running backtests and analysis:

```bash
pip install -e .
```

**Includes**:
- pandas, matplotlib, yfinance
- pandas-datareader, lxml (data sources)
- simpy (simulation framework)

### 2. Development Installation

For contributing, testing, and code quality:

```bash
pip install -e ".[dev]"
```

**Includes** core package plus:
- **Testing**: pytest, pytest-cov, pytest-xdist (parallel execution)
- **Type checking**: mypy
- **Linting**: flake8, pylint
- **Formatting**: black, isort

### 3. GUI Installation

For using the interactive order calculator:

```bash
pip install -e ".[gui]"
```

**Includes** core package plus:
- **markdown** - Rendering help documentation
- **tkinterweb** - HTML/Markdown widgets for tkinter
- **tkcalendar** - Date picker widgets

### 4. Complete Installation

Everything (recommended for developers):

```bash
pip install -e ".[all]"
```

**Includes**: All core, dev, and GUI dependencies.

---

## Development Workflow

### Using Make (Unix/Linux/macOS/WSL)

The Makefile provides convenient commands for all common tasks:

```bash
# See all available commands
make help

# Installation
make install # Core package only
make install-dev # With dev dependencies
make install-gui # With GUI dependencies
make install-all # Everything

# Testing
make test-checks # Fast tests only (CI mode)
make test-all # All tests including network tests
make test-parallel # Fast tests in parallel
make test-all-parallel # All tests in parallel
make test # Both test-checks and test-all

# Code Quality
make format # Auto-format with black and isort
make lint # Run all linters (black, isort, flake8, mypy)
make check # Format, lint, and test (full CI check)

# Build & Deploy
make clean # Remove build artifacts and cache
make build # Build distribution packages
make publish # Publish to PyPI
make examples # Re-generate all experiment data
```

### Using Python Directly (Cross-Platform)

```bash
# Run tests
python -m pytest -q # All tests
python -m pytest -q -m "not slow" # Fast tests only
python -m pytest -q -n auto # Parallel execution

# Format code
python -m black .
python -m isort .

# Type checking
python -m mypy --explicit-package-bases --exclude "src/research|src/charts" src

# Run linters
python -m flake8 src tests --max-line-length=100 --extend-ignore=E203,W503
```

### Using the CLI

```bash
# Run backtests
sd backtest NVDA 2024-01-01 2024-12-31 sd-4,50

# Analyze volatility alpha
sd analyze volatility-alpha --ticker NVDA --start 01/01/2024 --end 12/31/2024

# Launch order calculator GUI
sd-calc-orders
```

---

## Virtual Environment Management

### Creating a Virtual Environment

**Windows (PowerShell)**:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Unix/Linux/macOS**:
```bash
python -m venv .venv
source .venv/bin/activate
```

### Activation Best Practices

#### Option 1: VS Code Python Extension (Recommended)
1. Open Command Palette: `Ctrl+Shift+P` (Windows) or `Cmd+Shift+P` (Mac)
2. Type: "Python: Select Interpreter"
3. Choose: `.venv/Scripts/python.exe` (Windows) or `.venv/bin/python` (Unix)
4. All new terminals will auto-activate the virtual environment

#### Option 2: Manual Activation
Every time you open a new terminal, activate manually:
- **Windows**: `.\.venv\Scripts\Activate.ps1`
- **Unix**: `source .venv/bin/activate`

#### Option 3: PowerShell Profile (Windows)
Auto-activate when you `cd` into the project:
```powershell
# Edit your PowerShell profile
notepad $PROFILE

# Add this line:
if (Test-Path ".venv\Scripts\Activate.ps1") { .\.venv\Scripts\Activate.ps1 }

# Reload profile
. $PROFILE
```

---

## WSL Setup (Windows Users)

Windows Subsystem for Linux provides a better development experience:

### Benefits
- [OK] True Unix environment (bash, make, symlinks)
- [OK] Faster package installation
- [OK] Better Docker compatibility
- [OK] Consistent Git line endings
- [OK] No PowerShell execution policy issues

### Setup Steps

1. **Install WSL2**:
 ```powershell
 # Run in PowerShell as Administrator
 wsl --install -d Ubuntu-22.04
 # Restart computer
 ```

2. **Install VS Code WSL Extension**:
 - Install extension: `ms-vscode-remote.remote-wsl`
 - Click green icon (bottom-left) → "New WSL Window"

3. **Setup Python in WSL**:
 ```bash
 # In WSL terminal
 sudo apt update
 sudo apt install python3.11 python3.11-venv python3-pip make

 # Navigate to your Windows project
 cd /mnt/c/build/synthetic-dividend

 # Create virtual environment
 python3.11 -m venv .venv
 source .venv/bin/activate

 # Install with all dependencies
 make install-all
 ```

4. **File Access**:
 - Windows: `C:\build\synthetic-dividend`
 - WSL: `/mnt/c/build/synthetic-dividend`

---

## Building Distribution Packages

### Build Wheel and Source Distribution

```bash
# Install build tools (if not already installed)
pip install build twine

# Build packages
python -m build

# Or use Make
make build
```

This creates in `dist/`:
- `synthetic_dividend-0.1.0.tar.gz` (source distribution)
- `synthetic_dividend-0.1.0-py3-none-any.whl` (wheel)

### Install from Local Build

```bash
pip install dist/synthetic_dividend-0.1.0-py3-none-any.whl
```

---

## Publishing to PyPI

### Test Publishing (TestPyPI)

```bash
# Build packages
make build

# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ synthetic-dividend
```

### Production Publishing

```bash
# Build and publish
make publish

# Or manually:
python -m build
python -m twine upload dist/*
```

### Setup PyPI Credentials

Create `~/.pypirc`:
```ini
[pypi]
username = __token__
password = pypi-YOUR-API-TOKEN-HERE

[testpypi]
username = __token__
password = pypi-YOUR-TEST-API-TOKEN-HERE
```

---

## Dependency Management

### Modern Standard: pyproject.toml

All dependencies are defined in `pyproject.toml` following [PEP 621](https://peps.python.org/pep-0621/). This is the modern Python standard.

**Core dependencies**:
```toml
dependencies = [
 "pandas>=1.0",
 "matplotlib>=3.0",
 "yfinance>=0.2.0",
 "pandas-datareader>=0.10",
 "lxml>=4.9",
 "simpy>=4.0",
]
```

**Optional dependencies** (install with `pip install -e ".[group]"`):
```toml
[project.optional-dependencies]
dev = ["pytest>=7.0", "mypy>=1.0", "black>=23.0", ...]
gui = ["markdown>=3.4", "tkinterweb>=3.15", "tkcalendar>=1.6"]
all = [...] # Combines dev + gui
```

### No More requirements.txt Files

The old `requirements.txt` and `requirements-dev.txt` files have been **removed**. All dependency management is now in `pyproject.toml`.

**Migration guide**:
- [FAIL] Old: `pip install -r requirements.txt`
- [OK] New: `pip install -e .`

- [FAIL] Old: `pip install -r requirements-dev.txt`
- [OK] New: `pip install -e ".[dev]"`

### Viewing Installed Dependencies

```bash
# List all installed packages
pip list

# Show specific package details
pip show pandas

# Export current environment (for reproducibility)
pip freeze > current_env.txt
```

---

## Troubleshooting

### "Module not found" errors

**Problem**: Importing `src.models` fails.

**Solution**: Install in editable mode:
```bash
pip install -e .
```

### Tests running slowly

**Problem**: Tests take 60+ seconds.

**Solution**: Use parallel execution:
```bash
make test-parallel # Fast tests in parallel
make test-all-parallel # All tests in parallel
```

### Cache directory issues

**Problem**: Cache files created in wrong location.

**Solution**: The project uses centralized path management via `src/paths.py`. Cache always goes to `<project_root>/cache/` regardless of where you run commands from.

### PowerShell execution policy errors

**Problem**: Cannot run `.ps1` scripts.

**Solution**:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Or use WSL instead (no execution policy restrictions).

### Virtual environment not activating in VS Code

**Problem**: New terminals don't have venv activated.

**Solution**: Select Python interpreter once (see "Virtual Environment Management" section above).

---

## Package Structure

```
synthetic-dividend/
├── src/ # Source code (importable package)
│ ├── __init__.py
│ ├── cli.py # Main CLI entry point
│ ├── data/ # Data providers and caching
│ ├── models/ # Backtesting and simulation
│ ├── compare/ # Batch comparison tools
│ ├── research/ # Research modules
│ ├── tools/ # GUI and utilities
│ └── paths.py # Centralized path management
├── tests/ # Test suite
│ ├── test_backtest.py
│ ├── test_portfolio_algorithms.py
│ └── ...
├── cache/ # Downloaded price data (auto-created)
├── data/ # Persistent data (e.g., best_sdn.json)
├── experiments/ # Reproducible experiments
├── pyproject.toml # All package configuration (modern standard)
├── Makefile # Unix/WSL dev commands
├── LICENSE # MIT License
└── README.md # User documentation
```

---

## Key Benefits

1. **Modern Standards** - Uses `pyproject.toml` (PEP 517/518/621 compliant)
2. **Editable Install** - Changes immediately available with `pip install -e .`
3. **Cross-Platform** - Works on Windows, macOS, Linux, WSL
4. **Flexible Dependencies** - Install only what you need
5. **Professional** - Ready for PyPI publication
6. **Developer-Friendly** - Make commands, parallel tests, auto-formatting

---

## Further Reading

- [Python Packaging Guide](https://packaging.python.org/)
- [PEP 621 - Storing project metadata in pyproject.toml](https://peps.python.org/pep-0621/)
- [PEP 517 - Build system specification](https://peps.python.org/pep-0517/)
- [PEP 518 - pyproject.toml specification](https://peps.python.org/pep-0518/)
- [pytest documentation](https://docs.pytest.org/)
- [WSL Documentation](https://docs.microsoft.com/en-us/windows/wsl/)

---

**Last Updated**: November 2024
**Status**: Production-ready, modern Python packaging
