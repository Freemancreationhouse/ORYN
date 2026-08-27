# ORYN Pattern Forge Pro V10.3 Verification

Baseline: Pattern Forge Pro V10.2 on locked motion baseline `UC-DUNE-MOTION-V9-20260827-1`.

## Corrected
- Source-artwork preview now uses a contain-sized CSS background preview, isolating it from global image CSS that caused vertical cropping.
- Auto raster classification recognises high-contrast logos/mandalas/ornamental artwork as graphic line art instead of swollen photo-edge contours.
- Raster invert polarity is sanity-checked and automatically corrected when the selected polarity would turn the page/background into the artwork.
- Closed-loop smoothing and simplification preserve loop seams and corners while removing pixel wobble.
- New default Artwork-safe connector constructs the minimum safe component bridges and computes a single Euler-style machine route; movement retraces existing artwork where topology requires it instead of adding arbitrary passing lines/perimeter spokes.
- All runtime/source release and update repository references point to `Freemancreationhouse/ORYN`.
- CLI user-facing update/install/help wording uses `oryn` commands.

## Retained from V10.2
- Async Pattern Forge jobs / 504 protection
- Clean JSON/user-facing errors
- Raster / SVG / DXF / G-code / THR pipelines
- G0/G1/G2/G3, G90/G91, G20/G21, I/J/R G-code support
- Exact-preview-to-THR output
- Settings/config serial-I/O blocking during active pattern playback
- Cached read-only hardware settings during playback

## Verification
- Python compilation: PASS
- Pattern Forge JavaScript syntax: PASS
- ORYN/setup shell syntax: PASS
- Raster conversion using the supplied Ganesha and knot samples: PASS
- Invert auto-correction on both raster samples: PASS
- G-code parser fixture: PASS
- THR parser fixture: PASS
- DXF parser fixture: PASS
- Repository identity scan for obsolete upstream URLs / old install command: PASS
- `modules/core/pattern_manager.py`: unchanged from V10.2/V9 baseline
- `modules/connection/connection_manager.py`: unchanged from V10.2/V9 baseline
- `BUILD_UNIVERSAL_FINAL.txt`: unchanged
- `oryn.service`: unchanged
- `requirements.txt`: unchanged
- Existing static PNG/JPG/ICO/WEBP assets: byte-for-byte unchanged

SVG support remains through the declared `svgpathtools` dependency in `requirements.txt`; `oryn update` refreshes Python requirements before service restart.
