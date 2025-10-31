#!/bin/bash
# run-tests.sh - Cross-platform script to run the test suite
# Replaces run-tests.bat

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

echo
echo "======================================================================"
echo "Running ALL Tests"
echo "======================================================================"
echo

# Run pytest with coverage
"$PYTHON_EXE" -m pytest -v --cov=src --cov-report=term-missing "$@"