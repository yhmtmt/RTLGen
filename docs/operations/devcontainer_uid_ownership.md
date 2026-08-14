# Devcontainer UID and Codex ownership

The developer and evaluator containers run interactive tools and control-plane
daemons as the non-root `rtlgen` user. Dev Containers remaps that account to the
host user's numeric UID and GID through `updateRemoteUserUID`.

The host Codex directory is mounted at `/home/rtlgen/.codex`. Do not mount it at
`/root/.codex` or run Codex as root: bind-mount ownership is numeric, so either
choice recreates host-inaccessible files.

The control-plane virtual environment is created as `rtlgen` under
`/home/rtlgen/.venvs/rtlgen-control-plane` by `postCreateCommand`. Keeping it
outside the bind-mounted checkout avoids host/container Python ABI and file
ownership conflicts. Rebuilding the container recreates this environment before
the resolver is started by `postStartCommand`.

The devcontainer also sets `RTLCP_REPO_SLUG=yhmtmt/RTLGen` explicitly. Use an
independent clone as the folder opened by the devcontainer. Do not open a host
linked worktree by itself: its `.git` file normally refers to the primary
checkout through an absolute host path that is not mounted in the container,
which leaves all Git commands unusable. The fixed workspace mount maps the
independent checkout to `/workspaces/RTLGen` regardless of its host directory
name.

`scripts/install-codex-cli.sh` installs the Codex CLI into
`/home/rtlgen/.local/bin` without sudo. This directory is included in the image
PATH. When the mounted Codex plugin provides `codex-code-mode-host`, the script
also links that executable into the same directory. Installing developer CLI
tools must not require a root password or write to `/usr/local/bin` at runtime.

For the developer/server role, post-start launches the API before the resolver.
The API initializes a fresh local database schema, after which the resolver can
poll without racing missing tables. Set `RTLCP_AUTOSTART_API=0` only when the
dashboard and API are deliberately hosted elsewhere.

## Privileged initialization

Only `/usr/local/sbin/rtlgen-container-init`, copied into the image and owned by
root, may run passwordlessly through sudo. It has two validated operations:

- `prepare`: create the control-plane runtime and evaluator service-checkout
  directories for `rtlgen`. It also prepares only the writable OpenROAD runtime
  roots used by generation and flow execution: `designs/src`,
  `designs/nangate45`, `logs`, `objects`, `reports`, and `results` under
  `/orfs/flow`.
- `postgres`: initialize the local PostgreSQL service for the server role.

The helper does not execute files from the writable workspace. API, resolver,
worker, completion, Git, Codex, RTL generation, and OpenROAD processes remain
unprivileged. Ownership changes are non-recursive; OpenROAD tools, platform
files, and scripts remain root-owned image content.

## One-time host repair

Stop Codex and the old container before repairing ownership. On each developer
or evaluator host, run outside the container:

```bash
sudo chown -R "$(id -u):$(id -g)" "$HOME/.codex"
```

If the old root container wrote into the repository checkout, repair that
checkout in the same way. Rebuild the container afterward; startup-time chown
is not a substitute for matching UID/GID.

## Verification

Inside each rebuilt container, verify:

```bash
test "$(id -u)" -ne 0
stat -c '%u:%g %n' "$HOME" "$HOME/.codex"
touch "$HOME/.codex/permission-test"
ps -eo user,pid,cmd | grep -E 'codex|control_plane'
```

The host must be able to edit and remove `permission-test`. Control-plane
processes must run as `rtlgen`; PostgreSQL retains its normal system accounts.
For the evaluator, also confirm its stable machine key, remote DB connection,
heartbeat, and exact-source reconciliation before dispatching more work.
