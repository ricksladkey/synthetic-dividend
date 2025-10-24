@echo off
REM Phase 1: Core 1-year dataset (12 assets x 7 sdN values = 84 backtests)
REM Tests all asset classes with 50% profit sharing

echo ========================================
echo PHASE 1: Core Dataset (1-year horizon)
echo ========================================
echo.
echo Assets: 12 (NVDA, GOOG, PLTR, MSTR, SHOP, BTC-USD, ETH-USD, GLD, SLV, SPY, QQQ, DIA)
echo sdN values: 7 (sd4, sd6, sd8, sd10, sd12, sd16, sd20)
echo Profit sharing: 50%%
echo Total backtests: 84
echo.
echo This will take approximately 20-30 minutes...
echo.

REM Run without --ticker or --asset-class to test ALL assets
c:\Users\ricks\OneDrive\Documents\GenAI\profit-sharing\.venv\Scripts\python.exe -m src.research.optimal_rebalancing --start 10/22/2024 --end 10/22/2025 --profit 50 --qty 10000 --output research_phase1_1year_core.csv

echo.
echo ========================================
echo Phase 1 Complete!
echo ========================================
echo Output: research_phase1_1year_core.csv
echo.
pause
