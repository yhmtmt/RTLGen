# Evaluation Gate

- status: approved
- approved_by: developer_agent
- approved_utc: 2026-07-02T00:00:00Z
- allowed_evaluations:
  - l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_command_overhead_llama7b_v1
- note: Dependency-gated command-overhead sensitivity for the score32 exp-LUT divider reduced-replica recost.
- release_gate: The generated L2 task must run `npu/eval/check_attention_exp_lut_frontier_release.py` before recosting. The gate must confirm the score32 exp-LUT generation-quality result passes and the composed PPA metrics/config are the bucket-20 exp-LUT wrapper.
