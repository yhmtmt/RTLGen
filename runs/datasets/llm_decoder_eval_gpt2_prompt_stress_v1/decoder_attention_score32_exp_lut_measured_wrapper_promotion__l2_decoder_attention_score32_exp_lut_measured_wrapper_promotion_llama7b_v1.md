# Score32 Exp-LUT Measured Wrapper Promotion Audit

## Decision
- decision: `decoder_attention_score32_exp_lut_measured_wrapper_promotion_recorded`
- recommended_next_step: `promote reduced-replica score32 exp-LUT datapath using the measured dual-stream wrapper instead of partitioned-wrapper physical follow-up.`

## Readiness
- l2_measured_decision: `dual_stream_feasible`
- l1_wrapper_accepted: `True`
- l1_wrapper_metrics_match: `True`
- requires_partitioned_or_cluster_validation: `False`

- l2_selected_wrapper_metrics_csv: `runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20/metrics.csv`
