"""GUI entry point for the financial modeling application.

Launches the Tkinter-based graphical user interface for interactive
backtesting and analysis.
"""

import tkinter as tk
from typing import List, Optional

from gui.layout import FinancialModelingApp


def main(argv: Optional[List[str]] = None) -> int:
    """Launch the financial modeling GUI application."""
    root = tk.Tk()
    root.title("Financial Modeling Application")
    root.geometry("600x400")

    FinancialModelingApp(root)  # noqa: F841

    root.mainloop()
    return 0


if __name__ == "__main__":
    main()
