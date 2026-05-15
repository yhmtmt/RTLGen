## Summary
- item_id: `l2_decoder_frontier_synthesis_integrated_v1`
- run_key: `l2_decoder_frontier_synthesis_integrated_v1_run_3cbce66f1b60cd7c`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `10/10 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_frontier_synthesis_integrated_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_frontier_synthesis_integrated_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_frontier_synthesis_integrated_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_frontier_synthesis_integrated_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_frontier_synthesis_integrated_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `27ecd8deeb2ff0485365050a656c62caae452dae`
- review_metadata_source_commit: `27ecd8deeb2ff0485365050a656c62caae452dae`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_frontier_synthesis_integrated`
- comparison_role: `frontier_synthesis`
- expected_direction: `iterate`
- expected_reason: `Use the refreshed synthesis to choose whether the next measured RTL job should target attention/KV memory hierarchy, producer/ranker integration, or another whole-decoder bottleneck.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_frontier_synthesis__l2_decoder_frontier_synthesis_integrated_v1.json: decision=decoder_evidence_recorded.`

## Focused Comparison
- primary_question: `After adding measured additive producer/ranker integration PPA context, is the next measured RTL frontier still producer/ranker, or does attention/KV memory dominate larger contexts?`
- comparison_role: `frontier_synthesis`
- proposal_outcome: `decoder_evidence_recorded`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_frontier_synthesis__l2_decoder_frontier_synthesis_integrated_v1.json: decision=decoder_evidence_recorded.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
