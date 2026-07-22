# Evaluation Gate

1. Queue v15 only after merged, promotion-valid
   `l1_decoder_attention_decode_score_multivalue_cluster_pnr_targeted_binary_fsm_8ns_v1` and
   `l2_decoder_attention_decode_score_multivalue_cluster_equivalence_llama7b_v1`
   evidence is available.
2. Run the activity-power audit on the remote evaluator with evaluator-local
   VCD/ODB/SPEF and temporary activity files; commit only portable JSON/MD.
3. Require the result to spell out annotation coverage, clock assumptions,
   macro activity attribution, and finite power-gate assumptions.
4. Keep the FakeRAM score-store qualification explicit; no SRAM signoff or
   silicon-current claim is allowed from LEF/LIB proxy views.
5. Treat vectorless OpenROAD power as structural diagnostics only. It cannot
   substitute for activity-backed power or token-energy claims.
6. Select only `config_targeted_binary_fsm.json` with
   `decode_score_multivalue_cluster_v1_8ns_targeted_binary_fsm_v1_proxy_die_2500`,
   empty/default `SYNTH_ARGS`, and the exact promotion-valid `targeted_binary`
   checker diagnostic bound to the selected metrics hashes. The v14 `-nofsm`
   row and prior one-hot rows are invalid for this consumer.
7. Require 100% routed sequential Q/QN coverage, applied assignments equal to
   matched assignments, zero query/apply errors, and finite positive power for
   every phase. Preserve the merged 10 ns and one-hot 8 ns rows as prior PPA
   evidence rather than reusing them for v15 power. Reject vectorless,
   stale-row, baseline, or fallback substitutions.
