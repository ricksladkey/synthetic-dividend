#!/usr/bin/env python
"""Launch Synthetic Dividend Order Calculator GUI without console window.

Double-click this file in Windows to launch the order calculator
without showing a console window.

On Windows, .pyw files are associated with pythonw.exe which runs
Python scripts without creating a console window.
"""

from src.tools.order_calculator_gui import main

if __name__ == "__main__":
    main()
