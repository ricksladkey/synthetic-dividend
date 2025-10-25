@echo off
echo.
echo ======================================================================
echo Running Profit Sharing Composition Analysis
echo ======================================================================
echo.
echo This analysis explores how profit-sharing ratios from -25%% to 125%%
echo affect holdings composition over 2-3 years.
echo.
echo Categories:
echo   -25%% to 0%%   : Accumulation (deploy less than 100%% of profits)
echo     0%% to 50%%  : Standard approach
echo    50%% to 100%% : Aggressive cash extraction  
echo   100%% to 125%% : Core depletion (unstable)
echo.
echo ======================================================================
echo.

C:/build/synthetic-dividend/.venv/Scripts/python.exe src\research\profit_sharing_composition.py

echo.
echo ======================================================================
echo Analysis Complete!
echo ======================================================================
echo.
pause
