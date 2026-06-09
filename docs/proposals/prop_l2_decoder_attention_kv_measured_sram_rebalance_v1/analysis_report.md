# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_kv_measured_sram_rebalance_v1`
- `candidate_id`: `l2_decoder_attention_kv_measured_sram_rebalance_llama7b_v1`

## Evaluations Consumed
- `l2_decoder_attention_kv_measured_sram_rebalance_llama7b_v1`
- `l2_decoder_attention_kv_measured_sram_rebalance_llama7b_v1_run_0d0bc78d4130c008`
- source commit: `a290ca9774bfdf35624cc90c3cb1a39fa6adb396`
- review: PR #822

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `measured_sram_rebalance_recorded`
- summary: Decoder measured-SRAM rebalance evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_measured_sram_rebalance__l2_decoder_attention_kv_measured_sram_rebalance_llama7b_v1.json: decision=measured_sram_rebalance_recorded; latency_us=2138.84136; hbm_byte_share=0.983398438; measured_shared_sram_capacity_mib=68.0; local_capacity_bytes_per_cluster=614656; abstract_local_capacity_bytes_per_cluster_replaced=19140624; dominant_tile_resource=tile_attention.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Decoder measured-SRAM rebalance evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_measured_sram_rebalance__l2_decoder_attention_kv_measured_sram_rebalance_llama7b_v1.json: decision=measured_sram_rebalance_recorded; latency_us=2138.84136; hbm_byte_share=0.983398438; measured_shared_sram_capacity_mib=68.0; local_capacity_bytes_per_cluster=614656; abstract_local_capacity_bytes_per_cluster_replaced=19140624; dominant_tile_resource=tile_attention.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Decoder measured-SRAM rebalance evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_measured_sram_rebalance__l2_decoder_attention_kv_measured_sram_rebalance_llama7b_v1.json: decision=measured_sram_rebalance_recorded; latency_us=2138.84136; hbm_byte_share=0.983398438; measured_shared_sram_capacity_mib=68.0; local_capacity_bytes_per_cluster=614656; abstract_local_capacity_bytes_per_cluster_replaced=19140624; dominant_tile_resource=tile_attention.
- next_action: inspect follow-on work after l2_decoder_attention_kv_measured_sram_rebalance_llama7b_v1
