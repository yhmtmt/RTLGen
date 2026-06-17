# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_kv_hbm_closed_onchip_schedule_softmax_recip_lut_v1`
- `candidate_id`: `l2_decoder_attention_kv_hbm_closed_onchip_schedule_softmax_recip_lut_llama7b_v1`

## Evaluations Consumed
- item: `l2_decoder_attention_kv_hbm_closed_onchip_schedule_softmax_recip_lut_llama7b_v1`
- run: `l2_decoder_attention_kv_hbm_closed_onchip_schedule_softmax_recip_lut_llama7b_v1_run_23c73d0286366557`
- source commit: `7540125e5410eadb3b3ac1327aa0859e59087cd8`

## Baseline Comparison
- baseline item: `l2_decoder_attention_kv_measured_hbm_service_softmax_recip_lut_llama7b_v1`
- result artifact:
  `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_hbm_closed_onchip_schedule__l2_decoder_attention_kv_hbm_closed_onchip_schedule_softmax_recip_lut_llama7b_v1.json`

## Result
- latency: `2138.84136 us`
- dominant resource: `tile_attention`
- tile HBM cycles: `1301`
- tile attention cycles: `1354`
- tile service cycles: `1354`
- on-chip shared service cycles: `225`
- schedule policy: `static_wave`
- bank arbiter: `locality_first`
- endpoint queue depth: `1024 B`
- bank queue depth: `1024 B`
- router latency: `1 cycle/hop`
- packet payload: `64 B`
- logic area: `399591889.5248 um2`
- logic power: `8123.59136 mW`
- MACs/cycle: `109440`

## Failures and Caveats
- The remote assigned evaluator did not lease the ready item, so this small
  analytic L2 run was rescued locally under
  `eval-daemon-local-hbm-closed-softmax-rescue`.
- The result still uses analytic HBM controller and NoC/SRAM service models.

## Recommendation
- `iterate`
- reason: Re-sweeping on-chip service did not move the softmax-recip measured-HBM frontier; tile attention remains the next bottleneck.
- next_action: Run `l2_decoder_attention_kv_subtile_pipeline_schedule_softmax_recip_lut_llama7b_v1`.
