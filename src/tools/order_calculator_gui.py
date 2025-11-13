"""Order Calculator GUI - Tkinter-based GUI for calculating synthetic dividend orders.

This GUI provides an interactive interface for the order calculator tool,
with persistent defaults per ticker and chart visualization.
"""

import json
import math
import os
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from typing import Dict, Optional

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from src.models.backtest_utils import calculate_synthetic_dividend_orders
from src.tools.order_calculator import calculate_orders_for_manual_entry, format_order_display


class OrderCalculatorGUI:
    """Tkinter GUI for order calculator with chart visualization."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Synthetic Dividend Order Calculator")
        self.root.geometry("1200x800")

        # History file path
        self.history_file = os.path.join(os.path.dirname(__file__), "order_calculator_history.json")
        self.history: Dict[str, Dict] = self.load_history()

        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)

        # Input frame
        input_frame = ttk.LabelFrame(main_frame, text="Order Parameters", padding="5")
        input_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        # Ticker selection
        ttk.Label(input_frame, text="Ticker:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.ticker_var = tk.StringVar()
        self.ticker_combo = ttk.Combobox(input_frame, textvariable=self.ticker_var, width=10)
        self.ticker_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        self.ticker_combo['values'] = list(self.history.keys())
        self.ticker_combo.bind('<<ComboboxSelected>>', self.on_ticker_selected)

        # Holdings
        ttk.Label(input_frame, text="Holdings:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.holdings_var = tk.StringVar()
        self.holdings_entry = ttk.Entry(input_frame, textvariable=self.holdings_var, width=12)
        self.holdings_entry.grid(row=0, column=3, sticky=(tk.W, tk.E), padx=(0, 10))

        # Last Price
        ttk.Label(input_frame, text="Last Price:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.last_price_var = tk.StringVar()
        self.last_price_entry = ttk.Entry(input_frame, textvariable=self.last_price_var, width=12)
        self.last_price_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=(5, 0))

        # Current Price
        ttk.Label(input_frame, text="Current Price:").grid(row=1, column=2, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.current_price_var = tk.StringVar()
        self.current_price_entry = ttk.Entry(input_frame, textvariable=self.current_price_var, width=12)
        self.current_price_entry.grid(row=1, column=3, sticky=(tk.W, tk.E), padx=(0, 10), pady=(5, 0))

        # SDN
        ttk.Label(input_frame, text="SDN:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.sdn_var = tk.StringVar()
        self.sdn_entry = ttk.Entry(input_frame, textvariable=self.sdn_var, width=12)
        self.sdn_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=(5, 0))

        # Profit
        ttk.Label(input_frame, text="Profit %:").grid(row=2, column=2, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.profit_var = tk.StringVar()
        self.profit_entry = ttk.Entry(input_frame, textvariable=self.profit_var, width=12)
        self.profit_entry.grid(row=2, column=3, sticky=(tk.W, tk.E), padx=(0, 10), pady=(5, 0))

        # Bracket Seed
        ttk.Label(input_frame, text="Bracket Seed:").grid(row=3, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 10))
        self.bracket_seed_var = tk.StringVar()
        self.bracket_seed_entry = ttk.Entry(input_frame, textvariable=self.bracket_seed_var, width=12)
        self.bracket_seed_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=(5, 10))

        # Calculate button
        self.calc_button = ttk.Button(input_frame, text="Calculate Orders", command=self.calculate_orders)
        self.calc_button.grid(row=3, column=2, columnspan=2, pady=(5, 10))

        # Output frame
        output_frame = ttk.LabelFrame(main_frame, text="Order Details", padding="5")
        output_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        output_frame.rowconfigure(0, weight=1)
        output_frame.columnconfigure(0, weight=1)

        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, height=20)
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Chart frame
        chart_frame = ttk.LabelFrame(main_frame, text="Price Chart with Brackets", padding="5")
        chart_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        chart_frame.rowconfigure(0, weight=1)
        chart_frame.columnconfigure(0, weight=1)

        # Matplotlib figure
        self.figure = Figure(figsize=(6, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=chart_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E))

    def load_history(self) -> Dict[str, Dict]:
        """Load calculation history from JSON file."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load history: {e}")
        return {}

    def save_history(self):
        """Save calculation history to JSON file."""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save history: {e}")

    def on_ticker_selected(self, event):
        """Handle ticker selection - load defaults."""
        ticker = self.ticker_var.get()
        if ticker in self.history:
            params = self.history[ticker]
            self.holdings_var.set(params.get('holdings', ''))
            self.last_price_var.set(params.get('last_price', ''))
            # Current price defaults to last transaction price
            self.current_price_var.set(params.get('last_price', ''))
            self.sdn_var.set(params.get('sdn', ''))
            self.profit_var.set(params.get('profit', ''))
            self.bracket_seed_var.set(params.get('bracket_seed', ''))

    def calculate_orders(self):
        """Calculate and display orders."""
        try:
            # Get inputs
            ticker = self.ticker_var.get().strip()
            holdings = float(self.holdings_var.get())
            last_price = float(self.last_price_var.get())
            current_price = float(self.current_price_var.get())
            sdn = int(self.sdn_var.get())
            profit = float(self.profit_var.get())
            bracket_seed_str = self.bracket_seed_var.get().strip()
            bracket_seed = float(bracket_seed_str) if bracket_seed_str else None

            # Validate
            if not ticker:
                raise ValueError("Ticker is required")
            if holdings <= 0:
                raise ValueError("Holdings must be positive")
            if last_price <= 0 or current_price <= 0:
                raise ValueError("Prices must be positive")
            if sdn < 2 or sdn > 20:
                raise ValueError("SDN must be between 2 and 20")
            if profit < 0 or profit > 200:
                raise ValueError("Profit must be between 0 and 200")

            # Calculate orders
            buy_price, buy_qty, sell_price, sell_qty = calculate_orders_for_manual_entry(
                ticker=ticker,
                holdings=holdings,
                last_transaction_price=last_price,
                current_price=current_price,
                sdn=sdn,
                profit_sharing_pct=profit,
                bracket_seed=bracket_seed,
            )

            # Format output
            output = format_order_display(
                ticker=ticker,
                holdings=holdings,
                last_price=last_price,
                current_price=current_price,
                buy_price=buy_price,
                buy_qty=buy_qty,
                sell_price=sell_price,
                sell_qty=sell_qty,
                sdn=sdn,
                profit_pct=profit,
                bracket_seed=bracket_seed,
            )

            # Display output
            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(tk.END, output)

            # Save to history
            self.history[ticker] = {
                'holdings': holdings,
                'last_price': last_price,
                'current_price': current_price,
                'sdn': sdn,
                'profit': profit,
                'bracket_seed': bracket_seed,
            }
            self.save_history()

            # Update ticker list
            self.ticker_combo['values'] = list(self.history.keys())

            # Update chart
            self.update_chart(ticker, last_price, current_price, buy_price, sell_price, sdn, bracket_seed)

            self.status_var.set(f"Calculated orders for {ticker}")

        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.status_var.set("Error in calculation")

    def update_chart(self, ticker: str, last_price: float, current_price: float,
                    buy_price: float, sell_price: float, sdn: int, bracket_seed: Optional[float]):
        """Update the price chart with brackets."""
        try:
            # Clear previous plot
            self.ax.clear()

            # Try to load asset data
            try:
                from src.data.asset import Asset
                asset = Asset(ticker)
                df = asset._load_price_cache()
                if df is not None and not df.empty:
                    # Plot price on log scale
                    self.ax.semilogy(df.index, df['Close'], label='Price', linewidth=1)
                    self.ax.set_title(f'{ticker} Price Chart (Log Scale)')
                    self.ax.set_xlabel('Date')
                    self.ax.set_ylabel('Price ($)')
                    self.ax.grid(True, alpha=0.3)

                    # Add bracket lines
                    self.ax.axhline(y=buy_price, color='green', linestyle='--', alpha=0.7,
                                   label=f'Buy: ${buy_price:.2f}')
                    self.ax.axhline(y=sell_price, color='red', linestyle='--', alpha=0.7,
                                   label=f'Sell: ${sell_price:.2f}')
                    self.ax.axhline(y=last_price, color='blue', linestyle='-', alpha=0.7,
                                   label=f'Last: ${last_price:.2f}')

                    # Add bracket ladder annotations
                    self.add_bracket_annotations(last_price, buy_price, sell_price, sdn, bracket_seed)

                    self.ax.legend()
                else:
                    self.ax.text(0.5, 0.5, f'No price data available for {ticker}',
                               ha='center', va='center', transform=self.ax.transAxes)
            except Exception as e:
                self.ax.text(0.5, 0.5, f'Failed to load chart data: {str(e)}',
                           ha='center', va='center', transform=self.ax.transAxes)

            self.canvas.draw()

        except Exception as e:
            self.status_var.set(f"Chart error: {str(e)}")

    def add_bracket_annotations(self, last_price: float, buy_price: float, sell_price: float,
                               sdn: int, bracket_seed: Optional[float]):
        """Add bracket ladder annotations to the chart."""
        try:
            rebalance_size = (2.0 ** (1.0 / float(sdn))) - 1.0

            # Calculate bracket positions
            anchor_price = last_price
            if bracket_seed is not None and bracket_seed > 0:
                bracket_n = math.log(last_price / bracket_seed) / math.log(1 + rebalance_size)
                bracket_rounded = round(bracket_n)
                anchor_price = bracket_seed * math.pow(1 + rebalance_size, bracket_rounded)

            # Add a few bracket levels around the current position
            for i in range(-3, 4):
                bracket_price = anchor_price * math.pow(1 + rebalance_size, i)
                if bracket_price > 0:
                    color = 'purple' if i == 0 else 'gray'
                    alpha = 0.5 if abs(i) > 1 else 0.3
                    self.ax.axhline(y=bracket_price, color=color, linestyle=':', alpha=alpha,
                                   label=f'Bracket {i}' if i != 0 else f'Current Bracket')

        except Exception:
            pass  # Skip annotations if calculation fails


def main():
    """Main entry point for the GUI."""
    root = tk.Tk()
    app = OrderCalculatorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()