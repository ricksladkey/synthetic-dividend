# Installation & Packaging Guide

## 🚀 Quick Start

### For Users (Install from GitHub)

```bash
# Clone repository
git clone https://github.com/ricksladkey/synthetic-dividend.git
cd synthetic-dividend/financial-modeling-app

# Install in development mode (editable)
pip install -e .

# Or install with dev tools
pip install -e ".[dev]"
```

**After installation**, these commands become available globally:
- `synthetic-dividend` - Unified CLI (recommended)
- `sd-backtest` - Run single backtests
- `sd-compare` - Compare multiple strategies
- `sd-research` - Research optimal parameters
- `sd-volatility-alpha` - Analyze volatility alpha
- `sd-run-tests` - Run test suite

### Cross-Platform Scripts

For convenience, we've also included shell scripts that work on Windows, macOS, and Linux:

```bash
# Run backtests
./scripts/shell/run-model.sh NVDA 2024-10-22 2025-10-22 sd-9.05,50

# Run tests
./scripts/shell/run-tests.sh

# Quick tests
./scripts/shell/test-sd.sh
./scripts/shell/test-buy-and-hold.sh
./scripts/shell/test-batch-comparison.sh
```

### For Development

**Cross-Platform (Recommended)**:
```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
python -m src.cli test

# Or use convenience scripts
./scripts/shell/run-tests.sh

# Run backtests
python -m src.cli backtest NVDA 2024-10-22 2025-10-22 sd-9.05,50
./scripts/shell/run-model.sh NVDA 2024-10-22 2025-10-22 sd-9.05,50
```

**Windows (PowerShell)**:
```powershell
# Install development dependencies
pip install -e ".[dev]"

# Run tests
python -m src.cli test

# Run backtests
python -m src.cli backtest NVDA 2024-10-22 2025-10-22 sd-9.05,50
```

**Unix/Linux/macOS (Make)**:
```bash
# Install development dependencies
make install-dev

# Run tests
make test

# Run backtests
python -m src.cli backtest NVDA 2024-10-22 2025-10-22 sd-9.05,50
```

# Format code
make format

# Run linters
make lint

# See all commands
make help
```

---

## 📦 Building Distribution Packages

### Build Wheel and Source Distribution

```bash
# Install build tools
pip install build twine

# Build packages (creates dist/ directory)
python -m build

# Or use shortcuts
make build        # Unix
.\dev.ps1 build   # Windows
```

This creates:
- `dist/synthetic_dividend-0.1.0.tar.gz` (source distribution)
- `dist/synthetic_dividend-0.1.0-py3-none-any.whl` (wheel)

### Install from Local Build

```bash
pip install dist/synthetic_dividend-0.1.0-py3-none-any.whl
```

---

## 🐳 Cross-Platform Development with WSL

### Why WSL?

Windows Subsystem for Linux provides:
- **True Unix environment** - native bash, make, symlinks
- **Better Python tooling** - fewer encoding issues, faster package installs
- **Docker compatibility** - run containers natively
- **Git line endings** - consistent LF without .gitattributes fights
- **Zero dual-boot** - switch between Windows/Linux instantly

### Setup WSL2 + VS Code Integration

1. **Install WSL2**:
   ```powershell
   # Run in PowerShell as Administrator
   wsl --install -d Ubuntu-22.04
   
   # Restart computer
   ```

2. **Install VS Code WSL Extension**:
   - Open VS Code
   - Install extension: `ms-vscode-remote.remote-wsl`
   - Click green icon in bottom-left corner → "New WSL Window"

3. **Setup Python in WSL**:
   ```bash
   # In WSL terminal
   sudo apt update
   sudo apt install python3.11 python3.11-venv python3-pip
   
   # Navigate to project
   cd /mnt/c/Users/ricks/OneDrive/Documents/GenAI/profit-sharing/financial-modeling-app
   
   # Create venv
   python3.11 -m venv .venv
   source .venv/bin/activate
   
   # Install in dev mode
   make install-dev
   ```

4. **VS Code will automatically**:
   - Detect `.venv` in WSL
   - Use correct Python interpreter
   - Run terminals in WSL bash
   - Git operations use Unix line endings

### File Access

Your Windows files are accessible at `/mnt/c/...`:
```bash
# Windows: C:\Users\ricks\OneDrive\...
# WSL:     /mnt/c/Users/ricks/OneDrive/...
```

---

## 🔧 Fixing Environment Activation Issues

### Problem: Virtual Environment "Lost" Between Commands

**Root Cause**: PowerShell terminals are stateless - each new terminal starts fresh.

**Solution 1: VS Code Python Extension** (Recommended)
- Select Python interpreter once: `Ctrl+Shift+P` → "Python: Select Interpreter"
- Choose `.venv/Scripts/python.exe`
- All terminals auto-activate venv

**Solution 2: PowerShell Profile Auto-Activation**
```powershell
# Edit profile
notepad $PROFILE

# Add this line:
if (Test-Path ".venv\Scripts\Activate.ps1") { .\.venv\Scripts\Activate.ps1 }

# Save and reload
. $PROFILE
```

**Solution 3: Use WSL** (Best long-term)
- WSL terminals stay activated
- Better shell experience overall
- No PowerShell execution policy issues

---

## 📋 Development Workflow

### Daily Development (Windows)

```powershell
# Activate venv (if not using VS Code Python extension)
.\.venv\Scripts\Activate.ps1

# Make code changes
# ...

# Format and lint before committing
.\dev.ps1 format
.\dev.ps1 lint

# Run tests
.\dev.ps1 test

# Commit changes
git add .
git commit -m "Your message"
git push
```

### Daily Development (WSL/Unix)

```bash
# Activate venv
source .venv/bin/activate

# Make code changes
# ...

# Format and lint
make format
make lint

# Run tests
make test

# Commit
git add .
git commit -m "Your message"
git push
```

---

## 🌍 Publishing to PyPI

### Test Publishing (TestPyPI)

```bash
# Build packages
python -m build

# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ synthetic-dividend
```

### Production Publishing (PyPI)

```bash
# Build packages
python -m build

# Upload to PyPI (requires API token)
python -m twine upload dist/*

# Users can now install with:
# pip install synthetic-dividend
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

## 🎯 Package Structure

```
financial-modeling-app/
├── src/                    # Source code (importable package)
│   ├── __init__.py
│   ├── synthetic_dividend_tool.py  # Unified CLI entry point
│   ├── compare/
│   │   └── batch_comparison.py  # Entry point: sd-compare
│   └── research/
│       └── optimal_rebalancing.py  # Entry point: sd-research
├── tests/                  # Test suite
├── pyproject.toml          # Modern package config (replaces setup.py)
├── MANIFEST.in             # Include non-Python files in dist
├── LICENSE                 # MIT License
├── README.md               # User-facing documentation
├── Makefile                # Unix dev commands
├── dev.ps1                 # Windows dev commands
└── requirements.txt        # Deprecated - use pyproject.toml instead
```

---

## 🔑 Key Benefits of This Structure

1. **`pip install -e .`** - Editable install, changes immediately available
2. **Entry points** - `synthetic-dividend`, `sd-compare`, `sd-research` work globally after install
3. **`pyproject.toml`** - Single source of truth for all config (PEP 517/518 compliant)
4. **Cross-platform** - Makefile (Unix) + dev.ps1 (Windows) + WSL support
5. **Professional** - Ready for PyPI, follows modern Python packaging standards
6. **Developer-friendly** - Consistent commands across platforms

---

## 📚 Further Reading

- [Python Packaging Guide](https://packaging.python.org/)
- [PEP 517](https://peps.python.org/pep-0517/) - Build system specification
- [PEP 518](https://peps.python.org/pep-0518/) - pyproject.toml specification
- [WSL Documentation](https://docs.microsoft.com/en-us/windows/wsl/)
- [VS Code Remote - WSL](https://code.visualstudio.com/docs/remote/wsl)

---

**Last Updated**: October 2025  
**Status**: Production-ready package structure
