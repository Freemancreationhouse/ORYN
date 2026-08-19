# ORYN Raspberry Pi Zero 2 W — Locked Windows Baseline Port

This Raspberry Pi release is built from the user-confirmed locked Windows baseline:
`Studio_Kinematics_ORYN_FINAL_TWO_CORRECTIONS_ONLY`.

## Lock rule
No application UI, Pattern Forge behavior, Theta–Rho motion/core, perimeter calibration,
delete behavior, branding/footer, dark mode, or other working application behavior was changed.

Only Raspberry Pi deployment files were prepared/hardened for direct GitHub installation.

## Target
- Raspberry Pi Zero 2 W
- Raspberry Pi OS Lite 64-bit
- USB controller first (recommended)
- Wi-Fi web access at `http://oryn.local`
- systemd autostart
- nginx on port 80
- backend on localhost:8080

## Direct GitHub install
```bash
curl -fsSL https://raw.githubusercontent.com/Freemancreationhouse/ORYN/main/install-pi-from-github.sh | bash
```

Then reboot if requested:
```bash
sudo reboot
```

Check:
```bash
oryn status
oryn logs
```
