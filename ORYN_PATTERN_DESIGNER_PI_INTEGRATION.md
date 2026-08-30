# ORYN Pattern Designer V2.0 Pro — Pi Integration

Integration marker: `PD-PI-V1-20260831-1`

Base supplied by user:
- Git commit: `96426e91bcedf454662db936b20684094c826fee`
- Commit message: `ORYN V10.4.1 - fix queued pattern continuation after clearing`
- Pattern Forge: `PF-PRO-V10.4.1-20260828-1`
- Motion baseline: `UC-DUNE-MOTION-V9-20260827-1`

## Integration design

Pattern Designer remains isolated from the locked motion application. ORYN serves the designer as a first-class full-screen page at `/pattern-designer`; the existing Browse Patterns toolbar receives one additive `Pattern Designer` launcher through a small backend-injected UI script. No React bundle rebuild is required, so the locked compiled ORYN interface remains intact.

The only backend bridge is `POST /api/pattern-designer/save`. It validates the generated THR text, rejects malformed/non-finite/out-of-radius coordinates, writes the unchanged THR text into `patterns/custom_patterns`, and asks ORYN's existing preview cache generator to create the normal library thumbnail. It never calls motion, homing, calibration, clearing, serial, queue execution, or Pattern Forge conversion logic.

## Added

- `static/pattern-designer/index.html`
- `static/pattern-designer/app.js`
- `static/pattern-designer/styles.css`
- `static/custom/oryn-pattern-designer-integration.js`
- `ORYN_PATTERN_DESIGNER_V2_GENERATOR_CATALOG.md`
- `ORYN_PATTERN_DESIGNER_V2_REFERENCE_NOTICE.md`
- this integration note

## Minimally modified

- `main.py`: additive Pattern Designer page route, status/save API, and launcher script injection only

## Explicitly preserved

- existing compiled React UI (`static/dist`)
- frontend React source
- motion executor and theta-rho coupling
- machine profiles and calibration
- clearing behavior
- Pattern Forge converter and APIs
- playlist/queue execution

Direct library saving never changes geometry to force a fit. If normalized rho exceeds the table boundary, save is rejected and the user must adjust Pattern Designer scale/offset.
