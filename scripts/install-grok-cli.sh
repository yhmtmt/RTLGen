#!/usr/bin/env bash
set -euo pipefail

# Install the Grok CLI from @vibe-kit on Ubuntu 22.04 (inside a container).
# This installs Node.js and npm, then the grok-cli package.

SUDO=""
if [ "$(id -u)" -ne 0 ]; then
  SUDO="sudo"
fi

echo "[grok] Installing dependencies (curl, ca-certificates)..."
$SUDO apt-get update -y
$SUDO apt-get install -y curl ca-certificates

echo "[grok] Installing Node.js and npm..."
if [ -n "$SUDO" ]; then
  curl -fsSL https://deb.nodesource.com/setup_lts.x | $SUDO -E bash -
else
  curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -
fi
$SUDO apt-get install -y nodejs

echo "[grok] Installing Grok CLI..."
$SUDO npm install -g @vibe-kit/grok-cli

echo "[grok] Verifying installation..."
grok --version

echo "[grok] Done. You can now run 'grok' inside this container."
