# Evaluation Gate

Queue `l1_decoder_attention_kv_reducer_tree_frontier_v1` only after:

- the `attention_kv_reducer_tree` RTLGen operation is merged to `master`
- both tree config paths exist in the same source commit
- the tree sweep path exists in the same source commit
- local build and RTL generation checks pass
- the queued objective includes boundary acceptance text so timing or flow
  failures are retained as metrics evidence
- the queued payload includes `source_requirement.required_sha` for the merged
  source commit
