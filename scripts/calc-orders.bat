@echo off
REM Order Calculator - Quick launcher for manual trading
REM Usage: .\calc-orders.bat NVDA 1000 120.50 125.30 8 50

c:\Users\ricks\OneDrive\Documents\GenAI\profit-sharing\.venv\Scripts\python.exe -m src.tools.order_calculator --ticker %1 --holdings %2 --last-price %3 --current-price %4 --sdn %5 --profit %6
