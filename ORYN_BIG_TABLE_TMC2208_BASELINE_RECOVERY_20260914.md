# ORYN Big-Table TMC2208 Baseline Recovery — 2026-09-14

Base: exact user-supplied working A4988 package `ORYN_PI_PATTERN_FORGE_PRO_V10_4_1_HOTFIX(6).zip`.

## Purpose
Restore the physically proven big-table ORYN motion/clear/calibration execution after later TMC2208 compatibility experiments incorrectly introduced Mini-profile assumptions and other motion-layer changes.

## Hardware
- Host: Raspberry Pi
- Motion controller: Arduino Uno + CNC Shield / GRBL
- Driver: TMC2208 standalone STEP/DIR
- Current GRBL scale: X `$100=205.000`, Y `$101=143.504`
- Previous proven A4988 scale: X `$100=25.625`, Y `$101=17.938`

The TMC values are exactly 8x the prior A4988 values on both axes. Therefore the X:Y step ratio and the original big-table coupling mathematics are unchanged. No Mini mechanism profile is used.

## Restored from the proven baseline
- main.py
- machine_profile.json
- modules/connection/connection_manager.py
- modules/connection/fluidnc_config.py
- modules/core/pattern_manager.py
- modules/core/process_thr.py
- SetupPage source and served compiled frontend files touched by later driver experiments

## Important
Do not use the previous Mini-profile patch. Do not change `$100/$101` again. Do not press Apply Driver/Microstep during the first recovery test. First verify Home, 360°, Perimeter, then Adaptive clear and a simple pattern.

If the radial motor still stops physically after several spiral turns while GRBL/UI continue, the original software is now restored and the remaining fault is open-loop TMC2208 motor current/torque/driver setup, not ORYN path mathematics.
