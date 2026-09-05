# ORYN Pi V10.4.1 — TMC2208 + Arduino Uno/GRBL Hotfix

Build: `UC-DUNE-MOTION-V9-TMC2208-UNO-GRBL-HOTFIX-20260905-2`

This is a targeted compatibility hotfix for the locked ORYN Pi V10.4.1 baseline when changing a working Arduino Uno + CNC Shield machine from A4988 to TMC2208 standalone STEP/DIR.

## Confirmed hardware baseline

- Controller: Arduino Uno running GRBL
- Shield: CNC Shield
- Previous driver: A4988
- Previous shield microstep jumpers: none -> A4988 full-step (1/1)
- New driver: TMC2208 standalone STEP/DIR
- New shield microstep jumpers: none -> TMC2208 1/8 STEP-input resolution
- Existing GRBL values before migration: `$100=25.625`, `$101=17.938`
- Correct migrated values: `$100=205.000`, `$101=143.504`

## What this hotfix changes

1. Machine Profile reads Arduino GRBL motion settings through `$$` instead of sending FluidNC-only config-tree queries.
2. Machine Profile writes X/Y step scale through the GRBL-compatible `$100/$101` settings.
3. GRBL `$100/$101` changes are treated as persistent immediately; ORYN does not try to run FluidNC `$CD` save commands on an Uno.
4. First migration baseline is A4988 full-step (1/1), matching the no-jumper CNC Shield configuration.
5. TMC2208 no-jumper mode is represented as 1/8.
6. Locked Theta-Rho geometry, Dune motion core, calibration math, patterns, Pattern Forge, UI/branding, playlists and playback behavior are otherwise unchanged.

## One-time migration in ORYN

With the old GRBL values still present (`25.625` / `17.938`), select TMC2208 and 1/8 for X and Y, then use **Apply Driver / Microstep** once. ORYN will scale the values by 8 to approximately `205.000` and `143.504`.

Do not manually multiply `$100/$101` and then also run the first-time Apply operation, because that would apply the microstep ratio twice.
