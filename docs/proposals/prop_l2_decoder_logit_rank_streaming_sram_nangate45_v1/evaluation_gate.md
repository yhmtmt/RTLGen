# Evaluation Gate

The evaluator should produce:

- `decoder_logit_rank_streaming_overlap__l2_decoder_logit_rank_streaming_sram_nangate45_v1.json`
- `decoder_logit_rank_streaming_overlap__l2_decoder_logit_rank_streaming_sram_nangate45_v1.md`

Acceptance checks:

- report `memory_hierarchy_model.source` is `sram_metrics_json_plus_planning_noc`
- report inputs include `sram_metrics_json_path` set to `runs/designs/sram/minimal_v0_2_draft/sram_metrics.json`
- SRAM model provenance reports `pdk` containing `nangate45` and `tech_node_nm` containing `45`
- NoC model provenance remains `planning_default_not_literature_backed`
- ready-valid perf-sim/RTL equivalence observables are unchanged from the prior measured-merge streaming run
