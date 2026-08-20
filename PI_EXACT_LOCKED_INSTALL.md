# ORYN Raspberry Pi — Exact Locked Application Build

Application source is the exact user-approved:
`Studio_Kinematics_ORYN_FINAL_TWO_CORRECTIONS_ONLY.zip`

No ORYN application/UI/motion files were replaced from another version.
Only Raspberry Pi deployment support is different:
- `requirements-pi.txt` excludes the Pi-5-only NeoPixel package.
- `setup-pi.sh` installs `requirements-pi.txt`.
- `oryn update` installs `requirements-pi.txt`.
- `verify-locked-pi.sh` verifies locked features are physically present on Pi.

After GitHub sync on Pi:

```bash
cd ~/oryn
./verify-locked-pi.sh
```

The result must say:
`RESULT: LOCKED ORYN APPLICATION FILES PRESENT`
