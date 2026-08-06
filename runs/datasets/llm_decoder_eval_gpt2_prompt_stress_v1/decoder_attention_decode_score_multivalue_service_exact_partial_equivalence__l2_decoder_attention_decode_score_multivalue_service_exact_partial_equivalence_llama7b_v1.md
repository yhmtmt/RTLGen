# Attention Decode Score Multivalue Integrated Service Probe

- decision: `pass`
- outcome: `multivalue_integrated_service_probe_passed`
- repo commit: `39f44cf83e48565a4a9b26a751f70f0e6f066d53`
- cases: `14`
- max_cluster_count: `32`
- max_completion_cycle: `14472`
- max_service_penalty_cycles: `13818`
- stress_case_id: `c32_p256_b32_rl6_rr`
- selected_scale_point: `c32_p256_b32_rr`
- selected_scale_point_role: `representative_largest_nominal_scale_point`
- selected_scale_point_note: Largest tested cluster_count, then packet_w, then banks among q4/read_latency=2/round_robin cases; coverage representative only, not a performance or architectural ranking.
- gates: `hash=True` `protocol=True` `count=True`
- compact_report_shape: `deduplicated_shared_artifact_identities_v1`
- workload_contract: `active_context_tokens=24` `max_context_capacity_tokens=128` `value_dim=128`
- compact_report_size: `69368 bytes / 1743 lines` (gate <= 100000 bytes / 2500 lines)
- exclusions: `physical_ppa, hbm, total_token_energy, value_sram_macro_timing, score_bank_macro_timing`
- proposal_id: `prop_l2_decoder_attention_decode_score_multivalue_service_exact_partial_equivalence_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_decode_score_multivalue_service_exact_partial_equivalence_llama7b_v1/proposal.json`
- depends_on_item_ids: `l2_decoder_attention_decode_score_multivalue_cluster_equivalence_llama7b_v1`

## Cases

| case | cfg | done | penalty | gate | req stall | router arb | bank conflict | resp block r/s | shared arb/block | occ rreq/rresp/sreq/sresp |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: | --- | --- | --- |
| c1_p128_b4_rr | c1/p128/b4/round_robin/q4/rl2 | 1039 | 385 | h:ok/p:ok/c:ok | 0 | 0 | 0 | 0/0 | 0/0 | 1/1/1/1 |
| c2_p128_b4_rr | c2/p128/b4/round_robin/q4/rl2 | 1198 | 544 | h:ok/p:ok/c:ok | 0 | 1 | 93 | 0/0 | 30/8 | 2/1/2/1 |
| c4_p128_b4_rr | c4/p128/b4/round_robin/q4/rl2 | 1848 | 1194 | h:ok/p:ok/c:ok | 0 | 7 | 189 | 0/0 | 60/8 | 4/1/4/2 |
| c8_p128_b4_rr | c8/p128/b4/round_robin/q4/rl2 | 3144 | 2490 | h:ok/p:ok/c:ok | 0 | 2412 | 381 | 0/0 | 114/8 | 8/1/7/2 |
| c16_p128_b4_rr | c16/p128/b4/round_robin/q4/rl2 | 5972 | 5318 | h:ok/p:ok/c:ok | 0 | 5282 | 765 | 0/0 | 253/8 | 16/1/10/2 |
| c32_p128_b4_rr | c32/p128/b4/round_robin/q4/rl2 | 11492 | 10838 | h:ok/p:ok/c:ok | 0 | 10658 | 1533 | 0/0 | 509/8 | 32/1/10/2 |
| c8_p256_b8_rr | c8/p256/b8/round_robin/q4/rl2 | 2400 | 1746 | h:ok/p:ok/c:ok | 0 | 1674 | 381 | 0/0 | 118/41 | 8/1/7/1 |
| c8_p256_b8_locality | c8/p256/b8/locality_first_bounded/q4/rl2 | 2366 | 1712 | h:ok/p:ok/c:ok | 0 | 1615 | 378 | 0/0 | 117/76 | 8/1/7/1 |
| c16_p256_b16_rr | c16/p256/b16/round_robin/q4/rl2 | 4472 | 3818 | h:ok/p:ok/c:ok | 0 | 3766 | 765 | 0/0 | 253/6 | 16/1/9/1 |
| c16_p256_b16_locality | c16/p256/b16/locality_first_bounded/q4/rl2 | 4201 | 3547 | h:ok/p:ok/c:ok | 0 | 3577 | 760 | 0/0 | 215/156 | 16/1/10/1 |
| c32_p256_b32_rr | c32/p256/b32/round_robin/q4/rl2 | 8488 | 7834 | h:ok/p:ok/c:ok | 0 | 7606 | 1533 | 0/0 | 510/6 | 32/1/9/1 |
| c32_p256_b32_locality | c32/p256/b32/locality_first_bounded/q4/rl2 | 7255 | 6601 | h:ok/p:ok/c:ok | 0 | 6566 | 1522 | 0/0 | 319/41 | 32/1/10/1 |
| c32_p256_b32_q1_rr | c32/p256/b32/round_robin/q1/rl2 | 8518 | 7864 | h:ok/p:ok/c:ok | 0 | 7651 | 1533 | 0/0 | 510/6 | 32/1/4/1 |
| c32_p256_b32_rl6_rr | c32/p256/b32/round_robin/q4/rl6 | 14472 | 13818 | h:ok/p:ok/c:ok | 0 | 13686 | 1533 | 0/0 | 510/10 | 32/1/10/1 |
