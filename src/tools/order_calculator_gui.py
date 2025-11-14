"""Order Calculator GUI - Tkinter-based GUI for calculating synthetic dividend orders.

This GUI provides an interactive interface for the order calculator tool,
with persistent defaults per ticker and chart visualization.
"""

import json
import math
import os
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from typing import Any, Dict, Optional

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from src.tools.order_calculator import calculate_orders_for_manual_entry, format_order_display


class OrderCalculatorGUI:
    """Tkinter GUI for order calculator with chart visualization."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Synthetic Dividend Order Calculator")
        self.root.geometry("1200x800")

        # History file path
        self.history_file = os.path.join(os.path.dirname(__file__), "order_calculator_history.json")
        self.history: Dict[str, Dict] = {}
        self.last_ticker: Optional[str] = None
        self.load_history()

        # Store calculated order values for buy/sell buttons
        self.current_buy_price = 0.0
        self.current_buy_qty = 0.0
        self.current_sell_price = 0.0
        self.current_sell_qty = 0.0

        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="wens")

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Input frame
        input_frame = ttk.LabelFrame(main_frame, text="Order Parameters", padding="5")
        input_frame.grid(row=0, column=0, sticky="we", pady=(0, 10))

        # Ticker selection
        ttk.Label(input_frame, text="Ticker:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.ticker_var = tk.StringVar()
        self.ticker_combo = ttk.Combobox(input_frame, textvariable=self.ticker_var, width=10)
        self.ticker_combo.grid(row=0, column=1, sticky="we", padx=(0, 10))
        self.ticker_combo["values"] = [t for t in self.history.keys() if t != "last_ticker"]
        self.ticker_combo.bind("<<ComboboxSelected>>", self.on_ticker_selected)

        # Holdings
        ttk.Label(input_frame, text="Holdings:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.holdings_var = tk.StringVar()
        self.holdings_entry = ttk.Entry(input_frame, textvariable=self.holdings_var, width=12)
        self.holdings_entry.grid(row=0, column=3, sticky="we", padx=(0, 10))

        # Last Price
        ttk.Label(input_frame, text="Last Price:").grid(
            row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0)
        )
        self.last_price_var = tk.StringVar()
        self.last_price_entry = ttk.Entry(input_frame, textvariable=self.last_price_var, width=12)
        self.last_price_entry.grid(row=1, column=1, sticky="we", padx=(0, 10), pady=(5, 0))

        # Current Price
        ttk.Label(input_frame, text="Current Price:").grid(
            row=1, column=2, sticky=tk.W, padx=(0, 5), pady=(5, 0)
        )
        self.current_price_var = tk.StringVar()
        self.current_price_entry = ttk.Entry(
            input_frame, textvariable=self.current_price_var, width=12
        )
        self.current_price_entry.grid(row=1, column=3, sticky="we", padx=(0, 10), pady=(5, 0))

        # SDN
        ttk.Label(input_frame, text="SDN:").grid(
            row=2, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0)
        )
        self.sdn_var = tk.StringVar()
        self.sdn_entry = ttk.Entry(input_frame, textvariable=self.sdn_var, width=12)
        self.sdn_entry.grid(row=2, column=1, sticky="we", padx=(0, 10), pady=(5, 0))

        # Profit
        ttk.Label(input_frame, text="Profit %:").grid(
            row=2, column=2, sticky=tk.W, padx=(0, 5), pady=(5, 0)
        )
        self.profit_var = tk.StringVar()
        self.profit_entry = ttk.Entry(input_frame, textvariable=self.profit_var, width=12)
        self.profit_entry.grid(row=2, column=3, sticky="we", padx=(0, 10), pady=(5, 0))

        # Bracket Seed
        ttk.Label(input_frame, text="Bracket Seed:").grid(
            row=3, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 10)
        )
        self.bracket_seed_var = tk.StringVar()
        self.bracket_seed_entry = ttk.Entry(
            input_frame, textvariable=self.bracket_seed_var, width=12
        )
        self.bracket_seed_entry.grid(row=3, column=1, sticky="we", padx=(0, 10), pady=(5, 10))

        # Buy and Sell buttons
        self.buy_button = ttk.Button(
            input_frame, text="BUY", command=self.execute_buy_order
        )
        self.buy_button.grid(row=3, column=2, sticky="we", padx=(0, 5), pady=(5, 10))

        self.sell_button = ttk.Button(
            input_frame, text="SELL", command=self.execute_sell_order
        )
        self.sell_button.grid(row=3, column=3, sticky="we", pady=(5, 10))

        # Calculate button
        self.calc_button = ttk.Button(
            input_frame, text="Calculate Orders", command=self.calculate_orders
        )
        self.calc_button.grid(row=4, column=0, columnspan=3, pady=(5, 10))

        # Help button
        self.help_button = ttk.Button(
            input_frame, text="Help", command=self.show_help
        )
        self.help_button.grid(row=4, column=3, pady=(5, 10))

        # Output frame (right side)
        output_frame = ttk.LabelFrame(main_frame, text="Broker Orders", padding="5")
        output_frame.grid(row=0, column=1, sticky="wen", padx=(10, 0))

        # Buy order display
        ttk.Label(output_frame, text="Buy Order:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.buy_order_var = tk.StringVar()
        self.buy_order_var.set("")  # Initialize empty
        self.buy_order_entry = ttk.Entry(
            output_frame, textvariable=self.buy_order_var, state="readonly", width=35
        )
        self.buy_order_entry.grid(row=0, column=1, sticky="we", pady=(0, 5))

        # Sell order display
        ttk.Label(output_frame, text="Sell Order:").grid(row=1, column=0, sticky=tk.W)
        self.sell_order_var = tk.StringVar()
        self.sell_order_var.set("")  # Initialize empty
        self.sell_order_entry = ttk.Entry(
            output_frame, textvariable=self.sell_order_var, state="readonly", width=35
        )
        self.sell_order_entry.grid(row=1, column=1, sticky="we")

        # Configure output frame columns
        output_frame.columnconfigure(1, weight=1)

        # Tab control
        self.tab_control = ttk.Notebook(main_frame)
        self.tab_control.grid(row=1, column=0, columnspan=2, sticky="wens", pady=(10, 10))

        # Chart tab (first/default tab)
        chart_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(chart_tab, text="Price Chart")
        chart_tab.columnconfigure(0, weight=1)
        chart_tab.rowconfigure(0, weight=1)

        # Matplotlib figure
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=chart_tab)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="wens", padx=5, pady=5)

        # Order Details tab
        order_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(order_tab, text="Order Details")
        order_tab.columnconfigure(0, weight=1)
        order_tab.rowconfigure(0, weight=1)

        self.output_text = scrolledtext.ScrolledText(order_tab, wrap=tk.WORD, height=20)
        self.output_text.grid(row=0, column=0, sticky="wens", padx=5, pady=5)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(
            main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W
        )
        status_bar.grid(row=2, column=0, sticky="we")

        # Load last ticker and pre-fill if available (after UI is created)
        if self.last_ticker and self.last_ticker in self.history:
            self.pre_fill_with_ticker(self.last_ticker)

    @staticmethod
    def parse_price(s: str) -> float:
        """Parse a price string, handling currency symbols and commas."""
        s = s.strip()
        if not s:
            raise ValueError("Price cannot be empty")
        # Remove common currency symbols
        s = s.replace("$", "").replace("€", "").replace("£", "").replace("¥", "").replace("₹", "")
        # Remove commas
        s = s.replace(",", "")
        return float(s)

    @staticmethod
    def format_price(price: float) -> str:
        """Format a price to canonical accounting format."""
        return f"{price:,.2f}"

    @staticmethod
    def parse_holdings(s: str) -> float:
        """Parse a holdings string, handling commas."""
        s = s.strip()
        if not s:
            raise ValueError("Holdings cannot be empty")
        # Remove commas
        s = s.replace(",", "")
        return float(s)

    @staticmethod
    def format_holdings(holdings: float) -> str:
        """Format holdings with commas for readability."""
        return f"{holdings:,.0f}"

    def load_history(self) -> None:
        """Load calculation history from JSON file."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r") as f:
                    data = json.load(f)
                    # Extract ticker data (exclude last_ticker)
                    self.history = {k: v for k, v in data.items() if k != "last_ticker"}
                    # Store last_ticker separately
                    self.last_ticker = data.get("last_ticker")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load history: {e}")

    def save_history(self):
        """Save calculation history to JSON file."""
        try:
            # Prepare data with last_ticker
            data_to_save: Dict[str, Any] = dict(self.history)
            if self.last_ticker:
                data_to_save["last_ticker"] = self.last_ticker
            with open(self.history_file, "w") as f:
                json.dump(data_to_save, f, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save history: {e}")

    def pre_fill_with_ticker(self, ticker: str):
        """Pre-fill all fields with the specified ticker's data."""
        if ticker in self.history:
            params = self.history[ticker]
            self.ticker_var.set(ticker)
            self.holdings_var.set(
                self.format_holdings(params.get("holdings", 0)) if params.get("holdings") else ""
            )
            self.last_price_var.set(
                self.format_price(params.get("last_price", 0)) if params.get("last_price") else ""
            )
            # Current price defaults to last transaction price
            self.current_price_var.set(
                self.format_price(params.get("last_price", 0)) if params.get("last_price") else ""
            )
            self.sdn_var.set(params.get("sdn", ""))
            self.profit_var.set(params.get("profit", ""))
            bracket_seed = params.get("bracket_seed")
            if bracket_seed is not None:
                self.bracket_seed_var.set(self.format_price(bracket_seed))
            else:
                self.bracket_seed_var.set("")

    def on_ticker_selected(self, event):
        """Handle ticker selection - load defaults."""
        ticker = self.ticker_var.get()
        if ticker in self.history:
            params = self.history[ticker]
            self.holdings_var.set(
                self.format_holdings(params.get("holdings", 0)) if params.get("holdings") else ""
            )
            self.last_price_var.set(
                self.format_price(params.get("last_price", 0)) if params.get("last_price") else ""
            )
            # Current price defaults to last transaction price
            self.current_price_var.set(
                self.format_price(params.get("last_price", 0)) if params.get("last_price") else ""
            )
            self.sdn_var.set(params.get("sdn", ""))
            self.profit_var.set(params.get("profit", ""))
            bracket_seed = params.get("bracket_seed")
            if bracket_seed is not None:
                self.bracket_seed_var.set(self.format_price(bracket_seed))
            else:
                self.bracket_seed_var.set("")

    def calculate_orders(self):
        """Calculate and display orders."""
        try:
            # Get inputs
            ticker = self.ticker_var.get().strip()
            holdings = self.parse_holdings(self.holdings_var.get())
            last_price = self.parse_price(self.last_price_var.get())
            current_price = self.parse_price(self.current_price_var.get())
            sdn = int(self.sdn_var.get())
            profit = float(self.profit_var.get())
            bracket_seed_str = self.bracket_seed_var.get().strip()
            if bracket_seed_str.lower() in ("", "none", "nil"):
                bracket_seed = None
            else:
                bracket_seed = self.parse_price(bracket_seed_str)

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

            # Update fields to canonical format
            self.holdings_var.set(self.format_holdings(holdings))
            self.last_price_var.set(self.format_price(last_price))
            self.current_price_var.set(self.format_price(current_price))
            if bracket_seed is not None:
                self.bracket_seed_var.set(self.format_price(bracket_seed))

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

            # Store current order values for buy/sell buttons
            self.current_buy_price = buy_price
            self.current_buy_qty = buy_qty
            self.current_sell_price = sell_price
            self.current_sell_qty = sell_qty

            # Format broker syntax orders
            buy_amount = buy_price * buy_qty
            sell_amount = sell_price * sell_qty

            buy_order_text = f"BUY {ticker} {int(buy_qty)} @ ${buy_price:.2f} = ${buy_amount:.2f}"
            sell_order_text = f"SELL {ticker} {int(sell_qty)} @ ${sell_price:.2f} = ${sell_amount:.2f}"

            # Update broker order displays
            self.buy_order_var.set(buy_order_text)
            self.sell_order_var.set(sell_order_text)

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
                "holdings": holdings,
                "last_price": last_price,
                "current_price": current_price,
                "sdn": sdn,
                "profit": profit,
                "bracket_seed": bracket_seed,
            }
            # Update last ticker
            self.last_ticker = ticker
            self.save_history()

            # Update ticker list
            self.ticker_combo["values"] = [t for t in self.history.keys() if t != "last_ticker"]

            # Update chart
            self.update_chart(
                ticker, last_price, current_price, buy_price, sell_price, sdn, bracket_seed
            )

            self.status_var.set(f"Calculated orders for {ticker}")

        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.status_var.set("Error in calculation")
            # Clear broker order displays on error
            self.buy_order_var.set("")
            self.sell_order_var.set("")

    def execute_buy_order(self):
        """Execute the calculated buy order by updating position and recalculating."""
        try:
            if self.current_buy_price <= 0 or self.current_buy_qty <= 0:
                messagebox.showwarning("Warning", "No buy order calculated. Please calculate orders first.")
                return

            # Get current holdings
            holdings_str = self.holdings_var.get().strip()
            current_holdings = float(holdings_str.replace(",", "")) if holdings_str else 0.0

            # Update holdings (add bought shares)
            new_holdings = current_holdings + self.current_buy_qty

            # Update last price and current price to the buy execution price
            execution_price = self.current_buy_price
            self.last_price_var.set(self.format_price(execution_price))
            self.current_price_var.set(self.format_price(execution_price))

            # Update holdings
            self.holdings_var.set(self.format_holdings(new_holdings))

            # Recalculate orders with new position
            self.calculate_orders()

            self.status_var.set(f"Executed BUY: {int(self.current_buy_qty)} shares @ ${execution_price:.2f}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to execute buy order: {str(e)}")

    def execute_sell_order(self):
        """Execute the calculated sell order by updating position and recalculating."""
        try:
            if self.current_sell_price <= 0 or self.current_sell_qty <= 0:
                messagebox.showwarning("Warning", "No sell order calculated. Please calculate orders first.")
                return

            # Get current holdings
            holdings_str = self.holdings_var.get().strip()
            current_holdings = float(holdings_str.replace(",", "")) if holdings_str else 0.0

            # Check if we have enough shares to sell
            if current_holdings < self.current_sell_qty:
                messagebox.showwarning("Warning", f"Insufficient holdings. Have {current_holdings:.0f} shares, trying to sell {self.current_sell_qty:.0f} shares.")
                return

            # Update holdings (subtract sold shares)
            new_holdings = current_holdings - self.current_sell_qty

            # Update last price and current price to the sell execution price
            execution_price = self.current_sell_price
            self.last_price_var.set(self.format_price(execution_price))
            self.current_price_var.set(self.format_price(execution_price))

            # Update holdings
            self.holdings_var.set(self.format_holdings(new_holdings))

            # Recalculate orders with new position
            self.calculate_orders()

            self.status_var.set(f"Executed SELL: {int(self.current_sell_qty)} shares @ ${execution_price:.2f}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to execute sell order: {str(e)}")

    def show_help(self):
        """Show help documentation in a scrollable window."""
        try:
            # Read the help file
            help_file_path = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "HOW_TO_order_gui.md")
            with open(help_file_path, "r", encoding="utf-8") as f:
                help_content = f.read()

            # Create help window
            help_window = tk.Toplevel(self.root)
            help_window.title("Order Calculator GUI - Help")
            help_window.geometry("800x600")

            # Create scrolled text widget
            help_text = scrolledtext.ScrolledText(help_window, wrap=tk.WORD, padx=10, pady=10)
            help_text.pack(fill=tk.BOTH, expand=True)

            # Insert help content
            help_text.insert(tk.END, help_content)
            help_text.config(state=tk.DISABLED)  # Make it read-only

            # Focus the help window
            help_window.focus_set()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load help documentation: {str(e)}")

    def update_chart(
        self,
        ticker: str,
        last_price: float,
        current_price: float,
        buy_price: float,
        sell_price: float,
        sdn: int,
        bracket_seed: Optional[float],
    ):
        """Update the price chart with brackets and backtest signals."""
        try:
            # Clear previous plot
            self.ax.clear()

            # Try to load asset data
            try:
                from datetime import date, timedelta

                from src.data.asset import Asset

                asset = Asset(ticker)
                # Get data for the last 2 years for chart visualization
                end_date = date.today()
                start_date = end_date - timedelta(days=730)  # 2 years
                df = asset.get_prices(start_date, end_date)
                if df is not None and not df.empty:
                    # Plot price on log scale
                    self.ax.semilogy(df.index, df["Close"], label="Price", linewidth=1)
                    self.ax.set_title(f"{ticker} Price Chart (Log Scale)")
                    self.ax.set_xlabel("Date")
                    self.ax.set_ylabel("Price ($)")
                    self.ax.grid(True, alpha=0.3)

                    # Add bracket lines
                    self.ax.axhline(
                        y=buy_price,
                        color="red",
                        linestyle="--",
                        alpha=0.7,
                        label=f"Buy: ${buy_price:.2f}",
                    )
                    self.ax.axhline(
                        y=sell_price,
                        color="green",
                        linestyle="--",
                        alpha=0.7,
                        label=f"Sell: ${sell_price:.2f}",
                    )
                    self.ax.axhline(
                        y=last_price,
                        color="blue",
                        linestyle="-",
                        alpha=0.7,
                        label=f"Last: ${last_price:.2f}",
                    )

                    # Add bracket ladder annotations
                    self.add_bracket_annotations(
                        last_price, buy_price, sell_price, sdn, bracket_seed
                    )

                    # Run backtest to get buy/sell signals
                    self.add_backtest_signals(
                        ticker, last_price, sdn, self.profit_var.get(), bracket_seed, df, start_date, end_date
                    )

                    self.ax.legend()
                else:
                    self.ax.text(
                        0.5,
                        0.5,
                        f"No price data available for {ticker}",
                        ha="center",
                        va="center",
                        transform=self.ax.transAxes,
                    )
            except Exception as e:
                self.ax.text(
                    0.5,
                    0.5,
                    f"Failed to load chart data: {str(e)}",
                    ha="center",
                    va="center",
                    transform=self.ax.transAxes,
                )

            self.canvas.draw()

        except Exception as e:
            self.status_var.set(f"Chart error: {str(e)}")

    def add_backtest_signals(
        self,
        ticker: str,
        last_price: float,
        sdn: int,
        profit_pct_str: str,
        bracket_seed: Optional[float],
        df: pd.DataFrame,
        start_date: date,
        end_date: date,
    ):
        """Run backtest and add buy/sell signal dots to the chart."""
        try:
            # Parse profit percentage
            profit_pct = float(profit_pct_str) if profit_pct_str.strip() else 50.0

            # Calculate algorithm parameters
            rebalance_size = (2.0 ** (1.0 / float(sdn))) - 1.0
            profit_sharing = profit_pct / 100.0

            # Get holdings from GUI
            holdings_str = self.holdings_var.get().strip()
            holdings = float(holdings_str.replace(",", "")) if holdings_str else 1000.0

            # Create algorithm
            from src.algorithms.synthetic_dividend import SyntheticDividendAlgorithm

            algo = SyntheticDividendAlgorithm(
                rebalance_size=rebalance_size,
                profit_sharing=profit_sharing,
                buyback_enabled=True,
                bracket_seed=bracket_seed,
            )

            # Run backtest
            from src.models.backtest import run_algorithm_backtest

            transactions, _ = run_algorithm_backtest(
                df=df,
                ticker=ticker,
                initial_qty=holdings,
                start_date=start_date,
                end_date=end_date,
                algo=algo,
                simple_mode=True,  # Use simple mode for faster execution
            )

            # Extract buy/sell signals
            buy_signals = []
            sell_signals = []

            for txn in transactions:
                if txn.action == "BUY":
                    buy_signals.append((txn.transaction_date, txn.price))
                elif txn.action == "SELL":
                    sell_signals.append((txn.transaction_date, txn.price))

            # Plot signals as dots
            if buy_signals:
                buy_dates, buy_prices = zip(*buy_signals)
                self.ax.scatter(buy_dates, buy_prices, color="red", s=30, alpha=0.8, label="Buy Signals", zorder=5)

            if sell_signals:
                sell_dates, sell_prices = zip(*sell_signals)
                self.ax.scatter(sell_dates, sell_prices, color="green", s=30, alpha=0.8, label="Sell Signals", zorder=5)

            # Add signal count inset in lower right
            total_buys = len(buy_signals)
            total_sells = len(sell_signals)

            # Create inset text box
            inset_text = f"Signals\nBuys: {total_buys}\nSells: {total_sells}"
            self.ax.text(
                0.98, 0.02, inset_text,
                transform=self.ax.transAxes,
                fontsize=9,
                verticalalignment="bottom",
                horizontalalignment="right",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8),
                family="monospace",
            )

        except Exception as e:
            # Silently skip signal plotting on error
            print(f"Warning: Could not add backtest signals: {e}")
            pass

    def add_bracket_annotations(
        self,
        last_price: float,
        buy_price: float,
        sell_price: float,
        sdn: int,
        bracket_seed: Optional[float],
    ):
        """Add order of magnitude reference lines (powers of 2) and subdivisions to the chart."""
        try:
            # Get the current y-axis limits (price range shown on chart)
            y_min, y_max = self.ax.get_ylim()

            # Add solid light gray lines for every mathematical order of magnitude (factor of 2)
            # Find the range of powers of 2 that fit within the visible price range
            import math

            # Find the lowest power of 2 that would be visible (or just below)
            min_power = math.floor(math.log2(y_min))
            # Find the highest power of 2 that would be visible (or just above)
            max_power = math.ceil(math.log2(y_max))

            # Add horizontal lines for all powers of 2 within the visible range
            for power in range(min_power, max_power + 1):
                magnitude_price = 2.0 ** power
                if y_min <= magnitude_price <= y_max:  # Only add if within visible range
                    self.ax.axhline(
                        y=magnitude_price,
                        color=(0.5, 0.5, 0.5),
                        linestyle="-",
                        alpha=0.5,
                        linewidth=0.8,
                        zorder=1,  # Behind other elements
                    )

            # Add dashed light gray lines for 8 subdivisions between each factor of 2
            # For each pair of consecutive powers of 2, add 8 subdivision lines
            for power in range(min_power, max_power):
                base_price = 2.0 ** power
                next_base_price = 2.0 ** (power + 1)

                # Add 8 subdivisions between base_price and next_base_price
                for i in range(1, 8):  # 1/8, 2/8, 3/8, 4/8, 5/8, 6/8, 7/8
                    subdivision_price = base_price + (next_base_price - base_price) * (i / 8.0)
                    if y_min <= subdivision_price <= y_max:  # Only add if within visible range
                        self.ax.axhline(
                            y=subdivision_price,
                            color=(0.5, 0.5, 0.5),
                            linestyle="--",
                            alpha=0.3,
                            linewidth=0.5,
                            zorder=1,  # Behind other elements
                        )

        except Exception:
            pass  # Skip annotations if calculation fails


def main():
    """Main entry point for the GUI."""
    root = tk.Tk()
    OrderCalculatorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
