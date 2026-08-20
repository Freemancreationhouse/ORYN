#!/usr/bin/env bash
set -u
cd "$(dirname "$0")/../.." 2>/dev/null || cd ~/oryn
echo "ORYN Pi visual-only verification"
for f in \
  static/custom/studio-kinematics-logo.png \
  static/custom/oryn-pi-visual-only.css \
  static/dist/index.html
do
  if [ -f "$f" ]; then echo "[OK] $f"; else echo "[MISSING] $f"; fi
done
grep -q "oryn-pi-visual-only.css?v=PI-VISUAL-FINAL-1" static/dist/index.html \
  && echo "[OK] fresh Pi visual stylesheet reference" \
  || echo "[MISSING] fresh Pi visual stylesheet reference"
