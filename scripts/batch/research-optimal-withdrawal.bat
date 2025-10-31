@echo off
REM Find optimal withdrawal rate that minimizes abs(bank)
REM This finds the "balanced" withdrawal rate where volatility alpha matches withdrawals

echo Running Optimal Withdrawal Rate Research...
echo.

call .venv\Scripts\activate.bat
python -m src.research.optimal_withdrawal_rate

echo.
echo Results saved to: experiments\optimal_withdrawal\
pause
