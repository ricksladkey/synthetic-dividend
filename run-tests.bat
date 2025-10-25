@echo off
REM Run ALL unit tests for the synthetic dividend project
REM
REM This batch file runs the complete test suite using pytest, which includes:
REM   - test_buyback_stack.py - FIFO buyback stack unwinding logic
REM   - test_synthetic_dividend.py - Core synthetic dividend algorithm
REM   - test_volatility_alpha_synthetic.py - Volatility alpha calculations
REM   - Any other test files in the tests/ directory
REM
REM Usage:
REM   run-tests.bat              - Run all tests
REM   run-tests.bat -v           - Run with verbose output
REM   run-tests.bat -k pattern   - Run tests matching pattern
REM   run-tests.bat --lf         - Run last failed tests only

echo.
echo ======================================================================
echo Running ALL Tests
echo ======================================================================
echo.

REM Set PYTHONPATH to include the app root
set PYTHONPATH=%~dp0

REM Run all tests using pytest in the virtual environment
.venv\Scripts\python.exe -m pytest tests\ %*

REM Capture exit code
set TEST_EXIT_CODE=%ERRORLEVEL%

echo.
echo ======================================================================
if %TEST_EXIT_CODE% EQU 0 (
    echo All tests PASSED!
) else (
    echo Some tests FAILED - see details above
)
echo ======================================================================
echo.

exit /b %TEST_EXIT_CODE%
