# Decoder Producer SOFTMAX/EVENT CQ Ablation

- base_config: `runs/designs/npu_blocks/npu_fp16_cpp_nm2_producer/config_nm2_producer.json`
- make_target: `1_2_yosys`
- timeout_seconds: `900`
- stall_timeout_seconds: `450`

| variant | top | status | elapsed_s | verilog_kb | reg_bits_est | wire_bits_est | log |
|---|---|---|---:|---:|---:|---:|---|
| cq_v1_vec_only_anchor | npu_top | ok | 172.2 | 56.1 | 2633 | 3864 | cq_v1_vec_only_anchor_npu_top_1_2_yosys.log |
| cq_v1_softmax_checks_only | npu_top | ok | 178.2 | 53.1 | 2633 | 3864 | cq_v1_softmax_checks_only_npu_top_1_2_yosys.log |
| cq_v1_softmax_issue_only | npu_top | ok | 174.2 | 53.0 | 2633 | 3864 | cq_v1_softmax_issue_only_npu_top_1_2_yosys.log |
| cq_v1_softmax_only | npu_top | ok | 174.2 | 53.5 | 2633 | 3864 | cq_v1_softmax_only_npu_top_1_2_yosys.log |
| cq_v1_event_signal_only | npu_top | ok | 174.2 | 54.0 | 2634 | 3864 | cq_v1_event_signal_only_npu_top_1_2_yosys.log |
| cq_v1_event_wait_only | npu_top | ok | 174.2 | 53.6 | 2634 | 3864 | cq_v1_event_wait_only_npu_top_1_2_yosys.log |
| cq_v1_event_index_only | npu_top | ok | 168.2 | 54.3 | 2633 | 3864 | cq_v1_event_index_only_npu_top_1_2_yosys.log |
| cq_v1_event_only | npu_top | ok | 178.2 | 55.0 | 2634 | 3864 | cq_v1_event_only_npu_top_1_2_yosys.log |
| cq_v1_softmax_event_guard | npu_top | ok | 196.2 | 55.8 | 2634 | 3864 | cq_v1_softmax_event_guard_npu_top_1_2_yosys.log |

## Diagnosis

- decision: `softmax_event_guard_synth_ok_under_bound`
- ok_variants: `['cq_v1_vec_only_anchor', 'cq_v1_softmax_checks_only', 'cq_v1_softmax_issue_only', 'cq_v1_softmax_only', 'cq_v1_event_signal_only', 'cq_v1_event_wait_only', 'cq_v1_event_index_only', 'cq_v1_event_only', 'cq_v1_softmax_event_guard']`
- non_ok_variants: `[]`
- first_non_ok_variant: `None`
- recommended_next_step: Use the guard metrics as an updated synthesis boundary before changing RTL.
