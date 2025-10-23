@echo off
REM Compare full synthetic-dividend with ATH-only variant
CALL run-model.bat NVDA 10/22/2024 10/22/2025 synthetic-dividend/9.05%%%%/50%%%%
echo.
echo ======================================
echo.
CALL run-model.bat NVDA 10/22/2024 10/22/2025 synthetic-dividend-ath-only/9.05%%%%/50%%%%
