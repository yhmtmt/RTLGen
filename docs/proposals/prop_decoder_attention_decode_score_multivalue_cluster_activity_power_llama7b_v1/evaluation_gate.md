# Evaluation Gate

1. Queue only after merged
   `l1_decoder_attention_decode_score_multivalue_cluster_pnr_8ns_v2` and
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

6. Preserve the merged 10 ns Nangate45 row as prior evidence and append the new
   8 ns proxy-die_2500 (2.5 mm die / 2.4 mm square core) bridge row from the
   refreshed routed evaluator-local artifacts as the next data point for the same
   design.
