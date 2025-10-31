@echo off
REM Generate complete system prompt from consolidated theory documentation
REM
REM Usage:
REM   generate-full-prompt.bat
REM
REM This creates a comprehensive prompt with the complete theoretical framework:
REM - All 7 consolidated theory documents
REM - Complete context for AI assistants working on the project

echo Generating complete system prompt...

if not exist "output" mkdir output

set OUTPUT_FILE=output\system-prompt-full.md

echo # Synthetic Dividend Algorithm - Complete Theoretical Framework > "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"
echo This is a comprehensive system prompt containing the complete theoretical foundation >> "%OUTPUT_FILE%"
echo for the Synthetic Dividend Algorithm. Use this to provide full context to AI assistants >> "%OUTPUT_FILE%"
echo working on this project. >> "%OUTPUT_FILE%"
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
echo. >> "%OUTPUT_FILE%"
echo --- >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"

echo ## 4. Income Generation >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"
type theory\04-income-generation.md >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"
echo --- >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"

echo ## 5. Implementation Details >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"
type theory\05-implementation-details.md >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"
echo --- >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"

echo ## 6. Applications and Use Cases >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"
type theory\06-applications-use-cases.md >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"
echo --- >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"

echo ## 7. Research and Validation >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"
type theory\07-research-validation.md >> "%OUTPUT_FILE%"

for /f %%a in ('find /c /v "" ^< "%OUTPUT_FILE%"') do set "lineCount=%%a"
echo Done! Complete system prompt generated: %OUTPUT_FILE%
echo Total lines: %lineCount%
echo.
echo You can now use this file as a system prompt for AI assistants.
echo Example: type %OUTPUT_FILE% ^| clip