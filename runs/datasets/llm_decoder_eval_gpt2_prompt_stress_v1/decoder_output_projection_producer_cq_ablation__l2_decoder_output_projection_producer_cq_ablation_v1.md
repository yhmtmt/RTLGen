# Decoder Producer CQ Ablation

- base_config: `runs/designs/npu_blocks/npu_fp16_cpp_nm2_producer/config_nm2_producer.json`
- make_target: `1_2_yosys`
- timeout_seconds: `900`
- stall_timeout_seconds: `450`

| variant | top | status | elapsed_s | verilog_kb | reg_bits_est | wire_bits_est | log |
|---|---|---|---:|---:|---:|---:|---|
| no_cq_mem_ports | npu_top | ok | 188.2 | 51.0 | 68109 | 3864 | no_cq_mem_ports_npu_top_1_2_yosys.log |
| cq_fetch_only | npu_top | ok | 178.2 | 51.9 | 68109 | 3864 | cq_fetch_only_npu_top_1_2_yosys.log |
| cq_v1_header_only | npu_top | ok | 174.2 | 52.0 | 68109 | 3864 | cq_v1_header_only_npu_top_1_2_yosys.log |
| cq_v1_dma_only | npu_top | ok | 178.2 | 52.4 | 68109 | 3864 | cq_v1_dma_only_npu_top_1_2_yosys.log |
| cq_v1_gemm_only | npu_top | ok | 188.2 | 54.8 | 68109 | 3864 | cq_v1_gemm_only_npu_top_1_2_yosys.log |
| cq_v2_gemm_only | npu_top | ok | 190.2 | 55.8 | 68109 | 3864 | cq_v2_gemm_only_npu_top_1_2_yosys.log |
| cq_v1_vec_only | npu_top | ok | 192.2 | 55.4 | 68109 | 3864 | cq_v1_vec_only_npu_top_1_2_yosys.log |
| cq_v1_softmax_event_only | npu_top | timeout | 900.9 | 53.5 | 68110 | 3864 | cq_v1_softmax_event_only_npu_top_1_2_yosys.log |
| full_reference_guard | npu_top | stall_timeout | 512.5 | 69.5 | 68110 | 3864 | full_reference_guard_npu_top_1_2_yosys.log |

## Diagnosis

- decision: `cq_subpath_culprit_bracketed`
- ok_variants: `['no_cq_mem_ports', 'cq_fetch_only', 'cq_v1_header_only', 'cq_v1_dma_only', 'cq_v1_gemm_only', 'cq_v2_gemm_only', 'cq_v1_vec_only']`
- non_ok_variants: `['cq_v1_softmax_event_only', 'full_reference_guard']`
- first_non_ok_variant: `cq_v1_softmax_event_only`
- recommended_next_step: Compare the first non-OK CQ subpath against the preceding OK subpath and stage or preserve hierarchy around that decode/issue expression.
