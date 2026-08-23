## Summary
- item_id: `l2_decoder_attention_score32_noc_phase2_exact_transport_revision_llama7b_v1`
- run_key: `l2_decoder_attention_score32_noc_phase2_exact_transport_revision_llama7b_v1_run_d967025f30c2b44d`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_score32_noc_phase2_exact_transport_revision_llama7b_v1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_score32_noc_phase2_exact_transport_revision_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_score32_noc_phase2_exact_transport_revision_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_score32_noc_phase2_exact_transport_revision_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_score32_noc_phase2_exact_transport_revision_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `1c99dd823b2faf28ac2e0f230b45c842db437ba5`
- review_metadata_source_commit: `68a35cfe83f7f3e143efa4a623cfa3c39b6b4f88`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_score32_noc_phase2_exact_transport`
- comparison_role: `phase2_exact_transport_revision`
- expected_direction: `retract_and_replace_phase2_reduction_transport`
- expected_reason: `Use actual 419-bit exact aggregate beats and group-major release before any NoC PPA or frontier recost.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder score32 Phase-2 exact transport revision recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_noc_phase2_exact_transport_revision__l2_decoder_attention_score32_noc_phase2_exact_transport_revision_llama7b_v1.json: decision=prior_phase2_reduction_contract_retracted_exact_transport_required; clusters=16; aggregate_beats_per_group_per_cluster=128; partial_link_bits_per_beat=419; prior_scheduled_flits=92128; exact_mode_flits=aligned_419b_two_flits_per_beat:76288,packed_419b_group_bitstream:73528,stats_once_ordered_exact:70948; recommended_frontier_candidate=stats_once_ordered_exact.`

## Focused Comparison
- primary_question: `What exact packet traffic must connect the embodied local temporal reducers to the root global reducer?`
- comparison_role: `phase2_exact_transport_revision`
- proposal_outcome: `prior_phase2_reduction_contract_retracted_exact_transport_required`
- comparison_summary: `Decoder score32 Phase-2 exact transport revision recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_noc_phase2_exact_transport_revision__l2_decoder_attention_score32_noc_phase2_exact_transport_revision_llama7b_v1.json: decision=prior_phase2_reduction_contract_retracted_exact_transport_required; clusters=16; aggregate_beats_per_group_per_cluster=128; partial_link_bits_per_beat=419; prior_scheduled_flits=92128; exact_mode_flits=aligned_419b_two_flits_per_beat:76288,packed_419b_group_bitstream:73528,stats_once_ordered_exact:70948; recommended_frontier_candidate=stats_once_ordered_exact.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
