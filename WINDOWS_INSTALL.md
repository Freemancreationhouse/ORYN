# ORYN — Windows Installation

## Quick install

1. On GitHub, click **Code → Download ZIP**.
2. Extract the ZIP completely.
3. Open the ORYN folder.
4. Double-click `install-oryn-windows.bat`.
5. When installation finishes, double-click `run-oryn-windows.bat`.

You can also use `ORYN-Windows-Setup-and-Run.bat` for first-time setup and launch.

## Requirements

- Windows 10 or Windows 11, 64-bit
- Python 3.11 or 3.12
- USB connection to the controller is recommended for first setup

## Git install

```powershell
git clone https://github.com/Freemancreationhouse/ORYN.git
cd ORYN
.\install-oryn-windows.bat
.\run-oryn-windows.bat
```

## Update later

```powershell
git pull origin main
```

Then run `install-oryn-windows.bat` again if dependencies changed.
