# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_kv_measured_hbm_service_softmax_recip_lut_v1`
- `candidate_id`: `l2_decoder_attention_kv_measured_hbm_service_softmax_recip_lut_llama7b_v1`

## Evaluations Consumed
- `l2_decoder_attention_kv_measured_hbm_service_softmax_recip_lut_llama7b_v1`
- `l2_decoder_attention_kv_measured_hbm_service_softmax_recip_lut_llama7b_v1_run_45deddc547b97676`
- source commit: `1c97907302c22c3f19f9913370da6fb0c791c73d`
- review: PR #905

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `measured_hbm_service_recorded`
- summary: Decoder measured-HBM service evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_measured_hbm_service__l2_decoder_attention_kv_measured_hbm_service_softmax_recip_lut_llama7b_v1.json: decision=measured_hbm_service_recorded; latency_us=2138.84136; dominant_tile_resource=tile_attention; effective_hbm_bytes_per_cycle=792.596465; source_effective_hbm_bytes_per_cycle=41341.3632; derived_hbm_efficiency_vs_source=0.019172; controller_service_cycles=1301; tile_attention_cycles=1354; hbm_byte_share=0.983398438.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Decoder measured-HBM service evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_measured_hbm_service__l2_decoder_attention_kv_measured_hbm_service_softmax_recip_lut_llama7b_v1.json: decision=measured_hbm_service_recorded; latency_us=2138.84136; dominant_tile_resource=tile_attention; effective_hbm_bytes_per_cycle=792.596465; source_effective_hbm_bytes_per_cycle=41341.3632; derived_hbm_efficiency_vs_source=0.019172; controller_service_cycles=1301; tile_attention_cycles=1354; hbm_byte_share=0.983398438.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Decoder measured-HBM service evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_measured_hbm_service__l2_decoder_attention_kv_measured_hbm_service_softmax_recip_lut_llama7b_v1.json: decision=measured_hbm_service_recorded; latency_us=2138.84136; dominant_tile_resource=tile_attention; effective_hbm_bytes_per_cycle=792.596465; source_effective_hbm_bytes_per_cycle=41341.3632; derived_hbm_efficiency_vs_source=0.019172; controller_service_cycles=1301; tile_attention_cycles=1354; hbm_byte_share=0.983398438.
- next_action: inspect follow-on work after l2_decoder_attention_kv_measured_hbm_service_softmax_recip_lut_llama7b_v1
