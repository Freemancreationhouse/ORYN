# ORYN Pi — TMC2208 Compatibility Hotfix

Build: **UC-DUNE-MOTION-V9-TMC2208-HOTFIX-20260905-1**

Base: locked ORYN Pi / Pattern Forge V10.4.1 package supplied by the user.

## Scope
Only the STEP/DIR driver-profile compatibility layer and its on-screen guidance were changed. ORYN THR mathematics, coupled Theta–Rho execution, calibration geometry, Pattern Forge, patterns, Wi-Fi, branding, playlists, and other locked behavior are preserved.

## Correction
The previous Universal Machine Profile exposed 1/32, 1/64, 1/128 and 1/256 as physical TMC2208 microstep selections. That is not correct for the standalone STEP/DIR mode used by this ORYN controller profile.

Standalone TMC2208 external STEP-input resolution:

- MS1 LOW, MS2 LOW → 1/8
- MS1 HIGH, MS2 LOW → 1/2
- MS1 LOW, MS2 HIGH → 1/4
- MS1 HIGH, MS2 HIGH → 1/16

The TMC2208 may internally interpolate those input steps to 256 microsteps. That interpolation is internal to the driver and must not be entered as 1/256 in ORYN steps/unit scaling.

## A4988 → TMC2208 migration
1. Power the table off before changing the driver or jumpers.
2. Install the TMC2208 as a STEP/DIR driver and verify the carrier-board pinout, motor supply, logic supply/common ground, coil pairs, EN/STEP/DIR, and current/VREF.
3. TMC2208 standalone uses MS1/MS2 for microstep selection; do not assume an A4988 MS3 jumper has the same function on every carrier board.
4. Start ORYN and connect to the controller.
5. Open **Hardware Setup → Universal Machine Profile**.
6. Select **TMC2208** on X and Y and select the actual physical microstep setting. If there are no MS jumpers, select **1/8**.
7. Press **Apply Driver / Microstep** once. ORYN rescales FluidNC steps/unit relative to the saved/legacy profile.
8. Re-check Full Circle (360°) and Centre→Perimeter calibration. These remain the final physical geometry authority.

## Important hardware note
TMC2208 is STEP/DIR compatible with A4988-style control, so ORYN does not need different pattern mathematics. If the motor does not energize or move at all after this software correction, the remaining cause is normally outside the ORYN motion math: driver enable/power, carrier pinout/orientation, current/VREF, motor coil pairing, or controller wiring.
