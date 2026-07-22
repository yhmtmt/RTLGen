# Evaluation Gate

1. Queue v14 only after merged
   `l1_decoder_attention_decode_score_multivalue_cluster_pnr_binary_fsm_8ns_v3_r2` and
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
6. Select only
   `decode_score_multivalue_cluster_v1_8ns_binary_fsm_v3_proxy_die_2500` with
   `SYNTH_ARGS=-nofsm`; the one-hot v2 row remains a PPA baseline but is invalid
   for bit-exact RTL-to-routed FSM activity transfer.
7. Require 100% routed sequential Q/QN coverage, applied assignments equal to
   matched assignments, zero query/apply errors, and finite positive power for
   every phase. Preserve the merged 10 ns and one-hot 8 ns rows as prior PPA
   evidence rather than reusing them for v14 power.
