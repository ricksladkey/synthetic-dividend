@echo off
REM Analyze missing opportunity cost on initial capital
REM
REM This script quantifies what we're NOT currently tracking:
REM the opportunity cost on the initial equity position.

echo.
echo ======================================================================
echo Initial Capital Opportunity Cost Analysis
echo ======================================================================
echo.

REM Set PYTHONPATH to include the app root
set PYTHONPATH=%~dp0

REM Run the analysis using the virtual environment Python
.venv\Scripts\python.exe src\research\initial_capital_opportunity_cost.py

REM Capture exit code
set EXIT_CODE=%ERRORLEVEL%

echo.
if %EXIT_CODE% EQU 0 (
    echo Analysis complete!
) else (
    echo Analysis failed - see errors above
)
echo.

exit /b %EXIT_CODE%
