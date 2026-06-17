# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_kv_endpoint_ready_valid_service_softmax_recip_lut_v1`
- `candidate_id`: `l2_decoder_attention_kv_endpoint_ready_valid_service_softmax_recip_lut_llama7b_v1`

## Evaluations Consumed
- `l2_decoder_attention_kv_endpoint_ready_valid_service_softmax_recip_lut_llama7b_v1`
- `l2_decoder_attention_kv_endpoint_ready_valid_service_softmax_recip_lut_llama7b_v1_run_5ce04d3cc6df47c4`
- source commit: `bcc381dd2e2251fccf74a2095c59caf9c38821c6`
- review: PR #886

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `ready_valid_endpoint_policy_passed`
- summary: Decoder endpoint ready/valid service evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_endpoint_ready_valid_service__l2_decoder_attention_kv_endpoint_ready_valid_service_softmax_recip_lut_llama7b_v1.json: decision=ready_valid_endpoint_policy_passed; rtl_passed=True; latency_us=3222.903773; schedule_policy=prefetch_overlap; bank_arbiter_policy=locality_first; endpoint_queue_depth_bytes=2048; bank_queue_depth_bytes=2048; packet_payload_bytes=128.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Decoder endpoint ready/valid service evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_endpoint_ready_valid_service__l2_decoder_attention_kv_endpoint_ready_valid_service_softmax_recip_lut_llama7b_v1.json: decision=ready_valid_endpoint_policy_passed; rtl_passed=True; latency_us=3222.903773; schedule_policy=prefetch_overlap; bank_arbiter_policy=locality_first; endpoint_queue_depth_bytes=2048; bank_queue_depth_bytes=2048; packet_payload_bytes=128.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Decoder endpoint ready/valid service evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_endpoint_ready_valid_service__l2_decoder_attention_kv_endpoint_ready_valid_service_softmax_recip_lut_llama7b_v1.json: decision=ready_valid_endpoint_policy_passed; rtl_passed=True; latency_us=3222.903773; schedule_policy=prefetch_overlap; bank_arbiter_policy=locality_first; endpoint_queue_depth_bytes=2048; bank_queue_depth_bytes=2048; packet_payload_bytes=128.
- next_action: inspect follow-on work after l2_decoder_attention_kv_endpoint_ready_valid_service_softmax_recip_lut_llama7b_v1
