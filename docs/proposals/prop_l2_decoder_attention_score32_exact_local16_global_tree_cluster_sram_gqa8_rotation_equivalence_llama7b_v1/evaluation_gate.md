# Evaluation Gate

- Item: `l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_rotation_equivalence_llama7b_v1`
- Target machine: `eval-daemon-b7c2d9c80c1c`
- Worker mode: exclusive
- Resource contract:
  - `MemoryHigh=6G`
  - `MemoryMax=8G`
  - `CPUQuota=300%`
  - `TasksMax=512`
  - outer runtime `5100 s`
  - stall timeout `1500 s`
  - compile timeout `1200 s`
  - probe timeout `3600 s`
  - launcher `control_plane/scripts/run_bounded_command.py`
  - simulation backend `verilator_hierarchical`

If a usable user `systemd` manager exists, the launcher applies the contract
with `systemd-run --user --scope`. In evaluator containers without a user bus,
the launcher falls back to process-group timeout, `RLIMIT_AS` for
`MemoryMax=8G`, `RLIMIT_NPROC` for `TasksMax=512`, and a CPU-affinity ceiling
derived from the current allowed CPUs and the requested quota rounded to whole
CPUs (`CPUQuota=300%` becomes at most three allowed CPUs). `MemoryHigh=6G`
stays advisory in fallback mode and is reported that way instead of claimed as
exact cgroup enforcement.

The probe backend should be `python3 npu/eval/probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8.py --sim-backend verilator_hierarchical --compile-timeout-sec 1200 --timeout-sec 3600`.
This backend uses Verilator `--binary --timing --hierarchical` with a generated
control file that marks exactly the generated p54 cluster, p53 cluster, and
global-tree modules as hierarchy blocks, adds `-Wno-fatal` so warnings do not
become false compile failures, and records separate compile/simulation timeout
metadata in the bounded JSON report.

Acceptance:

1. `passed=true`, `classification=passed`, `counts_passed=true`
2. exact totals:
   - `producer_handshake_count=32768`
   - `fill_target_accept_count=512`
   - `fill_row_accept_count=1048576`
   - `sram_request_accept_count=1048576`
   - `sram_response_accept_count=1048576`
   - `cluster_row_count=8192`
   - `root_row_count=512`
   - `command_accept_count=32`
   - `cadence_command_accept_count=32`
   - `protocol_error=0`
3. `report.command_ids=[33280, 33281, 33282, 33283]`
4. `report.head_bases=[0, 8, 16, 24]`
5. every cluster summary has `errors=0` and:
   - `wave_command_accept_count=32`
   - `completed_command_count=4`
   - `emitted_beat_count=512`
   - `fill_target_accept_count=32`
   - `fill_row_accept_count=65536`
   - `request_accept_count=65536`
   - `response_accept_count=65536`
   - `command_accept_count=32`
   - `command_release_count=32`
6. `full_row_audit.passed=true` for all 16 clusters and the root stream

Classification policy:

- timeout, OOM, kill, or bounded resource failure, including compile or simulation termination by SIGKILL, shell exit `137`, or a bare `Killed` diagnostic: inconclusive
- structured row mismatch, metadata mismatch, count mismatch, or protocol error: conclusive
