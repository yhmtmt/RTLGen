# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_mixed_precision_physical_feasibility_llama7b_v1`
- `candidate_id`: `l2_decoder_attention_mixed_precision_physical_feasibility_llama7b_v1`

## Evaluations Consumed
- `l2_decoder_attention_mixed_precision_physical_feasibility_llama7b_v1`
- `l2_decoder_attention_mixed_precision_physical_feasibility_llama7b_v1_run_95ef73a3ce675708`
- source commit: `df7db11ce15eabd09ff96192c58f49592473a8a3`
- review: PR #836

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `dual_stream_area_blocked`
- summary: Decoder mixed-precision physical feasibility evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_precision_physical_feasibility__l2_decoder_attention_mixed_precision_physical_feasibility_llama7b_v1.json: decision=dual_stream_area_blocked; precision_profile=q8_k8_v6_a24_s24_w16; best_requested_mode=dual_mac; best_requested_latency_us=1575.373891; best_requested_area_fit=False; best_requested_logic_slack_um2=-397395735.8284; best_requested_compute_area_over_budget_um2=397395735.8284; best_requested_required_compute_density_gain=2.003777; best_feasible_mode=split_mac; best_feasible_latency_us=2042.378179; recommended_next_step=measure a denser dual-stream fused attention datapath or reduce compute replicas before promoting dual_mac.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Decoder mixed-precision physical feasibility evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_precision_physical_feasibility__l2_decoder_attention_mixed_precision_physical_feasibility_llama7b_v1.json: decision=dual_stream_area_blocked; precision_profile=q8_k8_v6_a24_s24_w16; best_requested_mode=dual_mac; best_requested_latency_us=1575.373891; best_requested_area_fit=False; best_requested_logic_slack_um2=-397395735.8284; best_requested_compute_area_over_budget_um2=397395735.8284; best_requested_required_compute_density_gain=2.003777; best_feasible_mode=split_mac; best_feasible_latency_us=2042.378179; recommended_next_step=measure a denser dual-stream fused attention datapath or reduce compute replicas before promoting dual_mac.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Decoder mixed-precision physical feasibility evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_precision_physical_feasibility__l2_decoder_attention_mixed_precision_physical_feasibility_llama7b_v1.json: decision=dual_stream_area_blocked; precision_profile=q8_k8_v6_a24_s24_w16; best_requested_mode=dual_mac; best_requested_latency_us=1575.373891; best_requested_area_fit=False; best_requested_logic_slack_um2=-397395735.8284; best_requested_compute_area_over_budget_um2=397395735.8284; best_requested_required_compute_density_gain=2.003777; best_feasible_mode=split_mac; best_feasible_latency_us=2042.378179; recommended_next_step=measure a denser dual-stream fused attention datapath or reduce compute replicas before promoting dual_mac.
- next_action: inspect follow-on work after l2_decoder_attention_mixed_precision_physical_feasibility_llama7b_v1
