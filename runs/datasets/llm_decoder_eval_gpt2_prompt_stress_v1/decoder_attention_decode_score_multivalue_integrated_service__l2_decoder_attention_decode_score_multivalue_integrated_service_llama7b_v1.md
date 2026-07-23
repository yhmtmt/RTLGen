# Attention Decode Score Multivalue Integrated Service Probe

- decision: `pass`
- outcome: `multivalue_integrated_service_probe_passed`
- repo commit: `1e3258cd16a33487c8b91a80964070470e1c5b87`
- cases: `14`
- max_cluster_count: `32`
- max_completion_cycle: `21925`
- max_service_penalty_cycles: `13591`
- stress_case_id: `c32_p256_b32_rl6_rr`
- selected_scale_point: `c32_p256_b32_rr`
- selected_scale_point_role: `representative_largest_nominal_scale_point`
- selected_scale_point_note: Largest tested cluster_count, then packet_w, then banks among q4/read_latency=2/round_robin cases; coverage representative only, not a performance or architectural ranking.
- gates: `hash=True` `protocol=True` `count=True`
- exclusions: `physical_ppa, hbm, total_token_energy, value_sram_macro_timing, score_bank_macro_timing`
- proposal_id: `prop_l2_decoder_attention_decode_score_multivalue_integrated_service_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_decode_score_multivalue_integrated_service_llama7b_v1/proposal.json`
- depends_on_item_ids: `l2_decoder_attention_decode_score_multivalue_cluster_equivalence_llama7b_v1`

## Cases

| case | cfg | done | penalty | gate | req stall | router arb | bank conflict | resp block r/s | shared arb/block | occ rreq/rresp/sreq/sresp |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: | --- | --- | --- |
| c1_p128_b4_rr | c1/p128/b4/round_robin/q4/rl2 | 8719 | 385 | h:ok/p:ok/c:ok | 0 | 0 | 0 | 0/0 | 0/0 | 1/1/1/1 |
| c2_p128_b4_rr | c2/p128/b4/round_robin/q4/rl2 | 8863 | 529 | h:ok/p:ok/c:ok | 0 | 1 | 93 | 0/0 | 0/8 | 2/1/2/1 |
| c4_p128_b4_rr | c4/p128/b4/round_robin/q4/rl2 | 9507 | 1173 | h:ok/p:ok/c:ok | 0 | 7 | 189 | 0/0 | 0/8 | 4/1/4/2 |
| c8_p128_b4_rr | c8/p128/b4/round_robin/q4/rl2 | 10797 | 2463 | h:ok/p:ok/c:ok | 0 | 2412 | 381 | 0/0 | 0/8 | 8/1/7/2 |
| c16_p128_b4_rr | c16/p128/b4/round_robin/q4/rl2 | 13509 | 5175 | h:ok/p:ok/c:ok | 0 | 5282 | 765 | 0/0 | 0/8 | 16/1/10/2 |
| c32_p128_b4_rr | c32/p128/b4/round_robin/q4/rl2 | 18885 | 10551 | h:ok/p:ok/c:ok | 0 | 10658 | 1533 | 0/0 | 0/8 | 32/1/10/2 |
| c8_p256_b8_rr | c8/p256/b8/round_robin/q4/rl2 | 10036 | 1702 | h:ok/p:ok/c:ok | 0 | 1674 | 381 | 0/0 | 0/41 | 8/1/7/1 |
| c8_p256_b8_locality | c8/p256/b8/locality_first_bounded/q4/rl2 | 10017 | 1683 | h:ok/p:ok/c:ok | 0 | 1615 | 378 | 0/0 | 0/76 | 8/1/7/1 |
| c16_p256_b16_rr | c16/p256/b16/round_robin/q4/rl2 | 11981 | 3647 | h:ok/p:ok/c:ok | 0 | 3766 | 765 | 0/0 | 0/6 | 16/1/9/1 |
| c16_p256_b16_locality | c16/p256/b16/locality_first_bounded/q4/rl2 | 11806 | 3472 | h:ok/p:ok/c:ok | 0 | 3577 | 760 | 0/0 | 0/156 | 16/1/10/1 |
| c32_p256_b32_rr | c32/p256/b32/round_robin/q4/rl2 | 15821 | 7487 | h:ok/p:ok/c:ok | 0 | 7606 | 1533 | 0/0 | 0/6 | 32/1/9/1 |
| c32_p256_b32_locality | c32/p256/b32/locality_first_bounded/q4/rl2 | 14781 | 6447 | h:ok/p:ok/c:ok | 0 | 6566 | 1522 | 0/0 | 0/41 | 32/1/10/1 |
| c32_p256_b32_q1_rr | c32/p256/b32/round_robin/q1/rl2 | 15851 | 7517 | h:ok/p:ok/c:ok | 0 | 7651 | 1533 | 0/0 | 0/6 | 32/1/4/1 |
| c32_p256_b32_rl6_rr | c32/p256/b32/round_robin/q4/rl6 | 21925 | 13591 | h:ok/p:ok/c:ok | 0 | 13686 | 1533 | 0/0 | 0/10 | 32/1/10/1 |
