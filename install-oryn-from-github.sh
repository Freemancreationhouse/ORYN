#!/usr/bin/env bash
set -euo pipefail

REPO="${ORYN_REPO_URL:-https://github.com/Freemancreationhouse/ORYN.git}"
BRANCH="${ORYN_BRANCH:-main}"
TARGET="${ORYN_INSTALL_DIR:-$HOME/oryn}"

echo "ORYN — Designed to Move"
echo "by Studio Kinematics™"
echo "GitHub → Raspberry Pi installer"
echo

if ! command -v git >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y git
fi

if [[ -d "$TARGET/.git" ]]; then
    echo "Updating existing ORYN installation source..."
    git -C "$TARGET" fetch origin "$BRANCH"
    git -C "$TARGET" reset --hard "origin/$BRANCH"
else
    if [[ -e "$TARGET" ]]; then
        echo "ERROR: $TARGET exists but is not a Git repository."
        echo "Rename/delete that folder, then run again."
        exit 1
    fi
    git clone --branch "$BRANCH" --single-branch "$REPO" "$TARGET"
fi

cd "$TARGET"
exec bash setup-pi.sh "$@"
