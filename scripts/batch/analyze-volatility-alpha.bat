@echo off
REM Volatility Alpha Analyzer - Quick analysis tool
REM Auto-suggests SD parameter based on historical volatility

if "%~1"=="" (
    echo Usage: analyze-volatility-alpha.bat TICKER START_DATE END_DATE [OPTIONS]
    echo.
    echo Examples:
    echo   analyze-volatility-alpha.bat GLD 10/26/2024 10/26/2025
    echo   analyze-volatility-alpha.bat NVDA 10/23/2023 10/23/2024 --plot
    echo   analyze-volatility-alpha.bat AAPL 01/01/2024 12/31/2024 --sd 8 --plot
    echo   analyze-volatility-alpha.bat MSFT 01/01/2024 12/31/2024 --profit-sharing 75
    echo.
    echo Options:
    echo   --plot              Generate price chart with buy/sell markers
    echo   --sd N              Override SD parameter (e.g., --sd 8)
    echo   --profit-sharing N  Set profit sharing %% (default: 50)
    echo   --qty N             Set initial quantity (default: 100)
    echo.
    echo The tool will:
    echo   1. Calculate historical volatility
    echo   2. Auto-suggest optimal SD parameter
    echo   3. Compare full strategy vs ATH-only
    echo   4. Report volatility alpha
    echo   5. Optionally plot chart (--plot)
    exit /b 1
)

.venv\Scripts\python.exe -m src.tools.volatility_alpha_analyzer %*
