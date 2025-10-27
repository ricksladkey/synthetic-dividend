@echo off
REM Portfolio comparison batch file
REM Quick interface to portfolio simulator

REM Example 1: Compare crypto/stocks mix vs VOO (user's exact request)
REM python -m src.tools.portfolio_comparison --compare crypto_stocks conservative --start 2023-01-01 --end 2024-12-31

REM Example 2: Single portfolio analysis
REM python -m src.tools.portfolio_comparison --preset tech_heavy --start 2023-01-01

REM Example 3: Custom allocation
REM python -m src.tools.portfolio_comparison --custom "NVDA:0.5,VOO:0.5" --start 2023-01-01

REM Default: Run the user's requested comparison
python -m src.tools.portfolio_comparison --compare crypto_stocks conservative --start 2023-01-01 --end 2024-12-31 --output output/crypto_stocks_vs_voo.png

pause
