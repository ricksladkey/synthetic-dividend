@echo off
REM Run retirement planning research experiment
REM Tests sustainable withdrawal rates with volatility harvesting

echo Running Retirement Planning Experiment...
echo.

call .venv\Scripts\activate.bat
python -m src.research.retirement_planning

echo.
echo Results saved to: experiments\retirement_planning\
pause
