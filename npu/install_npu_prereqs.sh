#!/usr/bin/env bash
set -euo pipefail

echo "[npu] Installing base prerequisites for NVDLA VP and toolchain"
apt-get update
apt-get install -y --no-install-recommends \
  ninja-build \
  libglib2.0-dev \
  libpixman-1-dev \
  liblua5.2-dev \
  libcap-dev \
  libattr1-dev \
  swig \
  wget

echo "[npu] Installing Boost (>=1.78) from PPA"
apt-get install -y software-properties-common
add-apt-repository -y ppa:mhier/libboost-latest
apt-get update
apt-get install -y \
  "$(apt-cache search --names-only '^libboost[0-9\\.]+-all-dev$' | sort -V | tail -n 1 | awk '{print $1}')"

echo "[npu] Installing SystemC 2.3.0a"
SYSCTMP="$(mktemp -d)"
SYSCTARBALL="${SYSCTMP}/systemc-2.3.0a.tar.gz"
wget -O "${SYSCTARBALL}" \
  https://www.accellera.org/images/downloads/standards/systemc/systemc-2.3.0a.tar.gz
tar -xzf "${SYSCTARBALL}" -C "${SYSCTMP}"
cd "${SYSCTMP}/systemc-2.3.0a"
mkdir objdir
cd objdir
mkdir -p /usr/local/systemc-2.3.0
../configure --prefix=/usr/local/systemc-2.3.0
make -j"$(nproc)"
make install
cd /
rm -rf "${SYSCTMP}"

echo "[npu] Done. SystemC installed to /usr/local/systemc-2.3.0"
echo "[npu] Verifying SystemC install"
if [[ ! -d /usr/local/systemc-2.3.0/include ]] || [[ ! -d /usr/local/systemc-2.3.0/lib ]]; then
  echo "[npu] SystemC install missing include/lib directories" >&2
  exit 1
fi
if ! ls /usr/local/systemc-2.3.0/lib | grep -q "libsystemc"; then
  echo "[npu] SystemC library not found under /usr/local/systemc-2.3.0/lib" >&2
  exit 1
fi
echo "[npu] SystemC verification passed"
