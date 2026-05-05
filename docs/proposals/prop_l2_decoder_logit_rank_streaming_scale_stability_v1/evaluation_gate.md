# Evaluation Gate

The evaluator should produce:

- `decoder_logit_rank_streaming_overlap__l2_decoder_logit_rank_streaming_scale_stability_v1.json`
- `decoder_logit_rank_streaming_overlap__l2_decoder_logit_rank_streaming_scale_stability_v1.md`

Acceptance checks:

- report inputs include `vocab_size_list` with `50257`, `100000`, and `200000`
- report inputs include `producer_lanes_list` with `8`, `16`, `32`, `64`, and `128`
- report includes a `scale_stability_summary` entry for each vocabulary size
- SRAM provenance reports `nangate45` and `45 nm`
- NoC provenance remains `planning_default_not_literature_backed`
- ready-valid perf-sim/RTL equivalence observables remain unchanged
