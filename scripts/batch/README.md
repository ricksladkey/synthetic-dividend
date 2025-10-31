# Research Scripts

This folder contains batch scripts for running various research analyses on the synthetic dividend algorithm.

## Available Scripts

### 1. optimal-rebalancing.bat
**Source:** `src/research/optimal_rebalancing.py`  
**Purpose:** Phase 1 core dataset analysis - tests all asset classes with various sdN values  
**Output:** `research_phase1_1year_core.csv`

Tests:
- 12 assets (NVDA, GOOG, PLTR, MSTR, SHOP, BTC-USD, ETH-USD, GLD, SLV, SPY, QQQ, DIA)
- 7 sdN values (sd4, sd6, sd8, sd10, sd12, sd16, sd20)
- 50% profit sharing
- 1-year historical period

**Run time:** ~20-30 minutes (84 backtests)

### 2. volatility-alpha.bat
**Source:** `src/research/volatility_alpha.py`  
**Purpose:** Compares Enhanced (with buybacks) vs ATH-only (no buybacks) to quantify volatility harvesting  
**Output:** `volatility_alpha_1year_core.csv`

Metrics:
- Total return comparison
- Volatility alpha (Enhanced - ATH-only)
- Transaction counts
- Final portfolio values

**Run time:** ~10-15 minutes (comprehensive analysis across 12 assets)

### 3. profit-sharing-composition.bat
**Source:** `src/research/profit_sharing_composition.py`  
**Purpose:** Explores how profit-sharing ratios affect holdings composition over time  
**Output:** `output/profit_sharing_composition_NVDA.png` (chart)

Analysis:
- Profit sharing range: -25% to +125% (5% increments)
- 4 visualization panels:
  * Share holdings over time
  * Cash balance over time
  * Total portfolio value over time
  * Capital utilization over time

**Run time:** ~5-10 minutes (31 backtests with visualization)

## Usage

Simply double-click any `.bat` file to run the corresponding analysis. Results will be saved to the workspace root or `output/` folder as indicated.

## File Organization

```
research/
├── README.md                           # This file
├── optimal-rebalancing.bat             # Phase 1 core analysis
├── volatility-alpha.bat                # Volatility harvesting quantification
└── profit-sharing-composition.bat      # Composition over time analysis

src/research/
├── __init__.py
├── optimal_rebalancing.py              # Python source
├── volatility_alpha.py                 # Python source
├── profit_sharing_composition.py       # Python source
└── asset_classes.py                    # Asset definitions
```

## Requirements

All scripts use the virtual environment Python interpreter:
```
C:/build/synthetic-dividend/.venv/Scripts/python.exe
```

Ensure the virtual environment is set up and dependencies are installed:
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Notes

- All scripts use historical date ranges to avoid Yahoo Finance weekend data gaps
- Default period: 10/23/2023 - 10/23/2024 (1 year)
- Standard parameters: 50% profit sharing, 10,000 initial shares
- Results are cached in `src/cache/` to speed up repeated runs

## Documentation

See also:
- `../theory/RESEARCH_PLAN.md` - Overall research strategy
- `../theory/VOLATILITY_ALPHA_THESIS.md` - Theory behind volatility harvesting
- `../theory/PROFIT_SHARING_ANALYSIS_RESULTS.md` - Findings from composition analysis
- `../theory/RETURN_METRICS_ANALYSIS.md` - Capital deployment metrics framework
