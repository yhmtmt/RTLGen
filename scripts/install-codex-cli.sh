#!/usr/bin/env bash
set -euo pipefail

# Install the Codex CLI native binary without root privileges.
# The devcontainer image already provides wget, tar, and CA certificates.

INSTALL_DIR="${CODEX_INSTALL_DIR:-${HOME}/.local/bin}"

for dependency in wget tar; do
  if ! command -v "${dependency}" >/dev/null 2>&1; then
    echo "[codex] Missing dependency: ${dependency}" >&2
    echo "[codex] Install it in the image, then rebuild the devcontainer." >&2
    exit 1
  fi
done

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
trap 'rm -rf "${TMP_DIR}"' EXIT

echo "[codex] Downloading latest Codex CLI binary for $ARCH..."
wget -q \
  "https://github.com/openai/codex/releases/latest/download/${CODEx_ASSET}.tar.gz" \
  -O "${TMP_DIR}/codex.tar.gz"

echo "[codex] Extracting..."
tar -xzf "${TMP_DIR}/codex.tar.gz" -C "${TMP_DIR}"

# The tar contains a single binary named like codex-x86_64-unknown-linux-musl
echo "[codex] Installing to ${INSTALL_DIR}/codex ..."
mkdir -p "${INSTALL_DIR}"
install -m 0755 "${TMP_DIR}/${CODEx_ASSET}" "${INSTALL_DIR}/codex"

CODE_MODE_HOST_SOURCE="${CODEX_CODE_MODE_HOST_SOURCE:-${HOME}/.codex/plugins/.plugin-appserver/codex-code-mode-host}"
CODE_MODE_HOST_TARGET="${INSTALL_DIR}/codex-code-mode-host"
if [[ -x "${CODE_MODE_HOST_SOURCE}" ]]; then
  if [[ -L "${CODE_MODE_HOST_TARGET}" ]]; then
    ln -sfn "${CODE_MODE_HOST_SOURCE}" "${CODE_MODE_HOST_TARGET}"
  elif [[ ! -e "${CODE_MODE_HOST_TARGET}" ]]; then
    ln -s "${CODE_MODE_HOST_SOURCE}" "${CODE_MODE_HOST_TARGET}"
  fi
  echo "[codex] Code-mode host available at ${CODE_MODE_HOST_TARGET}"
else
  echo "[codex] Code-mode host plugin is not installed; CLI-only use remains available." >&2
fi

echo "[codex] Verifying installation..."
"${INSTALL_DIR}/codex" --version

echo "[codex] Done. You can now run 'codex' inside this container."
