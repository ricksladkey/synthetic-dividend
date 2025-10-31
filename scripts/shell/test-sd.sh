#!/bin/bash
# test-sd.sh - Test SD strategy on NVDA
# Replaces test-sd.bat

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Run the SD test with default parameters
"$SCRIPT_DIR/run-model.sh" NVDA 10/22/2024 10/22/2025 "sd-9.05,50" "$@"