#!/usr/bin/env bash
set -euo pipefail

# Install the Codex CLI native binary on Ubuntu 22.04 (inside a container).
# This does NOT use Node.js or npm.

SUDO=""
if [ "$(id -u)" -ne 0 ]; then
  SUDO="sudo"
fi

echo "[codex] Installing dependencies (curl, ca-certificates)..."
$SUDO apt-get update -y
$SUDO apt-get install -y curl ca-certificates

ARCH="$(uname -m)"
case "$ARCH" in
  x86_64)
    CODEx_ASSET="codex-x86_64-unknown-linux-musl"
    ;;
  aarch64|arm64)
    CODEx_ASSET="codex-aarch64-unknown-linux-musl"
    ;;
  *)
    echo "[codex] Unsupported architecture: $ARCH" >&2
    exit 1
    ;;
esac

TMP_DIR="$(mktemp -d)"
cd "$TMP_DIR"

echo "[codex] Downloading latest Codex CLI binary for $ARCH..."
curl -L "https://github.com/openai/codex/releases/latest/download/${CODEx_ASSET}.tar.gz" \
  -o codex.tar.gz

echo "[codex] Extracting..."
tar -xzf codex.tar.gz

# The tar contains a single binary named like codex-x86_64-unknown-linux-musl
echo "[codex] Installing to /usr/local/bin/codex ..."
$SUDO mv "$CODEx_ASSET" /usr/local/bin/codex
$SUDO chmod +x /usr/local/bin/codex

cd /
rm -rf "$TMP_DIR"

echo "[codex] Verifying installation..."
codex --version

echo "[codex] Done. You can now run 'codex' inside this container."
