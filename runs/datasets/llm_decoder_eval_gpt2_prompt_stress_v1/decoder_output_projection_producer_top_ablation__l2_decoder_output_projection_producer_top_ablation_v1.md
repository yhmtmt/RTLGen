# Decoder Producer Top Ablation

- base_config: `runs/designs/npu_blocks/npu_fp16_cpp_nm2_producer/config_nm2_producer.json`
- make_target: `1_2_yosys`
- timeout_seconds: `1800`
- stall_timeout_seconds: `900`

| variant | top | status | elapsed_s | verilog_kb | reg_bits_est | wire_bits_est | log |
|---|---|---|---:|---:|---:|---:|---|
| full_reference | npu_top | timeout | 1801.7 | 69.5 | 68110 | 3864 | full_reference_npu_top_1_2_yosys.log |
| no_axi_lite_wrapper | npu_top | timeout | 1801.8 | 65.2 | 68110 | 3755 | no_axi_lite_wrapper_npu_top_1_2_yosys.log |
| no_sram_instances | npu_top | timeout | 1801.7 | 69.5 | 68110 | 3864 | no_sram_instances_npu_top_1_2_yosys.log |
| no_axi_ports | npu_top | timeout | 1801.8 | 61.8 | 68110 | 3755 | no_axi_ports_npu_top_1_2_yosys.log |
| no_cq_mem_ports | npu_top | ok | 184.2 | 51.0 | 68109 | 3864 | no_cq_mem_ports_npu_top_1_2_yosys.log |
| external_ports_off | npu_top | ok | 4.0 | 42.7 | 68109 | 3755 | external_ports_off_npu_top_1_2_yosys.log |
| axi_lite_wrapper_top | npu_top_axi | failed | 2.0 | 69.5 | 68110 | 3864 | axi_lite_wrapper_top_npu_top_axi_1_2_yosys.log |

## Diagnosis

- decision: `producer_top_culprit_bracketed`
- ok_variants: `['no_cq_mem_ports', 'external_ports_off']`
- non_ok_variants: `['full_reference', 'no_axi_lite_wrapper', 'no_sram_instances', 'no_axi_ports', 'axi_lite_wrapper_top']`
- first_non_ok_variant: `full_reference`
- recommended_next_step: Compare the last passing ablation against the full reference to isolate the added top-level feature.
