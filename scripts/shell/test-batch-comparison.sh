#!/bin/bash
# test-batch-comparison.sh - Run batch comparison test
# Replaces test-batch-comparison.bat

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

# Run batch comparison
"$PYTHON_EXE" -m src.compare.batch_comparison NVDA 10/22/2024 10/22/2025 buy-and-hold sd-9.05,50 "$@"