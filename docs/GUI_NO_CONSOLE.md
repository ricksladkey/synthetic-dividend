# Running GUI Applications Without Console Window

## Problem

On Windows, when you launch a tkinter GUI application (like `sd-calc-orders`), a console window appears behind the GUI. This looks unprofessional and confuses users.

## Solutions

### Solution 1: Use `pythonw.exe` (Quick & Easy)

Instead of running:
```bash
python -m src.tools.order_calculator_gui
```

Use `pythonw.exe` (note the 'w'):
```bash
pythonw -m src.tools.order_calculator_gui
```

Or if installed as a package script:
```bash
# Find where pythonw is
where pythonw

# Use it to run the GUI
pythonw -c "from src.tools.order_calculator_gui import main; main()"
```

### Solution 2: Modern `gui-scripts` in pyproject.toml (Recommended)

**Status**: Configured in `pyproject.toml` but requires setuptools >= 75.0

```toml
[project.gui-scripts]
# These run without console window on Windows
sd-calc-orders = "src.tools.order_calculator_gui:main"
sd-plotter = "src.compare.plotter:main"
```

**How it works**:
- On Windows: Creates `.exe` launchers that use Windows GUI subsystem (no console)
- On Unix/Linux: Same as regular scripts (no difference)

**Requirements**:
- setuptools >= 75.0 (released August 2024)
- Python >= 3.8

**To upgrade setuptools**:
```bash
pip install --upgrade "setuptools>=75.0"
pip install -e ".[gui]"
```

After upgrading, `sd-calc-orders.exe` will launch without a console window.

### Solution 3: Create a `.pyw` file (Traditional)

Create a file `launch_calculator.pyw` (note the `.pyw` extension):

```python
#!/usr/bin/env python
"""Launch order calculator GUI without console."""
from src.tools.order_calculator_gui import main

if __name__ == "__main__":
 main()
```

**Usage**:
- Double-click the `.pyw` file in Windows Explorer
- Or run: `pythonw launch_calculator.pyw`

**How it works**:
- `.pyw` files are associated with `pythonw.exe` instead of `python.exe`
- Windows launches them without a console window

### Solution 4: Create a Windows Shortcut

1. Right-click on Desktop → New → Shortcut
2. Enter target:
 ```
 C:\path\to\.venv\Scripts\pythonw.exe -m src.tools.order_calculator_gui
 ```
3. Name it "Synthetic Dividend Order Calculator"
4. Optionally: Right-click → Properties → Change Icon

### Solution 5: Build a Standalone .exe (Advanced)

Use PyInstaller to create a true standalone executable:

```bash
# Install PyInstaller
pip install pyinstaller

# Build GUI exe (--windowed = no console)
pyinstaller --name "SD-Calculator" \
 --windowed \
 --onefile \
 src/tools/order_calculator_gui.py

# Output in dist/SD-Calculator.exe
```

**Pros**:
- Single `.exe` file, no Python installation needed
- Professional distribution

**Cons**:
- Large file size (~15-30 MB)
- Slower startup
- Antivirus false positives

## Current Project Status

**As of November 2024**:

[OK] **WORKING**: setuptools >= 75.0 is now required in `pyproject.toml`
[OK] **Configured**: `[project.gui-scripts]` creates console-less executables
[OK] **Verified**: `sd-calc-orders.exe` uses Windows GUI subsystem (no console)

## Recommended User Instructions

**Primary Method** (Simplest - No Console):
```bash
pip install -e ".[gui]"
sd-calc-orders # Launches GUI without console!
```

**Alternative Methods**:

**Option A**: Use pythonw directly
```bash
pythonw -m src.tools.order_calculator_gui
```

**Option B**: Double-click the .pyw file
```bash
# Just double-click this in Windows Explorer:
launch_calculator.pyw
```

**Option C**: Create a desktop shortcut
1. Right-click Desktop → New → Shortcut
2. Target: `sd-calc-orders` (or full path to .exe)
3. Name: "Order Calculator"

## Technical Details

### Windows Subsystem Types

Windows executables have a "subsystem" field:
- **Console (3)**: Shows console window, can print to stdout/stderr
- **GUI (2)**: No console window, GUI-only application

### Python Executables

- `python.exe`: Console subsystem (shows black window)
- `pythonw.exe`: GUI subsystem (no console window)

### How gui-scripts Works

Modern setuptools (75.0+) generates entry point executables that:
1. Check if script is in `[project.gui-scripts]`
2. If yes: Use GUI subsystem (like pythonw.exe)
3. If no: Use console subsystem (like python.exe)

Older setuptools versions always use console subsystem.

## Testing Console Behavior

To verify if an executable uses GUI subsystem:

```python
import struct

with open('sd-calc-orders.exe', 'rb') as f:
 # Find PE header
 f.seek(0x3C)
 pe_offset = struct.unpack('<I', f.read(4))[0]

 # Read subsystem field
 f.seek(pe_offset + 24 + 68)
 subsystem = struct.unpack('<H', f.read(2))[0]

 print("GUI subsystem" if subsystem == 2 else "Console subsystem")
```

## References

- [PEP 397 - Python launcher for Windows](https://peps.python.org/pep-0397/)
- [setuptools gui_scripts documentation](https://setuptools.pypa.io/en/latest/userguide/entry_point.html#gui-scripts)
- [Python on Windows FAQ](https://docs.python.org/3/faq/windows.html)
- [PyInstaller documentation](https://pyinstaller.org/)
