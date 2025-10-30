"""Chart abstraction layer - neutral, reusable visualization components.

This module provides clean, domain-neutral chart creation functions with
type-safe data contracts. Charts are defined by their quantitative structure
(stacked area, line with markers) not their business purpose (portfolio, income).

Key principles:
- Separation of concerns: data transformation separate from rendering
- Neutral terminology: "stacked area" not "portfolio composition"
- Type-safe contracts: dataclasses define clear input/output
- Platform-aware display: unified mechanism for showing/saving

Available chart types:
- create_stacked_area_chart: For multi-component totals over time
- create_line_with_markers_chart: For time series with event annotations
- create_multi_panel_chart: For side-by-side comparisons
"""

from src.charts.stacked_area import (
    SeriesData,
    StackedAreaData,
    create_stacked_area_chart,
)

__all__ = [
    "SeriesData",
    "StackedAreaData",
    "create_stacked_area_chart",
]
