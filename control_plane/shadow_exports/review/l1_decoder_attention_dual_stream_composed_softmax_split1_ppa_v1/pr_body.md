## Summary
- item_id: `l1_decoder_attention_dual_stream_composed_softmax_split1_ppa_v1`
- run_key: `l1_decoder_attention_dual_stream_composed_softmax_split1_ppa_v1_run_f710bc0f7ee395cf`
- layer: `layer1`
- task_type: `l1_sweep`
- status: `ok`
- summary: `7/7 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l1_decoder_attention_dual_stream_composed_softmax_split1_ppa_v1/evaluated.json`
- metrics_rows_count: `2`
- review_artifact: `promotion_proposal` at `control_plane/shadow_exports/l1_promotions/l1_decoder_attention_dual_stream_composed_softmax_split1_ppa_v1.json`

## Developer Context
- proposal_id: `prop_l1_decoder_attention_dual_stream_composed_softmax_frontier_v1`
- proposal_path: `docs/proposals/prop_l1_decoder_attention_dual_stream_composed_softmax_frontier_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l1_decoder_attention_dual_stream_composed_softmax_frontier_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `eec17a523f8dd0e2419ab9afd77fe639f79a0daa`
- review_metadata_source_commit: `eec17a523f8dd0e2419ab9afd77fe639f79a0daa`

## Evaluation Mode
- evaluation_mode: `frontier_correction`
- abstraction_layer: `decoder_attention_dual_stream_composed_datapath`
- evaluation_summary: `Physical metrics recorded from an accepted status=ok Layer 1 row.`

## Checklist
- [ ] Commit only lightweight metrics; shared runs/index.csv is exported centrally after merge
- [ ] Include metrics row references for each completed design
- [ ] Run python3 scripts/build_runs_index.py and python3 scripts/validate_runs.py --skip_eval_queue before pushing
