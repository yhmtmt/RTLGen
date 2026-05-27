# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_kv_measured_compute_partition_llama7b_v1`
- `candidate_id`: `l2_decoder_attention_kv_measured_compute_partition_llama7b_v1`

## Evaluations Consumed
- pending: `l2_decoder_attention_kv_measured_compute_partition_llama7b_v1`
- baseline: `l2_decoder_attention_kv_measured_compute_llama7b_v1`
- source commit: `7c44fa3d51c80e20a8b1b9c7fe7792fc0bc6c2b3`

## Baseline Comparison
- baseline uses measured compute PPA as one monolithic compute fabric.
- candidate adds clustered sequence-tile scheduling, local/shared SRAM shares, and NoC bandwidth/hop contention.

## Result
- pending evaluator result.

## Failures and Caveats
- This is a service/scheduling model, not detailed NoC or SRAM macro RTL/PPA.
- QKV projection uses aggregate compute while attention tiles are statically sequence-sharded.

## Recommendation
- iterate after evaluator evidence is merged.
- If cluster count does not materially change the frontier, queue command-routing hierarchy RTL/PPA.
- If NoC or local/shared SRAM split changes the frontier, refine memory/NOC hierarchy first.
