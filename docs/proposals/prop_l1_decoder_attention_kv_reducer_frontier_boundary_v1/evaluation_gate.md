# Evaluation Gate

Queue `l1_decoder_attention_kv_reducer_frontier_boundary_v2` only after:

- `l1_decoder_attention_kv_reducer_smoke_v1` has merged accepted evidence
- the queued payload uses `developer_loop.proposal_path` equal to
  `docs/proposals/prop_l1_decoder_attention_kv_reducer_frontier_boundary_v1/proposal.json`
- the queued objective includes boundary acceptance text so timing or flow
  failures are retained as metrics evidence
- the queued payload includes `source_requirement.required_sha` for the merged
  source commit
