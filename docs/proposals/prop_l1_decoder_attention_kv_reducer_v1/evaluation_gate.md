# Evaluation Gate

Queue `l1_decoder_attention_kv_reducer_smoke_v1` only after:

- the `attention_kv_reducer` RTLGen operation is merged to `master`
- the smoke config path exists in the same source commit
- the smoke sweep path exists in the same source commit
- local build and RTL generation checks pass
- perf-sim and RTL-visible reduced values and counters agree for at least one smoke vector
- the queued payload uses `developer_loop.proposal_path` equal to
  `docs/proposals/prop_l1_decoder_attention_kv_reducer_v1/proposal.json`
- the queued payload includes `source_requirement.required_sha` for the merged
  source commit

Queue `l1_decoder_attention_kv_reducer_frontier_v1` only after:

- `l1_decoder_attention_kv_reducer_smoke_v1` has merged accepted evidence
- no timing/placement failure in the smoke point indicates that the frontier
  should be narrowed first
