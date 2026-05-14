# Decoder Producer SOFTMAX/EVENT CQ Ablation

- base_config: `runs/designs/npu_blocks/npu_fp16_cpp_nm2_producer/config_nm2_producer.json`
- make_target: `1_2_yosys`
- timeout_seconds: `900`
- stall_timeout_seconds: `450`

| variant | top | status | elapsed_s | verilog_kb | reg_bits_est | wire_bits_est | log |
|---|---|---|---:|---:|---:|---:|---|
| cq_v1_vec_only_anchor | npu_top | ok | 178.2 | 55.4 | 68109 | 3864 | cq_v1_vec_only_anchor_npu_top_1_2_yosys.log |
| cq_v1_softmax_checks_only | npu_top | ok | 178.2 | 52.4 | 68109 | 3864 | cq_v1_softmax_checks_only_npu_top_1_2_yosys.log |
| cq_v1_softmax_issue_only | npu_top | ok | 178.2 | 52.3 | 68109 | 3864 | cq_v1_softmax_issue_only_npu_top_1_2_yosys.log |
| cq_v1_softmax_only | npu_top | ok | 186.2 | 52.7 | 68109 | 3864 | cq_v1_softmax_only_npu_top_1_2_yosys.log |
| cq_v1_event_signal_only | npu_top | ok | 188.2 | 52.4 | 68110 | 3864 | cq_v1_event_signal_only_npu_top_1_2_yosys.log |
| cq_v1_event_wait_only | npu_top | timeout | 900.9 | 52.2 | 68110 | 3864 | cq_v1_event_wait_only_npu_top_1_2_yosys.log |
| cq_v1_event_index_only | npu_top | ok | 186.2 | 52.2 | 68109 | 3864 | cq_v1_event_index_only_npu_top_1_2_yosys.log |
| cq_v1_event_only | npu_top | timeout | 900.9 | 52.6 | 68110 | 3864 | cq_v1_event_only_npu_top_1_2_yosys.log |
| cq_v1_softmax_event_guard | npu_top | timeout | 900.9 | 53.5 | 68110 | 3864 | cq_v1_softmax_event_guard_npu_top_1_2_yosys.log |

## Diagnosis

- decision: `softmax_event_subpath_culprit_bracketed`
- ok_variants: `['cq_v1_vec_only_anchor', 'cq_v1_softmax_checks_only', 'cq_v1_softmax_issue_only', 'cq_v1_softmax_only', 'cq_v1_event_signal_only', 'cq_v1_event_index_only']`
- non_ok_variants: `['cq_v1_event_wait_only', 'cq_v1_event_only', 'cq_v1_softmax_event_guard']`
- first_non_ok_variant: `cq_v1_event_wait_only`
- recommended_next_step: Inspect the first non-OK SOFTMAX/EVENT subpath and replace the failing expression with staged decode or preserved hierarchy.
