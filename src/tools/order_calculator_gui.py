"""Order Calculator GUI - Tkinter-based GUI for calculating synthetic dividend orders.

This GUI provides an interactive interface for the order calculator tool,
with persistent defaults per ticker and chart visualization.
"""

import json
import os
import tkinter as tk
from datetime import date, timedelta
from tkinter import messagebox, scrolledtext, ttk
from typing import Any, Dict, Optional

import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# Try to import tkcalendar for date picker functionality
try:
    from tkcalendar import DateEntry

    TKCALENDAR_AVAILABLE = True
except ImportError:
    TKCALENDAR_AVAILABLE = False

from src.data.asset import Asset
from src.tools.order_calculator import calculate_orders_for_manual_entry, format_order_display

# Optional imports for enhanced help display
try:
    import markdown  # type: ignore
    import tkinterweb

    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False


class ToolTip:
    """Simple tooltip class for Tkinter widgets."""

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        if self.tooltip_window or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self.tooltip_window,
            text=self.text,
            justify="left",
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
            font="tahoma 8 normal",
        )
        label.pack(ipadx=1)

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


class OrderCalculatorGUI:
    """Tkinter GUI for order calculator with chart visualization."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Synthetic Dividend Order Calculator")
        self.root.geometry("1200x800")

        # Load window settings
        self.load_window_settings()

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

        # Auto-calculation debouncing
        self.calculation_timer: Optional[str] = None
        self.calculation_delay = 500  # milliseconds

        # Create menu bar
        self.create_menu_bar()

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

        # Configure input frame columns to allow proper expansion
        input_frame.columnconfigure(1, weight=1)  # Ticker entry
        input_frame.columnconfigure(
            3, weight=1
        )  # Holdings, Last Price, Start Date, End Date, SDN, Profit, Bracket Seed entries

        # Ticker selection
        ttk.Label(input_frame, text="Ticker:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.ticker_var = tk.StringVar()
        self.ticker_combo = ttk.Combobox(input_frame, textvariable=self.ticker_var, width=10)
        self.ticker_combo.grid(row=0, column=1, sticky="we", padx=(0, 10))
        self.ticker_combo["values"] = [t for t in self.history.keys() if t != "last_ticker"]
        self.ticker_combo.bind("<<ComboboxSelected>>", self.on_ticker_selected)
        self.ticker_combo.bind("<FocusOut>", self.schedule_auto_calculation)
        ToolTip(self.ticker_combo, "Stock ticker symbol (e.g., NVDA, SPY, AAPL)")

        # Holdings
        ttk.Label(input_frame, text="Holdings:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.holdings_var = tk.StringVar()
        self.holdings_entry = ttk.Entry(input_frame, textvariable=self.holdings_var, width=12)
        self.holdings_entry.grid(row=0, column=3, sticky="we", padx=(0, 10))
        self.holdings_entry.bind("<FocusOut>", self.schedule_auto_calculation)
        ToolTip(self.holdings_entry, "Number of shares you currently own")

        # Last Price
        ttk.Label(input_frame, text="Last Price:").grid(
            row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0)
        )
        self.last_price_var = tk.StringVar()
        self.last_price_entry = ttk.Entry(input_frame, textvariable=self.last_price_var, width=12)
        self.last_price_entry.grid(row=1, column=1, sticky="we", padx=(0, 10), pady=(5, 0))
        self.last_price_entry.bind("<FocusOut>", self.schedule_auto_calculation)
        ToolTip(self.last_price_entry, "Price you last bought or sold shares at")

        # Start Date
        ttk.Label(input_frame, text="Start Date:").grid(
            row=1, column=2, sticky=tk.W, padx=(0, 5), pady=(5, 0)
        )
        if TKCALENDAR_AVAILABLE:
            self.start_date_entry = DateEntry(
                input_frame,
                width=12,
                background="darkblue",
                foreground="white",
                borderwidth=1,
                date_pattern="yyyy-mm-dd",
            )
            self.start_date_var = self.start_date_entry
        else:
            self.start_date_var = tk.StringVar()
            self.start_date_entry = ttk.Entry(
                input_frame, textvariable=self.start_date_var, width=12
            )
        self.start_date_entry.grid(row=1, column=3, sticky="we", padx=(0, 10), pady=(5, 0))
        self.start_date_entry.bind("<FocusOut>", self.schedule_auto_calculation)
        self.start_date_entry.bind("<<DateEntrySelected>>", self.schedule_auto_calculation)
        ToolTip(self.start_date_entry, "Start date for price data (YYYY-MM-DD)")

        # End Date
        ttk.Label(input_frame, text="End Date:").grid(
            row=2, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0)
        )
        if TKCALENDAR_AVAILABLE:
            self.end_date_entry = DateEntry(
                input_frame,
                width=12,
                background="darkblue",
                foreground="white",
                borderwidth=1,
                date_pattern="yyyy-mm-dd",
            )
            self.end_date_var = self.end_date_entry
        else:
            self.end_date_var = tk.StringVar()
            self.end_date_entry = ttk.Entry(input_frame, textvariable=self.end_date_var, width=12)
        self.end_date_entry.grid(row=2, column=1, sticky="we", padx=(0, 10), pady=(5, 0))
        self.end_date_entry.bind("<FocusOut>", self.schedule_auto_calculation)
        self.end_date_entry.bind("<<DateEntrySelected>>", self.schedule_auto_calculation)
        ToolTip(self.end_date_entry, "End date for price data (YYYY-MM-DD)")

        # SDN
        ttk.Label(input_frame, text="SDN:").grid(
            row=2, column=2, sticky=tk.W, padx=(0, 5), pady=(5, 0)
        )
        self.sdn_var = tk.StringVar()
        self.sdn_entry = ttk.Entry(input_frame, textvariable=self.sdn_var, width=12)
        self.sdn_entry.grid(row=2, column=3, sticky="we", padx=(0, 10), pady=(5, 0))
        self.sdn_entry.bind("<FocusOut>", self.schedule_auto_calculation)
        ToolTip(self.sdn_entry, "Synthetic Dividend Number (2-8): Controls bracket spacing")

        # Profit
        ttk.Label(input_frame, text="Profit %:").grid(
            row=3, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0)
        )
        self.profit_var = tk.StringVar()
        self.profit_entry = ttk.Entry(input_frame, textvariable=self.profit_var, width=12)
        self.profit_entry.grid(row=3, column=1, sticky="we", padx=(0, 10), pady=(5, 0))
        self.profit_entry.bind("<FocusOut>", self.schedule_auto_calculation)
        ToolTip(
            self.profit_entry,
            "Profit sharing percentage (25-75%): Higher = more aggressive profit-taking",
        )

        # Bracket Seed
        ttk.Label(input_frame, text="Bracket Seed:").grid(
            row=3, column=2, sticky=tk.W, padx=(0, 5), pady=(5, 10)
        )
        self.bracket_seed_var = tk.StringVar()
        self.bracket_seed_entry = ttk.Entry(
            input_frame, textvariable=self.bracket_seed_var, width=12
        )
        self.bracket_seed_entry.grid(row=3, column=3, sticky="we", padx=(0, 10), pady=(5, 10))
        self.bracket_seed_entry.bind("<FocusOut>", self.schedule_auto_calculation)
        ToolTip(self.bracket_seed_entry, "Optional: Starting price for bracket calculations")

        # Buy and Sell buttons
        self.buy_button = ttk.Button(input_frame, text="BUY", command=self.execute_buy_order)
        self.buy_button.grid(row=3, column=2, sticky="we", padx=(0, 5), pady=(5, 10))
        ToolTip(self.buy_button, "Execute calculated buy order and update position")

        self.sell_button = ttk.Button(input_frame, text="SELL", command=self.execute_sell_order)
        self.sell_button.grid(row=3, column=3, sticky="we", pady=(5, 10))
        ToolTip(self.sell_button, "Execute calculated sell order and update position")

        # Help button (moved to where Calculate Orders button was)
        self.help_button = ttk.Button(input_frame, text="Help", command=self.show_help)
        self.help_button.grid(row=4, column=0, columnspan=4, pady=(5, 10))
        ToolTip(self.help_button, "Show detailed help documentation (F1)")

        # Set default dates after date fields are created
        self.set_default_dates()

        # Output frame (right side)
        output_frame = ttk.LabelFrame(main_frame, text="Broker Orders", padding="5")
        output_frame.grid(row=0, column=1, sticky="wen", padx=(10, 0))

        # Current price display
        ttk.Label(output_frame, text="Current Price:").grid(
            row=0, column=0, sticky=tk.W, pady=(0, 5)
        )
        self.current_price_var = tk.StringVar()
        self.current_price_var.set("")  # Initialize empty
        self.current_price_entry = ttk.Entry(
            output_frame, textvariable=self.current_price_var, state="readonly", width=35
        )
        self.current_price_entry.grid(row=0, column=1, sticky="we", pady=(0, 5))

        # Buy order display
        ttk.Label(output_frame, text="Buy Order:").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        self.buy_order_var = tk.StringVar()
        self.buy_order_var.set("")  # Initialize empty
        self.buy_order_entry = ttk.Entry(
            output_frame, textvariable=self.buy_order_var, state="readonly", width=35
        )
        self.buy_order_entry.grid(row=1, column=1, sticky="we", pady=(0, 5))

        # Sell order display
        ttk.Label(output_frame, text="Sell Order:").grid(row=2, column=0, sticky=tk.W)
        self.sell_order_var = tk.StringVar()
        self.sell_order_var.set("")  # Initialize empty
        self.sell_order_entry = ttk.Entry(
            output_frame, textvariable=self.sell_order_var, state="readonly", width=35
        )
        self.sell_order_entry.grid(row=2, column=1, sticky="we")

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

        # Bind window close event to save settings
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_menu_bar(self):
        """Create the application menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(
            label="New Calculation", command=self.clear_all_fields, accelerator="Ctrl+N"
        )
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing, accelerator="Ctrl+Q")

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(
            label="Copy Buy Order", command=self.copy_buy_order, accelerator="Ctrl+B"
        )
        edit_menu.add_command(
            label="Copy Sell Order", command=self.copy_sell_order, accelerator="Ctrl+S"
        )
        edit_menu.add_separator()
        edit_menu.add_command(
            label="Clear All", command=self.clear_all_fields, accelerator="Ctrl+L"
        )

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Help", command=self.show_help, accelerator="F1")
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self.show_about)

        # Bind keyboard shortcuts
        self.root.bind("<Control-n>", lambda e: self.clear_all_fields())
        self.root.bind("<Control-q>", lambda e: self.on_closing())
        self.root.bind("<Control-b>", lambda e: self.copy_buy_order())
        self.root.bind("<Control-s>", lambda e: self.copy_sell_order())
        self.root.bind("<Control-l>", lambda e: self.clear_all_fields())
        self.root.bind("<F1>", lambda e: self.show_help())

    def load_window_settings(self):
        """Load window size and position settings."""
        settings_file = os.path.join(os.path.dirname(__file__), "window_settings.json")
        if os.path.exists(settings_file):
            try:
                with open(settings_file, "r") as f:
                    settings = json.load(f)
                    geometry = settings.get("geometry", "1200x800")
                    self.root.geometry(geometry)
            except Exception:
                pass  # Use default geometry

    def save_window_settings(self):
        """Save window size and position settings."""
        settings_file = os.path.join(os.path.dirname(__file__), "window_settings.json")
        try:
            geometry = self.root.geometry()
            settings = {"geometry": geometry}
            with open(settings_file, "w") as f:
                json.dump(settings, f, indent=2)
        except Exception:
            pass  # Silently fail

    def on_closing(self):
        """Handle window close event."""
        self.save_window_settings()
        self.root.quit()

    def copy_buy_order(self):
        """Copy buy order to clipboard."""
        buy_order = self.buy_order_var.get()
        if buy_order:
            self.root.clipboard_clear()
            self.root.clipboard_append(buy_order)
            self.status_var.set("Buy order copied to clipboard")
        else:
            self.status_var.set("No buy order to copy")

    def copy_sell_order(self):
        """Copy sell order to clipboard."""
        sell_order = self.sell_order_var.get()
        if sell_order:
            self.root.clipboard_clear()
            self.root.clipboard_append(sell_order)
            self.status_var.set("Sell order copied to clipboard")
        else:
            self.status_var.set("No sell order to copy")

    def clear_all_fields(self):
        """Clear all input fields."""
        self.ticker_var.set("")
        self.holdings_var.set("")
        self.last_price_var.set("")
        # Clear dates - handle both DateEntry and StringVar
        if TKCALENDAR_AVAILABLE:
            # Reset to defaults when clearing
            from datetime import date, timedelta

            today = date.today()
            one_year_ago = today - timedelta(days=365)
            self.start_date_entry.set_date(one_year_ago)
            self.end_date_entry.set_date(today)
        else:
            self.start_date_var.set("")
            self.end_date_var.set("")
        self.sdn_var.set("")
        self.profit_var.set("")
        self.bracket_seed_var.set("")
        self.buy_order_var.set("")
        self.sell_order_var.set("")
        self.current_price_var.set("")  # Clear current price
        self.output_text.delete(1.0, tk.END)
        self.status_var.set("All fields cleared")

    def show_about(self):
        """Show about dialog."""
        about_text = """Synthetic Dividend Order Calculator

Version 1.0

A professional tool for calculating synthetic dividend orders
using the Synthetic Dividend Algorithm.

Features:
• Interactive order calculation
• Visual price chart with signals
• Bracket order simulation
• Persistent settings per ticker
• Professional broker order formatting

© 2025 Synthetic Dividend Project"""

        messagebox.showinfo("About", about_text)

    def schedule_auto_calculation(self, event=None):
        """Schedule auto-calculation with debouncing."""
        # Cancel any existing timer
        if self.calculation_timer:
            self.root.after_cancel(self.calculation_timer)

        # Schedule new calculation after delay
        self.calculation_timer = self.root.after(
            self.calculation_delay, self.perform_auto_calculation
        )

    def perform_auto_calculation(self):
        """Perform auto-calculation if all required fields are filled."""
        try:
            # Check if we have enough information to calculate
            if not self.can_calculate():
                return

            # Perform the calculation
            self.calculate_orders()

        except Exception:
            # Silently handle errors during auto-calculation
            # User will see error if they manually trigger calculation
            pass

    def can_calculate(self) -> bool:
        """Check if all required fields are filled for calculation."""
        try:
            ticker = self.ticker_var.get().strip()
            holdings_str = self.holdings_var.get().strip()
            last_price_str = self.last_price_var.get().strip()
            start_date_str = self.start_date_var.get().strip()
            end_date_str = self.end_date_var.get().strip()
            sdn_str = self.sdn_var.get().strip()
            profit_str = self.profit_var.get().strip()

            # Check required fields
            if not ticker:
                return False
            if not holdings_str:
                return False
            if not last_price_str:
                return False

            # Get dates - handle both DateEntry and StringVar
            if TKCALENDAR_AVAILABLE:
                try:
                    start_date = self.start_date_entry.get_date()
                    end_date = self.end_date_entry.get_date()
                except Exception:
                    return False
            else:
                if not start_date_str:
                    return False
                if not end_date_str:
                    return False
                try:
                    start_date = self.parse_date(start_date_str)
                    end_date = self.parse_date(end_date_str)
                except Exception:
                    return False

            if not sdn_str:
                return False
            if not profit_str:
                return False

            # Try to parse values to ensure they're valid
            holdings = self.parse_holdings(holdings_str)
            last_price = self.parse_price(last_price_str)
            sdn = int(sdn_str)
            profit = float(profit_str)

            # Basic validation
            if holdings <= 0 or last_price <= 0:
                return False
            if start_date >= end_date:
                return False
            if sdn < 2 or sdn > 20:
                return False
            if profit < 0 or profit > 200:
                return False

            return True

        except (ValueError, TypeError):
            return False

    def set_default_dates(self):
        """Set default start and end dates."""
        from datetime import date, timedelta

        today = date.today()
        one_year_ago = today - timedelta(days=365)

        if TKCALENDAR_AVAILABLE:
            self.start_date_entry.set_date(one_year_ago)
            self.end_date_entry.set_date(today)
        else:
            self.start_date_var.set(one_year_ago.isoformat())
            self.end_date_var.set(today.isoformat())

    @staticmethod
    def parse_date(date_str: str) -> date:
        """Parse a date string in YYYY-MM-DD format."""
        from datetime import datetime

        try:
            return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD format.")

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
    def format_holdings(holdings: float, ticker: str = "") -> str:
        """Format holdings with commas for readability.

        For assets that support fractional shares, shows decimal places.
        For assets that don't support fractional shares, rounds to whole numbers.
        """
        if ticker:
            try:
                from src.data.asset import Asset

                asset = Asset(ticker)
                if asset.supports_fractional_shares:
                    return f"{holdings:,.4f}"
            except Exception:
                pass  # Fall back to whole number formatting on error

        # Default: format as whole numbers with commas
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
                self.format_holdings(params.get("holdings", 0), ticker)
                if params.get("holdings")
                else ""
            )
            self.last_price_var.set(
                self.format_price(params.get("last_price", 0)) if params.get("last_price") else ""
            )
            # Set dates from history or use defaults
            start_date = params.get("start_date")
            if start_date:
                if TKCALENDAR_AVAILABLE:
                    from datetime import datetime

                    self.start_date_entry.set_date(datetime.fromisoformat(start_date).date())
                else:
                    self.start_date_var.set(start_date)
            end_date = params.get("end_date")
            if end_date:
                if TKCALENDAR_AVAILABLE:
                    from datetime import datetime

                    self.end_date_entry.set_date(datetime.fromisoformat(end_date).date())
                else:
                    self.end_date_var.set(end_date)
            # Note: current_price is now fetched from market data
            self.sdn_var.set(params.get("sdn", ""))
            self.profit_var.set(params.get("profit", ""))
            bracket_seed = params.get("bracket_seed")
            if bracket_seed is not None:
                self.bracket_seed_var.set(self.format_price(bracket_seed))
            else:
                self.bracket_seed_var.set("")

            # Trigger auto-calculation after loading ticker data
            self.schedule_auto_calculation()

    def on_ticker_selected(self, event):
        """Handle ticker selection - load defaults and trigger auto-calculation."""
        ticker = self.ticker_var.get()
        if ticker in self.history:
            params = self.history[ticker]
            self.holdings_var.set(
                self.format_holdings(params.get("holdings", 0), ticker)
                if params.get("holdings")
                else ""
            )
            self.last_price_var.set(
                self.format_price(params.get("last_price", 0)) if params.get("last_price") else ""
            )
            # Set dates from history or use defaults
            start_date = params.get("start_date")
            if start_date:
                if TKCALENDAR_AVAILABLE:
                    from datetime import datetime

                    self.start_date_entry.set_date(datetime.fromisoformat(start_date).date())
                else:
                    self.start_date_var.set(start_date)
            end_date = params.get("end_date")
            if end_date:
                if TKCALENDAR_AVAILABLE:
                    from datetime import datetime

                    self.end_date_entry.set_date(datetime.fromisoformat(end_date).date())
                else:
                    self.end_date_var.set(end_date)
            # Note: current_price is now fetched from market data
            self.sdn_var.set(params.get("sdn", ""))
            self.profit_var.set(params.get("profit", ""))
            bracket_seed = params.get("bracket_seed")
            if bracket_seed is not None:
                self.bracket_seed_var.set(self.format_price(bracket_seed))
            else:
                self.bracket_seed_var.set("")

            # Trigger auto-calculation after loading ticker data
            self.schedule_auto_calculation()

    def calculate_orders(self):
        """Calculate and display orders."""
        try:
            # Get inputs
            ticker = self.ticker_var.get().strip()
            holdings = self.parse_holdings(self.holdings_var.get())
            last_price = self.parse_price(self.last_price_var.get())

            # Get dates - handle both DateEntry and StringVar
            if TKCALENDAR_AVAILABLE:
                start_date = self.start_date_entry.get_date()
                end_date = self.end_date_entry.get_date()
            else:
                start_date = self.parse_date(self.start_date_var.get())
                end_date = self.parse_date(self.end_date_var.get())

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
            if last_price <= 0:
                raise ValueError("Last price must be positive")
            if start_date >= end_date:
                raise ValueError("Start date must be before end date")
            if sdn < 2 or sdn > 20:
                raise ValueError("SDN must be between 2 and 20")
            if profit < 0 or profit > 200:
                raise ValueError("Profit must be between 0 and 200")

            # Fetch current price from market data
            asset = Asset(ticker)
            price_df = asset.get_prices(start_date, end_date)
            if price_df.empty:
                raise ValueError(
                    f"No price data available for {ticker} between {start_date} and {end_date}"
                )

            # Calculate current price based on end_date
            today = date.today()

            if end_date >= today:
                # For today or future dates, use the most recent available close price
                current_price = float(price_df.iloc[-1]["Close"])
            else:
                # For past dates, use average of open and close for that specific date
                try:
                    # Convert end_date to pandas Timestamp for indexing
                    end_date_ts = pd.Timestamp(end_date)
                    if end_date_ts in price_df.index:
                        # Get the row for the specific date
                        row = price_df.loc[end_date_ts]
                        current_price = (float(row["Open"]) + float(row["Close"])) / 2.0
                    else:
                        # If exact date not found, use the last available close price
                        current_price = float(price_df.iloc[-1]["Close"])
                except (KeyError, IndexError):
                    # Fallback to last available close price
                    current_price = float(price_df.iloc[-1]["Close"])

            # Update current price display
            self.current_price_var.set(
                f"{self.format_price(current_price)} on {end_date.isoformat()}"
            )

            # Update fields to canonical format
            self.holdings_var.set(self.format_holdings(holdings, ticker))
            self.last_price_var.set(self.format_price(last_price))
            # Note: current_price is now fetched from market data, not displayed in UI
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

            # Check if asset supports fractional shares
            asset = Asset(ticker)
            supports_fractional = asset.supports_fractional_shares

            # Format quantity: use int() only for assets that don't support fractional shares
            if supports_fractional:
                buy_qty_display = f"{buy_qty:.4f}"
                sell_qty_display = f"{sell_qty:.4f}"
            else:
                buy_qty_display = f"{int(buy_qty)}"
                sell_qty_display = f"{int(sell_qty)}"

            buy_order_text = (
                f"BUY {ticker} {buy_qty_display} @ ${buy_price:.2f} = ${buy_amount:.2f}"
            )
            sell_order_text = (
                f"SELL {ticker} {sell_qty_display} @ ${sell_price:.2f} = ${sell_amount:.2f}"
            )

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
                # Note: current_price is now fetched from market data, not stored in history
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
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
                messagebox.showwarning(
                    "Warning", "No buy order calculated. Please calculate orders first."
                )
                return

            # Get current holdings
            holdings_str = self.holdings_var.get().strip()
            current_holdings = float(holdings_str.replace(",", "")) if holdings_str else 0.0

            # Update holdings (add bought shares)
            new_holdings = current_holdings + self.current_buy_qty

            # Update last price and current price to the buy execution price
            execution_price = self.current_buy_price
            self.last_price_var.set(self.format_price(execution_price))
            self.current_price_var.set(
                f"{self.format_price(execution_price)} on {date.today().isoformat()}"
            )

            # Update holdings
            self.holdings_var.set(self.format_holdings(new_holdings, self.ticker_var.get().strip()))

            # Recalculate orders with new position
            self.calculate_orders()

            # Format quantity for status message based on asset type
            asset = Asset(self.ticker_var.get().strip())
            if asset.supports_fractional_shares:
                qty_display = f"{self.current_buy_qty:.4f}"
            else:
                qty_display = f"{int(self.current_buy_qty)}"

            self.status_var.set(f"Executed BUY: {qty_display} shares @ ${execution_price:.2f}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to execute buy order: {str(e)}")

    def execute_sell_order(self):
        """Execute the calculated sell order by updating position and recalculating."""
        try:
            if self.current_sell_price <= 0 or self.current_sell_qty <= 0:
                messagebox.showwarning(
                    "Warning", "No sell order calculated. Please calculate orders first."
                )
                return

            # Get current holdings
            holdings_str = self.holdings_var.get().strip()
            current_holdings = float(holdings_str.replace(",", "")) if holdings_str else 0.0

            # Check if we have enough shares to sell
            if current_holdings < self.current_sell_qty:
                messagebox.showwarning(
                    "Warning",
                    f"Insufficient holdings. Have {current_holdings:.0f} shares, trying to sell {self.current_sell_qty:.0f} shares.",
                )
                return

            # Update holdings (subtract sold shares)
            new_holdings = current_holdings - self.current_sell_qty

            # Update last price and current price to the sell execution price
            execution_price = self.current_sell_price
            self.last_price_var.set(self.format_price(execution_price))
            self.current_price_var.set(
                f"{self.format_price(execution_price)} on {date.today().isoformat()}"
            )

            # Update holdings
            self.holdings_var.set(self.format_holdings(new_holdings, self.ticker_var.get().strip()))

            # Recalculate orders with new position
            self.calculate_orders()

            # Format quantity for status message based on asset type
            asset = Asset(self.ticker_var.get().strip())
            if asset.supports_fractional_shares:
                qty_display = f"{self.current_sell_qty:.4f}"
            else:
                qty_display = f"{int(self.current_sell_qty)}"

            self.status_var.set(f"Executed SELL: {qty_display} shares @ ${execution_price:.2f}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to execute sell order: {str(e)}")

    def show_help(self):
        """Show help documentation in a scrollable window with markdown rendering if available."""
        try:
            # Read the help file
            help_file_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "docs", "HOW_TO_order_gui.md"
            )
            with open(help_file_path, "r", encoding="utf-8") as f:
                help_content = f.read()

            # Create help window
            help_window = tk.Toplevel(self.root)
            help_window.title("Order Calculator GUI - Help")
            help_window.geometry("900x700")

            if MARKDOWN_AVAILABLE:
                # Use HTML rendering for better formatting
                html_content = markdown.markdown(help_content, extensions=["extra", "codehilite"])

                # Add some basic CSS styling
                styled_html = f"""
                <html>
                <head>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        margin: 20px;
                        background-color: #f5f5f5;
                    }}
                    h1 {{
                        color: #2c3e50;
                        border-bottom: 2px solid #3498db;
                        padding-bottom: 10px;
                    }}
                    h2 {{
                        color: #34495e;
                        margin-top: 30px;
                        border-left: 4px solid #3498db;
                        padding-left: 10px;
                    }}
                    h3 {{
                        color: #7f8c8d;
                    }}
                    code {{
                        background-color: #ecf0f1;
                        padding: 2px 4px;
                        border-radius: 3px;
                        font-family: 'Courier New', monospace;
                    }}
                    pre {{
                        background-color: #ecf0f1;
                        padding: 10px;
                        border-radius: 5px;
                        overflow-x: auto;
                    }}
                    ul, ol {{
                        margin-left: 20px;
                    }}
                    li {{
                        margin: 5px 0;
                    }}
                    strong {{
                        color: #2c3e50;
                    }}
                </style>
                </head>
                <body>
                {html_content}
                </body>
                </html>
                """

                # Create HTML frame
                html_frame = tkinterweb.HtmlFrame(help_window)
                html_frame.load_html(styled_html)
                html_frame.pack(fill=tk.BOTH, expand=True)
            else:
                # Fallback to plain text display
                help_text = scrolledtext.ScrolledText(help_window, wrap=tk.WORD, padx=10, pady=10)
                help_text.pack(fill=tk.BOTH, expand=True)
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
                from src.data.asset import Asset

                asset = Asset(ticker)
                # Use the selected date range for chart visualization
                if TKCALENDAR_AVAILABLE:
                    start_date = self.start_date_entry.get_date()
                    end_date = self.end_date_entry.get_date()
                else:
                    # Fallback to default dates if tkcalendar not available
                    end_date = date.today()
                    start_date = end_date - timedelta(days=365)
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
                        ticker,
                        last_price,
                        sdn,
                        self.profit_var.get(),
                        bracket_seed,
                        df,
                        start_date,
                        end_date,
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
                initial_qty=int(holdings),
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
                self.ax.scatter(
                    buy_dates,
                    buy_prices,
                    color="red",
                    s=30,
                    alpha=0.8,
                    label="Buy Signals",
                    zorder=5,
                )

            if sell_signals:
                sell_dates, sell_prices = zip(*sell_signals)
                self.ax.scatter(
                    sell_dates,
                    sell_prices,
                    color="green",
                    s=30,
                    alpha=0.8,
                    label="Sell Signals",
                    zorder=5,
                )

            # Add signal count inset in lower right
            total_buys = len(buy_signals)
            total_sells = len(sell_signals)

            # Create inset text box
            inset_text = f"Signals\nBuys: {total_buys}\nSells: {total_sells}"
            self.ax.text(
                0.98,
                0.02,
                inset_text,
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
                magnitude_price = 2.0**power
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
                base_price = 2.0**power
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
