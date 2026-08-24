# ORYN FINAL PI GITHUB SOURCE

This repository was rebuilt from the user's trusted **ORYN(2) desktop master**.

## Source-of-truth rule

The desktop UI/runtime is the master. The Raspberry Pi does **not** have a
separate visual design and does **not** use a Pi-only theme override.

The following desktop-master areas are copied byte-for-byte:
- `main.py`
- `frontend/src/`
- `static/dist/` (prebuilt desktop runtime)
- `static/custom/` (final UI overlays, Pattern Forge/Delete/visual fixes)

The only intentional Pi-specific update in this package is the networking layer:
- `modules/wifi/manager.py`
- `wifi/autohotspot`
- `wifi/setup-wifi.sh`

These contain the safe multi-network + autohotspot recovery work:
- remember multiple saved Wi-Fi networks
- test new credentials before replacing a same-SSID profile
- preserve other saved networks
- use `ORYNMotion-Hotspot`
- start ORYN hotspot when there is no genuine client connection + IPv4

## Important: do NOT rebuild the frontend on Raspberry Pi

The Pi Zero 2 W uses the prebuilt desktop-master runtime already committed under:

`static/dist/`

Do not run `npm ci` or `npm run build` on the Pi. `setup-pi.sh` is already
designed for a prebuilt frontend and removes Node/npm if they are present.

## Install on a fresh Raspberry Pi

```bash
sudo apt update
sudo apt install -y git
cd ~
git clone https://github.com/Freemancreationhouse/ORYN.git oryn
cd ~/oryn
chmod +x setup-pi.sh
sudo ./setup-pi.sh
```

After setup:

```bash
./verify-final-pi-source.sh
sudo systemctl restart oryn
```

Open:
- `http://oryn.local`
- or the Pi IP shown by the installer.

## Expected UI parity

The Pi webpage and mobile WebView receive the same desktop-master runtime:
- Pattern Forge
- Delete Pattern
- Perimeter Calibration
- final Clear-option styling (no solid yellow selected tile)
- final dark/light theme behavior
- final header/logo behavior
- final footer/navigation overlays

No `static/custom/oryn-pi-visual-only.css` is used.

## Verification

Run:

```bash
chmod +x verify-final-pi-source.sh
./verify-final-pi-source.sh
```

Expected:

`RESULT: ORYN FINAL PI SOURCE READY`
