@echo off
REM Strategy comparison for portfolio planning
REM Compares buy-and-hold, SD8-ATH-Only, and SD8 Full strategies
REM
REM Usage:
REM   compare-strategies.bat TICKER START END
REM
REM Example:
REM   compare-strategies.bat NVDA 2020-01-01 2025-01-01

if "%1"=="" (
    echo Usage: compare-strategies.bat TICKER START END
    echo Example: compare-strategies.bat NVDA 2020-01-01 2025-01-01
    exit /b 1
)

if "%2"=="" (
    echo Usage: compare-strategies.bat TICKER START END
    echo Example: compare-strategies.bat NVDA 2020-01-01 2025-01-01
    exit /b 1
)

if "%3"=="" (
    echo Usage: compare-strategies.bat TICKER START END
    echo Example: compare-strategies.bat NVDA 2020-01-01 2025-01-01
    exit /b 1
)

set TICKER=%1
set START=%2
set END=%3

echo Running strategy comparison for %TICKER% from %START% to %END%...
echo.

REM Change to repository root (two levels up from src\research\)
pushd "%~dp0..\.."

python -m src.research.strategy_comparison %TICKER% %START% %END%

popd
