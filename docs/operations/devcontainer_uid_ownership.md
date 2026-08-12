# Devcontainer UID and Codex ownership

The developer and evaluator containers run interactive tools and control-plane
daemons as the non-root `rtlgen` user. Dev Containers remaps that account to the
host user's numeric UID and GID through `updateRemoteUserUID`.

The host Codex directory is mounted at `/home/rtlgen/.codex`. Do not mount it at
`/root/.codex` or run Codex as root: bind-mount ownership is numeric, so either
choice recreates host-inaccessible files.

## Privileged initialization

Only `/usr/local/sbin/rtlgen-container-init`, copied into the image and owned by
root, may run passwordlessly through sudo. It has two validated operations:

- `prepare`: create the control-plane runtime and evaluator service-checkout
  directories for `rtlgen`.
- `postgres`: initialize the local PostgreSQL service for the server role.

The helper does not execute files from the writable workspace. API, resolver,
worker, completion, Git, and Codex processes remain unprivileged.

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
