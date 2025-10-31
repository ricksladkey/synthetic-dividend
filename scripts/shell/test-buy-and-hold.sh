#!/bin/bash
# test-buy-and-hold.sh - Test buy-and-hold strategy on NVDA
# Replaces test-buy-and-hold.bat

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Run the buy-and-hold test with default parameters
"$SCRIPT_DIR/run-model.sh" NVDA 10/22/2024 10/22/2025 "buy-and-hold" "$@"