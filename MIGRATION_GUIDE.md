# Migration Guide: requirements.txt → pyproject.toml

## What Changed?

As of November 2024, this project has migrated from `requirements.txt` files to `pyproject.toml` for dependency management, following modern Python packaging standards ([PEP 621](https://peps.python.org/pep-0621/)).

## Quick Migration

### Before (Old Way ❌)

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### After (New Way ✅)

```bash
pip install -e .              # Core dependencies
pip install -e ".[dev]"       # Development dependencies
pip install -e ".[gui]"       # GUI dependencies
pip install -e ".[all]"       # Everything
```

## What This Means

### Files Removed
- ❌ `requirements.txt` - **REMOVED**
- ❌ `requirements-dev.txt` - **REMOVED**

### Single Source of Truth
All dependencies are now defined in `pyproject.toml`:

```toml
[project]
dependencies = [
    "pandas>=1.0",
    "matplotlib>=3.0",
    "yfinance>=0.2.0",
    "pandas-datareader>=0.10",
    "lxml>=4.9",
    "simpy>=4.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "pytest-xdist>=3.0",
    "mypy>=1.0",
    "black>=23.0",
    "flake8>=6.0",
    "pylint>=3.0",
    "isort>=5.0",
]

gui = [
    "markdown>=3.4",
    "tkinterweb>=3.15",
    "tkcalendar>=1.6",
]

all = [
    # Combines dev + gui
]
```

## Benefits

1. **Modern Standard** - Follows PEP 517/518/621
2. **Single File** - All metadata in one place
3. **Optional Dependencies** - Install only what you need
4. **Better Tooling** - Supported by pip, build, poetry, hatch, etc.
5. **No Duplication** - One source of truth

## For CI/CD Pipelines

### Before
```yaml
- run: pip install -r requirements.txt
- run: pip install -r requirements-dev.txt
```

### After
```yaml
- run: pip install -e ".[dev]"
```

## For Docker/Containerization

### Before
```dockerfile
COPY requirements.txt .
RUN pip install -r requirements.txt
```

### After
```dockerfile
COPY pyproject.toml .
COPY src/ src/
RUN pip install .
```

## For Documentation

If your documentation references `requirements.txt`, update it to reference `pyproject.toml` instead:

- Installation instructions → See [INSTALLATION.md](INSTALLATION.md)
- Dependency list → See `pyproject.toml` `[project.dependencies]`
- Dev dependencies → See `pyproject.toml` `[project.optional-dependencies.dev]`

## Rollback (If Needed)

If you absolutely need the old `requirements.txt` format, you can generate it:

```bash
# Generate requirements.txt from current environment
pip freeze > requirements.txt

# Or generate from pyproject.toml using pip-tools
pip install pip-tools
pip-compile pyproject.toml
```

**However**, this is not recommended. Modern Python tooling works best with `pyproject.toml`.

## Questions?

See [INSTALLATION.md](INSTALLATION.md) for complete installation documentation.
