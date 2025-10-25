@echo off
REM Batch comparison for NVDA over 1-year period
REM Generates Excel/Sheets importable CSV with all algorithm configurations

python -m src.compare.batch_comparison NVDA 10/22/2024 10/22/2025 NVDA_comparison.csv
