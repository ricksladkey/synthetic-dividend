@echo off
REM Generate core concepts system prompt from consolidated theory documentation
REM
REM Usage:
REM   generate-core-prompt.bat
REM
REM This creates a focused prompt with the essential theoretical foundation:
REM - Core concepts (dividend illusion, time machine effect, volatility as asset class)
REM - Algorithm variants (all four including new ATH-Sell)
REM - Mathematical framework (volatility alpha formula and validation)

echo Generating core concepts system prompt...

if not exist "output" mkdir output

set OUTPUT_FILE=output\system-prompt-core.md

echo # Synthetic Dividend Algorithm - Core Theory Prompt > "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"
echo This prompt contains the essential theoretical foundation for understanding >> "%OUTPUT_FILE%"
echo the Synthetic Dividend Algorithm and its four variants. >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"
echo Generated from consolidated theory documentation. >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"
echo --- >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"

echo ## 1. Core Concepts >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"
type theory\01-core-concepts.md >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"
echo --- >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"

echo ## 2. Algorithm Variants >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"
type theory\02-algorithm-variants.md >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"
echo --- >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"

echo ## 3. Mathematical Framework >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"
type theory\03-mathematical-framework.md >> "%OUTPUT_FILE%"

for /f %%a in ('find /c /v "" ^< "%OUTPUT_FILE%"') do set "lineCount=%%a"
echo Done! Core system prompt generated: %OUTPUT_FILE%
echo Total lines: %lineCount%
echo.
echo You can now use this file as a system prompt for AI assistants.
echo Example: type %OUTPUT_FILE% ^| clip