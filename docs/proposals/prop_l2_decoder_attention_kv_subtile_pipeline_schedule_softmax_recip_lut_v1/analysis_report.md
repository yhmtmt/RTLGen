# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_kv_subtile_pipeline_schedule_softmax_recip_lut_v1`
- `candidate_id`: `l2_decoder_attention_kv_subtile_pipeline_schedule_softmax_recip_lut_llama7b_v1`

## Evaluations Consumed
- item: `l2_decoder_attention_kv_subtile_pipeline_schedule_softmax_recip_lut_llama7b_v1`
- run: `l2_decoder_attention_kv_subtile_pipeline_schedule_softmax_recip_lut_llama7b_v1_run_6364ceb1a3b8a12f`
- source commit: `f81774cba0b9e26dd9a6d15e8959ea6854bd0fa2`

## Baseline Comparison
- baseline item: `l2_decoder_attention_kv_hbm_closed_onchip_schedule_softmax_recip_lut_llama7b_v1`
- baseline latency: `2138.84136 us`
- result latency: `1575.373891 us`
- speedup: `1.357672x`

## Result
- dominant resource: `pipeline_attention`
- pipeline attention cycles: `986`
- tile service cycles: `986`
- tile HBM cycles: `1301`
- exposed HBM cycles: `815`
- residual memory cycles: `688`
- subtile count: `8`
- subtile buffer count: `4`
- prefetch distance: `3`
- normalize strategy: `online_correction`
- compute mode: `dual_mac`
- required stream buffer: `532608 B`
- available local capacity: `614656 B`
- logic area: `399591889.5248 um2`
- logic power: `8123.59136 mW`
- MACs/cycle: `109440`

## Failures and Caveats
- The run was rescued locally because the remote evaluator was not leasing the
  prior ready item in this chain.
- Dual-MAC schedule mode should not be treated as physically free; it needs
  explicit area/power accounting in the next frontier step.
- Online correction should be checked against precision/quality behavior before
  using this result as a final architecture recommendation.

## Recommendation
- `iterate`
- reason: Subtile scheduling materially improves latency and exposes
  pipeline_attention as the new bottleneck, but dual-MAC area and online
  correction quality remain unresolved.
- next_action: Measure/account the physical cost of the selected dual-MAC
  subtile pipeline or run a constrained variant excluding dual-MAC.
