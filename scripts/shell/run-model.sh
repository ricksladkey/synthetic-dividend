#!/bin/bash
# run-model.sh - Cross-platform script to run backtest simulations
# Replaces run-model.bat

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Try to find Python executable
if [ -f "$PROJECT_ROOT/.venv/bin/python" ]; then
    PYTHON_EXE="$PROJECT_ROOT/.venv/bin/python"
elif [ -f "$PROJECT_ROOT/.venv/Scripts/python.exe" ]; then
    PYTHON_EXE="$PROJECT_ROOT/.venv/Scripts/python.exe"
elif command -v python3 &> /dev/null; then
    PYTHON_EXE="python3"
else
    PYTHON_EXE="python"
fi

# Check if we have enough arguments
if [ $# -lt 4 ]; then
    echo "Usage: $0 TICKER START_DATE END_DATE STRATEGY_NAME [options]"
    echo "Example: $0 NVDA 10/22/2024 10/22/2025 sd-9.05,50 --qty 1000"
    exit 2
fi

# Run the backtest using synthetic-dividend CLI
"$PYTHON_EXE" -m src.synthetic_dividend_tool run backtest "$@"