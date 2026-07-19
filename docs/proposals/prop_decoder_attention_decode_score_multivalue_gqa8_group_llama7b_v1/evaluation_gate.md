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
7. Treat vectorless power as structural evidence only. Measure activity-backed
   energy separately for every timing-feasible folded lane count; never infer a
   missing lane point by linear scaling.
8. Gate folded activity power on the matching 1/2/4/8-lane equivalence row and
   PPA artifact, explicit accounting for every query-head wave and replay,
   routed annotation coverage, and direct-versus-compositional provenance. The
   activity transaction may include one observation cycle after the equivalence
   completion cycle, but no command-service cycle may be omitted.
9. Recost the Cartesian product of measured folded lane counts and physical
   group counts 1, 2, and 4 for the four Llama7B GQA groups per layer. Use each
   lane point's measured timing, area, cycles, and activity energy. Identify
   multi-group area/power as linear composition until direct array PNR/activity
   exists, and retain off-group memory/NoC/HBM and total-token energy as open
   boundaries.
10. Before direct array PPA, compose the merged complete-group equivalence
    result with protocol simulations of generated one-, two-, and four-group
    wrappers. Require atomic command/input acceptance and independent external
    value-memory and result channels.
11. Compare array PPA only at matched macro density: 7.2 mm for one group,
    10.2 mm for two groups, and 14.4 mm for four groups. Keep the 8 ns and
    10 ns targets and retain infeasible points.
12. Treat direct array PNR as timing, area, routing, command-fanout, and
    clock-tree evidence. It does not close external value memory, NoC, HBM,
    total-token energy, or a monolithic 32-cluster arithmetic simulation.
13. Recompute QKV tile allocation, layer latency, throughput, and embodied
    logic-plus-SRAM area from every timing-feasible direct array row. Preserve
    all rejected physical rows and label inherited group-component energy as
    compositional until direct array activity is measured.
