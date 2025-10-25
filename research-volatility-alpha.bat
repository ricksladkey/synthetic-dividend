@echo off
REM Volatility Alpha Research
REM Compares best synthetic dividend (with buybacks) vs ATH-only baseline
REM to quantify the extra profit from capitalizing on volatility

echo ========================================
echo Volatility Alpha Analysis
echo ========================================
echo.
echo This will compare:
echo - Enhanced Strategy: Best sdN with buybacks enabled
echo - ATH-Only Baseline: Same trigger, NO buybacks
echo.
echo The difference is "Volatility Alpha" - extra profit from price volatility
echo.

REM Use hardcoded venv Python path (bypasses activation)
set PYTHON=c:\Users\ricks\OneDrive\Documents\GenAI\profit-sharing\.venv\Scripts\python.exe

REM Historical period (weekday dates to avoid Yahoo Finance weekend gaps)
set START_DATE=10/23/2023
set END_DATE=10/23/2024

REM Standard parameters from Phase 1
set PROFIT_PCT=50
set INITIAL_QTY=10000

echo Running comprehensive analysis...
echo - Assets: 12 (NVDA, MSTR, BTC-USD, ETH-USD, etc.)
echo - Period: %START_DATE% to %END_DATE%
echo - Profit Taking: %PROFIT_PCT%%%
echo - Initial Quantity: %INITIAL_QTY%
echo.

%PYTHON% -m src.research.volatility_alpha ^
    --comprehensive ^
    --start "%START_DATE%" ^
    --end "%END_DATE%" ^
    --profit %PROFIT_PCT% ^
    --qty %INITIAL_QTY% ^
    --output volatility_alpha_1year_core.csv

echo.
echo ========================================
echo Analysis Complete!
echo ========================================
echo Output: volatility_alpha_1year_core.csv
echo.
pause
