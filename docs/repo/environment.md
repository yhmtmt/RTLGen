# Development Environment

## Purpose

Document the current supported development environment and point to the active
tooling entrypoints.

## Supported environment

The primary development environment is the devcontainer.

It provides:

- Ubuntu-based toolchain
- OpenROAD-related dependencies
- CMake/C++ build environment
- control-plane runtime dependencies

## Build

```sh
mkdir -p build
cd build
cmake ..
cmake --build .
```

## Common entrypoints

Layer 1 generator smoke:

```sh
build/rtlgen examples/config.json
```

Layer 2 campaign validation:

```sh
python3 npu/eval/validate.py --campaign <campaign.json> --check_paths
```

Control-plane API:

```sh
PYTHONPATH=/workspaces/RTLGen/control_plane python3 -m control_plane.cli.main serve-api --host 127.0.0.1 --port 8080
```

## Apple Silicon note

The devcontainer uses several `linux/amd64` tools, so Apple Silicon hosts run
the container under `linux/amd64` emulation.

## X11 note

Some `/orfs/flow`-related flows require GUI support. When needed, allow local
X11 access from the host before starting the container:

```sh
xhost + local:
```

## Scope rule

This page documents the current environment only.

Archive or remove:

- historical old-evaluation-script guidance
- superseded one-off environment notes
- duplicated workflow/runbook text that belongs in `docs/workflows/` or
  `control_plane/`
