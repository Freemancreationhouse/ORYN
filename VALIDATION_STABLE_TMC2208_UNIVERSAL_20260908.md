# Validation — ORYN Stable TMC2208 + Universal Controller

Build: `UC-DUNE-MOTION-V9-STABLE-DRIVER-NEUTRAL-20260908-1`

## Source baseline

Trusted source: user-uploaded `ORYN_PI_PATTERN_FORGE_PRO_V10_4_1_HOTFIX(6).zip`.

## Locked-file preservation checks

Byte-for-byte unchanged from the trusted source:

- `modules/connection/connection_manager.py`
- `modules/core/process_thr.py`
- `modules/core/state.py`
- `modules/core/playlist_manager.py`
- `modules/pattern_generator/converter.py`
- `settings.json`
- `state.json`

## Motion-core scope

`modules/core/pattern_manager.py` differs in one localized end-of-pattern synchronization block only. The coupled Theta–Rho transform, calibration scaling, coupling compensation, feed planning, GRBL relative move generation, first-point Idle gate, clear sequencing and pattern iteration are unchanged.

## Driver profile safety

PASS — TMC2208 standalone physical choices are restricted to 1/2, 1/4, 1/8 and 1/16.

PASS — driver-profile Apply saves metadata only.

PASS — driver-profile Apply contains no `$100/$101` or FluidNC `steps_per_mm` write.

PASS — old microstep/new microstep multiplication has been removed from the profile-apply path.

## Controller support

PASS — existing USB serial auto-detection remains untouched.

PASS — existing firmware detection for GRBL vs FluidNC remains untouched.

PASS — additive controller endpoint supports explicit USB serial selection.

PASS — additive controller endpoint supports FluidNC WebSocket host/port selection.

PASS — controller transport selection does not modify pattern math or calibration.

## Progress / preview end synchronization

PASS — final 100% update occurs after `check_idle_async()`.

PASS — execution time is logged after the same physical Idle gate.

PASS — clear/main sequencing remains the original source behavior.

## Static checks

PASS — Python syntax compile for modified Python files.

PASS — JavaScript syntax check for additive/modified custom UI scripts.
