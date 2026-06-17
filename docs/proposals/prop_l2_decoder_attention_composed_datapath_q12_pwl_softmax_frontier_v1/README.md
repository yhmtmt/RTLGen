# Q12/PWL Composed Softmax Frontier

This proposal prepares the dependent Layer2 substitution job for the concrete
q12/PWL reciprocal softmax composed attention wrapper.

The prerequisite Layer1 item is:

- `l1_decoder_attention_dual_stream_composed_q12_pwl_softmax_ppa_v1`

The Layer2 item prepared here is:

- `l2_decoder_attention_composed_datapath_q12_pwl_softmax_frontier_llama7b_v1`

It should run only after the q12/PWL wrapper metrics are materialized at:

- `runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_q12_pwl_recip_q12/metrics.csv`

The job keeps the existing Llama7B subtile schedule, HBM/SRAM/NoC assumptions,
and workload constant, then substitutes the measured q12/PWL composed wrapper
clock, area, and power into the same feasibility estimator used by the current
reciprocal-LUT composed frontier.
