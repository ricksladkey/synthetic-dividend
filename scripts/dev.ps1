# Synthetic Dividend - Development Commands (PowerShell)
# Run like: .\dev.ps1 install-dev

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

function Show-Help {
    Write-Host "Synthetic Dividend - Development Commands" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  .\dev.ps1 install       " -NoNewline; Write-Host "Install package in development mode"
    Write-Host "  .\dev.ps1 install-dev   " -NoNewline; Write-Host "Install with development dependencies"
    Write-Host "  .\dev.ps1 test          " -NoNewline; Write-Host "Run tests with coverage"
    Write-Host "  .\dev.ps1 lint          " -NoNewline; Write-Host "Run all linters (flake8, mypy, pylint)"
    Write-Host "  .\dev.ps1 format        " -NoNewline; Write-Host "Format code with black and isort"
    Write-Host "  .\dev.ps1 clean         " -NoNewline; Write-Host "Remove build artifacts and cache"
    Write-Host "  .\dev.ps1 build         " -NoNewline; Write-Host "Build distribution packages"
}

switch ($Command) {
    "install" {
        pip install -e .
    }
    "install-dev" {
        pip install -e ".[dev]"
    }
    "test" {
        pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html
    }
    "lint" {
        Write-Host "Running flake8..." -ForegroundColor Yellow
        flake8 src tests --max-line-length=100 --extend-ignore=E203,W503
        Write-Host "Running mypy..." -ForegroundColor Yellow
        mypy src --ignore-missing-imports
        Write-Host "Running pylint..." -ForegroundColor Yellow
        pylint src --max-line-length=100 --disable=C0103,C0114,C0115,C0116
    }
    "format" {
        Write-Host "Running isort..." -ForegroundColor Yellow
        isort src tests
        Write-Host "Running black..." -ForegroundColor Yellow
        black src tests
    }
    "clean" {
        Write-Host "Cleaning build artifacts..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force build, dist, *.egg-info, .pytest_cache, .mypy_cache, htmlcov -ErrorAction SilentlyContinue
        Get-ChildItem -Path . -Include __pycache__ -Recurse -Force | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
        Get-ChildItem -Path . -Include *.pyc,*.pkl -Recurse -Force | Remove-Item -Force -ErrorAction SilentlyContinue
    }
    "build" {
        & $PSCommandPath clean
        python -m build
    }
    default {
        Show-Help
    }
}
