# Chart Abstraction Design

## Current State Analysis

### Problems Identified

1. **Finance-Specific Terminology**: Chart functions are named after finance concepts (`plot_portfolio_composition`, `plot_income_bands`) rather than quantitative visualization types
2. **Inconsistent Display Mechanism**: Mix of `plt.show()`, `plt.savefig()`, and manual backend selection
3. **Color Schemes Duplicated**: `ASSET_COLORS` defined separately in multiple files with slight variations
4. **Data Contracts Unclear**: Each chart function expects specific DataFrame column names, making them brittle
5. **Mixed Responsibilities**: Chart functions handle both data transformation AND visualization

### Existing Chart Functions

| Current Function | What It Really Is | Data Dependencies |
|-----------------|-------------------|-------------------|
| `plot_portfolio_composition()` | Stacked area chart | `{ticker}_value` columns + allocations dict |
| `plot_income_bands()` | Stacked area chart | Asset columns + `expenses`/`cash` columns |
| `plot_price_with_trades()` | Line chart with scatter overlay | `Close` column + transaction strings |
| `plot_portfolio_comparison()` | Multi-panel: line chart + stacked area | Multiple result dicts |

---

## Proposed Architecture

### Core Principle: Separation of Concerns

```
┌─────────────────────────────────────────────────────────────┐
│ DATA LAYER │
│ - Business logic generates domain-specific data │
│ - Responsible for: calculations, aggregations, filtering │
└─────────────────────────────────────────────────────────────┘
 ↓
┌─────────────────────────────────────────────────────────────┐
│ CHART CONTRACT LAYER (NEW) │
│ - Transforms domain data → neutral chart data │
│ - Defines standard data contracts for each chart type │
│ - Example: series=[{"label": "VOO", "values": [...]}] │
└─────────────────────────────────────────────────────────────┘
 ↓
┌─────────────────────────────────────────────────────────────┐
│ VISUALIZATION LAYER (CLEANED) │
│ - Pure chart rendering functions │
│ - No business logic, no data transformation │
│ - No finance-specific terminology │
└─────────────────────────────────────────────────────────────┘
 ↓
┌─────────────────────────────────────────────────────────────┐
│ DISPLAY LAYER (UNIFIED) │
│ - Single mechanism for showing/saving charts │
│ - Platform-aware: shell execute on Windows, GUI on Linux │
└─────────────────────────────────────────────────────────────┘
```

---

## Chart Type Taxonomy

### 1. Stacked Area Chart (with Positive/Negative Split)
**Neutral Name**: `create_stacked_area_chart()`

**Data Contract**:
```python
@dataclass
class StackedAreaData:
 """Data for stacked area chart with optional positive/negative split."""
 dates: List[datetime] # X-axis
 positive_series: List[SeriesData] # Stacked above zero (bottom to top)
 negative_series: List[SeriesData] = [] # Stacked below zero (top to bottom)

@dataclass
class SeriesData:
 label: str # Series name for legend
 values: List[float] # Y values (same length as dates)
 color: Optional[str] = None # Hex color (auto-assigned if None)
```

**Visual Layout**:
```
┌─────────────────────────────────┐
│ BTC-USD (Crypto) │ ← Top band (most volatile)
│ VOO (Equities) │
│ BIL (Bonds) │
│ USD (Cash/Sweeps) │ ← Bottom of positive (least volatile)
├─────────────────────────────────┤ ← Zero line
│ Withdrawals (spending power) │ ← Negative band (below zero)
└─────────────────────────────────┘

Total Horn Height = Sum(positive_series) + Sum(negative_series)
Narrow Neck = Point where USD cash (sweeps account) is smallest

Note: USD cash is the SWEEPS ACCOUNT (buying power for trading),
distinct from BIL position (Treasury bill holdings).
```

**Key Insight**: Withdrawals appear as a **growing wedge below zero**, representing accumulated spending power. The zero line is just a visual separator - both sides represent positive wealth (what you have + what you spent).

**Use Cases**:
- Portfolio composition over time
- Income streams over time
- Any multi-component total over time

**Example**:
```python
data = StackedAreaData(
 dates=[date(2024, 1, 1), date(2024, 2, 1), ...],
 series=[
 SeriesData(label="VOO", values=[60000, 61000, ...], color="#ff7f0e"),
 SeriesData(label="BIL", values=[40000, 40500, ...], color="#2ca02c"),
 ]
)
create_stacked_area_chart(
 data=data,
 title="Portfolio Composition",
 y_label="Value ($)",
 output="composition.png"
)
```

### 2. Line Chart with Scatter Overlay
**Neutral Name**: `create_line_with_markers_chart()`

**Data Contract**:
```python
@dataclass
class LineWithMarkersData:
 """Data for line chart with scatter points."""
 dates: List[datetime] # X-axis
 line: SeriesData # Main line plot
 markers: List[MarkerData] # Scatter points

@dataclass
class MarkerData:
 date: datetime
 value: float
 label: str # For legend grouping (e.g., "BUY", "SELL")
 color: Optional[str] = None
```

**Use Cases**:
- Price with buy/sell markers
- Metric with event annotations

**Example**:
```python
data = LineWithMarkersData(
 dates=[date(2024, 1, 1), ...],
 line=SeriesData(label="NVDA Price", values=[120.0, 121.5, ...]),
 markers=[
 MarkerData(date(2024, 1, 15), 125.0, "BUY", "#ff0000"),
 MarkerData(date(2024, 2, 10), 135.0, "SELL", "#00ff00"),
 ]
)
create_line_with_markers_chart(
 data=data,
 title="Price with Transactions",
 y_label="Price ($)",
 output="trades.png"
)
```

### 3. Multi-Panel Chart
**Neutral Name**: `create_multi_panel_chart()`

**Data Contract**:
```python
@dataclass
class MultiPanelData:
 """Data for multi-panel chart."""
 panels: List[PanelData]
 layout: Tuple[int, int] # (rows, cols)

@dataclass
class PanelData:
 title: str
 chart_type: str # "line", "stacked_area", etc.
 data: Any # Type depends on chart_type
```

**Use Cases**:
- Portfolio comparison (total value + composition)
- Multi-metric dashboards

---

## Unified Display Mechanism

### Platform-Aware Display

```python
def display_chart(output_file: str) -> None:
 """Display chart using platform-appropriate method.

 - Windows: shell execute (opens in default viewer)
 - Linux: matplotlib.pyplot.show() in background thread
 - Headless: no-op (file already saved)
 """
 if not os.path.exists(output_file):
 raise FileNotFoundError(f"Chart file not found: {output_file}")

 if sys.platform == "win32":
 # Windows: shell execute
 os.startfile(output_file)
 elif os.environ.get("DISPLAY"):
 # Linux with X11: show in GUI window
 # (matplotlib already showed it, or we can re-open)
 pass
 else:
 # Headless: just print path
 print(f"Chart saved to: {output_file}")
```

### Chart Creation Pattern

All chart functions follow this pattern:

```python
def create_xxx_chart(
 data: XxxData,
 title: str,
 y_label: str,
 output: Optional[str] = None,
 **kwargs
) -> str:
 """Create xxx chart.

 Args:
 data: Chart data (type-checked dataclass)
 title: Chart title
 y_label: Y-axis label
 output: Output file path (PNG/PDF). If None, generates temp file.
 **kwargs: Additional matplotlib customization

 Returns:
 Path to output file
 """
 # 1. Validate data
 if not isinstance(data, XxxData):
 raise TypeError(f"Expected XxxData, got {type(data)}")

 # 2. Create matplotlib figure
 fig, ax = plt.subplots(...)

 # 3. Render chart (pure visualization, no business logic)
 ...

 # 4. Save to file
 if output is None:
 output = tempfile.mktemp(suffix=".png")
 plt.savefig(output, dpi=150, bbox_inches="tight")
 plt.close(fig)

 # 5. Return path (caller decides whether to display)
 return output
```

---

## Color Scheme Unification

### Central Color Registry

```python
# src/visualization/colors.py

# Semantic color categories
CHART_COLORS = {
 "primary": "#1f77b4",
 "secondary": "#ff7f0e",
 "success": "#2ca02c",
 "danger": "#d62728",
 "warning": "#ff9800",
 "info": "#17a2b8",
}

# Asset-specific colors (optional, for backwards compatibility)
ASSET_COLORS = {
 "BTC-USD": "#f7931a", # Bitcoin orange
 "ETH-USD": "#627eea", # Ethereum purple
 "VOO": "#ff7f0e",
 "BIL": "#2ca02c",
 # ... etc
}

def get_chart_color(index: int) -> str:
 """Get color from standard palette by index."""
 palette = [
 "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
 "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
 ]
 return palette[index % len(palette)]

def get_asset_color(ticker: str, fallback_index: int = 0) -> str:
 """Get color for asset ticker, with fallback to palette."""
 return ASSET_COLORS.get(ticker, get_chart_color(fallback_index))
```

---

## Migration Strategy

### Phase 1: Create New Abstraction
1. Create `src/charts/` directory (new, separate from `src/visualization/`)
2. Implement core chart types with clean data contracts
3. Add tests for each chart type
4. Document data contracts

### Phase 2: Add Adapter Layer
1. Create adapters that transform existing calls to new format
2. Example: `plot_portfolio_composition()` becomes thin wrapper around `create_stacked_area_chart()`
3. Maintain backwards compatibility

### Phase 3: Migrate Call Sites
1. Update research scripts to use new chart functions directly
2. Update tools to use new chart functions
3. Deprecate old functions with warnings

### Phase 4: Remove Old Code
1. Delete deprecated functions after one release cycle
2. Move old code to `src/visualization/_deprecated/`

---

## Benefits

### For Users
- **Consistent**: All charts created/displayed the same way
- **Predictable**: Clear data contracts, typed inputs
- **Flexible**: Easy to customize without touching chart code

### For Developers
- **Testable**: Pure functions with clear inputs/outputs
- **Reusable**: Chart types work for any domain
- **Maintainable**: Business logic separated from visualization

### For AI Assistants
- **Discoverable**: Clear type contracts make correct usage obvious
- **Composable**: Can combine chart types without understanding finance domain
- **Extensible**: Adding new chart types follows clear pattern

---

## Example: Before vs After

### Before (Current)
```python
# Caller must know DataFrame column naming conventions
daily_values = result['daily_values'] # Has {ticker}_value columns
allocations = {'VOO': 0.6, 'BIL': 0.4}

plot_portfolio_composition(
 daily_values=daily_values, # Finance-specific
 allocations=allocations, # Finance-specific
 output_file="chart.png",
 show_percentage=False
)
# Chart is saved, but not displayed automatically
```

### After (Proposed)
```python
# Caller transforms data to neutral format
chart_data = StackedAreaData(
 dates=result['dates'],
 series=[
 SeriesData("VOO", result['voo_values']),
 SeriesData("BIL", result['bil_values']),
 ]
)

output = create_stacked_area_chart(
 data=chart_data,
 title="Portfolio Composition",
 y_label="Value ($)"
)
display_chart(output) # Platform-aware display
```

---

## Open Questions

1. **Should we use dataclasses or TypedDict?**
 - Dataclasses: Better typing, validation
 - TypedDict: More flexible, easier migration

2. **Should chart creation return path or display automatically?**
 - Return path: More control, explicit display
 - Auto-display: More convenient, less code

3. **Should we support matplotlib figure customization?**
 - Yes via kwargs: Flexible but leaky abstraction
 - No: Clean but less powerful

4. **Should colors be in data or rendering?**
 - In data (SeriesData.color): More control
 - In rendering: More consistent, less duplication

---

## Next Steps

1. Review and approve this design
2. Create `src/charts/` module structure
3. Implement `create_stacked_area_chart()` as proof of concept
4. Test with existing portfolio composition use case
5. Iterate based on feedback

