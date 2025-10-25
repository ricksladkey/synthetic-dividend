.PHONY: help install install-dev test lint format clean build publish

help:
	@echo "Synthetic Dividend - Development Commands"
	@echo ""
	@echo "  make install       Install package in development mode"
	@echo "  make install-dev   Install with development dependencies"
	@echo "  make test          Run tests with coverage"
	@echo "  make lint          Run all linters (flake8, mypy, pylint)"
	@echo "  make format        Format code with black and isort"
	@echo "  make clean         Remove build artifacts and cache"
	@echo "  make build         Build distribution packages"
	@echo "  make publish       Publish to PyPI (requires credentials)"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test:
	pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html

lint:
	@echo "Running flake8..."
	flake8 src tests --max-line-length=100 --extend-ignore=E203,W503
	@echo "Running mypy..."
	mypy src --ignore-missing-imports
	@echo "Running pylint..."
	pylint src --max-line-length=100 --disable=C0103,C0114,C0115,C0116

format:
	@echo "Running isort..."
	isort src tests
	@echo "Running black..."
	black src tests

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pkl" -delete

build: clean
	python -m build

publish: build
	python -m twine upload dist/*
