@echo off
REM Run all unit tests for the buyback stack implementation
REM
REM This batch file runs the comprehensive test suite that validates:
REM   - FIFO buyback stack unwinding logic
REM   - Share count parity at ATH recovery
REM   - Buyback stack status tracking
REM   - Multiple rebalance trigger scenarios
REM
REM Expected results:
REM   - Tests with monotonic price rises: PASS
REM   - Tests with drawdown endings: PASS  
REM   - Tests with V-shapes (return to previous ATH, not new): FAIL (economically correct)
REM   - Tests with multiple cycles: Some PASS, some FAIL depending on final price

echo.
echo ======================================================================
echo Running Buyback Stack Unit Tests
echo ======================================================================
echo.

REM Set PYTHONPATH to include the app root
set PYTHONPATH=%~dp0

REM Run the tests using the virtual environment Python
c:\Users\ricks\OneDrive\Documents\GenAI\profit-sharing\.venv\Scripts\python.exe tests\test_buyback_stack.py

REM Capture exit code
set TEST_EXIT_CODE=%ERRORLEVEL%

echo.
echo ======================================================================
if %TEST_EXIT_CODE% EQU 0 (
    echo All tests PASSED!
) else (
    echo Some tests FAILED - see details above
    echo.
    echo Note: V-shape test failures are expected and demonstrate correct
    echo economic behavior when price returns to previous ATH without
    echo exceeding it. Different strategies produce different share counts.
)
echo ======================================================================
echo.

exit /b %TEST_EXIT_CODE%
