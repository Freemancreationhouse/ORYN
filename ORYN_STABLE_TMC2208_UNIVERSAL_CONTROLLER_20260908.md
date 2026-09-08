# ORYN Pi V10.4.1 — Stable TMC2208 + Universal Controller Recovery Build

Build: **UC-DUNE-MOTION-V9-STABLE-DRIVER-NEUTRAL-20260908-1**

Base: the user-supplied `ORYN_PI_PATTERN_FORGE_PRO_V10_4_1_HOTFIX(6).zip`, treated as the trusted A4988 working baseline.

## Why this recovery build exists

The earlier TMC2208 package carried extra source/frontend changes and automatically rescaled controller steps/unit when the driver profile changed. That is too risky for a machine whose Theta–Rho motion was already physically proven.

This build returns to the supplied working motion source and makes the driver layer **metadata-only**.

## What is preserved from the supplied working baseline

The following are preserved from the uploaded source:

- Theta–Rho coupled motion transform
- Dune-compatible theta→rho coupling mathematics
- Full Circle calibration geometry
- Centre→Perimeter calibration geometry
- clearing pattern selection and sequencing
- pattern parsing and execution
- queue / playlist logic
- homing logic
- Pattern Forge
- saved settings/state format
- connection manager motion transactions

`modules/core/pattern_manager.py` has one intentional synchronization change only: the UI is not allowed to report 100% until the controller reports physical `Idle` after the final queued segment.

## TMC2208 behavior

TMC2208 remains a normal STEP/DIR driver. ORYN does not need a different pattern engine for it.

For standalone TMC2208:

- MS1 LOW + MS2 LOW → 1/8 external STEP resolution
- MS1 HIGH + MS2 LOW → 1/2
- MS1 LOW + MS2 HIGH → 1/4
- MS1 HIGH + MS2 HIGH → 1/16

Internal MicroPlyer interpolation is not used as the GRBL/FluidNC external microstep value.

### Important change

Selecting A4988 / TMC2208 / TMC2209 / DRV8825 / etc. in ORYN now **does not modify `$100`, `$101`, or FluidNC `steps_per_mm`**. It saves driver metadata only.

This prevents:

- double scaling
- old-profile scaling being applied again
- a wrong assumed A4988 jumper state modifying controller geometry
- driver selection changing a previously calibrated motion system

## Recovery test for the current Uno + CNC Shield + TMC2208 machine

The last known A4988 GRBL values reported by the machine were:

- `$100=25.625`
- `$101=17.938`
- `$110=900.000`
- `$111=3000.000`
- `$120=30.000`
- `$121=30.000`

If the controller still contains the automatically multiplied TMC values from the earlier hotfix, a conservative diagnostic is to restore only `$100` and `$101` to the known working controller-unit values above, then redo Full Circle and Centre→Perimeter calibration with the TMC2208 physically installed. This will make motion slower than the A4988 at the same ORYN speed, but it isolates software geometry from TMC current/missed-step problems.

Do not change these values automatically on other machines; they are specific to this machine's known prior GRBL state.

## Controller compatibility

ORYN now exposes an additive **Universal Controller Connection** panel. It does not participate in motion mathematics.

Supported connection classes:

- Arduino Uno / ATmega328P running standard GRBL over USB serial
- Arduino Nano / compatible GRBL over USB serial
- ATmega2560 boards running GRBL-compatible firmware over USB serial
- MKS DLC (ATmega/GRBL-compatible) over USB serial
- MKS DLC32 directly over USB serial when its firmware presents a GRBL-compatible interface
- MKS DLC32 / ESP32-class boards running FluidNC over USB serial
- FluidNC network controllers over WebSocket (`ws://HOST:81`)
- other controllers that implement the standard GRBL 1.1 / FluidNC command and status behavior ORYN uses

This does not mean arbitrary non-GRBL firmware is automatically compatible.

## MKS DLC32 note

MKS DLC32 already has its own ESP32-family MCU on the controller board. When using the DLC32 as the actual GRBL/FluidNC controller, no separate external ESP32 bridge is required.

## UI synchronization correction

Previously the backend could emit 100% after the final THR coordinate had been accepted into the controller planner even though the last planner blocks were still physically moving. The main pattern correctly waited for Idle before starting, but the web UI could look finished early.

Now:

1. THR points are streamed using the original working motion path.
2. after the final point is accepted, progress remains below 100%.
3. ORYN waits for the controller's actual `Idle` status.
4. only then does progress become 100% and the next clear/pattern stage proceed visually.

