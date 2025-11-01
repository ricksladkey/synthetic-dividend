.PHONY: help install install-dev test lint format clean build publish

help:
	@echo "Synthetic Dividend - Development Commands"
	@echo ""
	@echo "  make install       Install package in development mode"
	@echo "  make install-dev   Install with development dependencies"
	@echo "  make test          Run tests (CI mode - quiet)"
	@echo "  make lint          Run all linters (black, isort, flake8, mypy)"
	@echo "  make format        Format code with black and isort"
	@echo "  make clean         Remove build artifacts and cache"
	@echo "  make build         Build distribution packages"
	@echo "  make publish       Publish to PyPI (requires credentials)"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test:
	.venv/Scripts/python -m pytest -q

lint:
	@echo "Running black..."
	.venv/Scripts/python -m black --check .
	@echo "Running isort..."
	.venv/Scripts/python -m isort --check-only .
	@echo "Running flake8..."
	.venv/Scripts/python -m flake8 src tests --max-line-length=100 --extend-ignore=E203,W503
	@echo "Running mypy..."
	.venv/Scripts/python -m mypy --explicit-package-bases src

format:
	@echo "Running isort..."
	.venv/Scripts/python -m isort src tests
	@echo "Running black..."
	.venv/Scripts/python -m black src tests

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pkl" -delete

build: clean
	python -m build

publish: build
	python -m twine upload dist/*
