@echo off
REM Example visualization commands for the financial modeling app
REM This batch file demonstrates how to generate price charts with buy/sell markers
REM
REM Usage of runner.py:
REM   python -m src.compare.runner <TICKER> <START> <END> <ALGO_ID> <OUT_PNG>
REM
REM Available algorithm IDs:
REM   - buy-and-hold
REM   - ath-only/9.05%
REM   - synthetic-dividend/9.05%/50%
REM   - synthetic-dividend/9.05%/50%/full  (with buyback stack)
REM
REM Examples below use NVDA data from Oct 2024 to Oct 2025

echo.
echo Generating visualization examples (using venv python)...
echo.

REM Use the project's venv python explicitly so the script works without activating the venv.
set VENV_PY=%~dp0\.venv\Scripts\python.exe
if not exist "%VENV_PY%" (
	REM Fallback to repository-relative path (when running from repo root)
	set VENV_PY=%CD%\.venv\Scripts\python.exe
)

REM Example 1: Buy and Hold strategy
echo [1/4] Generating Buy-and-Hold chart...
"%VENV_PY%" -m src.compare.runner NVDA 2024-10-22 2025-10-22 buy-and-hold out-nvda-buy-hold.png

REM Example 2: ATH-Only strategy (9.05% rebalance threshold)
echo [2/4] Generating ATH-Only chart...
"%VENV_PY%" -m src.compare.runner NVDA 2024-10-22 2025-10-22 sd-ath-only-9.05,50 out-nvda-ath-only.png

REM Example 3: Synthetic Dividend Trigger-Only (9.05% threshold, 50% profit sharing)
echo [3/4] Generating Synthetic Dividend Trigger-Only chart...
"%VENV_PY%" -m src.compare.runner NVDA 2024-10-22 2025-10-22 sd-9.05,50 out-nvda-sd-trigger.png

REM Example 4: Synthetic Dividend Full Mode (with buyback stack, 9.05% threshold, 50% profit sharing)
echo [4/4] Generating Synthetic Dividend Full Mode (with buyback stack) chart...
"%VENV_PY%" -m src.compare.runner NVDA 2024-10-22 2025-10-22 sd-9.05,50 out-nvda-sd-full.png

echo.
echo ========================================
echo Visualization generation complete!
echo ========================================
echo.
echo Generated files:
echo   - out-nvda-buy-hold.png (+ transaction log)
echo   - out-nvda-ath-only.png (+ transaction log)
echo   - out-nvda-sd-trigger.png (+ transaction log)
echo   - out-nvda-sd-full.png (+ transaction log)
echo.
echo Each PNG shows the price chart with buy/sell markers.
echo Transaction logs are saved as *-tx.txt files.
echo.

REM Alternative: Generate a single chart with your preferred settings
REM Uncomment the line below and adjust parameters as needed (use new naming convention):
REM "%VENV_PY%" -m src.compare.runner NVDA 2024-10-22 2025-10-22 sd-9.05,50 out-nvda.png

pause
