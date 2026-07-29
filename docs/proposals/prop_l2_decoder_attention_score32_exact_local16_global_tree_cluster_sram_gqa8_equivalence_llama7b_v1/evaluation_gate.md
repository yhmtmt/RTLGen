# Full GQA8 cluster-SRAM equivalence gate

## Dispatch

- Required machine: `eval-daemon-b7c2d9c80c1c`
- Required source: the merge SHA containing this proposal and task mapping
- Physical flow: disabled
- Compile timeout: 1200 seconds
- Simulation timeout: 900 seconds
- Outer job timeout: 2400 seconds
- Stall timeout: 1500 seconds
- Memory: `MemoryHigh=6G`, `MemoryMax=8G`
- CPU: `CPUQuota=300%`
- Tasks: `TasksMax=512`
- Launcher: `control_plane/scripts/run_bounded_command.py`
- Simulation backend: `fine_compositional_icarus`

If a usable user `systemd` manager exists, the launcher applies the contract
with `systemd-run --user --scope`. In evaluator containers without a user bus,
the launcher falls back to process-group timeout, `RLIMIT_AS` for
`MemoryMax=8G`, `RLIMIT_NPROC` for `TasksMax=512`, and a CPU-affinity ceiling
derived from the current allowed CPUs and the requested quota rounded to whole
CPUs (`CPUQuota=300%` becomes at most three allowed CPUs). `MemoryHigh=6G` is
advisory and reported as unavailable in fallback mode rather than claimed as
exact cgroup enforcement.

The probe backend should be `python3 npu/eval/probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8.py --sim-backend fine_compositional_icarus --compile-timeout-sec 1200 --timeout-sec 900`.
It must pass the strict generated-top guard, serially replay the exact
single-producer module for all 856 producer contexts, check its SRAM request
metadata, simulate the concrete p54/p53 SRAM endpoints and local
reducer/temporal-merge modules, and simulate the concrete global tree from
observed cluster streams. The JSON report must record component phases,
`producer_replay_parallelism=1`, and separate compile/simulation timeouts.

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
- `compositional_components.strict_generated_top_guard: passed`
- `compositional_components.producer_replay_parallelism: 1`
- `compositional_components.global_sidecar.value_packing: canonical_pack_numerators`

Hashes are diagnostics only. They cannot substitute for structured comparison.

## Failure classification

Timeout, OOM, or resource termination is inconclusive and must not reject the
architecture. That includes compile or simulation termination by SIGKILL, shell
exit `137`, or a bare `Killed` diagnostic from the bounded launcher/runtime.
Count, protocol, metadata, ordering, or row mismatches are conclusive
implementation failures and must be fixed before PPA or Llama7B recosting.
The r6 global-tree row mismatch produced before canonical 41-bit numerator
packing is a harness-inconclusive result, not an RTL mismatch: that sidecar
used a 32-bit lane stride for the 328-bit `leaf_value`. Apply the conclusive
row-mismatch rule only to reruns whose component metadata records
`global_sidecar.value_packing=canonical_pack_numerators`.

## Follow-on

After a passing artifact is merged, use measured cycle and traffic evidence to
replace the current idealized cluster-SRAM service interval in the Llama7B
model. Keep HBM arrival timing, SRAM macro PPA, mesh NoC behavior, broader head
groups, and full-array physical closure explicit until separately measured.
