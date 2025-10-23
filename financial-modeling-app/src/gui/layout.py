import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import pandas as pd

from data.fetcher import HistoryFetcher
from models.backtest import run_algorithm_backtest, default_algo, Transaction

DEFAULT_TICKER = "NVDA"
DEFAULT_QTY = 1000
DEFAULT_END = datetime.now().date()
DEFAULT_START = DEFAULT_END - timedelta(days=365)


class FinancialModelingApp:
    def __init__(self, master):
        self.master = master
        master.title("Financial Modeling Application")

        self.fetcher = HistoryFetcher()

        # Main frame
        self.frame = ttk.Frame(master)
        self.frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Input fields
        input_frame = ttk.LabelFrame(self.frame, text="Backtest inputs")
        input_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(input_frame, text="Ticker:").grid(row=0, column=0, sticky="w")
        self.ticker_var = tk.StringVar(value=DEFAULT_TICKER)
        ttk.Entry(input_frame, textvariable=self.ticker_var, width=12).grid(row=0, column=1, sticky="w")

        ttk.Label(input_frame, text="Quantity:").grid(row=0, column=2, sticky="w", padx=(10, 0))
        self.qty_var = tk.IntVar(value=DEFAULT_QTY)
        ttk.Entry(input_frame, textvariable=self.qty_var, width=12).grid(row=0, column=3, sticky="w")

        ttk.Label(input_frame, text="Start Date (YYYY-MM-DD):").grid(row=1, column=0, sticky="w", pady=(5, 0))
        self.start_var = tk.StringVar(value=DEFAULT_START.isoformat())
        ttk.Entry(input_frame, textvariable=self.start_var, width=15).grid(row=1, column=1, sticky="w", pady=(5, 0))

        ttk.Label(input_frame, text="End Date (YYYY-MM-DD):").grid(row=1, column=2, sticky="w", padx=(10, 0), pady=(5, 0))
        self.end_var = tk.StringVar(value=DEFAULT_END.isoformat())
        ttk.Entry(input_frame, textvariable=self.end_var, width=15).grid(row=1, column=3, sticky="w", pady=(5, 0))

        ttk.Label(input_frame, text="Strategy:").grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.strategy_var = tk.StringVar(value="Default - Buy and Hold")
        strategy_box = ttk.Combobox(input_frame, textvariable=self.strategy_var, state="readonly",
                                    values=["Default - Buy and Hold"]) 
        strategy_box.grid(row=2, column=1, sticky="w", pady=(8, 0))

        ttk.Button(input_frame, text="Back-Test", command=self.run_backtest).grid(row=2, column=3, sticky="e", pady=(8, 0))

        # Results area
        results_frame = ttk.Frame(self.frame)
        results_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Transactions list (scrollable)
        trans_frame = ttk.LabelFrame(results_frame, text="Transactions")
        trans_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        self.trans_listbox = tk.Listbox(trans_frame)
        self.trans_listbox.pack(side="left", fill="both", expand=True)
        trans_scroll = ttk.Scrollbar(trans_frame, orient="vertical", command=self.trans_listbox.yview)
        trans_scroll.pack(side="right", fill="y")
        self.trans_listbox.config(yscrollcommand=trans_scroll.set)

        # Summary / output
        summary_frame = ttk.LabelFrame(results_frame, text="Summary")
        summary_frame.pack(side="right", fill="both", expand=True)

        self.summary_text = tk.Text(summary_frame, width=40, height=15, wrap="word")
        self.summary_text.pack(fill="both", expand=True)

    def run_backtest(self):
        ticker = self.ticker_var.get().strip().upper()
        try:
            qty = int(self.qty_var.get())
        except Exception:
            messagebox.showerror("Input error", "Quantity must be an integer.")
            return

        try:
            start_date = datetime.fromisoformat(self.start_var.get()).date()
            end_date = datetime.fromisoformat(self.end_var.get()).date()
        except Exception:
            messagebox.showerror("Input error", "Dates must be in YYYY-MM-DD format.")
            return

        if start_date >= end_date:
            messagebox.showerror("Input error", "Start date must be before end date.")
            return

        # Fetch history (cached)
        try:
            df = self.fetcher.get_history(ticker, start_date, end_date)
        except Exception as e:
            messagebox.showerror("Fetcher error", str(e))
            return

        if df is None or df.empty:
            messagebox.showerror("Data error", f"No price data available for {ticker} in that range.")
            return

        try:
            transactions, summary = run_algorithm_backtest(df, ticker, qty, start_date, end_date, algo=default_algo)
        except Exception as e:
            messagebox.showerror("Backtest error", str(e))
            return

        # Transactions list
        self.trans_listbox.delete(0, tk.END)
        for t in transactions:
            self.trans_listbox.insert(tk.END, t)

        # Summary output (match previous formatting)
        self.summary_text.delete("1.0", tk.END)
        lines = [
            f"Ticker: {summary['ticker']}",
            f"Start Date: {summary['start_date'].isoformat()}",
            f"Start Price: {summary['start_price']:.2f}",
            f"Start Value: {summary['start_value']:.2f}",
            "",
            f"End Date: {summary['end_date'].isoformat()}",
            f"End Price: {summary['end_price']:.2f}",
            f"End Value: {summary['end_value']:.2f}",
            "",
            f"Total return: {summary['total_return']*100:.2f}%",
            f"Annualized return: {summary['annualized']*100:.2f}% (over {summary['years']:.3f} years)",
        ]
        self.summary_text.insert("1.0", "\n".join(lines))


def main():
    root = tk.Tk()
    app = FinancialModelingApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()