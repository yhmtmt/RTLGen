# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_kv_memory_v1`
- `candidate_id`: `l2_decoder_attention_kv_memory_v1`

## Evaluations Consumed
- pending remote evaluation

## Baseline Comparison
- baseline_ref: `docs/proposals/prop_l2_decoder_stage_breakdown_v1/proposal.json`
- baseline_item_id: `l2_decoder_stage_breakdown_v1`
- expected comparison: ranking/frontier evidence, not a focused pass/fail delta

## Result
- pending `l2_decoder_attention_kv_memory_v1`

## Failures and Caveats
- no remote evaluation consumed yet
- estimator is analytical and should not be treated as RTL PPA

## Recommendation
- run the proposal-backed attention/KV memory hierarchy evaluation
- use the result to choose between KV memory hierarchy, NoC coupling, and attention-compute datapath follow-up work
