@echo off
REM Generate Volatility Alpha Validation Dataset
REM Analyzes 6 assets across 1, 2, and 3 year timeframes

echo ================================================================================
echo Volatility Alpha Validation Dataset Generator
echo ================================================================================
echo.
echo This will analyze:
echo   - NVDA, MSTR, BTC-USD, ETH-USD, PLTR, GLD
echo   - 1, 2, and 3 year timeframes
echo   - Auto-suggested SD parameters
echo.
echo Output: volatility_alpha_table.csv
echo.

.venv\Scripts\python.exe -m src.research.volatility_alpha_table

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================================================
    echo ✅ Generation complete!
    echo.
    echo Results saved to: volatility_alpha_table.csv
    echo.
    echo To view:
    echo   - Open CSV in Excel/Sheets
    echo   - Check experiments/volatility-alpha-validation/README.md for analysis
    echo ================================================================================
) else (
    echo.
    echo ❌ Error generating dataset (exit code %ERRORLEVEL%)
)
