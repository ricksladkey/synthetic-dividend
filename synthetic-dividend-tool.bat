@echo off
REM Synthetic Dividend Tool - Master CLI Entry Point
REM
REM This is a swiss army knife tool that provides a unified interface
REM to all synthetic dividend operations.
REM
REM Usage: synthetic-dividend-tool <command> [options]
REM
REM Run 'synthetic-dividend-tool --help' for full documentation.

C:/build/synthetic-dividend/.venv/Scripts/python.exe -m src.synthetic_dividend_tool %*
