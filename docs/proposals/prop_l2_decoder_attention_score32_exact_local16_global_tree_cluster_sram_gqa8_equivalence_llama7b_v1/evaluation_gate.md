# Full GQA8 cluster-SRAM equivalence gate

## Dispatch

- Required machine: `eval-daemon-b7c2d9c80c1c`
- Required source: the merge SHA containing this proposal and task mapping
- Physical flow: disabled
- Subprocess timeout: 900 seconds
- Outer job timeout: 1200 seconds
- Stall timeout: 300 seconds
- Memory: `MemoryHigh=6G`, `MemoryMax=8G`
- CPU: `CPUQuota=300%`
- Tasks: `TasksMax=512`
- Launcher: `control_plane/scripts/run_bounded_command.py`

If a usable user `systemd` manager exists, the launcher applies the contract
with `systemd-run --user --scope`. In evaluator containers without a user bus,
the launcher falls back to process-group timeout, `RLIMIT_AS` for
`MemoryMax=8G`, `RLIMIT_NPROC` for `TasksMax=512`, and a CPU-affinity ceiling
derived from the current allowed CPUs and the requested quota rounded to whole
CPUs (`CPUQuota=300%` becomes at most three allowed CPUs). `MemoryHigh=6G` is
advisory and reported as unavailable in fallback mode rather than claimed as
exact cgroup enforcement.

Do not run this probe in the devcontainer.

## Pass criteria

The JSON report must contain:

- `passed: true`
- `classification: passed`
- 8,192 producer handshakes
- 128 accepted fill targets
- 262,144 accepted fill rows
- 262,144 SRAM requests and responses
- 2,048 cluster rows
- 128 root rows
- 16 passing per-cluster summaries
- zero protocol or sticky errors
- passing structured comparisons for every cluster row and root row

Hashes are diagnostics only. They cannot substitute for structured comparison.

## Failure classification

Timeout, OOM, or resource termination is inconclusive and must not reject the
architecture. Count, protocol, metadata, ordering, or row mismatches are
conclusive implementation failures and must be fixed before PPA or Llama7B
recosting.

## Follow-on

After a passing artifact is merged, use measured cycle and traffic evidence to
replace the current idealized cluster-SRAM service interval in the Llama7B
model. Keep HBM arrival timing, SRAM macro PPA, mesh NoC behavior, broader head
groups, and full-array physical closure explicit until separately measured.
