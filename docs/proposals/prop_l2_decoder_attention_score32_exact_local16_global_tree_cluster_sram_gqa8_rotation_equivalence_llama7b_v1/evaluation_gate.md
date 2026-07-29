# Evaluation Gate

- Item: `l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_rotation_equivalence_llama7b_v1`
- Target machine: `eval-daemon-b7c2d9c80c1c`
- Worker mode: exclusive
- Resource contract:
  - `MemoryHigh=6G`
  - `MemoryMax=8G`
  - `CPUQuota=300%`
  - `TasksMax=512`
  - outer runtime `4500 s`
  - stall timeout `600 s`
  - probe timeout `3600 s`

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

- timeout, OOM, kill, or bounded resource failure: inconclusive
- structured row mismatch, metadata mismatch, count mismatch, or protocol error: conclusive
