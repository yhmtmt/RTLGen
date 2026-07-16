# Evaluation Gate

1. Merge and execute the compositional equivalence item before PPA eligibility.
2. Require eight distinct query hashes and one identical key/value hash across
   all real single-cluster RTL runs.
3. Require exact score rows and all 128 ordered group result beats to match the
   integer reference directly as well as by hash.
4. Require the wrapper protocol test to prove key broadcast, one shared
   external value request stream, query-lane mapping, backpressure, and
   head-major/slice-major output order.
5. Preserve the explicit scope statement that no flat eight-cluster RTL
   equivalence simulation was run.
6. Keep timing- or placement-infeasible sweep rows as boundary evidence.
7. Treat vectorless power as structural evidence only; activity-backed energy
   remains a follow-on gate.
8. Gate activity power on merged equivalence and PPA, explicit phase-cycle
   accounting, routed annotation coverage for directly measured components,
   and direct-versus-compositional provenance. Do not promote compositional
   scaling as a direct full-group power measurement or as total token energy.
9. Recost only group counts 1, 2, and 4 for the four Llama7B GQA groups per
   layer. Use measured one-group timing, area, and activity energy, identify
   multi-group area/power as linear composition rather than array PNR, and
   retain off-group memory/NoC/HBM and total-token energy as open boundaries.
