#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "============================================"
echo " ORYN Locked Build Verification"
echo "============================================"

fail=0
check_file(){
  if [[ -f "$1" ]]; then echo "[OK] $1"; else echo "[MISSING] $1"; fail=1; fi
}
check_text(){
  local f="$1" p="$2" label="$3"
  if grep -Fq "$p" "$f" 2>/dev/null; then echo "[OK] $label"; else echo "[MISSING] $label"; fail=1; fi
}

check_file static/dist/index.html
check_file static/custom/oryn-final-only.js
check_file static/custom/oryn-final-only.css
check_file static/custom/oryn-v33-exact-ui.js
check_file modules/pattern_generator/converter.py

check_text static/dist/index.html 'oryn-final-only.js' 'Final locked UI reference'
check_text static/dist/index.html 'oryn-v33-exact-ui.js' 'Perimeter Calibration UI reference'
check_text static/custom/oryn-final-only.js 'Pattern Forge' 'Pattern Forge UI'
check_text static/custom/oryn-final-only.js '/delete_theta_rho_file' 'Delete Pattern UI/API wiring'
check_text static/custom/oryn-final-only.js 'Designed to Move' 'Final ORYN footer branding'
check_text main.py '/api/v2/pattern-generator/preview' 'Pattern Forge backend API'
check_text main.py '/api/perimeter-calibration/start' 'Perimeter Calibration backend API'
check_text main.py '/delete_theta_rho_file' 'Delete backend API'

if [[ $fail -ne 0 ]]; then
  echo
  echo "RESULT: NOT the locked ORYN build"
  exit 1
fi

echo
echo "RESULT: LOCKED ORYN APPLICATION FILES PRESENT"
