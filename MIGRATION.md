# Migration Guide: Development → Production Package

## What Changed

We've transformed the project from a development prototype into a production-ready installable Python package. Here's what changed and why:

### File Structure Changes

**NEW FILES**:
- `pyproject.toml` - Modern Python packaging configuration (PEP 517/518 compliant)
- `MANIFEST.in` - Controls which files are included in distributions
- `LICENSE` - MIT License for open-source distribution
- `Makefile` - Unix/Linux/macOS development commands
- `dev.ps1` - Windows PowerShell development commands
- `INSTALLATION.md` - Comprehensive installation and packaging guide
- `.flake8` - Linter configuration

**DEPRECATED** (but still present for now):
- `requirements.txt` - Dependencies now in `pyproject.toml`
- `.bat` files - Replaced by cross-platform entry points

### Installation Changes

**OLD WAY** (development only):
```powershell
# Clone repo
git clone...
cd financial-modeling-app

# Create venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run commands
python -m src.run_model NVDA ...
```

**NEW WAY** (production-ready):
```powershell
# Clone repo
git clone...
cd financial-modeling-app

# Install package in editable mode
pip install -e .

# Commands now available globally (no python -m needed!)
sd-backtest NVDA 10/22/2024 10/22/2025 sd8 --qty 1000
sd-compare NVDA 10/22/2024 10/22/2025 results.csv
sd-research --ticker NVDA --quick
```

### Why This Matters

1. **Cross-Platform**: Works identically on Windows, macOS, Linux, WSL
2. **Professional**: Follows Python packaging best practices
3. **Installable**: Can be published to PyPI for `pip install synthetic-dividend`
4. **Developer-Friendly**: Entry points mean no more typing `python -m src.run_model`
5. **WSL-Ready**: Seamless Windows ↔ Linux development

### Development Workflow Changes

**Windows**:
```powershell
# Install dev dependencies
.\dev.ps1 install-dev

# Format code before commit
.\dev.ps1 format

# Run linters
.\dev.ps1 lint

# Run tests
.\dev.ps1 test
```

**Unix/Linux/macOS/WSL**:
```bash
# Install dev dependencies
make install-dev

# Format code before commit
make format

# Run linters
make lint

# Run tests
make test
```

### Entry Points (CLI Commands)

After `pip install -e .`, these commands work from anywhere:

| Command | Old Command | Description |
|---------|-------------|-------------|
| `sd-backtest` or `synthetic-dividend` | `python -m src.run_model` | Run single backtest |
| `sd-compare` | `python -m src.compare.batch_comparison` | Compare multiple strategies |
| `sd-research` | `python -m src.research.optimal_rebalancing` | Research optimal parameters |

### WSL Integration

**Why WSL?**:
- ✅ Native Unix tools (bash, make, grep, sed)
- ✅ Faster package installs
- ✅ No PowerShell encoding issues
- ✅ Docker compatibility
- ✅ Consistent with Linux servers/CI

**Setup**:
1. Install WSL2: `wsl --install -d Ubuntu-22.04`
2. Open VS Code → Install "Remote - WSL" extension
3. Click green icon (bottom-left) → "New WSL Window"
4. Navigate to project: `cd /mnt/c/Users/ricks/OneDrive/.../financial-modeling-app`
5. Install: `make install-dev`

Your Windows files are accessible at `/mnt/c/...` from WSL.

### Publishing to PyPI (Future)

When ready for public release:

```bash
# Build packages
python -m build

# Test on TestPyPI
python -m twine upload --repository testpypi dist/*

# Publish to PyPI
python -m twine upload dist/*

# Users can then install with:
# pip install synthetic-dividend
```

### Migration Checklist

- [x] Create `pyproject.toml` with package metadata
- [x] Add entry points for CLI tools
- [x] Create `MANIFEST.in` for file inclusion
- [x] Add `LICENSE` (MIT)
- [x] Create `Makefile` for Unix development
- [x] Create `dev.ps1` for Windows development
- [x] Write `INSTALLATION.md` guide
- [x] Fix entry points to accept no arguments (for CLI)
- [x] Test package installation (`pip install -e .`)
- [x] Test entry points work (`sd-backtest --help`)
- [x] Test actual backtest runs

### Next Steps

1. **Adopt the new workflow**: Use `sd-backtest` instead of `python -m src.run_model`
2. **Try WSL**: Much better Python experience on Windows
3. **Run linters**: `.\dev.ps1 lint` or `make lint`
4. **Add type hints**: Gradually improve code quality with mypy
5. **Increase test coverage**: Use pytest-cov to measure

### Questions?

See `INSTALLATION.md` for comprehensive guide covering:
- Package installation
- Development setup
- WSL integration
- Publishing to PyPI
- Troubleshooting

---

**Status**: Production-ready package structure ✅  
**Last Updated**: October 2025
