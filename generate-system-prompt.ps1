# Generate concatenated system prompt from theory documentation
#
# Usage:
#   .\generate-system-prompt.ps1 [-Mode quick|full]

param(
    [ValidateSet('quick', 'full')]
    [string]$Mode = 'full'
)

$OutputDir = ".\output"
New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

Write-Host "Generating system prompt (mode: $Mode)..." -ForegroundColor Cyan

if ($Mode -eq 'quick') {
    $OutputFile = Join-Path $OutputDir "system-prompt-quick.md"
    
    "# Synthetic Dividend Algorithm - Quick Theory Reference" | Set-Content $OutputFile
    "" | Add-Content $OutputFile
    "This is a condensed system prompt containing the essential theoretical foundation." | Add-Content $OutputFile
    "" | Add-Content $OutputFile
    "---" | Add-Content $OutputFile
    "" | Add-Content $OutputFile
    
    Get-Content "theory\INVESTING_THEORY.md" | Add-Content $OutputFile
    "" | Add-Content $OutputFile
    "---" | Add-Content $OutputFile
    "" | Add-Content $OutputFile
    Get-Content "theory\VOLATILITY_ALPHA_THESIS.md" | Add-Content $OutputFile
    
    $lineCount = (Get-Content $OutputFile | Measure-Object -Line).Lines
    Write-Host "Done! Quick system prompt generated: $OutputFile" -ForegroundColor Green
    Write-Host "  Total lines: $lineCount" -ForegroundColor Gray
    
} else {
    $OutputFile = Join-Path $OutputDir "system-prompt-full.md"
    
    "# Synthetic Dividend Algorithm - Complete Theoretical Framework" | Set-Content $OutputFile
    "" | Add-Content $OutputFile
    "Generated from theory/ folder documentation." | Add-Content $OutputFile
    "" | Add-Content $OutputFile
    "---" | Add-Content $OutputFile
    "" | Add-Content $OutputFile
    
    # Concatenate in recommended reading order
    "## 1. Core Investment Theory" | Add-Content $OutputFile
    "" | Add-Content $OutputFile
    Get-Content "theory\INVESTING_THEORY.md" | Add-Content $OutputFile
    "" | Add-Content $OutputFile
    "---" | Add-Content $OutputFile
    "" | Add-Content $OutputFile
    
    "## 2. Mathematical Foundations (Volatility Alpha Thesis)" | Add-Content $OutputFile
    "" | Add-Content $OutputFile
    Get-Content "theory\VOLATILITY_ALPHA_THESIS.md" | Add-Content $OutputFile
    "" | Add-Content $OutputFile
    "---" | Add-Content $OutputFile
    "" | Add-Content $OutputFile
    
    "## 3. Metrics Interpretation Framework" | Add-Content $OutputFile
    "" | Add-Content $OutputFile
    Get-Content "theory\RETURN_METRICS_ANALYSIS.md" | Add-Content $OutputFile
    "" | Add-Content $OutputFile
    "---" | Add-Content $OutputFile
    "" | Add-Content $OutputFile
    
    "## 4. Opportunity Cost Theory" | Add-Content $OutputFile
    "" | Add-Content $OutputFile
    Get-Content "theory\INITIAL_CAPITAL_THEORY.md" | Add-Content $OutputFile
    "" | Add-Content $OutputFile
    "---" | Add-Content $OutputFile
    "" | Add-Content $OutputFile
    
    "## 5. Multi-Stock Portfolio Vision" | Add-Content $OutputFile
    "" | Add-Content $OutputFile
    Get-Content "theory\PORTFOLIO_VISION.md" | Add-Content $OutputFile
    "" | Add-Content $OutputFile
    "---" | Add-Content $OutputFile
    "" | Add-Content $OutputFile
    
    "## 6. Development Philosophy" | Add-Content $OutputFile
    "" | Add-Content $OutputFile
    Get-Content "theory\CODING_PHILOSOPHY.md" | Add-Content $OutputFile
    
    $lineCount = (Get-Content $OutputFile | Measure-Object -Line).Lines
    Write-Host "Done! Full system prompt generated: $OutputFile" -ForegroundColor Green
    Write-Host "  Total lines: $lineCount" -ForegroundColor Gray
}

Write-Host ""
Write-Host "You can now use this file as a system prompt for AI assistants." -ForegroundColor Yellow
Write-Host "To copy to clipboard: Get-Content $OutputFile | Set-Clipboard" -ForegroundColor Gray
