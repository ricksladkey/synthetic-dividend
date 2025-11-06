.PHONY: help install install-dev test test-all lint check format clean build publish examples

# Platform-independent Python executable detection
ROOT_DIR := $(CURDIR)
PYTHON_CANDIDATES := \
    $(ROOT_DIR)/.venv/bin/python \
    $(ROOT_DIR)/.venv/Scripts/python \
    $(ROOT_DIR)/.venv/Scripts/python.exe

PYTHON := $(firstword $(wildcard $(PYTHON_CANDIDATES)))

ifeq ($(PYTHON),)
  $(error Python executable not found in .venv. Please create virtual environment: python -m venv .venv)
endif

# Export for sub-Makefiles
export PYTHON

help:
	@echo "Synthetic Dividend - Development Commands"
	@echo ""
	@echo "  make install       Install package in development mode"
	@echo "  make install-dev   Install with development dependencies"
	@echo "  make test-checks    Run tests (CI mode - quiet)"
	@echo "  make test-all      Run all tests (quiet, includes network tests)"
	@echo "  make test          Run both CI-only and all tests (quiet)"
	@echo "  make lint          Run all linters (black, isort, flake8, mypy)"
	@echo "  make check         Run lint and test (simulates CI checks)"
	@echo "  make format        Format code with black and isort"
	@echo "  make clean         Remove build artifacts and cache"
	@echo "  make build         Build distribution packages"
	@echo "  make publish       Publish to PyPI (requires credentials)"
	@echo "  make examples      Re-generate all experiment data (volatility alpha, etc.)"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test-checks:
	env CI=true $(PYTHON) -m pytest -q -m "not slow"

test-all:
	$(PYTHON) -m pytest -q

test: test-checks test-all

lint:
	@echo "Running black..."
	$(PYTHON) -m black --check .
	@echo "Running isort..."
	$(PYTHON) -m isort --check-only .
	@echo "Running flake8..."
	$(PYTHON) -m flake8 src tests --max-line-length=100 --extend-ignore=E203,W503
	@echo "Running mypy..."
	$(PYTHON) -m mypy --explicit-package-bases --exclude "src/research|src/charts" src

check: format lint test-checks test-all

format:
	@echo "Running isort..."
	$(PYTHON) -m isort src tests
	@echo "Running black..."
	$(PYTHON) -m black src tests

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pkl" -delete

build: clean
	$(PYTHON) -m build

publish: build
	$(PYTHON) -m twine upload dist/*

examples:
	@echo "================================================================================"
	@echo "Re-generating all experiment data"
	@echo "================================================================================"
	@echo ""
	@echo "[1/3] Volatility Alpha Validation..."
	@$(MAKE) -C experiments/volatility-alpha-validation
	@echo ""
	@echo "[2/3] Portfolio Volatility Alpha..."
	@$(MAKE) -C experiments/portfolio_volatility_alpha
	@echo ""
	@echo "[3/3] Optimal Withdrawal Rate..."
	@$(MAKE) -C experiments/optimal_withdrawal
	@echo ""
	@echo "================================================================================"
	@echo "✅ All experiments complete!"
	@echo "================================================================================"
	@echo ""
	@echo "Generated data:"
	@echo "  - experiments/volatility-alpha-validation/volatility_alpha_table.csv"
	@echo "  - experiments/portfolio_volatility_alpha/results.csv"
	@echo "  - experiments/optimal_withdrawal/*.csv"
	@echo ""
	@echo "Review README.md to ensure documented numbers match generated results."
