# Naming Convention

> **Note (October 2025)**: This document describes the legacy slash/percent notation (`sd/9.05%/50%`). The project has migrated to a cleaner comma-based format (`sd-9.05,50`). See updated examples in README.md and source code. Legacy format is still supported for backward compatibility.

This document establishes the consistent naming convention for the synthetic dividend algorithm throughout the codebase.

## Core Principle

**Verbosity in code, terseness in identifiers.**

- **Internal Code**: Use full descriptive names (`SyntheticDividendAlgorithm`, `calculate_synthetic_dividend_orders()`)
- **User-Facing Identifiers**: Use abbreviated form with comma-based parameters (`sd-9.05,50`, `sd-ath-only-9.05,50`)
- **Legacy Format**: Slash/percent notation (`sd/9.05%/50%`) still supported for backward compatibility

## User-Facing Identifiers

### Command Line Arguments
```powershell
# Full algorithm with buyback
python -m src.run_model NVDA 10/22/2024 10/22/2025 "sd/9.05%/50%"

# ATH-only variant (no buyback)
python -m src.run_model NVDA 10/22/2024 10/22/2025 "sd-ath-only/9.05%/50%"
```

### Batch Files
- `test-sd.bat` - Test full algorithm
- `test-sd-ath-only.bat` - Test ATH-only variant
- `compare-algorithms.bat` - Run both for comparison

### GUI Dropdown
```python
values=["buy-and-hold", "sd/9.15%/50%"]
```

### Visualization Labels
- "SD (9.05%/50%)" - Full algorithm
- "SD ATH-Only (9.05%/50%)" - ATH-only variant
- "Buy and Hold" - Baseline

### Documentation
When referring to the algorithm in prose:
- "synthetic dividend" (lowercase, spelled out)
- "SD" when used as an abbreviation in tables/charts
- "sd" in command examples

## Internal Code

### Class Names
```python
class SyntheticDividendAlgorithm(AlgorithmBase):
    """Full descriptive name for clarity"""
    pass
```

### Function Names
```python
def calculate_synthetic_dividend_orders(...):
    """Verbose function names aid comprehension"""
    pass
```

### Variable Names
```python
# Use full words for algorithm state
self.rebalance_size_pct = rebalance_size_pct
self.profit_sharing_pct = profit_sharing_pct
self.buyback_enabled = buyback_enabled
```

## Backward Compatibility

The parser accepts both abbreviated and legacy verbose forms:

```python
# Modern abbreviated form (preferred)
build_algo_from_name("sd/9.05%/50%")
build_algo_from_name("sd-ath-only/9.05%/50%")

# Legacy verbose form (still supported)
build_algo_from_name("synthetic-dividend/9.05%/50%")
build_algo_from_name("synthetic-dividend-ath-only/9.05%/50%")
```

This ensures existing scripts and saved configurations continue to work.

## Rationale

This convention follows best practices in software engineering:

1. **Code Readability**: Internal code uses descriptive names that make the purpose immediately clear to developers
2. **User Efficiency**: Command-line and GUI interfaces use concise identifiers that are quick to type and read
3. **Mathematical Tradition**: Academic and financial literature often uses abbreviated notation (e.g., "BS model" for Black-Scholes)
4. **Maintainability**: Clear separation between internal and external naming makes refactoring easier
5. **Backward Compatibility**: Supporting legacy names ensures smooth migration

## Examples in Context

### CLI Usage
```powershell
# Quick and concise
.\test-sd.bat
.\test-sd-ath-only.bat
.\compare-algorithms.bat
```

### Comparison Table Output
```
Algorithm                    Shares      Value          Bank         Total
------------------------------------------------------------------------------
Buy and Hold                10,000   $1,802,800         $0     $1,802,800
SD (9.05%/50%)               8,989   $1,620,537   $236,493     $1,857,030
SD ATH-Only (9.05%/50%)      8,806   $1,587,546   $203,351     $1,790,897
```

### Code Implementation
```python
class SyntheticDividendAlgorithm(AlgorithmBase):
    """
    Algorithm that generates synthetic dividends through volatility harvesting.
    
    Uses clear, descriptive naming internally for maintainability.
    """
    
    def calculate_synthetic_dividend_orders(
        self,
        holdings: int,
        rebalance_size_pct: float,
        profit_sharing_pct: float
    ) -> tuple[int, int]:
        """
        Calculate buy and sell quantities for synthetic dividend strategy.
        
        Verbose parameter names make the math formulas self-documenting.
        """
        # Implementation...
        pass
```

## Migration Guide

When updating existing code:

1. **Do change**: CLI arguments, batch file names, GUI labels, chart titles
2. **Don't change**: Python class names, function names, variable names
3. **Optional**: Add support for abbreviated form while keeping legacy support
4. **Document**: Update examples in README and documentation to show abbreviated form

## Summary

- **Commands**: `sd`, `sd-ath-only`
- **Classes**: `SyntheticDividendAlgorithm`
- **Functions**: `calculate_synthetic_dividend_orders()`
- **Documentation**: "synthetic dividend" (prose), "SD" (tables/charts)
