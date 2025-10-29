"""GUI entry point for the financial modeling application.

Launches the Tkinter-based graphical user interface for interactive
backtesting and analysis.
"""

import tkinter as tk

from gui.layout import FinancialModelingApp


def main():
    """Launch the financial modeling GUI application."""
    root = tk.Tk()
    root.title("Financial Modeling Application")
    root.geometry("600x400")

    FinancialModelingApp(root)  # noqa: F841

    root.mainloop()


if __name__ == "__main__":
    main()
