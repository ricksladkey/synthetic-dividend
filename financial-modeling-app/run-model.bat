@echo off
REM run-model.bat TICKER START_DATE END_DATE STRATEGY_NAME
if "%~1"=="" (
  echo Usage: run-model.bat TICKER START_DATE END_DATE STRATEGY_NAME
  exit /b 2
)

set SCRIPT_DIR=%~dp0\src
REM try venv in financial-modeling-app\.venv first, then repo parent .venv
set VENV_PY=%~dp0\.venv\Scripts\python.exe
if not exist "%VENV_PY%" (
  set VENV_PY=%~dp0\..\.venv\Scripts\python.exe
)

if not exist "%VENV_PY%" (
  REM fallback to system python
  set VENV_PY=python
)

REM Pass arguments properly, using %~4 to handle quoted strings with special chars
"%VENV_PY%" "%SCRIPT_DIR%\run_model.py" %1 %2 %3 %~4 %5 %6 %7 %8 %9
exit /b %ERRORLEVEL%
