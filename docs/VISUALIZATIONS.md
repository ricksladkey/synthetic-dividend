# Visualization guide

This document explains how to generate the example visualization PNGs used in the repository.

Prerequisites
- A working Python 3.11 virtual environment for this project (recommended path: `.venv`).
- The project dependencies installed into that venv. In particular, `matplotlib` is required for plotting.

Quick steps (Windows PowerShell, from repo root)

```powershell
# Install dependencies into the project's venv (if not already installed)
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install matplotlib

# Run the pre-made example batch (no need to Activate the venv; the script invokes the venv python)
.\test-visualization.bat
```

Notes
- The `test-visualization.bat` script calls the venv Python directly so you don't need to run `Activate.ps1` first.
- The runner and other CLI tools expect the *modern* algorithm naming convention. Examples:
 - `buy-and-hold`
 - `sd8` (exponential shorthand)
 - `sd-9.05,50` (explicit rebalance percent and profit sharing)

What the script produces
- PNG files in the repository root, e.g. `out-nvda-sd-full.png`.
- Transaction logs saved next to each PNG as `*-tx.txt`.

Troubleshooting
- If you see `ModuleNotFoundError: No module named 'matplotlib'`, install `matplotlib` into the project's venv as shown above.
- If the runner raises `Unrecognized algorithm name`, update the algorithm id to the modern naming convention.

If you want these visuals to run in CI, consider adding an extra job that installs plotting deps (matplotlib) and gates the visual generation behind an environment variable to avoid heavy CI runs by default.