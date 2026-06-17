# Composed Q12/PWL Softmax Datapath

This proposal measures the concrete PPA cost of replacing the current composed
dual-stream S8/W8 softmax datapath with an in-wrapper q12/PWL reciprocal
softmax. The target is the Llama7B attention frontier where the current q8
reciprocal-LUT composed wrapper is best on PPA but remains risky under the
Llama7B-shape quality proxy.

## Requested Item

- `l1_decoder_attention_dual_stream_composed_q12_pwl_softmax_ppa_v1`

## Key Artifacts

- `runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_q12_pwl_recip_q12/config.json`
- `runs/campaigns/npu/attention_dual_stream_composed_v1/sweeps/nangate45_dual_stream_composed_hier_q12_pwl.json`
