#!/usr/bin/env bash
set -euo pipefail

if [[ "$(id -u)" == "0" ]]; then
  echo "post_start.sh must run as the remapped non-root devcontainer user" >&2
  exit 1
fi

sudo -n /usr/local/sbin/rtlgen-container-init prepare
exec /workspaces/RTLGen/.devcontainer/start_control_plane_services.sh
