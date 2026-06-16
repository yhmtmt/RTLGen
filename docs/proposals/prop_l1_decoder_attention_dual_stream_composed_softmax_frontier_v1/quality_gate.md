# Quality Gate

## Proposal
- `proposal_id`: `prop_l1_decoder_attention_dual_stream_composed_softmax_frontier_v1`
- `title`: Composed dual-stream attention softmax split vs replacement frontier

## Why This Gate Is Required
- The `pow2sum` replacement removes the softmax sum divider and improved PPA to 6.4411 ns, 5.49 mW, and 243160 um2.
- That replacement changes normalization arithmetic, so it must not be promoted from PPA evidence alone.
- The gate compares `rtl_exact` and `rtl_pow2sum` for the same Q8/K8/V6/S8/W8 attention proxy.

## Reference
- PPA candidate: `l1_decoder_attention_dual_stream_composed_softmax_pow2sum_ppa_v1`
- prior mixed-precision quality baseline: `l2_decoder_attention_mixed_precision_quality_llama7b_v1`
- gate item: `l2_decoder_attention_softmax_pow2sum_quality_llama7b_v1`

## Checks
- metric: `mean_top1_match`
  - threshold: `>= 0.995`
- metric: `mean_retrieval_hit`
  - threshold: `>= 0.995`
- metric: `mean_output_cosine`
  - threshold: `>= 0.999`
- metric: `max_kl_divergence`
  - threshold: `<= 0.02`

## Local Command Shape
- command: `python3 npu/eval/estimate_llm_decoder_attention_mixed_precision_quality.py --candidate-spec-list q8:k8:v6:a24:s8:w8 --softmax-mode-list rtl_exact,rtl_pow2sum ...`

## Result
- status: pending
- note: This is a Llama7B-shape synthetic native-GQA quality/equivalence proxy, not final Llama7B perplexity or task accuracy.
