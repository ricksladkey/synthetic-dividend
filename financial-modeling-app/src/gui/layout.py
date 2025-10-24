"""Tkinter GUI for interactive backtesting.

Provides visual interface for running trading algorithms with input fields
for ticker, dates, strategy selection, and displays transaction log with summary statistics.
"""

import tkinter as tk
from datetime import date, datetime, timedelta
from tkinter import messagebox, ttk
from typing import Any, Dict, List

import pandas as pd

from data.fetcher import HistoryFetcher
from models.backtest import build_algo_from_name, run_algorithm_backtest

# Default parameter values for GUI initialization
DEFAULT_TICKER: str = "NVDA"
DEFAULT_QTY: int = 10000
DEFAULT_END: date = datetime.now().date()
DEFAULT_START: date = DEFAULT_END - timedelta(days=365)


class FinancialModelingApp:
    """Main GUI application for backtesting trading strategies.

    Provides input fields for:
    - Ticker symbol and quantity
    - Start/end date range
    - Strategy selection (buy-and-hold, synthetic dividend variants)

    Displays:
    - Transaction log (scrollable list)
    - Summary statistics (returns, holdings, bank balance)
    """

    def __init__(self, master: tk.Tk) -> None:
        """Initialize GUI with default values and layout.

        Args:
            master: Root Tkinter window
        """
        self.master: tk.Tk = master
        master.title("Financial Modeling Application")

        # Data fetcher with disk cache
        self.fetcher: HistoryFetcher = HistoryFetcher()

        # Tkinter variables for input fields
        self.ticker_var: tk.StringVar
        self.qty_var: tk.IntVar
        self.start_var: tk.StringVar
        self.end_var: tk.StringVar
        self.strategy_var: tk.StringVar

        # Widgets for output display
        self.trans_listbox: tk.Listbox
        self.summary_text: tk.Text

        # Main container frame
        self.frame: ttk.Frame = ttk.Frame(master)
        self.frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Input section: ticker, quantity, dates, strategy
        input_frame: ttk.LabelFrame = ttk.LabelFrame(self.frame, text="Backtest inputs")
        input_frame.pack(fill="x", padx=5, pady=5)

        # Row 0: Ticker and Quantity
        ttk.Label(input_frame, text="Ticker:").grid(row=0, column=0, sticky="w")
        self.ticker_var = tk.StringVar(value=DEFAULT_TICKER)
        ttk.Entry(input_frame, textvariable=self.ticker_var, width=12).grid(
            row=0, column=1, sticky="w"
        )

        ttk.Label(input_frame, text="Quantity:").grid(row=0, column=2, sticky="w", padx=(10, 0))
        self.qty_var = tk.IntVar(value=DEFAULT_QTY)
        ttk.Entry(input_frame, textvariable=self.qty_var, width=12).grid(
            row=0, column=3, sticky="w"
        )

        # Row 1: Start and End dates (ISO format: YYYY-MM-DD)
        ttk.Label(input_frame, text="Start Date (YYYY-MM-DD):").grid(
            row=1, column=0, sticky="w", pady=(5, 0)
        )
        self.start_var = tk.StringVar(value=DEFAULT_START.isoformat())
        ttk.Entry(input_frame, textvariable=self.start_var, width=15).grid(
            row=1, column=1, sticky="w", pady=(5, 0)
        )

        ttk.Label(input_frame, text="End Date (YYYY-MM-DD):").grid(
            row=1, column=2, sticky="w", padx=(10, 0), pady=(5, 0)
        )
        self.end_var = tk.StringVar(value=DEFAULT_END.isoformat())
        ttk.Entry(input_frame, textvariable=self.end_var, width=15).grid(
            row=1, column=3, sticky="w", pady=(5, 0)
        )

        # Row 2: Strategy dropdown and Run button
        ttk.Label(input_frame, text="Strategy:").grid(row=2, column=0, sticky="w", pady=(8, 0))
        # Strategy identifiers: parameters embedded in string (e.g., "sd-9.15,50")
        self.strategy_var = tk.StringVar(value="buy-and-hold")
        strategy_box: ttk.Combobox = ttk.Combobox(
            input_frame,
            textvariable=self.strategy_var,
            state="readonly",
            values=["buy-and-hold", "sd-9.15,50"],
        )
        strategy_box.grid(row=2, column=1, sticky="w", pady=(8, 0))

        # Run button triggers backtest execution
        ttk.Button(input_frame, text="Back-Test", command=self.run_backtest).grid(
            row=2, column=3, sticky="e", pady=(8, 0)
        )

        # Results area: two-column layout for transactions and summary
        results_frame: ttk.Frame = ttk.Frame(self.frame)
        results_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Left column: Transaction log (scrollable list)
        trans_frame: ttk.LabelFrame = ttk.LabelFrame(results_frame, text="Transactions")
        trans_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        self.trans_listbox = tk.Listbox(trans_frame)
        self.trans_listbox.pack(side="left", fill="both", expand=True)

        # Vertical scrollbar for transaction list
        trans_scroll: ttk.Scrollbar = ttk.Scrollbar(
            trans_frame, orient="vertical", command=self.trans_listbox.yview
        )
        trans_scroll.pack(side="right", fill="y")
        self.trans_listbox.config(yscrollcommand=trans_scroll.set)

        # Right column: Summary statistics (text widget)
        summary_frame: ttk.LabelFrame = ttk.LabelFrame(results_frame, text="Summary")
        summary_frame.pack(side="right", fill="both", expand=True)

        self.summary_text = tk.Text(summary_frame, width=40, height=15, wrap="word")
        self.summary_text.pack(fill="both", expand=True)

    def run_backtest(self) -> None:
        """Event handler for Back-Test button click.

        Workflow:
        1. Validate and parse user inputs (ticker, quantity, dates)
        2. Fetch historical price data via HistoryFetcher
        3. Build algorithm instance from strategy string
        4. Execute backtest via run_algorithm_backtest()
        5. Display transaction log and summary statistics in GUI

        Shows error dialogs for invalid inputs or execution failures.
        """
        # Parse ticker symbol (uppercase, trimmed)
        ticker: str = self.ticker_var.get().strip().upper()

        # Parse quantity as integer
        try:
            qty: int = int(self.qty_var.get())
        except Exception:
            messagebox.showerror("Input error", "Quantity must be an integer.")
            return

        # Parse dates in ISO format (YYYY-MM-DD)
        try:
            start_date: date = datetime.fromisoformat(self.start_var.get()).date()
            end_date: date = datetime.fromisoformat(self.end_var.get()).date()
        except Exception:
            messagebox.showerror("Input error", "Dates must be in YYYY-MM-DD format.")
            return

        # Validate date range ordering
        if start_date >= end_date:
            messagebox.showerror("Input error", "Start date must be before end date.")
            return

        # Fetch historical data (uses disk cache for efficiency)
        try:
            df: pd.DataFrame = self.fetcher.get_history(ticker, start_date, end_date)
        except Exception as e:
            messagebox.showerror("Fetcher error", str(e))
            return

        # Validate data availability
        if df is None or df.empty:
            messagebox.showerror(
                "Data error", f"No price data available for {ticker} in that range."
            )
            return

        # Build algorithm instance from strategy identifier string
        algo_inst = build_algo_from_name(self.strategy_var.get())

        # Execute backtest and collect results
        try:
            transactions: List[str]
            summary: Dict[str, Any]
            transactions, summary = run_algorithm_backtest(
                df, ticker, qty, start_date, end_date, algo=algo_inst
            )
        except Exception as e:
            messagebox.showerror("Backtest error", str(e))
            return

        # Populate transaction log listbox (clear existing, insert new)
        self.trans_listbox.delete(0, tk.END)
        for t in transactions:
            self.trans_listbox.insert(tk.END, t)

        # Format summary statistics as multi-line text
        self.summary_text.delete("1.0", tk.END)
        lines: List[str] = [
            f"Ticker: {summary['ticker']}",
            f"Start Date: {summary['start_date'].isoformat()}",
            f"Start Price: {summary['start_price']:.2f}",
            f"Start Value: {summary['start_value']:.2f}",
            "",
            f"End Date: {summary['end_date'].isoformat()}",
            f"End Price: {summary['end_price']:.2f}",
            f"End Value: {summary['end_value']:.2f}",
            f"Holdings: {summary.get('holdings', qty)} shares",
            "",
            f"Bank: {summary.get('bank', 0.0):.2f}",
            f"Total (holdings + bank): {summary.get('total', summary['end_value']):.2f}",
            "",
            f"Total return: {summary['total_return']*100:.2f}%",
            f"Annualized return: {summary['annualized']*100:.2f}% (over {summary['years']:.3f} years)",
        ]
        # Insert formatted text into summary widget
        self.summary_text.insert("1.0", "\n".join(lines))


def main() -> None:
    """Entry point: create root window and start Tkinter event loop."""
    root: tk.Tk = tk.Tk()
    FinancialModelingApp(root)  # noqa: F841
    root.mainloop()


if __name__ == "__main__":
    main()
