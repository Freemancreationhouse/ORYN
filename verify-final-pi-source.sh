#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "=============================================="
echo " ORYN FINAL PI SOURCE VERIFICATION"
echo "=============================================="

fail=0
ok(){ echo "[OK] $1"; }
bad(){ echo "[FAIL] $1"; fail=1; }

grep -q "Pattern Forge" frontend/src/pages/BrowsePage.tsx && ok "Pattern Forge source" || bad "Pattern Forge source"
grep -q "Perimeter Calibration" frontend/src/pages/TableControlPage.tsx && ok "Perimeter Calibration source" || bad "Perimeter Calibration source"
grep -q "Delete Pattern" static/custom/oryn-final-only.js && ok "Delete Pattern overlay" || bad "Delete Pattern overlay"
grep -q 'preExecutionAction.*checked' static/custom/oryn-final-only.css && ok "Clear selection visual fix" || bad "Clear selection visual fix"
grep -q "oryn-final-only.css" static/dist/index.html && ok "Desktop custom CSS runtime reference" || bad "Desktop custom CSS runtime reference"
grep -q "oryn-final-only.js" static/dist/index.html && ok "Desktop custom JS runtime reference" || bad "Desktop custom JS runtime reference"
test ! -e static/custom/oryn-pi-visual-only.css && ok "No Pi-only visual override" || bad "Pi-only visual override exists"

python3 -m py_compile main.py modules/wifi/manager.py && ok "Python syntax" || bad "Python syntax"
bash -n wifi/autohotspot && ok "Autohotspot syntax" || bad "Autohotspot syntax"
bash -n wifi/setup-wifi.sh && ok "WiFi setup syntax" || bad "WiFi setup syntax"

echo
if [ "$fail" -eq 0 ]; then
  echo "RESULT: ORYN FINAL PI SOURCE READY"
else
  echo "RESULT: VERIFICATION FAILED"
  exit 1
fi
