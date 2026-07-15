# Evaluation Gate

1. Queue only after merged
   `l1_decoder_attention_decode_score_multivalue_cluster_pnr_v1` and
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
